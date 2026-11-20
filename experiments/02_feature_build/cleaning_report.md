# Cleaning Report — Sub-step 2.1

Deterministic cleaning and operational exclusion (protocol.yaml §4).
No imputation, no scaling, no feature construction.

## Base counts
- Total rows in studentInfo: **32,593**
- Unique students: **28,785**
- Rows with date_registration null: **45**
- Rows with date_unregistration null: **22,521**

## Eligibility per window
| window | cutoff | rows | excluded | eligible | eligible % |
|---|---|---|---|---|---|
| W2 | 14 | 32,593 | 4,474 | 28,119 | 86.273% |
| W4 | 28 | 32,593 | 5,055 | 27,538 | 84.491% |
| W6 | 42 | 32,593 | 5,569 | 27,024 | 82.914% |
| W8 | 56 | 32,593 | 6,071 | 26,522 | 81.373% |

ver2.py result:
## Exclusion decomposition (by unregistration date)

| Interval | N | Cumulative excluded |
|---|---|---|
| Before day 0 (negative) | 2,678 | 2,678 |
| 0–14 days | 1,796 | 4,474 (W2) |
| 15–28 days | 581 | 5,055 (W4) |
| 29–42 days | 514 | 5,569 (W6) |
| 43–56 days | 502 | 6,071 (W8) |
| After 56 days | 4,001 | — |
| **Total** | **10,072** | |

Cross-check: excluded per window matches cumulative sums exactly
(W2=4,474; W4=5,055; W6=5,569; W8=6,071).

Interpretation:
- 44.4% of all withdrawals occur before day 14, consistent with the
  literature on early dropout in distance education.
- The W2 sample represents "students still enrolled at day 14", not
  "all students at course start". This is the intended behavior of the
  operational exclusion rule (§4).
- The 4,001 students who withdraw after day 56 remain eligible at every
  window, correctly reflecting that they were still enrolled at
  prediction time. The target `Withdrawn ∪ Fail` captures them at
  course completion.
- Consequence for SHAP: explanations are generated only for eligible
  students at each window; excluded students have no artifact.

## Outputs
- `data/processed/eligibility_W2.parquet`
- `data/processed/eligibility_W4.parquet`
- `data/processed/eligibility_W6.parquet`
- `data/processed/eligibility_W8.parquet`