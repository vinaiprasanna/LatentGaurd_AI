# BurnInGuard AI 2.0 - Model Training

Trains and exports models for BurnInGuard AI 2.0.

## Structure

```
model-training/
├── src/              # All ML source modules (11 files)
├── anomaly_ensemble/
│   ├── train.py      # Trains HybridAnomalyEnsemble (XGBoost + RF + PCA-SPC)
│   └── export.py     # Exports to backend/models/anomaly_ensemble_model.pkl
├── drift_model/
│   ├── train.py      # Trains per-parameter DriftPredictor
│   └── export.py     # Exports to backend/models/drift_model.pkl
├── data/             # Training data (large_physics_calibrated_burnin_dataset.csv)
├── outputs/          # Training outputs
└── requirements.txt
```

## Usage

### Train and export anomaly ensemble
```bash
python anomaly_ensemble/train.py
```

### Train and export drift model
```bash
python drift_model/train.py
```

### Train both
```bash
python anomaly_ensemble/train.py && python drift_model/train.py
```

## Data

Uses `large_physics_calibrated_burnin_dataset.csv` (20,000 rows, NASA_MOSFET real curve fit data).
The `calibration_source` column is automatically excluded from features.

## Output

Models are exported to `backend/models/` as pickle files:
- `anomaly_ensemble_model.pkl` - HybridAnomalyEnsemble object
- `drift_model.pkl` - Dict of 3 DriftPredictor objects (one per parameter)

## Requirements

Install with: `pip install -r requirements.txt`

Requires: numpy, pandas, scikit-learn, xgboost, scipy, shap
