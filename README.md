# BurnInGuard AI 2.0

Physics-informed, explainable PASS/FAIL prediction for component burn-in screening.

[![CI/CD](https://github.com/ISRO-BurnInGuard/burninguard-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/ISRO-BurnInGuard/burninguard-ai/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-2.0.0-green.svg)](CHANGELOG.md)


## HOW TO RUN
### Install Dependencies
> Windows
```bash
scripts/install-dependencies.bat
```
> Linux
```bash
source scripts/install-dependencies.sh
```
### Train Models
> Windows
```bash
scripts/train-models.bat
```
> Linux
```bash
source scripts/train-models.sh
```

### RUN BACKEND (TERMINAL 1)
> Windows
```bash
scripts/run-backend.bat
```
> Linux
```bash
source scripts/run-backend.sh
```


### RUN FRONTEND (TERMINAL 2)
> Windows
```bash
scripts/run-frontend.bat
```
> Linux
```bash
source scripts/run-frontend.sh
```


- Frontend: **http://localhost:3000**
- API: **http://localhost:8000**
- API Docs: **http://localhost:8000/docs**

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Model Training](#model-training)
- [Configuration](#configuration)
- [Docker Deployment](#docker-deployment)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Overview

BurnInGuard AI 2.0 is an AI-powered component screening system that predicts PASS/FAIL outcomes for burn-in tested components. It combines:

- **Hybrid Anomaly Ensemble** (XGBoost + Random Forest + PCA-SPC) for anomaly detection
- **Physics-Informed Drift Models** for predicting component behaviour beyond burn-in
- **Digital Twin Projection** for fast-forwarding component trajectories to 500h
- **Risk Fusion Engine** combining anomaly, lot deviation, drift rate, and future margin into a single 0-100 risk score
- **Explainability Layer** providing plain-language reasons for each prediction

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)               │
│  Dashboard │ Anomaly Analysis │ Digital Twin │ Explain  │
│              │                  │               │ Audit   │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP/REST API
                   ▼
┌─────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                      │
│  /api/duts  │ /predict  │ /predict/batch  │ /health     │
│  /status    │ /audit-log  │ /dashboard/stats           │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│                 ML Models (Pickle)                       │
│  anomaly_ensemble_model.pkl  │ drift_model.pkl           │
└─────────────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│               Data Pipeline                              │
│  data_generator │ features │ risk_engine │ digital_twin │
│  explainability │ anomaly_ensemble │ drift_model │ spc  │
└─────────────────────────────────────────────────────────┘
```

## Prerequisites

- **Python** 3.10+ and **pip**
- **Node.js** 18+ and **npm**
- **Git**
- **Docker** and **Docker Compose** (optional)

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd Burninguard_AI
```

### 2. Install Python dependencies (Backend + Model Training)

```bash
cd backend
pip install -r requirements.txt
```

```bash
cd model-training
pip install -r requirements.txt
```

### 3. Install Node.js dependencies (Frontend)

```bash
cd frontend
npm install
```

### 4. Install root-level dev dependencies (optional)

```bash
cd ..
npm install
```

## Running the Application

### Option A: Individual Processes (Recommended for Development)

Open **three terminal windows**:

**Terminal 1 - Backend API Server:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend Dev Server:**
```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at **http://localhost:3000** and the API at **http://localhost:8000**.

**Terminal 3 - (Optional) Model Training:**
```bash
cd model-training
pip install -r requirements.txt
python anomaly_ensemble/train.py
python drift_model/train.py
```

### Option B: All at Once

```bash
# From the project root (Burnin-Guard/)
npm run dev
```

This starts both backend and frontend simultaneously using `concurrently`.

### Option C: Docker Compose

```bash
# Start all services
docker-compose up --build

# Start only backend + frontend
docker-compose up --build backend frontend

# Start training service separately
docker-compose up --build --profile training model-training
```

The application will be available at:
- Frontend: **http://localhost:3000**
- API: **http://localhost:8000**
- API Docs: **http://localhost:8000/docs** (Swagger UI)

## Model Training

Before running predictions, train and export the models:

```bash
cd model-training
pip install -r requirements.txt

# Train and export anomaly ensemble
python anomaly_ensemble/train.py

# Train and export drift model
python drift_model/train.py
```

Models are exported to `backend/models/`:
- `anomaly_ensemble_model.pkl`
- `drift_model.pkl`

## API Documentation

All API endpoints are available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/status` | Model loading status |
| GET | `/api/duts` | Get all DUT data with risk scores |
| GET | `/api/duts/{dut_id}` | Get individual DUT data |
| GET | `/api/dashboard/stats` | Dashboard KPI statistics |
| GET | `/api/audit-log` | Get audit log entries |
| POST | `/predict` | Upload CSV, get predictions |
| POST | `/predict/batch` | Upload CSV, get summary + save CSV |

### POST /predict

Upload a CSV file with columns: `dut_id, lot_id, checkpoint_h, temperature_c, vcc_v, iddq_uA, leakage_uA, delay_ns`

```bash
curl -X POST http://localhost:8000/predict -F "file=@prediction_input.csv"
```

### POST /predict/batch

Same as above but returns summary and saves to `outputs/prediction_output.csv`.

```json
{
  "total_duts": 1248,
  "pass": 1160,
  "fail": 88,
  "output_file": "/app/outputs/prediction_output.csv"
}
```

### GET /api/duts

Returns all DUT data with computed risk scores.

### GET /api/dashboard/stats

Returns dashboard KPI statistics.

## Project Structure

```
Burnin-Guard/
├── backend/                    # FastAPI backend
│   ├── main.py                # FastAPI app with all endpoints
│   ├── predict.py             # CLI prediction script
│   ├── requirements.txt       # Python dependencies
│   ├── src/                   # ML source modules
│   │   ├── features.py        # Feature engineering
│   │   ├── risk_engine.py     # Risk fusion engine
│   │   ├── digital_twin.py    # Digital twin projection
│   │   ├── explainability.py  # Plain-language explanations
│   │   ├── anomaly_ensemble.py # Hybrid anomaly ensemble
│   │   ├── drift_model.py     # Drift prediction
│   │   ├── spc.py             # PCA-SPC detector
│   │   └── data_generator.py  # Synthetic data generator
│   ├── models/                # Trained model pickles
│   ├── outputs/               # Prediction outputs
│   └── prediction_input.csv   # Sample input CSV
│
├── frontend/                   # React + Vite frontend
│   ├── src/
│   │   ├── api.js             # API service layer
│   │   ├── App.jsx            # Main app component
│   │   ├── components/        # Reusable components
│   │   └── pages/             # Page components
│   ├── vite.config.js         # Vite config with API proxy
│   └── package.json
│
├── model-training/             # Model training scripts
│   ├── anomaly_ensemble/
│   ├── drift_model/
│   ├── src/                   # Shared source modules
│   └── requirements.txt
│
├── docker-compose.yml         # Docker Compose configuration
├── package.json               # Root package.json with workspaces
└── README.md                  # This file
```

## Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
API_HOST=0.0.0.0
API_PORT=8000
MODEL_PATH=./models
OUTPUT_PATH=./outputs
```

Create a `.env` file in the `frontend/` directory:

```env
VITE_API_URL=http://localhost:8000
```

### Input Data Format

Input CSV should have one row per checkpoint measurement per DUT:

| Column | Type | Description |
|--------|------|-------------|
| `dut_id` | string | Device Under Test identifier |
| `lot_id` | string | Manufacturing lot identifier |
| `checkpoint_h` | int | Burn-in checkpoint (0, 24, 96, 168) |
| `temperature_c` | float | Temperature in Celsius |
| `vcc_v` | float | Supply voltage |
| `iddq_uA` | float | Quiescent current |
| `leakage_uA` | float | Leakage current |
| `delay_ns` | float | Propagation delay |

The `calibration_source` column is automatically excluded from features.

## Docker Deployment

### Build Images

```bash
docker-compose build
```

### Run Services

```bash
docker-compose up -d
```

### Logs

```bash
docker-compose logs -f backend
```

### Stop Services

```bash
docker-compose down
```

## Testing

### Backend Tests

```bash
cd backend
python -m pytest tests/ -v
```

### Frontend Tests

```bash
cd frontend
npm test
```

### Manual Testing

```bash
# Test API health
curl http://localhost:8000/health

# Test dashboard data
curl http://localhost:8000/api/duts
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

---

**BurnInGuard AI 2.0** -- Physics-informed, explainable PASS/FAIL prediction for component burn-in screening.
