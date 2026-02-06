"""
Application configuration – environment-driven settings.
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── Paths ───────────────────────────────────────────────
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    SOURCES_DIR: Path = DATA_DIR / "sources"
    INDEX_DIR: Path = DATA_DIR / "index"
    DB_URL: str = ""   # computed at init

    # ── Retrieval ───────────────────────────────────────────
    DENSE_TOP_K: int = 20
    BM25_TOP_K: int = 20
    RERANK_TOP_K: int = 5
    CHUNK_SIZE: int = 512          # tokens (approx chars / 4)
    CHUNK_OVERLAP: int = 64

    # ── Verification thresholds ─────────────────────────────
    NLI_CONTRADICT_THRESHOLD: float = 0.70
    NLI_ENTAIL_THRESHOLD: float = 0.65
    NUMERIC_TOLERANCE: float = 0.01     # 1 % tolerance

    # ── Model identifiers ───────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    NLI_MODEL: str = "cross-encoder/nli-deberta-v3-base"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # ── Trust-score weights ─────────────────────────────────
    WEIGHT_NUMERIC: float = 1.6
    WEIGHT_NEGATION: float = 1.4
    WEIGHT_ENTITY: float = 1.2
    WEIGHT_DEFAULT: float = 1.0
    UNVERIFIABLE_SCORE: float = 0.5
    CRITICAL_PENALTY: float = 5.0

    # ── Server ──────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_prefix = "AUDITOR_"
        env_file = ".env"

    def model_post_init(self, __context):
        if not self.DB_URL:
            db_path = self.DATA_DIR / "auditor.db"
            object.__setattr__(self, 'DB_URL', f"sqlite+aiosqlite:///{db_path.as_posix()}")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
