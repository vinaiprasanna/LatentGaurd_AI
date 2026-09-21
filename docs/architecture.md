# System Architecture

## High-Level Overview

BurnInGuard AI 2.0 follows a three-tier architecture:

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                     │
│              React + Vite Frontend                        │
│  Dashboard │ Anomaly Analysis │ Digital Twin │ Explain   │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP/REST API (CORS-enabled)
                   ▼
┌─────────────────────────────────────────────────────────┐
│                     Application Layer                     │
│                  FastAPI Backend                          │
│  /api/duts │ /predict │ /predict/batch │ /health        │
│  /status │ /api/model-metrics │ /api/dashboard/stats    │
│  /api/audit-log │ /api/audit-jobs │ /api/chat            │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│                      Data Layer                          │
│  ML Models (Pickle) │ SQLite Audit Store │ CSV I/O      │
└─────────────────────────────────────────────────────────┘
```

## ML Pipeline

### 1. Feature Engineering (`features.py`)
- Converts raw CSV telemetry into model-ready feature vectors
- Normalizes parameters across checkpoints using physics-informed transforms
- Generates Arrhenius acceleration factors and lot z-scores

### 2. Anomaly Detection (`anomaly_ensemble.py`)
- **XGBoost** component for gradient-boosted tree predictions
- **Random Forest** component for ensemble diversity
- **PCA-SPC** component for statistical process control
- Weighted ensemble produces `anomaly_ensemble_score` (0–1)

### 3. Drift Modeling (`drift_model.py`)
- Physics-informed models trained on early-burn-in data (0h checkpoints)
- Predicts parametric values at 168h for each DUT
- Provides prediction intervals (`_lo`, `_hi` bounds)

### 4. Digital Twin (`digital_twin.py`)
- Projects component trajectories to 500h using physics-based models
- Computes remaining margin percentages against static limits

### 5. Risk Engine (`risk_engine.py`)
- Fuses four components into a single risk score:
  - Anomaly score
  - Lot deviation
  - Drift rate
  - Future margin
- Applies stage-A flag penalty (+20 points)
- Maps score to risk band and predicted outcome

### 6. Explainability (`explainability.py`)
- Generates plain-language explanations for each prediction
- Builds evidence chains linking features to decisions
- Provides recommended confirmation tests and thermal counterfactuals

## Data Flow

1. User uploads CSV → Data is cleaned and validated (`data_cleaner.py`)
2. Features are built → Anomaly scores computed
3. Drift predictions generated → Digital twin projections created
4. Risk scores computed → Explanations generated
5. Results returned → Audit job recorded → Dashboard updated

## Audit and Provenance

- Every prediction job is assigned a unique `job_id`
- Audit trails are stored in `backend/outputs/audit_jobs.json`
- Review actions (acknowledge, investigate, resolve) are tracked separately
- Job results are retained (max 100 jobs) in `backend/outputs/jobs/`
