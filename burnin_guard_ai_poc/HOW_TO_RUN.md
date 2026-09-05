# How to Run — BurnInGuard AI 2.0 PoC

Follow these steps in order. Total setup time: ~5 minutes.

## 0. Requirements

- Python 3.9–3.12
- ~500 MB free disk space (for dependencies)
- Works on Windows, macOS, and Linux

## 1. Unzip and open a terminal in the project folder

```bash
unzip BurnInGuard_AI_PoC.zip
cd burnin_guard_ai_poc
```

## 2. (Recommended) Create a virtual environment

```bash
python3 -m venv venv

# Activate it:
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

> If `pip install shap` fails or is slow on your machine, that's fine — skip it
> (comment it out of `requirements.txt` or `pip install -r requirements.txt --no-deps`
> won't be needed; just `pip install numpy pandas scikit-learn xgboost streamlit
> plotly` instead). The pipeline automatically falls back to built-in feature
> importances when `shap` isn't available, so nothing breaks.

## 4. Run the end-to-end AI pipeline

This generates synthetic burn-in data, trains all models, and writes results:

```bash
python src/pipeline.py
```

You should see 8 numbered stages print to the console, ending with:

```
Done. Results written to: .../outputs/results.csv
Now run:  streamlit run dashboard/app.py
```

This creates:
- `data/synthetic_burnin_data.csv` — the raw synthetic telemetry
- `outputs/results.csv` — per-DUT features, anomaly scores, drift predictions, risk scores
- `outputs/audit_log.csv` — every HIGH/CRITICAL flag raised
- `outputs/shap_feature_importance.json` — global feature importances per parameter
- `outputs/evaluation_report.txt` — offline precision/recall vs. synthetic ground truth

## 5. Launch the dashboard

```bash
streamlit run dashboard/app.py
```

Your browser should open automatically to `http://localhost:8501`. If it doesn't,
open that URL manually.

**Dashboard tabs:**
1. **Live Risk Heatmap** — every DUT colour-coded by fused risk score, plus a sortable table
2. **Parameter Trends** — pick a DUT, see its measured trend + predicted 168h value with a confidence interval, vs. the static safety limit
3. **Digital Twin** — projected parameter values at 500h with remaining-margin gauges
4. **Explainability** — plain-language reasons for every HIGH/CRITICAL flag, plus global SHAP feature importance
5. **Audit Log** — downloadable CSV of every flag raised, for traceability
6. **Model Evaluation** — offline precision/recall against the known synthetic ground truth (PoC validation only)

You can re-run the pipeline with fresh random data at any time using the
**"🔄 Regenerate data & re-run pipeline"** button in the sidebar.

## 6. (Optional) Run the federated-learning concept demo

This is a separate, standalone script illustrating Section 5.6 (Federated Learning
Across Test Labs) — it simulates 3 independent test labs and shows how their models can
be combined via Federated Averaging without sharing raw data:

```bash
python src/federated_demo.py
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'xgboost'` | `pip install xgboost` — or ignore it, `drift_model.py` will automatically fall back to scikit-learn's `GradientBoostingRegressor` |
| `ModuleNotFoundError: No module named 'shap'` | Optional dependency — safe to skip, explainability falls back to built-in feature importances |
| Streamlit opens a blank page / "No results found" | Run `python src/pipeline.py` first, then launch the dashboard |
| Port 8501 already in use | `streamlit run dashboard/app.py --server.port 8502` |
| Want more/fewer DUTs for a faster demo | Edit the call at the bottom of `src/pipeline.py`: `run_pipeline(n_lots=..., duts_per_lot=..., anomaly_fraction=...)` |

## Demo script suggestion (for your SIH pitch)

1. Open the dashboard with the pipeline already run.
2. Start on the **Risk Heatmap** tab — point out the handful of red/orange cells among
   mostly green ones.
3. Click into **Parameter Trends** for one CRITICAL DUT — show that its measured value is
   still *within* the static limit, but the predicted trajectory (with confidence band)
   crosses it.
4. Switch to **Explainability** — read out the plain-language reason live.
5. Show the **Digital Twin** gauge for the same DUT projected to 500h.
6. Finish on **Audit Log** — emphasize traceability for a regulated/aerospace context.
