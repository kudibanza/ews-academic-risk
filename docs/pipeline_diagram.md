┌─────────────────────────────────────────────────────────────────────┐
│ RAW DATA  (data/raw/)                                               │
│   studentInfo.csv  studentRegistration.csv  studentVle.csv          │
│   vle.csv  studentAssessment.csv  assessments.csv  courses.csv      │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│ STEP 1 — AUDIT (report-only)                        [DONE]          │
│   checksums.py (SHA-256)  →  audit_schema.py  →  pytest 16/16       │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│ STEP 2.1 — CLEANING + EXCLUSION                     [DONE]          │
│   dates → Int64                                                     │
│   exclude if date_unregistration <= cutoff_k (§4)                   │
│   → eligibility_W{2,4,6,8}.parquet                                  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│ STEP 2.2 — FEATURES (Rule 3: date <= cutoff)        [DONE]          │
│   S_vle  D_active  H_entropy  Delta_t  S_score                      │
│   click_trend  still_registered=1                                   │
│   → features_W{2,4,6,8}.parquet                                     │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│ STEP 2.3 — LEAKAGE ASSERTS                          [DONE]          │
│   R3 (temporal) ✓   R4 (student group) ✓                            │
│   R1, R2 skipped until Step 3                                       │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│ STEP 3.1 — PIPELINE (Rule 1: fit on train fold)     [DONE]          │
│   Imputer(median) → [Scaler] → Classifier                           │
│   R1 ✓  R2 ✓  (pytest 8/8)                                          │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│ STEP 3.2 — BENCHMARK (RQ2)                          [CURRENT]       │
│   GroupKFold(5) by student_id                                       │
│   logreg · dtree · rf · xgboost · lightgbm                          │
│   W2: Variant A (7 feats) and B (5 feats)                           │
│   metrics: PR-AUC, Recall, F2, Precision, ROC-AUC                   │
│   → benchmark_results.csv  benchmark_summary.csv                    │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│ FUTURE                                              [PLANNED]       │
│   Step 4 — imbalance + cost-sensitive threshold (RQ3)               │
│   Step 5 — SHAP caching (RQ4)                                       │
│   Step 6 — cross-cohort 2013→2014                                   │
│   Step 7 — web prototype + SCS validation (RQ5)                     │
└─────────────────────────────────────────────────────────────────────┘