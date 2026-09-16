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
    if not os.path.exists(ANOMALY_MODEL_PATH) or not os.path.exists(DRIFT_MODEL_PATH):
        return None, None
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


def build_sample_dut_data():
    """Generate sample DUT data for the dashboard when models are not loaded."""
    checkpoints = ["0h", "24h", "48h", "72h", "96h", "120h", "144h", "168h"]
    lots = ["LOT2026A", "LOT2026B", "LOT2026C", "LOT2026D", "LOT2026E", "LOT2026G"]
    components = []
    for i in range(1, 13):
        dut_id = f"DUT-0{i:03d}"
        lot = lots[i % len(lots)]
        for j, cp in enumerate(checkpoints):
            components.append({
                "dut_id": dut_id,
                "lot_id": lot,
                "checkpoint_h": j * 24,
                "temperature_c": round(110 + np.random.normal(0, 10), 2),
                "vcc_v": round(5.0 + np.random.normal(0, 0.02), 3),
                "iddq_uA": round(8 + np.random.exponential(3) + j * 0.5, 3),
                "leakage_uA": round(2 + np.random.exponential(1) + j * 0.2, 3),
                "delay_ns": round(5 + np.random.normal(0, 1) + j * 0.3, 3),
            })
    return pd.DataFrame(components)


# ---------------------------------------------------------------------------
# FastAPI
# ---------------------------------------------------------------------------

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

app = FastAPI(
    title="BurnInGuard AI 2.0",
    description="Physics-informed, explainable PASS/FAIL prediction for component burn-in screening",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictionResponse(BaseModel):
    dut_id: str
    lot_id: str
    risk_score: float
    risk_band: str
    risk_confidence_pct: float
    predicted_outcome: str
    explanation: str


class DutData(BaseModel):
    dut_id: str
    lot_id: str
    risk_score: float
    risk_band: str
    risk_confidence_pct: float
    predicted_outcome: str
    explanation: str
    anomaly_score: float
    checkpoint_h: int
    temperature_c: float
    iddq_uA: float
    leakage_uA: float
    delay_ns: float


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


@app.get("/api/duts")
def get_duts():
    """Get all DUT data with risk scores for the dashboard."""
    if _models is None:
        # Return sample data if models not loaded
        return {"duts": _get_sample_duts(), "model_loaded": False}
    return {"duts": _get_all_duts(), "model_loaded": True}


@app.get("/api/duts/{dut_id}")
def get_dut(dut_id: str):
    """Get individual DUT data and digital twin projection."""
    if _models is None:
        return {"dut": _get_sample_dut(dut_id), "model_loaded": False}
    return {"dut": _get_dut_data(dut_id), "model_loaded": True}


def _get_all_duts():
    """Run prediction on sample data and return all DUT results."""
    sample_df = build_sample_dut_data()
    results = run_prediction(sample_df)
    output_cols = [
        "dut_id", "lot_id", "risk_score", "risk_band",
        "risk_confidence_pct", "predicted_outcome", "explanation",
        "anomaly_ensemble_score", "temperature_c", "iddq_uA",
        "leakage_uA", "delay_ns"
    ]
    available_cols = [c for c in output_cols if c in results.columns]
    return results[available_cols].to_dict(orient="records")


def _get_dut_data(dut_id: str):
    """Get data for a single DUT."""
    all_duts = _get_all_duts()
    for dut in all_duts:
        if dut["dut_id"] == dut_id:
            return dut
    return {"dut_id": dut_id, "error": "Not found"}


def _get_sample_duts():
    """Return sample DUT data when models aren't loaded."""
    checkpoints = ["0h", "24h", "48h", "72h", "96h", "120h", "144h", "168h"]
    lots = ["LOT2026A", "LOT2026B", "LOT2026C", "LOT2026D", "LOT2026E", "LOT2026G"]
    duts = []
    for i in range(1, 13):
        dut_id = f"DUT-0{i:03d}"
        lot = lots[i % len(lots)]
        risk_scores = np.random.uniform(10, 95)
        band = "CRITICAL" if risk_scores >= 80 else "HIGH" if risk_scores >= 60 else "MEDIUM" if risk_scores >= 30 else "LOW"
        duts.append({
            "dut_id": dut_id,
            "lot_id": lot,
            "risk_score": round(risk_scores, 1),
            "risk_band": band,
            "risk_confidence_pct": round(np.random.uniform(0, 40), 1),
            "predicted_outcome": "FAIL" if band in ("HIGH", "CRITICAL") else "PASS",
            "explanation": "Synthetic demonstration data",
            "anomaly_score": round(risk_scores / 100, 2),
            "checkpoint_h": 168,
            "temperature_c": round(110 + np.random.normal(0, 10), 2),
            "iddq_uA": round(8 + np.random.exponential(3), 3),
            "leakage_uA": round(2 + np.random.exponential(1), 3),
            "delay_ns": round(5 + np.random.normal(0, 1), 3),
        })
    return duts


def _get_sample_dut(dut_id: str):
    """Return sample DUT data for a single DUT."""
    all_sample = _get_sample_duts()
    for dut in all_sample:
        if dut["dut_id"] == dut_id:
            return dut
    return {"dut_id": dut_id, "error": "Not found"}


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


@app.get("/api/dashboard/stats")
def get_dashboard_stats():
    """Get dashboard KPI statistics."""
    if _models is None:
        return {
            "total_components": 1248,
            "anomalies_detected": 87,
            "high_risk_components": 23,
            "anomaly_rate": "6.97%",
            "pass_rate": "93.03%",
            "model_loaded": False,
        }
    all_duts = _get_all_duts()
    total = len(all_duts)
    fail_count = sum(1 for d in all_duts if d["predicted_outcome"] == "FAIL")
    pass_count = total - fail_count
    high_risk = sum(1 for d in all_duts if d["risk_band"] in ("HIGH", "CRITICAL"))
    return {
        "total_components": total,
        "anomalies_detected": high_risk,
        "high_risk_components": high_risk,
        "anomaly_rate": f"{(high_risk/total*100):.2f}%" if total > 0 else "0%",
        "pass_rate": f"{(pass_count/total*100):.2f}%" if total > 0 else "0%",
        "model_loaded": True,
    }


@app.get("/api/audit-log")
def get_audit_log():
    """Get audit log entries."""
    if _models is None:
        return {"entries": _get_sample_audit_log()}
    all_duts = _get_all_duts()
    entries = []
    for i, dut in enumerate(all_duts[:20]):
        entries.append({
            "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
            "dut_id": dut["dut_id"],
            "lot_id": dut["lot_id"],
            "risk_band": dut["risk_band"],
            "risk_score": dut["risk_score"],
            "confidence_pct": dut["risk_confidence_pct"],
            "explanation": dut["explanation"],
            "model_version": "BG-AI-2.0",
        })
    return {"entries": entries}


def _get_sample_audit_log():
    return [
        {"timestamp": "2026-09-16 09:42", "dut_id": "IC0060", "lot_id": "LOT2026B", "risk_band": "CRITICAL", "risk_score": 87.3, "confidence_pct": 0, "explanation": "Predicted value approaching safety limit", "model_version": "BG-AI-2.0"},
        {"timestamp": "2026-09-16 09:38", "dut_id": "IC0075", "lot_id": "LOT2026B", "risk_band": "CRITICAL", "risk_score": 87.2, "confidence_pct": 0, "explanation": "Predicted value approaching safety limit", "model_version": "BG-AI-2.0"},
        {"timestamp": "2026-09-16 09:34", "dut_id": "IC0201", "lot_id": "LOT2026E", "risk_band": "CRITICAL", "risk_score": 82.1, "confidence_pct": 0, "explanation": "Significant deviation from lot population", "model_version": "BG-AI-2.0"},
        {"timestamp": "2026-09-16 09:30", "dut_id": "IC0042", "lot_id": "LOT2026A", "risk_band": "HIGH", "risk_score": 77.7, "confidence_pct": 32.5, "explanation": "High physics-normalised drift rate", "model_version": "BG-AI-2.0"},
    ]
