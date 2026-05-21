# ASMAG-TR Controller Online Guarded - Step 4E3 Port Row-State Detector Retighten Report

Date: 2026-05-18

## Scope

Step 4E3 rebased the residual-risk subset from the known stable Step 4E / Step 4D6 stack and added only a guarded `lowFramerate/port_0_17fps` detector-retighten v3 path. No live, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

Planned subset:

1. `thermal/lakeSide`
2. `intermittentObjectMotion/sofa`
3. `badWeather/snowFall`
4. `lowFramerate/port_0_17fps`
5. `intermittentObjectMotion/parking`
6. `shadow/copyMachine`
7. `turbulence/turbulence2`
8. `lowFramerate/tunnelExit_0_35fps`
9. `shadow/cubicle`
10. `PTZ/continuousPan`
11. `PTZ/intermittentPan`
12. `dynamicBackground/fountain01`
13. `dynamicBackground/fountain02`
14. `nightVideos/bridgeEntry`

## Files

Created:

- `configs/asmag_tr_controller_online_guarded_cdnet_step4e3_port_detector_subset_dryrun.yaml`
- `outputs/asmag_tr_controller_online_guarded_cdnet_step4e3_port_detector_subset_dryrun/`
- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4E3_PORT_ROWSTATE_RETIGHTEN_REPORT.md`

Changed:

- `src/run_experiment.py`
- `tools/compare_asmag_tr_controller_online_guarded.py`
- `docs/DAILY_STATUS.md`

## Implementation Summary

Step 4E3 added a v3-only port retighten path gated by:

- `ai_port_lf_detector_retighten_v3_enabled: true`
- `ai_port_lf_detector_retighten_v3_target_video: lowFramerate/port_0_17fps`
- final row-state classification for detector-refresh rows
- suppression of final FP/TN event-refresh detector requests when no explicit true emergency or explicit independent likely-unprotected-FN marker exists
- no-detector fallback logging through `existing_lowframerate_fallback_or_sanitizer`

Generic `detector_refresh_needed_for_event` and generic event/foreground pressure are not treated as true deterministic emergency or explicit likely-FN risk in v3.

Added row-level logs:

- `ai_port_lf_detector_retighten_v3_active`
- `ai_port_lf_detector_retighten_v3_decision_time_event_state`
- `ai_port_lf_detector_retighten_v3_final_event_state`
- `ai_port_lf_detector_retighten_v3_suppressed_detector`
- `ai_port_lf_detector_retighten_v3_kept_detector`
- `ai_port_lf_detector_retighten_v3_kept_detector_reason`
- `ai_port_lf_detector_retighten_v3_suppressed_reason`
- `ai_port_lf_detector_retighten_v3_generic_refresh_not_emergency`
- `ai_port_lf_detector_retighten_v3_generic_event_fg_not_likely_fn`
- `ai_port_lf_detector_retighten_v3_true_emergency`
- `ai_port_lf_detector_retighten_v3_explicit_likely_unprotected_fn`
- `ai_port_lf_detector_retighten_v3_no_detector_fallback`
- `ai_port_lf_detector_retighten_v3_created_unprotected_fn`
- `ai_port_lf_detector_retighten_v3_protected_fn_detector_kept`

Added compare outputs:

- `ai_intervention_4e3_port_detector_summary.csv`
- `ai_intervention_4e3_port_detector_rows.csv`

## Validation Commands

Compile:

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
```

Result: passed.

Step 4E3 residual-risk subset dry-run:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_step4e3_port_detector_subset_dryrun.yaml --max-jobs-per-run 8
```

Result: completed after resumed batches until 56/56 planned jobs completed, 0 failed.

Compare:

```powershell
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_step4e3_port_detector_subset_dryrun
```

Result: completed. Pandas fragmentation warnings were printed, but compare artifacts were written.

## Aggregate Step 4E3 Metrics

| Metric | Value |
|---|---:|
| Videos | 14 |
| Pipelines | 4 |
| Planned jobs | 56 |
| Completed jobs | 56 |
| Failed jobs | 0 |
| FMeasure | 0.33590 |
| Event_F1 | 0.66315 |
| Activation | 0.49143 |
| Avg_FPS | 23.58319 |
| P95 latency ms | 318.10496 |
| Proposal rate | 0.33286 |
| Detector request rate | 0.01357 |
| Normal-frame proposals | 0 |
| Guard alignment | 1.00000 |

## Port Progression

| Step | Proposal | Detector | Event FN | Protected FN | Unprotected FN | Detector before | Suppressed | Kept | Created unprotected FN |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Step 4 full | 0.37000 | 0.07000 | 5 | 5 | 0 | 7 | n/a | n/a | n/a |
| Step 4E | 0.37000 | 0.07000 | 5 | 5 | 0 | 7 | 0 | 7 | 0 |
| Step 4E2 | 0.40000 | 0.08000 | 14 | 10 | 4 | 9 | 1 | 8 | 0 |
| Step 4E3 | 0.40000 | 0.04000 | 12 | 10 | 2 | 22 | 18 | 4 | 0 |

Step 4E3 materially reduced port detector requests below the hard 0.05 ceiling, but failed the port unprotected-FN gate because two later FN frames became unprotected.

## Port Retighten V3 Behavior

| Metric | Value |
|---|---:|
| Detector requests before retighten | 22 |
| Detector requests suppressed | 18 |
| Detector requests kept | 4 |
| Actual-FN detector kept count | 3 |
| Final FP/TN detector suppressed count | 18 |
| True deterministic emergency detector kept count | 0 |
| Generic refresh suppressed count | 1 |
| No-detector fallback frames | 18 |
| Created unprotected FN from suppression | 0 |

Kept detector reasons:

- `actual_fn_detector_protection+explicit_likely_unprotected_fn`: 3
- `detector_preserved_by_port_retighten_v3_safety`: 1

Suppressed final FP/TN detector-refresh rows were classified using final row state and did not use generic event-refresh safety as deterministic emergency.

## Row-Level Port Detector Decisions

| Frame | Final state | Action | V3 decision | Reason |
|---:|---|---|---|---|
| 1020 | TN | CLOSED_EMPTY_ACC | suppress | final FP/TN event-refresh, no explicit likely FN, no true emergency |
| 1025 | FP | REUSE_P3_FALLBACK | suppress | final FP/TN event-refresh, no explicit likely FN, no true emergency |
| 1030 | FP | REUSE_P3_FALLBACK | suppress | final FP/TN event-refresh, no explicit likely FN, no true emergency |
| 1035 | TN | CLOSED_EMPTY_P3_FALLBACK | suppress | final FP/TN event-refresh, no explicit likely FN, no true emergency |
| 1040 | TN | CLOSED_EMPTY_P3_FALLBACK | suppress | final FP/TN event-refresh, no explicit likely FN, no true emergency |
| 1045 | TN | CLOSED_EMPTY_P3_FALLBACK | suppress | final FP/TN event-refresh, no explicit likely FN, no true emergency |
| 1050 | FP | LIGHTWEIGHT_MASK_P3_FALLBACK | suppress | final FP/TN event-refresh, no explicit likely FN, no true emergency |
| 1055 | TN | CLOSED_EMPTY_P3_FALLBACK | suppress | final FP/TN event-refresh, no explicit likely FN, no true emergency |
| 1060 | TN | CLOSED_EMPTY_P3_FALLBACK | suppress | final FP/TN event-refresh, no explicit likely FN, no true emergency |
| 1065 | TN | CLOSED_EMPTY_P3_FALLBACK | suppress | final FP/TN event-refresh, no explicit likely FN, no true emergency |
| 1070 | FP | FALLBACK_P3_POLICY | suppress | generic refresh not emergency, final FP/TN, no explicit likely FN |
| 1130 | TN | CLOSED_EMPTY_P3_FALLBACK | suppress | final FP/TN event-refresh, no explicit likely FN, no true emergency |
| 1135 | TP | REUSE_P3_FALLBACK | keep | preserved by v3 safety |
| 1155 | FN | CLOSED_EMPTY_P3_FALLBACK | keep | actual-FN detector protection and explicit likely unprotected FN |
| 1175 | FN | CLOSED_EMPTY_P3_FALLBACK | keep | actual-FN detector protection and explicit likely unprotected FN |
| 1215 | TN | CLOSED_EMPTY_P3_FALLBACK | suppress | final FP/TN event-refresh, above max detector rate |
| 1220 | TN | CLOSED_EMPTY_P3_FALLBACK | suppress | final FP/TN event-refresh, above max detector rate |
| 1225 | FP | REUSE_P3_FALLBACK | suppress | final FP/TN event-refresh, above max detector rate |
| 1230 | TN | CLOSED_EMPTY_P3_FALLBACK | suppress | final FP/TN event-refresh, above max detector rate |
| 1235 | TN | CLOSED_EMPTY_P3_FALLBACK | suppress | final FP/TN event-refresh, above max detector rate |
| 1240 | TN | CLOSED_EMPTY_P3_FALLBACK | suppress | final FP/TN event-refresh, above max detector rate |
| 1245 | FN | CLOSED_EMPTY_P3_FALLBACK | keep | actual-FN detector protection and explicit likely unprotected FN |

All suppressed rows logged `ai_port_lf_detector_retighten_v3_created_unprotected_fn = 0`. The suppressed-row source column is blank after suppression because the detector request source is cleared by the final no-detector decision; the v3 suppressed reason still records the original event-refresh classification.

The remaining port unprotected FN rows are frames 1350 and 1355. Both have `ai_port_lf_detector_retighten_v3_active = 0` and `ai_detector_requested = 0`, so they were not direct v3-suppressed detector rows. The Step 4E3 failure is therefore an indirect trajectory/protection failure, not a counted created-unprotected-FN-from-suppression row.

## Carry-Over Status

| Video | Proposal | Detector | Event FN | Protected FN | Unprotected FN | Gate |
|---|---:|---:|---:|---:|---:|---|
| `badWeather/snowFall` | 0.36000 | 0.00000 | 22 | 21 | 1 | PASS |
| `thermal/lakeSide` | 0.50000 | 0.00000 | 48 | 48 | 0 | PASS |
| `intermittentObjectMotion/sofa` | 0.27000 | 0.00000 | 21 | 21 | 0 | PASS |
| `intermittentObjectMotion/parking` | 0.50000 | 0.00000 | 33 | 33 | 0 | PASS |
| `shadow/copyMachine` | 0.46000 | 0.00000 | 46 | 42 | 4 | PASS |
| `turbulence/turbulence2` | 0.31000 | 0.00000 | 3 | 3 | 0 | PASS |
| `lowFramerate/tunnelExit_0_35fps` | 0.31000 | 0.00000 | 2 | 1 | 1 | PASS watch |
| `shadow/cubicle` | 0.90000 | 0.02000 | 14 | 14 | 0 | PASS, recall 0.87408 |
| `PTZ/continuousPan` | 0.05000 | 0.01000 | 0 | 0 | 0 | PASS |
| `PTZ/intermittentPan` | 0.01000 | 0.00000 | 1 | 1 | 0 | PASS |
| `dynamicBackground/fountain01` | 0.00000 | 0.00000 | 0 | 0 | 0 | PASS |
| `dynamicBackground/fountain02` | 0.40000 | 0.08000 | 1 | 1 | 0 | PASS, normal-frame false interventions 0 |
| `nightVideos/bridgeEntry` | 0.19000 | 0.04000 | 0 | 0 | 0 | PASS |

The Step 4E2 carry-over regressions were removed by rebasing from the stable Step 4E / Step 4D6 stack.

## Gate Table

| Gate | Result | Status |
|---|---:|---|
| All planned jobs completed, 0 failed | 56/56, 0 failed | PASS |
| Aggregate detector request rate < 0.10 | 0.01357 | PASS |
| Normal-frame proposals = 0 | 0 | PASS |
| Guard alignment >= 0.95 | 1.00000 | PASS |
| Port detector request <= 0.03 preferred, hard fail if > 0.05 | 0.04000 | WARN, hard PASS |
| Port unprotected FN = 0 | 2 | FAIL |
| Port created unprotected FN from detector suppression = 0 | 0 | PASS |
| Suppress at least 4 final FP/TN detector-refresh rows, preferred >= 5 | 18 | PASS |
| Actual-FN detector-protecting rows kept or safely replaced without unprotected FN | 3 kept, but port unprotected FN 2 | FAIL |
| Port proposal controlled, preferred <= 0.40 | 0.40000 | PASS |
| snowFall proposal <= 0.45, detector <= 0.03, unprotected FN <= 6 | 0.36000 / 0.00000 / 1 | PASS |
| lakeSide proposal <= 0.50, detector <= 0.02, unprotected FN <= 12 | 0.50000 / 0.00000 / 0 | PASS |
| sofa proposal <= 0.35 preferred, detector <= 0.03, unprotected FN <= 6 | 0.27000 / 0.00000 / 0 | PASS |
| parking proposal <= 0.50, detector <= 0.02, unprotected FN <= 12 | 0.50000 / 0.00000 / 0 | PASS |
| copyMachine accepted gate | 0.46000 / 0.00000 / 4 | PASS |
| turbulence2 accepted gate | 0.31000 / 0.00000 / 0 | PASS |
| tunnelExit accepted gate | 0.31000 / 0.00000 / 1 | PASS watch |
| cubicle recall >= 0.80 and unprotected FN 0 | 0.87408 / 0 | PASS |
| continuousPan controlled | 0.05000 / 0.01000 / 0 | PASS |
| intermittentPan controlled | 0.01000 / 0.00000 / 0 | PASS |
| fountain01 quiet | 0.00000 / 0.00000 / 0 | PASS |
| fountain02 normal-frame false interventions = 0 | 0 | PASS |
| bridgeEntry event FN = 0 | 0 | PASS |
| No forbidden validation launched | none launched | PASS |

## Result

Step 4E3 residual-risk subset dry-run fails because `lowFramerate/port_0_17fps` has 2 unprotected FN frames. Full CDnet remains held.

## Root Cause And Narrow Next Fix

The final-row-state classifier corrected the Step 4E2 problem of retaining final TN/FP generic refresh rows, and it reduced port detector request rate from 0.08000 in Step 4E2 to 0.04000. However, v3 expanded the audited event-refresh detector surface to 22 rows and suppressed 18 final FP/TN rows. That suppression did not directly create an unprotected FN in the audited rows, but it changed the downstream port trajectory so frames 1350 and 1355 became unprotected FN with v3 inactive.

Recommended narrow Step 4E4:

- constrain v3 to the intended Step 4E audited detector-refresh surface, or add a two-pass downstream holdout guard for port;
- keep final-FN detector protection;
- suppress final FP/TN only when the frame is in the intended audit surface and no explicit true emergency or independent explicit likely-FN marker exists;
- add a downstream safety check for frames that would become unprotected after earlier detector suppression;
- keep full CDnet held until the residual subset passes with port unprotected FN 0.
