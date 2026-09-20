"""
Explainability layer.

Produces a short, human-readable reason string for each flagged DUT,
built from the risk-fusion component breakdown and global feature
importances.
"""
import numpy as np

from data_generator import STATIC_LIMITS
from digital_twin import project_trajectory, remaining_margin
from features import PARAMS, _arrhenius_factor

try:
    import shap
    _HAS_SHAP = True
except ImportError:
    _HAS_SHAP = False


COMPONENT_LABELS = {
    "_component_anomaly": "abnormal multi-parameter pattern (ensemble anomaly score)",
    "_component_lot_deviation": "significant deviation from lot population",
    "_component_drift_rate": "high physics-normalised drift rate",
    "_component_future_margin": "predicted value approaching the safety limit",
}


def explain_row(row, top_n=3):
    """Rank the four risk components for one DUT and turn them into a
    short plain-language explanation string."""
    comps = {k: row[k] for k in COMPONENT_LABELS if k in row}
    ranked = sorted(comps.items(), key=lambda kv: -kv[1])[:top_n]
    reasons = []
    for key, val in ranked:
        if val <= 0.05:
            continue
        reasons.append(f"{COMPONENT_LABELS[key]} (contribution {val:.2f})")
    if not reasons:
        return "No significant risk drivers identified; parameters tracking within normal population behaviour."
    return "; ".join(reasons) + "."


def build_evidence_chain(row):
    """Return the concrete signals supporting the current DUT decision."""
    evidence = [
        f"Anomaly ensemble {float(row.get('anomaly_ensemble_score', 0.0)):.2f} ({row.get('anomaly_decision', 'NORMAL')})",
        f"Risk {float(row.get('risk_score', 0.0)):.1f}/100 ({row.get('risk_band', 'LOW')})",
        f"Confidence {float(row.get('risk_confidence_pct', 0.0)):.1f}%",
    ]
    if bool(row.get("stage_a_flag", False)):
        evidence.append(f"Stage A MAD flag {float(row.get('stage_a_robust_zscore_max', 0.0)):.2f}")
    if float(row.get("_component_future_margin", 0.0)) >= 0.5:
        evidence.append("168-hour upper forecast is close to a safety limit")
    if float(row.get("_component_lot_deviation", 0.0)) >= 0.5:
        evidence.append("DUT is separated from its lot population")
    return " | ".join(evidence)


def recommended_confirmation_test(row):
    """Select a concrete follow-up test from the observed evidence."""
    if bool(row.get("stage_a_flag", False)):
        return "Repeat lot-relative electrical screen; confirm the Stage A MAD outlier."
    if float(row.get("_component_future_margin", 0.0)) >= 0.6:
        return "Run an extended thermal burn-in and remeasure the limiting parameter."
    if float(row.get("_component_drift_rate", 0.0)) >= 0.6:
        return "Repeat the early checkpoints under controlled temperature to confirm drift."
    if float(row.get("anomaly_ensemble_confidence", 1.0)) < 0.5:
        return "Repeat the multi-parameter measurement; detector agreement is low."
    return "Perform a confirmation measurement at the current burn-in temperature."


def thermal_counterfactual(row, temperature_delta=10.0):
    """Project 500-hour safety margins under a temperature-only change."""
    current_temp = float(row.get("temperature_c", 125.0))
    new_temp = current_temp + temperature_delta
    new_accel = _arrhenius_factor(new_temp)
    summaries = []
    for parameter in PARAMS:
        slope = float(row.get(f"{parameter}_slope", 0.0))
        v0 = float(row.get(f"{parameter}_0h", 0.0))
        projection = project_trajectory(
            v0=v0,
            physics_norm_slope=slope / max(new_accel, 1e-6),
            accel_factor=new_accel,
        )
        margin = remaining_margin(projection, STATIC_LIMITS[parameter], 500)
        if margin is not None:
            summaries.append(f"{parameter} margin {margin['margin_pct']:.1f}%")
    return f"At {new_temp:.1f}C (+{temperature_delta:.0f}C), 500-hour physics projection: " + ", ".join(summaries) + "."


def shap_summary(model, X, feature_names, max_display=8):
    """Return a small dict of {feature: mean_abs_shap} for the given
    tree-based model, or a fallback based on built-in feature
    importances if shap is unavailable."""
    if _HAS_SHAP:
        try:
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X)
            mean_abs = np.abs(shap_values).mean(axis=0)
            ranked = sorted(zip(feature_names, mean_abs), key=lambda kv: -kv[1])
            return dict(ranked[:max_display])
        except Exception:
            pass

    try:
        importances = model.feature_importances_
        ranked = sorted(zip(feature_names, importances), key=lambda kv: -kv[1])
        return dict(ranked[:max_display])
    except AttributeError:
        return {}
