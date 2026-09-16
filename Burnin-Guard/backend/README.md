# BurnInGuard AI 2.0 - Backend

FastAPI-based inference service for BurnInGuard AI PASS/FAIL prediction.

## Structure

```
backend/
├── src/              # Prediction modules (features, risk_engine, digital_twin, explainability, anomaly_ensemble, drift_model, spc, data_generator)
├── models/           # Exported model pickles
│   ├── anomaly_ensemble_model.pkl
│   └── drift_model.pkl
├── main.py           # FastAPI app (uvicorn)
├── predict.py        # CLI prediction script
├── requirements.txt
├── prediction_input.csv  # Input CSV (raw telemetry, 4 checkpoints per DUT)
└── outputs/          # Prediction output
```

## Usage

### Train models (one-time)
```bash
cd model-training
python anomaly_ensemble/train.py
python drift_model/train.py
```

### Run CLI prediction
```bash
cd backend
python predict.py
```

### Run API server
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### API Endpoints
- `GET /health` - Health check
- `GET /status` - Model status
- `POST /predict` - Upload CSV, get predictions
- `POST /predict/batch` - Upload CSV, get summary + save to output file

## Endpoints

### POST /predict
Upload a CSV file with columns: `dut_id, lot_id, checkpoint_h, temperature_c, vcc_v, iddq_uA, leakage_uA, delay_ns`

Returns: JSON array of predictions with `dut_id`, `risk_score`, `risk_band`, `predicted_outcome`, `explanation`

### POST /predict/batch
Same as above but returns summary and saves to `outputs/prediction_output.csv`

## Data Format

Input CSV should have one row per checkpoint measurement per DUT (4 checkpoints: 0h, 24h, 96h, 168h). The backend automatically collapses to one row per DUT and computes features.

The `calibration_source` column is automatically excluded from features.
