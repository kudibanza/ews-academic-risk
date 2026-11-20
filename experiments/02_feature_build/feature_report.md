# Feature Report — Sub-step 2.2

Cumulative features per protocol.yaml §5 (v1.0.5).
Only eligible students. Only date <= cutoff_k (Rule 3).

## W2 (cutoff=14 days)
- Rows: **28,119**
- Null counts per feature:
  - `S_vle`: 1,691
  - `D_active`: 1,691
  - `H_entropy`: 1,691
  - `Delta_t`: 26,933
  - `S_score`: 26,934
  - `click_trend`: 2,787
- `still_registered` unique values: [1]
- Output: `data/processed/features_W2.parquet`

## W4 (cutoff=28 days)
- Rows: **27,538**
- Null counts per feature:
  - `S_vle`: 921
  - `D_active`: 921
  - `H_entropy`: 921
  - `Delta_t`: 6,868
  - `S_score`: 6,887
  - `click_trend`: 1,273
- `still_registered` unique values: [1]
- Output: `data/processed/features_W4.parquet`

## W6 (cutoff=42 days)
- Rows: **27,024**
- Null counts per feature:
  - `S_vle`: 717
  - `D_active`: 717
  - `H_entropy`: 717
  - `Delta_t`: 4,236
  - `S_score`: 4,254
  - `click_trend`: 1,756
- `still_registered` unique values: [1]
- Output: `data/processed/features_W6.parquet`

## W8 (cutoff=56 days)
- Rows: **26,522**
- Null counts per feature:
  - `S_vle`: 603
  - `D_active`: 603
  - `H_entropy`: 603
  - `Delta_t`: 3,994
  - `S_score`: 4,006
  - `click_trend`: 2,278
- `still_registered` unique values: [1]
- Output: `data/processed/features_W8.parquet`

## Coverage note on assessment features

In W2 (cutoff=14), only ONE assessment in the entire OULAD has a deadline
on or before day 14 (id_assessment=15008, module BBB, presentation 2014B,
deadline day 12). Consequently:
- Delta_t and S_score have ~4% coverage in W2 (1,186 of 28,119 students).
- In W4, coverage rises to 75% (20,670 of 27,538).
- From W4 onward, assessment features become informative.

Implication for Step 3: W2 models will rely almost exclusively on VLE
features (S_vle, D_active, H_entropy, click_trend). Whether to retain
Delta_t and S_score in W2 (with imputation) or drop them is a decision
for Step 3, based on benchmark results, and must be documented there.

# Leakage Report — Sub-step 2.3

Zero-leakage asserts for protocol.yaml §6 (Rules R1–R4).
Executed with `pytest tests/test_leakage.py -v`.

## Result

- Passed: 6
- Skipped: 2 (R1, R2 — require the CV pipeline, Step 3)
- Failed: 0

## R3 — Temporal boundary integrity (testable, all passed)

| Test | What it verifies | Result |
|---|---|---|
| `test_r3_monotonic_cumulative_features` | S_vle and D_active are non-decreasing across W2→W4→W6→W8 for each student-module-presentation. A decrease would indicate future data leaked into an earlier window. | PASSED |
| `test_r3_no_future_activity_in_w2` | For W2 rows, S_vle recomputed from raw studentVle using only date <= 14 matches the stored value. Detects accidental inclusion of future activity. | PASSED |
| `test_r3_entropy_bounds` | H_entropy lies in [0, log2(20)] ≈ [0, 4.3219] for all windows. | PASSED |

## R4 — Student-level group isolation (testable now, all passed)

| Test | What it verifies | Result |
|---|---|---|
| `test_r4_no_duplicate_keys_within_window` | Each (id_student, code_module, code_presentation) appears at most once per window. | PASSED |
| `test_r4_eligibility_matches_features` | The set of keys in features_Wk equals the set of eligible keys in eligibility_Wk. No ineligible student received features; no eligible student was silently dropped. | PASSED |
| `test_r4_overlap_students_exist` | 25,247 students have 1 row; 3,538 students have >1 row; 3,808 is the number of excess rows. Overlapping students remain present in every window. | PASSED |

Note: the previous version of `test_r4_overlap_students_exist` failed because it
conflated overlap_rows (3,808) with overlap_students (3,538). The distinction
is now verified explicitly and documented in protocol.yaml §1.

## R1 and R2 — Deferred to Step 3

- **R1 (preprocessing isolation):** will test that imputers and scalers are
  fit only on the training fold of each CV split. Requires the CV pipeline.
- **R2 (resampling boundary):** will test that SMOTE/ADASYN/Tomek are applied
  only to the training fold after the split. Requires the CV pipeline.

Both are marked `@pytest.mark.skip` with the reason documented. They will be
implemented in Step 3 and the skip removed.

## Files

- `tests/test_leakage.py` — all six active tests plus two skipped stubs.
- Raw data untouched; processed files unchanged by this sub-step.