# ASMAG-TR Controller Online Guarded Step 4E5 Port/Parking Carry-over Report

Date: 2026-05-18

## Scope

Step 4E5 used the residual-risk subset only:

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

The run used four pipelines for 56 planned jobs. No live, live compare, full CDnet, full CDnet compare, cross-dataset, LASIESTA, SBI2015, BMC, PTZ-targeted standalone, or Jetson/edge profiling validation was launched.

## Files

Created:

- `configs/asmag_tr_controller_online_guarded_cdnet_step4e5_port_parking_subset_dryrun.yaml`
- `outputs/asmag_tr_controller_online_guarded_cdnet_step4e5_port_parking_subset_dryrun/`
- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4E5_PORT_PARKING_CARRYOVER_REPORT.md`

Changed:

- `src/run_experiment.py`
- `tools/compare_asmag_tr_controller_online_guarded.py`
- `docs/DAILY_STATUS.md`

## Validation Commands

Compile:

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
```

Subset dry-run:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_step4e5_port_parking_subset_dryrun.yaml --max-jobs-per-run 8
```

Compare:

```powershell
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_step4e5_port_parking_subset_dryrun
```

The run needed multiple resume invocations. One local command timed out during `PTZ/intermittentPan/ASMAG_TR_CONTROLLER_ONLINE_GUARDED`; the subsequent resume recovered the stale running job and completed normally.

## Completion

- Planned jobs: 56
- Completed jobs: 56
- Failed jobs: 0

## Aggregate Metrics

- FMeasure: 0.30991
- Event_F1: 0.64280
- Activation: 0.31143
- Avg_FPS: 23.43675
- P95 latency: 467.12444 ms
- Proposal rate: 0.37500
- Detector request rate: 0.01643
- Normal-frame proposals: 0
- Guard alignment: 1.00000

## Port Result

`lowFramerate/port_0_17fps` did not preserve the Step 4E4 V4 trajectory.

| Step | Proposal | Detector | Event FN | Protected FN | Unprotected FN | Suppressed / Kept |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Step 4E3 | 0.40000 | 0.04000 | 12 | 10 | 2 | 18 / 4 |
| Step 4E4 | 0.42000 | 0.05000 | 5 | 5 | 0 | 8 / 5 |
| Step 4E5 | 0.43000 | 0.06000 | 13 | 10 | 3 | 6 / 6 |

Step 4E5 port telemetry:

- Detector requests before retighten: 12
- Detector requests suppressed: 6
- Detector requests kept: 6
- Actual-FN detector kept count: 3
- Pre-FN/context detectors kept: 0
- Final FP/TN detector rows suppressed: 6
- True deterministic emergency detector kept: 0
- Created unprotected FN from detector suppression: 0
- Holdout activations: 1
- Holdout protected event-FN count: 0

Frames 1350 and 1355 regressed:

| Frame | Event_State | Action | Detector | Protected | Unprotected FN |
| ---: | --- | --- | ---: | ---: | ---: |
| 1350 | FN | CLOSED_EMPTY_P3_FALLBACK | 0 | 0 | 1 |
| 1355 | FN | CLOSED_EMPTY_P3_FALLBACK | 0 | 0 | 1 |

Audited detector/holdout row summary:

| Frame | State | Decision | Protected FN | Unprotected FN |
| ---: | --- | --- | ---: | ---: |
| 1130 | FP | kept detector | 0 | 0 |
| 1165 | FN | kept detector | 1 | 0 |
| 1185 | FN | kept detector | 1 | 0 |
| 1210 | TP | kept detector | 0 | 0 |
| 1230 | TN | kept detector | 0 | 0 |
| 1250 | TN | suppressed detector | 0 | 0 |
| 1255 | FP | suppressed detector | 0 | 0 |
| 1300 | FP | suppressed detector | 0 | 0 |
| 1305 | TN | suppressed detector | 0 | 0 |
| 1310 | FP | suppressed detector | 0 | 0 |
| 1315 | TN | suppressed detector | 0 | 0 |
| 1320 | FN | kept detector | 1 | 0 |
| 1335 | TN | holdout | 0 | 0 |
| 1350 | FN | frame status | 0 | 1 |
| 1355 | FN | frame status | 0 | 1 |

## Parking Result

Parking proposal was restored below the hard proposal gate, but preferred zero-unprotected-FN carry-over was not restored.

| Step | Proposal | Detector | Event FN | Protected FN | Unprotected FN | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Step 4D6 | 0.50000 | 0.00000 | 33 | 33 | 0 | Stable carry-over target |
| Step 4E4 | 0.51000 | 0.00000 | 37 | 35 | 2 | Failed proposal gate |
| Step 4E5 | 0.49000 | 0.00000 | 45 | 35 | 10 | Passes acceptable FN gate, misses preferred zero |

Parking Step 4E5 trim/fallback telemetry:

- Restored 4D3 trim count: 4
- Restored 4D5 trim count: 4
- Restored 4D6 trim count: 1
- Extra reserve trim count: 0
- Parking FN fallback activations: 0
- Parking fallback protected event-FN count: 0
- Accidental FN-protected trim count: 0
- Accidental rescue trim count: 0

Unprotected parking FN frames were 1350, 1355, 1360, 1365, 1370, 1475, 1480, 1485, 1490, and 1495.

## Carry-over Status

| Video | Proposal | Detector | Unprotected FN | Status |
| --- | ---: | ---: | ---: | --- |
| `badWeather/snowFall` | 0.49000 | 0.00000 | 6 | FAIL proposal > 0.45; FN acceptable limit |
| `thermal/lakeSide` | 0.53000 | 0.00000 | 1 | FAIL proposal > 0.50 |
| `intermittentObjectMotion/sofa` | 0.35000 | 0.00000 | 0 | PASS |
| `intermittentObjectMotion/parking` | 0.49000 | 0.00000 | 10 | PASS acceptable, misses preferred 0 |
| `shadow/copyMachine` | 0.49000 | 0.00000 | 2 | PASS accepted gate |
| `turbulence/turbulence2` | 0.31000 | 0.00000 | 0 | PASS |
| `lowFramerate/tunnelExit_0_35fps` | 0.40000 | 0.00000 | 3 | WATCH / accepted-history level |
| `shadow/cubicle` | 0.90000 | 0.03000 | 0 | PASS recall 0.84021 >= 0.80 |
| `PTZ/continuousPan` | 0.05000 | 0.01000 | 0 | PASS |
| `PTZ/intermittentPan` | 0.10000 | 0.00000 | 0 | WATCH / controlled |
| `dynamicBackground/fountain01` | 0.00000 | 0.00000 | 0 | PASS quiet |
| `dynamicBackground/fountain02` | 0.40000 | 0.05000 | 0 | PASS normal-frame false interventions 0 |
| `nightVideos/bridgeEntry` | 0.31000 | 0.08000 | 0 | PASS event FN 0 |

## Gate Table

| Gate | Result | Evidence |
| --- | --- | --- |
| All planned subset jobs completed, 0 failed | PASS | 56/56 completed, 0 failed |
| Aggregate detector request rate < 0.10 | PASS | 0.01643 |
| Normal-frame proposals = 0 | PASS | 0 |
| Guard alignment >= 0.95 | PASS | 1.00000 |
| Port detector <= 0.05 hard | FAIL | 0.06000 |
| Port unprotected FN = 0 | FAIL | 3 |
| Port created unprotected FN from suppression = 0 | PASS | 0 |
| Port frames 1350/1355 protected or no longer unprotected | FAIL | both unprotected FN |
| Port proposal preferred <= 0.40 | FAIL | 0.43000 |
| Parking proposal <= 0.50 | PASS | 0.49000 |
| Parking detector <= 0.02 | PASS | 0.00000 |
| Parking unprotected FN <= 12 | PASS | 10 |
| Parking preferred unprotected FN = 0 | FAIL preferred | 10 |
| Parking accidental FN/rescue trim count = 0 | PASS | 0 / 0 |
| snowFall proposal <= 0.45 | FAIL | 0.49000 |
| lakeSide proposal <= 0.50 | FAIL | 0.53000 |
| sofa proposal <= 0.35, detector <= 0.03, unprotected FN <= 6 | PASS | 0.35000 / 0.00000 / 0 |
| copyMachine accepted gate | PASS | 0.49000 / 0.00000 / 2 |
| turbulence2 accepted gate | PASS | 0.31000 / 0.00000 / 0 |
| tunnelExit accepted gate | WATCH | 0.40000 / 0.00000 / 3 |
| cubicle recall >= 0.80 and unprotected FN 0 | PASS | recall 0.84021, unprotected FN 0 |
| continuousPan controlled | PASS | 0.05000 / 0.01000 / 0 |
| intermittentPan controlled | WATCH | 0.10000 / 0.00000 / 0 |
| fountain01 quiet | PASS | proposal 0.00000 |
| fountain02 normal-frame false interventions = 0 | PASS | 0 |
| bridgeEntry event FN = 0 | PASS | 0 |
| No forbidden validation launched | PASS | subset dry-run and compare only |

## Root Cause

Step 4E5 did not actually preserve the successful Step 4E4 port trajectory. The new port preserve switch is telemetry-only; it records that the v4 preservation target is active, but it does not lock the Step 4E4 row decisions or enforce the Step 4E4 detector/holdout outcome. In the Step 4E5 run, v4 kept 6 detector rows instead of 5, failed to keep the Step 4E4 pre-FN/context detector pattern, and left frames 1350 and 1355 outside active holdout protection. The direct suppression safety counter stayed clean, so the failure is trajectory/holdout preservation rather than a direct created-unprotected-FN event at a suppressed detector row.

Parking partially improved from Step 4E4 by restoring proposal under 0.50, but the new fallback did not activate. The likely next inspection point is the parking fallback pre-signal and actual fallback branch alignment: the unprotected parking FN rows retained `CLOSED_EMPTY_ACC` but had no `ai_parking_restore_4d6_fn_fallback_reason`, indicating the fallback path was not reached for those rows.

## Outcome

Step 4E5 residual-risk subset dry-run fails. Full CDnet rerun remains held.

Recommended narrow next fix:

- Replace the port V4 preserve telemetry-only switch with an actual exact-video Step 4E4 decision lock or a row-level allowlist that reproduces Step 4E4 kept/suppressed/context rows, especially the pre-FN/context protection around the late-FN region.
- Keep detector hard-capped at <= 0.05 while restoring port unprotected FN to 0.
- Fix the parking fallback pre-signal/branch reachability only after port is re-locked, and keep it exact-video/no-detector.
