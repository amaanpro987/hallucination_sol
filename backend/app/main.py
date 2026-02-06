"""
DataForge Hallucination Auditor — FastAPI application entry-point.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers import sources, verify, runs
from app.services.ingestion import load_indexes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
log = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    # Ensure data dirs exist
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    settings.SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    settings.INDEX_DIR.mkdir(parents=True, exist_ok=True)

    # Create DB tables
    await init_db()
    log.info("Database initialised.")

    # Load persisted indexes (if any)
    load_indexes()

    yield  # app runs here

    log.info("Shutting down.")


app = FastAPI(
    title="DataForge Hallucination Auditor",
    version="0.1.0",
    description="Audit-grade hallucination detection with citation grounding.",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────────────────
app.include_router(sources.router)
app.include_router(verify.router)
app.include_router(runs.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
