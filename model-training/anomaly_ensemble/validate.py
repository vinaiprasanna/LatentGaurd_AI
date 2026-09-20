"""
Evaluate the anomaly ensemble on unseen lots.

This intentionally splits by lot so lot-relative features from validation data are
not used to fit the training model or its scaler.
"""
import json
import os
import sys
import pickle

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score

TRAINING_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(TRAINING_ROOT)
SRC_DIR = os.path.join(TRAINING_ROOT, "src")
sys.path.insert(0, TRAINING_ROOT)
sys.path.insert(0, SRC_DIR)

from src.features import build_dut_features, get_model_feature_columns
from src.anomaly_ensemble import HybridAnomalyEnsemble

DATA_PATH = os.path.join(TRAINING_ROOT, "data", "large_physics_calibrated_burnin_dataset.csv")
OUTPUT_PATH = os.path.join(REPO_ROOT, "backend", "models", "validation_metrics.json")


def validate(data_path=DATA_PATH, output_path=OUTPUT_PATH):
    raw_df = pd.read_csv(data_path)
    raw_df = raw_df[raw_df["checkpoint_h"] < 168].copy()
    lots = sorted(raw_df["lot_id"].astype(str).unique())
    holdout_lots = lots[::5]
    train_lots = [lot for lot in lots if lot not in holdout_lots]

    train_raw = raw_df[raw_df["lot_id"].astype(str).isin(train_lots)]
    valid_raw = raw_df[raw_df["lot_id"].astype(str).isin(holdout_lots)]
    train_df = build_dut_features(train_raw)
    valid_df = build_dut_features(valid_raw)
    feature_cols = get_model_feature_columns(train_df)

    train_x = train_df[feature_cols].fillna(0).values
    valid_x = valid_df.reindex(columns=feature_cols, fill_value=0).fillna(0).values
    train_y = train_df["true_latent_defect"].astype(int).values
    valid_y = valid_df["true_latent_defect"].astype(int).values

    model = HybridAnomalyEnsemble()
    model.fit(train_x, train_y)
    scores = model.score(valid_x)
    anomaly_scores = scores["anomaly_ensemble_score"]

    threshold_rows = []
    for threshold in [round(value, 2) for value in np.arange(0.10, 0.91, 0.05)]:
        valid_pred = (anomaly_scores >= threshold).astype(int)
        matrix = confusion_matrix(valid_y, valid_pred, labels=[0, 1])
        threshold_rows.append({
            "threshold": threshold,
            "accuracy": round(float(accuracy_score(valid_y, valid_pred)), 4),
            "precision": round(float(precision_score(valid_y, valid_pred, zero_division=0)), 4),
            "recall": round(float(recall_score(valid_y, valid_pred, zero_division=0)), 4),
            "f1": round(float(f1_score(valid_y, valid_pred, zero_division=0)), 4),
            "false_negative_rate": round(float(matrix[1, 0] / max(matrix[1].sum(), 1)), 4),
        })

    eligible = [row for row in threshold_rows if row["precision"] >= 0.95]
    selected = max(eligible, key=lambda row: (row["recall"], row["f1"], -row["threshold"]))
    valid_pred = (anomaly_scores >= selected["threshold"]).astype(int)
    matrix = confusion_matrix(valid_y, valid_pred, labels=[0, 1])

    metrics = {
        "available": True,
        "evaluation_scope": "lot-level holdout; model trained on 16 lots and evaluated on 4 unseen lots",
        "train_lots": train_lots,
        "holdout_lots": holdout_lots,
        "train_duts": int(len(train_df)),
        "holdout_duts": int(len(valid_df)),
        "feature_count": len(feature_cols),
        "threshold": selected["threshold"],
        "threshold_policy": "highest recall with precision >= 0.95",
        "accuracy": selected["accuracy"],
        "precision": selected["precision"],
        "recall": selected["recall"],
        "f1": selected["f1"],
        "false_negative_rate": round(float(matrix[1, 0] / max(matrix[1].sum(), 1)), 4),
        "confusion_matrix": matrix.tolist(),
        "threshold_sweep": threshold_rows,
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)
    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    validate()
