# BurnInGuard AI 2.0 — Proof of Concept

**SIH 2026 — "AI-Based Anomaly Detection in Component Burn-In and Screening"**

This is a runnable proof-of-concept implementing the architecture described in the
BurnInGuard AI 2.0 solution blueprint: physics-informed feature engineering, a hybrid
ensemble anomaly detector, physics-informed drift prediction with uncertainty, Bayesian
risk fusion, explainability, a digital twin, and a federated-learning concept demo — all
wrapped in an interactive Streamlit dashboard.

➡️ **First time here? Open `HOW_TO_RUN.md` for step-by-step setup instructions.**

## What's inside

```
burnin_guard_ai_poc/
├── HOW_TO_RUN.md              <- start here
├── README.md                  <- this file
├── requirements.txt
├── data/                      <- synthetic burn-in telemetry (generated on first run)
├── outputs/                   <- pipeline results (generated on first run)
├── src/
│   ├── data_generator.py      <- synthetic burn-in data generator
│   ├── features.py            <- physics-informed + statistical feature engineering
│   ├── anomaly_ensemble.py    <- Isolation Forest + Autoencoder + One-Class SVM + Mahalanobis
│   ├── drift_model.py         <- XGBoost drift prediction + 10/90 quantile intervals
│   ├── digital_twin.py        <- physics-based "what-if" projection beyond 168h
│   ├── risk_engine.py         <- Bayesian-style risk fusion + confidence scoring
│   ├── explainability.py      <- SHAP-based (or fallback) plain-language explanations
│   ├── federated_demo.py      <- standalone FedAvg concept demo across simulated labs
│   └── pipeline.py            <- runs everything end-to-end, writes outputs/results.csv
└── dashboard/
    └── app.py                 <- Streamlit dashboard (heatmap, trends, twin, explainability, audit log)
```

## Important note on the data

All data in this PoC is **synthetically generated** (see `src/data_generator.py`) to
demonstrate the pipeline end-to-end. It must never be presented as real ISRO / DRDO /
manufacturer test data. To use this on real burn-in telemetry, replace
`data_generator.py` with a loader for your actual DAQ/ATE export in the same schema
(`dut_id, lot_id, checkpoint_h, temperature_c, vcc_v, iddq_uA, leakage_uA, delay_ns, status`).

## Mapping back to the solution blueprint

| Blueprint section | Code |
|---|---|
| 5.1 Physics-Informed Feature Engineering | `src/features.py` |
| 5.2 Hybrid Ensemble Anomaly Detection | `src/anomaly_ensemble.py` |
| 5.3 Physics-Informed Drift Prediction | `src/drift_model.py` |
| 5.4 Bayesian Risk Fusion & Uncertainty | `src/risk_engine.py` |
| 5.5 Explainable AI & Audit Trail | `src/explainability.py`, `outputs/audit_log.csv` |
| 5.6 Federated Learning Across Test Labs | `src/federated_demo.py` |
| 5.7 Digital Twin of the DUT | `src/digital_twin.py` |
| 8. Dashboard & UX | `dashboard/app.py` |

## Honest scope of this PoC

- The anomaly ensemble and drift models are unsupervised / self-supervised — they never
  see the synthetic ground-truth label during fitting. That label is used **only** in the
  "Model Evaluation" dashboard tab, to sanity-check the pipeline against known injected
  anomalies.
- The federated-learning script is a standalone, self-contained illustration of the
  Federated Averaging concept (3 simulated labs) — it is not wired into the main
  pipeline, since a true multi-node federated deployment is out of scope for a
  single-machine PoC.
- The digital twin is a simplified analytical projection (re-applies the fitted
  physics-normalised drift rate forward in time), not a full physics/circuit simulator.
- Risk-score thresholds and fusion weights are PoC defaults (see `src/risk_engine.py`)
  and must be re-calibrated against real reliability data before any production use —
  this is stated explicitly in the dashboard and in the solution blueprint PDF.
