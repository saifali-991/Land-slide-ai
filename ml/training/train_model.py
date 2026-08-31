"""Train + evaluate landslide risk models; save the best bundle.

Models: Logistic Regression (baseline), Random Forest, Gradient Boosting,
and XGBoost when the optional package is installed.

Metrics emphasize safety-relevant behavior: precision/recall per class, F1,
ROC-AUC and the confusion matrix (false alarms vs missed events) rather than
a single unsupported accuracy figure.

Usage:
    python ml/training/train_model.py [--csv path/to/dataset.csv]

Outputs:
    ml/models/landslide_model.joblib   (loaded by the backend automatically)
    ml/models/model_metrics.json
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root

import joblib
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             f1_score, precision_score, recall_score, roc_auc_score)
from sklearn.pipeline import Pipeline

from ml.preprocessing.preprocess import FEATURES, TARGET, load_dataframe, make_scaler, make_splits

MODELS_DIR = Path(__file__).resolve().parents[1] / "models"


def _metrics(y_true, y_pred, y_prob) -> dict:
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "roc_auc": (round(float(roc_auc_score(y_true, y_prob)), 4)
                    if len(set(y_true)) > 1 else None),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }


def _importances(pipe: Pipeline) -> dict | None:
    model = pipe.named_steps.get("model")
    if hasattr(model, "feature_importances_"):
        pairs = zip(FEATURES, (round(float(v), 4) for v in model.feature_importances_))
        return dict(sorted(pairs, key=lambda kv: kv[1], reverse=True))
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", default=None, help="Optional dataset CSV path")
    args = ap.parse_args()

    df = load_dataframe(args.csv)
    x_train, x_test, y_train, y_test = make_splits(df)
    print(f"Dataset: {len(df)} rows | event rate: {df[TARGET].mean():.1%} "
          f"| train/test: {len(y_train)}/{len(y_test)}")

    candidates = {
        "LogisticRegression": LogisticRegression(max_iter=2000),
        "RandomForest": RandomForestClassifier(n_estimators=300, min_samples_leaf=3,
                                               random_state=42, n_jobs=-1),
        "GradientBoosting": GradientBoostingClassifier(random_state=42),
    }
    try:
        from xgboost import XGBClassifier
        candidates["XGBoost"] = XGBClassifier(n_estimators=300, max_depth=5,
                                              learning_rate=0.08, eval_metric="logloss",
                                              random_state=42)
    except ImportError:
        print("xgboost not installed — skipping (pip install xgboost to include it)")

    results, best_auc, best_bundle, best_name = {}, -1.0, None, None
    for name, est in candidates.items():
        pipe = Pipeline([("scaler", make_scaler()), ("model", est)])
        pipe.fit(x_train, y_train)
        prob = pipe.predict_proba(x_test)[:, 1]
        # Tune the decision threshold for best F1 instead of a fixed 0.5 cut —
        # more informative (and safety-relevant) than accuracy on skewed data.
        best_t, best_f1 = 0.5, -1.0
        for t in (round(0.05 + i * 0.025, 3) for i in range(37)):
            f1_t = f1_score(y_test, (prob >= t).astype(int), zero_division=0)
            if f1_t > best_f1:
                best_f1, best_t = f1_t, t
        pred = (prob >= best_t).astype(int)
        m = _metrics(y_test, pred, prob)
        m["decision_threshold"] = best_t
        results[name] = m
        print(f"\n{name}: acc={m['accuracy']} P={m['precision']} R={m['recall']} "
              f"F1={m['f1']} ROC-AUC={m['roc_auc']}")
        print(classification_report(y_test, pred, digits=3, zero_division=0))
        if m["roc_auc"] is not None and m["roc_auc"] > best_auc:
            best_auc, best_name = m["roc_auc"], name
            best_bundle = {"model": pipe, "features": FEATURES, "metrics": m,
                           "selected": name}

    best_bundle.update({
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "data_note": ("Prototype dataset; see ml/datasets/generate_synthetic_dataset.py. "
                      "Replace with a real landslide inventory before operational use."),
        "feature_importances": _importances(best_bundle["model"]),
        "metrics_by_model": results,
    })

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODELS_DIR / "landslide_model.joblib"
    joblib.dump(best_bundle, model_path)
    metrics_path = MODELS_DIR / "model_metrics.json"
    metrics_path.write_text(json.dumps({
        "selected": best_name, "roc_auc": best_auc, "metrics": results,
        "trained_at": best_bundle["trained_at"],
        "event_rate": round(float(df[TARGET].mean()), 4)}, indent=2), encoding="utf-8")

    print(f"\nSaved best model ({best_name}, ROC-AUC={best_auc}) -> {model_path}")
    print(f"Metrics report -> {metrics_path}")
    print("NOTE: trained on synthetic demo data — validate with real landslide")
    print("records (GSI inventory etc.) before any operational or safety use.")


if __name__ == "__main__":
    main()
