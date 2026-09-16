"""
Explainability layer.

Produces a short, human-readable reason string for each flagged DUT,
built from the risk-fusion component breakdown and global feature
importances.
"""
import numpy as np

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
