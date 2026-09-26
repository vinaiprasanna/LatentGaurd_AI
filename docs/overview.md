# Project Overview

BurnInGuard AI 2.0 is a physics-informed, explainable PASS/FAIL prediction system for component burn-in screening. It is developed for ISRO and targets high-reliability electronics screening.

## Core Capabilities

- **Anomaly Detection**: Hybrid ensemble of XGBoost, Random Forest, and PCA-SPC detects anomalous components during burn-in.
- **Physics-Informed Drift Modeling**: Predicts parametric degradation beyond the burn-in window using physics-based models.
- **Digital Twin Projection**: Fast-forwards component trajectories to 500 hours and computes remaining margins.
- **Risk Fusion Engine**: Combines anomaly scores, lot deviations, drift rates, and future margins into a single 0–100 risk score.
- **Explainability**: Provides plain-language explanations, evidence chains, driver evidence, and recommended confirmation tests for every prediction.

## Risk Bands

| Score | Band | Outcome |
|-------|------|---------|
| 0–30 | LOW | PASS |
| 30–60 | MEDIUM | PASS |
| 60–80 | HIGH | FAIL |
| 80–100 | CRITICAL | FAIL |

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, FastAPI |
| Frontend | React 18, Vite |
| ML Models | XGBoost, Random Forest, scikit-learn, PCA |
| Infrastructure | Docker, Docker Compose |
| CI/CD | GitHub Actions |
