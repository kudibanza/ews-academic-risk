"""
Out-of-fold SHAP generation per protocol.yaml §14 (RQ4, sub-step 5.1).
For each window, GroupKFold(5); students in the test fold are explained
by a model that did not see them in training.
Writes JSONL artifacts to results/shap_artifacts/{window}/{presentation}.jsonl.
Run from project root: python -m src.explain.shap_cache
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import shap
from sklearn.model_selection import GroupKFold
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.impute import SimpleImputer
from lightgbm import LGBMClassifier

from src.models.pipeline import get_feature_names

PROCESSED_DIR = Path("data/processed")
ARTIFACTS_DIR = Path("results/shap_artifacts")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

WINDOWS = ["W2", "W4", "W6", "W8"]
THETA_STAR = {"W2": 0.116, "W4": 0.120, "W6": 0.160, "W8": 0.172}
N_SPLITS = 5
SEED = 42
PROTOCOL_VERSION = "1.0.15"
MODEL_NAME = "lightgbm"
MAX_FACTORS = 5


def build_pipeline() -> ImbPipeline:
    return ImbPipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("model", LGBMClassifier(
            n_estimators=100, random_state=SEED, n_jobs=-1, verbose=-1,
            class_weight="balanced",
        )),
    ])


def shapiro_explanations(explainer, X_test, feature_names):
    """Return (shap_values, base_value) for the positive class.
    shap_values: array shape (n_samples, n_features)
    base_value: float
    """
    sv = explainer.shap_values(X_test)
    # LightGBM binary: shap_values is a list of two arrays or a single array
    if isinstance(sv, list):
        sv = sv[1]
    base = explainer.expected_value
    if isinstance(base, list):
        base = base[1]
    return np.asarray(sv), float(base)


def top_factors(shap_row, feature_names, feature_values_row, k=MAX_FACTORS):
    """Return (top_positive, top_negative, other_sum).
    other_sum = sum of SHAP values not captured in the top-k lists on
    either side. Enables exact reconstruction.
    """
    idx = np.argsort(shap_row)
    neg_idx = idx[:k]
    pos_idx = idx[::-1][:k]

    pos = [{"feature": feature_names[i],
            "shap_value": float(shap_row[i]),
            "feature_value": float(feature_values_row[i])}
           for i in pos_idx if shap_row[i] > 0]
    neg = [{"feature": feature_names[i],
            "shap_value": float(shap_row[i]),
            "feature_value": float(feature_values_row[i])}
           for i in neg_idx if shap_row[i] < 0]

    captured = sum(f["shap_value"] for f in pos) + sum(f["shap_value"] for f in neg)
    total = float(np.sum(shap_row))
    other_sum = total - captured
    return pos, neg, other_sum


def run_window(window: str, theta: float) -> int:
    df = pd.read_parquet(PROCESSED_DIR / f"features_{window}.parquet")
    features = get_feature_names("A")
    X = df[features].values
    y = df["final_result"].isin(["Withdrawn", "Fail"]).astype(int).values
    groups = df["id_student"].values

    # Per-presentation output files
    out_dir = ARTIFACTS_DIR / window
    out_dir.mkdir(parents=True, exist_ok=True)

    gkf = GroupKFold(n_splits=N_SPLITS)
    rows_written = 0
    for fold, (tr, te) in enumerate(gkf.split(X, y, groups), start=1):
        pipe = build_pipeline()
        pipe.fit(X[tr], y[tr])

        # Extract the fitted imputer and model to explain in the imputed space
        imputer = pipe.named_steps["imputer"]
        model = pipe.named_steps["model"]
        X_te_imputed = imputer.transform(X[te])

        explainer = shap.TreeExplainer(model)
        shap_vals, base_value = shapiro_explanations(
            explainer, X_te_imputed, features
        )
        proba = pipe.predict_proba(X[te])[:, 1]

        # Group test rows by presentation
        te_df = df.iloc[te].copy()
        te_df["_row_in_te"] = np.arange(len(te))
        for pres, grp in te_df.groupby("code_presentation"):
            path = out_dir / f"{pres}.jsonl"
            with path.open("a", encoding="utf-8") as f:
                for _, row in grp.iterrows():
                    i = int(row["_row_in_te"])
                    pos, neg, other_sum = top_factors(
                        shap_vals[i], features, X_te_imputed[i]
                    )
                    record = {
                        "student_id": int(row["id_student"]),
                        "presentation": pres,
                        "window": window,
                        "model_name": MODEL_NAME,
                        "model_version": f"fold{fold}",
                        "protocol_version": PROTOCOL_VERSION,
                        "risk_score": float(proba[i]),
                        "threshold_applied": float(theta),
                        "flagged": bool(proba[i] >= theta),
                        "top_positive_factors": pos,
                        "top_negative_factors": neg,
                        "other_factors_sum": other_sum,
                        "base_value": base_value,
                    }
                    f.write(json.dumps(record) + "\n")
                    rows_written += 1
        print(f"[done] {window} | fold {fold} | {len(te)} rows explained")

    return rows_written


def main() -> None:
    # Clean existing artifacts to avoid appending duplicates on re-runs
    for window in WINDOWS:
        wdir = ARTIFACTS_DIR / window
        if wdir.exists():
            for p in wdir.glob("*.jsonl"):
                p.unlink()

    total = 0
    for window in WINDOWS:
        total += run_window(window, THETA_STAR[window])
    print(f"\nTotal artifacts written: {total}")
    print(f"Output: {ARTIFACTS_DIR}")


if __name__ == "__main__":
    main()