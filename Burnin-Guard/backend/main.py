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
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_absolute_error, mean_squared_error, r2_score

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT, "src")
MODELS_DIR = os.path.join(ROOT, "models")
sys.path.insert(0, SRC_DIR)

from features import build_dut_features, get_model_feature_columns, PARAMS
from explainability import explain_row
from digital_twin import project_trajectory, remaining_margin
from data_generator import STATIC_LIMITS
from risk_engine import compute_risk
from failure_chatbot import answer_question
from data_cleaner import clean_and_validate

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
_active_results = None
_active_raw_data = None
_model_metrics = None
_active_test_metrics = None
_active_cleaning_report = None

# ---------------------------------------------------------------------------
# Prediction logic
# ---------------------------------------------------------------------------

def run_prediction(df: pd.DataFrame) -> pd.DataFrame:
    ensemble, drift_models = _models
    if ensemble is None or drift_models is None:
        raise RuntimeError("Trained models are not available")

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
            if margin is None:
                raise RuntimeError(f"Projection horizon 500h is unavailable for {p}")
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


def _inference_rows(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Exclude 168h target rows from inference when a labeled horizon is supplied."""
    if "checkpoint_h" not in raw_df.columns:
        return raw_df
    checkpoints = set(pd.to_numeric(raw_df["checkpoint_h"], errors="coerce").dropna().astype(int))
    if 168 in checkpoints and len(checkpoints) > 1:
        early = raw_df[raw_df["checkpoint_h"] < 168].copy()
        if not early.empty:
            return early
    return raw_df


def _get_model_metrics():
    """Return cached training-set diagnostics for the loaded artifacts."""
    global _model_metrics
    if _model_metrics is not None:
        metrics = dict(_model_metrics)
        if _active_test_metrics is not None:
            metrics["test"] = _active_test_metrics
        return metrics
    if _models[0] is None or _models[1] is None:
        return {"model_loaded": False}

    training_path = os.path.join(ROOT, "..", "model-training", "data", "large_physics_calibrated_burnin_dataset.csv")
    if not os.path.exists(training_path):
        return {"model_loaded": True, "metrics_available": False, "message": "Training dataset is unavailable"}

    raw_df = pd.read_csv(training_path)
    dut_df = build_dut_features(raw_df)
    feature_cols = get_model_feature_columns(dut_df)
    X = dut_df[feature_cols].fillna(0).values
    ensemble, drift_models = _models
    scores = ensemble.score(X)

    metrics = {
        "model_loaded": True,
        "metrics_available": True,
        "evaluation_scope": "in-sample training diagnostics; not a held-out validation score",
        "validation_available": False,
        "validation_message": "No labeled held-out validation dataset is configured.",
        "training_rows": int(len(raw_df)),
        "training_duts": int(len(dut_df)),
        "feature_count": len(feature_cols),
        "feature_columns": feature_cols,
        "anomaly": {
            "ensemble_mean_score": round(float(scores["anomaly_ensemble_score"].mean()), 4),
        },
        "drift": {},
        "anomaly_feature_importance": [],
        "drift_feature_importance": {},
    }

    prediction_path = os.path.join(ROOT, "prediction_input.csv")
    if os.path.exists(prediction_path):
        prediction_df = pd.read_csv(prediction_path, usecols=["dut_id"])
        training_ids = set(raw_df["dut_id"].astype(str))
        prediction_ids = set(prediction_df["dut_id"].astype(str))
        metrics["prediction_input"] = {
            "path": prediction_path,
            "dut_count": len(prediction_ids),
            "has_labels": False,
            "overlap_with_training_duts": len(training_ids & prediction_ids),
            "is_independent_validation": False,
            "message": "This file is inference input, not an independent labeled test set.",
        }

    if "true_latent_defect" in dut_df.columns:
        y_true = np.asarray(dut_df["true_latent_defect"].to_numpy(dtype=int))
        y_pred = np.asarray((scores["anomaly_ensemble_score"] >= 0.5).astype(int))
        metrics["anomaly"].update({
            "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
            "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
            "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        })

    anomaly_importance = (
        ensemble.weights["xgboost"] * ensemble.xgb_model.feature_importances_
        + ensemble.weights["random_forest"] * ensemble.rf_model.feature_importances_
    )
    importance_total = float(anomaly_importance.sum())
    if importance_total:
        anomaly_importance = anomaly_importance / importance_total
    metrics["anomaly_feature_importance"] = [
        {"feature": name, "importance": round(float(value), 4)}
        for name, value in sorted(zip(feature_cols, anomaly_importance), key=lambda item: -item[1])[:12]
    ]

    early_feature_cols = [c for c in feature_cols if "_0h" in c or "physics_norm_slope" in c
                          or "arrhenius" in c or "temperature" in c or "_lot_zscore" in c]
    Xp = dut_df[early_feature_cols].fillna(0).values
    for parameter, model in drift_models.items():
        target = np.asarray(dut_df[f"{parameter}_last"].to_numpy(dtype=float))
        prediction = np.asarray(model.predict(Xp)[f"{parameter}_pred_168h"])
        metrics["drift"][parameter] = {
            "mae": round(float(mean_absolute_error(target, prediction)), 4),
            "rmse": round(float(np.sqrt(mean_squared_error(target, prediction))), 4),
            "r2": round(float(r2_score(target, prediction)), 4),
        }
        metrics["drift_feature_importance"][parameter] = [
            {"feature": name, "importance": round(float(value), 4)}
            for name, value in list(model.feature_importances(early_feature_cols).items())[:12]
        ]

    _model_metrics = metrics
    if _active_test_metrics is not None:
        metrics["test"] = _active_test_metrics
    return metrics


def _evaluate_uploaded_test(results: pd.DataFrame, raw_df: pd.DataFrame):
    """Evaluate uploaded test labels and 168h regression targets without retraining."""
    training_path = os.path.join(ROOT, "..", "model-training", "data", "large_physics_calibrated_burnin_dataset.csv")
    training_ids = set(pd.read_csv(training_path, usecols=["dut_id"])["dut_id"].astype(str)) if os.path.exists(training_path) else set()
    test_ids = set(raw_df["dut_id"].astype(str))
    metrics = {
        "available": False,
        "evaluation_scope": "uploaded labeled test dataset; model weights were not retrained",
        "test_rows": int(len(raw_df)),
        "test_duts": int(raw_df["dut_id"].nunique()),
        "has_labels": "true_latent_defect" in raw_df.columns,
        "overlap_with_training_duts": int(len(training_ids & test_ids)),
        "is_independent_test": len(training_ids & test_ids) == 0,
    }
    if "true_latent_defect" in raw_df.columns:
        labels = raw_df[["dut_id", "true_latent_defect"]].drop_duplicates("dut_id")
        evaluated = results.merge(labels, on="dut_id", how="inner", suffixes=("", "_input"))
        if not evaluated.empty:
            y_true = np.asarray(evaluated["true_latent_defect_input"].to_numpy(dtype=int))
            y_pred = np.asarray((evaluated["anomaly_ensemble_score"].to_numpy(dtype=float) >= 0.5).astype(int))
            metrics.update({
                "available": True,
                "anomaly_metrics_available": True,
                "test_duts": int(len(evaluated)),
                "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
                "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
                "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
                "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
                "false_negative_count": int(((y_true == 1) & (y_pred == 0)).sum()),
                "false_negative_rate": round(float(((y_true == 1) & (y_pred == 0)).sum() / max((y_true == 1).sum(), 1)), 4),
            })
    else:
        metrics["message"] = "No true_latent_defect labels; classification metrics are unavailable."

    complete = raw_df.groupby("dut_id")["checkpoint_h"].max()
    complete_ids = set(complete[complete >= 168].index.astype(str))
    drift_results = results[results["dut_id"].astype(str).isin(complete_ids)]
    actual_168 = raw_df[raw_df["checkpoint_h"] == 168].sort_values("checkpoint_h").groupby("dut_id").tail(1)
    actual_168 = actual_168.set_index(actual_168["dut_id"].astype(str)) if not actual_168.empty else actual_168
    drift_metrics = {}
    for parameter in PARAMS:
        target_field = f"{parameter}_last"
        prediction_field = f"{parameter}_pred_168h"
        if target_field in drift_results and prediction_field in drift_results and not drift_results.empty:
            prediction = drift_results.set_index(drift_results["dut_id"].astype(str))[prediction_field]
            prediction = prediction[prediction.index.isin(actual_168.index)]
            target = actual_168.loc[prediction.index, parameter].astype(float) if not actual_168.empty else pd.Series(dtype=float)
            prediction = prediction.astype(float)
            if target.empty:
                continue
            drift_metrics[parameter] = {
                "mae": round(float(mean_absolute_error(target, prediction)), 4),
                "rmse": round(float(np.sqrt(mean_squared_error(target, prediction))), 4),
                "r2": round(float(r2_score(target, prediction)), 4),
                "test_duts": int(len(drift_results)),
            }
    metrics["drift"] = drift_metrics
    metrics["drift_metrics_available"] = bool(drift_metrics)
    if not drift_metrics:
        metrics["drift_message"] = "168h measured checkpoints are required to calculate drift test RMSE."
    metrics["available"] = bool(metrics.get("anomaly_metrics_available") or drift_metrics)
    return metrics


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


class ChatRequest(BaseModel):
    question: str
    dut_id: Optional[str] = None
    history: Optional[List[Dict[str, Any]]] = None


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


@app.get("/api/model-metrics")
def get_model_metrics():
    """Expose loaded model diagnostics and feature importance for the UI."""
    return _get_model_metrics()


@app.get("/api/data-quality")
def get_data_quality():
    """Return the latest uploaded CSV cleaning report."""
    return _active_cleaning_report or {"available": False, "message": "No CSV has been uploaded."}


@app.post("/api/chat")
def chat_with_cosmo(request: ChatRequest):
    """Answer a read-only COSMO question using the current prediction results."""
    if _models is None:
        raise HTTPException(status_code=503, detail="Trained models are not available")

    try:
        records = _get_all_duts()
        results = pd.DataFrame(records)
        if results.empty:
            raise HTTPException(status_code=404, detail="No prediction results are available")

        selected = results.iloc[0]
        if request.dut_id and request.dut_id in results["dut_id"].astype(str).values:
            selected = results[results["dut_id"].astype(str) == request.dut_id].iloc[0]
        raw_data = _active_raw_data
        if raw_data is None and os.path.exists("prediction_input.csv"):
            raw_data = pd.read_csv("prediction_input.csv")
        response = answer_question(
            request.question,
            selected,
            results=results,
            chat_history=request.history or [],
            raw_data=raw_data,
            model_metrics=_get_model_metrics(),
        )
        return {"assistant": "COSMO", "answer": response, "dut_id": selected.get("dut_id")}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"COSMO could not answer: {exc}")


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
    if _active_results is not None:
        return _active_results.to_dict(orient="records")
    sample_df = pd.read_csv("prediction_input.csv")
    results = run_prediction(_inference_rows(sample_df))
    results = _attach_dashboard_telemetry(results, sample_df)
    return results.to_dict(orient="records")


def _attach_dashboard_telemetry(results: pd.DataFrame, raw_df: pd.DataFrame) -> pd.DataFrame:
    """Add the latest raw telemetry fields consumed by dashboard views."""
    telemetry_cols = [
        "dut_id", "checkpoint_h", "temperature_c", "vcc_v",
        "iddq_uA", "leakage_uA", "delay_ns",
    ]
    available_cols = [column for column in telemetry_cols if column in raw_df.columns]
    latest = (
        raw_df.sort_values("checkpoint_h")
        .groupby("dut_id", as_index=False)
        .tail(1)[available_cols]
    )
    quality_columns = [column for column in ["dut_id", "data_quality_abnormal", "data_quality_flags"] if column in raw_df.columns]
    quality = raw_df[quality_columns].drop_duplicates("dut_id") if quality_columns else pd.DataFrame(columns=["dut_id"])
    result_without_telemetry = results.drop(
        columns=[column for column in available_cols if column != "dut_id" and column in results.columns],
        errors="ignore",
    )
    enriched = result_without_telemetry.merge(latest, on="dut_id", how="left")
    return enriched.merge(quality, on="dut_id", how="left")


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


@app.post("/predict", response_model=List[Dict[str, Any]])
def predict(file: UploadFile = File(...)):
    global _active_results, _active_raw_data, _active_test_metrics, _active_cleaning_report
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    try:
        df = pd.read_csv(file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")

    if df.empty:
        raise HTTPException(status_code=400, detail="CSV file is empty")

    try:
        cleaned_df, cleaning_report = clean_and_validate(df)
        if cleaned_df.empty:
            raise HTTPException(status_code=400, detail="CSV has no usable telemetry rows after cleaning")
        results = run_prediction(_inference_rows(cleaned_df))
        results = _attach_dashboard_telemetry(results, cleaned_df)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    output = results
    _active_results = output.copy()
    _active_raw_data = cleaned_df.copy()
    _active_test_metrics = _evaluate_uploaded_test(output, cleaned_df)
    _active_cleaning_report = cleaning_report.as_dict()

    return output.to_dict(orient="records")


@app.post("/predict/batch")
def predict_batch(file: UploadFile = File(...)):
    global _active_results, _active_raw_data, _active_test_metrics, _active_cleaning_report
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    try:
        df = pd.read_csv(file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")

    if df.empty:
        raise HTTPException(status_code=400, detail="CSV file is empty")

    try:
        cleaned_df, cleaning_report = clean_and_validate(df)
        if cleaned_df.empty:
            raise HTTPException(status_code=400, detail="CSV has no usable telemetry rows after cleaning")
        results = run_prediction(_inference_rows(cleaned_df))
        results = _attach_dashboard_telemetry(results, cleaned_df)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    output = results
    _active_results = output.copy()
    _active_raw_data = cleaned_df.copy()
    _active_test_metrics = _evaluate_uploaded_test(output, cleaned_df)
    _active_cleaning_report = cleaning_report.as_dict()

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
    if _active_results is not None:
        all_duts = _active_results.to_dict(orient="records")
        total = len(all_duts)
        fail_count = sum(1 for d in all_duts if d.get("predicted_outcome") == "FAIL")
        high_risk = sum(1 for d in all_duts if d.get("risk_band") in ("HIGH", "CRITICAL"))
        return {
            "total_components": total,
            "anomalies_detected": high_risk,
            "high_risk_components": high_risk,
            "anomaly_rate": f"{(high_risk / total * 100):.2f}%" if total else "0%",
            "pass_rate": f"{((total - fail_count) / total * 100):.2f}%" if total else "0%",
            "model_loaded": True,
        }
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
