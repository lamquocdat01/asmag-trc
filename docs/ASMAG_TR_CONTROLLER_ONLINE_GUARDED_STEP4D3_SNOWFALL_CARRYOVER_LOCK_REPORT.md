# ASMAG-TR Controller Online Guarded Step 4D3 SnowFall Carry-Over Lock Report

Date: 2026-05-17

## Scope And Safety

Step 4D3 used a separate dry-run config and output root:

- Config: `configs/asmag_tr_controller_online_guarded_cdnet_step4d3_snowfall_carryover_subset_dryrun.yaml`
- Output: `outputs/asmag_tr_controller_online_guarded_cdnet_step4d3_snowfall_carryover_subset_dryrun/`

No live run, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched. The default guarded config remains unchanged.

Compile passed:

`python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py`

The Step 4D3 residual-risk subset dry-run completed 56/56 planned jobs with 0 failed jobs. Compare completed for the Step 4D3 output root.

## Planned Subset

The run used the same 14-video residual-risk subset:

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

## Aggregate Metrics

| Metric | Step 4D3 |
| --- | ---: |
| Planned jobs | 56 |
| Completed jobs | 56 |
| Failed jobs | 0 |
| FMeasure | 0.34747 |
| Event_F1 | 0.67444 |
| Activation | 0.52000 |
| Avg_FPS | 34.58562 |
| P95 latency | 235.50198 ms |
| Proposed intervention rate | 0.33500 |
| Detector request rate | 0.01071 |
| Normal-frame proposals | 0 |
| Guard alignment | 1.00000 |

## SnowFall Progression

| Step | Proposal | Detector | Event FN | Protected FN | Unprotected FN |
| --- | ---: | ---: | ---: | ---: | ---: |
| Step 4 full 2Q2 | 0.29000 | 0.03000 | 22 | 12 | 10 |
| Step 4D subset | 0.28000 | 0.00000 | 22 | 12 | 10 |
| Step 4D2 subset | 0.30000 | 0.00000 | 23 | 16 | 7 |
| Step 4D3 subset | 0.36000 | 0.00000 | 22 | 21 | 1 |

Step 4D3's snowFall cap increase worked. The actual-FN rescue cap rose to 20 active no-detector rescues, with 20 rescue-protected event-FN frames. The run logged 21 actual-FN candidates, 20 activations, cap used max 20, 1 remaining `snowfall_actual_fn_rescue_cap_exhausted` row after D3, and 0 mask-quality skips.

The remaining snowFall miss is not evidence for broader detector logic. Detector stayed 0.00000, proposal stayed below the 0.45 gate, and the residual miss is a single cap-exhausted exact actual-FN row with no logged mask-quality exposure.

## Carry-Over Locks

| Video | Proposal | Detector | Event FN | Protected FN | Unprotected FN | Step 4D3 carry-over behavior |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `thermal/lakeSide` | 0.50000 | 0.00000 | 48 | 48 | 0 | Carry-over lock active on 62 frames; final rate held at 0.50000; no detector; accidental hard/rescue trim count 0. |
| `intermittentObjectMotion/sofa` | 0.27000 | 0.00000 | 21 | 21 | 0 | Existing Step 4C rescue path recovered the carry-over; fallback lock did not need to fire. |
| `intermittentObjectMotion/parking` | 0.54000 | 0.00000 | 33 | 33 | 0 | Carry-over lock active on 9 cap-exhausted event-FN-risk frames; recall recovered, but proposal exceeded the 0.50000 gate. |

Parking is the only blocking regression. The new lock converted the Step 4D2 unprotected-FN failure into full event-FN protection, but proposal pressure rose from 0.44000 to 0.54000. Root cause: the 9-frame no-detector carry-over reserve adds protected proposal frames after existing parking preserve/rescue pressure, while the post-preservation trim only reclaimed 4 generic non-risk frames and did not trim protected lock/rescue/FN-risk frames. The configured max proposal target is present, but the lock needs a post-lock pressure trim or stricter activation budget to honor 0.50000.

## Carry-Over Status

| Video | Step 4D3 status |
| --- | --- |
| `lowFramerate/port_0_17fps` | Watch item preserved: proposal 0.37000, detector 0.07000, unprotected FN 0. Detector improved versus Step 4D2 but remains a later retighten target. |
| `shadow/copyMachine` | Within accepted carry-over gate: proposal 0.49000, detector 0.00000, unprotected FN 8. |
| `turbulence/turbulence2` | Pass: proposal 0.31000, detector 0.00000, unprotected FN 0. |
| `lowFramerate/tunnelExit_0_35fps` | Pass/watch: proposal 0.31000, detector 0.00000, unprotected FN 1. |
| `shadow/cubicle` | Pass: pixel recall 0.87408 and unprotected event FN 0. |
| `PTZ/continuousPan` | Controlled: proposal 0.04000, detector 0.01000, event FN 0. |
| `PTZ/intermittentPan` | Controlled: proposal 0.01000, detector 0.00000, unprotected FN 0. |
| `dynamicBackground/fountain01` | Quiet: proposal 0.00000, detector 0.00000. |
| `dynamicBackground/fountain02` | Normal-frame false interventions remain 0; proposal 0.40000, detector 0.01000. |
| `nightVideos/bridgeEntry` | Pass: event FN 0. |

## Gate Table

| Gate | Result | Status |
| --- | --- | --- |
| All planned subset jobs completed, 0 failed | 56/56 completed, 0 failed | Pass |
| Aggregate detector request rate < 0.10 | 0.01071 | Pass |
| Normal-frame proposals = 0 | 0 | Pass |
| Guard alignment >= 0.95 | 1.00000 | Pass |
| snowFall detector request <= 0.03 | 0.00000 | Pass |
| snowFall proposal <= 0.45 | 0.36000 | Pass |
| snowFall unprotected FN materially improves versus 10 | 1 | Pass |
| snowFall preferred unprotected FN <= 4 | 1 | Pass |
| snowFall acceptable unprotected FN <= 6 | 1 | Pass |
| Hard fail if snowFall unprotected FN >= 10 | 1 | Pass |
| lakeSide proposal <= 0.50 | 0.50000 | Pass |
| lakeSide detector <= 0.02 | 0.00000 | Pass |
| lakeSide unprotected FN <= 8 preferred | 0 | Pass |
| sofa proposal <= 0.35 preferred | 0.27000 | Pass |
| sofa hard fail if proposal > 0.40 | 0.27000 | Pass |
| sofa detector <= 0.03 | 0.00000 | Pass |
| sofa unprotected FN <= 4 preferred | 0 | Pass |
| parking proposal <= 0.50 | 0.54000 | Fail |
| parking detector <= 0.02 | 0.00000 | Pass |
| parking unprotected FN <= 12 | 0 | Pass |
| copyMachine remains within accepted gate | Proposal 0.49000, detector 0.00000, unprotected FN 8 | Pass |
| turbulence2 remains within accepted gate | Proposal 0.31000, detector 0.00000, unprotected FN 0 | Pass |
| tunnelExit remains within accepted gate | Proposal 0.31000, detector 0.00000, unprotected FN 1 | Pass |
| cubicle recall >= 0.80 and FN 0 | Recall 0.87408, unprotected FN 0 | Pass |
| continuousPan remains controlled | Proposal 0.04000, detector 0.01000, event FN 0 | Pass |
| intermittentPan remains controlled | Proposal 0.01000, detector 0.00000, unprotected FN 0 | Pass |
| fountain01 remains quiet | Proposal 0.00000, detector 0.00000 | Pass |
| fountain02 normal-frame false interventions = 0 | 0 | Pass |
| bridgeEntry event FN = 0 | 0 | Pass |
| No forbidden validation launched | No live/full/cross/PTZ-targeted/edge validation launched | Pass |

## Result And Recommendation

Step 4D3 residual-risk subset dry-run does not pass because `intermittentObjectMotion/parking` exceeds the proposal gate at 0.54000.

The snowFall change is successful and should be preserved: it needs the narrow actual-FN cap increase, not broader detector policy. LakeSide and sofa carry-over behavior are restored. Parking needs one narrow follow-up before full CDnet remains appropriate: add a Step 4D4 parking post-lock proposal-pressure trim or stricter carry-over lock budget that keeps the 9 no-detector FN-risk recovery intent while restoring proposal <= 0.50000 and preserving unprotected FN <= 12.

Full CDnet and live validation remain held. Step 4E `port_0_17fps` detector retighten should wait until the parking proposal gate is restored.
