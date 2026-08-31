"""Generate a synthetic landslide training dataset (prototype).

WHY SYNTHETIC?
Real landslide inventories (GSI, NASA cooperative reporting, etc.) are
restricted / patchy. For the prototype pipeline we generate a physically
plausible, correlated feature space over the 9 risk factors and label samples
with a logistic response to a rule-weighted susceptibility score + noise.

IMPORTANT: models trained on this file are for DEMO / pipeline validation only.
To train on real data, drop a CSV with the same columns at
ml/datasets/landslide_dataset.csv (see ml/README.md) and re-run training.

Columns (features 0-100): rainfall, slope, soil_moisture, elevation,
soil_geology, land_cover, historical, drainage, road_cutting
Label: landslide_event (0/1)

Usage:
    python ml/datasets/generate_synthetic_dataset.py [--samples 8000] [--seed 42]
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT_CSV = HERE / "landslide_dataset.csv"

FEATURES = ["rainfall", "slope", "soil_moisture", "elevation", "soil_geology",
            "land_cover", "historical", "drainage", "road_cutting"]

RULE_WEIGHTS = np.array([0.30, 0.20, 0.15, 0.10, 0.10, 0.05, 0.05, 0.03, 0.02])


def _clip100(x):
    return np.clip(x, 0.0, 100.0)


def generate(n: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # Correlated, physically plausible factor distributions -------------------
    rainfall = _clip100(rng.gamma(shape=2.2, scale=20.0, size=n))       # skew wet
    slope = _clip100(rng.beta(2.2, 2.6, size=n) * 100)
    soil_moisture = _clip100(12 + 0.55 * rainfall + rng.normal(0, 8, n))
    elevation = _clip100(rng.beta(1.6, 2.2, size=n) * 100)
    soil_geology = _clip100(rng.normal(62, 14, n))
    land_cover = _clip100(rng.normal(56, 12, n))
    historical = _clip100(rng.normal(52, 18, n))
    drainage = _clip100(0.5 * rainfall + 0.3 * slope + 0.2 * elevation + rng.normal(0, 6, n))
    road_cutting = _clip100(rng.normal(48, 20, n))

    X = np.column_stack([rainfall, slope, soil_moisture, elevation, soil_geology,
                         land_cover, historical, drainage, road_cutting])

    # Labels: logistic response to the weighted rule score --------------------
    rule_score = X @ RULE_WEIGHTS
    logit = -6.0 + 0.085 * rule_score + rng.normal(0, 0.45, n)
    p = 1.0 / (1.0 + np.exp(-logit))
    event = (rng.random(n) < p).astype(int)

    df = pd.DataFrame(X, columns=FEATURES)
    df["landslide_event"] = event
    return df


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--samples", type=int, default=8000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    df = generate(args.samples, args.seed)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    print(f"Synthetic dataset written: {OUT_CSV}")
    print(f"  samples={len(df)}  event_rate={df['landslide_event'].mean():.1%}")
    print("  NOTE: synthetic demo data — replace with a real landslide inventory")
    print("        for any operational use (see ml/README.md).")


if __name__ == "__main__":
    main()
