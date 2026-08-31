"""Central configuration for the NER Landslide AI backend.

All secrets and tunables are read from environment variables so that no
credentials are hard-coded in source (see .env.example at the repo root).
"""
import os
from pathlib import Path

# backend/utils/config.py -> parents[2] == repository root
REPO_ROOT = Path(__file__).resolve().parents[2]

APP_NAME = "NER Landslide AI API"
APP_VERSION = "1.0.0"
DESCRIPTION = (
    "AI-Based Early Warning and Landslide Risk Monitoring System for the "
    "North Eastern Region of India"
)

ENV = os.getenv("NER_ENV", "development")

# --- Security ------------------------------------------------------------
SECRET_KEY = os.getenv("NER_SECRET_KEY", "dev-only-insecure-key-change-me")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("NER_TOKEN_EXPIRE_MINUTES", "1440"))

# --- Database ------------------------------------------------------------
# Default: local SQLite file (zero-setup). Override with e.g.
#   postgresql://user:pass@host:5432/ner_landslide
DATABASE_URL = os.getenv(
    "NER_DATABASE_URL", f"sqlite:///{(REPO_ROOT / 'database' / 'ner_landslide.db').as_posix()}"
)

# --- CORS ----------------------------------------------------------------
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "NER_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
    ).split(",")
    if o.strip()
]

# --- Weather service (Open-Meteo, no API key required) ---------------------
WEATHER_CACHE_TTL_SECONDS = int(os.getenv("NER_WEATHER_CACHE_TTL", "600"))
WEATHER_API_TIMEOUT = int(os.getenv("NER_WEATHER_TIMEOUT", "12"))

# --- Rate limiting (public API protection) --------------------------------
RATE_LIMIT_PER_MINUTE = int(os.getenv("NER_RATE_LIMIT_PER_MINUTE", "120"))

# --- ML -------------------------------------------------------------------
# Trained bundle produced by ml/training/train_model.py; the backend loads it
# automatically and falls back to the rule engine when the file is absent.
ML_MODEL_PATH = Path(os.getenv(
    "NER_ML_MODEL_PATH",
    str(REPO_ROOT / "ml" / "models" / "landslide_model.joblib"),
))

# --- Risk model weights (conceptual, configurable, sum normalized to 100) --
WEIGHTS = {
    "rainfall": float(os.getenv("NER_W_RAINFALL", "30")),
    "slope": float(os.getenv("NER_W_SLOPE", "20")),
    "soil_moisture": float(os.getenv("NER_W_SOIL_MOISTURE", "15")),
    "elevation": float(os.getenv("NER_W_ELEVATION", "10")),
    "soil_geology": float(os.getenv("NER_W_SOIL_GEOLOGY", "10")),
    "land_cover": float(os.getenv("NER_W_LAND_COVER", "5")),
    "historical": float(os.getenv("NER_W_HISTORICAL", "5")),
    "drainage": float(os.getenv("NER_W_DRAINAGE", "3")),
    "road_cutting": float(os.getenv("NER_W_ROAD_CUTTING", "2")),
}

# --- Risk classification thresholds (configurable) -------------------------
# 0-24 LOW | 25-49 MODERATE | 50-74 HIGH | 75-100 CRITICAL
THRESHOLD_MODERATE = float(os.getenv("NER_THRESHOLD_MODERATE", "25"))
THRESHOLD_HIGH = float(os.getenv("NER_THRESHOLD_HIGH", "50"))
THRESHOLD_CRITICAL = float(os.getenv("NER_THRESHOLD_CRITICAL", "75"))

RISK_LEVEL_COLORS = {
    "LOW": "#22c55e",
    "MODERATE": "#eab308",
    "HIGH": "#f97316",
    "CRITICAL": "#dc2626",
}

# Severity rank used for "risk got worse" notifications
LEVEL_SEVERITY = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}

DISCLAIMER = (
    "This is a prototype decision-support tool built on publicly available data. "
    "The risk score is NOT a scientifically validated prediction of a landslide. "
    "A HIGH or CRITICAL indicator means 'elevated landslide risk detected based on "
    "available data' - it does NOT mean a landslide will definitely happen. Always "
    "follow official disaster-management warnings and local authority instructions."
)


def classify_score(score: float) -> str:
    """Map a 0-100 risk score to a risk level using configurable thresholds."""
    if score < THRESHOLD_MODERATE:
        return "LOW"
    if score < THRESHOLD_HIGH:
        return "MODERATE"
    if score < THRESHOLD_CRITICAL:
        return "HIGH"
    return "CRITICAL"
