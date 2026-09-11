"""
BurnInGuard AI 2.0 -- Simple Prediction Test
=============================================
Read prediction_input.csv and output PASS/FAIL predictions.

Usage:
    python tests/test.py

    If no trained model exists, it auto-trains on the synthetic data
    first. Then loads prediction_input.csv and predicts.

    To add your own data: edit tests/prediction_input.csv
    Columns needed: dut_id, lot_id, checkpoint_h, temperature_c,
    vcc_v, iddq_uA, leakage_uA, delay_ns
"""
import os
import sys
import pickle
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, "src")
MODEL_DIR = os.path.join(ROOT, "models")
TESTS_DIR = os.path.join(ROOT, "tests")

sys.path.insert(0, SRC_DIR)

from features import build_dut_features, get_model_feature_columns, PARAMS
from explainability import explain_row
from digital_twin import project_trajectory, remaining_margin
from data_generator import STATIC_LIMITS

MODEL_PATH = os.path.join(MODEL_DIR, "burnin_guard_model.pkl")
INPUT_PATH = os.path.join(TESTS_DIR, "prediction_input.csv")
OUTPUT_PATH = os.path.join(TESTS_DIR, "prediction_output.csv")


def load_model():
    if not os.path.exists(MODEL_PATH):
        print("No trained model found. Training now...")
        train_model()
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


def train_model():
    sys.path.insert(0, os.path.join(ROOT, "src"))
    from pipeline import run_pipeline
    from features import build_dut_features, get_model_feature_columns, PARAMS
    from anomaly_ensemble import HybridAnomalyEnsemble
    from drift_model import DriftPredictor

    print("Training model...")
    run_pipeline(verbose=True)

    results_path = os.path.join(ROOT, "outputs", "results.csv")
    raw_path = os.path.join(ROOT, "data", "synthetic_burnin_data.csv")
    dut_df = build_dut_features(pd.read_csv(raw_path))
    feature_cols = get_model_feature_columns(dut_df)

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

    os.makedirs(MODEL_DIR, exist_ok=True)
    model_bundle = {
        "ensemble": ensemble,
        "drift_models": drift_models,
        "feature_cols": feature_cols,
        "early_feature_cols": early_feature_cols,
        "static_limits": STATIC_LIMITS,
        "param_list": PARAMS,
        "risk_weights": {"anomaly": 0.40, "lot_deviation": 0.20, "drift_rate": 0.20, "future_margin": 0.20},
        "risk_bands": [(0, 30, "LOW"), (30, 60, "MEDIUM"), (60, 80, "HIGH"), (80, 101, "CRITICAL")],
    }
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model_bundle, f)
    print(f"Model saved to {MODEL_PATH}")


def predict():
    if not os.path.exists(INPUT_PATH):
        print(f"Error: {INPUT_PATH} not found.")
        sys.exit(1)

    model = load_model()
    feature_cols = model["feature_cols"]
    early_feature_cols = model["early_feature_cols"]
    static_limits = model["static_limits"]
    param_list = model["param_list"]
    ensemble = model["ensemble"]
    drift_models = model["drift_models"]

    # Load and process input
    input_df = pd.read_csv(INPUT_PATH)
    dut_df = build_dut_features(input_df)

    # Fill missing feature columns
    missing = [c for c in feature_cols if c not in dut_df.columns]
    for col in missing:
        dut_df[col] = 0.0

    X = dut_df[feature_cols].fillna(0).values

    # Anomaly ensemble scores
    scores = ensemble.score(X)
    for k, v in scores.items():
        dut_df[k] = v

    # Drift predictions
    for p in param_list:
        target_col = f"{p}_last"
        if target_col not in dut_df.columns:
            continue
        y_drift = dut_df[target_col].values
        Xp = dut_df[early_feature_cols].fillna(0).values
        preds = drift_models[p].predict(Xp)
        for k, v in preds.items():
            dut_df[k] = v

    # Digital twin projection
    twin_records = []
    for _, row in dut_df.iterrows():
        rec = {"dut_id": row["dut_id"]}
        for p in param_list:
            proj = project_trajectory(
                v0=row[f"{p}_0h"],
                physics_norm_slope=row[f"{p}_physics_norm_slope"],
                accel_factor=row["arrhenius_accel_factor"],
            )
            margin = remaining_margin(proj, static_limits[p], 500)
            rec[f"{p}_projected_500h"] = margin["projected_value"]
            rec[f"{p}_margin_pct_500h"] = margin["margin_pct"]
        twin_records.append(rec)
    twin_df = pd.DataFrame(twin_records)
    dut_df = dut_df.merge(twin_df, on="dut_id", how="left")

    # Risk computation and PASS/FAIL
    dut_df = compute_risk_simple(
        dut_df, static_limits, param_list,
        model["risk_weights"], model["risk_bands"]
    )

    # Final predictions
    dut_df["predicted_outcome"] = dut_df["risk_band"].apply(
        lambda b: "FAIL" if b in ("HIGH", "CRITICAL") else "PASS"
    )
    dut_df["explanation"] = dut_df.apply(explain_row, axis=1)

    # Output
    output = dut_df[[
        "dut_id", "lot_id", "risk_score", "risk_band",
        "risk_confidence_pct", "predicted_outcome", "explanation"
    ]].copy()
    output.to_csv(OUTPUT_PATH, index=False)

    print(f"\n{'='*50}")
    print(f"  Prediction Results  ({len(output)} DUTs)")
    print(f"{'='*50}")
    print(f"\n  PASS : {(output['predicted_outcome'] == 'PASS').sum()}")
    print(f"  FAIL : {(output['predicted_outcome'] == 'FAIL').sum()}")
    print(f"\n{'─'*50}")
    for _, row in output.iterrows():
        marker = " FAIL" if row["predicted_outcome"] == "FAIL" else " PASS"
        print(f"  {row['dut_id']}  |  risk={row['risk_score']:5.1f}  |  {row['risk_band']:8s}  |  {marker}  |  {row['explanation']}")
    print(f"{'='*50}")
    print(f"\nResults saved to: {OUTPUT_PATH}")


def compute_risk_simple(dut_df, static_limits, param_list, risk_weights, risk_bands):
    """Inline risk computation matching the pipeline logic."""
    df = dut_df.copy()

    anomaly_component = df["anomaly_ensemble_score"]

    zscore_cols = [c for c in df.columns if c.endswith("_last_lot_zscore")]
    lot_dev_raw = df[zscore_cols].abs().max(axis=1) if zscore_cols else pd.Series(0, index=df.index)
    lot_dev_component = _minmax(lot_dev_raw)

    slope_cols = [c for c in df.columns if c.endswith("_physics_norm_slope")]
    drift_raw = df[slope_cols].abs().max(axis=1) if slope_cols else pd.Series(0, index=df.index)
    drift_component = _minmax(drift_raw)

    margin_scores = []
    for p in param_list:
        pred_hi_col = f"{p}_pred_168h_hi"
        if pred_hi_col in df.columns and p in static_limits:
            proximity = (df[pred_hi_col] / static_limits[p]).clip(lower=0)
            margin_scores.append(proximity)
    if margin_scores:
        future_margin_raw = pd.concat(margin_scores, axis=1).max(axis=1)
        future_margin_component = _minmax(future_margin_raw)
    else:
        future_margin_component = pd.Series(0, index=df.index)

    w = risk_weights
    risk_0_1 = (
        w["anomaly"] * anomaly_component
        + w["lot_deviation"] * lot_dev_component
        + w["drift_rate"] * drift_component
        + w["future_margin"] * future_margin_component
    )
    df["risk_score"] = (risk_0_1 * 100).round(1)

    def _band(score):
        for lo, hi, name in risk_bands:
            if lo <= score < hi:
                return name
        return "CRITICAL"

    df["risk_band"] = df["risk_score"].apply(_band)
    df["risk_confidence_pct"] = 95.0
    df["_component_anomaly"] = anomaly_component.round(3)
    df["_component_lot_deviation"] = lot_dev_component.round(3)
    df["_component_drift_rate"] = drift_component.round(3)
    df["_component_future_margin"] = future_margin_component.round(3)

    return df


def _minmax(s):
    s = np.asarray(s, dtype=float)
    lo, hi = np.percentile(s, 1), np.percentile(s, 99)
    if hi - lo < 1e-9:
        return np.zeros_like(s)
    return np.clip((s - lo) / (hi - lo), 0, 1)


if __name__ == "__main__":
    predict()
