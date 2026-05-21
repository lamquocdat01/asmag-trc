# ASMAG-TR Controller Online Guarded Step 4D5 Parking Trim-Order Report

Date: 2026-05-17

## Scope

Step 4D5 tested a parking-only trim-order correction on top of Step 4D4. The run restored the known-safe Step 4D3 post-preservation trim first, then applied a narrower post-lock soft trim.

Residual-risk subset:

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

This stayed dry-run only. No live, live compare, full CDnet, full CDnet compare, cross-dataset, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

## Files And Commands

Created:

- `configs/asmag_tr_controller_online_guarded_cdnet_step4d5_parking_trim_order_subset_dryrun.yaml`
- `outputs/asmag_tr_controller_online_guarded_cdnet_step4d5_parking_trim_order_subset_dryrun/`
- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4D5_PARKING_TRIM_ORDER_REPORT.md`

Changed:

- `src/run_experiment.py`
- `tools/compare_asmag_tr_controller_online_guarded.py`
- `docs/DAILY_STATUS.md`

Validation commands run:

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_step4d5_parking_trim_order_subset_dryrun.yaml --max-jobs-per-run 8
python -W ignore tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_step4d5_parking_trim_order_subset_dryrun
```

The first compare invocation hit the local 120-second tool timeout; the same Step 4D5 compare was rerun with a longer timeout and completed.

## Aggregate Result

Run completion:

- Planned jobs: 56
- Completed jobs: 56
- Failed jobs: 0
- Pipelines: `P3_MOG2`, `ASMAG_TR_CONTROLLER`, `ONLINE_CALIBRATED`, `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`

Guarded aggregate metrics:

| Metric | Step 4D5 |
|---|---:|
| FMeasure | 0.35061 |
| Event_F1 | 0.67692 |
| Activation | 0.52429 |
| Proposed intervention rate | 0.33143 |
| Detector request rate | 0.01071 |
| Normal-frame proposals | 0 |
| Guard alignment | 1.00000 |
| Avg FPS | 37.28567 |
| P95 latency ms | 245.21436 |

Step 4D5 technically completed, but it fails the parking proposal gate by one frame.

## Parking Result

| Metric | Step 4D3 | Step 4D4 | Step 4D5 |
|---|---:|---:|---:|
| Proposal rate | 0.54000 | 0.58000 | 0.51000 |
| Detector request rate | 0.00000 | 0.00000 | 0.00000 |
| Event FN | 33 | 33 | 33 |
| Protected event FN | 33 | 33 | 33 |
| Unprotected event FN | 0 | 0 | 0 |
| Rescue active frames | 24 | 24 | 24 |
| Carry-over lock active frames | 9 | 9 | 9 |
| Carry-over lock protected event-FN frames | 9 | 9 | 9 |
| Step 4D3 post-preservation trim count | 4 | 0 | 4 |
| Step 4D5 post-lock candidates | n/a | n/a | 40 |
| Step 4D5 post-lock soft candidates | n/a | n/a | 12 |
| Step 4D5 post-lock trim count | n/a | n/a | 4 |
| Step 4D5 final rate | n/a | n/a | 0.51000 |
| Accidental FN-protected trim count | n/a | 0 | 0 |
| Accidental rescue trim count | n/a | n/a | 0 |

Step 4D5 restored the known-safe Step 4D3 four-frame post-preservation trim. The later hard-protection phase did not block it: `restore_4d3_trim_count_max=4`, `restore_4d3_trim_blocked_by_later_hardprotect_frames=0`.

The new post-lock trim found safe soft pressure after the restored trim: 40 candidates, 12 soft candidates, and 4 suppressed frames. It did not trim protected event-FN or rescue frames: accidental FN/rescue trim counts were both 0.

However, parking still ended at 51 retained proposals out of 100 frames. Root cause: Step 4D5 corrected the trim order and safely reclaimed eight total frames, but the post-lock stage stopped after four extra soft trims while one more safe trim was needed to satisfy the `<= 0.50000` proposal gate. The failure is now a one-frame target-count residual, not a missing carry-over lock or protected-frame safety issue.

Narrow next fix: a Step 4D6 parking-only dry-run should keep the restored Step 4D3 trim unchanged and let the same Step 4D5 soft-candidate post-lock trim continue until `<= 0.50000`, with an explicit final-needed-frame calculation and the same no-FN/no-rescue safety counters.

## Carry-Over Status

| Video | Proposal | Detector | Event FN | Protected FN | Unprotected FN | Status |
|---|---:|---:|---:|---:|---:|---|
| snowFall | 0.36000 | 0.00000 | 22 | 21 | 1 | Pass |
| lakeSide | 0.50000 | 0.00000 | 48 | 48 | 0 | Pass |
| sofa | 0.27000 | 0.00000 | 21 | 21 | 0 | Pass |
| port_0_17fps | 0.37000 | 0.07000 | 5 | 5 | 0 | Monitored, unchanged target |
| parking | 0.51000 | 0.00000 | 33 | 33 | 0 | Fail proposal gate |
| copyMachine | 0.46000 | 0.00000 | 46 | 42 | 4 | Pass |
| turbulence2 | 0.31000 | 0.00000 | 3 | 3 | 0 | Pass |
| tunnelExit_0_35fps | 0.31000 | 0.00000 | 2 | 1 | 1 | Pass |
| cubicle | 0.90000 | 0.02000 | 14 | 14 | 0 | Pass, recall 0.87408 |
| continuousPan | 0.05000 | 0.01000 | 0 | 0 | 0 | Pass |
| intermittentPan | 0.01000 | 0.00000 | 1 | 1 | 0 | Pass |
| fountain01 | 0.00000 | 0.00000 | 0 | 0 | 0 | Pass |
| fountain02 | 0.40000 | 0.01000 | 0 | 0 | 0 | Pass, normal-frame false interventions 0 |
| bridgeEntry | 0.19000 | 0.04000 | 0 | 0 | 0 | Pass |

SnowFall remained within the Step 4D3 gate: proposal 0.36000, detector 0.00000, unprotected FN 1. The cap increase logged 21 actual-FN candidates, 20 activations, 20 no-detector rescue-protected event-FN frames, one cap-exhausted row after D3, and no mask-quality skips.

LakeSide remained locked at proposal 0.50000, detector 0.00000, unprotected FN 0. Sofa remained locked at proposal 0.27000, detector 0.00000, unprotected FN 0.

## Gate Table

| Gate | Result | Status |
|---|---:|---|
| All planned jobs complete, 0 failed | 56/56, 0 failed | Pass |
| Aggregate detector request rate < 0.10 | 0.01071 | Pass |
| Normal-frame proposals = 0 | 0 | Pass |
| Guard alignment >= 0.95 | 1.00000 | Pass |
| Parking proposal <= 0.50 | 0.51000 | Fail |
| Parking detector <= 0.02 | 0.00000 | Pass |
| Parking unprotected FN <= 12 | 0 | Pass |
| Parking accidental FN/rescue trim count = 0 | 0 / 0 | Pass |
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
| continuousPan controlled | proposal 0.05000, detector 0.01000 | Pass |
| intermittentPan controlled | proposal 0.01000, detector 0.00000 | Pass |
| fountain01 quiet | proposal 0.00000, detector 0.00000 | Pass |
| fountain02 normal-frame false interventions = 0 | 0 | Pass |
| bridgeEntry event FN = 0 | 0 | Pass |
| No forbidden validation launched | confirmed | Pass |

## Conclusion

Step 4D5 residual-risk subset dry-run fails due only to parking proposal rate: 0.51000 versus the 0.50000 gate. The trim-order correction worked in principle: it restored the Step 4D3 four-frame trim, added four safe post-lock trims, kept detector 0.00000, and left parking unprotected FN at 0. Full CDnet remains held.
