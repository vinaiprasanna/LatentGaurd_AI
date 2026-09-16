"""
BurnInGuard AI 2.0 -- Anomaly Ensemble Training
=====================================================
Trains the hybrid anomaly ensemble (XGBoost + Random Forest + PCA-SPC)
and exports the model.
"""
import os
import sys
import pickle
import pandas as pd
import numpy as np

TRAINING_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(TRAINING_ROOT)
SRC_DIR = os.path.join(TRAINING_ROOT, "src")
sys.path.insert(0, TRAINING_ROOT)
sys.path.insert(0, SRC_DIR)

from src.features import build_dut_features, get_model_feature_columns, PARAMS
from src.anomaly_ensemble import HybridAnomalyEnsemble
from src.data_generator import STATIC_LIMITS

MODEL_PATH = os.path.join(REPO_ROOT, "backend", "models")


def train(data_path=None):
    print("Loading data ...")
    if data_path:
        raw_df = pd.read_csv(data_path)
    else:
        raw_df = pd.read_csv(os.path.join(TRAINING_ROOT, "data", "large_physics_calibrated_burnin_dataset.csv"))

    print(f"  {len(raw_df)} rows, {raw_df['dut_id'].nunique()} DUTs")

    print("Engineering features ...")
    dut_df = build_dut_features(raw_df)
    feature_cols = get_model_feature_columns(dut_df)
    print(f"  {len(feature_cols)} feature columns")

    print("Training anomaly ensemble ...")
    X = dut_df[feature_cols].fillna(0).values
    y = dut_df["true_latent_defect"].values if "true_latent_defect" in dut_df.columns else None

    ensemble = HybridAnomalyEnsemble()
    ensemble.fit(X, y)
    scores = ensemble.score(X)
    print(f"  Anomaly ensemble score mean: {scores['anomaly_ensemble_score'].mean():.4f}")

    os.makedirs(MODEL_PATH, exist_ok=True)
    model_path = os.path.join(MODEL_PATH, "anomaly_ensemble_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(ensemble, f)
    print(f"Model saved to {model_path}")

    return ensemble, feature_cols


def export(data_path=None):
    ensemble, feature_cols = train(data_path)
    return ensemble, feature_cols


if __name__ == "__main__":
    train()
