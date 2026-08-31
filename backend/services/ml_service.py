"""ML prediction service.

Loads the trained scikit-learn bundle produced by ml/training/train_model.py
(ml/models/landslide_model.joblib). If the model file is missing, the backend
still works - the rule-based engine is the fallback.

Bundle format: {"model": <estimator with predict_proba>, "features": [names],
"metrics": {...}, "trained_at": iso, "data_note": str}
"""
import logging
from datetime import datetime, timezone
from pathlib import Path

import joblib

from utils.config import ML_MODEL_PATH, classify_score

logger = logging.getLogger("ml_service")

_bundle = None
_loaded = False


def _load():
    global _bundle, _loaded
    if _loaded:
        return
    _loaded = True
    path = Path(ML_MODEL_PATH)
    if path.exists():
        try:
            _bundle = joblib.load(path)
            logger.info("ML model loaded: %s", path)
        except Exception as exc:  # corrupted / incompatible bundle
            logger.warning("Failed to load ML model %s: %s", path, exc)
            _bundle = None


def model_available() -> bool:
    _load()
    return _bundle is not None


def _inner_model():
    """Unwrap the sklearn Pipeline to report the actual estimator name."""
    model = _bundle["model"]
    return getattr(model, "named_steps", {}).get("model", model) if model else model


def model_info() -> dict:
    _load()
    if not _bundle:
        return {
            "model_available": False,
            "how_to_train": (
                "python ml/datasets/generate_synthetic_dataset.py && "
                "python ml/training/train_model.py"
            ),
            "note": "Backend automatically falls back to the rule-based engine.",
        }
    return {
        "model_available": True,
        "model_type": type(_inner_model()).__name__,
        "features": _bundle.get("features", []),
        "metrics": _bundle.get("metrics", {}),
        "trained_at": _bundle.get("trained_at"),
        "data_note": _bundle.get("data_note", ""),
    }


def predict_from_factor_scores(factor_scores: dict) -> dict | None:
    """Run the trained model on 0-100 factor scores -> probability/score/level."""
    _load()
    if not _bundle:
        return None
    features = _bundle["features"]
    try:
        x = [[float(factor_scores[f]) for f in features]]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"Missing/invalid factor for ML input: {exc}") from exc

    prob = float(_bundle["model"].predict_proba(x)[0][1])
    score = round(prob * 100.0, 1)
    return {
        "probability_elevated_risk": round(prob, 4),
        "risk_score": score,
        "risk_level": classify_score(score),
        "model_type": type(_inner_model()).__name__,
        "trained_at": _bundle.get("trained_at"),
        "metrics": _bundle.get("metrics", {}),
        "predicted_at": datetime.now(timezone.utc).isoformat(),
    }
