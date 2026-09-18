"""
BurnInGuard AI 2.0 -- Backend Prediction Module
================================================
Loads exported models and provides prediction functionality.
"""
import os
import sys
import pickle
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT, "src")
MODELS_DIR = os.path.join(ROOT, "models")
sys.path.insert(0, SRC_DIR)

from features import build_dut_features, get_model_feature_columns, PARAMS, get_drift_input_rows
from explainability import explain_row
from digital_twin import project_trajectory, remaining_margin
from data_generator import STATIC_LIMITS

ANOMALY_MODEL_PATH = os.path.join(MODELS_DIR, "anomaly_ensemble_model.pkl")
DRIFT_MODEL_PATH = os.path.join(MODELS_DIR, "drift_model.pkl")
OUTPUT_PATH = os.path.join(ROOT, "outputs", "prediction_output.csv")


def load_models():
    with open(ANOMALY_MODEL_PATH, "rb") as f:
        ensemble = pickle.load(f)
    with open(DRIFT_MODEL_PATH, "rb") as f:
        drift_models = pickle.load(f)
    return ensemble, drift_models


def predict(input_csv=None, output_csv=None):
    ensemble, drift_models = load_models()

    if input_csv:
        input_df = pd.read_csv(input_csv)
    else:
        input_csv = os.path.join(ROOT, "prediction_input.csv")
        input_df = pd.read_csv(input_csv)

    if input_df.empty:
        print("Error: No input data found.")
        return None

    print(f"Loaded {len(input_df)} rows, {input_df['dut_id'].nunique()} DUTs")

    dut_df = build_dut_features(input_df)
    feature_cols = get_model_feature_columns(dut_df)

    missing = [c for c in feature_cols if c not in dut_df.columns]
    for col in missing:
        dut_df[col] = 0.0

    X = dut_df[feature_cols].fillna(0).values

    # Anomaly ensemble scores
    scores = ensemble.score(X)
    for k, v in scores.items():
        dut_df[k] = v

    # Drift predictions: only the early burn-in signal set is valid as input.
    drift_input_df = build_dut_features(get_drift_input_rows(input_df))
    drift_feature_cols = get_model_feature_columns(drift_input_df)
    early_feature_cols = [c for c in drift_feature_cols if "_0h" in c or "physics_norm_slope" in c
                           or "arrhenius" in c or "temperature" in c or "_lot_zscore" in c]
    for p in PARAMS:
        target_col = f"{p}_last"
        if target_col not in dut_df.columns:
            continue
        y_drift = dut_df[target_col].values
        Xp = drift_input_df[early_feature_cols].fillna(0).values
        preds = drift_models[p].predict(Xp)
        for k, v in preds.items():
            dut_df[k] = v

    # Digital twin projection
    twin_records = []
    for _, row in dut_df.iterrows():
        rec = {"dut_id": row["dut_id"]}
        for p in PARAMS:
            proj = project_trajectory(
                v0=row[f"{p}_0h"],
                physics_norm_slope=row[f"{p}_physics_norm_slope"],
                accel_factor=row["arrhenius_accel_factor"],
            )
            margin = remaining_margin(proj, STATIC_LIMITS[p], 500)
            rec[f"{p}_projected_500h"] = margin["projected_value"]
            rec[f"{p}_margin_pct_500h"] = margin["margin_pct"]
        twin_records.append(rec)
    twin_df = pd.DataFrame(twin_records)
    dut_df = dut_df.merge(twin_df, on="dut_id", how="left")

    # Risk computation
    from risk_engine import compute_risk
    dut_df = compute_risk(dut_df, STATIC_LIMITS, PARAMS)
    dut_df["explanation"] = dut_df.apply(explain_row, axis=1)

    # Predictions
    dut_df["predicted_outcome"] = dut_df["risk_band"].apply(
        lambda b: "FAIL" if b in ("HIGH", "CRITICAL") else "PASS"
    )

    # Output
    output_cols = [
        "dut_id", "lot_id", "risk_score", "risk_band",
        "risk_confidence_pct", "predicted_outcome", "explanation"
    ]
    available_cols = [c for c in output_cols if c in dut_df.columns]
    output_df = dut_df[available_cols].copy()

    if output_csv:
        out_path = output_csv
    else:
        out_path = OUTPUT_PATH
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    output_df.to_csv(out_path, index=False)

    print(f"\n{'='*50}")
    print(f"  Prediction Results  ({len(output_df)} DUTs)")
    print(f"{'='*50}")
    print(f"\n  PASS : {(output_df['predicted_outcome'] == 'PASS').sum()}")
    print(f"  FAIL : {(output_df['predicted_outcome'] == 'FAIL').sum()}")
    print(f"\n{'─'*50}")
    for _, row in output_df.iterrows():
        marker = " FAIL" if row["predicted_outcome"] == "FAIL" else " PASS"
        print(f"  {row['dut_id']}  |  risk={row['risk_score']:5.1f}  |  {row['risk_band']:8s}  |  {marker}")
    print(f"{'='*50}")
    print(f"\nResults saved to: {out_path}")
    return output_df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="BurnInGuard AI -- PASS/FAIL Prediction")
    parser.add_argument("--input", type=str, default=None, help="Path to input CSV")
    parser.add_argument("--output", type=str, default=None, help="Path to output CSV")
    args = parser.parse_args()
    predict(input_csv=args.input, output_csv=args.output)
