"""
Run retrieval + job status endpoints.
  GET /runs              → list all runs
  GET /runs/{run_id}     → full annotated run with claims
  GET /jobs/{job_id}     → ingestion job status
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db, VerificationRun, ClaimResult, IngestionJob
from app.models import (
    RunOut, RunSummaryOut, ClaimResultOut, EvidenceItem,
    TrustScoreOut, JobStatusOut,
)

router = APIRouter(tags=["Runs & Jobs"])


# ── Runs ────────────────────────────────────────────────────
@router.get("/runs", response_model=list[RunSummaryOut])
async def list_runs(db: AsyncSession = Depends(get_db)):
    stmt = select(VerificationRun).order_by(VerificationRun.created_at.desc())
    result = await db.execute(stmt)
    runs = result.scalars().all()
    return [
        RunSummaryOut(
            id=r.id, run_name=r.run_name, status=r.status,
            trust_score=r.trust_score, created_at=str(r.created_at),
        )
        for r in runs
    ]


@router.get("/runs/{run_id}", response_model=RunOut)
async def get_run(run_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(VerificationRun)
        .options(selectinload(VerificationRun.claims))
        .where(VerificationRun.id == run_id)
    )
    result = await db.execute(stmt)
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(404, "Run not found")

    claims_out = []
    sup = con = unv = hr = 0
    for c in sorted(run.claims, key=lambda x: x.claim_id):
        ev_list = [EvidenceItem(**e) for e in (c.evidence or [])]
        claims_out.append(ClaimResultOut(
            id=c.id, sentence_id=c.sentence_id, claim_id=c.claim_id,
            claim_text=c.claim_text, claim_type=c.claim_type,
            risk_weight=c.risk_weight, label=c.label,
            confidence=c.confidence, rationale=c.rationale,
            evidence=ev_list, suggested_correction=c.suggested_correction,
        ))
        if c.label == "SUPPORTED":
            sup += 1
        elif c.label == "CONTRADICTED":
            con += 1
            if c.claim_type in ("numeric_date", "negation", "causal"):
                hr += 1
        else:
            unv += 1

    trust = TrustScoreOut(
        overall=run.trust_score or 0,
        faithfulness=run.faithfulness or 0,
        groundedness=run.groundedness or 0,
        supported_count=sup,
        contradicted_count=con,
        unverifiable_count=unv,
        high_risk_contradictions=hr,
    )

    return RunOut(
        id=run.id, run_name=run.run_name, source_set_id=run.source_set_id,
        llm_output=run.llm_output, status=run.status, trust=trust,
        claims=claims_out, created_at=str(run.created_at),
        finished_at=str(run.finished_at) if run.finished_at else None,
    )


# ── Jobs ────────────────────────────────────────────────────
@router.get("/jobs/{job_id}", response_model=JobStatusOut)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await db.get(IngestionJob, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return JobStatusOut(
        id=job.id, source_set_id=job.source_set_id,
        status=job.status, progress=job.progress,
        error=job.error, created_at=str(job.created_at),
        finished_at=str(job.finished_at) if job.finished_at else None,
    )
