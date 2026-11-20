"""
Cost-sensitive threshold tuning per protocol.yaml §9 (RQ3, sub-step 4.3).
Models: LightGBM + class_weight, XGBoost + class_weight (both uncalibrated).
Threshold searched on validation fold; evaluated on test fold.
Run from project root: python -m src.imbalance.threshold
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.metrics import (
    average_precision_score, roc_auc_score, recall_score,
    precision_score, fbeta_score,
)
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.impute import SimpleImputer
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier

from src.models.pipeline import get_feature_names

PROCESSED_DIR = Path("data/processed")
RESULTS_DIR = Path("results/tables")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

WINDOWS = ["W2", "W4", "W6", "W8"]
MODELS = ["lightgbm", "xgboost"]
N_SPLITS = 5
SEED = 42
THRESHOLDS = np.arange(0.10, 0.91, 0.01)
COST_RATIOS = {"5:1": (5, 1), "3:1": (3, 1), "10:1": (10, 1)}


def build_pipeline(model_name: str, scale_pos_weight: float = 1.0) -> ImbPipeline:
    """Build pipeline for the given model. Both models use class_weight
    (LightGBM via class_weight='balanced', XGBoost via numeric
    scale_pos_weight computed from the training fold)."""
    if model_name == "lightgbm":
        clf = LGBMClassifier(
            n_estimators=100, random_state=SEED, n_jobs=-1, verbose=-1,
            class_weight="balanced",
        )
    elif model_name == "xgboost":
        clf = XGBClassifier(
            n_estimators=100, random_state=SEED, n_jobs=-1,
            eval_metric="logloss", scale_pos_weight=scale_pos_weight,
        )
    else:
        raise ValueError(f"unknown model: {model_name}")

    return ImbPipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("model", clf),
    ])


def expected_cost(y_true, y_pred, c_fn, c_fp):
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    return fn * c_fn + fp * c_fp


def find_optimal_threshold(y_val, proba_val, c_fn, c_fp):
    """Return theta* minimising expected cost on the validation fold."""
    best_theta, best_cost = 0.5, float("inf")
    for theta in THRESHOLDS:
        y_pred = (proba_val >= theta).astype(int)
        cost = expected_cost(y_val, y_pred, c_fn, c_fp)
        if cost < best_cost:
            best_cost, best_theta = cost, float(theta)
    return best_theta, best_cost


def metrics_at(y_true, proba, theta):
    y_pred = (proba >= theta).astype(int)
    return {
        "threshold": float(theta),
        "pr_auc": float(average_precision_score(y_true, proba)),
        "roc_auc": float(roc_auc_score(y_true, proba)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "f2": float(fbeta_score(y_true, y_pred, beta=2, zero_division=0)),
        "flagged_rate": float(y_pred.mean()),
    }


def compute_spw(y_train):
    """Compute scale_pos_weight = n_neg / n_pos on the training data."""
    n_pos = int((y_train == 1).sum())
    n_neg = int((y_train == 0).sum())
    return (n_neg / n_pos) if n_pos > 0 else 1.0


def run_threshold_tuning() -> pd.DataFrame:
    rows = []
    for window in WINDOWS:
        df = pd.read_parquet(PROCESSED_DIR / f"features_{window}.parquet")
        features = get_feature_names("A")
        X = df[features].values
        y = df["final_result"].isin(["Withdrawn", "Fail"]).astype(int).values
        groups = df["id_student"].values

        gkf = GroupKFold(n_splits=N_SPLITS)
        for fold, (tr, te) in enumerate(gkf.split(X, y, groups), start=1):
            # Inner split: part of train used to search the threshold
            inner = GroupKFold(n_splits=2)
            tr_inner, val_inner = next(inner.split(X[tr], y[tr], groups[tr]))

            for model_name in MODELS:
                # XGBoost: spw from inner training subset (Rule 1)
                spw_inner = compute_spw(y[tr][tr_inner]) if model_name == "xgboost" else 1.0
                pipe_val = build_pipeline(model_name, spw_inner)
                pipe_val.fit(X[tr][tr_inner], y[tr][tr_inner])
                proba_val = pipe_val.predict_proba(X[tr][val_inner])[:, 1]
                y_val = y[tr][val_inner]

                # Full training fold for test evaluation
                spw_full = compute_spw(y[tr]) if model_name == "xgboost" else 1.0
                pipe_full = build_pipeline(model_name, spw_full)
                pipe_full.fit(X[tr], y[tr])
                proba_test = pipe_full.predict_proba(X[te])[:, 1]
                y_test = y[te]

                for label, (c_fn, c_fp) in COST_RATIOS.items():
                    theta_star, _ = find_optimal_threshold(y_val, proba_val, c_fn, c_fp)

                    # Baseline at 0.5
                    base = metrics_at(y_test, proba_test, 0.5)
                    base.update({
                        "window": window, "model": model_name, "fold": fold,
                        "ratio": label, "threshold_type": "0.5",
                        "expected_cost": expected_cost(
                            y_test, (proba_test >= 0.5).astype(int), c_fn, c_fp),
                    })
                    rows.append(base)

                    # Tuned threshold
                    tuned = metrics_at(y_test, proba_test, theta_star)
                    tuned.update({
                        "window": window, "model": model_name, "fold": fold,
                        "ratio": label, "threshold_type": "tuned",
                        "expected_cost": expected_cost(
                            y_test, (proba_test >= theta_star).astype(int),
                            c_fn, c_fp),
                    })
                    rows.append(tuned)
        print(f"[done] {window}")
    return pd.DataFrame(rows)


def summarize(results: pd.DataFrame) -> pd.DataFrame:
    metrics = ["pr_auc", "roc_auc", "recall", "precision", "f2",
               "flagged_rate", "expected_cost", "threshold"]
    agg = (results.groupby(["window", "model", "ratio", "threshold_type"])[metrics]
           .agg(["mean", "std"]).reset_index())
    agg.columns = ["_".join(c).strip("_") for c in agg.columns]
    return agg


def main() -> None:
    results = run_threshold_tuning()
    results.to_csv(RESULTS_DIR / "threshold_results.csv", index=False)
    summary = summarize(results)
    summary.to_csv(RESULTS_DIR / "threshold_summary.csv", index=False)
    print(f"\nWrote {RESULTS_DIR / 'threshold_results.csv'}")
    print(f"Wrote {RESULTS_DIR / 'threshold_summary.csv'}")


if __name__ == "__main__":
    main()