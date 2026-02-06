"""
Ingestion service
=================
Parse uploaded PDFs / text → extract paragraphs → chunk → build dual index.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import logging
import pickle
from pathlib import Path
from typing import List

import numpy as np
from rank_bm25 import BM25Okapi
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import SourceDoc, SourceChunk, IngestionJob, async_session
from app.utils.pdf_parser import parse_file, Paragraph

log = logging.getLogger(__name__)
settings = get_settings()

# ── Module-level singletons (populated after ingestion) ─────
_dense_index = None          # FAISS index
_bm25_index: BM25Okapi | None = None
_chunk_store: list[dict] = []     # parallel list to FAISS rows
_embedder = None
_models_available = None


def _check_models():
    global _models_available
    if _models_available is not None:
        return _models_available
    try:
        import sentence_transformers  # noqa: F401
        _models_available = True
    except ImportError:
        _models_available = False
        log.warning("sentence_transformers not available — BM25-only indexing")
    return _models_available


def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _embedder


def get_dense_index():
    return _dense_index


def get_bm25_index():
    return _bm25_index


def get_chunk_store():
    return _chunk_store


# ── Chunking with sliding window fallback ───────────────────
def _chunk_paragraphs(paragraphs: list[Paragraph],
                      max_chars: int = 2048,
                      overlap: int = 256) -> list[Paragraph]:
    """Paragraph-first chunking.  Long paragraphs get sliding-window split."""
    out: list[Paragraph] = []
    for p in paragraphs:
        if len(p.text) <= max_chars:
            out.append(p)
        else:
            # sliding window
            words = p.text.split()
            window_words = max_chars // 6          # rough estimate
            step = max(1, window_words - (overlap // 6))
            for i in range(0, len(words), step):
                snippet = " ".join(words[i: i + window_words])
                if not snippet:
                    break
                char_start = p.char_start + p.text.find(snippet[:40])
                out.append(Paragraph(
                    page=p.page,
                    paragraph_id=p.paragraph_id,
                    text=snippet,
                    char_start=max(char_start, p.char_start),
                    char_end=min(char_start + len(snippet), p.char_end),
                ))
    return out


# ── Build indexes ───────────────────────────────────────────
def _build_indexes(chunks: list[dict]):
    """Build FAISS dense index + BM25 from chunk dicts."""
    global _dense_index, _bm25_index, _chunk_store

    _chunk_store = chunks
    texts = [c["text"] for c in chunks]
    index_dir = settings.INDEX_DIR
    index_dir.mkdir(parents=True, exist_ok=True)

    # BM25 (always built — no model needed)
    tokenised = [t.lower().split() for t in texts]
    _bm25_index = BM25Okapi(tokenised)
    with open(index_dir / "bm25.pkl", "wb") as f:
        pickle.dump(_bm25_index, f)
    with open(index_dir / "chunks.pkl", "wb") as f:
        pickle.dump(_chunk_store, f)
    log.info("BM25 index built: %d docs", len(tokenised))

    # Dense index (only if sentence_transformers available)
    if _check_models():
        try:
            import faiss
            embedder = _get_embedder()
            log.info("Encoding %d chunks …", len(texts))
            vectors = embedder.encode(texts, show_progress_bar=True, convert_to_numpy=True)
            vectors = vectors.astype("float32")
            dim = vectors.shape[1]
            index = faiss.IndexFlatIP(dim)
            faiss.normalize_L2(vectors)
            index.add(vectors)
            _dense_index = index
            faiss.write_index(index, str(index_dir / "dense.faiss"))
            log.info("Dense index built: %d vectors", index.ntotal)
        except Exception as e:
            log.warning("Dense index build failed (%s) — BM25-only mode", e)
    else:
        log.info("Skipping dense index (no sentence_transformers) — BM25-only mode")


def load_indexes():
    """Load persisted indexes from disk (called on startup)."""
    global _dense_index, _bm25_index, _chunk_store
    index_dir = settings.INDEX_DIR

    # Load BM25 + chunk store (always)
    try:
        with open(index_dir / "bm25.pkl", "rb") as f:
            _bm25_index = pickle.load(f)
        with open(index_dir / "chunks.pkl", "rb") as f:
            _chunk_store = pickle.load(f)
        log.info("Loaded BM25 index: %d chunks", len(_chunk_store))
    except Exception:
        log.warning("No persisted BM25 index found — ingest sources first.")

    # Load dense index (optional)
    try:
        import faiss
        dense_path = index_dir / "dense.faiss"
        if dense_path.exists():
            _dense_index = faiss.read_index(str(dense_path))
            log.info("Loaded FAISS dense index: %d vectors", _dense_index.ntotal)
    except Exception:
        log.info("No dense index loaded — will use BM25-only retrieval.")


# ── Main ingestion routine (runs in background task) ────────
async def run_ingestion(job_id: str, source_set_id: str):
    """Parse all source docs for the set, chunk, build indexes."""
    async with async_session() as db:
        # Mark running
        job = await db.get(IngestionJob, job_id)
        job.status = "running"
        await db.commit()

        try:
            # Gather source docs
            stmt = select(SourceDoc).where(SourceDoc.source_set_id == source_set_id)
            result = await db.execute(stmt)
            docs: list[SourceDoc] = list(result.scalars().all())

            if not docs:
                job.status = "failed"
                job.error = "No source documents found for this set."
                await db.commit()
                return

            all_chunks: list[dict] = []
            total = len(docs)

            for idx, doc in enumerate(docs):
                parsed = await asyncio.to_thread(parse_file, doc.filepath)
                doc.num_pages = parsed.num_pages

                chunked = _chunk_paragraphs(parsed.paragraphs)
                for chunk in chunked:
                    chunk_dict = dict(
                        doc_id=doc.id,
                        doc_name=doc.filename,
                        page=chunk.page,
                        paragraph_id=chunk.paragraph_id,
                        text=chunk.text,
                        char_start=chunk.char_start,
                        char_end=chunk.char_end,
                    )
                    all_chunks.append(chunk_dict)

                    # Also persist in DB
                    db.add(SourceChunk(
                        doc_id=doc.id,
                        page=chunk.page,
                        paragraph_id=chunk.paragraph_id,
                        text=chunk.text,
                        char_start=chunk.char_start,
                        char_end=chunk.char_end,
                    ))

                job.progress = (idx + 1) / total * 0.5   # parsing = 50%
                await db.commit()

            # Build indexes (CPU-heavy → run in thread)
            await asyncio.to_thread(_build_indexes, all_chunks)

            job.progress = 1.0
            job.status = "done"
            job.finished_at = dt.datetime.utcnow()
            await db.commit()
            log.info("Ingestion job %s complete – %d chunks indexed.", job_id, len(all_chunks))

        except Exception as exc:
            log.exception("Ingestion failed")
            job.status = "failed"
            job.error = str(exc)
            await db.commit()
