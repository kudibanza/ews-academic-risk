"""
Deterministic cleaning and operational exclusion per protocol.yaml §4.
Global operations only (per-student, no dataset statistics).
Run from project root: python -m src.data.cleaning
"""
import json
from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
REPORT_DIR = Path("experiments/02_feature_build")
REPORT_MD = REPORT_DIR / "cleaning_report.md"
REPORT_JSON = REPORT_DIR / "cleaning_summary.json"

CUTOFFS = {"W2": 14, "W4": 28, "W6": 42, "W8": 56}
DATE_COLS = ["date_registration", "date_unregistration"]


def load_student_info() -> pd.DataFrame:
    info = pd.read_csv(RAW_DIR / "studentInfo.csv")
    reg = pd.read_csv(RAW_DIR / "studentRegistration.csv")
    # Convert date columns to nullable Int64 (audit confirmed no fractional values)
    for col in DATE_COLS:
        reg[col] = reg[col].astype("Int64")
    # Merge registration dates onto studentInfo
    merged = info.merge(
        reg[["id_student", "code_module", "code_presentation",
             "date_registration", "date_unregistration"]],
        on=["id_student", "code_module", "code_presentation"],
        how="left",
        validate="one_to_one",
    )
    return merged


def compute_eligibility(df: pd.DataFrame, cutoff: int) -> pd.DataFrame:
    """
    Eligible at window k if NOT (date_unregistration.notna() AND
    date_unregistration <= cutoff). Depends ONLY on date_unregistration
    (protocol §4 independence_from_registration_date).
    """
    excluded = df["date_unregistration"].notna() & (df["date_unregistration"] <= cutoff)
    out = df[["id_student", "code_module", "code_presentation",
              "final_result", "date_registration", "date_unregistration"]].copy()
    out["window"] = None  # filled by caller
    out["cutoff_days"] = cutoff
    out["eligible"] = ~excluded
    return out


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    base = load_student_info()
    summary = {"total_rows": int(len(base))}
    md = ["# Cleaning Report — Sub-step 2.1", "",
          "Deterministic cleaning and operational exclusion (protocol.yaml §4).",
          "No imputation, no scaling, no feature construction.", ""]

    md.append("## Base counts")
    md.append(f"- Total rows in studentInfo: **{len(base):,}**")
    md.append(f"- Unique students: **{base['id_student'].nunique():,}**")
    md.append(f"- Rows with date_registration null: "
              f"**{int(base['date_registration'].isna().sum()):,}**")
    md.append(f"- Rows with date_unregistration null: "
              f"**{int(base['date_unregistration'].isna().sum()):,}**")
    md.append("")

    md.append("## Eligibility per window")
    md.append("| window | cutoff | rows | excluded | eligible | eligible % |")
    md.append("|---|---|---|---|---|---|")

    for window, cutoff in CUTOFFS.items():
        elig = compute_eligibility(base, cutoff)
        elig["window"] = window
        n_rows = len(elig)
        n_excluded = int((~elig["eligible"]).sum())
        n_eligible = int(elig["eligible"].sum())
        pct = n_eligible / n_rows if n_rows else 0.0
        md.append(f"| {window} | {cutoff} | {n_rows:,} | {n_excluded:,} | "
                  f"{n_eligible:,} | {pct:.3%} |")

        out_path = PROCESSED_DIR / f"eligibility_{window}.parquet"
        elig.to_parquet(out_path, index=False)

        summary[window] = {
            "cutoff_days": cutoff,
            "rows": n_rows,
            "excluded": n_excluded,
            "eligible": n_eligible,
            "eligible_pct": round(pct, 4),
            "output": str(out_path),
        }

    md.append("")
    md.append("## Outputs")
    for window in CUTOFFS:
        md.append(f"- `data/processed/eligibility_{window}.parquet`")

    REPORT_MD.write_text("\n".join(md), encoding="utf-8")
    REPORT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Report written to {REPORT_MD}")
    print(f"Summary written to {REPORT_JSON}")


if __name__ == "__main__":
    main()