# ASMAG-TRC Step 4E Port Detector Retighten Report

Date: 2026-05-17

## Executive Summary

Step 4E added an exact-video `lowFramerate/port_0_17fps` detector-retighten path on top of the Step 4D6 residual-risk subset stack. The dry-run completed technically, but the subset does **not** pass because the port detector rate remained `0.07000`, above the `0.05000` hard-fail gate.

No live, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

## Files And Outputs

- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_step4e_port_detector_subset_dryrun.yaml`
- Created output root: `outputs/asmag_tr_controller_online_guarded_cdnet_step4e_port_detector_subset_dryrun/`
- Updated implementation: `src/run_experiment.py`
- Updated compare/reporting: `tools/compare_asmag_tr_controller_online_guarded.py`
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4E_PORT_DETECTOR_RETIGHTEN_REPORT.md`

Compile passed:

```text
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
```

## Planned Subset Scope

The Step 4E dry-run used the same 14-video residual-risk subset:

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

| Metric | Step 4E |
|---|---:|
| Planned jobs | 56 |
| Completed jobs | 56 |
| Failed jobs | 0 |
| FMeasure | 0.34682 |
| Event_F1 | 0.67667 |
| Activation | 0.52000 |
| Avg_FPS | 36.87264 |
| P95 latency ms | 220.49601 |
| Proposed intervention rate | 0.33000 |
| Detector request rate | 0.01214 |
| Normal-frame proposals | 0 |
| Guard alignment | 1.00000 |

Step 4E completed technically, but fails the residual-risk subset gates because `lowFramerate/port_0_17fps` detector request rate stayed at `0.07000`.

## Port Step 4 Full Vs Step 4E

| Metric | Step 4 full audit baseline | Step 4E |
|---|---:|---:|
| Proposal rate | 0.37000 | 0.37000 |
| Detector request rate | 0.07000 | 0.07000 |
| Event FN | 5 | 5 |
| Protected event FN | 5 | 5 |
| Unprotected event FN | 0 | 0 |
| Detector-request frames | 7 | 7 |
| Detector requests suppressed | n/a | 0 |
| Detector requests kept | n/a | 7 |
| Kept detectors that protected FN | 1 | 1 |
| Created unprotected FN from suppression | n/a | 0 |

## Port Detector Retighten Behavior

The Step 4E telemetry found the expected seven port detector-refresh frames, all with `ai_detector_request_source = detector_refresh_needed_for_event`.

| Frame | State | Action | Retighten decision | Reason |
|---:|---|---|---|---|
| 1210 | FN | `CLOSED_EMPTY_P3_FALLBACK` | kept detector | `actual_fn_detector_protection+likely_unprotected_fn_risk+strong_localized_fn_risk` |
| 1230 | FP | `FORCED_REFRESH` | kept detector | `detector_preserved_by_port_retighten_safety` |
| 1255 | FP | `FALLBACK_P3_POLICY` | kept detector | `deterministic_emergency_safeguard` |
| 1340 | TN | `CLOSED_EMPTY_P3_FALLBACK` | kept detector | `detector_preserved_by_port_retighten_safety` |
| 1360 | TN | `CLOSED_EMPTY_P3_FALLBACK` | kept detector | `detector_preserved_by_port_retighten_safety` |
| 1405 | TN | `CLOSED_EMPTY_P3_FALLBACK` | kept detector | `detector_preserved_by_port_retighten_safety` |
| 1425 | TN | `CLOSED_EMPTY_P3_FALLBACK` | kept detector | `detector_preserved_by_port_retighten_safety` |

Root cause: the exact-video retighten hook and reporting are present, but the suppression decision is too conservative. The code identified FP/TN event-refresh rows with `no_likely_unprotected_fn_risk`, yet the final safety branch preserved them as `detector_preserved_by_port_retighten_safety`. One FP row was also kept as `deterministic_emergency_safeguard`, so the implementation did not reclaim any detector requests.

Detector suppression safety stayed intact because no detector was suppressed:

| Safety metric | Step 4E |
|---|---:|
| Suppressed detector requests | 0 |
| Created unprotected FN | 0 |
| Protected-FN detector kept | 1 |

## Carry-Over Status

| Video | Proposal | Detector | Event FN | Protected FN | Unprotected FN | Status |
|---|---:|---:|---:|---:|---:|---|
| `badWeather/snowFall` | 0.36000 | 0.00000 | 22 | 21 | 1 | Pass, Step 4D3/4D6 cap behavior preserved |
| `thermal/lakeSide` | 0.50000 | 0.00000 | 48 | 48 | 0 | Pass, Step 4B4 gate preserved |
| `intermittentObjectMotion/sofa` | 0.28000 | 0.00000 | 22 | 22 | 0 | Pass, Step 4C gate preserved |
| `intermittentObjectMotion/parking` | 0.46000 | 0.00000 | 33 | 33 | 0 | Pass, protection-aware gate preserved |
| `shadow/copyMachine` | 0.49000 | 0.00000 | 47 | 45 | 2 | Pass, accepted gate preserved |
| `turbulence/turbulence2` | 0.31000 | 0.00000 | 3 | 3 | 0 | Pass |
| `lowFramerate/tunnelExit_0_35fps` | 0.30000 | 0.00000 | 3 | 1 | 2 | Watch: unprotected FN is higher than Step 4D6's 1 |
| `shadow/cubicle` | 0.91000 | 0.02000 | 14 | 14 | 0 | Pass, recall 0.87396 |
| `PTZ/continuousPan` | 0.04000 | 0.01000 | 0 | 0 | 0 | Pass, controlled |
| `PTZ/intermittentPan` | 0.01000 | 0.00000 | 1 | 1 | 0 | Pass, controlled |
| `dynamicBackground/fountain01` | 0.00000 | 0.00000 | 0 | 0 | 0 | Pass, quiet |
| `dynamicBackground/fountain02` | 0.40000 | 0.02000 | 0 | 0 | 0 | Pass, normal-frame false interventions 0 |
| `nightVideos/bridgeEntry` | 0.19000 | 0.05000 | 0 | 0 | 0 | Pass, event FN 0 |

## Gate Table

| Gate | Result | Status |
|---|---:|---|
| Planned jobs complete, 0 failed | 56/56, 0 failed | PASS |
| Aggregate detector request rate < 0.10 | 0.01214 | PASS |
| Normal-frame proposals = 0 | 0 | PASS |
| Guard alignment >= 0.95 | 1.00000 | PASS |
| Port detector request <= 0.03000 preferred, hard fail if > 0.05000 | 0.07000 | FAIL |
| Port unprotected FN = 0 | 0 | PASS |
| Port created unprotected FN from detector suppression = 0 | 0 | PASS |
| Port proposal preferred <= 0.40000 | 0.37000 | PASS |
| SnowFall proposal <= 0.45000 | 0.36000 | PASS |
| SnowFall detector <= 0.03000 | 0.00000 | PASS |
| SnowFall unprotected FN <= 6 acceptable, <=4 preferred | 1 | PASS |
| LakeSide proposal <= 0.50000 | 0.50000 | PASS |
| LakeSide detector <= 0.02000 | 0.00000 | PASS |
| LakeSide unprotected FN <= 8 preferred, <=12 acceptable | 0 | PASS |
| Sofa proposal <= 0.35000 preferred, hard fail > 0.40000 | 0.28000 | PASS |
| Sofa detector <= 0.03000 | 0.00000 | PASS |
| Sofa unprotected FN <= 4 preferred, <=6 acceptable | 0 | PASS |
| Parking proposal <= 0.50000 | 0.46000 | PASS |
| Parking detector <= 0.02000 | 0.00000 | PASS |
| Parking unprotected FN <= 12 | 0 | PASS |
| CopyMachine accepted gate | unprotected FN 2 | PASS |
| Turbulence2 accepted gate | unprotected FN 0 | PASS |
| TunnelExit accepted carry-over | unprotected FN 2 vs Step 4D6 1 | WATCH |
| Cubicle recall >= 0.80 and FN 0 | recall 0.87396, unprotected FN 0 | PASS |
| ContinuousPan controlled | event FN 0 | PASS |
| IntermittentPan controlled | unprotected FN 0 | PASS |
| Fountain01 quiet | proposal 0.00000, detector 0.00000 | PASS |
| Fountain02 normal-frame false interventions = 0 | 0 | PASS |
| BridgeEntry event FN = 0 | 0 | PASS |
| No forbidden validation launched | none launched | PASS |

## Conclusion And Next Fix

Step 4E residual-risk subset dry-run **fails**. The failure is not caused by reduced port FN safety: `port_0_17fps` still has unprotected FN `0`, and the actual-FN detector-protecting row stayed protected. The failure is that the retighten rule did not suppress the six FP/TN detector-refresh rows identified by the Step 4A audit.

Recommended next step: create a narrow Step 4E2 port-only correction that changes the preservation order for `lowFramerate/port_0_17fps` only:

- Always keep the actual-FN detector-protecting row.
- Re-audit the one FP row currently labeled deterministic emergency before deciding whether to keep it.
- Suppress FP/TN `detector_refresh_needed_for_event` rows with `no_likely_unprotected_fn_risk`, especially once the preferred/max detector-rate thresholds are exceeded.
- Route suppressed rows through the no-detector fallback path.
- Keep the created-unprotected-FN counter at `0`.

Full CDnet, live, cross-dataset, PTZ-targeted standalone validation, and edge profiling remain **held**.
