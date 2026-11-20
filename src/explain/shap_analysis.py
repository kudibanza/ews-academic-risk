"""
Global SHAP analysis per protocol.yaml §14 (RQ4, sub-step 5.3).
Reads JSONL artifacts, computes per-feature mean |SHAP| per window,
flagged counts, and produces a figure.
Run from project root: python -m src.explain.shap_analysis
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ARTIFACTS_DIR = Path("results/shap_artifacts")
TABLES_DIR = Path("results/tables")
FIGURES_DIR = Path("results/figures")
TABLES_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

WINDOWS = ["W2", "W4", "W6", "W8"]
PRESENTATIONS = ["2013B", "2013J", "2014B", "2014J"]
FEATURES = ["S_vle", "D_active", "H_entropy", "Delta_t", "S_score", "click_trend"]


def load_records() -> list[dict]:
    recs = []
    for window in WINDOWS:
        for pres in PRESENTATIONS:
            path = ARTIFACTS_DIR / window / f"{pres}.jsonl"
            if not path.exists():
                continue
            with path.open(encoding="utf-8") as f:
                for line in f:
                    recs.append(json.loads(line))
    return recs


def build_feature_matrix(records: list[dict]) -> pd.DataFrame:
    """For each record, extract per-feature SHAP value.
    Factors not in top-5 are aggregated into other_factors_sum and
    distributed proportionally? No — for feature importance we only
    use the factors that appear in the top-5 lists. This is a known
    limitation: the top-5 lists capture the dominant contributions.
    """
    rows = []
    for r in records:
        row = {"window": r["window"], "flagged": r["flagged"],
               "risk_score": r["risk_score"]}
        for f in FEATURES:
            row[f] = 0.0
        for f in r["top_positive_factors"] + r["top_negative_factors"]:
            if f["feature"] in FEATURES:
                row[f["feature"]] += f["shap_value"]
        rows.append(row)
    return pd.DataFrame(rows)


def compute_importance(df: pd.DataFrame) -> pd.DataFrame:
    """Mean absolute SHAP per feature per window."""
    records = []
    for window in WINDOWS:
        sub = df[df["window"] == window]
        for f in FEATURES:
            records.append({
                "window": window,
                "feature": f,
                "mean_abs_shap": float(sub[f].abs().mean()),
            })
    return pd.DataFrame(records)


def flagged_counts(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for window in WINDOWS:
        sub = df[df["window"] == window]
        out.append({
            "window": window,
            "n_students": len(sub),
            "n_flagged": int(sub["flagged"].sum()),
            "flagged_pct": float(sub["flagged"].mean()),
            "mean_risk": float(sub["risk_score"].mean()),
        })
    return pd.DataFrame(out)


def plot_importance(imp: pd.DataFrame) -> None:
    pivot = imp.pivot(index="feature", columns="window",
                      values="mean_abs_shap").loc[FEATURES, WINDOWS]
    ax = pivot.plot(kind="bar", figsize=(10, 6))
    ax.set_ylabel("Mean |SHAP| (log-odds)")
    ax.set_title("SHAP feature importance by window")
    ax.set_xlabel("Feature")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "shap_importance_by_window.png", dpi=150)
    plt.close()


def main() -> None:
    records = load_records()
    print(f"Loaded {len(records):,} records")
    df = build_feature_matrix(records)

    imp = compute_importance(df)
    imp.to_csv(TABLES_DIR / "shap_importance.csv", index=False)

    counts = flagged_counts(df)
    counts.to_csv(TABLES_DIR / "shap_flagged_counts.csv", index=False)

    plot_importance(imp)

    print("\nMean |SHAP| per feature and window:")
    pivot = imp.pivot(index="feature", columns="window",
                      values="mean_abs_shap").loc[FEATURES, WINDOWS]
    print(pivot.round(4).to_string())

    print("\nFlagged counts per window:")
    print(counts.round(4).to_string(index=False))

    print(f"\nWrote {TABLES_DIR / 'shap_importance.csv'}")
    print(f"Wrote {TABLES_DIR / 'shap_flagged_counts.csv'}")
    print(f"Wrote {FIGURES_DIR / 'shap_importance_by_window.png'}")


if __name__ == "__main__":
    main()