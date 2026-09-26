# LatentGuard AI

Physics-informed, explainable PASS/FAIL prediction for component burn-in screening.

LatentGuard AI is an AI-powered component screening system that predicts PASS/FAIL outcomes for burn-in tested components. It combines:

- **Hybrid Anomaly Ensemble** (XGBoost + Random Forest + PCA-SPC) for anomaly detection
- **Physics-Informed Drift Models** for predicting component behaviour beyond burn-in
- **Digital Twin Projection** for fast-forwarding component trajectories to 500h
- **Risk Fusion Engine** combining anomaly, lot deviation, drift rate, and future margin into a single 0–100 risk score
- **Explainability Layer** providing plain-language reasons for each prediction

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Model Training](#model-training)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Docker Deployment](#docker-deployment)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Contributing](#contributing)

## Overview

LatentGuard AI predicts PASS/FAIL outcomes for component burn-in screening using a combination of machine learning and physics-informed models. The system provides:

| Component | Description |
|-----------|-------------|
| **Anomaly Ensemble** | Hybrid XGBoost + Random Forest + PCA-SPC for anomaly detection |
| **Drift Models** | Physics-informed models predicting component behaviour beyond burn-in |
| **Digital Twin** | Projects component trajectories to 500h with margin analysis |
| **Risk Engine** | Fuses anomaly, lot deviation, drift, and margin into a 0–100 risk score |
| **Explainability** | Plain-language explanations and evidence chains for every prediction |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)               │
│  Dashboard │ Anomaly Analysis │ Digital Twin │ Explain  │
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
│  anomaly_ensemble_model.pkl  │ drift_model.pkl          │
└──────────────────┬──────────────────────────────────────┘
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

## Platform Support

All scripts work on **Windows (CMD)**, **Windows (PowerShell)**, **macOS**, and **Linux**.

| Platform | Install | Train | Dev | Other |
|----------|---------|-------|-----|-------|
| Windows CMD | `scripts\install-dependencies.bat` | `scripts\train-models.bat` | `scripts\run-backend.bat` + `scripts\run-frontend.bat` | `npm run build`, `npm test`, `npm run clean` |
| PowerShell | `scripts\install-dependencies.ps1` | `scripts\train-models.ps1` | `scripts\run-backend.ps1` + `scripts\run-frontend.ps1` | `npm run build`, `npm test`, `npm run clean` |
| macOS / Linux | `./scripts/install-dependencies.sh` | `./scripts/train-models.sh` | `npm run dev` | `npm run build`, `npm test`, `npm run clean` |
| Cross-platform (npm) | `npm run install:all` | `npm run train` | `npm run dev` | `npm run build`, `npm test`, `npm run clean`, `npm run setup` |

**PowerShell users:** If a `.ps1` script won't run, execute `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` once.

## Quick Start

```bash
git clone <repository-url>
cd LatentGuard-AI
```

Install dependencies and train models:

**Windows:**
```cmd
scripts\install-dependencies.bat
scripts\train-models.bat
scripts\run-backend.bat
```
and then in another terminal:
```cmd
scripts\run-frontend.bat
```

**macOS / Linux:**
```bash
./scripts/install-dependencies.sh
./scripts/train-models.sh
npm run dev
```

That's it. Frontend at **http://localhost:3000**, API at **http://localhost:8000**.

Or use the quick setup command to do it all at once:

```bash
npm run setup
```

This runs: install → train → dev.

## Installation

### Step 1 — Clone the repo

```bash
git clone <repository-url>
cd LatentGuard-AI
```

### Step 2 — Install dependencies

**Windows (CMD):**
```cmd
scripts\install-dependencies.bat
```

**Windows (PowerShell):**
```powershell
scripts\install-dependencies.ps1
```

**macOS / Linux:**
```bash
./scripts/install-dependencies.sh
```

Or cross-platform via npm:
```bash
npm run install:all
```

This sets up Python virtual environments and installs all packages automatically.

### Step 3 — Verify

```bash
cd backend && python -c "import fastapi; print('OK')"
cd ../frontend && npx vite --version
```

## Running the Application

### Quick setup (install → train → run)

**Cross-platform (recommended):**
```bash
npm run setup
```
This runs: install → train → starts both backend and frontend.

**Windows:**
```cmd
scripts\install-dependencies.bat
scripts\train-models.bat
scripts\run-backend.bat
```
Then in another terminal:
```cmd
scripts\run-frontend.bat
```

**macOS / Linux:**
```bash
./scripts/install-dependencies.sh
./scripts/train-models.sh
./scripts/run-backend.sh
```
Then in another terminal:
```bash
./scripts/run-frontend.sh
```

### Step by step

**Terminal 1 — Backend:**

**Cross-platform:**
```bash
npm run dev:backend
```

**Windows (CMD):**
```cmd
scripts\run-backend.bat
```

**macOS / Linux:**
```bash
./scripts/run-backend.sh
```

**Terminal 2 — Frontend:**

**Cross-platform:**
```bash
npm run dev:frontend
```

**Windows (CMD):**
```cmd
scripts\run-frontend.bat
```

**macOS / Linux:**
```bash
./scripts/run-frontend.sh
```

**Terminal 3 — Train models (first time only):**

**Cross-platform:**
```bash
npm run train
```

**Windows (CMD):**
```cmd
scripts\train-models.bat
```

**macOS / Linux:**
```bash
./scripts/train-models.sh
```

### Docker

```bash
docker-compose up
```

### Other Commands

| Command | What it does | Works on |
|---------|-------------|----------|
| `npm run install:all` | Install all dependencies | All platforms |
| `npm run train` | Train ML models | All platforms |
| `npm run dev` | Start backend + frontend | All platforms |
| `npm run dev:backend` | Start backend only | All platforms |
| `npm run dev:frontend` | Start frontend only | All platforms |
| `npm run setup` | Quick setup (install → train → dev) | All platforms |
| `npm run build` | Build frontend | All platforms |
| `npm test` | Run all tests | All platforms |
| `npm run clean` | Remove generated files | All platforms |
| `scripts\*.bat` | Windows CMD direct | Windows CMD |
| `scripts\*.ps1` | PowerShell direct | Windows PowerShell |
| `scripts\*.sh` | macOS/Linux direct | macOS / Linux |

## API Documentation

All API endpoints are available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/status` | Model loading status |
| GET | `/api/model-metrics` | Model diagnostics and feature importance |
| GET | `/api/duts` | Get all DUT data with risk scores |
| GET | `/api/duts/{dut_id}` | Get individual DUT data |
| GET | `/api/dashboard/stats` | Dashboard KPI statistics |
| GET | `/api/audit-log` | Get audit log entries |
| GET | `/api/audit-jobs` | Get audit job provenance records |
| GET | `/api/review-actions` | Get reviewer actions |
| POST | `/api/review-actions` | Record a reviewer action |
| POST | `/predict` | Upload CSV, get predictions |
| POST | `/predict/batch` | Upload CSV, get summary + save CSV |
| POST | `/api/chat` | Query COSMO failure chatbot |

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

### GET /api/model-metrics

Returns loaded model diagnostics including feature importance, training metrics, and drift validation results.

### GET /api/dashboard/stats

Returns dashboard KPI statistics including total components, anomaly rate, and pass rate.

## Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
API_HOST=0.0.0.0
API_PORT=8000
MODEL_PATH=./models
OUTPUT_PATH=./outputs
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
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

## Model Training

First time setup — train models after installing dependencies:

```bash
# Cross-platform (recommended)
npm run train

# Windows (CMD)
scripts\train-models.bat

# macOS / Linux
./scripts/train-models.sh
```

Models are saved to `backend/models/`:
- `anomaly_ensemble_model.pkl`
- `drift_model.pkl`

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

## Project Structure

```
LatentGuard-AI/
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
│   │   ├── data_generator.py  # Synthetic data generator
│   │   ├── data_cleaner.py    # CSV cleaning and validation
│   │   └── failure_chatbot.py # COSMO chatbot integration
│   ├── models/                # Trained model pickles
│   ├── outputs/               # Prediction outputs and audit logs
│   └── prediction_input.csv   # Sample input CSV
│
├── docs/                       # Documentation
│   ├── architecture.md        # System architecture details
│   ├── api-reference.md       # API endpoint reference
│   ├── contributing.md        # Contributing guidelines
│   ├── deployment.md          # Deployment guides
│   ├── installation.md        # Installation guide
│   ├── model-training.md      # Model training documentation
│   └── overview.md            # Project overview
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
├── scripts/                    # Scripts for all platforms
│   ├── install-dependencies.sh # macOS / Linux
│   ├── install-dependencies.bat # Windows CMD
│   ├── install-dependencies.ps1 # Windows PowerShell
│   ├── run-backend.sh          # macOS / Linux
│   ├── run-backend.bat         # Windows CMD
│   ├── run-backend.ps1         # Windows PowerShell
│   ├── run-frontend.sh         # macOS / Linux
│   ├── run-frontend.bat        # Windows CMD
│   ├── run-frontend.ps1        # Windows PowerShell
│   ├── train-models.sh         # macOS / Linux
│   ├── train-models.bat        # Windows CMD
│   └── train-models.ps1        # Windows PowerShell
│
├── docker-compose.yml         # Docker Compose configuration
├── package.json               # Root package.json with workspaces
└── README.md                  # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

**LatentGuard AI** — Physics-informed, explainable PASS/FAIL prediction for component burn-in screening.
