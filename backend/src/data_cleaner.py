"""Input telemetry cleaning and physics sanity checks for BurnInGuard.

The cleaner never silently removes a DUT because of a physical anomaly. It
repairs safe formatting issues, rejects unusable rows, and marks abnormal DUTs
so the application can send them to investigation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = {
    "dut_id", "lot_id", "checkpoint_h", "temperature_c", "vcc_v",
    "iddq_uA", "leakage_uA", "delay_ns",
}
NUMERIC_COLUMNS = [
    "checkpoint_h", "temperature_c", "vcc_v", "iddq_uA", "leakage_uA", "delay_ns",
]
TELEMETRY_COLUMNS = ["iddq_uA", "leakage_uA", "delay_ns"]
STATIC_LIMITS = {"iddq_uA": 50.0, "leakage_uA": 10.0, "delay_ns": 8.0}
PHYSICS_RANGES = {
    "temperature_c": (-55.0, 200.0),
    "vcc_v": (0.0, 7.0),
    "iddq_uA": (0.0, 1_000.0),
    "leakage_uA": (0.0, 1_000.0),
    "delay_ns": (0.0, 1_000.0),
}
EXPECTED_CHECKPOINTS = {0, 24, 96, 168}


@dataclass
class CleaningReport:
    total_rows: int
    cleaned_rows: int
    dropped_rows: int
    abnormal_duts: List[str]
    row_errors: Dict[str, int]
    dut_flags: Dict[str, List[str]]

    def as_dict(self):
        return {
            "total_rows": self.total_rows,
            "cleaned_rows": self.cleaned_rows,
            "dropped_rows": self.dropped_rows,
            "abnormal_duts": self.abnormal_duts,
            "abnormal_dut_count": len(self.abnormal_duts),
            "row_errors": self.row_errors,
            "dut_flags": self.dut_flags,
        }


def clean_and_validate(raw_df: pd.DataFrame):
    """Clean safe formatting issues and flag physics abnormalities.

    Returns ``(cleaned_dataframe, report)``. Abnormal telemetry is retained so
    the model can score it and the investigation queue can show it.
    """
    missing = sorted(REQUIRED_COLUMNS - set(raw_df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    df = raw_df.copy()
    total_rows = len(df)
    df["dut_id"] = df["dut_id"].astype("string").str.strip()
    df["lot_id"] = df["lot_id"].astype("string").str.strip()
    row_errors = {"missing_identity": 0, "invalid_numeric": 0, "duplicate_checkpoint": 0}

    identity_invalid = df["dut_id"].isna() | df["dut_id"].eq("") | df["lot_id"].isna() | df["lot_id"].eq("")
    row_errors["missing_identity"] = int(identity_invalid.sum())
    df = df.loc[~identity_invalid].copy()

    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    numeric_invalid = df[NUMERIC_COLUMNS].isna().any(axis=1) | ~np.isfinite(df[NUMERIC_COLUMNS]).all(axis=1)
    row_errors["invalid_numeric"] = int(numeric_invalid.sum())
    df = df.loc[~numeric_invalid].copy()

    duplicate_mask = df.duplicated(["dut_id", "checkpoint_h"], keep="first")
    row_errors["duplicate_checkpoint"] = int(duplicate_mask.sum())
    df = df.loc[~duplicate_mask].copy()

    flags: Dict[str, set] = {}
    def add_flag(mask, reason):
        for dut_id in df.loc[mask, "dut_id"].astype(str).unique():
            flags.setdefault(dut_id, set()).add(reason)

    checkpoint_mask = ~df["checkpoint_h"].astype(int).isin(EXPECTED_CHECKPOINTS)
    add_flag(checkpoint_mask, "unexpected checkpoint")
    for column, (lower, upper) in PHYSICS_RANGES.items():
        values = df[column]
        add_flag((values < lower) | (values > upper), f"{column} outside physics range [{lower:g}, {upper:g}]")
    for column, limit in STATIC_LIMITS.items():
        add_flag(df[column] > limit, f"{column} exceeds static limit {limit:g}")

    report = CleaningReport(
        total_rows=total_rows,
        cleaned_rows=len(df),
        dropped_rows=total_rows - len(df),
        abnormal_duts=sorted(flags),
        row_errors=row_errors,
        dut_flags={dut_id: sorted(reasons) for dut_id, reasons in flags.items()},
    )
    df["data_quality_abnormal"] = df["dut_id"].astype(str).isin(report.abnormal_duts)
    df["data_quality_flags"] = df["dut_id"].astype(str).map(
        lambda dut_id: "; ".join(report.dut_flags.get(dut_id, []))
    )
    return df, report
