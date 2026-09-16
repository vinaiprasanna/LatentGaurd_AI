"""
BurnInGuard AI 2.0 -- FastAPI Backend
=========================================
REST API for BurnInGuard AI prediction service.
Run with:  uvicorn main:app --host 0.0.0.0 --port 8000
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

from features import build_dut_features, get_model_feature_columns, PARAMS
from explainability import explain_row
from digital_twin import project_trajectory, remaining_margin
from data_generator import STATIC_LIMITS
from risk_engine import compute_risk

ANOMALY_MODEL_PATH = os.path.join(MODELS_DIR, "anomaly_ensemble_model.pkl")
DRIFT_MODEL_PATH = os.path.join(MODELS_DIR, "drift_model.pkl")


def load_models():
    with open(ANOMALY_MODEL_PATH, "rb") as f:
        ensemble = pickle.load(f)
    with open(DRIFT_MODEL_PATH, "rb") as f:
        drift_models = pickle.load(f)
    return ensemble, drift_models


_models = load_models()

# ---------------------------------------------------------------------------
# Prediction logic
# ---------------------------------------------------------------------------

def run_prediction(df: pd.DataFrame) -> pd.DataFrame:
    ensemble, drift_models = _models

    dut_df = build_dut_features(df)
    feature_cols = get_model_feature_columns(dut_df)

    missing = [c for c in feature_cols if c not in dut_df.columns]
    for col in missing:
        dut_df[col] = 0.0

    X = dut_df[feature_cols].fillna(0).values

    # Anomaly ensemble scores
    scores = ensemble.score(X)
    for k, v in scores.items():
        dut_df[k] = v

    # Drift predictions
    early_feature_cols = [c for c in feature_cols if "_0h" in c or "physics_norm_slope" in c
                           or "arrhenius" in c or "temperature" in c or "_lot_zscore" in c]
    for p in PARAMS:
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
    dut_df = compute_risk(dut_df, STATIC_LIMITS, PARAMS)
    dut_df["explanation"] = dut_df.apply(explain_row, axis=1)
    dut_df["predicted_outcome"] = dut_df["risk_band"].apply(
        lambda b: "FAIL" if b in ("HIGH", "CRITICAL") else "PASS"
    )

    return dut_df


# ---------------------------------------------------------------------------
# FastAPI
# ---------------------------------------------------------------------------

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

app = FastAPI(
    title="BurnInGuard AI 2.0",
    description="Physics-informed, explainable PASS/FAIL prediction for component burn-in screening",
    version="2.0.0"
)


class PredictionResponse(BaseModel):
    dut_id: str
    lot_id: str
    risk_score: float
    risk_band: str
    risk_confidence_pct: float
    predicted_outcome: str
    explanation: str


@app.get("/health")
def health():
    return {"status": "healthy", "model_loaded": _models is not None}


@app.get("/status")
def status():
    global _models
    return {
        "model_loaded": _models is not None,
        "anomaly_ensemble": ANOMALY_MODEL_PATH if _models else None,
        "drift_model": DRIFT_MODEL_PATH if _models else None,
    }


@app.post("/predict", response_model=List[PredictionResponse])
def predict(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    try:
        df = pd.read_csv(file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")

    if df.empty:
        raise HTTPException(status_code=400, detail="CSV file is empty")

    try:
        results = run_prediction(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    output_cols = [
        "dut_id", "lot_id", "risk_score", "risk_band",
        "risk_confidence_pct", "predicted_outcome", "explanation"
    ]
    available_cols = [c for c in output_cols if c in results.columns]
    output = results[available_cols]

    return output.to_dict(orient="records")


@app.post("/predict/batch")
def predict_batch(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    try:
        df = pd.read_csv(file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")

    if df.empty:
        raise HTTPException(status_code=400, detail="CSV file is empty")

    try:
        results = run_prediction(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    output_cols = [
        "dut_id", "lot_id", "risk_score", "risk_band",
        "risk_confidence_pct", "predicted_outcome", "explanation"
    ]
    available_cols = [c for c in output_cols if c in results.columns]
    output = results[available_cols]

    output_path = os.path.join(ROOT, "outputs", "prediction_output.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    output.to_csv(output_path, index=False)

    return {
        "total_duts": len(output),
        "pass": int((output["predicted_outcome"] == "PASS").sum()),
        "fail": int((output["predicted_outcome"] == "FAIL").sum()),
        "output_file": output_path
    }
