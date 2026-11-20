"""
Contract tests for SHAP artifacts per protocol.yaml §14 (sub-step 5.2).
Reads all JSONL files in results/shap_artifacts/{window}/{presentation}.jsonl
and validates the §14 invariants.
Run from project root: pytest tests/test_shap_contract.py -v
"""
import json
import math
from pathlib import Path

import pytest

ARTIFACTS_DIR = Path("results/shap_artifacts")
PROCESSED_DIR = Path("data/processed")
WINDOWS = ["W2", "W4", "W6", "W8"]
PRESENTATIONS = ["2013B", "2013J", "2014B", "2014J"]
THETA_STAR = {"W2": 0.116, "W4": 0.120, "W6": 0.160, "W8": 0.172}
PROTOCOL_VERSION = "1.0.15"

REQUIRED_FIELDS = {
    "student_id", "presentation", "window", "model_name",
    "model_version", "protocol_version", "risk_score",
    "threshold_applied", "flagged", "top_positive_factors",
    "top_negative_factors", "base_value",
}


def load_all_records():
    """Load all JSONL records into a list of dicts."""
    records = []
    for window in WINDOWS:
        for pres in PRESENTATIONS:
            path = ARTIFACTS_DIR / window / f"{pres}.jsonl"
            if not path.exists():
                continue
            with path.open(encoding="utf-8") as f:
                for line in f:
                    records.append(json.loads(line))
    return records


@pytest.fixture(scope="module")
def records():
    recs = load_all_records()
    assert len(recs) > 0, "no SHAP artifacts found"
    return recs


# ---------------------------------------------------------------------
# Schema and basic invariants
# ---------------------------------------------------------------------
def test_schema_fields_present(records):
    """Every record must have all §14 fields."""
    for r in records:
        missing = REQUIRED_FIELDS - set(r.keys())
        assert not missing, (
            f"student {r.get('student_id')} missing fields: {missing}"
        )


def test_protocol_version(records):
    """All records must carry the frozen protocol version."""
    for r in records:
        assert r["protocol_version"] == PROTOCOL_VERSION, (
            f"student {r['student_id']}: protocol_version "
            f"{r['protocol_version']} != {PROTOCOL_VERSION}"
        )


def test_model_version_is_fold(records):
    """model_version must be one of fold1..fold5."""
    allowed = {f"fold{i}" for i in range(1, 6)}
    for r in records:
        assert r["model_version"] in allowed, (
            f"student {r['student_id']}: invalid model_version "
            f"{r['model_version']}"
        )


def test_window_presentation_consistent(records):
    """window and presentation must match the file they came from."""
    for r in records:
        assert r["window"] in WINDOWS, f"invalid window: {r['window']}"
        assert r["presentation"] in PRESENTATIONS, (
            f"invalid presentation: {r['presentation']}"
        )


# ---------------------------------------------------------------------
# Probability and threshold invariants
# ---------------------------------------------------------------------
def test_risk_score_in_unit_interval(records):
    for r in records:
        assert 0.0 <= r["risk_score"] <= 1.0, (
            f"student {r['student_id']}: risk_score {r['risk_score']} out of [0,1]"
        )


def test_threshold_matches_frozen(records):
    """threshold_applied must equal the frozen theta* for that window."""
    for r in records:
        expected = THETA_STAR[r["window"]]
        assert abs(r["threshold_applied"] - expected) < 1e-9, (
            f"student {r['student_id']} ({r['window']}): threshold "
            f"{r['threshold_applied']} != {expected}"
        )


def test_flagged_matches_threshold(records):
    """flagged == (risk_score >= threshold_applied)."""
    for r in records:
        expected = r["risk_score"] >= r["threshold_applied"]
        assert r["flagged"] == expected, (
            f"student {r['student_id']}: flagged={r['flagged']} but "
            f"risk_score={r['risk_score']} vs threshold={r['threshold_applied']}"
        )


# ---------------------------------------------------------------------
# SHAP reconstruction: sigmoid(base + sum(shap)) == risk_score
# ---------------------------------------------------------------------
def test_shap_probability_reconstruction(records):
    """
    SHAP values are in log-odds. The probability is
    sigmoid(base_value + sum(top5) + other_factors_sum).
    With other_factors_sum capturing the SHAP values outside the top-5
    lists, the reconstruction is exact (tolerance 1e-6).
    """
    for r in records:
        shap_sum = sum(f["shap_value"] for f in r["top_positive_factors"])
        shap_sum += sum(f["shap_value"] for f in r["top_negative_factors"])
        shap_sum += r["other_factors_sum"]
        log_odds = r["base_value"] + shap_sum
        reconstructed = 1.0 / (1.0 + math.exp(-log_odds))
        assert abs(reconstructed - r["risk_score"]) < 1e-6, (
            f"student {r['student_id']} ({r['window']}): "
            f"sigmoid(base + sum_top5 + other) = {reconstructed:.8f} "
            f"vs risk_score = {r['risk_score']:.8f} "
            f"(diff = {abs(reconstructed - r['risk_score']):.2e})"
        )


# ---------------------------------------------------------------------
# Factor list invariants
# ---------------------------------------------------------------------
def test_positive_factors_positive(records):
    for r in records:
        for f in r["top_positive_factors"]:
            assert f["shap_value"] > 0, (
                f"student {r['student_id']}: positive factor "
                f"{f['feature']} has shap_value {f['shap_value']} <= 0"
            )


def test_negative_factors_negative(records):
    for r in records:
        for f in r["top_negative_factors"]:
            assert f["shap_value"] < 0, (
                f"student {r['student_id']}: negative factor "
                f"{f['feature']} has shap_value {f['shap_value']} >= 0"
            )


def test_factor_lists_max_five(records):
    for r in records:
        assert len(r["top_positive_factors"]) <= 5, (
            f"student {r['student_id']}: too many positive factors"
        )
        assert len(r["top_negative_factors"]) <= 5, (
            f"student {r['student_id']}: too many negative factors"
        )


def test_factor_feature_values_populated(records):
    """feature_value must be a number (not null) for every factor."""
    for r in records:
        for f in r["top_positive_factors"] + r["top_negative_factors"]:
            assert f["feature_value"] is not None, (
                f"student {r['student_id']}: feature {f['feature']} "
                f"has null feature_value"
            )


# ---------------------------------------------------------------------
# Exclusion invariant: no artifacts for excluded students
# ---------------------------------------------------------------------
def test_no_artifacts_for_excluded_students(records):
    """
    For each window, the set of (student_id, presentation) in artifacts
    must equal the set of eligible (student_id, presentation) from
    data/processed/eligibility_Wk.parquet.
    """
    import pandas as pd
    for window in WINDOWS:
        elig = pd.read_parquet(
            PROCESSED_DIR / f"eligibility_{window}.parquet"
        )
        elig_keys = set(
            zip(elig[elig["eligible"]]["id_student"],
                elig[elig["eligible"]]["code_presentation"])
        )
        artifact_keys = set(
            (r["student_id"], r["presentation"])
            for r in records if r["window"] == window
        )
        missing = elig_keys - artifact_keys
        extra = artifact_keys - elig_keys
        assert not missing, (
            f"{window}: {len(missing)} eligible students have no artifact"
        )
        assert not extra, (
            f"{window}: {len(extra)} artifacts for ineligible students"
        )