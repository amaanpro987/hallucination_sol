"""
SQLAlchemy async engine + session factory + ORM table definitions.
"""
from __future__ import annotations

import uuid
import datetime as dt
from typing import Optional

from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, JSON, ForeignKey, Enum as SAEnum,
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.DB_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# ── Helper ──────────────────────────────────────────────────
def _uuid() -> str:
    return uuid.uuid4().hex[:12]


# ── Source Document ─────────────────────────────────────────
class SourceDoc(Base):
    __tablename__ = "source_docs"

    id = Column(String, primary_key=True, default=_uuid)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    num_pages = Column(Integer, default=0)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    source_set_id = Column(String, index=True, default="default")

    chunks = relationship("SourceChunk", back_populates="doc", cascade="all, delete-orphan")


# ── Source Chunk (paragraph-level) ──────────────────────────
class SourceChunk(Base):
    __tablename__ = "source_chunks"

    id = Column(String, primary_key=True, default=_uuid)
    doc_id = Column(String, ForeignKey("source_docs.id"), nullable=False)
    page = Column(Integer)
    paragraph_id = Column(Integer)
    char_start = Column(Integer)
    char_end = Column(Integer)
    text = Column(Text, nullable=False)
    embedding_idx = Column(Integer)           # position in FAISS index

    doc = relationship("SourceDoc", back_populates="chunks")


# ── Ingestion Job ───────────────────────────────────────────
class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id = Column(String, primary_key=True, default=_uuid)
    source_set_id = Column(String, nullable=False)
    status = Column(String, default="pending")       # pending | running | done | failed
    progress = Column(Float, default=0.0)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)


# ── Verification Run ───────────────────────────────────────
class VerificationRun(Base):
    __tablename__ = "verification_runs"

    id = Column(String, primary_key=True, default=_uuid)
    run_name = Column(String, default="Untitled run")
    source_set_id = Column(String, nullable=False)
    llm_output = Column(Text, nullable=False)
    trust_score = Column(Float, nullable=True)
    faithfulness = Column(Float, nullable=True)
    groundedness = Column(Float, nullable=True)
    status = Column(String, default="pending")       # pending | running | done | failed
    performance_metrics = Column(JSON, nullable=True)  # timing breakdown per stage
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    claims = relationship("ClaimResult", back_populates="run", cascade="all, delete-orphan")


# ── Claim-level Result ──────────────────────────────────────
class ClaimResult(Base):
    __tablename__ = "claim_results"

    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("verification_runs.id"), nullable=False)

    sentence_id = Column(Integer)
    claim_id = Column(String)            # e.g. "7.2"
    claim_text = Column(Text)
    claim_type = Column(String)          # numeric_date | entity | negation | …
    risk_weight = Column(Float, default=1.0)

    label = Column(String)               # SUPPORTED | CONTRADICTED | UNVERIFIABLE
    confidence = Column(Float)
    rationale = Column(Text)

    evidence = Column(JSON)              # list of evidence dicts
    suggested_correction = Column(Text, nullable=True)

    run = relationship("VerificationRun", back_populates="claims")


# ── DB lifecycle helpers ────────────────────────────────────
async def init_db():
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
