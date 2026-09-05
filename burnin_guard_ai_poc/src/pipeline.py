"""
BurnInGuard AI 2.0 -- End-to-End PoC Pipeline
------------------------------------------------
Run this to regenerate everything the dashboard reads:

    python src/pipeline.py

Stages:
  1. Generate synthetic burn-in telemetry
  2. Physics-informed + statistical feature engineering
  3. Hybrid ensemble anomaly detection
  4. Physics-informed drift prediction (XGBoost + quantile intervals)
  5. Digital twin projection (500h / 1000h "what-if")
  6. Bayesian-style risk fusion
  7. Explainability (SHAP or fallback) + plain-language reasons
  8. Write results.csv + audit_log.csv for the Streamlit dashboard
"""
import os
import sys
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))

from data_generator import generate_dataset, STATIC_LIMITS, CHECKPOINTS_H  # noqa: E402
from features import build_dut_features, get_model_feature_columns, PARAMS  # noqa: E402
from anomaly_ensemble import HybridAnomalyEnsemble  # noqa: E402
from drift_model import DriftPredictor  # noqa: E402
from risk_engine import compute_risk  # noqa: E402
from explainability import explain_row, shap_summary  # noqa: E402
from digital_twin import project_trajectory, remaining_margin  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
OUT_DIR = os.path.join(ROOT, "outputs")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)


def run_pipeline(n_lots=8, duts_per_lot=45, anomaly_fraction=0.09, seed=42, verbose=True):
    log = lambda msg: print(msg) if verbose else None  # noqa: E731

    # ---------------------------------------------------------------
    # 1. Data generation
    # ---------------------------------------------------------------
    log("[1/8] Generating synthetic burn-in telemetry ...")
    raw_df = generate_dataset(n_lots=n_lots, duts_per_lot=duts_per_lot,
                               anomaly_fraction=anomaly_fraction, seed=seed)
    raw_df.to_csv(os.path.join(DATA_DIR, "synthetic_burnin_data.csv"), index=False)
    log(f"      {raw_df['dut_id'].nunique()} DUTs across {raw_df['lot_id'].nunique()} lots.")

    # ---------------------------------------------------------------
    # 2. Feature engineering
    # ---------------------------------------------------------------
    log("[2/8] Building physics-informed + statistical features ...")
    dut_df = build_dut_features(raw_df)
    feature_cols = get_model_feature_columns(dut_df)

    # ---------------------------------------------------------------
    # 3. Hybrid ensemble anomaly detection
    # ---------------------------------------------------------------
    log("[3/8] Fitting hybrid anomaly ensemble (IsolationForest + Autoencoder"
        " + One-Class SVM + Mahalanobis) ...")
    X = dut_df[feature_cols].fillna(0).values
    ensemble = HybridAnomalyEnsemble()
    ensemble.fit(X)
    anomaly_scores = ensemble.score(X)
    for k, v in anomaly_scores.items():
        dut_df[k] = v

    # ---------------------------------------------------------------
    # 4. Drift prediction per parameter (XGBoost mean + 10/90 quantiles)
    # ---------------------------------------------------------------
    log("[4/8] Training physics-informed drift predictors (per parameter) ...")
    early_feature_cols = [c for c in feature_cols if "_0h" in c or "physics_norm_slope" in c
                           or "arrhenius" in c or "temperature" in c or "_lot_zscore" in c]
    drift_models = {}
    for p in PARAMS:
        target_col = f"{p}_last"  # 168h value (last checkpoint)
        y = dut_df[target_col].values
        Xp = dut_df[early_feature_cols].fillna(0).values
        model = DriftPredictor(p)
        model.fit(Xp, y)
        preds = model.predict(Xp)
        for k, v in preds.items():
            dut_df[k] = v
        drift_models[p] = model
        log(f"      {p}: trained on {len(early_feature_cols)} early-checkpoint features")

    # ---------------------------------------------------------------
    # 5. Digital twin: project forward beyond 168h
    # ---------------------------------------------------------------
    log("[5/8] Running digital-twin projections (300h / 500h / 1000h) ...")
    twin_records = []
    for _, row in dut_df.iterrows():
        rec = {"dut_id": row["dut_id"]}
        for p in PARAMS:
            proj = project_trajectory(
                v0=row[f"{p}_0h"],
                physics_norm_slope=row[f"{p}_physics_norm_slope"],
                accel_factor=row["arrhenius_accel_factor"],
            )
            margin_500h = remaining_margin(proj, STATIC_LIMITS[p], 500)
            rec[f"{p}_projected_500h"] = margin_500h["projected_value"]
            rec[f"{p}_margin_pct_500h"] = margin_500h["margin_pct"]
        twin_records.append(rec)
    twin_df = pd.DataFrame(twin_records)
    dut_df = dut_df.merge(twin_df, on="dut_id", how="left")

    # ---------------------------------------------------------------
    # 6. Risk fusion
    # ---------------------------------------------------------------
    log("[6/8] Fusing signals into calibrated risk scores ...")
    dut_df = compute_risk(dut_df, STATIC_LIMITS, PARAMS)

    # ---------------------------------------------------------------
    # 7. Explainability
    # ---------------------------------------------------------------
    log("[7/8] Generating plain-language explanations (+ SHAP if available) ...")
    dut_df["explanation"] = dut_df.apply(explain_row, axis=1)

    shap_report = {}
    for p in PARAMS:
        Xp = dut_df[early_feature_cols].fillna(0).values
        shap_report[p] = shap_summary(drift_models[p].model_mean, Xp, early_feature_cols)
    with open(os.path.join(OUT_DIR, "shap_feature_importance.json"), "w") as f:
        json.dump(shap_report, f, indent=2, default=float)

    # ---------------------------------------------------------------
    # 8. Persist results + audit log
    # ---------------------------------------------------------------
    log("[8/8] Writing results.csv and audit_log.csv for the dashboard ...")
    results_path = os.path.join(OUT_DIR, "results.csv")
    dut_df.to_csv(results_path, index=False)

    audit_rows = []
    now = datetime.now(timezone.utc).isoformat()
    for _, row in dut_df[dut_df["risk_band"].isin(["HIGH", "CRITICAL"])].iterrows():
        audit_rows.append({
            "timestamp_utc": now,
            "dut_id": row["dut_id"],
            "lot_id": row["lot_id"],
            "risk_band": row["risk_band"],
            "risk_score": row["risk_score"],
            "risk_confidence_pct": row["risk_confidence_pct"],
            "explanation": row["explanation"],
            "model_version": "BurnInGuard-2.0-PoC",
        })
    audit_df = pd.DataFrame(audit_rows)
    audit_df.to_csv(os.path.join(OUT_DIR, "audit_log.csv"), index=False)

    # ---------------------------------------------------------------
    # Offline evaluation vs. ground-truth synthetic labels
    # (only possible because this is synthetic data with known labels;
    #  a real deployment would not have this at inference time)
    # ---------------------------------------------------------------
    if "true_latent_defect" in dut_df.columns:
        from sklearn.metrics import classification_report
        y_true = dut_df["true_latent_defect"].values
        y_pred = (dut_df["risk_band"].isin(["HIGH", "CRITICAL"])).astype(int).values
        report = classification_report(y_true, y_pred, target_names=["normal", "latent_defect"],
                                        zero_division=0)
        log("\n--- Offline evaluation vs. synthetic ground truth (PoC only) ---")
        log(report)
        with open(os.path.join(OUT_DIR, "evaluation_report.txt"), "w") as f:
            f.write(report)

    log(f"\nDone. Results written to: {results_path}")
    log("Now run:  streamlit run dashboard/app.py")
    return dut_df


if __name__ == "__main__":
    run_pipeline()
