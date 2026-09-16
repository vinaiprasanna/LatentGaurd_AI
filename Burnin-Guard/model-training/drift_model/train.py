"""
BurnInGuard AI 2.0 -- Drift Model Training
===================================================
Trains per-parameter XGBoost drift predictors and exports the model.
"""
import os
import sys
import pickle
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_DIR = os.path.join(ROOT, "src")
sys.path.insert(0, SRC_DIR)

from features import build_dut_features, get_model_feature_columns, PARAMS
from drift_model import DriftPredictor

MODEL_PATH = os.path.join(ROOT, "backend", "models")


def train(data_path=None):
    print("Loading data ...")
    if data_path:
        raw_df = pd.read_csv(data_path)
    else:
        raw_df = pd.read_csv(os.path.join(ROOT, "data", "large_physics_calibrated_burnin_dataset.csv"))

    print(f"  {len(raw_df)} rows, {raw_df['dut_id'].nunique()} DUTs")

    print("Engineering features ...")
    dut_df = build_dut_features(raw_df)
    feature_cols = get_model_feature_columns(dut_df)

    early_feature_cols = [c for c in feature_cols if "_0h" in c or "physics_norm_slope" in c
                           or "arrhenius" in c or "temperature" in c or "_lot_zscore" in c]

    print("Training drift models ...")
    drift_models = {}
    for p in PARAMS:
        target_col = f"{p}_last"
        y_drift = dut_df[target_col].values
        Xp = dut_df[early_feature_cols].fillna(0).values
        model = DriftPredictor(p)
        model.fit(Xp, y_drift)
        drift_models[p] = model
        print(f"  {p}: trained on {len(early_feature_cols)} features")

    os.makedirs(MODEL_PATH, exist_ok=True)
    model_path = os.path.join(MODEL_PATH, "drift_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(drift_models, f)
    print(f"Model saved to {model_path}")

    return drift_models, feature_cols, early_feature_cols


def export(data_path=None):
    return train(data_path)


if __name__ == "__main__":
    train()
