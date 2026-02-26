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
    GROQ_MODEL_NAME: str = "llama3-8b-8192"

    # --- Task Queue ---
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    # --- Push Notifications ---
    VAPID_PUBLIC_KEY: str = ""
    VAPID_PRIVATE_KEY: str = ""
    VAPID_CLAIM_EMAIL: str = ""

    # --- Agent Thresholds ---
    COMPLAINT_CONFIDENCE_THRESHOLD: float = 0.85
    MESS_DISSATISFACTION_THRESHOLD: float = 2.5
    MESS_SPIKE_DELTA: float = 1.5
    LAUNDRY_NOSHOW_PENALTY_HOURS: int = 48
    LAUNDRY_UNAVAILABILITY_DAYS: int = 4
    APPROVAL_QUEUE_TIMEOUT_MINUTES: int = 30

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