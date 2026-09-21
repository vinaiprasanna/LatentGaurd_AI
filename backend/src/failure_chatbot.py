"""Fast, deterministic COSMO operator for BurnInGuard AI.

COSMO = Component Observation & Screening Monitoring Operator.
It uses the pipeline's actual results and performs safe, read-only analysis tasks.
No external LLM/API is required.
"""
import math
import re

PARAM_LABELS = {
    "iddq_uA": "IDDQ current",
    "leakage_uA": "leakage current",
    "delay_ns": "propagation delay",
}
STATIC_LIMITS = {"iddq_uA": 50.0, "leakage_uA": 10.0, "delay_ns": 8.0}


def _num(row, key, default=0.0):
    try:
        value = float(row.get(key, default))
        return value if math.isfinite(value) else default
    except (TypeError, ValueError):
        return default


def _pct_change(row, p):
    start = _num(row, f"{p}_0h")
    last = _num(row, f"{p}_last")
    if abs(start) < 1e-12:
        return 0.0
    return (last - start) / abs(start) * 100.0


def _raw_dut(raw_data, dut_id):
    if raw_data is None or not dut_id or "dut_id" not in raw_data.columns:
        return None
    return raw_data[raw_data["dut_id"].astype(str) == str(dut_id)].sort_values("checkpoint_h")


def _dut_analysis(row):
    band = str(row.get("risk_band", "UNKNOWN"))
    anomaly = _num(row, "anomaly_ensemble_score")
    return (f"### DUT Analysis: {row.get('dut_id', 'Selected DUT')}\n\n"
            f"Risk band: **{band}**\n\nRisk score: **{_num(row, 'risk_score'):.1f}/100**\n\n"
            f"Anomaly probability: **{anomaly * 100:.1f}%**\n\n"
            f"Model outcome: **{row.get('predicted_outcome', 'UNKNOWN')}**\n\n"
            f"Evidence: {row.get('explanation', 'No pipeline explanation is available.')}")


def _anomaly_probability(row):
    score = _num(row, "anomaly_ensemble_score")
    return (f"### Anomaly Probability: {row.get('dut_id', 'Selected DUT')}\n\n"
            f"Ensemble anomaly probability: **{score * 100:.1f}%**\n\n"
            f"Risk classification: **{row.get('risk_band', 'UNKNOWN')}** with risk score **{_num(row, 'risk_score'):.1f}/100**.\n\n"
            "This is the normalized ensemble score, not a calibrated probability guarantee.")


def _latent_defect_answer(row):
    band = str(row.get("risk_band", "UNKNOWN"))
    anomaly = _num(row, "anomaly_ensemble_score")
    lot = _num(row, "_component_lot_deviation")
    drift = _num(row, "_component_drift_rate")
    if band in ("HIGH", "CRITICAL"):
        conclusion = "potential latent defect / investigation candidate"
    else:
        conclusion = "normal or non-critical outlier; no latent-defect conclusion should be made without confirmation"
    return (f"### Outlier Interpretation: {row.get('dut_id')}\n\n"
            f"Classification: **{conclusion}**.\n\n"
            f"Evidence signals: anomaly **{anomaly:.3f}**, lot deviation **{lot:.3f}**, drift rate **{drift:.3f}**.\n\n"
            "The model flags abnormal behavior relative to learned population patterns; it does not prove a physical defect.")


def _highest_anomaly(results):
    row = results.sort_values("anomaly_ensemble_score", ascending=False).iloc[0]
    return (f"### Highest Anomaly Score\n\n**{row['dut_id']}** has the highest ensemble anomaly score: "
            f"**{_num(row, 'anomaly_ensemble_score') * 100:.1f}%**, risk **{row['risk_band']}**, score **{_num(row, 'risk_score'):.1f}/100**.")


def _normal_range(row, results, raw_data):
    lines = [f"### Normal Range vs Observed: {row.get('dut_id')}", ""]
    peers = results[results["lot_id"].astype(str) == str(row.get("lot_id"))]
    for parameter in PARAM_LABELS:
        field = f"{parameter}_last"
        observed = _num(row, field)
        values = peers[field].astype(float) if field in peers else None
        if values is not None and len(values) > 1:
            mean, std = float(values.mean()), float(values.std())
            lines.append(f"- **{PARAM_LABELS[parameter]}:** observed **{observed:.3f}**, lot normal range approximately **{mean - 2 * std:.3f} to {mean + 2 * std:.3f}** (mean ± 2σ)")
        else:
            lines.append(f"- **{PARAM_LABELS[parameter]}:** observed **{observed:.3f}**, peer range unavailable")
    return "\n".join(lines)


def _safety_projection(row):
    lines = [f"### Safety-Crossing Projection: {row.get('dut_id')}", ""]
    for parameter, limit in STATIC_LIMITS.items():
        current = _num(row, f"{parameter}_last")
        future = _num(row, f"{parameter}_projected_500h")
        if current >= limit:
            estimate = "already at or beyond the configured limit"
        elif future <= limit or future <= current:
            estimate = "not projected to cross the limit by 500h"
        else:
            hours = 168 + (limit - current) / (future - current) * (500 - 168)
            estimate = f"approximately **{hours:.0f}h**"
        lines.append(f"- **{PARAM_LABELS[parameter]}:** {estimate} (limit {limit:g}, projected 500h value {future:.3g})")
    lines.append("\nThis is a linear interpolation between the latest observed value and the model's 500h projection, not a new model prediction.")
    return "\n".join(lines)


def _static_status(row, raw_data):
    data = _raw_dut(raw_data, row.get("dut_id"))
    if data is None or data.empty:
        return "Static-limit status cannot be determined because raw checkpoint telemetry is unavailable."
    failures = []
    for parameter, limit in STATIC_LIMITS.items():
        maximum = float(data[parameter].max())
        if maximum > limit:
            failures.append(f"{PARAM_LABELS[parameter]} reached **{maximum:.3g}** against limit **{limit:.3g}**")
    if failures:
        return "### Static Datasheet Limit Check\n\n**FAIL**: " + "; ".join(failures) + "."
    return ("### Static Datasheet Limit Check\n\n**PASS**: all observed checkpoints stayed within the configured limits "
            f"(IDDQ ≤ {STATIC_LIMITS['iddq_uA']:.0f} μA, leakage ≤ {STATIC_LIMITS['leakage_uA']:.0f} μA, delay ≤ {STATIC_LIMITS['delay_ns']:.0f} ns).")


def _telemetry_table(row, raw_data):
    data = _raw_dut(raw_data, row.get("dut_id"))
    if data is None or data.empty:
        return "Checkpoint telemetry is unavailable for this DUT."
    wanted = [0, 24, 96]
    lines = [f"### Checkpoint Telemetry: {row.get('dut_id')}", "", "| Checkpoint | IDDQ (μA) | Leakage (μA) | Delay (ns) |", "|---|---:|---:|---:|"]
    for checkpoint in wanted:
        match = data[data["checkpoint_h"] == checkpoint]
        if match.empty:
            lines.append(f"| {checkpoint}h | unavailable | unavailable | unavailable |")
        else:
            item = match.iloc[0]
            lines.append(f"| {checkpoint}h | {_num(item, 'iddq_uA'):.3f} | {_num(item, 'leakage_uA'):.3f} | {_num(item, 'delay_ns'):.3f} |")
    return "\n".join(lines)


def _lot_comparison(row, results):
    lot = row.get("lot_id")
    peers = results[results["lot_id"].astype(str) == str(lot)]
    if peers.empty:
        return "Lot comparison is unavailable for this DUT."
    lines = [f"### Lot Comparison: {row.get('dut_id')} vs {lot} average", ""]
    for parameter in PARAM_LABELS:
        field = f"{parameter}_last"
        value = _num(row, field)
        average = float(peers[field].mean()) if field in peers else 0.0
        delta = value - average
        lines.append(f"- **{PARAM_LABELS[parameter]}:** DUT **{value:.3f}**, lot average **{average:.3f}**, delta **{delta:+.3f}**")
    return "\n".join(lines)


def _drift_answer(row, question):
    parameter = next((p for p in PARAM_LABELS if p.replace("_uA", "").replace("_ns", "") in question), None)
    parameters = [parameter] if parameter else list(PARAM_LABELS)
    lines = [f"### Drift Analysis: {row.get('dut_id')}", ""]
    for p in parameters:
        change = _pct_change(row, p)
        start = _num(row, f"{p}_0h")
        last = _num(row, f"{p}_last")
        slope = _num(row, f"{p}_slope")
        curvature = _num(row, f"{p}_curvature")
        lines.append(f"- **{PARAM_LABELS[p]}:** 0h **{start:.3f}**, latest **{last:.3f}**, change **{change:+.1f}%**, slope **{slope:.5f}/h**, curvature **{curvature:.6f}**")
    if any(word in question for word in ["significant", "statistically"]):
        zscores = [_num(row, f"{p}_last_lot_zscore") for p in parameters]
        lines.append(f"\nLot-relative significance heuristic: maximum absolute z-score **{max(map(abs, zscores)):.2f}**; values above approximately 2 merit investigation. This is not a formal hypothesis test.")
    if any(word in question for word in ["linear", "non-linear", "nonlinear"]):
        curvature = max((_num(row, f"{p}_curvature") for p in parameters), key=abs)
        lines.append(f"\nTrend shape: **{'non-linear' if abs(curvature) > 1e-6 else 'approximately linear'}** based on the engineered curvature term.")
    return "\n".join(lines)


def _detector_answer(row, model_metrics, question):
    detector_fields = {
        "xgboost": "anomaly_xgboost",
        "random forest": "anomaly_random_forest",
        "random_forest": "anomaly_random_forest",
        "pca": "anomaly_pca_spc",
        "pca-spc": "anomaly_pca_spc",
    }
    lines = [f"### Detector Evidence: {row.get('dut_id')}", ""]
    for label, field in detector_fields.items():
        if field in row:
            lines.append(f"- **{label.upper()}:** {_num(row, field) * 100:.1f}% anomaly score")
    values = [_num(row, field) for field in detector_fields.values() if field in row]
    if values:
        lines.append(f"\nDetector agreement spread: **{max(values) - min(values):.3f}**. The ensemble combines the detector scores with configured weights; it does not require unanimous agreement.")
    if "feature" in question and model_metrics:
        features = model_metrics.get("anomaly_feature_importance", [])[:5]
        lines.append("\nTop learned features: " + ", ".join(f"**{item['feature']}** ({item['importance']:.3f})" for item in features))
    return "\n".join(lines) if len(lines) > 2 else "Individual detector scores are not present in the current API result."


def _model_answer(model_metrics, question):
    if not model_metrics or not model_metrics.get("metrics_available"):
        return "Model evaluation metadata is unavailable. I will not invent accuracy or validation values."
    anomaly = model_metrics.get("anomaly", {})
    test = model_metrics.get("test", {})
    if test.get("available") and any(term in question for term in ["validation", "test accuracy", "test performance", "false negative", "false-negative", "unseen", "rmse", "root mean", "168h"]):
        lines = [f"### Uploaded Test Performance\n\nTest DUTs: **{test['test_duts']}**"]
        if test.get("anomaly_metrics_available"):
            lines.append(f"Accuracy: **{test['accuracy']:.4f}**\nPrecision: **{test['precision']:.4f}**\nRecall: **{test['recall']:.4f}**\nF1-score: **{test['f1']:.4f}**\nFalse-negative rate: **{test['false_negative_rate']:.4f}**")
        if test.get("drift_metrics_available"):
            lines.append("\n168h drift regression metrics:")
            for parameter, values in test["drift"].items():
                lines.append(f"- **{parameter}**: RMSE **{values['rmse']:.4f}**, MAE **{values['mae']:.4f}**, R² **{values['r2']:.4f}**")
        lines.append(f"\nTraining DUT overlap: **{test['overlap_with_training_duts']}**. Independent test: **{'yes' if test['is_independent_test'] else 'no'}**.")
        return "\n".join(lines)
    if "false-negative" in question or "false negative" in question or "miss" in question:
        return "False-negative count and rate are not stored in the current model metadata. They require a held-out labeled evaluation with a defined decision threshold."
    if "threshold" in question or "confidence" in question:
        return "The ensemble decision used by the diagnostics is an anomaly score threshold of **0.50**. Risk confidence is a separate agreement/interval-confidence signal; low confidence should trigger confirmation testing rather than automatic release or failure."
    if "retrain" in question:
        return "Retrain after a validated process change, sensor/calibration change, feature-schema change, or sustained drift in false alarms. Set the cadence from monitored performance; no fixed interval is encoded in this project."
    if "manufacturing process" in question or "process changes" in question:
        return "A process change can shift lot distributions and invalidate learned baselines. Revalidate on post-change lots, monitor false positives/negatives, and retrain only after the new data is quality-checked."
    if "dataset" in question or "trained on" in question:
        return f"The loaded artifacts were trained from the bundled calibrated burn-in dataset with **{model_metrics.get('training_duts', 'unknown')} DUTs** and **{model_metrics.get('feature_count', 'unknown')} engineered features**."
    if "validation" in question or "unseen" in question or "leakage" in question or "held-out" in question:
        return ("### Evaluation Scope\n\nThe available metrics are training-dataset diagnostics only. "
                "No held-out validation, unseen-lot evaluation, or leakage-control report is stored in the current artifacts.")
    if "confusion" in question:
        return "A confusion matrix is not stored in the current model metadata. The available training diagnostics are accuracy, precision, recall, and F1."
    return (f"### Model Performance\n\nTraining DUTs: **{model_metrics.get('training_duts', 'unknown')}**\n\n"
            f"Accuracy: **{anomaly.get('accuracy', 'unavailable')}**\nPrecision: **{anomaly.get('precision', 'unavailable')}**\n"
            f"Recall: **{anomaly.get('recall', 'unavailable')}**\nF1-score: **{anomaly.get('f1', 'unavailable')}**\n\n"
            "These are training diagnostics, not validation accuracy.")


def _drift_metrics_answer(model_metrics, question, row=None):
    test = (model_metrics or {}).get("test", {})
    if test.get("drift_metrics_available"):
        lines = [f"### Drift Model Accuracy: {row.get('dut_id') if row is not None else 'Current Test Set'}", "", "Drift prediction is regression: `true_latent_defect` labels are not required. The measured 168h telemetry is the target."]
        if row is not None:
            lines.append("\nSelected DUT 168h prediction:")
            for parameter, label in PARAM_LABELS.items():
                actual = _num(row, f"{parameter}_last")
                predicted = _num(row, f"{parameter}_pred_168h")
                lines.append(f"- **{label}:** measured **{actual:.3f}**, predicted **{predicted:.3f}**, error **{predicted - actual:+.3f}**")
            lines.append("\nModel metrics across the uploaded test DUTs:")
        for parameter, values in test["drift"].items():
            lines.append(f"- **{parameter}:** RMSE **{values['rmse']:.4f}**, MAE **{values['mae']:.4f}**, R² **{values['r2']:.4f}**")
        lines.append(f"\nEvaluated DUTs: **{test['test_duts']}**. Training overlap: **{test['overlap_with_training_duts']}**.")
        return "\n".join(lines)
    drift = (model_metrics or {}).get("drift", {})
    if drift:
        lines = [f"### Drift Model Accuracy: {row.get('dut_id') if row is not None else 'Training Set'}", "", "No uploaded-test drift metrics are active. These are in-sample training diagnostics:"]
        if row is not None:
            lines.append("\nSelected DUT 168h prediction:")
            for parameter, label in PARAM_LABELS.items():
                actual = _num(row, f"{parameter}_last")
                predicted = _num(row, f"{parameter}_pred_168h")
                lines.append(f"- **{label}:** measured **{actual:.3f}**, predicted **{predicted:.3f}**, error **{predicted - actual:+.3f}**")
        for parameter, values in drift.items():
            lines.append(f"- **{parameter}:** RMSE **{values['rmse']:.4f}**, MAE **{values['mae']:.4f}**, R² **{values['r2']:.4f}**")
        return "\n".join(lines)
    return "Upload a CSV containing measured 168h telemetry to calculate drift RMSE. `true_latent_defect` is not required for drift regression."


def _drift_label_answer():
    return ("### Drift Evaluation\n\nDrift prediction does **not** require `true_latent_defect`. "
            "The model predicts continuous 168h values, and evaluation compares them with measured 168h IDDQ, leakage, and delay values. "
            "Use RMSE, MAE, and R² rather than classification accuracy.")


def _dut_id_from_question(question, results):
    q = question or ""
    ids = [] if results is None else [str(x) for x in results.get("dut_id", [])]
    for dut in ids:
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(dut)}(?![A-Za-z0-9])", q, re.I):
            return dut
    return None


def _requested_id_not_found(question, results):
    if results is None:
        return None
    known = {str(value).upper() for value in results.get("dut_id", [])}
    candidates = re.findall(r"\b(?:DUT|IC)[_-]?\d+\b", question or "", flags=re.I)
    for candidate in candidates:
        normalized = candidate.replace("_", "").replace("-", "").upper()
        if normalized not in {item.replace("_", "").replace("-", "").upper() for item in known}:
            return candidate
    return None


def explain_dut(row):
    band = str(row.get("risk_band", "UNKNOWN"))
    score = _num(row, "risk_score")
    confidence = _num(row, "risk_confidence_pct")
    anomaly = _num(row, "anomaly_ensemble_score")
    changes = {p: _pct_change(row, p) for p in PARAM_LABELS}
    largest_p = max(changes, key=lambda p: abs(changes[p]))
    margin_items = []
    for p, label in PARAM_LABELS.items():
        margin = _num(row, f"{p}_margin_pct_500h", 100.0)
        projected = _num(row, f"{p}_projected_500h")
        margin_items.append((margin, p, label, projected))
    margin_items.sort(key=lambda x: x[0])
    lines = [
        f"**{row.get('dut_id', 'Selected DUT')}** is currently **{band} risk** with a risk score of **{score:.1f}/100** and confidence of **{confidence:.0f}%**.",
        f"The anomaly signal is **{anomaly:.2f}**. The largest relative change is **{PARAM_LABELS[largest_p]}** at **{changes[largest_p]:+.1f}%** from 0h to the latest checkpoint.",
    ]
    worst_margin, _, label, projected = margin_items[0]
    if worst_margin < 0:
        lines.append(f"At 500h, **{label}** is projected to be **{projected:.3g}**, beyond its configured limit.")
    else:
        lines.append(f"The tightest projected 500h margin is **{label}** at **{worst_margin:.1f}%**.")
    explanation = str(row.get("explanation", "")).strip()
    if explanation:
        lines.append(f"Pipeline explanation: {explanation}")
    return "\n\n".join(lines)


def _list_duts(results, bands):
    subset = results[results["risk_band"].isin(bands)].sort_values("risk_score", ascending=False)
    if subset.empty:
        return "No DUTs match that condition."
    lines = [f"### 📋 DUT List ({len(subset)})"]
    for i, (_, item) in enumerate(subset.iterrows(), 1):
        lines.append(f"{i}. **{item['dut_id']}** — **{item['risk_band']}** — Score **{_num(item, 'risk_score'):.1f}/100** — Confidence **{_num(item, 'risk_confidence_pct'):.0f}%**")
    return "\n".join(lines)


def fleet_summary(results):
    total = len(results)
    counts = results["risk_band"].value_counts()
    low, medium = int(counts.get("LOW", 0)), int(counts.get("MEDIUM", 0))
    high, critical = int(counts.get("HIGH", 0)), int(counts.get("CRITICAL", 0))
    risky = high + critical
    pct = risky / total * 100 if total else 0
    return (f"### 🏭 Fleet Summary\n\n**{total} DUTs** total.\n\n"
            f"- 🟢 LOW: **{low}**\n- 🟡 MEDIUM: **{medium}**\n- 🟠 HIGH: **{high}**\n- 🔴 CRITICAL: **{critical}**\n\n"
            f"**Risky (HIGH + CRITICAL): {risky} ({pct:.1f}%)**")


def _compare_duts(results, ids):
    if len(ids) < 2:
        return "Please provide two DUT IDs, for example: **Compare IC0001 and IC0010**."
    rows = results[results["dut_id"].astype(str).isin(ids)].copy()
    if len(rows) < 2:
        return "I could not find both DUTs in the current results."
    rows = rows.sort_values("risk_score", ascending=False)
    lines = ["### 🔬 DUT Comparison"]
    for _, r in rows.iterrows():
        lines.append(f"- **{r['dut_id']}** — {r['risk_band']} risk, score **{_num(r, 'risk_score'):.1f}**, confidence **{_num(r, 'risk_confidence_pct'):.0f}%**, lot **{r['lot_id']}**")
    winner = rows.iloc[0]
    lines.append(f"\n**Highest risk:** {winner['dut_id']} ({winner['risk_band']}, {_num(winner, 'risk_score'):.1f}/100).")
    return "\n".join(lines)


def _lot_analysis(results):
    g = results.groupby("lot_id").agg(
        DUTs=("dut_id", "count"),
        Avg_Risk=("risk_score", "mean"),
        Critical=("risk_band", lambda s: int((s == "CRITICAL").sum())),
        High=("risk_band", lambda s: int((s == "HIGH").sum())),
    ).reset_index()
    g["Risky"] = g["Critical"] + g["High"]
    g = g.sort_values(["Risky", "Avg_Risk"], ascending=False)
    lines = ["### 🏭 Lot Risk Analysis"]
    for _, r in g.iterrows():
        lines.append(f"- **{r['lot_id']}** — {int(r['DUTs'])} DUTs, **{int(r['Risky'])} risky**, average risk **{r['Avg_Risk']:.1f}**")
    return "\n".join(lines)


def _highest_risk_lot(results):
    grouped = results.groupby("lot_id").agg(
        DUTs=("dut_id", "count"),
        Avg_Risk=("risk_score", "mean"),
        Max_Risk=("risk_score", "max"),
        Risky=("risk_band", lambda s: int(s.isin(["HIGH", "CRITICAL"]).sum())),
    ).reset_index()
    grouped = grouped.sort_values(["Risky", "Max_Risk", "Avg_Risk"], ascending=False)
    lot = grouped.iloc[0]
    return (f"### 🏭 Highest-Risk Lot\n\n**{lot['lot_id']}** has **{int(lot['Risky'])} risky DUTs** out of "
            f"{int(lot['DUTs'])}, with a maximum risk score of **{float(lot['Max_Risk']):.1f}/100** "
            f"and average risk of **{float(lot['Avg_Risk']):.1f}/100**.")


def _short_explanation(row):
    band = str(row.get("risk_band", "UNKNOWN"))
    score = _num(row, "risk_score")
    changes = {p: _pct_change(row, p) for p in PARAM_LABELS}
    p = max(changes, key=lambda x: abs(changes[x]))
    return (f"**{row.get('dut_id', 'Selected DUT')}** is **{band} risk** with a score of **{score:.1f}/100**.\n\n"
            f"The strongest monitored change is **{PARAM_LABELS[p]}** at **{changes[p]:+.1f}%**.")


def _risk_components(row):
    """Return the four normalized signals used by the risk fusion engine."""
    component_labels = {
        "_component_anomaly": "Anomaly signal",
        "_component_lot_deviation": "Lot deviation",
        "_component_drift_rate": "Drift rate",
        "_component_future_margin": "Future-margin proximity",
    }
    lines = [
        f"### Risk Components: {row.get('dut_id', 'Selected DUT')}",
        "",
        f"Overall risk: **{_num(row, 'risk_score'):.1f}/100** (**{row.get('risk_band', 'UNKNOWN')}**)",
        f"Confidence: **{_num(row, 'risk_confidence_pct'):.0f}%**",
        "",
    ]
    for field, label in component_labels.items():
        value = _num(row, field)
        lines.append(f"- **{label}:** **{value:.3f}** ({value * 100:.1f}% of normalized scale)")
    lines.append("\nThe final risk score combines these four normalized signals through the configured risk-fusion weights.")
    return "\n".join(lines)


def _release_recommendation(results):
    risky = results[results["risk_band"].isin(["HIGH", "CRITICAL"])].sort_values("risk_score", ascending=False)
    if risky.empty:
        return ("### ✅ Release Recommendation\n\n**PROVISIONAL RELEASE**: no HIGH or CRITICAL DUTs are present "
                "in the current result set. Continue normal QA sampling and retain the audit record.")
    top = risky.iloc[0]
    lines = [
        "### ⛔ Release Recommendation",
        "",
        f"**HOLD / CONTAIN** the affected population: **{len(risky)} DUTs** are HIGH or CRITICAL risk.",
        f"Highest priority: **{top['dut_id']}** ({top['risk_band']}, score **{_num(top, 'risk_score'):.1f}/100**, lot **{top['lot_id']}**).",
        "",
        "Recommended QA action: quarantine flagged DUTs, review the lot, and repeat targeted telemetry before release.",
    ]
    return "\n".join(lines)


def _containment_recommendation(results):
    risky = results[results["risk_band"].isin(["HIGH", "CRITICAL"])].copy()
    if risky.empty:
        return "### ✅ Containment Check\n\nNo HIGH or CRITICAL DUTs require containment in the current results."
    lots = risky.groupby("lot_id").agg(
        risky_duts=("dut_id", "count"),
        highest_score=("risk_score", "max"),
    ).sort_values(["risky_duts", "highest_score"], ascending=False)
    lines = ["### 🧰 Containment Candidates", "", "Prioritize these lots for review:"]
    for lot_id, item in lots.head(5).iterrows():
        lines.append(f"- **{lot_id}** — {int(item['risky_duts'])} risky DUTs, highest score **{float(item['highest_score']):.1f}/100**")
    return "\n".join(lines)


def _low_confidence_risk(results):
    subset = results[
        results["risk_band"].isin(["HIGH", "CRITICAL"])
        & (results["risk_confidence_pct"] < 50)
    ].sort_values("risk_score", ascending=False)
    if subset.empty:
        return "### 🔎 Confidence Review\n\nNo HIGH or CRITICAL DUTs currently have confidence below 50%."
    lines = ["### 🔎 Low-Confidence High-Risk Review", "", "These DUTs need confirmation testing:"]
    for _, item in subset.iterrows():
        lines.append(f"- **{item['dut_id']}** — {item['risk_band']}, score **{_num(item, 'risk_score'):.1f}**, confidence **{_num(item, 'risk_confidence_pct'):.0f}%**")
    lines.append("\nTreat these as investigation candidates, not automatic failures, until repeat measurements confirm the signal.")
    return "\n".join(lines)


def _worst_parameter(row):
    changes = {p: _pct_change(row, p) for p in PARAM_LABELS}
    margins = {p: _num(row, f"{p}_margin_pct_500h", 100.0) for p in PARAM_LABELS}
    change_param = max(changes, key=lambda p: abs(changes[p]))
    margin_param = min(margins, key=lambda parameter: margins[parameter])
    return (f"### 📈 Parameter Review: {row.get('dut_id', 'Selected DUT')}\n\n"
            f"Largest observed change: **{PARAM_LABELS[change_param]}**, **{changes[change_param]:+.1f}%** from 0h to the latest checkpoint.\n\n"
            f"Tightest 500h projected margin: **{PARAM_LABELS[margin_param]}**, **{margins[margin_param]:.1f}%**.\n\n"
            "Prioritize the parameter with the tightest projected margin for repeat measurement and limit review.")


def answer_question(question, row, results=None, chat_history=None, raw_data=None, model_metrics=None):
    q = (question or "").lower().strip()

    greetings = {"hi", "hello", "hey", "hii", "helo", "good morning", "good afternoon", "good evening"}
    if q in greetings or q in {"hi cosmo", "hello cosmo", "hey cosmo"}:
        return ("Hello! I’m **COSMO**, your BurnInGuard AI assistant.\n\n"
                "I can analyze DUTs, compare components, find risky devices, report drift prediction accuracy, check 500h digital-twin projections, summarize lots, and generate reports.")

    if not q:
        return ("Ask COSMO to **analyze a DUT**, **compare DUTs**, **find risky DUTs**, **review drift accuracy**, "
                "**check 500h projections**, or **summarize the fleet**.")

    missing_id = _requested_id_not_found(question, results)
    if missing_id:
        return f"I cannot find **{missing_id}** in the current prediction results. Check the DUT ID or upload the relevant CSV first."

    # Explicit task commands.
    if results is not None:
        if any(x in q for x in ["rmse", "root mean", "mae", "mean absolute", "r2", "r²", "drift accuracy", "drift model accuracy", "accuracy of drift", "accuracy of the drift", "drift prediction accuracy", "168h drift"]):
            return _drift_metrics_answer(model_metrics, q, row)
        if any(x in q for x in ["does drift", "drift prediction need", "true_latent_defect", "latent defect label"]):
            return _drift_label_answer()
        if any(x in q for x in ["training accuracy", "validation accuracy", "precision", "recall", "f1", "confusion matrix", "unseen lot", "data leakage", "retrain", "manufacturing process", "process changes", "what dataset", "trained on", "confidence threshold", "false negative", "false-negative", "rmse", "root mean", "168h accuracy"]):
            return _model_answer(model_metrics, q)
        if any(x in q for x in ["release", "ship", "disposition", "pass the lot", "can we release"]):
            return _release_recommendation(results)
        if any(x in q for x in ["contain", "quarantine", "hold the lot", "affected lot"]):
            return _containment_recommendation(results)
        if any(x in q for x in ["which duts need confirmation", "show low confidence", "low-confidence high-risk", "confidence review"]):
            return _low_confidence_risk(results)
        if any(x in q for x in ["what happens when model confidence is low", "when confidence is low", "low model confidence"]):
            return _model_answer(model_metrics, q)
        if any(x in q for x in ["fleet summary", "fleet status", "summary of fleet", "summarize the fleet", "summarise the fleet", "whole fleet", "entire fleet"]):
            return fleet_summary(results)
        if any(x in q for x in ["which lot is most", "most risky lot", "highest risk lot", "top risk lot", "worst lot"]):
            return _highest_risk_lot(results)
        if any(x in q for x in ["which lot", "lot has", "lot analysis", "lot risk", "worst lot"]):
            return _lot_analysis(results)
        if any(x in q for x in ["highest risk", "worst dut", "most risky dut", "top risky dut"]):
            r = results.sort_values("risk_score", ascending=False).iloc[0]
            return f"### 🚨 Highest-Risk DUT\n\n**{r['dut_id']}** is **{r['risk_band']}** with a score of **{_num(r, 'risk_score'):.1f}/100** and confidence **{_num(r, 'risk_confidence_pct'):.0f}%**."
        if "compare" in q:
            if any(x in q for x in ["lot", "average behavior", "average behaviour", "lot-relative"]):
                return _lot_comparison(row, results)
            ids = re.findall(r"\b[A-Za-z]+\d+\b", question or "")
            return _compare_duts(results, list(dict.fromkeys(ids))[:2])

        if any(x in q for x in ["normal range", "observed value", "normal behavior", "normal behaviour"]):
            return _normal_range(row, results, raw_data)

        if any(x in q for x in ["highest overall anomaly", "highest anomaly score", "most anomalous component"]):
            return _highest_anomaly(results)

        if any(x in q for x in ["static limit", "datasheet", "pass the static", "static pass", "static fail"]):
            status = _static_status(row, raw_data)
            if "passed" in q and "anomal" in q:
                return status + "\n\nA static pass does not prevent an anomaly classification: COSMO also considers lot-relative deviation, drift behavior, and future-margin projection."
            return status
        if any(x in q for x in ["average behavior", "average behaviour", "against the average", "lot average", "lot-relative"]):
            return _lot_comparison(row, results)
        if any(x in q for x in ["xgboost", "random forest", "pca-spc", "pca spc", "all three methods", "agree"]):
            return _detector_answer(row, model_metrics, q)
        if any(x in q for x in ["drift", "degrading", "degradation", "statistically significant", "linear", "non-linear", "nonlinear"]):
            return _drift_answer(row, q)
        if any(x in q for x in ["0h", "24h", "96h", "telemetry values", "show me the values"]):
            return _telemetry_table(row, raw_data)
        if any(x in q for x in ["safe burn-in", "become unsafe", "cross", "safety limit", "expected value at 168"]):
            if any(x in q for x in ["become unsafe", "cross", "safe burn-in"]):
                return _safety_projection(row)
            parts = []
            for p, label in PARAM_LABELS.items():
                prediction = _num(row, f"{p}_pred_168h")
                projected = _num(row, f"{p}_projected_500h")
                margin = _num(row, f"{p}_margin_pct_500h", 100.0)
                parts.append(f"- **{label}:** predicted 168h **{prediction:.3f}**, projected 500h **{projected:.3f}**, margin **{margin:.1f}%**")
            return "### Projection and Safety Check\n\n" + "\n".join(parts) + "\n\nExact unsafe time is not stored; the 500h projection is the available horizon."

        total = len(results)
        counts = results["risk_band"].value_counts()
        low, medium = int(counts.get("LOW", 0)), int(counts.get("MEDIUM", 0))
        high, critical = int(counts.get("HIGH", 0)), int(counts.get("CRITICAL", 0))
        risky = high + critical
        if any(x in q for x in ["list", "show", "which dut", "which duts", "give me the duts", "names of", "them", "those"]):
            previous_question = ""
            if chat_history:
                for previous in reversed(chat_history):
                    if isinstance(previous, dict):
                        previous_question = str(previous.get("user", "")).lower()
                    elif isinstance(previous, (tuple, list)) and previous:
                        previous_question = str(previous[0]).lower()
                    if previous_question:
                        break
            combined = q + " " + previous_question
            if any(x in q for x in ["risky", "risk", "defect", "failure"]):
                return _list_duts(results, ["HIGH", "CRITICAL"])
            if "critical" in combined: return _list_duts(results, ["CRITICAL"])
            if "high" in combined and "risky" not in combined: return _list_duts(results, ["HIGH"])
            if "medium" in combined: return _list_duts(results, ["MEDIUM"])
            if "low" in combined or "good" in combined or "normal" in combined: return _list_duts(results, ["LOW"])
        if any(x in q for x in ["how many", "number of", "count", "total"]):
            if "critical" in q: return f"There are **{critical} CRITICAL-risk DUTs** out of **{total} total DUTs**."
            if "high" in q: return f"There are **{high} HIGH-risk DUTs** out of **{total} total DUTs**."
            if "medium" in q: return f"There are **{medium} MEDIUM-risk DUTs** out of **{total} total DUTs**."
            if "normal" in q or "good" in q: return f"There are **{low} LOW-risk (normal) DUTs** out of **{total} total DUTs**."
            return f"There are **{risky} HIGH/CRITICAL-risk DUTs** out of **{total} total DUTs** ({risky / total * 100:.1f}%)."

        if any(x in q for x in ["investigate next", "investigate first", "where should i start", "next action", "what should i do"]):
            risky_rows = results[results["risk_band"].isin(["CRITICAL", "HIGH"])].sort_values("risk_score", ascending=False)
            if risky_rows.empty:
                return "No HIGH or CRITICAL DUTs are currently present. The fleet has no immediate investigation candidates."
            top = risky_rows.head(5)
            lines = ["### 🚨 Recommended Investigation Order", "", "Start with these highest-risk DUTs:"]
            for index, (_, item) in enumerate(top.iterrows(), 1):
                lines.append(f"{index}. **{item['dut_id']}** — **{item['risk_band']}**, score **{_num(item, 'risk_score'):.1f}/100**, lot **{item['lot_id']}**")
            return "\n".join(lines)

    # If the user names a DUT, use it for the task where possible.
    named = _dut_id_from_question(question, results)
    if named and results is not None:
        row = results[results["dut_id"].astype(str) == named].iloc[0]

    if any(x in q for x in ["anomaly probability", "probability of anomaly", "anomaly score"]):
        return _anomaly_probability(row)

    if any(x in q for x in ["latent defect", "normal outlier", "potentially latent", "normal or"]):
        return _latent_defect_answer(row)

    if "passed" in q and "anomal" in q:
        return (_static_status(row, raw_data) + "\n\n" +
                "A static pass does not prevent an anomaly classification: COSMO also considers lot-relative deviation, drift behavior, and future-margin projection.")

    if any(x in q for x in ["which electrical parameter", "parameter caused", "cause the anomaly"]):
        return _worst_parameter(row)

    if any(x in q for x in ["normal range", "observed value", "normal behavior", "normal behaviour"]):
        return _normal_range(row, results, raw_data)

    if any(x in q for x in ["analyze", "analyse", "anomalous", "anomaly"]):
        return _dut_analysis(row)

    if any(x in q for x in ["risk component", "risk components", "risk signal", "risk signals", "component contribution"]):
        return _risk_components(row)

    if any(x in q for x in ["worst parameter", "weakest parameter", "weakest", "which parameter should", "parameter to investigate", "parameter review"]):
        return _worst_parameter(row)

    if any(x in q for x in ["tell me about", "what about", "analyze", "analyse", "details", "overview"]):
        return explain_dut(row)

    if q in {"it", "that dut", "this dut", "what about it", "and its risk", "more details"}:
        return explain_dut(row)

    brief = any(term in q for term in ["2 lines", "two lines", "2 line", "three lines", "3 lines", "brief", "short explanation", "in short"])
    if brief and any(word in q for word in ["explain", "why", "reason", "risk"]):
        return _short_explanation(row)

    if any(word in q for word in ["500", "future", "projection", "predict", "forecast"]):
        parts = []
        for p, label in PARAM_LABELS.items():
            value = _num(row, f"{p}_projected_500h")
            margin = _num(row, f"{p}_margin_pct_500h")
            parts.append(f"**{label}**: projected {value:.3g}, remaining margin {margin:.1f}%")
        return "At the **500h digital-twin projection**:\n\n" + "\n\n".join(parts)

    if any(word in q for word in ["parameter", "iddq", "leakage", "delay", "which parameter"]):
        changes = {p: _pct_change(row, p) for p in PARAM_LABELS}
        p = max(changes, key=lambda x: abs(changes[x]))
        return (f"The strongest parameter change is **{PARAM_LABELS[p]}**: {changes[p]:+.1f}% from 0h to the latest checkpoint.\n\n"
                f"IDDQ: {changes['iddq_uA']:+.1f}%\nLeakage: {changes['leakage_uA']:+.1f}%\nDelay: {changes['delay_ns']:+.1f}%")

    if any(word in q for word in ["score", "confidence", "model", "algorithm"]):
        return (f"Risk score: **{_num(row, 'risk_score'):.1f}/100**\n\nRisk band: **{row.get('risk_band', 'UNKNOWN')}**\n\n"
                f"Confidence: **{_num(row, 'risk_confidence_pct'):.0f}%**\n\nAnomaly score: **{_num(row, 'anomaly_ensemble_score'):.2f}**")

    if any(word in q for word in ["why", "reason", "cause", "risk", "flag", "defect"]):
        return explain_dut(row)

    return ("I can perform these tasks: **analyze a DUT**, **compare two DUTs**, **find the highest-risk DUT**, "
            "**list risky DUTs**, **review drift accuracy**, **analyze lots**, **summarize the fleet**, or **check 500h projections**.")
