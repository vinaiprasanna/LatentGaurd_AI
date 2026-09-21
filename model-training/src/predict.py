"""
BurnInGuard AI 2.0 -- Prediction Script
========================================
Loads raw telemetry CSV (prediction_input.csv), runs the trained
model, and outputs PASS/FAIL predictions.

Usage:
    python src/predict.py --train          Train model + predict
    python src/predict.py                  Predict using saved model
    python src/predict.py --model-path m   Use custom model path
"""
import os
import sys
import pickle
import argparse
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, "src")
DATA_DIR = os.path.join(ROOT, "data")
OUT_DIR = os.path.join(ROOT, "outputs")
MODEL_DIR = os.path.join(ROOT, "models")
TESTS_DIR = os.path.join(ROOT, "tests")

sys.path.insert(0, SRC_DIR)

from features import build_dut_features, get_model_feature_columns, PARAMS
from anomaly_ensemble import HybridAnomalyEnsemble
from drift_model import DriftPredictor
from risk_engine import compute_risk, RISK_WEIGHTS, RISK_BANDS
from explainability import explain_row
from digital_twin import project_trajectory, remaining_margin
from data_generator import STATIC_LIMITS, CHECKPOINTS_H

MODEL_PATH = os.path.join(MODEL_DIR, "burnin_guard_model.pkl")
FEATURES_PATH = os.path.join(MODEL_DIR, "model_metadata.pkl")
PREDICTION_INPUT = os.path.join(TESTS_DIR, "prediction_input.csv")
PREDICTION_OUTPUT = os.path.join(TESTS_DIR, "prediction_output.csv")


def train_and_save():
    from pipeline import run_pipeline
    print("[1/3] Training model via pipeline ...")
    run_pipeline(verbose=True)

    results_path = os.path.join(OUT_DIR, "results.csv")
    dut_df = pd.read_csv(results_path)
    raw_df = pd.read_csv(os.path.join(DATA_DIR, "synthetic_burnin_data.csv"))
    dut_df = build_dut_features(raw_df)
    feature_cols = get_model_feature_columns(dut_df)

    print("[2/3] Saving models and metadata ...")
    os.makedirs(MODEL_DIR, exist_ok=True)

    ensemble = HybridAnomalyEnsemble()
    X = dut_df[feature_cols].fillna(0).values
    y = dut_df["true_latent_defect"].values if "true_latent_defect" in dut_df.columns else None
    ensemble.fit(X, y)

    early_feature_cols = [c for c in feature_cols if "_0h" in c or "physics_norm_slope" in c
                          or "arrhenius" in c or "temperature" in c or "_lot_zscore" in c]
    drift_models = {}
    for p in PARAMS:
        target_col = f"{p}_last"
        y_drift = dut_df[target_col].values
        Xp = dut_df[early_feature_cols].fillna(0).values
        model = DriftPredictor(p)
        model.fit(Xp, y_drift)
        drift_models[p] = model

    model_bundle = {
        "ensemble": ensemble,
        "drift_models": drift_models,
        "feature_cols": feature_cols,
        "early_feature_cols": early_feature_cols,
        "static_limits": STATIC_LIMITS,
        "param_list": PARAMS,
        "risk_weights": RISK_WEIGHTS,
        "risk_bands": RISK_BANDS,
    }

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model_bundle, f)

    metadata = {
        "feature_cols": feature_cols,
        "early_feature_cols": early_feature_cols,
        "static_limits": STATIC_LIMITS,
        "param_list": PARAMS,
    }
    with open(FEATURES_PATH, "wb") as f:
        pickle.dump(metadata, f)

    print(f"      Model saved to {MODEL_PATH}")
    print(f"      Metadata saved to {FEATURES_PATH}")
    print("[3/3] Training complete.")
    return model_bundle


def load_model():
    if not os.path.exists(MODEL_PATH):
        print("No saved model found. Training first ...")
        return train_and_save()
    with open(MODEL_PATH, "rb") as f:
        model_bundle = pickle.load(f)
    print(f"Loaded model from {MODEL_PATH}")
    return model_bundle


def predict():
    if not os.path.exists(PREDICTION_INPUT):
        print(f"Error: {PREDICTION_INPUT} not found.")
        print("Create the file with raw telemetry data (columns: dut_id, lot_id, checkpoint_h,")
        print("temperature_c, vcc_v, iddq_uA, leakage_uA, delay_ns, status)")
        return None

    print(f"Loading prediction input from {PREDICTION_INPUT} ...")
    input_df = pd.read_csv(PREDICTION_INPUT)
    print(f"  {len(input_df)} rows, {input_df['dut_id'].nunique()} DUTs")

    model_bundle = load_model()
    feature_cols = model_bundle["feature_cols"]
    early_feature_cols = model_bundle["early_feature_cols"]
    static_limits = model_bundle["static_limits"]
    param_list = model_bundle["param_list"]

    print("[1/5] Engineering features ...")
    dut_df = build_dut_features(input_df)

    missing = [c for c in feature_cols if c not in dut_df.columns]
    if missing:
        print(f"  Warning: missing feature columns: {missing}")
        for col in missing:
            dut_df[col] = 0.0

    X = dut_df[feature_cols].fillna(0).values

    print("[2/5] Running anomaly ensemble ...")
    ensemble = model_bundle["ensemble"]
    scores = ensemble.score(X)
    for k, v in scores.items():
        dut_df[k] = v

    print("[3/5] Running drift prediction ...")
    for p in param_list:
        target_col = f"{p}_last"
        if target_col not in dut_df.columns:
            continue
        y_drift = dut_df[target_col].values
        Xp = dut_df[early_feature_cols].fillna(0).values
        model = model_bundle["drift_models"][p]
        preds = model.predict(Xp)
        for k, v in preds.items():
            dut_df[k] = v

    print("[4/5] Running digital twin projection ...")
    twin_records = []
    for _, row in dut_df.iterrows():
        rec = {"dut_id": row["dut_id"]}
        for p in param_list:
            proj = project_trajectory(
                v0=row[f"{p}_0h"],
                physics_norm_slope=row[f"{p}_physics_norm_slope"],
                accel_factor=row["arrhenius_accel_factor"],
            )
            margin_500h = remaining_margin(proj, static_limits[p], 500)
            rec[f"{p}_projected_500h"] = margin_500h["projected_value"]
            rec[f"{p}_margin_pct_500h"] = margin_500h["margin_pct"]
        twin_records.append(rec)
    twin_df = pd.DataFrame(twin_records)
    dut_df = dut_df.merge(twin_df, on="dut_id", how="left")

    print("[5/5] Computing risk scores and PASS/FAIL ...")
    dut_df = compute_risk(dut_df, static_limits, param_list)
    dut_df["explanation"] = dut_df.apply(explain_row, axis=1)

    dut_df["predicted_outcome"] = dut_df["risk_band"].apply(
        lambda band: "FAIL" if band in ("HIGH", "CRITICAL") else "PASS"
    )

    output_cols = [
        "dut_id", "lot_id", "temperature_c", "arrhenius_accel_factor",
        "anomaly_ensemble_score", "anomaly_ensemble_confidence",
        "risk_score", "risk_band", "risk_confidence_pct",
        "predicted_outcome", "explanation"
    ]
    available_cols = [c for c in output_cols if c in dut_df.columns]
    output_df = dut_df[available_cols].copy()

    output_df.to_csv(PREDICTION_OUTPUT, index=False)
    print(f"\n{'='*60}")
    print(f"Predictions saved to {PREDICTION_OUTPUT}")
    print(f"{'='*60}")
    print(f"\nSummary:")
    print(f"  Total DUTs:     {len(output_df)}")
    print(f"  PASS:           {(output_df['predicted_outcome'] == 'PASS').sum()}")
    print(f"  FAIL:           {(output_df['predicted_outcome'] == 'FAIL').sum()}")
    print(f"\nFull results:")
    print(output_df.to_string(index=False))

    return dut_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BurnInGuard AI -- PASS/FAIL Prediction")
    parser.add_argument("--train", action="store_true", help="Retrain model before predicting")
    parser.add_argument("--model-path", type=str, default=None, help="Path to model pickle")
    args = parser.parse_args()

    if args.train:
        train_and_save()

    predict()
