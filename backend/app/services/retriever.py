"""
Hybrid Retriever
================
Dense (FAISS) + Sparse (BM25), merge + cross-encoder rerank.
Falls back to BM25-only + TF-IDF cosine when heavy models aren't available.
Returns top-K evidence passages for a given claim.
"""
from __future__ import annotations

import logging
import re
import math
from collections import Counter
from dataclasses import dataclass

import numpy as np

from app.config import get_settings
from app.services.ingestion import (
    get_dense_index,
    get_bm25_index,
    get_chunk_store,
)

log = logging.getLogger(__name__)
settings = get_settings()

_reranker = None
_embedder = None
_models_available = None   # None = not checked yet


def _check_models():
    """Try to import sentence_transformers; cache result."""
    global _models_available
    if _models_available is not None:
        return _models_available
    try:
        import sentence_transformers  # noqa: F401
        _models_available = True
    except ImportError:
        _models_available = False
        log.warning("sentence_transformers not available — using lightweight retrieval")
    return _models_available


def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _embedder


def _get_reranker():
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder
        _reranker = CrossEncoder(settings.RERANKER_MODEL)
    return _reranker


# ── Lightweight TF-IDF cosine (no external models needed) ───
def _tokenize(text: str) -> list[str]:
    return re.findall(r'\w+', text.lower())


def _tfidf_cosine(query_tokens: list[str], doc_tokens: list[str]) -> float:
    """Simple TF-IDF-ish cosine similarity."""
    all_tokens = set(query_tokens) | set(doc_tokens)
    if not all_tokens:
        return 0.0
    q_counts = Counter(query_tokens)
    d_counts = Counter(doc_tokens)
    dot = sum(q_counts.get(t, 0) * d_counts.get(t, 0) for t in all_tokens)
    q_norm = math.sqrt(sum(v * v for v in q_counts.values()))
    d_norm = math.sqrt(sum(v * v for v in d_counts.values()))
    if q_norm == 0 or d_norm == 0:
        return 0.0
    return dot / (q_norm * d_norm)


@dataclass
class RetrievedEvidence:
    doc_id: str
    doc_name: str
    page: int
    paragraph_id: int
    text: str
    char_start: int
    char_end: int
    score: float              # reranker / similarity score


def _retrieve_lightweight(claim_text: str, top_k: int) -> list[RetrievedEvidence]:
    """BM25 + TF-IDF cosine reranking (no model downloads needed)."""
    bm25_index = get_bm25_index()
    chunks = get_chunk_store()

    if not chunks or bm25_index is None:
        log.warning("Indexes not loaded. Returning empty evidence.")
        return []

    # BM25 retrieval
    query_tokens = claim_text.lower().split()
    bm25_scores = bm25_index.get_scores(query_tokens)
    candidate_count = min(settings.BM25_TOP_K * 2, len(chunks))
    bm25_top = np.argsort(bm25_scores)[::-1][:candidate_count].tolist()

    # Rerank with TF-IDF cosine
    claim_toks = _tokenize(claim_text)
    scored = []
    for idx in bm25_top:
        if idx < len(chunks):
            chunk_toks = _tokenize(chunks[idx]["text"])
            cos = _tfidf_cosine(claim_toks, chunk_toks)
            # Blend BM25 + cosine
            combined = 0.5 * (bm25_scores[idx] / (max(bm25_scores) + 1e-9)) + 0.5 * cos
            scored.append((idx, combined))

    scored.sort(key=lambda x: x[1], reverse=True)

    results: list[RetrievedEvidence] = []
    for idx, score in scored[:top_k]:
        c = chunks[idx]
        results.append(RetrievedEvidence(
            doc_id=c["doc_id"],
            doc_name=c["doc_name"],
            page=c["page"],
            paragraph_id=c["paragraph_id"],
            text=c["text"],
            char_start=c["char_start"],
            char_end=c["char_end"],
            score=round(score, 4),
        ))

    return results


def _retrieve_with_models(claim_text: str, top_k: int) -> list[RetrievedEvidence]:
    """Full dense+BM25+reranker pipeline (requires sentence_transformers)."""
    dense_index = get_dense_index()
    bm25_index = get_bm25_index()
    chunks = get_chunk_store()

    if not chunks:
        return []

    # If no dense index, fall back to lightweight
    if dense_index is None:
        return _retrieve_lightweight(claim_text, top_k)

    # 1. Dense retrieval
    embedder = _get_embedder()
    query_vec = embedder.encode([claim_text], convert_to_numpy=True).astype("float32")
    import faiss
    faiss.normalize_L2(query_vec)
    dense_scores, dense_ids = dense_index.search(query_vec, settings.DENSE_TOP_K)
    dense_ids = dense_ids[0].tolist()
    dense_scores = dense_scores[0].tolist()

    # 2. BM25 retrieval
    bm25_scores = bm25_index.get_scores(claim_text.lower().split())
    bm25_top = np.argsort(bm25_scores)[::-1][: settings.BM25_TOP_K].tolist()

    # 3. Merge + deduplicate
    seen = set()
    candidates: list[tuple[int, float]] = []
    for idx, sc in zip(dense_ids, dense_scores):
        if 0 <= idx < len(chunks) and idx not in seen:
            seen.add(idx)
            candidates.append((idx, float(sc)))
    for idx in bm25_top:
        if idx not in seen:
            seen.add(idx)
            candidates.append((idx, float(bm25_scores[idx])))

    if not candidates:
        return []

    # 4. Cross-encoder rerank
    try:
        reranker = _get_reranker()
        pairs = [(claim_text, chunks[idx]["text"]) for idx, _ in candidates]
        rerank_scores = reranker.predict(pairs).tolist()
        ranked = sorted(zip(candidates, rerank_scores), key=lambda x: x[1], reverse=True)
    except Exception as e:
        log.warning("Reranker failed (%s), using dense scores", e)
        ranked = sorted(candidates, key=lambda x: x[1], reverse=True)
        ranked = [((idx, sc), sc) for idx, sc in ranked]

    results: list[RetrievedEvidence] = []
    for (idx, _), rr_score in ranked[:top_k]:
        c = chunks[idx]
        results.append(RetrievedEvidence(
            doc_id=c["doc_id"],
            doc_name=c["doc_name"],
            page=c["page"],
            paragraph_id=c["paragraph_id"],
            text=c["text"],
            char_start=c["char_start"],
            char_end=c["char_end"],
            score=rr_score,
        ))

    return results


def retrieve_evidence(claim_text: str, top_k: int | None = None) -> list[RetrievedEvidence]:
    """
    Hybrid retrieval for a single claim.
    Uses lightweight BM25+cosine by default, upgrades to dense+reranker if models exist.
    """
    top_k = top_k or settings.RERANK_TOP_K

    if _check_models():
        try:
            return _retrieve_with_models(claim_text, top_k)
        except Exception as e:
            log.warning("Model-based retrieval failed (%s), falling back to lightweight", e)

    return _retrieve_lightweight(claim_text, top_k)
