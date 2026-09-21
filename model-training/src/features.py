"""
Feature engineering: statistical (lot-relative) + physics-informed
(Arrhenius-normalised drift) features, one row per DUT.
"""
import numpy as np
import pandas as pd

PARAMS = ["iddq_uA", "leakage_uA", "delay_ns"]
EA_EV = 0.7
K_BOLTZMANN = 8.617e-5
T_REF_C = 125.0
ALLOWED_DRIFT_INPUT_CHECKPOINTS = {0, 24}


def get_drift_input_rows(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Return only the early checkpoint rows that may seed the drift forecast.

    The drift model is trained and evaluated against 0h/24h signal inputs only,
    while later checkpoints are treated as target horizons or digital twin outputs.
    """
    if raw_df is None or raw_df.empty:
        return raw_df
    if "checkpoint_h" not in raw_df.columns:
        return raw_df

    cp = pd.to_numeric(raw_df["checkpoint_h"], errors="coerce")
    allowed = raw_df[cp.isin(ALLOWED_DRIFT_INPUT_CHECKPOINTS)].copy()
    if not allowed.empty:
        return allowed
    return raw_df.copy()


def _arrhenius_factor(temp_c):
    t_k = temp_c + 273.15
    t_ref_k = T_REF_C + 273.15
    return np.exp((EA_EV / K_BOLTZMANN) * (1.0 / t_ref_k - 1.0 / t_k))


def build_dut_features(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Collapse per-checkpoint telemetry into one physics + statistics
    feature row per DUT, then add lot-relative (population) features.
    """
    records = []
    for dut_id, g in raw_df.groupby("dut_id"):
        g = g.sort_values("checkpoint_h")
        lot_id = g["lot_id"].iloc[0]
        temp_c = g["temperature_c"].mean()
        accel = _arrhenius_factor(temp_c)
        rec = {"dut_id": dut_id, "lot_id": lot_id, "temperature_c": temp_c,
               "arrhenius_accel_factor": accel}
        if "true_latent_defect" in g.columns:
            rec["true_latent_defect"] = int(g["true_latent_defect"].iloc[0])

        t = g["checkpoint_h"].values.astype(float)
        for p in PARAMS:
            v = g[p].values.astype(float)
            v0, v_last = v[0], v[-1]
            abs_change = v_last - v0
            pct_change = abs_change / max(v0, 1e-6) * 100.0
            slope = np.polyfit(t, v, 1)[0] if len(t) > 1 else 0.0
            if len(t) >= 3:
                coeffs2 = np.polyfit(t, v, 2)
                curvature = coeffs2[0]
            else:
                curvature = 0.0
            physics_norm_slope = slope / max(accel, 1e-6)

            rec[f"{p}_0h"] = v0
            rec[f"{p}_last"] = v_last
            rec[f"{p}_abs_change"] = abs_change
            rec[f"{p}_pct_change"] = pct_change
            rec[f"{p}_slope"] = slope
            rec[f"{p}_curvature"] = curvature
            rec[f"{p}_physics_norm_slope"] = physics_norm_slope

        records.append(rec)

    dut_df = pd.DataFrame(records)

    for p in PARAMS:
        for col in [f"{p}_last", f"{p}_slope", f"{p}_physics_norm_slope"]:
            lot_mean = dut_df.groupby("lot_id")[col].transform("mean")
            lot_std = dut_df.groupby("lot_id")[col].transform("std").replace(0, np.nan)
            dut_df[f"{col}_lot_zscore"] = ((dut_df[col] - lot_mean) / lot_std).fillna(0.0)

    return dut_df


FEATURE_COLUMNS = None


def get_model_feature_columns(dut_df: pd.DataFrame):
    """Numeric columns used as the ML feature vector (excludes IDs / labels)."""
    exclude = {"dut_id", "lot_id", "true_latent_defect", "calibration_source"}
    cols = [c for c in dut_df.columns if c not in exclude and dut_df[c].dtype != object]
    return cols
