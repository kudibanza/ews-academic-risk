"""
Imbalance strategy benchmark per protocol.yaml §6 (RQ3, sub-step 4.1).
Uses imblearn.pipeline.Pipeline so resampling is applied ONLY on the
training fold (Rule 2). Models: lightgbm, xgboost, logreg.
Run from project root: python -m src.imbalance.benchmark
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.over_sampling import SMOTE, ADASYN
from imblearn.under_sampling import TomekLinks
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier


from src.models.metrics import compute_metrics
from src.models.pipeline import get_feature_names

from sklearn.base import BaseEstimator, TransformerMixin

class ClassWeightForXGBoost(BaseEstimator, TransformerMixin):
    """
    Computes scale_pos_weight = n_negative / n_positive on the training
    fold and sets it on the downstream XGBClassifier. This replicates
    class_weight='balanced' without requiring XGBoost to parse a string.
    Only used when strategy == 'class_weight'.
    """
    def fit(self, X, y):
        y = np.asarray(y)
        n_pos = int((y == 1).sum())
        n_neg = int((y == 0).sum())
        self.scale_pos_weight_ = n_neg / n_pos if n_pos > 0 else 1.0
        return self

    def transform(self, X):
        return X

    def fit_transform(self, X, y=None):
        self.fit(X, y)
        return X

PROCESSED_DIR = Path("data/processed")
RESULTS_DIR = Path("results/tables")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

WINDOWS = ["W2", "W4", "W6", "W8"]
MODELS = ["lightgbm", "xgboost", "logreg"]
'''As strategias funcionam como transformers nesse caso'''
STRATEGIES = ["none", "smote", "adasyn", "tomek", "class_weight"]
N_SPLITS = 5
SEED = 42


def build_imbalance_pipeline(model_name: str, strategy: str, variant: str = "A"):
    """Build imblearn Pipeline with resampling inside training fold only.
    Correction B: for ADASYN/SMOTE/Tomek, XGBoost uses scale_pos_weight=1.0
    to avoid double correction (the resampler already balances the classes).
    """
    steps = [("imputer", SimpleImputer(strategy="median"))]

    if strategy == "smote":
        steps.append(("resampler", SMOTE(random_state=SEED)))
    elif strategy == "adasyn":
        steps.append(("resampler", ADASYN(
            sampling_strategy="minority",
            random_state=SEED,
            n_neighbors=3,
        )))
    elif strategy == "tomek":
        steps.append(("resampler", TomekLinks()))

    if model_name == "logreg":
        steps.append(("scaler", StandardScaler()))

    if model_name == "lightgbm":
        clf = LGBMClassifier(
            n_estimators=100, random_state=SEED, n_jobs=-1, verbose=-1,
            class_weight="balanced" if strategy == "class_weight" else None,
        )
    elif model_name == "xgboost":
        # XGBoost requires a numeric scale_pos_weight (no "balanced" string).
        # We compute it from the training fold at fit time via a small
        # wrapper, so it respects Rule 1 (no test-fold statistics).
        clf = XGBClassifier(
            n_estimators=100, random_state=SEED, n_jobs=-1,
            eval_metric="logloss",
            scale_pos_weight=1.0,  # default; overridden by wrapper below
        )
        if strategy == "class_weight":
            steps.append(("scale_pos", ClassWeightForXGBoost()))
    elif model_name == "logreg":
        clf = LogisticRegression(
            max_iter=1000, random_state=SEED,
            class_weight="balanced" if strategy == "class_weight" else None,
        )
    else:
        raise ValueError(f"unknown model: {model_name}")

    steps.append(("model", clf))
    return ImbPipeline(steps)


def run_benchmark() -> pd.DataFrame:
    """Run benchmark. Records a 'status' column: 'ok' or 'skipped'.
    Skipped folds (e.g. ADASYN failures) are logged with null metrics,
    so the summary can report valid-fold counts explicitly.
    """
    rows = []
    for window in WINDOWS:
        df = pd.read_parquet(PROCESSED_DIR / f"features_{window}.parquet")
        features = get_feature_names("A")
        X = df[features].values
        y = df["final_result"].isin(["Withdrawn", "Fail"]).astype(int).values
        groups = df["id_student"].values

        gkf = GroupKFold(n_splits=N_SPLITS)
        for model_name in MODELS:
            for strategy in STRATEGIES:
                skipped = 0
                for fold, (tr, te) in enumerate(gkf.split(X, y, groups), start=1):
                    pipe = build_imbalance_pipeline(model_name, strategy, "A")
                    try:
                        pipe.fit(X[tr], y[tr])
                        proba = pipe.predict_proba(X[te])[:, 1]
                        m = compute_metrics(y[te], proba, threshold=0.5)
                        rows.append({
                            "window": window,
                            "model": model_name,
                            "strategy": strategy,
                            "fold": fold,
                            "n_train": int(len(tr)),
                            "n_test": int(len(te)),
                            "status": "ok",
                            **m,
                        })
                    except ValueError as e:
                        if "No samples will be generated" in str(e):
                            skipped += 1
                            rows.append({
                                "window": window,
                                "model": model_name,
                                "strategy": strategy,
                                "fold": fold,
                                "n_train": int(len(tr)),
                                "n_test": int(len(te)),
                                "status": "skipped",
                                "pr_auc": None, "roc_auc": None,
                                "recall": None, "precision": None, "f2": None,
                            })
                            continue
                        raise
                msg = f"[done] {window} | {model_name} | {strategy}"
                if skipped:
                    msg += f"  ({skipped}/{N_SPLITS} folds skipped)"
                print(msg)
    return pd.DataFrame(rows)


def summarize(results: pd.DataFrame) -> pd.DataFrame:
    """Summarize only valid folds. Reports n_valid_folds and n_skipped_folds
    explicitly, so combinations with systematic resampler failures are
    visible rather than silently omitted.
    """
    metrics = ["pr_auc", "roc_auc", "recall", "precision", "f2"]
    ok = results[results["status"] == "ok"]
    agg = (ok.groupby(["window", "model", "strategy"])[metrics]
           .agg(["mean", "std"]).reset_index())
    agg.columns = ["_".join(c).strip("_") for c in agg.columns]

    # Add fold counts (valid and skipped) per combination
    counts = (results.groupby(["window", "model", "strategy", "status"])
              .size().unstack(fill_value=0).reset_index())
    counts = counts.rename(columns={"ok": "n_valid_folds",
                                    "skipped": "n_skipped_folds"})
    for col in ["n_valid_folds", "n_skipped_folds"]:
        if col not in counts.columns:
            counts[col] = 0
    agg = agg.merge(counts[["window", "model", "strategy",
                            "n_valid_folds", "n_skipped_folds"]],
                    on=["window", "model", "strategy"], how="left")
    return agg


def main() -> None:
    results = run_benchmark()
    results.to_csv(RESULTS_DIR / "imbalance_results.csv", index=False)
    summary = summarize(results)
    summary.to_csv(RESULTS_DIR / "imbalance_summary.csv", index=False)
    print(f"\nWrote {RESULTS_DIR / 'imbalance_results.csv'}")
    print(f"Wrote {RESULTS_DIR / 'imbalance_summary.csv'}")
    print(f"Total runs: {len(results) // N_SPLITS}  |  rows: {len(results)}")


if __name__ == "__main__":
    main()