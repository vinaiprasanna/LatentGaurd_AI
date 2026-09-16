"""
BurnInGuard AI 2.0 -- Anomaly Ensemble Export
================================================
Loads raw data, trains the anomaly ensemble, and exports
the model to backend/models/anomaly_ensemble_model.pkl
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
from anomaly_ensemble import HybridAnomalyEnsemble

BACKEND_MODELS = os.path.join(ROOT, "backend", "models")


def export(data_path=None):
    print("Training anomaly ensemble ...")
    if data_path:
        raw_df = pd.read_csv(data_path)
    else:
        raw_df = pd.read_csv(os.path.join(ROOT, "data", "large_physics_calibrated_burnin_dataset.csv"))

    dut_df = build_dut_features(raw_df)
    feature_cols = get_model_feature_columns(dut_df)

    X = dut_df[feature_cols].fillna(0).values
    y = dut_df["true_latent_defect"].values if "true_latent_defect" in dut_df.columns else None

    ensemble = HybridAnomalyEnsemble()
    ensemble.fit(X, y)
    scores = ensemble.score(X)
    print(f"  Anomaly ensemble score mean: {scores['anomaly_ensemble_score'].mean():.4f}")

    os.makedirs(BACKEND_MODELS, exist_ok=True)
    model_path = os.path.join(BACKEND_MODELS, "anomaly_ensemble_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(ensemble, f)
    print(f"Exported to {model_path}")
    return ensemble, feature_cols


if __name__ == "__main__":
    export()
