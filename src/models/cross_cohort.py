"""
Cross-cohort generalization per protocol.yaml §7 (Step 6, sub-step 6.1).
Train on 2013B+2013J, test on 2014B+2014J.
Students appearing in both 2013 and 2014 are REMOVED from the test set
to guarantee strictly out-of-cohort evaluation.
No retraining, no threshold recalibration.
Run from project root: python -m src.models.cross_cohort
"""
from pathlib import Path

import numpy as np
import pandas as pd
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.impute import SimpleImputer
from lightgbm import LGBMClassifier
from sklearn.metrics import (
    average_precision_score, roc_auc_score, recall_score,
    precision_score, fbeta_score,
)

from src.models.pipeline import get_feature_names

PROCESSED_DIR = Path("data/processed")
RESULTS_DIR = Path("results/tables")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

WINDOWS = ["W2", "W4", "W6", "W8"]
THETA_STAR = {"W2": 0.116, "W4": 0.120, "W6": 0.160, "W8": 0.172}
TRAIN_PRES = {"2013B", "2013J"}
TEST_PRES = {"2014B", "2014J"}
SEED = 42


def build_pipeline() -> ImbPipeline:
    return ImbPipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("model", LGBMClassifier(
            n_estimators=100, random_state=SEED, n_jobs=-1, verbose=-1,
            class_weight="balanced",
        )),
    ])


def expected_cost(y_true, y_pred, c_fn=5, c_fp=1):
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    return fn * c_fn + fp * c_fp


def metrics_at(y_true, proba, theta):
    y_pred = (proba >= theta).astype(int)
    return {
        "n_test": int(len(y_true)),
        "pos_rate_test": float(y_true.mean()),
        "pr_auc": float(average_precision_score(y_true, proba)),
        "roc_auc": float(roc_auc_score(y_true, proba)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "f2": float(fbeta_score(y_true, y_pred, beta=2, zero_division=0)),
        "flagged_rate": float(y_pred.mean()),
        "expected_cost": expected_cost(y_true, y_pred),
        "threshold_applied": float(theta),
    }


def run_window(window: str) -> tuple[dict, dict]:
    df = pd.read_parquet(PROCESSED_DIR / f"features_{window}.parquet")
    features = get_feature_names("A")

    train_mask = df["code_presentation"].isin(TRAIN_PRES)
    test_mask = df["code_presentation"].isin(TEST_PRES)

    # Overlap check: students in both 2013 and 2014
    train_ids = set(df[train_mask]["id_student"])
    test_ids_all = set(df[test_mask]["id_student"])
    overlap_ids = train_ids & test_ids_all
    # Remove overlapping students from the test set
    test_mask_clean = test_mask & ~df["id_student"].isin(overlap_ids)

    train_df = df[train_mask]
    test_df = df[test_mask_clean]

    X_tr = train_df[features].values
    y_tr = train_df["final_result"].isin(["Withdrawn", "Fail"]).astype(int).values
    X_te = test_df[features].values
    y_te = test_df["final_result"].isin(["Withdrawn", "Fail"]).astype(int).values

    pipe = build_pipeline()
    pipe.fit(X_tr, y_tr)
    proba = pipe.predict_proba(X_te)[:, 1]

    metrics = metrics_at(y_te, proba, THETA_STAR[window])
    metrics["window"] = window
    metrics["n_train"] = int(len(train_df))
    metrics["n_overlap_removed"] = int(len(overlap_ids))
    metrics["n_test_after_overlap_removal"] = int(len(test_df))

    overlap_info = {
        "window": window,
        "train_students": int(len(train_ids)),
        "test_students_before": int(len(test_ids_all)),
        "overlap_students": int(len(overlap_ids)),
        "test_students_after": int(len(set(test_df["id_student"]))),
    }

    return metrics, overlap_info


def main() -> None:
    rows = []
    overlaps = []
    for window in WINDOWS:
        m, o = run_window(window)
        rows.append(m)
        overlaps.append(o)
        print(f"[done] {window} | overlap removed: {o['overlap_students']}")

    results = pd.DataFrame(rows)
    overlap_df = pd.DataFrame(overlaps)
    results.to_csv(RESULTS_DIR / "cross_cohort_results.csv", index=False)
    overlap_df.to_csv(RESULTS_DIR / "cross_cohort_overlap.csv", index=False)

    print("\nCross-cohort results (2013 -> 2014):")
    print(results[["window", "n_train", "n_test",
                   "pr_auc", "recall", "f2",
                   "expected_cost"]].round(4).to_string(index=False))
    print("\nOverlap summary:")
    print(overlap_df.to_string(index=False))
    print(f"\nWrote {RESULTS_DIR / 'cross_cohort_results.csv'}")
    print(f"Wrote {RESULTS_DIR / 'cross_cohort_overlap.csv'}")


if __name__ == "__main__":
    main()