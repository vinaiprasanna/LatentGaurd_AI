"""
Evaluate drift forecasting on unseen lots.

The split is by lot and uses only early checkpoints as model inputs. The measured
168h checkpoint remains the target, so no future telemetry leaks into features.
"""
import json
import os
import sys
import pickle

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

TRAINING_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(TRAINING_ROOT)
SRC_DIR = os.path.join(TRAINING_ROOT, "src")
sys.path.insert(0, TRAINING_ROOT)
sys.path.insert(0, SRC_DIR)

from src.features import build_dut_features, get_model_feature_columns, PARAMS, get_drift_input_rows
from src.drift_model import DriftPredictor

DATA_PATH = os.path.join(TRAINING_ROOT, "data", "large_physics_calibrated_burnin_dataset.csv")
OUTPUT_PATH = os.path.join(REPO_ROOT, "backend", "models", "drift_validation_metrics.json")


def _early_feature_columns(columns):
    return [c for c in columns if "_0h" in c or "physics_norm_slope" in c
            or "arrhenius" in c or "temperature" in c or "_lot_zscore" in c]


def validate(data_path=DATA_PATH, output_path=OUTPUT_PATH):
    raw_df = pd.read_csv(data_path)
    lots = sorted(raw_df["lot_id"].astype(str).unique())
    holdout_lots = lots[::5]
    train_lots = [lot for lot in lots if lot not in holdout_lots]

    train_raw = raw_df[raw_df["lot_id"].astype(str).isin(train_lots)]
    valid_raw = raw_df[raw_df["lot_id"].astype(str).isin(holdout_lots)]
    train_early = build_dut_features(get_drift_input_rows(train_raw))
    valid_early = build_dut_features(get_drift_input_rows(valid_raw))
    train_target = build_dut_features(train_raw)
    valid_target = build_dut_features(valid_raw)

    feature_cols = _early_feature_columns(get_model_feature_columns(train_early))
    train_x = train_early[feature_cols].fillna(0).values
    valid_x = valid_early.reindex(columns=feature_cols, fill_value=0).fillna(0).values
    metrics = {
        "available": True,
        "evaluation_scope": "lot-level holdout; model trained on 16 lots and evaluated on 4 unseen lots",
        "train_lots": train_lots,
        "holdout_lots": holdout_lots,
        "train_duts": int(len(train_target)),
        "holdout_duts": int(len(valid_target)),
        "feature_count": len(feature_cols),
        "parameters": {},
    }

    for parameter in PARAMS:
        target = valid_target[f"{parameter}_last"].astype(float).to_numpy()
        model = DriftPredictor(parameter)
        model.fit(train_x, train_target[f"{parameter}_last"].astype(float).to_numpy())
        prediction = model.predict(valid_x)
        mean = np.asarray(prediction[f"{parameter}_pred_168h"], dtype=float)
        lower = np.asarray(prediction[f"{parameter}_pred_168h_lo"], dtype=float)
        upper = np.asarray(prediction[f"{parameter}_pred_168h_hi"], dtype=float)
        metrics["parameters"][parameter] = {
            "mae": round(float(mean_absolute_error(target, mean)), 4),
            "rmse": round(float(np.sqrt(mean_squared_error(target, mean))), 4),
            "r2": round(float(r2_score(target, mean)), 4),
            "interval_coverage": round(float(np.mean((target >= lower) & (target <= upper))), 4),
            "mean_interval_width": round(float(np.mean(upper - lower)), 4),
        }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)
    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    validate()
