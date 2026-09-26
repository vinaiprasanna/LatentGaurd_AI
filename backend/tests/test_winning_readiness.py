import sys
from types import SimpleNamespace
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import main
from main import filter_output_columns, resolve_allowed_origins


@pytest.fixture(autouse=True)
def disable_database_for_tests(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)


def test_resolve_allowed_origins_reads_env(monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://app.example.com, https://admin.example.com")
    assert resolve_allowed_origins() == [
        "https://app.example.com",
        "https://admin.example.com",
    ]


def test_filter_output_columns_removes_non_contract_columns():
    df = pd.DataFrame(
        {
            "dut_id": ["DUT-001"],
            "lot_id": ["LOT-1"],
            "risk_score": [62.4],
            "risk_band": ["HIGH"],
            "predicted_outcome": ["FAIL"],
            "debug_only_field": ["should be removed"],
            "anomaly_ensemble_score": [0.81],
            "iddq_uA_projected_500h": [45.1],
        }
    )

    filtered = filter_output_columns(df)

    assert list(filtered.columns) == [
        "dut_id",
        "lot_id",
        "risk_score",
        "risk_band",
        "predicted_outcome",
        "anomaly_ensemble_score",
        "iddq_uA_projected_500h",
    ]
    assert "debug_only_field" not in filtered.columns


def test_compute_stage_a_mad_flags_marks_outlier():
    from features import compute_stage_a_mad_flags

    lot_df = pd.DataFrame(
        {
            "dut_id": ["DUT-001", "DUT-002", "DUT-003", "DUT-004"],
            "lot_id": ["LOT-1", "LOT-1", "LOT-1", "LOT-1"],
            "iddq_uA": [10.0, 9.8, 10.2, 45.0],
            "leakage_uA": [1.0, 1.1, 0.9, 10.0],
            "delay_ns": [5.0, 5.1, 4.9, 20.0],
        }
    )

    flagged = compute_stage_a_mad_flags(lot_df)

    assert "stage_a_robust_zscore_max" in flagged.columns
    assert "stage_a_flag" in flagged.columns
    assert bool(flagged.loc[flagged["dut_id"] == "DUT-004", "stage_a_flag"].iloc[0]) is True


def test_stage_a_metadata_is_not_sent_to_trained_model():
    from features import get_model_feature_columns

    dut_df = pd.DataFrame(
        {
            "dut_id": ["DUT-001"],
            "lot_id": ["LOT-1"],
            "iddq_uA_last": [10.0],
            "stage_a_robust_zscore_max": [4.2],
            "stage_a_flag": [True],
        }
    )

    assert get_model_feature_columns(dut_df) == ["iddq_uA_last"]


def test_risk_component_scales_are_independent_of_batch_composition():
    from risk_engine import compute_risk

    base = pd.DataFrame(
        {
            "dut_id": ["DUT-001"],
            "anomaly_ensemble_score": [0.5],
            "anomaly_ensemble_confidence": [0.8],
            "iddq_uA_last_lot_zscore": [1.75],
            "iddq_uA_physics_norm_slope": [0.025],
            "iddq_uA_pred_168h_hi": [10.0],
            "iddq_uA_pred_interval_width": [1.0],
        }
    )
    extra = base.assign(dut_id="DUT-002", iddq_uA_last_lot_zscore=20.0)

    single = compute_risk(base, {"iddq_uA": 20.0}, ["iddq_uA"])
    combined = compute_risk(pd.concat([base, extra], ignore_index=True), {"iddq_uA": 20.0}, ["iddq_uA"])

    assert combined.loc[0, "risk_score"] == single.loc[0, "risk_score"]


def test_prediction_job_persists_provenance(monkeypatch, tmp_path):
    raw = pd.DataFrame({"dut_id": ["DUT-001"], "lot_id": ["LOT-1"]})
    cleaned = raw.copy()
    results = pd.DataFrame(
        {
            "dut_id": ["DUT-001"],
            "lot_id": ["LOT-1"],
            "risk_band": ["HIGH"],
            "stage_a_flag": [True],
        }
    )
    report = SimpleNamespace(as_dict=lambda: {"valid": True})
    store_path = tmp_path / "audit_jobs.json"
    monkeypatch.setattr(main, "AUDIT_STORE_PATH", str(store_path))
    monkeypatch.setattr(main, "JOB_RESULTS_DIR", str(tmp_path / "jobs"))

    job_id = main._record_prediction_job("input.csv", raw, cleaned, results, report)
    record = main._load_audit_jobs()[0]

    assert record["job_id"] == job_id
    assert record["feature_schema_version"] == "32"
    assert record["input_sha256"]
    assert record["stage_a_flagged"] == 1
    assert (tmp_path / "jobs" / f"{job_id}.csv").exists()

    snapshot = main.get_audit_job_results(job_id)
    assert snapshot["job_id"] == job_id
    assert snapshot["results"][0]["dut_id"] == "DUT-001"


def test_database_snapshot_restores_dashboard_results(monkeypatch):
    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, query):
            assert "SELECT results FROM audit_jobs" in query
            return self

        def fetchone(self):
            return ([{
                "dut_id": "DUT-001",
                "lot_id": "LOT-1",
                "risk_score": 25.0,
                "risk_band": "LOW",
                "predicted_outcome": "PASS",
                "internal_feature": 123,
            }],)

    monkeypatch.setattr(main, "_active_results", None)
    monkeypatch.setattr(main, "_database_enabled", lambda: True)
    monkeypatch.setattr(main, "_connect_database", FakeConnection)

    restored = main._get_active_uploaded_results()

    assert restored.iloc[0]["dut_id"] == "DUT-001"
    assert "internal_feature" not in restored.columns


def test_review_action_persists_with_job_link(monkeypatch, tmp_path):
    store_path = tmp_path / "review_actions.json"
    monkeypatch.setattr(main, "REVIEW_STORE_PATH", str(store_path))
    monkeypatch.setattr(main, "_active_job_id", "job_test123")

    record = main._record_review_action("DUT-001", "LOT-1", "ACKNOWLEDGED")

    assert record["status"] == "Acknowledged"
    assert record["job_id"] == "job_test123"
    assert main._load_review_actions()[0]["action"] == "ACKNOWLEDGED"


def test_prediction_job_retention_caps_metadata_and_snapshots(monkeypatch, tmp_path):
    raw = pd.DataFrame({"dut_id": ["DUT-001"], "lot_id": ["LOT-1"]})
    results = pd.DataFrame({"dut_id": ["DUT-001"], "lot_id": ["LOT-1"], "risk_band": ["LOW"]})
    report = SimpleNamespace(as_dict=lambda: {"valid": True})
    monkeypatch.setattr(main, "AUDIT_STORE_PATH", str(tmp_path / "audit_jobs.json"))
    monkeypatch.setattr(main, "JOB_RESULTS_DIR", str(tmp_path / "jobs"))

    for _ in range(101):
        main._record_prediction_job("input.csv", raw, raw, results, report)

    assert len(main._load_audit_jobs()) == 100
    assert len(list((tmp_path / "jobs").glob("*.csv"))) == 100


def test_explanation_names_parameter_level_evidence():
    from explainability import build_driver_evidence, explain_row

    row = {
        "anomaly_ensemble_score": 0.62,
        "iddq_uA_last": 42.0,
        "iddq_uA_last_lot_zscore": 2.4,
        "iddq_uA_physics_norm_slope": 0.031,
        "iddq_uA_pred_168h_hi": 48.0,
        "stage_a_flag": True,
        "stage_a_robust_zscore_max": 4.1,
    }

    evidence = build_driver_evidence(row)
    explanation = explain_row(row)

    assert any(item["type"] == "lot_deviation" and item["parameter"] == "iddq_uA" for item in evidence)
    assert any(item["type"] == "forecast_bound" and item["parameter"] == "iddq_uA" for item in evidence)
    assert "upper forecast" in explanation
    assert "Stage A" in explanation
    assert "contribution" not in explanation
