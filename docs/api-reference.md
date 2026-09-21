# API Reference

Base URL: `http://localhost:8000`

Interactive documentation is available at `http://localhost:8000/docs` (Swagger UI).

## Health & Status

### GET `/health`

Returns backend health status and model availability.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

### GET `/status`

Returns model loading status and paths.

**Response:**
```json
{
  "model_loaded": true,
  "anomaly_ensemble": "./models/anomaly_ensemble_model.pkl",
  "drift_model": "./models/drift_model.pkl"
}
```

### GET `/api/model-metrics`

Returns diagnostics and feature importance for loaded models.

**Response fields:**
- `model_loaded`: Whether models are loaded
- `anomaly`: Ensemble mean score, accuracy, precision, recall, F1
- `drift`: Per-parameter MAE, RMSE, R²
- `anomaly_feature_importance`: Top 12 features with importance scores
- `drift_feature_importance`: Per-parameter feature importance

## Data Endpoints

### GET `/api/duts`

Returns all uploaded DUT results with risk scores.

**Response:**
```json
{
  "duts": [...],
  "model_loaded": true
}
```

### GET `/api/duts/{dut_id}`

Returns data for a single DUT including digital twin projection.

### GET `/api/dashboard/stats`

Returns dashboard KPI statistics.

**Response:**
```json
{
  "total_components": 1248,
  "anomalies_detected": 88,
  "high_risk_components": 88,
  "anomaly_rate": "7.05%",
  "pass_rate": "92.95%",
  "model_loaded": true
}
```

## Prediction Endpoints

### POST `/predict`

Upload a CSV file and receive per-DUT predictions.

**Request:** `multipart/form-data` with `file` field (CSV)

**Response:** Array of prediction objects.

**CSV Format:**
Columns: `dut_id, lot_id, checkpoint_h, temperature_c, vcc_v, iddq_uA, leakage_uA, delay_ns`

### POST `/predict/batch`

Same as `/predict` but returns a summary and saves results to `outputs/prediction_output.csv`.

**Response:**
```json
{
  "total_duts": 1248,
  "pass": 1160,
  "fail": 88,
  "output_file": "/app/outputs/prediction_output.csv"
}
```

## Audit Endpoints

### GET `/api/audit-log`

Returns audit log entries for the current session.

### GET `/api/audit-jobs`

Returns durable upload-level provenance records.

### GET `/api/audit-jobs/{job_id}/results`

Returns prediction results for a specific audit job.

### GET `/api/review-actions`

Returns reviewer actions (acknowledge, investigate, resolve).

### POST `/api/review-actions`

Records a reviewer action.

**Request body:**
```json
{
  "dut_id": "DUT-001",
  "lot_id": "LOT2026A",
  "action": "ACKNOWLEDGE"
}
```

**Valid actions:** `ACKNOWLEDGE`, `INVESTIGATE`, `RESOLVE`

## Chatbot

### POST `/api/chat`

Query COSMO for failure analysis insights.

**Request body:**
```json
{
  "question": "Why is this component failing?",
  "dut_id": "DUT-001",
  "history": []
}
```

**Response:**
```json
{
  "assistant": "COSMO",
  "answer": "...",
  "dut_id": "DUT-001"
}
```
