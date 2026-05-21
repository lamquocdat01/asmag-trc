# ASMAG-TR Controller Online Guarded Phase 8C-2Q Live Cap-Exhaustion Reserve Report

Date: 2026-05-15

## Executive summary

Phase 8C-2Q implemented a dry-run-only, no-detector live cap-exhaustion reserve for `shadow/copyMachine` and `intermittentObjectMotion/parking` on top of the 8C-2P policy stack.

The targeted 20-video dry-run completed technically: 80/80 jobs completed, 0 failed. The intended copyMachine and parking residuals improved materially, detector requests stayed sparse, and normal-frame proposals remained 0.

However, 8C-2Q does not pass targeted category dry-run gates because `turbulence/turbulence2` regressed from the 8C-2P accepted carry-over state of 1 unprotected FN to 3 unprotected FNs. No live validation was run.

## Scope and safety confirmation

- Scope: targeted category dry-run only.
- Config: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2q_dryrun.yaml`.
- Output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2q_dryrun/`.
- No live validation, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.
- Previous 8C outputs and accidental 8C-2E live artifacts were not deleted or overwritten.
- Default guarded config remains unchanged with `ai_intervention_enabled: false`.

## Implementation summary

Added exact no-detector reserves in `src/run_experiment.py`:

- `shadow/copyMachine`: `ai_copymachine_live_cap_reserve_*`, separate cap 8, no detector, exact target video, unsafe empty/fallback action, active event memory, reuse/score gate, final-normal suppressor preserved.
- `intermittentObjectMotion/parking`: `ai_parking_live_cap_reserve_*`, separate cap 8, no detector, exact target video, unsafe empty/fallback action, active memory/reuse or high score.
- `intermittentObjectMotion/parking` burst bridge: `ai_parking_live_burst_bridge_*`, separate cap 5, no detector, exact target video, reuse-age/foreground-risk bridge after recent parking preserve/rescue sequence.
- Post-preservation trim skips live reserve/bridge frames and logs `ai_live_reserve_trim_skipped`.

Updated compare reporting in `tools/compare_asmag_tr_controller_online_guarded.py`:

- Added the new reserve/bridge columns to frame ingestion.
- Added `ai_intervention_2q_live_cap_reserve_summary.csv`.

## Run result

- Compile: passed.
- Dry-run command: `python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2q_dryrun.yaml --max-jobs-per-run 8`.
- Resume batches completed: 80/80 jobs, 0 failed.
- Compare command: `python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2q_dryrun`.
- Compare result: completed and wrote guarded comparison files.

## Aggregate metrics

For `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`:

- FMeasure: 0.43084
- Event_F1: 0.66386
- Activation: 0.57292
- Avg_FPS: 31.94125
- P95 latency: 229.94988 ms
- Proposal/intervention rate: 0.21537
- Detector request rate: 0.01112
- Block-only rate: 0.20425
- Event/foreground block-only rate: 0.16835
- Normal-frame proposals: 0
- Guard alignment: 1.00000

## Reserve behavior

| Video | 2P proposal/detector/FN | 2Q proposal/detector/FN | New reserve behavior |
| --- | ---: | ---: | --- |
| `shadow/copyMachine` | 0.38000 / 0.00000 / 12 | 0.46000 / 0.00000 / 4 | 8 reserve activations, 8 protected FN, no detector impact |
| `intermittentObjectMotion/parking` | 0.39000 / 0.00000 / 9 | 0.50000 / 0.00000 / 4 | 8 live reserve activations, 5 reserve-protected FN, burst bridge 0 in dry-run, no detector impact, 8 trim skips, 0 reserve frames trimmed |

The parking burst bridge did not activate in dry-run because the low-score live gap pattern was not reproduced; it remains available for the live-sensitive gap described by the Step 3B live failure audit.

## Carry-over status

| Video | Proposal | Detector | Normal proposals | Unprotected FN | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| `shadow/cubicle` | 0.90000 | 0.02000 | 0 | 0 | Pass |
| `PTZ/intermittentPan` | 0.01000 | 0.00000 | 0 | 0 | Pass |
| `PTZ/continuousPan` | 0.05000 | 0.01000 | 0 | 0 | Pass |
| `nightVideos/bridgeEntry` | 0.24000 | 0.05000 | 0 | 0 event FN | Pass |
| `lowFramerate/tramCrossroad_1fps` | 0.00000 | 0.00000 | 0 | 0 | Pass |
| `dynamicBackground/fountain01` | 0.00000 | 0.00000 | 0 | 0 | Pass |
| `dynamicBackground/fountain02` | 0.40000 | 0.01000 | 0 | 0 | Pass |
| `turbulence/turbulence2` | 0.30000 | 0.00000 | 0 | 3 | Fail: accepted gate is <= 2 |
| `lowFramerate/tunnelExit_0_35fps` | 0.30000 | 0.00000 | 0 | 1 | Pass |

## Turbulence2 regression note

The 8C-2P dry-run had `turbulence/turbulence2` event FN count 3, protected FN count 2, and unprotected FN count 1. The 8C-2Q dry-run has event FN count 5, protected FN count 2, and unprotected FN count 3.

New unprotected FN frames in 8C-2Q compared with 8C-2P:

| Frame | 2P status | 2Q status | 2Q action | 2Q rescue rejection |
| ---: | --- | --- | --- | --- |
| 950 | TP, `DETECT_ACC` | FN | `CLOSED_EMPTY_ACC` | `rescue_cap_exhausted` |
| 975 | TP, `DETECT_ACC` | FN | `CLOSED_EMPTY_ACC` | `rescue_cap_exhausted` |
| 985 | FN | FN | `CLOSED_EMPTY_ACC` | `rescue_cap_exhausted` |

The new 2Q reserve paths are exact-scoped to copyMachine and parking and were inactive for turbulence2. The immediate failing mechanism in the 2Q run is turbulence2 rescue cap exhaustion under carry-over behavior, not a detector-heavy path.

## Gate table

| Gate | Result | Status |
| --- | --- | --- |
| 80/80 completed, 0 failed | 80/80, 0 failed | Pass |
| Aggregate detector request rate < 0.10 | 0.01112 | Pass |
| Normal-frame proposals = 0 | 0 | Pass |
| Guard alignment >= 0.95 | 1.00000 | Pass |
| Cubicle recall >= 0.80 and unprotected FN = 0 | recall 0.90909, FN 0 | Pass |
| IntermittentPan proposal <= 0.15 and unprotected FN = 0 | 0.01000, FN 0 | Pass |
| ContinuousPan proposal <= 0.05 | 0.05000 | Pass |
| BridgeEntry event FN = 0 | 0 | Pass |
| TramCrossroad_1fps controlled | 0.00000 / 0.00000 | Pass |
| Fountain01 quiet | 0.00000 / 0.00000 | Pass |
| Fountain02 normal false interventions = 0 | 0 | Pass |
| CopyMachine unprotected FN <= 15 | 4 | Pass |
| Parking unprotected FN <= 12 | 4 | Pass |
| CopyMachine detector request <= 0.02 | 0.00000 | Pass |
| Parking detector request <= 0.02 | 0.00000 | Pass |
| Turbulence2 remains within 2O accepted gate | FN 3, gate <= 2 | Fail |
| TunnelExit remains within accepted gate | FN 1 | Pass |
| No forbidden validation launched | Confirmed | Pass |

## Decision

8C-2Q targeted category dry-run does not pass because of the turbulence2 carry-over regression. Live remains held.

Recommended next action: do not run Step 3B live retry yet. First perform a narrow dry-run-only carry-over audit for `turbulence/turbulence2` under the current 2Q code path, then decide whether to restore the 2P/2O accepted turbulence2 behavior with the smallest possible targeted adjustment. Do not broaden detector policy, and do not alter copyMachine or parking reserves unless later evidence shows they caused a direct regression.
