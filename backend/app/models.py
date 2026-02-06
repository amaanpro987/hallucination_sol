"""
Pydantic schemas for API request / response bodies.
"""
from __future__ import annotations

import datetime as dt
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator


class _DateTimeMixin(BaseModel):
    """Auto-convert datetime fields to ISO strings."""

    @field_validator("created_at", "finished_at", mode="before", check_fields=False)
    @classmethod
    def _dt_to_str(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, dt.datetime):
            return v.isoformat()
        return str(v)


# ── Source ──────────────────────────────────────────────────
class SourceDocOut(_DateTimeMixin):
    id: str
    filename: str
    num_pages: int
    source_set_id: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


# ── Ingestion ──────────────────────────────────────────────
class IngestRequest(BaseModel):
    source_set_id: str = "default"


class JobStatusOut(_DateTimeMixin):
    id: str
    source_set_id: str
    status: str
    progress: float
    error: Optional[str] = None
    created_at: Optional[str] = None
    finished_at: Optional[str] = None

    class Config:
        from_attributes = True


# ── Verification ────────────────────────────────────────────
class VerifyRequest(BaseModel):
    run_name: str = "Untitled run"
    llm_output: str
    source_set_id: str = "default"


class EvidenceItem(BaseModel):
    doc_id: str
    doc_name: str
    page: int
    paragraph_id: int
    snippet: str
    highlight_offsets: list[int] = Field(default_factory=list)
    retrieval_score: float = 0.0
    nli: dict = Field(default_factory=dict)


class ClaimResultOut(BaseModel):
    id: str
    sentence_id: int
    claim_id: str
    claim_text: str
    claim_type: str
    risk_weight: float
    label: str
    confidence: float
    rationale: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
    suggested_correction: Optional[str] = None

    class Config:
        from_attributes = True


class TrustScoreOut(BaseModel):
    overall: float
    faithfulness: float
    groundedness: float
    supported_count: int
    contradicted_count: int
    unverifiable_count: int
    high_risk_contradictions: int


class RunOut(_DateTimeMixin):
    id: str
    run_name: str
    source_set_id: str
    llm_output: str
    status: str
    trust: Optional[TrustScoreOut] = None
    claims: list[ClaimResultOut] = Field(default_factory=list)
    created_at: Optional[str] = None
    finished_at: Optional[str] = None

    class Config:
        from_attributes = True


class RunSummaryOut(_DateTimeMixin):
    id: str
    run_name: str
    status: str
    trust_score: Optional[float] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
