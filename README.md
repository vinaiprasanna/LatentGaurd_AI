# BurnInGuard AI 2.0

Physics-informed, explainable PASS/FAIL prediction for component burn-in screening.

[![CI/CD](https://github.com/ISRO-BurnInGuard/burninguard-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/ISRO-BurnInGuard/burninguard-ai/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-2.0.0-green.svg)](CHANGELOG.md)

BurnInGuard AI 2.0 is an AI-powered component screening system that predicts PASS/FAIL outcomes for burn-in tested components. It combines:

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
- [License](#license)

## Overview

BurnInGuard AI 2.0 predicts PASS/FAIL outcomes for component burn-in screening using a combination of machine learning and physics-informed models. The system provides:

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

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd BurnInGuard-AI

# Install all dependencies (Linux/macOS)
./scripts/install-dependencies

# Or use the Makefile
make install
```

- Frontend: **http://localhost:3000**
- API: **http://localhost:8000**
- API Docs: **http://localhost:8000/docs**

All scripts support Linux, macOS, and Windows (via Git Bash/WSL). Use `./scripts/<command>` or `make <target>`.

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd BurnInGuard-AI
```

### 2. Install Python dependencies

The backend and model-training packages each have their own `requirements.txt`:

```bash
cd backend && pip install -r requirements.txt
cd ../model-training && pip install -r requirements.txt
```

### 3. Install Node.js dependencies

```bash
cd ../frontend && npm install
```

Alternatively, use the automated installer script (see [Quick Start](#quick-start)).

## Running the Application

All scripts work on Linux, macOS, and Windows (via Git Bash/WSL). Use `./scripts/<command>` or `make <target>`.

### Option A: Individual Processes (Recommended for Development)

Open **three terminal windows**:

**Terminal 1 — Backend API Server:**
```bash
./scripts/run-backend
# or: make dev-backend
```

**Terminal 2 — Frontend Dev Server:**
```bash
./scripts/run-frontend
# or: make dev-frontend
```

**Terminal 3 — (Optional) Model Training:**
```bash
./scripts/train-models
# or: make train
```

### Option B: All at Once

```bash
# From the project root
make dev
```

Or using npm:

```bash
npm run dev
```

This starts both backend and frontend simultaneously using `concurrently`.

### Option C: Docker Compose

```bash
# Start all services
make up
# or: docker-compose up --build

# Start only backend + frontend
docker-compose up --build backend frontend

# Start training service separately
docker-compose up --build --profile training model-training
```

The application will be available at:
- Frontend: **http://localhost:3000**
- API: **http://localhost:8000**
- API Docs: **http://localhost:8000/docs** (Swagger UI)

### Common Makefile Targets

| Target | Description |
|--------|-------------|
| `make install` | Install all dependencies |
| `make dev` | Start backend and frontend |
| `make dev-backend` | Start backend only |
| `make dev-frontend` | Start frontend only |
| `make train` | Train all ML models |
| `make build` | Build Docker images |
| `make up` | Start all services with Docker Compose |
| `make down` | Stop all Docker services |
| `make logs` | View backend logs |
| `make test` | Run all tests |
| `make clean` | Remove generated artifacts |

## Model Training

Before running predictions, train and export the models:

```bash
# Cross-platform (auto-detects OS)
./scripts/train-models

# Or using Makefile
make train

# Or manually
cd model-training
pip install -r requirements.txt
python anomaly_ensemble/train.py
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
BurnInGuard-AI/
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
├── scripts/                    # Utility scripts (cross-platform)
│   ├── install-dependencies    # Auto-detects OS (Linux/macOS/Windows)
│   ├── install-dependencies.sh # POSIX shell variant
│   ├── install-dependencies.bat # Windows batch variant
│   ├── run-backend             # Auto-detects OS
│   ├── run-backend.sh          # POSIX shell variant
│   ├── run-backend.bat         # Windows batch variant
│   ├── run-frontend            # Auto-detects OS
│   ├── run-frontend.sh         # POSIX shell variant
│   ├── run-frontend.bat        # Windows batch variant
│   ├── train-models            # Auto-detects OS
│   ├── train-models.sh         # POSIX shell variant
│   └── train-models.bat        # Windows batch variant
├── Makefile                    # Cross-platform build targets (make install, make dev, etc.)
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

## License

This project is licensed under the MIT License.

---

**BurnInGuard AI 2.0** — Physics-informed, explainable PASS/FAIL prediction for component burn-in screening.
