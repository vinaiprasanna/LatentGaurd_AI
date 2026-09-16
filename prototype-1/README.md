# BurnInGuard AI 2.0 — Trial 2 (XGBoost + Random Forest + PCA-SPC)

**SIH 2026 — "AI-Based Anomaly Detection in Component Burn-In and Screening"**

This project extends the BurnInGuard AI PoC with a new hybrid anomaly
detection ensemble combining **XGBoost**, **Random Forest**, and **PCA-SPC**
(Principal Component Analysis + Statistical Process Control).

## Ensemble Architecture

| Detector | Type | Weight | Description |
|---|---|---:|---|
| XGBoost | Supervised | 0.35 | Gradient-boosted tree classifier producing anomaly probability |
| Random Forest | Supervised | 0.35 | Ensemble tree classifier producing anomaly probability |
| PCA-SPC | Unsupervised | 0.30 | PCA dimensionality reduction + Hotelling's T² and Q statistics from SPC |

Each detector's raw score is min-max normalised to [0, 1] and combined via
weighted averaging into a single calibrated anomaly probability.

## Dataset

Same synthetic burn-in telemetry as `burnin_guard_ai_poc`:
- 8 lots × 45 DUTs = 360 DUTs, 1,440 checkpoint rows
- 4 checkpoints: 0h, 24h, 96h, 168h
- 3 monitored parameters: iddq_uA, leakage_uA, delay_ns
- ~9% latent defects injected

## Running

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the end-to-end pipeline
python src/pipeline.py
```

## Output Files

- `data/synthetic_burnin_data.csv` — raw synthetic telemetry
- `outputs/results.csv` — per-DUT features, anomaly scores, drift predictions, risk scores
- `outputs/audit_log.csv` — every HIGH/CRITICAL flag raised
- `outputs/evaluation_report.txt` — precision/recall vs. synthetic ground truth
- `outputs/shap_feature_importance.json` — global feature importances per parameter

## Evaluation Metrics

The pipeline produces the same classification evaluation as the original
`burnin_guard_ai_poc`:

```
               precision    recall  f1-score   support

       normal       0.96      1.00      0.98       328
latent_defect       1.00      0.53      0.69        32

     accuracy                           0.96       360
    macro avg       0.98      0.77      0.84       360
 weighted avg       0.96      0.96      0.95       360
```

## Project Structure

```
project-trial-2/
├── data/                      <- synthetic burn-in telemetry
├── outputs/                   <- pipeline results
├── src/
│   ├── data_generator.py      <- synthetic burn-in data generator
│   ├── features.py            <- physics-informed + statistical feature engineering
│   ├── spc.py                 <- PCA-SPC anomaly detector
│   ├── anomaly_ensemble.py    <- XGBoost + Random Forest + PCA-SPC ensemble
│   ├── drift_model.py         <- XGBoost drift prediction + 10/90 quantile intervals
│   ├── digital_twin.py        <- physics-based "what-if" projection
│   ├── risk_engine.py         <- Bayesian risk fusion + confidence scoring
│   ├── explainability.py      <- Plain-language explanations
│   └── pipeline.py            <- End-to-end pipeline
├── requirements.txt
├── README.md
└── .gitignore
```

## How It Differs from Trial 1

The original `burnin_guard_ai_poc` used a 4-detector unsupervised ensemble
(Isolation Forest + Autoencoder + One-Class SVM + Mahalanobis). Trial 2
replaces this with a 3-detector ensemble using supervised (XGBoost, Random
Forest) and unsupervised (PCA-SPC) methods, providing complementary detection
strengths.

> **Note:** All data is synthetic. Labels are only used for model training
> (PoC) and evaluation. The PCA-SPC component remains fully unsupervised.
