"""
BurnInGuard AI 2.0 -- Drift Model Export
================================================
Loads raw data, trains drift models, and exports to backend/models/drift_model.pkl
"""
import os
import sys
import pickle
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_DIR = os.path.join(ROOT, "src")
sys.path.insert(0, SRC_DIR)

from features import build_dut_features, get_model_feature_columns, PARAMS, get_drift_input_rows
from drift_model import DriftPredictor

BACKEND_MODELS = os.path.join(ROOT, "backend", "models")


def export(data_path=None):
    print("Training drift models ...")
    if data_path:
        raw_df = pd.read_csv(data_path)
    else:
        raw_df = pd.read_csv(os.path.join(ROOT, "data", "large_physics_calibrated_burnin_dataset.csv"))

    print(f"  {len(raw_df)} rows, {raw_df['dut_id'].nunique()} DUTs")

    early_df = get_drift_input_rows(raw_df)
    dut_df = build_dut_features(early_df)
    target_df = build_dut_features(raw_df)
    feature_cols = get_model_feature_columns(dut_df)

    early_feature_cols = [c for c in feature_cols if "_0h" in c or "physics_norm_slope" in c
                           or "arrhenius" in c or "temperature" in c or "_lot_zscore" in c]

    print("Training drift models ...")
    drift_models = {}
    for p in PARAMS:
        target_col = f"{p}_last"
        y_drift = target_df[target_col].values
        Xp = dut_df[early_feature_cols].fillna(0).values
        model = DriftPredictor(p)
        model.fit(Xp, y_drift)
        drift_models[p] = model
        print(f"  {p}: trained on {len(early_feature_cols)} features")

    os.makedirs(BACKEND_MODELS, exist_ok=True)
    model_path = os.path.join(BACKEND_MODELS, "drift_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(drift_models, f)
    print(f"Exported to {model_path}")
    return drift_models, feature_cols, early_feature_cols


if __name__ == "__main__":
    export()
