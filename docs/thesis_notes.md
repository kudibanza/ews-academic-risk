# Thesis Notes — ready-to-paste material

This file collects passages that are already written and can be pasted
into the thesis, with pointers to where each decision was made. It is
the single source for thesis writing; reports are the evidence, this
file is the prose.

**Last updated:** 2026-11-16 (protocol v1.0.19)

---

## Table of contents

1. Future work
2. Limitations
3. Design decisions
4. Data and methodology
5. Results
6. Technical notes

---

## 1. Future work

### 1.1 Step 3b — Hyperparameter tuning (deferred)

Hyperparameter tuning (Step 3b) was identified in the protocol but deferred.
The benchmark in Step 3 used default hyperparameters, which is the
pre-registered protocol and ensures reproducibility and comparability with
the literature. A future iteration could apply RandomSearch or Bayesian
optimisation to the selected LightGBM configuration, but this would require
re-running the imbalance benchmark (4.1), threshold tuning (4.3), and SHAP
generation (5.1) if the optimal hyperparameters change the winning imbalance
strategy or the feature attributions. Given the time constraints of the
master's programme, this was left as future work.

**Source:** protocol.yaml §15 change_log v1.0.19; discussed 2026-11-16.

---

## 2. Limitations

### 2.1 ADASYN failure in W2

ADASYN failed to generate synthetic samples in W2 across all three models
(5/5 folds skipped). This is consistent with documented behaviour of ADASYN
when the minority class is too small to satisfy its nearest-neighbour
requirement [58], and with recent evidence that synthetic oversampling,
including ADASYN, can lower performance when at-risk students are scattered
within the majority class [57]. In our setting, the combination of
operational exclusion (§4) and the low coverage of assessment features in
W2 leaves the minority class too small for ADASYN to operate. The failure is
documented rather than corrected, as it reflects a genuine limitation of the
method in this early-window context. Notably, cost-sensitive weighting
(class_weight), which does not require synthetic samples, performed best
overall (Section 4.1 of imbalance_report.md).

**Source:** imbalance_report.md; refs [57] and [58].

### 2.2 W2 cross-cohort — assessment features absent in 2013

In W2, `Delta_t` and `S_score` have no observed values in the 2013 training
set (only one assessment in all OULAD is due by day 14, `id_assessment=15008`,
and it belongs to presentation 2014B). The W2 cross-cohort model is therefore
VLE-only; the W4–W8 gaps are the cleaner estimate of cohort shift.

**Source:** cross_cohort_report.md §4; feature_report.md.

### 2.3 SHAP global importance uses top-5 factors only

The global importance is computed from the top-5 factors per side only. For
students with more than 5 contributing factors, the factors outside the top-5
are aggregated in `other_factors_sum` and are not attributed to individual
features in the global analysis. This slightly underestimates the importance
of features that frequently fall just outside the top-5.

**Source:** shap_report.md §5.

### 2.4 `still_registered` excluded from model

The `still_registered` flag is computed per §5 but is excluded from the model
feature set. After operational exclusion (§4), every eligible student is by
definition still registered at the cutoff, so the flag takes the constant
value 1 and carries no variance. It is retained in the processed datasets for
auditability but is not used as a predictor.

**Source:** src/models/pipeline.py; protocol.yaml §5.

---

## 3. Design decisions

### 3.1 Calibration rejected

LightGBM is already well calibrated (ECE ≈ 0.018–0.056). Platt and isotonic
both degrade ECE and Brier. Calibration was tested and rejected; threshold
tuning compensates for XGBoost's compressed probabilities.

**Source:** calibration_report.md; imbalance_report.md §4.3.

### 3.2 Operational implication of 99.5% flagged in W2

At the 5:1 cost ratio, θ* is very low (0.116–0.172), so almost all students
are flagged in W2 (99.5%). This is mathematically correct for the cost
function but not actionable for advisors. The 3:1 ratio (θ* ≈ 0.26) reduces
the flagged rate to ~90%.

**Source:** shap_report.md §3.

---

## 4. Data and methodology

### 4.1 Unique students vs. student-module-presentation rows

The OULAD contains 32,593 student-module-presentation rows but only 28,785
unique students; 3,538 students appear in more than one module presentation
(overlap_rows = 3,808 is the number of excess rows, not the number of
students). This overlap is why all cross-validation folds are constructed at
the student level (Rule 4): a naive random split would place the same student
in both train and test, inflating reported performance. Zhang & Duan (2026)
show this empirically on the same dataset.

**Source:** protocol.yaml §1 audit_notes; cleaning_report.md.

### 4.2 Operational exclusion depends only on `date_unregistration`

A student is excluded at window k if and only if
`date_unregistration.notna() AND date_unregistration <= cutoff_k`. The rule
never depends on `date_registration`. This matters because 45 students have a
null `date_registration` but a non-null `date_unregistration`; requiring
`date_registration.notna()` would silently retain students who had already
left, creating a leakage pathway.

**Source:** protocol.yaml §4 and §4.1; cleaning_report.md.

---

## 5. Results

### 5.1 Signal migration across windows (RQ4)

The global SHAP analysis shows a clear migration of predictive signal across
windows. In W2, `S_vle` dominates (mean |SHAP| 0.471), reflecting that only
clickstream volume is available before assessments begin. By W8, `S_score`
dominates (0.661) and `D_active` is second (0.437). `Delta_t` rises from 0.013
(W2) to 0.263 (W8), mirroring the coverage jump from ~4% to 75%. `click_trend`,
added as an engagement-trajectory feature, contributes 0.117–0.236. This
confirms the proposal's hypothesis that the predictive signal shifts from VLE
behaviour to academic performance as the semester progresses.

**Source:** shap_report.md §2; results/figures/shap_importance_by_window.png.

### 5.2 Cross-cohort generalization gap

Cross-cohort evaluation (train 2013, test 2014, no retraining, no threshold
recalibration) shows a PR-AUC drop of 0.05–0.10 relative to GroupKFold
(W2: 0.619→0.570; W4: 0.694→0.604; W6: 0.715→0.620; W8: 0.745→0.646).
Recall is essentially unchanged (0.956–0.998), showing that the
cost-sensitive threshold optimized on 2013 generalizes to 2014 without
recalibration. The gap is consistent with Zhang & Duan (2026), who report a
0.019–0.040 AUC penalty on the same dataset.

**Source:** cross_cohort_report.md §3.

### 5.3 Threshold tuning effectiveness (RQ3)

At the primary 5:1 cost ratio, threshold tuning raises recall from
0.617–0.675 (at threshold 0.5) to 0.969–0.998 (at θ*), and F2 from
0.610–0.672 to 0.796–0.805, while roughly halving the expected cost. XGBoost
requires lower thresholds than LightGBM, compensating for its compressed
probability scale; at θ*, the two models converge on operational cost
(0.9–2.4% difference).

**Source:** imbalance_report.md §4.3.

---

## 6. Technical notes

### 6.1 SHAP values in log-odds

SHAP values are expressed in log-odds (the model's native output space). The
probability reported as `risk_score` is obtained as
`sigmoid(base_value + sum(top5) + other_factors_sum)`. The `other_factors_sum`
field captures the SHAP values outside the top-5 lists, making the
reconstruction exact (tolerance 1e-6, verified in sub-step 5.2). Without it,
the residual was up to ~1.1 percentage points for students with many
contributing factors.

**Source:** shap_report.md §1; tests/test_shap_contract.py.

### 6.2 Class weighting for XGBoost uses numeric scale_pos_weight

XGBoost does not accept `class_weight="balanced"` (unlike LightGBM and
LogisticRegression). The equivalent is a numeric `scale_pos_weight =
n_negative / n_positive`, computed from the training fold only (Rule 1). For
resampling strategies (SMOTE, ADASYN, Tomek), `scale_pos_weight` is left at
1.0 to avoid double correction.

**Source:** src/imbalance/benchmark.py; src/imbalance/threshold.py.

---

## Cross-references

| Topic | Source file |
|---|---|
| Protocol contract | config/protocol.yaml |
| Data audit | experiments/01_data_audit/audit_report.md |
| Cleaning + exclusion | experiments/02_feature_build/cleaning_report.md |
| Features | experiments/02_feature_build/feature_report.md |
| Leakage asserts | experiments/02_feature_build/leakage_report.md |
| Benchmark | experiments/03_model_benchmark/benchmark_report.md |
| Imbalance + calibration + threshold | experiments/04_imbalance_cost/imbalance_report.md |
| SHAP | experiments/05_shap/shap_report.md |
| Cross-cohort | experiments/06_cross_cohort/cross_cohort_report.md |
| References [57][58] | imbalance_report.md (end) |


### The SCS Evaluation and Prototype Limitations

The prototype was evaluated using the SCS with [N] academic coordinators.
The average SCS score was [X.XX], indicating that the SHAP-based risk cards
were perceived as [highly/moderately] actionable. Key qualitative feedback
included [insert feedback, e.g., the usefulness of the feature values].

**Limitations of the prototype:** The web app served a stratified sample of
2,000 students, not the full 109,000 artifacts, to ensure fast local
performance. The architecture (FastAPI + React + PostgreSQL) is
production-ready, but the authentication is local and the ML inference is
pre-computed, which are acceptable trade-offs for a proof-of-concept
validation vehicle.

**Source:** experiments/07_webapp/webapp_report.md and scs_protocol.md.