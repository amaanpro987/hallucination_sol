"""
Verification endpoints.
  POST /verify         → start a verification run
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, VerificationRun
from app.models import VerifyRequest, RunSummaryOut
from app.services.orchestrator import run_verification

router = APIRouter(tags=["Verification"])


@router.post("/verify", response_model=RunSummaryOut)
async def verify(
    body: VerifyRequest,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start a new verification run (async background)."""
    run = VerificationRun(
        run_name=body.run_name,
        source_set_id=body.source_set_id,
        llm_output=body.llm_output,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    background.add_task(run_verification, run.id)

    return RunSummaryOut(
        id=run.id,
        run_name=run.run_name,
        status=run.status,
        trust_score=run.trust_score,
        created_at=str(run.created_at),
    )
