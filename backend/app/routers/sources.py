"""
Source document management endpoints.
  POST /sources/upload    → upload PDFs / text files
  POST /sources/ingest    → trigger parsing + indexing
  GET  /sources           → list uploaded docs
  GET  /sources/{id}/pdf  → stream PDF for viewer
"""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db, SourceDoc, IngestionJob
from app.models import SourceDocOut, IngestRequest, JobStatusOut
from app.services.ingestion import run_ingestion

router = APIRouter(prefix="/sources", tags=["Sources"])
settings = get_settings()


@router.post("/upload", response_model=list[SourceDocOut])
async def upload_sources(
    files: list[UploadFile] = File(...),
    source_set_id: str = "default",
    db: AsyncSession = Depends(get_db),
):
    """Upload one or more PDF/TXT files."""
    dest_dir = settings.SOURCES_DIR / source_set_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    docs_out: list[SourceDoc] = []

    for f in files:
        doc_id = uuid.uuid4().hex[:12]
        filepath = dest_dir / f"{doc_id}_{f.filename}"
        with open(filepath, "wb") as buf:
            shutil.copyfileobj(f.file, buf)

        doc = SourceDoc(
            id=doc_id,
            filename=f.filename,
            filepath=str(filepath),
            source_set_id=source_set_id,
        )
        db.add(doc)
        docs_out.append(doc)

    await db.commit()
    return docs_out


@router.post("/ingest", response_model=JobStatusOut)
async def ingest_sources(
    body: IngestRequest,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Trigger async ingestion: parse → chunk → index."""
    job = IngestionJob(source_set_id=body.source_set_id)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    background.add_task(run_ingestion, job.id, body.source_set_id)
    return job


@router.get("", response_model=list[SourceDocOut])
async def list_sources(
    source_set_id: str = "default",
    db: AsyncSession = Depends(get_db),
):
    stmt = select(SourceDoc).where(SourceDoc.source_set_id == source_set_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{doc_id}/pdf")
async def get_pdf(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(SourceDoc, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    p = Path(doc.filepath)
    if not p.exists():
        raise HTTPException(404, "File missing on disk")
    media = "application/pdf" if p.suffix.lower() == ".pdf" else "text/plain"
    return FileResponse(str(p), media_type=media, filename=doc.filename)
