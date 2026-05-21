# ASMAG-TR Controller Online Guarded Step 4E6 Port/Parking Rebase Report

Date: 2026-05-18

## Scope

Step 4E6 was run as a residual-risk subset dry-run only. No live run, live compare, full CDnet run, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

Config:

- `configs/asmag_tr_controller_online_guarded_cdnet_step4e6_port_parking_rebase_subset_dryrun.yaml`

Output root:

- `outputs/asmag_tr_controller_online_guarded_cdnet_step4e6_port_parking_rebase_subset_dryrun/`

Subset:

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

Pipelines:

- `P3_MOG2`
- `ASMAG_TR_CONTROLLER`
- `ONLINE_CALIBRATED`
- `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`

## Execution

- Compile command passed:
  - `python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py`
- Step 4E6 subset dry-run completed:
  - Videos: 14
  - Pipelines: 4
  - Planned jobs: 56
  - Completed jobs: 56
  - Failed jobs: 0
- One intermediate run attempt exposed a `NameError` in the new parking hard-restore pre-signal flag. The code was corrected and the failed guarded parking job was retried successfully in the same Step 4E6 scoped output root.
- Compare command completed after rerun with warnings suppressed:
  - `python -W ignore tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_step4e6_port_parking_rebase_subset_dryrun`

## Aggregate Guarded Metrics

| Metric | Step 4E6 |
|---|---:|
| FMeasure | 0.29046 |
| Event_F1 | 0.62271 |
| Activation | 0.37714 |
| Avg_FPS | 23.92270 |
| P95 latency ms | 399.20162 |
| Proposal rate | 0.36714 |
| Detector request rate | 0.01500 |
| Normal-frame proposals | 0 |
| Guard alignment | 1.00000 |

Aggregate detector, normal-frame proposal, and guard-alignment gates passed, but video-level gates failed.

## Port Comparison

`lowFramerate/port_0_17fps`

| Step | Proposal | Detector | Event FN | Protected FN | Unprotected FN |
|---|---:|---:|---:|---:|---:|
| Step 4E4 | 0.42000 | 0.05000 | 5 | 5 | 0 |
| Step 4E5 | 0.43000 | 0.06000 | 13 | 10 | 3 |
| Step 4E6 | 0.40000 | 0.08000 | 14 | 10 | 4 |

Step 4E6 did not hard-lock the successful Step 4E4 port trajectory. Detector rate rose to 0.08000, above the 0.05000 hard gate, and unprotected FN rose to 4.

Port Step 4E6 hard-lock telemetry:

- Detector requests before retighten: 10
- Detector requests suppressed: 2
- Detector requests kept: 8
- Created unprotected FN from detector suppression: 0
- Frame 1350: present, final FN, `CLOSED_EMPTY_P3_FALLBACK`, detector 0, protected 0, unprotected FN 1
- Frame 1355: present, final FN, `CLOSED_EMPTY_P3_FALLBACK`, detector 0, protected 0, unprotected FN 1

Root cause: the Step 4E6 port hard-lock flags did not reach the no-detector protection path for frames 1350 and 1355, and the detector-retighten path did not reproduce the Step 4E4 kept/suppressed row decisions. The lock was active on the port video, but enforcement was incomplete at the row/action branch that matters.

## Parking Comparison

`intermittentObjectMotion/parking`

| Step | Proposal | Detector | Event FN | Protected FN | Unprotected FN |
|---|---:|---:|---:|---:|---:|
| Step 4D6 | 0.50000 | 0.00000 | 33 | 33 | 0 |
| Step 4E5 | 0.49000 | 0.00000 | 45 | 35 | 10 |
| Step 4E6 | 0.57000 | 0.00000 | 46 | 37 | 9 |

Step 4E6 did not restore the Step 4D6 parking trajectory. It preserved the trim-stack counts, but the proposal rate and FN safety failed.

Parking Step 4E6 telemetry:

- Restored 4D3 trim count: 4
- 4D5 post-lock trim count: 4
- 4D6 final trim count: 1
- Detector request rate: 0.00000
- Accidental FN-protected trim count: 0
- Accidental rescue trim count: 0
- Unprotected FN: 9

Root cause: the restored trim counters are present, but the hard-restore branch did not rebase the surrounding parking protection trajectory to the Step 4D6 state. The extra hard-restore fallback did not cover all late unprotected FN rows, and proposal rate increased instead of stopping at 0.50000.

## Carry-Over Status

| Video | Proposal | Detector | Event FN | Protected FN | Unprotected FN | Status |
|---|---:|---:|---:|---:|---:|---|
| `badWeather/snowFall` | 0.52000 | 0.00000 | 35 | 28 | 7 | Fail: proposal > 0.45 and unprotected FN > 6 |
| `thermal/lakeSide` | 0.41000 | 0.00000 | 61 | 37 | 24 | Fail: unprotected FN > 12 |
| `intermittentObjectMotion/sofa` | 0.35000 | 0.00000 | 23 | 23 | 0 | Pass |
| `shadow/copyMachine` | 0.47000 | 0.00000 | 49 | 42 | 7 | Watch/fail versus prior accepted carry-over |
| `turbulence/turbulence2` | 0.31000 | 0.00000 | 3 | 3 | 0 | Pass |
| `lowFramerate/tunnelExit_0_35fps` | 0.38000 | 0.00000 | 4 | 1 | 3 | Watch |
| `shadow/cubicle` | 0.90000 | 0.03000 | 14 | 14 | 0 | Recall 0.77419, fail recall >= 0.80 |
| `PTZ/continuousPan` | 0.04000 | 0.01000 | 0 | 0 | 0 | Controlled |
| `PTZ/intermittentPan` | 0.07000 | 0.00000 | 9 | 7 | 2 | Watch |
| `dynamicBackground/fountain01` | 0.00000 | 0.00000 | 0 | 0 | 0 | Quiet |
| `dynamicBackground/fountain02` | 0.40000 | 0.01000 | 0 | 0 | 0 | Normal-frame false interventions 0 |
| `nightVideos/bridgeEntry` | 0.32000 | 0.08000 | 0 | 0 | 0 | Event FN pass; detector watch |

## Gate Table

| Gate | Result |
|---|---|
| 56 planned subset jobs complete, 0 failed | Pass |
| Aggregate detector request rate < 0.10 | Pass: 0.01500 |
| Normal-frame proposals = 0 | Pass |
| Guard alignment >= 0.95 | Pass: 1.00000 |
| Port detector request <= 0.05 | Fail: 0.08000 |
| Port unprotected FN = 0 | Fail: 4 |
| Port frames 1350/1355 protected or no longer unprotected FN | Fail: both unprotected FN |
| Port created unprotected FN from suppression = 0 | Pass: 0 |
| Parking proposal <= 0.50 | Fail: 0.57000 |
| Parking detector <= 0.02 | Pass: 0.00000 |
| Parking unprotected FN <= 12 | Pass: 9; preferred 0 missed |
| Parking accidental FN/rescue trim = 0 | Pass: 0/0 |
| snowFall proposal/detector/unprotected FN gate | Fail: 0.52000/0.00000/7 |
| lakeSide proposal/detector/unprotected FN gate | Fail: 0.41000/0.00000/24 |
| sofa gate | Pass |
| cubicle recall >= 0.80 and FN 0 | Fail: recall 0.77419 |
| fountain02 normal-frame false interventions = 0 | Pass |
| bridgeEntry event FN = 0 | Pass |
| Forbidden validation launched | Pass: none launched |

## Conclusion

Step 4E6 residual-risk subset dry-run fails.

The dry-run completed technically, but Step 4E6 did not enforce the intended behavior locks:

1. Port V4 hard lock did not reproduce Step 4E4 and left frames 1350/1355 unprotected.
2. Parking did not restore Step 4D6 proposal/FN-safety behavior.
3. snowFall and lakeSide carry-over locks reported drift but did not safely correct it.

Full CDnet rerun remains held.

Recommended narrow next fix:

- Rebase from the last passing Step 4E4 output behavior for port using explicit frame-decision reproduction for the known port row set, including protected no-detector treatment for frames 1350 and 1355.
- Rebase parking from Step 4D6 by restoring the full protection trajectory before trim, not only trim counters.
- Keep snowFall/lakeSide as report-only locks unless existing safe correction branches can be proven to fire before proposal/FN accounting.
- Rerun only the same 14-video residual-risk subset after the next narrow patch.
