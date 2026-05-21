# ASMAG-TRC Phase 8C-2P Live Final-Action Mismatch Patch Report

Date: 2026-05-15

## Scope

Phase 8C-2P adds two narrow, opt-in, no-detector live final-action mismatch guards on top of 8C-2O:

- `shadow/cubicle`: exact low-count live mismatch reserve for unsafe empty/fallback actions after active event memory and high event/loss score.
- `PTZ/intermittentPan`: exact closed-empty live mismatch rescue for high-score active-memory PTZ intermittentPan frames.

This phase intentionally does not fix `shadow/copyMachine` or `intermittentObjectMotion/parking`. `turbulence/turbulence2` and `lowFramerate/tunnelExit_0_35fps` were left unchanged because they were within the accepted 8C-2O live gates.

No live validation, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched. `ONLINE_CALIBRATED`, P1/P2/P3/FAST/ASMAG_TR_CONTROLLER, frozen CDnet2014 v1.6 outputs, accidental 8C-2E live artifacts, and the default guarded config were not modified.

## Files

- Updated controller logic: `src/run_experiment.py`
- Updated guarded compare reporting: `tools/compare_asmag_tr_controller_online_guarded.py`
- Created dry-run config: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2p_dryrun.yaml`
- Created output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2p_dryrun/`
- Created compare outputs:
  - `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2p_dryrun/ai_intervention_2p_live_mismatch_summary.csv`
  - `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2p_dryrun/ai_intervention_2p_frame_status.csv`
- Created runner resume logs under `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2p_dryrun/_resume_logs/`
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2P_LIVE_MISMATCH_REPORT.md`
- Updated daily status: `docs/DAILY_STATUS.md`

## Implementation

The cubicle reserve is enabled only by 2P config keys and applies only to `shadow/cubicle`. It requires an unsafe empty/fallback action, active event memory, reuse age >= 8, event score >= 0.80 or foreground-loss score >= 0.60, not final-normal, and a separate reserve cap of 3. It never requests a detector and remains subject to final normal-frame suppression.

The PTZ live mismatch rescue is enabled only by 2P config keys and applies only to `PTZ/intermittentPan`. It requires an unsafe empty/fallback action, active event memory, reuse age >= 8, event score >= 0.85, foreground risk >= 0.80 or localized/global motion risk with memory, not final-normal, and a separate reserve cap of 4. It never requests a detector and is explicitly preserved by the existing intermittentPan cap when active.

New logs include:

- `ai_cubicle_live_mismatch_reserve_active`
- `ai_cubicle_live_mismatch_reserve_reason`
- `ai_cubicle_live_mismatch_reserve_rejected_reason`
- `ai_cubicle_live_mismatch_reserve_frame`
- `ai_cubicle_live_mismatch_reserve_no_detector`
- `ai_cubicle_live_mismatch_reserve_cap_used`
- `ai_ptz_intermittent_pan_live_mismatch_rescue_active`
- `ai_ptz_intermittent_pan_live_mismatch_rescue_reason`
- `ai_ptz_intermittent_pan_live_mismatch_rescue_rejected_reason`
- `ai_ptz_intermittent_pan_live_mismatch_rescue_frame`
- `ai_ptz_intermittent_pan_live_mismatch_rescue_no_detector`
- `ai_ptz_intermittent_pan_live_mismatch_rescue_cap_used`
- `ai_live_mismatch_final_normal_suppressed`

## Commands Run

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2p_dryrun.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2p_dryrun
```

The dry-run command was resumed in bounded 8-job batches until `run_progress.csv` reached 80 completed, 0 failed. No live command was run.

## Aggregate Result

- Jobs: 80/80 completed, 0 failed
- FMeasure: 0.43110
- Event_F1: 0.66604
- Activation: 0.58078
- Avg_FPS: 27.16402
- P95 latency: 233.21158 ms
- Proposed intervention rate: 0.19818
- Detector request rate: 0.01011
- Block-only rate: 0.18807
- Event/foreground block-only rate: 0.15167
- Normal-frame proposals: 0
- Guard alignment: 1.00000

## Dry-Run vs Live Comparison

| Run | FMeasure | Event_F1 | Activation | Avg_FPS | P95 ms | Proposal | Detector | Normal proposals | Guard alignment |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 8C-2O dry-run | 0.40060 | 0.66904 | 0.47128 | 22.57987 | 418.20077 | 0.21587 | 0.01921 | 0 | 1.00000 |
| 8C-2O live | 0.42292 | 0.66650 | 0.47928 | 16.50218 | 484.56976 | 0.23357 | 0.02477 | 0 | 1.00000 |
| 8C-2P dry-run | 0.43110 | 0.66604 | 0.58078 | 27.16402 | 233.21158 | 0.19818 | 0.01011 | 0 | 1.00000 |

## Target Frame Status

| Frame | 8C-2O live audit status | 8C-2P dry-run status | 2P guard behavior |
| --- | --- | --- | --- |
| `shadow/cubicle` frame 1560 | FN, `CLOSED_EMPTY_P3_FALLBACK`, unprotected | TP, `FORCED_REFRESH`, not unprotected | Reserve rejected as `action_not_unsafe_empty_fallback`; this is expected in dry-run because the frame is already safe. |
| `PTZ/intermittentPan` frame 1370 | FN, `CLOSED_EMPTY_ACC`, unprotected | TP, `DETECT_ACC`, not unprotected | Live mismatch rescue rejected as `action_not_unsafe_empty_fallback`; expected because dry-run already uses `DETECT_ACC`. |
| `PTZ/intermittentPan` frame 1375 | FN, `CLOSED_EMPTY_ACC`, unprotected | TP, `DETECT_ACC`, not unprotected | Live mismatch rescue rejected as `action_not_unsafe_empty_fallback`; expected because dry-run already uses `DETECT_ACC`. |

The 2P dry-run therefore verifies compatibility and logging, but it cannot directly prove the live-only final-action mismatch cases because the audited frames are protected before the live mismatch occurs in dry-run.

## 2P Guard Activity

| Video | Cubicle reserve | PTZ mismatch rescue | No-detector count | Final-normal suppressions |
| --- | ---: | ---: | ---: | ---: |
| `shadow/cubicle` | 3 | 0 | 3 | 0 |
| `PTZ/intermittentPan` | 0 | 0 | 0 | 0 |
| `shadow/copyMachine` | 0 | 0 | 0 | 0 |
| `intermittentObjectMotion/parking` | 0 | 0 | 0 | 0 |
| `turbulence/turbulence2` | 0 | 0 | 0 | 0 |
| `lowFramerate/tunnelExit_0_35fps` | 0 | 0 | 0 | 0 |

Cubicle reserve activations occurred on frames 1535, 1540, and 1545. They were no-detector proposals, used the separate reserve cap of 3, and produced 0 compare-defined normal-frame proposals.

## Per-Video Summary

| Video | Proposal | Detector | Normal proposals | Event FN | Unprotected FN | Detector budget max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `PTZ/continuousPan` | 0.04000 | 0.01000 | 0 | 0 | 0 | 1 |
| `PTZ/intermittentPan` | 0.01000 | 0.00000 | 0 | 1 | 0 | 0 |
| `baseline/highway` | 0.02000 | 0.00000 | 0 | 1 | 1 | 0 |
| `baseline/office` | 0.04000 | 0.01000 | 0 | 3 | 0 | 1 |
| `cameraJitter/traffic` | 0.02000 | 0.01000 | 0 | 0 | 0 | 1 |
| `dynamicBackground/canoe` | 0.00000 | 0.00000 | 0 | 0 | 0 | 0 |
| `dynamicBackground/fountain01` | 0.00000 | 0.00000 | 0 | 0 | 0 | 0 |
| `dynamicBackground/fountain02` | 0.40000 | 0.02000 | 0 | 0 | 0 | 2 |
| `dynamicBackground/overpass` | 0.24000 | 0.00000 | 0 | 0 | 0 | 0 |
| `intermittentObjectMotion/parking` | 0.39000 | 0.00000 | 0 | 33 | 9 | 0 |
| `lowFramerate/tramCrossroad_1fps` | 0.00000 | 0.00000 | 0 | 0 | 0 | 0 |
| `lowFramerate/tunnelExit_0_35fps` | 0.31000 | 0.00000 | 0 | 2 | 1 | 0 |
| `lowFramerate/turnpike_0_5fps` | 0.01000 | 0.00000 | 0 | 0 | 0 | 0 |
| `nightVideos/bridgeEntry` | 0.22000 | 0.05000 | 0 | 0 | 0 | 5 |
| `nightVideos/streetCornerAtNight` | 0.10000 | 0.01000 | 0 | 0 | 0 | 1 |
| `nightVideos/tramStation` | 0.14000 | 0.03000 | 0 | 0 | 0 | 3 |
| `shadow/backdoor` | 0.40000 | 0.04000 | 0 | 0 | 0 | 4 |
| `shadow/copyMachine` | 0.38000 | 0.00000 | 0 | 46 | 12 | 0 |
| `shadow/cubicle` | 0.90000 | 0.02000 | 0 | 14 | 0 | 2 |
| `turbulence/turbulence2` | 0.30000 | 0.00000 | 0 | 3 | 1 | 0 |

## Carry-Over Risk Status

| Video | 8C-2O dry-run | 8C-2O live | 8C-2P dry-run | Status |
| --- | --- | --- | --- | --- |
| `shadow/cubicle` | recall 0.87879, unprotected FN 0 | recall 0.81818, unprotected FN 1 | recall 0.90909, unprotected FN 0 | Dry-run passes; live retry still needed to validate mismatch reserve. |
| `PTZ/intermittentPan` | proposal 0.01000, unprotected FN 0 | proposal 0.05000, unprotected FN 2 | proposal 0.01000, unprotected FN 0 | Dry-run passes; live retry still needed to validate mismatch rescue. |
| `shadow/copyMachine` | unprotected FN 12 | unprotected FN 18 | unprotected FN 12 | Carry-over unchanged from accepted dry-run residual; live issue not fixed in 2P. |
| `intermittentObjectMotion/parking` | proposal 0.43000, unprotected FN 9 | proposal 0.43000, unprotected FN 14 | proposal 0.39000, unprotected FN 9 | Carry-over within dry-run gate; live issue not fixed in 2P. |
| `turbulence/turbulence2` | unprotected FN 2 | unprotected FN 1 | proposal 0.30000, unprotected FN 1 | Within 2O acceptable gate. |
| `lowFramerate/tunnelExit_0_35fps` | unprotected FN 1 | unprotected FN 1 | proposal 0.31000, unprotected FN 1 | Within 2O acceptable gate. |

## Gate Table

| Gate | 2P result | Status |
| --- | --- | --- |
| 80/80 completed, 0 failed | 80/80, 0 failed | Pass |
| Aggregate detector request rate < 0.10 | 0.01011 | Pass |
| Normal-frame proposals = 0 | 0 | Pass |
| Guard alignment >= 0.95 | 1.00000 | Pass |
| Cubicle recall >= 0.80 and unprotected FN = 0 | 0.90909, 0 | Pass |
| IntermittentPan proposal <= 0.15 and unprotected FN = 0 | 0.01000, 0 | Pass |
| ContinuousPan proposal <= 0.05 | 0.04000 | Pass |
| BridgeEntry event FN = 0 | 0 | Pass |
| TramCrossroad_1fps controlled | proposal/detector 0.00000/0.00000 | Pass |
| Fountain01 quiet | proposal/detector 0.00000/0.00000 | Pass |
| Fountain02 normal false interventions = 0 | 0 | Pass |
| CopyMachine does not regress beyond accepted residuals | unprotected FN 12 | Pass acceptable |
| Parking does not regress beyond accepted residuals | proposal 0.39000, unprotected FN 9 | Pass |
| Turbulence2 remains within 2O acceptable gate | proposal 0.30000, unprotected FN 1 | Pass |
| TunnelExit remains within 2O acceptable gate | proposal 0.31000, unprotected FN 1 | Pass |
| No forbidden validation launched | none launched | Pass |

## Conclusion

8C-2P passes targeted category dry-run gates. Live remains held because this phase was dry-run-only and because `shadow/copyMachine` and `intermittentObjectMotion/parking` still have documented live failures that were intentionally not patched here.

Recommended next action: patch the remaining live-sensitive cap-exhaustion residuals for `shadow/copyMachine` and `intermittentObjectMotion/parking` in a separate dry-run phase before authorizing a targeted category live retry. Step 4 full CDnet dry-run remains held.
