"""
Risk Fusion Engine.

Combines:
  - ensemble anomaly probability (+ its cross-detector confidence)
  - lot-relative deviation (z-score)
  - physics-normalised drift rate
  - predicted future value vs. static safety limit (+ prediction interval)

into a single 0-100 Risk Score, a risk band (LOW/MEDIUM/HIGH/CRITICAL),
and an overall confidence percentage.
"""
import numpy as np
import pandas as pd

RISK_WEIGHTS = {
    "anomaly": 0.40,
    "lot_deviation": 0.20,
    "drift_rate": 0.20,
    "future_margin": 0.20,
}

RISK_BANDS = [
    (0, 30, "LOW"),
    (30, 60, "MEDIUM"),
    (60, 80, "HIGH"),
    (80, 101, "CRITICAL"),
]


def _band(score):
    for lo, hi, name in RISK_BANDS:
        if lo <= score < hi:
            return name
    return "CRITICAL"


def _minmax_series(s: pd.Series) -> pd.Series:
    lo, hi = s.quantile(0.01), s.quantile(0.99)
    if hi - lo < 1e-9:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return ((s - lo) / (hi - lo)).clip(0, 1)


def compute_risk(dut_df: pd.DataFrame, static_limits: dict, param_list) -> pd.DataFrame:
    df = dut_df.copy()

    anomaly_component = df["anomaly_ensemble_score"]

    zscore_cols = [c for c in df.columns if c.endswith("_last_lot_zscore")]
    lot_dev_raw = df[zscore_cols].abs().max(axis=1) if zscore_cols else pd.Series(0, index=df.index)
    lot_dev_component = _minmax_series(lot_dev_raw)

    slope_cols = [c for c in df.columns if c.endswith("_physics_norm_slope")]
    drift_raw = df[slope_cols].abs().max(axis=1) if slope_cols else pd.Series(0, index=df.index)
    drift_component = _minmax_series(drift_raw)

    margin_scores = []
    for p in param_list:
        pred_hi_col = f"{p}_pred_168h_hi"
        if pred_hi_col in df.columns and p in static_limits:
            proximity = (df[pred_hi_col] / static_limits[p]).clip(lower=0)
            margin_scores.append(proximity)
    if margin_scores:
        future_margin_raw = pd.concat(margin_scores, axis=1).max(axis=1)
        future_margin_component = _minmax_series(future_margin_raw)
    else:
        future_margin_component = pd.Series(0, index=df.index)

    w = RISK_WEIGHTS
    risk_0_1 = (
        w["anomaly"] * anomaly_component
        + w["lot_deviation"] * lot_dev_component
        + w["drift_rate"] * drift_component
        + w["future_margin"] * future_margin_component
    )
    df["risk_score"] = (risk_0_1 * 100).round(1)
    df["risk_band"] = df["risk_score"].apply(_band)

    width_cols = [c for c in df.columns if c.endswith("_pred_interval_width")]
    if width_cols:
        avg_width = df[width_cols].mean(axis=1)
        interval_confidence = 1.0 - _minmax_series(avg_width)
    else:
        interval_confidence = pd.Series(0.5, index=df.index)

    df["risk_confidence_pct"] = (
        (0.6 * df["anomaly_ensemble_confidence"] + 0.4 * interval_confidence) * 100
    ).round(1)

    df["_component_anomaly"] = anomaly_component.round(3)
    df["_component_lot_deviation"] = lot_dev_component.round(3)
    df["_component_drift_rate"] = drift_component.round(3)
    df["_component_future_margin"] = future_margin_component.round(3)

    return df
