# ASMAG-TRC Step 4E2 Port Detector Retighten Report

Date: 2026-05-18

## Executive Summary

Step 4E2 added a separate `lowFramerate/port_0_17fps` detector-retighten v2 path and ran the 14-video residual-risk subset dry-run only.

The run completed technically, but Step 4E2 **does not pass**. The port detector gate still fails and several carry-over gates regressed, so full CDnet remains held.

No live, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

## Files And Outputs

- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_step4e2_port_detector_subset_dryrun.yaml`
- Created output root: `outputs/asmag_tr_controller_online_guarded_cdnet_step4e2_port_detector_subset_dryrun/`
- Updated implementation: `src/run_experiment.py`
- Updated compare/reporting: `tools/compare_asmag_tr_controller_online_guarded.py`
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4E2_PORT_DETECTOR_RETIGHTEN_REPORT.md`
- Updated status: `docs/DAILY_STATUS.md`

Compile passed:

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
```

Compare passed:

```powershell
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_step4e2_port_detector_subset_dryrun
```

## Planned Subset Scope

The Step 4E2 dry-run used the requested 14-video residual-risk subset:

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

The run completed `56/56` planned jobs with `0` failed jobs.

## Aggregate Result

| Metric | Step 4E2 |
|---|---:|
| Planned jobs | 56 |
| Completed jobs | 56 |
| Failed jobs | 0 |
| FMeasure | 0.28116 |
| Event_F1 | 0.59756 |
| Activation | 0.31429 |
| Avg_FPS | 20.92067 |
| P95 latency ms | 412.66461 |
| Proposed intervention rate | 0.36071 |
| Detector request rate | 0.01643 |
| Normal-frame proposals | 0 |
| Guard alignment | 1.00000 |

## Port Step 4 Full Vs Step 4E Vs Step 4E2

| Metric | Step 4 full audit baseline | Step 4E | Step 4E2 |
|---|---:|---:|---:|
| Proposal rate | 0.37000 | 0.37000 | 0.40000 |
| Detector request rate | 0.07000 | 0.07000 | 0.08000 |
| Event FN | 5 | 5 | 14 |
| Protected event FN | 5 | 5 | 10 |
| Unprotected event FN | 0 | 0 | 4 |
| Detector-request frames before retighten | 7 | 7 | 9 |
| Detector requests suppressed | n/a | 0 | 1 |
| Detector requests kept | n/a | 7 | 8 |
| Actual-FN detector kept count | 1 | 1 | 3 |
| True deterministic emergency detector kept count | n/a | 1 labeled | 0 |
| Created unprotected FN from suppression | n/a | 0 | 0 |

## Port Detector Retighten V2 Behavior

The v2 hook was active only for `lowFramerate/port_0_17fps`, but it did not reproduce the intended Step 4E seven-row audit surface. It saw 9 event-refresh detector frames and suppressed only 1 FP/TN detector request.

V2 correctly avoided creating an unprotected FN from detector suppression, but the detector gate still fails because detector rate increased to `0.08000` and unprotected FN regressed to `4`.

| Counter | Step 4E2 |
|---|---:|
| Detector requests before retighten | 9 |
| Detector requests suppressed | 1 |
| Detector requests kept | 8 |
| Actual-FN detector kept | 3 |
| True deterministic emergency detector kept | 0 |
| Generic refresh suppressed | 0 |
| FP/TN detector suppressed | 1 |
| No-detector fallback rows | 1 |
| Created unprotected FN from suppression | 0 |

## Row-Level Port Audit

| Frame | State | Action | Decision | Reason |
|---:|---|---|---|---|
| 1020 | TN | `CLOSED_EMPTY_ACC` | kept detector | `detector_preserved_by_port_retighten_v2_safety`; final row was TN but v2 did not classify it as FP/TN at decision time |
| 1040 | TN | `CLOSED_EMPTY_P3_FALLBACK` | kept detector | `detector_preserved_by_port_retighten_v2_safety`; final row was TN but v2 did not classify it as FP/TN at decision time |
| 1060 | TN | `CLOSED_EMPTY_P3_FALLBACK` | kept detector | `detector_preserved_by_port_retighten_v2_safety`; above preferred detector rate |
| 1130 | TN | `CLOSED_EMPTY_P3_FALLBACK` | kept detector | `detector_preserved_by_port_retighten_v2_safety`; above preferred and max detector rate |
| 1150 | FN | `CLOSED_EMPTY_P3_FALLBACK` | kept detector | `actual_fn_detector_protection+likely_unprotected_fn_risk` |
| 1170 | FN | `CLOSED_EMPTY_P3_FALLBACK` | kept detector | `actual_fn_detector_protection+likely_unprotected_fn_risk` |
| 1190 | TN | `CLOSED_EMPTY_P3_FALLBACK` | suppressed detector | `fp_tn_event_state+event_refresh_detector+no_likely_unprotected_fn_risk+no_true_deterministic_emergency+no_final_normal_blocker+above_preferred_detector_rate+above_max_detector_rate` |
| 1210 | FN | `CLOSED_EMPTY_P3_FALLBACK` | kept detector | `actual_fn_detector_protection+likely_unprotected_fn_risk` |
| 1255 | FP | `FALLBACK_P3_POLICY` | kept detector | `likely_unprotected_fn_risk`; v2 did not keep it as true emergency, but the likely-FN test remained too broad |

## Carry-Over Status

| Video | Proposal | Detector | Event FN | Protected FN | Unprotected FN | Status |
|---|---:|---:|---:|---:|---:|---|
| `badWeather/snowFall` | 0.44000 | 0.00000 | 42 | 27 | 15 | FAIL, unprotected FN > 6 |
| `thermal/lakeSide` | 0.46000 | 0.00000 | 63 | 45 | 18 | FAIL, unprotected FN > 12 |
| `intermittentObjectMotion/sofa` | 0.35000 | 0.00000 | 26 | 22 | 4 | PASS preferred unprotected FN, proposal at preferred ceiling |
| `intermittentObjectMotion/parking` | 0.53000 | 0.00000 | 47 | 35 | 12 | FAIL, proposal > 0.50 |
| `shadow/copyMachine` | 0.45000 | 0.00000 | 66 | 39 | 27 | FAIL, accepted carry-over not preserved |
| `turbulence/turbulence2` | 0.28000 | 0.00000 | 5 | 5 | 0 | PASS |
| `lowFramerate/tunnelExit_0_35fps` | 0.40000 | 0.00000 | 6 | 3 | 3 | PASS accepted/watch |
| `shadow/cubicle` | 0.88000 | 0.05000 | 18 | 18 | 0 | PASS recall gate not assessed in this CSV, unprotected FN 0 |
| `PTZ/continuousPan` | 0.04000 | 0.01000 | 0 | 0 | 0 | PASS controlled |
| `PTZ/intermittentPan` | 0.11000 | 0.00000 | 11 | 11 | 0 | PASS unprotected FN 0, proposal higher than Step 4E |
| `dynamicBackground/fountain01` | 0.00000 | 0.00000 | 0 | 0 | 0 | PASS quiet |
| `dynamicBackground/fountain02` | 0.40000 | 0.01000 | 0 | 0 | 0 | PASS, normal-frame false interventions 0 at aggregate |
| `nightVideos/bridgeEntry` | 0.31000 | 0.08000 | 0 | 0 | 0 | PASS event FN 0, detector higher than Step 4E |

## Gate Table

| Gate | Result | Status |
|---|---:|---|
| Planned jobs complete, 0 failed | 56/56, 0 failed | PASS |
| Aggregate detector request rate < 0.10 | 0.01643 | PASS |
| Normal-frame proposals = 0 | 0 | PASS |
| Guard alignment >= 0.95 | 1.00000 | PASS |
| Port detector request <= 0.03000 preferred, hard fail if > 0.05000 | 0.08000 | FAIL |
| Port unprotected FN = 0 | 4 | FAIL |
| Port created unprotected FN from detector suppression = 0 | 0 | PASS |
| Port proposal preferred <= 0.40000 | 0.40000 | PASS |
| Suppress at least 4 of 6 FP/TN detector-refresh rows | 1 suppressed | FAIL |
| Actual-FN detector-protecting row kept or safely replaced | 3 actual-FN detectors kept | PASS |
| SnowFall proposal <= 0.45000 | 0.44000 | PASS |
| SnowFall detector <= 0.03000 | 0.00000 | PASS |
| SnowFall unprotected FN <= 6 acceptable | 15 | FAIL |
| LakeSide proposal <= 0.50000 | 0.46000 | PASS |
| LakeSide detector <= 0.02000 | 0.00000 | PASS |
| LakeSide unprotected FN <= 12 acceptable | 18 | FAIL |
| Sofa proposal <= 0.35000 preferred, hard fail > 0.40000 | 0.35000 | PASS |
| Sofa detector <= 0.03000 | 0.00000 | PASS |
| Sofa unprotected FN <= 6 acceptable | 4 | PASS |
| Parking proposal <= 0.50000 | 0.53000 | FAIL |
| Parking detector <= 0.02000 | 0.00000 | PASS |
| Parking unprotected FN <= 12 | 12 | PASS |
| CopyMachine accepted gate | unprotected FN 27 | FAIL |
| Turbulence2 accepted gate | unprotected FN 0 | PASS |
| TunnelExit accepted gate | unprotected FN 3 | PASS |
| Cubicle recall >= 0.80 and FN 0 | unprotected FN 0 | PASS/watch recall separately |
| ContinuousPan controlled | event FN 0 | PASS |
| IntermittentPan controlled | unprotected FN 0 | PASS |
| Fountain01 quiet | proposal 0.00000, detector 0.00000 | PASS |
| Fountain02 normal-frame false interventions = 0 | aggregate normal-frame proposals 0 | PASS |
| BridgeEntry event FN = 0 | 0 | PASS |
| No forbidden validation launched | none launched | PASS |

## Root Cause And Narrow Next Fix

Step 4E2 fails for two reasons:

1. The v2 row classifier did not lock onto the intended Step 4E seven-row surface. It audited 9 detector-refresh rows and kept 8, including four final-TN rows whose v2 decision-time state was not classified as FP/TN.
2. The v2 `likely_unprotected_fn` predicate is still too broad for port. It kept the FP row at frame 1255 as `likely_unprotected_fn_risk` even though it was not a true deterministic emergency.

Narrow next fix:

- Rebase the next dry-run from the known Step 4E config/output behavior, not the current failed Step 4E2 result.
- In the v2 decision, classify FP/TN using the same row state that compare reports, or log both decision-time and final event state so mismatches cannot bypass suppression.
- For `lowFramerate/port_0_17fps`, keep likely-unprotected-FN detector only on actual FN or an explicit unprotected-FN marker, not generic event-refresh/closed-empty safety.
- Suppress final FP/TN `detector_refresh_needed_for_event` rows even when generic refresh safety labels are present, unless a true emergency flag is present.

Full CDnet remains held. Recommended next step is a narrow Step 4E3 port-row classifier correction before any Step 4F freeze or Step 4G full CDnet dry-run.
