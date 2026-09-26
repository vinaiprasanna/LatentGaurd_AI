# Model Training

## Overview

BurnInGuard AI 2.0 uses two primary ML models that must be trained before predictions can be made:

1. **Anomaly Ensemble** — Detects anomalous components using XGBoost, Random Forest, and PCA-SPC
2. **Drift Model** — Predicts parametric degradation beyond burn-in

## Prerequisites

```bash
cd model-training
pip install -r requirements.txt
```

## Training

### Train Anomaly Ensemble

```bash
python anomaly_ensemble/train.py
```

This trains the hybrid anomaly ensemble and exports it to `backend/models/anomaly_ensemble_model.pkl`.

### Train Drift Model

```bash
python drift_model/train.py
```

This trains the physics-informed drift models and exports them to `backend/models/drift_model.pkl`.

### Train Both

```bash
# Linux/macOS
./scripts/train-models.sh

# Windows (CMD)
scripts\train-models.bat

# Windows (PowerShell)
scripts\train-models.ps1

# Or manually
python anomaly_ensemble/train.py && python drift_model/train.py
```

## Model Artifacts

After training, the following files are generated in `backend/models/`:

| File | Description |
|------|-------------|
| `anomaly_ensemble_model.pkl` | Trained anomaly ensemble (XGBoost + RF + PCA-SPC) |
| `drift_model.pkl` | Dictionary of drift models per parameter |
| `validation_metrics.json` | Anomaly validation metrics and threshold |
| `drift_validation_metrics.json` | Drift model validation metrics |

## Training Data

The models are trained on the dataset at:
```
model-training/data/large_physics_calibrated_burnin_dataset.csv
```

The dataset contains labeled burn-in measurements with `true_latent_defect` targets for validation.

## Retraining

To retrain models with new data:

1. Place the new dataset in `model-training/data/`
2. Run the training scripts
3. Verify the new artifacts are generated in `backend/models/`
4. Restart the backend to load the new models

## Feature Schema

Feature schema version: **32**

The following feature types are used:
- Normalized parameters across checkpoints
- Physics-normalized slopes
- Arrhenius acceleration factors
- Lot z-scores
- Early burn-in signal features (`_0h` columns)
