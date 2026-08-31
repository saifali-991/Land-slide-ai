"""Standalone prediction helper (demonstrates the backend contract).

Usage:
    python ml/prediction/predict.py --rainfall 80 --slope 60 --soil_moisture 70
"""
import argparse
import sys
from pathlib import Path

import joblib

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root

FEATURES = ["rainfall", "slope", "soil_moisture", "elevation", "soil_geology",
            "land_cover", "historical", "drainage", "road_cutting"]
MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "landslide_model.joblib"


def classify(score: float) -> str:
    if score < 25:
        return "LOW"
    if score < 50:
        return "MODERATE"
    if score < 75:
        return "HIGH"
    return "CRITICAL"


def load_bundle(path: str | None = None) -> dict:
    path = Path(path) if path else MODEL_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Model not found: {path}\nTrain it first: python ml/training/train_model.py")
    return joblib.load(path)


def predict(bundle: dict, factor_scores: dict) -> dict:
    x = [[float(factor_scores[f]) for f in bundle["features"]]]
    prob = float(bundle["model"].predict_proba(x)[0][1])
    score = round(prob * 100.0, 1)
    return {
        "probability_elevated_risk": round(prob, 4),
        "risk_score": score,
        "risk_level": classify(score),
        "model_type": type(bundle["model"].named_steps["model"]).__name__,
        "metrics": bundle.get("metrics", {}),
        "trained_at": bundle.get("trained_at"),
        "data_note": bundle.get("data_note", ""),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for f in FEATURES:
        ap.add_argument(f"--{f}", type=float, default=50.0)
    args = ap.parse_args()
    result = predict(load_bundle(), {f: getattr(args, f) for f in FEATURES})
    for k, v in result.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
