# BurnInGuard AI 2.0

Physics-informed, explainable PASS/FAIL prediction for component burn-in screening.

## Quick Start

```bash
# Terminal 1 - Backend
cd backend
python3 -m venv venv
venv\script\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Frontend
cd frontend
npm install
npm run dev

# Terminal 3 - Model Training (optional)
cd model-training
pip install -r requirements.txt
python anomaly_ensemble/train.py
python drift_model/train.py
```

- Frontend: **http://localhost:3000**
- API: **http://localhost:8000**
- API Docs: **http://localhost:8000/docs**

See [../README.md](../README.md) for full documentation.
