# SHAP Report — Step 5 (RQ4)

Out-of-fold SHAP explanations generated for 109,203 student-window
records (4 windows × eligible students per window). Model: LightGBM +
class_weight, uncalibrated. Threshold θ* per window at 5:1
(W2=0.116, W4=0.120, W6=0.160, W8=0.172). SHAP values computed via
TreeSHAP on the fold in which each student was held out (out-of-fold).

## 1. Contract validation (sub-step 5.2)

13/13 tests passed in `tests/test_shap_contract.py`:
- Schema fields present; protocol version 1.0.15; model_version in
  {fold1..fold5}; window/presentation consistent.
- risk_score in [0,1]; threshold matches frozen θ*; flagged matches
  risk_score >= threshold.
- Exact probability reconstruction:
  sigmoid(base_value + sum(top5) + other_factors_sum) == risk_score
  (tolerance 1e-6).
- Positive factors have shap_value > 0; negative factors < 0; max 5
  per side; feature_value populated.
- No artifact for excluded students (set equality with eligibility
  parquet per window).

Note on reconstruction: the §14 schema stores top-5 factors per side
plus `other_factors_sum` (the sum of SHAP values outside the top-5).
This makes reconstruction exact. Without `other_factors_sum`, the
residual was up to ~1.1 pp for students with many contributing factors.

## 2. Global feature importance by window

Mean |SHAP| (log-odds) per feature and window:

| Feature | W2 | W4 | W6 | W8 |
|---|---|---|---|---|
| S_vle | **0.471** | 0.150 | 0.101 | 0.070 |
| D_active | 0.109 | 0.365 | 0.379 | **0.437** |
| H_entropy | 0.162 | 0.195 | 0.178 | 0.184 |
| Delta_t | 0.013 | 0.217 | 0.239 | 0.263 |
| S_score | 0.043 | 0.409 | 0.554 | **0.661** |
| click_trend | 0.117 | 0.072 | 0.202 | 0.236 |

Figure: `results/figures/shap_importance_by_window.png`.

### Key findings

1. **Signal migration from behaviour to assessment.** In W2, `S_vle`
   dominates (0.471), reflecting that only clickstream volume is
   available before assessments begin (recall: only 1 assessment in all
   OULAD is due by day 14; see feature_report.md). By W8, `S_score`
   dominates (0.661) and `D_active` is second (0.437). This confirms the
   proposal's hypothesis that the predictive signal shifts from VLE
   behaviour to academic performance as the semester progresses.

2. **`Delta_t` becomes informative only when assessments exist.** Its
   importance rises from 0.013 in W2 to 0.263 in W8, mirroring the
   coverage jump from ~4% to 75% documented in Step 2.

3. **`click_trend` is a non-trivial contributor.** Added in Step 2 as
   an engagement-trajectory feature, it has mean |SHAP| of 0.117 (W2),
   0.072 (W4), 0.202 (W6), 0.236 (W8). The dip in W4 is consistent with
   assessment features taking over at that point; the recovery in W6–W8
   indicates that disengagement trajectory becomes discriminative again
   later in the term.

4. **`H_entropy` is stable but secondary.** ~0.16–0.20 across windows.
   Resource diversity is consistently informative but never the dominant
   driver.

These results are consistent with Zhang & Duan (2026), who found
engagement-trajectory features carry the largest share of predictive
attribution from mid-course onward, and with Waheed et al. (2020), who
showed VLE interaction and assessment features outperform demographic
baselines.

## 3. Flagged counts at θ* (5:1)

| Window | N students | N flagged | Flagged % | Mean risk |
|---|---|---|---|---|
| W2 | 28,119 | 27,977 | **99.5%** | 0.493 |
| W4 | 27,538 | 27,143 | 98.6% | 0.486 |
| W6 | 27,024 | 25,113 | 92.9% | 0.482 |
| W8 | 26,522 | 23,282 | 87.8% | 0.475 |

At the 5:1 cost ratio, the optimal threshold is very low (0.116–0.172),
so almost all students are flagged in W2. This is the mathematically
correct behaviour for a cost function that penalises false negatives
5× more than false positives: the model prefers to flag nearly everyone
rather than miss an at-risk student.

**Operational implication:** flagging 99.5% of students in W2 is not
actionable for advisors (no coordinator can intervene on 28,000
students). If the institution wants a more selective alert, the 3:1
ratio (θ* ≈ 0.26) reduces the flagged rate to ~90%, and a higher ratio
(e.g., 1:1, not tested here) would reduce it further. The threshold
should be chosen operationally, not only mathematically. This is
documented as a design consideration for Step 7 (prototype).

## 4. Reproducibility

- results/shap_artifacts/{W2,W4,W6,W8}/{2013B,2013J,2014B,2014J}.jsonl
  — 16 files, 109,203 records total.
- results/tables/shap_importance.csv — 24 rows (6 features × 4 windows).
- results/tables/shap_flagged_counts.csv — 4 rows.
- results/figures/shap_importance_by_window.png.
- tests/test_shap_contract.py — 13 tests, all passed.
- Seed 42. Out-of-fold SHAP via TreeExplainer. Protocol version 1.0.15.

## 5. Limitation

The global importance is computed from the top-5 factors per side only.
For students with more than 5 contributing factors, the factors outside
the top-5 are aggregated in `other_factors_sum` and are not attributed
to individual features in the global analysis. This slightly
underestimates the importance of features that frequently fall just
outside the top-5. The effect is small (`other_factors_sum` is typically
much smaller than the top-5 sum) but should be noted when interpreting
the global ranking.