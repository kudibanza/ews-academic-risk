"""
Model benchmarking per protocol.yaml §16 (RQ2).
GroupKFold(5) by student_id. Default hyperparameters (tuning in Step 3b).
W2 runs under Variant A and Variant B; W4-W8 under Variant A only.
Run from project root: python -m src.models.benchmark
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

from src.models.metrics import compute_metrics
from src.models.pipeline import build_pipeline, get_feature_names

PROCESSED_DIR = Path("data/processed")
RESULTS_DIR = Path("results/tables")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

WINDOWS = ["W2", "W4", "W6", "W8"]
MODELS = ["logreg", "dtree", "rf", "xgboost", "lightgbm"]
N_SPLITS = 5
SEED = 42


def get_runs() -> list[tuple[str, str, str]]:
    """Return (window, model, variant) runs. W2 has A and B; others A only."""
    runs = []
    for window in WINDOWS:
        for model in MODELS:
            runs.append((window, model, "A"))
        if window == "W2":
            for model in MODELS:
                runs.append((window, model, "B"))
    return runs


def run_benchmark() -> pd.DataFrame:
    rows = []
    for window, model_name, variant in get_runs():
        df = pd.read_parquet(PROCESSED_DIR / f"features_{window}.parquet")
        features = get_feature_names(variant)
        X = df[features].values
        y = df["final_result"].isin(["Withdrawn", "Fail"]).astype(int).values
        groups = df["id_student"].values

        gkf = GroupKFold(n_splits=N_SPLITS)
        for fold, (tr, te) in enumerate(gkf.split(X, y, groups), start=1):
            pipe = build_pipeline(model_name, variant)
            pipe.fit(X[tr], y[tr])
            proba = pipe.predict_proba(X[te])[:, 1]
            m = compute_metrics(y[te], proba, threshold=0.5)
            rows.append({
                "window": window,
                "model": model_name,
                "variant": variant,
                "fold": fold,
                "n_train": int(len(tr)),
                "n_test": int(len(te)),
                "pos_rate_test": float(y[te].mean()),
                **m,
            })
        print(f"[done] {window} | {model_name} | variant {variant}")
    return pd.DataFrame(rows)


def summarize(results: pd.DataFrame) -> pd.DataFrame:
    metrics = ["pr_auc", "roc_auc", "recall", "precision", "f2"]
    agg = (results.groupby(["window", "model", "variant"])[metrics]
           .agg(["mean", "std"]).reset_index())
    agg.columns = ["_".join(c).strip("_") for c in agg.columns]
    return agg


def main() -> None:
    results = run_benchmark()
    results.to_csv(RESULTS_DIR / "benchmark_results.csv", index=False)
    summary = summarize(results)
    summary.to_csv(RESULTS_DIR / "benchmark_summary.csv", index=False)
    print(f"\nWrote {RESULTS_DIR / 'benchmark_results.csv'}")
    print(f"Wrote {RESULTS_DIR / 'benchmark_summary.csv'}")
    print(f"Total runs: {len(results) // N_SPLITS}  |  rows: {len(results)}")


if __name__ == "__main__":
    main()