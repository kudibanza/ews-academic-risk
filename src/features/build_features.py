"""
Cumulative feature engineering per protocol.yaml §5 (v1.0.5).
Seven features: S_vle, D_active, H_entropy, Delta_t, S_score,
still_registered, click_trend.
Only eligible students per window. Only date <= cutoff_k (Rule 3).
Run from project root: python -m src.features.build_features
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
REPORT_DIR = Path("experiments/02_feature_build")
REPORT_MD = REPORT_DIR / "feature_report.md"
REPORT_JSON = REPORT_DIR / "feature_summary.json"

CUTOFFS = {"W2": 14, "W4": 28, "W6": 42, "W8": 56}
N_ACTIVITY_TYPES = 20  # OULAD activity_type categories


def shannon_entropy(series_of_counts: pd.Series) -> float:
    """Shannon entropy (base 2) over a vector of counts."""
    total = series_of_counts.sum()
    if total == 0:
        return 0.0
    p = series_of_counts / total
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def load_inputs():
    info = pd.read_csv(RAW_DIR / "studentInfo.csv")
    reg = pd.read_csv(RAW_DIR / "studentRegistration.csv")
    for col in ["date_registration", "date_unregistration"]:
        reg[col] = reg[col].astype("Int64")
    info = info.merge(
        reg[["id_student", "code_module", "code_presentation",
             "date_registration", "date_unregistration"]],
        on=["id_student", "code_module", "code_presentation"],
        how="left", validate="one_to_one",
    )
    vle = pd.read_csv(RAW_DIR / "vle.csv")
    svle = pd.read_csv(RAW_DIR / "studentVle.csv")
    asm = pd.read_csv(RAW_DIR / "assessments.csv")
    sa = pd.read_csv(RAW_DIR / "studentAssessment.csv")
    return info, vle, svle, asm, sa


def compute_vle_features(svle_w: pd.DataFrame, vle: pd.DataFrame) -> pd.DataFrame:
    """S_vle, D_active, H_entropy from clicks up to cutoff."""
    key = ["id_student", "code_module", "code_presentation"]
    # Total clicks and distinct active days
    base = svle_w.groupby(key).agg(
        S_vle=("sum_click", "sum"),
        D_active=("date", "nunique"),
    ).reset_index()
    # Entropy: join activity_type, count clicks per type per student
    svle_typed = svle_w.merge(
        vle[["id_site", "code_module", "code_presentation", "activity_type"]],
        on=["id_site", "code_module", "code_presentation"],
        how="left",
    )
    counts = (svle_typed.groupby(key + ["activity_type"])["sum_click"]
              .sum().reset_index())
    ent = (counts.groupby(key)["sum_click"]
           .apply(shannon_entropy)
           .reset_index(name="H_entropy"))
    return base.merge(ent, on=key, how="left")


def compute_assessment_features(sa_w: pd.DataFrame) -> pd.DataFrame:
    """Delta_t and S_score from assessments due up to cutoff.
    Expects sa_w to already contain 'date_due' and 'score'."""
    key = ["id_student", "code_module", "code_presentation"]
    merged = sa_w.copy()
    merged["latency"] = merged["date_submitted"] - merged["date_due"]
    out = merged.groupby(key).agg(
        Delta_t=("latency", "mean"),
        S_score=("score", "mean"),
    ).reset_index()
    return out


def compute_click_trend(svle: pd.DataFrame, cutoff: int) -> pd.DataFrame:
    """
    click_trend(w_k) = mean daily clicks in the two most recent weeks
                     - mean daily clicks in the two weeks before that.
    For W2 (cutoff=14): week 2 minus week 1 (reduced form).
    Only uses activity with date <= cutoff (Rule 3).
    """
    key = ["id_student", "code_module", "code_presentation"]
    df = svle[svle["date"] <= cutoff].copy()
    if cutoff == 14:
        recent_start, prev_start = 7, 0
        recent_days, prev_days = 7, 7
    else:
        recent_start, prev_start = cutoff - 14, cutoff - 28
        recent_days, prev_days = 14, 14

    recent = df[(df["date"] > recent_start) & (df["date"] <= cutoff)]
    prev = df[(df["date"] > prev_start) & (df["date"] <= recent_start)]

    r = recent.groupby(key)["sum_click"].sum().rename("recent_clicks").reset_index()
    p = prev.groupby(key)["sum_click"].sum().rename("prev_clicks").reset_index()
    out = r.merge(p, on=key, how="outer").fillna(0)
    out["click_trend"] = out["recent_clicks"] / recent_days - out["prev_clicks"] / prev_days
    return out[key + ["click_trend"]]


def build_window(info: pd.DataFrame, vle, svle, asm, sa,
                 window: str, cutoff: int) -> pd.DataFrame:
    key = ["id_student", "code_module", "code_presentation"]

    elig = info[
        ~(info["date_unregistration"].notna() &
          (info["date_unregistration"] <= cutoff))
    ][key + ["final_result", "date_registration", "date_unregistration"]].copy()

    svle_w = svle[svle["date"] <= cutoff]

    asm_due = asm[["id_assessment", "code_module", "code_presentation", "date"]].rename(
        columns={"date": "date_due"}
    )
    sa_w = sa.merge(asm_due, on="id_assessment", how="left")
    sa_w = sa_w[sa_w["date_due"] <= cutoff]
    sa_w = sa_w[["id_assessment", "id_student", "code_module",
                 "code_presentation", "date_submitted", "date_due", "score"]]

    vle_feat = compute_vle_features(svle_w, vle)
    asm_feat = compute_assessment_features(sa_w)
    trend_feat = compute_click_trend(svle, cutoff)

    out = (elig
           .merge(vle_feat, on=key, how="left")
           .merge(asm_feat, on=key, how="left")
           .merge(trend_feat, on=key, how="left"))
    out["still_registered"] = 1
    out["window"] = window
    out["cutoff_days"] = cutoff
    return out


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    info, vle, svle, asm, sa = load_inputs()
    summary = {}
    md = ["# Feature Report — Sub-step 2.2", "",
          "Cumulative features per protocol.yaml §5 (v1.0.5).",
          "Only eligible students. Only date <= cutoff_k (Rule 3).", ""]

    for window, cutoff in CUTOFFS.items():
        feats = build_window(info, vle, svle, asm, sa, window, cutoff)
        out_path = PROCESSED_DIR / f"features_{window}.parquet"
        feats.to_parquet(out_path, index=False)

        n = len(feats)
        md.append(f"## {window} (cutoff={cutoff} days)")
        md.append(f"- Rows: **{n:,}**")
        md.append(f"- Null counts per feature:")
        for col in ["S_vle", "D_active", "H_entropy", "Delta_t",
                    "S_score", "click_trend"]:
            md.append(f"  - `{col}`: {int(feats[col].isna().sum()):,}")
        md.append(f"- `still_registered` unique values: "
                  f"{sorted(feats['still_registered'].unique().tolist())}")
        md.append(f"- Output: `{out_path}`")
        md.append("")

        summary[window] = {
            "cutoff_days": cutoff,
            "rows": n,
            "nulls": {c: int(feats[c].isna().sum())
                      for c in ["S_vle", "D_active", "H_entropy",
                                "Delta_t", "S_score", "click_trend"]},
            "output": str(out_path),
        }

    REPORT_MD.write_text("\n".join(md), encoding="utf-8")
    REPORT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Report written to {REPORT_MD}")
    print(f"Summary written to {REPORT_JSON}")


if __name__ == "__main__":
    main()