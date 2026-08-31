"""Preprocessing: load dataset, feature/label split, train-test split, scaler."""
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
DATASET_CSV = HERE.parent / "datasets" / "landslide_dataset.csv"

FEATURES = ["rainfall", "slope", "soil_moisture", "elevation", "soil_geology",
            "land_cover", "historical", "drainage", "road_cutting"]
TARGET = "landslide_event"


def load_dataframe(csv_path: str | None = None) -> pd.DataFrame:
    path = Path(csv_path) if csv_path else DATASET_CSV
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {path}\n"
            "Run: python ml/datasets/generate_synthetic_dataset.py  "
            "(or place a real inventory CSV with the documented columns there)")
    df = pd.read_csv(path)
    missing = [c for c in FEATURES + [TARGET] if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")
    return df.dropna(subset=FEATURES + [TARGET])


def make_splits(df: pd.DataFrame, test_size: float = 0.2, seed: int = 42):
    X = df[FEATURES].to_numpy(dtype=float)
    y = df[TARGET].to_numpy(dtype=int)
    return train_test_split(X, y, test_size=test_size, random_state=seed, stratify=y)


def make_scaler():
    return StandardScaler()
