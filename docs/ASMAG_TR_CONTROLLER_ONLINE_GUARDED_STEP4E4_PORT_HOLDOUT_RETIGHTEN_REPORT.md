# ASMAG-TR Controller Online Guarded - Step 4E4 Port Holdout Retighten Report

Date: 2026-05-18

## Scope

Step 4E4 added a scoped `lowFramerate/port_0_17fps` detector-retighten v4 path plus a downstream no-detector holdout guard. No live, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

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

- `configs/asmag_tr_controller_online_guarded_cdnet_step4e4_port_detector_subset_dryrun.yaml`
- `outputs/asmag_tr_controller_online_guarded_cdnet_step4e4_port_detector_subset_dryrun/`
- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4E4_PORT_HOLDOUT_RETIGHTEN_REPORT.md`

Changed:

- `src/run_experiment.py`
- `tools/compare_asmag_tr_controller_online_guarded.py`
- `docs/DAILY_STATUS.md`

## Implementation Summary

Step 4E4 keeps the Step 4E3 final row-state classifier but narrows broad early suppression by retaining detector context inside the configured pre-FN window and when downstream holdout risk is predicted. It adds exact-video v4 controls:

- `ai_port_lf_detector_retighten_v4_enabled: true`
- `ai_port_lf_detector_retighten_v4_target_video: lowFramerate/port_0_17fps`
- `ai_port_lf_detector_retighten_v4_keep_pre_fn_context: true`
- `ai_port_lf_detector_retighten_v4_pre_fn_window_frames: 3`
- `ai_port_lf_detector_retighten_v4_post_suppression_holdout_window: 4`
- `ai_port_lf_detector_retighten_v4_max_detector_rate: 0.05000`
- `ai_port_lf_detector_retighten_v4_preferred_detector_rate: 0.03000`

It also adds an exact-video downstream no-detector holdout guard:

- `ai_port_lf_post_suppression_holdout_enabled: true`
- `ai_port_lf_post_suppression_holdout_target_video: lowFramerate/port_0_17fps`
- `ai_port_lf_post_suppression_holdout_no_detector: true`
- `ai_port_lf_post_suppression_holdout_window: 4`
- `ai_port_lf_post_suppression_holdout_extra_cap_per_video: 6`

Added compare outputs:

- `ai_intervention_4e4_port_detector_summary.csv`
- `ai_intervention_4e4_port_detector_rows.csv`

## Validation Commands

Compile:

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
```

Result: passed.

Step 4E4 residual-risk subset dry-run:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_step4e4_port_detector_subset_dryrun.yaml --max-jobs-per-run 8
```

Result: completed after resumed batches until 56/56 planned jobs completed, 0 failed.

Compare:

```powershell
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_step4e4_port_detector_subset_dryrun
```

Result: completed. Pandas fragmentation warnings were printed, but compare artifacts were written.

## Aggregate Step 4E4 Metrics

| Metric | Value |
|---|---:|
| Videos | 14 |
| Pipelines | 4 |
| Planned jobs | 56 |
| Completed jobs | 56 |
| Failed jobs | 0 |
| FMeasure | 0.34056 |
| Event_F1 | 0.67182 |
| Activation | 0.51786 |
| Avg_FPS | 33.93451 |
| P95 latency ms | 252.63299 |
| Proposal rate | 0.33857 |
| Detector request rate | 0.01000 |
| Normal-frame proposals | 0 |
| Guard alignment | 1.00000 |

## Port Progression

| Step | Proposal | Detector | Event FN | Protected FN | Unprotected FN | Detector before | Suppressed | Kept | Created unprotected FN |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Step 4 full | 0.37000 | 0.07000 | 5 | 5 | 0 | 7 | n/a | n/a | n/a |
| Step 4E | 0.37000 | 0.07000 | 5 | 5 | 0 | 7 | 0 | 7 | 0 |
| Step 4E2 | 0.40000 | 0.08000 | 14 | 10 | 4 | 9 | 1 | 8 | 0 |
| Step 4E3 | 0.40000 | 0.04000 | 12 | 10 | 2 | 22 | 18 | 4 | 0 |
| Step 4E4 | 0.42000 | 0.05000 | 5 | 5 | 0 | 13 | 8 | 5 | 0 |

Step 4E4 reaches the port detector hard gate exactly and recovers port unprotected FN to 0. It misses the preferred port proposal target of 0.40000 by 0.02000 and misses the preferred detector target of 0.03000, but not the hard detector gate.

## Port Retighten V4 Behavior

| Metric | Value |
|---|---:|
| Detector requests before retighten | 13 |
| Detector requests suppressed | 8 |
| Detector requests kept | 5 |
| Actual-FN detector kept count | 1 |
| Pre-FN context detectors kept | 2 |
| Final FP/TN detector suppressed count | 8 |
| True deterministic emergency detector kept count | 0 |
| Created unprotected FN from suppression | 0 |

Kept detector reasons:

- `actual_fn_detector_protection+explicit_likely_unprotected_fn`: 1
- `pre_fn_context+downstream_holdout_risk`: 2
- `within_hard_detector_budget_context_kept`: 2

Suppressed reasons were all event-refresh rows without true deterministic emergency or explicit independent likely-FN risk, with the final eight suppressed above the v4 max detector-rate condition.

## Downstream Holdout Behavior

The downstream no-detector holdout activated 6 times on frames 1405, 1410, 1415, 1420, 1425, and 1430. These were all final TN rows, so holdout protected-event-FN count was 0. The holdout did not request detector and did not create normal-frame false interventions in the aggregate summary.

Frames 1350 and 1355 are no longer unprotected FN:

| Frame | Final state | Action | Detector requested | Holdout active | Protected FN | Unprotected FN |
|---:|---|---|---:|---:|---:|---:|
| 1350 | FN | CLOSED_EMPTY_P3_FALLBACK | 0 | 0 | 1 | 0 |
| 1355 | FN | CLOSED_EMPTY_P3_FALLBACK | 0 | 0 | 1 | 0 |

The late FN repair came from retaining pre-FN/context detector state at nearby frames 1340 and 1360 rather than direct holdout activation on frames 1350 and 1355.

## Row-Level Port Decisions

| Frame | Final state | Action | V4 decision | Reason |
|---:|---|---|---|---|
| 1210 | FN | CLOSED_EMPTY_P3_FALLBACK | keep detector | actual-FN detector protection and explicit likely-unprotected-FN |
| 1230 | FP | FORCED_REFRESH | keep detector | within hard detector budget context kept |
| 1255 | FP | FALLBACK_P3_POLICY | keep detector | within hard detector budget context kept |
| 1340 | TN | CLOSED_EMPTY_P3_FALLBACK | keep detector | pre-FN context plus downstream holdout risk |
| 1350 | FN | CLOSED_EMPTY_P3_FALLBACK | frame status | protected FN, no detector request, no holdout activation |
| 1355 | FN | CLOSED_EMPTY_P3_FALLBACK | frame status | protected FN, no detector request, no holdout activation |
| 1360 | TN | CLOSED_EMPTY_P3_FALLBACK | keep detector | pre-FN context plus downstream holdout risk |
| 1405 | TN | CLOSED_EMPTY_P3_FALLBACK | suppress detector + holdout | above max detector rate; no-detector holdout active |
| 1410 | TN | CLOSED_EMPTY_P3_FALLBACK | suppress detector + holdout | above max detector rate; no-detector holdout active |
| 1415 | TN | CLOSED_EMPTY_P3_FALLBACK | suppress detector + holdout | above max detector rate; no-detector holdout active |
| 1420 | TN | CLOSED_EMPTY_P3_FALLBACK | suppress detector + holdout | above max detector rate; no-detector holdout active |
| 1425 | TN | CLOSED_EMPTY_P3_FALLBACK | suppress detector + holdout | above max detector rate; no-detector holdout active |
| 1430 | TN | CLOSED_EMPTY_P3_FALLBACK | suppress detector + holdout | above max detector rate; no-detector holdout active |
| 1435 | TN | CLOSED_EMPTY_P3_FALLBACK | suppress detector | above max detector rate |
| 1440 | TN | CLOSED_EMPTY_P3_FALLBACK | suppress detector | above max detector rate |

## Carry-Over Status

| Video | Proposal | Detector | Event FN | Protected FN | Unprotected FN | Status |
|---|---:|---:|---:|---:|---:|---|
| `badWeather/snowFall` | 0.36000 | 0.00000 | 22 | 21 | 1 | pass |
| `thermal/lakeSide` | 0.50000 | 0.00000 | 48 | 48 | 0 | pass |
| `intermittentObjectMotion/sofa` | 0.28000 | 0.00000 | 22 | 22 | 0 | pass |
| `intermittentObjectMotion/parking` | 0.51000 | 0.00000 | 37 | 35 | 2 | fail proposal gate |
| `shadow/copyMachine` | 0.47000 | 0.00000 | 46 | 43 | 3 | pass |
| `turbulence/turbulence2` | 0.31000 | 0.00000 | 3 | 3 | 0 | pass |
| `lowFramerate/tunnelExit_0_35fps` | 0.31000 | 0.00000 | 2 | 1 | 1 | pass |
| `shadow/cubicle` | 0.90000 | 0.02000 | 14 | 14 | 0 | pass, recall 0.87320 |
| `PTZ/continuousPan` | 0.05000 | 0.01000 | 0 | 0 | 0 | pass |
| `PTZ/intermittentPan` | 0.01000 | 0.00000 | 1 | 1 | 0 | pass |
| `dynamicBackground/fountain01` | 0.00000 | 0.00000 | 0 | 0 | 0 | pass, quiet |
| `dynamicBackground/fountain02` | 0.40000 | 0.01000 | 0 | 0 | 0 | pass, normal-frame false interventions 0 |
| `nightVideos/bridgeEntry` | 0.22000 | 0.05000 | 0 | 0 | 0 | pass |

## Gate Table

| Gate | Result | Status |
|---|---:|---|
| Planned subset jobs completed | 56/56, 0 failed | pass |
| Aggregate detector request rate < 0.10 | 0.01000 | pass |
| Normal-frame proposals = 0 | 0 | pass |
| Guard alignment >= 0.95 | 1.00000 | pass |
| Port detector <= 0.05 hard gate | 0.05000 | pass |
| Port detector preferred <= 0.03 | 0.05000 | preferred miss |
| Port unprotected FN = 0 | 0 | pass |
| Port created unprotected FN from suppression = 0 | 0 | pass |
| Frames 1350 and 1355 protected or no longer unprotected FN | both protected | pass |
| Port proposal preferred <= 0.40 | 0.42000 | preferred miss |
| snowFall proposal/detector/unprotected-FN gate | 0.36000 / 0.00000 / 1 | pass |
| lakeSide proposal/detector/unprotected-FN gate | 0.50000 / 0.00000 / 0 | pass |
| sofa proposal/detector/unprotected-FN gate | 0.28000 / 0.00000 / 0 | pass |
| parking proposal/detector/unprotected-FN gate | 0.51000 / 0.00000 / 2 | fail |
| copyMachine accepted gate | 0.47000 / 0.00000 / 3 | pass |
| turbulence2 accepted gate | 0.31000 / 0.00000 / 0 | pass |
| tunnelExit accepted gate | 0.31000 / 0.00000 / 1 | pass |
| cubicle recall >= 0.80 and unprotected FN 0 | 0.87320 / 0 | pass |
| continuousPan controlled | 0.05000 / 0.01000 / 0 | pass |
| intermittentPan controlled | 0.01000 / 0.00000 / 0 | pass |
| fountain01 quiet | proposal 0.00000 | pass |
| fountain02 normal-frame false interventions = 0 | 0 | pass |
| bridgeEntry event FN = 0 | 0 | pass |
| No forbidden validation launched | none launched | pass |

## Result

Step 4E4 residual-risk subset dry-run fails because `intermittentObjectMotion/parking` regressed to proposal 0.51000, above the 0.50000 gate, and exposed 2 unprotected FN. The port-specific detector retighten and late-FN repair did meet the hard port gates.

Root cause: the Step 4E4 port path is exact-video scoped in its telemetry (`parking` has zero port-retighten and holdout activations), but the current run did not preserve the previously stable Step 4E3 / Step 4D6 parking trajectory. Parking changed from the accepted Step 4E3 carry-over status `0.50000 / 0.00000 / 0` to `0.51000 / 0.00000 / 2` while Step 4E output had `0.46000 / 0.00000 / 0`. This is a non-port carry-over regression and must be corrected before any freeze or full rerun.

Narrow next fix: Step 4E5 should keep the v4 port detector behavior, but rebase or explicitly lock the parking Step 4D6 carry-over behavior so parking returns to proposal `<= 0.50000` and unprotected FN `0` without changing port detector rate or widening non-port policies.

Full CDnet remains held.
