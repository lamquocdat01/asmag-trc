# ASMAG-TR Controller Online Guarded Step 4D4 Parking Post-Lock Trim Report

Date: 2026-05-17

## Scope

Step 4D4 tested a parking-only post-lock proposal trim on top of Step 4D3. The run used the same residual-risk subset:

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

The run stayed dry-run only. No live, live compare, full CDnet, full CDnet compare, cross-dataset, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

## Files And Commands

Created:

- `configs/asmag_tr_controller_online_guarded_cdnet_step4d4_parking_trim_subset_dryrun.yaml`
- `outputs/asmag_tr_controller_online_guarded_cdnet_step4d4_parking_trim_subset_dryrun/`
- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4D4_PARKING_POST_LOCK_TRIM_REPORT.md`

Changed:

- `src/run_experiment.py`
- `tools/compare_asmag_tr_controller_online_guarded.py`
- `docs/DAILY_STATUS.md`

Validation commands run:

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_step4d4_parking_trim_subset_dryrun.yaml --max-jobs-per-run 8
python -W ignore tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_step4d4_parking_trim_subset_dryrun
```

The first compare invocation hit the local 120-second tool timeout; the same Step 4D4 compare was rerun with a longer timeout and completed.

## Aggregate Result

Run completion:

- Planned jobs: 56
- Completed jobs: 56
- Failed jobs: 0
- Pipelines: `P3_MOG2`, `ASMAG_TR_CONTROLLER`, `ONLINE_CALIBRATED`, `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`

Guarded aggregate metrics:

| Metric | Step 4D4 |
|---|---:|
| FMeasure | 0.34816 |
| Event_F1 | 0.67692 |
| Activation | 0.52429 |
| Proposed intervention rate | 0.33571 |
| Detector request rate | 0.01071 |
| Normal-frame proposals | 0 |
| Guard alignment | 1.00000 |
| Avg FPS | 35.50413 |
| P95 latency ms | 234.25517 |

Step 4D4 technically completed, but it fails the parking proposal gate.

## Parking Result

| Metric | Step 4D3 | Step 4D4 |
|---|---:|---:|
| Proposal rate | 0.54000 | 0.58000 |
| Detector request rate | 0.00000 | 0.00000 |
| Event FN | 33 | 33 |
| Protected event FN | 33 | 33 |
| Unprotected event FN | 0 | 0 |
| Rescue active frames | 24 | 24 |
| Carry-over lock active frames | 9 | 9 |
| Carry-over lock protected event-FN frames | 9 | 9 |
| Post-preservation trim candidates | 40 | 38 |
| Post-preservation trim count | 4 | 0 |
| Post-lock trim candidates | n/a | 38 |
| Post-lock soft candidates | n/a | 0 |
| Post-lock trim count | n/a | 0 |
| Post-lock final rate | n/a | 0.58000 |
| Post-lock hard-protected frames | n/a | 58 |
| Post-lock skipped hard-protected frames | n/a | 58 |
| Accidental hard trim count | n/a | 0 |
| Accidental FN-protected trim count | n/a | 0 |
| Deduplicate accounting count | n/a | 0 |

Parking stayed recall-safe: detector remained 0.00000, event FN was fully protected, and accidental hard/FN-protected trim counts were both 0.

However, the proposal trim failed. Step 4D4 did not find any safe soft-lock candidates and also prevented the existing Step 4D3 post-preservation trim from reclaiming its 4 generic/nonrisk frames. As a result, parking proposal rose from 0.54000 to 0.58000 instead of falling to <= 0.50000.

Root cause: the Step 4D4 hard-protection classification was too conservative for the post-lock trim stage. All 58 retained parking proposal frames were marked hard-protected, and the rejected-reason accounting shows no eligible soft-lock candidates. The requested fallback deduplicate path also found no rescue/lock overlap to reclaim. This means Step 4D4 protected FN safety correctly, but it did not preserve the known-safe Step 4D3 trim behavior.

Narrow next fix: create a Step 4D5 dry-run that restores the Step 4D3 parking post-preservation 4-frame trim unchanged, then applies a separate post-lock soft trim only after that baseline trim has already run. The next candidate predicate should target the known generic/nonrisk over-gate frames and must not classify every retained parking proposal as hard-protected merely because it is under parking cap pressure.

## Carry-Over Status

| Video | Proposal | Detector | Event FN | Protected FN | Unprotected FN | Status |
|---|---:|---:|---:|---:|---:|---|
| lakeSide | 0.50000 | 0.00000 | 48 | 48 | 0 | Pass |
| sofa | 0.27000 | 0.00000 | 21 | 21 | 0 | Pass |
| snowFall | 0.36000 | 0.00000 | 22 | 21 | 1 | Pass |
| port_0_17fps | 0.37000 | 0.07000 | 5 | 5 | 0 | Monitored, unchanged target |
| parking | 0.58000 | 0.00000 | 33 | 33 | 0 | Fail proposal gate |
| copyMachine | 0.46000 | 0.00000 | 46 | 42 | 4 | Pass |
| turbulence2 | 0.31000 | 0.00000 | 3 | 3 | 0 | Pass |
| tunnelExit_0_35fps | 0.31000 | 0.00000 | 2 | 1 | 1 | Pass |
| cubicle | 0.90000 | 0.02000 | 14 | 14 | 0 | Pass, recall 0.87408 |
| continuousPan | 0.04000 | 0.01000 | 0 | 0 | 0 | Pass |
| intermittentPan | 0.01000 | 0.00000 | 1 | 1 | 0 | Pass |
| fountain01 | 0.00000 | 0.00000 | 0 | 0 | 0 | Pass |
| fountain02 | 0.40000 | 0.01000 | 0 | 0 | 0 | Pass, normal-frame false interventions 0 |
| bridgeEntry | 0.19000 | 0.04000 | 0 | 0 | 0 | Pass |

SnowFall remained within the Step 4D3 gate: proposal 0.36000, detector 0.00000, unprotected FN 1. The actual-FN cap increase remained active on 20 frames, with one cap-exhausted row after Step 4D3 and no mask-quality rows skipped.

LakeSide remained locked at proposal 0.50000, detector 0.00000, unprotected FN 0. Sofa remained locked at proposal 0.27000, detector 0.00000, unprotected FN 0.

## Gate Table

| Gate | Result | Status |
|---|---:|---|
| All planned jobs complete, 0 failed | 56/56, 0 failed | Pass |
| Aggregate detector request rate < 0.10 | 0.01071 | Pass |
| Normal-frame proposals = 0 | 0 | Pass |
| Guard alignment >= 0.95 | 1.00000 | Pass |
| Parking proposal <= 0.50 | 0.58000 | Fail |
| Parking detector <= 0.02 | 0.00000 | Pass |
| Parking unprotected FN <= 12 | 0 | Pass |
| Parking accidental hard/FN-protected trim count = 0 | 0 / 0 | Pass |
| snowFall proposal <= 0.45 | 0.36000 | Pass |
| snowFall detector <= 0.03 | 0.00000 | Pass |
| snowFall unprotected FN <= 6 acceptable | 1 | Pass |
| lakeSide proposal <= 0.50 | 0.50000 | Pass |
| lakeSide detector <= 0.02 | 0.00000 | Pass |
| lakeSide unprotected FN <= 12 acceptable | 0 | Pass |
| sofa proposal hard fail > 0.40 | 0.27000 | Pass |
| sofa detector <= 0.03 | 0.00000 | Pass |
| sofa unprotected FN <= 6 acceptable | 0 | Pass |
| copyMachine accepted gate | proposal 0.46000, unprotected FN 4 | Pass |
| turbulence2 accepted gate | proposal 0.31000, unprotected FN 0 | Pass |
| tunnelExit accepted gate | proposal 0.31000, unprotected FN 1 | Pass |
| cubicle recall >= 0.80 and FN 0 | recall 0.87408, unprotected FN 0 | Pass |
| continuousPan controlled | proposal 0.04000, detector 0.01000 | Pass |
| intermittentPan controlled | proposal 0.01000, detector 0.00000 | Pass |
| fountain01 quiet | proposal 0.00000, detector 0.00000 | Pass |
| fountain02 normal-frame false interventions = 0 | 0 | Pass |
| bridgeEntry event FN = 0 | 0 | Pass |
| No forbidden validation launched | confirmed | Pass |

## Conclusion

Step 4D4 residual-risk subset dry-run fails due only to the parking proposal gate. The attempted post-lock trim preserved parking FN safety and did not accidentally trim hard/FN-protected frames, but it over-protected the candidate set and disabled the Step 4D3 4-frame post-preservation trim. Full CDnet remains held.
