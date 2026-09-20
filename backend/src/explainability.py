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

PARAMETER_LABELS = {
    "iddq_uA": ("IDDQ", "μA"),
    "leakage_uA": ("leakage", "μA"),
    "delay_ns": ("delay", "ns"),
}


def _strongest_parameter(row, suffix, absolute=True):
    candidates = []
    for parameter in PARAMS:
        value = row.get(f"{parameter}{suffix}")
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if np.isfinite(numeric):
            candidates.append((parameter, numeric))
    if not candidates:
        return None
    return max(candidates, key=lambda item: abs(item[1]) if absolute else item[1])


def build_driver_evidence(row):
    """Build parameter-level evidence without claiming causal attribution."""
    evidence = []
    lot_driver = _strongest_parameter(row, "_last_lot_zscore")
    if lot_driver and abs(lot_driver[1]) > 0.05:
        parameter, zscore = lot_driver
        label, unit = PARAMETER_LABELS[parameter]
        latest = float(row.get(f"{parameter}_last", 0.0))
        direction = "above" if zscore > 0 else "below"
        evidence.append({
            "type": "lot_deviation",
            "parameter": parameter,
            "label": label,
            "text": f"{label} is {abs(zscore):.2f}σ {direction} its lot population (latest {latest:.2f} {unit}).",
            "value": round(zscore, 4),
        })

    drift_driver = _strongest_parameter(row, "_physics_norm_slope")
    if drift_driver and abs(drift_driver[1]) > 0.0001:
        parameter, slope = drift_driver
        label, unit = PARAMETER_LABELS[parameter]
        direction = "increasing" if slope > 0 else "decreasing"
        evidence.append({
            "type": "drift",
            "parameter": parameter,
            "label": label,
            "text": f"{label} shows an {direction} physics-normalized trend ({slope:.4f} {unit}/h).",
            "value": round(slope, 6),
        })

    forecast_candidates = []
    for parameter in PARAMS:
        upper = row.get(f"{parameter}_pred_168h_hi")
        limit = STATIC_LIMITS.get(parameter)
        try:
            ratio = float(upper) / float(limit)
        except (TypeError, ValueError, ZeroDivisionError):
            continue
        if np.isfinite(ratio):
            forecast_candidates.append((parameter, float(upper), float(limit), ratio))
    if forecast_candidates:
        parameter, upper, limit, ratio = max(forecast_candidates, key=lambda item: item[3])
        label, unit = PARAMETER_LABELS[parameter]
        evidence.append({
            "type": "forecast_bound",
            "parameter": parameter,
            "label": label,
            "text": f"The 168h {label} upper forecast is {upper:.2f} {unit}, {ratio * 100:.1f}% of the {limit:.2f} {unit} safety limit.",
            "value": round(ratio, 4),
        })

    if bool(row.get("stage_a_flag", False)):
        robust_z = float(row.get("stage_a_robust_zscore_max", 0.0))
        evidence.append({
            "type": "stage_a",
            "parameter": None,
            "label": "Stage A",
            "text": f"Stage A robust screening flagged this DUT with a maximum MAD z-score of {robust_z:.2f}; the final risk includes a 20-point screening adjustment.",
            "value": round(robust_z, 4),
        })
    return evidence


def explain_row(row, top_n=3):
    """Rank the four risk components for one DUT and turn them into a
    short plain-language explanation string."""
    comps = {k: row[k] for k in COMPONENT_LABELS if k in row}
    ranked = sorted(comps.items(), key=lambda kv: -kv[1])[:top_n]
    reasons = []
    driver_evidence = build_driver_evidence(row)
    if float(row.get("anomaly_ensemble_score", 0.0)) >= 0.3:
        reasons.append(f"multi-parameter detector evidence is elevated (ensemble score {float(row.get('anomaly_ensemble_score', 0.0)):.2f})")
    reasons.extend(item["text"] for item in driver_evidence[:top_n])
    if bool(row.get("stage_a_flag", False)) and not any(item["type"] == "stage_a" for item in driver_evidence[:top_n]):
        reasons.append(driver_evidence[-1]["text"])
    for key, val in ranked:
        if val > 0.05 and not driver_evidence:
            reasons.append(f"{COMPONENT_LABELS[key]} component score {val:.2f}")
    if not reasons:
        return "No significant risk drivers identified; parameters tracking within normal population behaviour."
    cleaned = [reason.rstrip(". ") for reason in reasons]
    return ". ".join(cleaned) + "."


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
