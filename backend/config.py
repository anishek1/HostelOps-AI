"""
config.py — HostelOps AI
========================
Single source of truth for all environment variables.
This is the ONLY file in the project allowed to read from os.environ / .env.
All other files import from here.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

# Absolute path to the directory containing this file (backend/)
BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    # --- Database ---
    DATABASE_URL: str

    # --- Auth ---
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # --- LLM ---
    GROQ_API_KEY: str = ""
    GROQ_MODEL_NAME: str = "llama-3.3-70b-versatile"

    # --- Task Queue ---
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    # --- Agent Thresholds ---
    COMPLAINT_CONFIDENCE_THRESHOLD: float = 0.85
    MESS_DISSATISFACTION_THRESHOLD: float = 2.5
    MESS_SPIKE_DELTA: float = 1.5
    LAUNDRY_NOSHOW_PENALTY_HOURS: int = 48
    LAUNDRY_UNAVAILABILITY_DAYS: int = 4
    APPROVAL_QUEUE_TIMEOUT_MINUTES: int = 30

    # --- Sprint 4: Mess Alert Thresholds ---
    MESS_ALERT_THRESHOLD: float = 2.5
    MESS_CRITICAL_THRESHOLD: float = 2.0
    MESS_MIN_PARTICIPATION: float = 0.15
    MESS_MIN_RESPONSES: int = 5

    # --- Sprint 4: Laundry Slot Generation ---
    LAUNDRY_SLOTS_START_HOUR: int = 8
    LAUNDRY_SLOTS_END_HOUR: int = 22
    LAUNDRY_SLOT_DURATION_HOURS: int = 1

    # --- Sprint 5: Hostel Identity & Config Fallbacks ---
    HOSTEL_NAME: str = "HostelOps AI"
    HOSTEL_MODE: str = "college"
    TOTAL_FLOORS: int = 3
    TOTAL_STUDENTS_CAPACITY: int = 200
    COMPLAINT_RATE_LIMIT_DAILY: int = 5
    LAUNDRY_CANCELLATION_DEADLINE_MINUTES: int = 15

    # --- Embeddings (Phase 5: semantic deduplication) ---
    HF_API_KEY: str = ""  # HuggingFace Inference API key (free tier). If empty, vector dedup is disabled.
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    SIMILARITY_THRESHOLD: float = 0.82  # cosine similarity above this = probable duplicate

    # --- CORS ---
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    model_config = {
        "env_file": str(BASE_DIR / ".env"),  # absolute path — works from any working directory
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()