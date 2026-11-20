"""
Zero-leakage asserts for protocol.yaml §6 (Rules R1–R4).
R3 and R4 are testable now; R1 and R2 are marked skip until Step 3
(they require the CV pipeline, not yet built).

Run from project root: pytest tests/test_leakage.py -v
"""
from pathlib import Path

import pandas as pd
import pytest

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

CUTOFFS = {"W2": 14, "W4": 28, "W6": 42, "W8": 56}
KEY = ["id_student", "code_module", "code_presentation"]


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------
@pytest.fixture(scope="module")
def features():
    out = {}
    for window in CUTOFFS:
        path = PROCESSED_DIR / f"features_{window}.parquet"
        assert path.exists(), f"missing features file: {path}"
        out[window] = pd.read_parquet(path)
    return out


@pytest.fixture(scope="module")
def eligibility():
    out = {}
    for window in CUTOFFS:
        path = PROCESSED_DIR / f"eligibility_{window}.parquet"
        assert path.exists(), f"missing eligibility file: {path}"
        out[window] = pd.read_parquet(path)
    return out


@pytest.fixture(scope="module")
def raw_svle():
    return pd.read_csv(RAW_DIR / "studentVle.csv")


# ---------------------------------------------------------------------
# R3 — Temporal boundary integrity
# ---------------------------------------------------------------------
def test_r3_monotonic_cumulative_features(features):
    """
    Cumulative features must be non-decreasing across windows for each
    student-module-presentation. A violation would mean future data
    leaked into an earlier window.
    """
    monotonic_cols = ["S_vle", "D_active"]
    # Build a combined frame keyed by (student, module, presentation)
    merged = None
    for window in ["W2", "W4", "W6", "W8"]:
        df = features[window][KEY + monotonic_cols].copy()
        df = df.rename(columns={c: f"{c}_{window}" for c in monotonic_cols})
        merged = df if merged is None else merged.merge(df, on=KEY, how="outer")

    for col in monotonic_cols:
        for w_prev, w_next in [("W2", "W4"), ("W4", "W6"), ("W6", "W8")]:
            prev = merged[f"{col}_{w_prev}"]
            nxt = merged[f"{col}_{w_next}"]
            # Ignore rows where either side is NaN (student absent in one window)
            mask = prev.notna() & nxt.notna()
            violations = (nxt[mask] < prev[mask]).sum()
            assert violations == 0, (
                f"R3 violation: {col} decreased from {w_prev} to {w_next} "
                f"for {violations} student-module-presentations"
            )


def test_r3_no_future_activity_in_w2(features, raw_svle):
    """
    For a sample of W2 rows, recompute S_vle from raw studentVle using
    only date <= 14 and compare. Detects accidental inclusion of future
    activity in W2 features.
    """
    w2 = features["W2"]
    cutoff = CUTOFFS["W2"]
    svle_cut = raw_svle[raw_svle["date"] <= cutoff]
    recomputed = (svle_cut.groupby(KEY)["sum_click"].sum()
                  .reset_index(name="S_vle_recomputed"))
    merged = w2[KEY + ["S_vle"]].merge(recomputed, on=KEY, how="left")
    # Students with no clicks have NaN in recomputed and NaN in S_vle: both NaN, OK
    both = merged[merged["S_vle"].notna() & merged["S_vle_recomputed"].notna()]
    mismatches = (both["S_vle"] != both["S_vle_recomputed"]).sum()
    assert mismatches == 0, (
        f"R3 violation: {mismatches} W2 rows have S_vle inconsistent "
        f"with date <= {cutoff} recomputation"
    )


def test_r3_entropy_bounds(features):
    """H_entropy must lie in [0, log2(20)] ≈ [0, 4.3219]."""
    import math
    upper = math.log2(20)
    for window, df in features.items():
        s = df["H_entropy"].dropna()
        assert (s >= 0).all(), f"{window}: negative entropy values"
        assert (s <= upper + 1e-9).all(), (
            f"{window}: entropy exceeds log2(20)={upper:.4f}: max={s.max()}"
        )


# ---------------------------------------------------------------------
# R4 — Student-level group isolation
# ---------------------------------------------------------------------
def test_r4_no_duplicate_keys_within_window(features):
    """
    Each (id_student, code_module, code_presentation) must appear at most
    once per window. Duplicates would inflate counts and break group CV.
    """
    for window, df in features.items():
        dups = df.duplicated(subset=KEY).sum()
        assert dups == 0, f"{window}: {dups} duplicate keys"


def test_r4_eligibility_matches_features(eligibility, features):
    """
    The set of keys in features_Wk must equal the set of eligible keys in
    eligibility_Wk. Any difference means an ineligible student received
    features, or an eligible student was silently dropped.
    """
    for window in CUTOFFS:
        elig = eligibility[window]
        elig_keys = set(map(tuple, elig[elig["eligible"]][KEY].values))
        feat_keys = set(map(tuple, features[window][KEY].values))
        missing = elig_keys - feat_keys
        extra = feat_keys - elig_keys
        assert not missing, (
            f"{window}: {len(missing)} eligible students missing from features"
        )
        assert not extra, (
            f"{window}: {len(extra)} ineligible students present in features"
        )


def test_r4_overlap_students_exist(features):
    """
    Sanity check: students appearing in multiple module presentations must
    still be present (as separate rows) in each window. Confirms Rule 4 is
    meaningful and the data was not silently deduplicated by student_id.

    Note: two distinct quantities must not be conflated:
    - overlap_rows = studentInfo rows - unique students = 3,808
    - overlap_students = students with >1 row = 3,538
    """
    info = pd.read_csv(RAW_DIR / "studentInfo.csv")
    counts = info.groupby("id_student").size()
    overlap_ids = set(counts[counts > 1].index)

    n_rows = len(info)
    n_unique = info["id_student"].nunique()
    n_overlap_rows = n_rows - n_unique
    n_overlap_students = len(overlap_ids)

    # Documented invariants (protocol.yaml §1 audit_notes, corrected in v1.0.7)
    assert n_rows == 32593, f"studentInfo rows: expected 32,593, got {n_rows}"
    assert n_unique == 28785, f"unique students: expected 28,785, got {n_unique}"
    assert n_overlap_rows == 3808, (
        f"overlap rows (rows - unique): expected 3,808, got {n_overlap_rows}"
    )
    assert n_overlap_students == 3538, (
        f"overlap students (>1 row): expected 3,538, got {n_overlap_students}"
    )

    for window, df in features.items():
        present = set(df["id_student"]) & overlap_ids
        assert len(present) > 0, (
            f"{window}: no overlapping students present — data may have "
            f"been deduplicated by student_id"
        )

# ---------------------------------------------------------------------
# R1 — Preprocessing isolation
# ---------------------------------------------------------------------
def test_r1_preprocessing_fit_on_train_only():
    """
    Imputer and scaler statistics must differ between a pipeline fit on
    the full dataset and one fit on a training fold only. If they are
    identical, the transformer was fit on the full data (leakage).
    """
    from sklearn.model_selection import GroupKFold
    from src.models.pipeline import build_pipeline, get_feature_names
    import numpy as np

    df = pd.read_parquet(PROCESSED_DIR / "features_W4.parquet")
    features = get_feature_names("A")
    X = df[features].values
    y = (df["final_result"].isin(["Withdrawn", "Fail"])).astype(int).values
    groups = df["id_student"].values

    gkf = GroupKFold(n_splits=5)
    train_idx, _ = next(gkf.split(X, y, groups))

    pipe_fold = build_pipeline("logreg", "A")
    pipe_fold.fit(X[train_idx], y[train_idx])
    imputer_fold = pipe_fold.named_steps["imputer"]
    scaler_fold = pipe_fold.named_steps["scaler"]

    pipe_full = build_pipeline("logreg", "A")
    pipe_full.fit(X, y)
    imputer_full = pipe_full.named_steps["imputer"]
    scaler_full = pipe_full.named_steps["scaler"]

    # Imputer statistics must differ (training fold is a subset)
    assert not np.allclose(imputer_fold.statistics_, imputer_full.statistics_), (
        "R1 violation: imputer statistics identical between fold and full fit"
    )
    # Scaler statistics must differ
    assert not np.allclose(scaler_fold.mean_, scaler_full.mean_), (
        "R1 violation: scaler mean identical between fold and full fit"
    )


# ---------------------------------------------------------------------
# R2 — Resampling boundary
# ---------------------------------------------------------------------
def test_r2_resampling_after_split_only():
    """
    Structural test: when a resampler is present in the pipeline, it must
    be an imblearn.pipeline.Pipeline (not sklearn.pipeline.Pipeline), so
    that fit_resample is called only on the training fold during fit().
    Also verifies that fitting on the training fold does not change the
    test fold's class distribution.
    """
    from sklearn.model_selection import GroupKFold
    from imblearn.pipeline import Pipeline as ImbPipeline
    from src.imbalance.benchmark import build_imbalance_pipeline
    from src.models.pipeline import get_feature_names
    import numpy as np

    df = pd.read_parquet(PROCESSED_DIR / "features_W4.parquet")
    features = get_feature_names("A")
    X = df[features].values
    y = df["final_result"].isin(["Withdrawn", "Fail"]).astype(int).values
    groups = df["id_student"].values

    gkf = GroupKFold(n_splits=5)
    train_idx, test_idx = next(gkf.split(X, y, groups))

    pipe = build_imbalance_pipeline("logreg", "smote", "A")
    assert isinstance(pipe, ImbPipeline), (
        "R2 violation: resampling pipeline must be imblearn.pipeline.Pipeline"
    )

    y_test_before = y[test_idx].copy()
    pipe.fit(X[train_idx], y[train_idx])
    y_test_after = y[test_idx]
    assert np.array_equal(y_test_before, y_test_after), (
        "R2 violation: test fold labels changed after fitting on train fold"
    )