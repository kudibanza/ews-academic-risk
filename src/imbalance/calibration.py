"""
Calibration per protocol.yaml §8 (RQ3, sub-step 4.2).
Calibrates the best configurations from 4.1 on the training fold,
evaluates ECE and Brier on the test fold.
Run from project root: python -m src.imbalance.calibration
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.over_sampling import SMOTE
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

from src.models.metrics import compute_metrics
from src.models.pipeline import get_feature_names
from sklearn.frozen import FrozenEstimator

PROCESSED_DIR = Path("data/processed")
RESULTS_DIR = Path("results/tables")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

WINDOWS = ["W2", "W4", "W6", "W8"]
N_SPLITS = 5
SEED = 42

CONFIGS = [
    ("lightgbm", "class_weight"),
    ("xgboost", "class_weight"),
    ("lightgbm", "none"),
]
CALIBRATION_METHODS = ["sigmoid", "isotonic"]  # Platt, isotonic


def expected_calibration_error(y_true, y_prob, n_bins=10):
    """ECE: weighted mean absolute difference between accuracy and confidence."""
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_ids = np.digitize(y_prob, bins) - 1
    bin_ids = np.clip(bin_ids, 0, n_bins - 1)
    ece = 0.0
    n = len(y_true)
    for b in range(n_bins):
        mask = bin_ids == b
        if mask.sum() == 0:
            continue
        acc = y_true[mask].mean()
        conf = y_prob[mask].mean()
        ece += (mask.sum() / n) * abs(acc - conf)
    return float(ece)


def build_base_pipeline(model_name: str, strategy: str):
    """Build the imblearn pipeline (same as 4.1) without calibration."""
    steps = [("imputer", SimpleImputer(strategy="median"))]
    if model_name == "logreg":
        steps.append(("scaler", StandardScaler()))
    if model_name == "lightgbm":
        clf = LGBMClassifier(
            n_estimators=100, random_state=SEED, n_jobs=-1, verbose=-1,
            class_weight="balanced" if strategy == "class_weight" else None,
        )
    elif model_name == "xgboost":
        clf = XGBClassifier(
            n_estimators=100, random_state=SEED, n_jobs=-1,
            eval_metric="logloss",
            scale_pos_weight=1.0,  # class_weight handled below
        )
    else:
        raise ValueError(model_name)
    steps.append(("model", clf))
    return ImbPipeline(steps)


def run_calibration() -> pd.DataFrame:
    rows = []
    for window in WINDOWS:
        df = pd.read_parquet(PROCESSED_DIR / f"features_{window}.parquet")
        features = get_feature_names("A")
        X = df[features].values
        y = df["final_result"].isin(["Withdrawn", "Fail"]).astype(int).values
        groups = df["id_student"].values

        gkf = GroupKFold(n_splits=N_SPLITS)
        for model_name, strategy in CONFIGS:
            for fold, (tr, te) in enumerate(gkf.split(X, y, groups), start=1):
                # Compute scale_pos_weight for XGBoost class_weight
                spw = 1.0
                if model_name == "xgboost" and strategy == "class_weight":
                    n_pos = int((y[tr] == 1).sum())
                    n_neg = int((y[tr] == 0).sum())
                    spw = n_neg / n_pos if n_pos > 0 else 1.0

                # Uncalibrated baseline
                pipe = build_base_pipeline(model_name, strategy)
                if model_name == "xgboost" and strategy == "class_weight":
                    pipe.named_steps["model"].set_params(scale_pos_weight=spw)
                pipe.fit(X[tr], y[tr])
                proba_uncal = pipe.predict_proba(X[te])[:, 1]

                rows.append({
                    "window": window, "model": model_name,
                    "strategy": strategy, "fold": fold,
                    "calibration": "none",
                    "ece": expected_calibration_error(y[te], proba_uncal),
                    "brier": float(brier_score_loss(y[te], proba_uncal)),
                    "pr_auc": float(compute_metrics(y[te], proba_uncal)["pr_auc"]),
                })

                # Calibrated versions
                for method in CALIBRATION_METHODS:
                    base = build_base_pipeline(model_name, strategy)
                    if model_name == "xgboost" and strategy == "class_weight":
                        base.named_steps["model"].set_params(scale_pos_weight=spw)
                    base.fit(X[tr], y[tr])

                    cal = CalibratedClassifierCV(
                        estimator=FrozenEstimator(base),
                        method=method,
                    )
                    cal.fit(X[tr], y[tr])
                    proba_cal = cal.predict_proba(X[te])[:, 1]

                    rows.append({
                        "window": window, "model": model_name,
                        "strategy": strategy, "fold": fold,
                        "calibration": method,
                        "ece": expected_calibration_error(y[te], proba_cal),
                        "brier": float(brier_score_loss(y[te], proba_cal)),
                        "pr_auc": float(compute_metrics(y[te], proba_cal)["pr_auc"]),
                    })
            print(f"[done] {window} | {model_name} | {strategy}")
    return pd.DataFrame(rows)


def summarize(results: pd.DataFrame) -> pd.DataFrame:
    metrics = ["ece", "brier", "pr_auc"]
    agg = (results.groupby(["window", "model", "strategy", "calibration"])[metrics]
           .agg(["mean", "std"]).reset_index())
    agg.columns = ["_".join(c).strip("_") for c in agg.columns]
    return agg


def main() -> None:
    results = run_calibration()
    results.to_csv(RESULTS_DIR / "calibration_results.csv", index=False)
    summary = summarize(results)
    summary.to_csv(RESULTS_DIR / "calibration_summary.csv", index=False)
    print(f"\nWrote {RESULTS_DIR / 'calibration_results.csv'}")
    print(f"Wrote {RESULTS_DIR / 'calibration_summary.csv'}")


if __name__ == "__main__":
    main()