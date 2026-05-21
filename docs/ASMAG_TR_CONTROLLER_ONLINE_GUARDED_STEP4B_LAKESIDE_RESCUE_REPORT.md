# ASMAG-TRC Step 4B lakeSide No-Detector FN Rescue Report

Date: 2026-05-16

## Executive Summary

Step 4B implemented a narrow no-detector `thermal/lakeSide` FN rescue on top of the frozen 8C-2Q2 guarded policy stack and ran only the requested residual-risk subset dry-run.

The rescue succeeded on the primary FN-safety mechanism: `thermal/lakeSide` unprotected event FN improved from 21 to 0, with detector request remaining 0.00000 and normal-frame proposals remaining 0. However, the rescue was too permissive under the phase's proposal-pressure discipline: `lakeSide` proposal rate rose from 0.40000 to 0.60000, above the accepted 0.50000 ceiling stated for this phase.

Decision: Step 4B subset dry-run is not a clean pass. Full CDnet rerun remains held. The narrow next fix is to add or lower a `thermal/lakeSide` rescue proposal-pressure cap so the rescue protects only the highest-priority cap-exhausted/early-memory frames, targeting proposal <= 0.50000 while keeping detector request 0 and unprotected FN <= 12.

## Safety Audit

No live validation, live compare, full CDnet run, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

The run used a separate Step 4B residual-risk subset dry-run config and output root:

- `configs/asmag_tr_controller_online_guarded_cdnet_step4b_lakeside_risk_subset_dryrun.yaml`
- `outputs/asmag_tr_controller_online_guarded_cdnet_step4b_lakeside_risk_subset_dryrun/`

The default guarded config remained unchanged with `ai_intervention_enabled: false`. Baseline pipelines and frozen full-CDnet/targeted-category outputs were not overwritten.

## Planned Subset Scope

Dataset root:

`D:/THS Programing/06.6 ASMAG Project/dataset cdnet2014/archive/dataset`

Subset scope:

| Item | Count |
|---|---:|
| Categories | 9 |
| Videos | 14 |
| Pipelines | 4 |
| Planned jobs | 56 |
| Completed jobs | 56 |
| Failed jobs | 0 |

Videos:

| Category | Video |
|---|---|
| `thermal` | `lakeSide` |
| `intermittentObjectMotion` | `sofa` |
| `badWeather` | `snowFall` |
| `lowFramerate` | `port_0_17fps` |
| `intermittentObjectMotion` | `parking` |
| `shadow` | `copyMachine` |
| `turbulence` | `turbulence2` |
| `lowFramerate` | `tunnelExit_0_35fps` |
| `shadow` | `cubicle` |
| `PTZ` | `continuousPan` |
| `PTZ` | `intermittentPan` |
| `dynamicBackground` | `fountain01` |
| `dynamicBackground` | `fountain02` |
| `nightVideos` | `bridgeEntry` |

## Aggregate Subset Metrics

Official guarded subset metrics:

| Metric | Value |
|---|---:|
| FMeasure | 0.35061 |
| Event_F1 | 0.67692 |
| Activation / proposed activation | 0.52429 |
| Avg_FPS | 38.36761 |
| P95 latency | 219.14120 ms |
| Proposed intervention rate | 0.32786 |
| Proposed detector request rate | 0.01571 |
| Block-only rate | 0.31214 |
| Event/foreground block-only rate | 0.25643 |
| Normal-frame proposals | 0 |
| Guard alignment | 1.00000 |

The aggregate detector, normal-frame, and guard-alignment controls remained strong.

## lakeSide Before/After

| Run | Proposal | Detector | Event FN | Protected FN | Unprotected FN | Normal proposals |
|---|---:|---:|---:|---:|---:|---:|
| Step 4 full CDnet 2Q2 dry-run | 0.40000 | 0.00000 | 48 | 27 | 21 | 0 |
| Step 4B subset dry-run | 0.60000 | 0.00000 | 48 | 48 | 0 | 0 |

Interpretation:

- The rescue converted all 21 previously unprotected `lakeSide` event FNs into protected event FNs.
- Detector request stayed at 0.00000.
- Normal-frame proposals stayed at 0.
- Proposal rate increased by 0.20000, exceeding the intended Step 4B acceptance ceiling of 0.50000.

## lakeSide Rescue Behavior

| Metric | Value |
|---|---:|
| Cap-exhausted rescue candidate frames | 25 |
| Main rescue candidate frames | 22 |
| Main rescue active frames | 15 |
| Main rescue no-detector frames | 15 |
| Main rescue protected event-FN frames | 15 |
| Main rescue cap used max | 15 |
| Main rescue final-normal suppressions | 0 |
| Early-memory candidate frames | 48 |
| Early-memory active frames | 3 |
| Early-memory protected event-FN frames | 3 |
| Final-normal suppressed frames | 0 |

Main rescue active reasons:

| Reason | Frames |
|---|---:|
| exact target + unsafe empty/fallback + cap/budget exhausted + active memory + event score + foreground-loss score + foreground risk + event-FN risk | 7 |
| exact target + unsafe empty/fallback + cap/budget exhausted + active memory + foreground-loss score + foreground risk + event-FN risk | 8 |

Rejected main rescue reasons:

| Reason | Frames |
|---|---:|
| already protected | 42 |
| action not unsafe empty/fallback | 12 |
| cap not exhausted | 3 |

Root cause of Step 4B miss:

The thermal rescue cap was large enough to protect every audited FN, but no final proposal-pressure ceiling stopped the rescue at the accepted `lakeSide` rate. The next patch should keep the same exact-video/no-detector conditions and add a final thermal rescue proposal ceiling or lower effective rescue cap, likely protecting about 10 of the 21 previously unprotected FN frames to target proposal 0.50000 and acceptable unprotected FN <= 12.

## Carry-Over Status

| Video | Proposal | Detector | Event FN | Protected FN | Unprotected FN | Normal proposals | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| `intermittentObjectMotion/sofa` | 0.20000 | 0.04000 | 21 | 11 | 10 | 0 | Watch, unchanged residual risk. |
| `badWeather/snowFall` | 0.29000 | 0.03000 | 22 | 12 | 10 | 0 | Watch, unchanged residual risk. |
| `lowFramerate/port_0_17fps` | 0.37000 | 0.07000 | 5 | 5 | 0 | 0 | Watch, detector pressure remains. |
| `intermittentObjectMotion/parking` | 0.50000 | 0.00000 | 33 | 29 | 4 | 0 | Pass under protection-aware parking gate. |
| `shadow/copyMachine` | 0.46000 | 0.00000 | 46 | 42 | 4 | 0 | Pass under accepted copyMachine gate. |
| `turbulence/turbulence2` | 0.31000 | 0.00000 | 3 | 3 | 0 | 0 | Pass. |
| `lowFramerate/tunnelExit_0_35fps` | 0.31000 | 0.00000 | 2 | 1 | 1 | 0 | Pass. |
| `shadow/cubicle` | 0.90000 | 0.02000 | 14 | 14 | 0 | 0 | Pass, recall 0.90909. |
| `PTZ/continuousPan` | 0.05000 | 0.01000 | 0 | 0 | 0 | 0 | Pass at cap. |
| `PTZ/intermittentPan` | 0.01000 | 0.00000 | 1 | 1 | 0 | 0 | Pass. |
| `dynamicBackground/fountain01` | 0.00000 | 0.00000 | 0 | 0 | 0 | 0 | Pass, quiet. |
| `dynamicBackground/fountain02` | 0.40000 | 0.01000 | 0 | 0 | 0 | 0 | Pass, no normal-frame false interventions. |
| `nightVideos/bridgeEntry` | 0.19000 | 0.04000 | 0 | 0 | 0 | 0 | Pass, event FN 0. |

## Gate Evaluation

| Gate | Result | Status |
|---|---|---|
| All planned subset jobs complete, 0 failed | 56/56 completed, 0 failed | PASS |
| Aggregate detector request rate < 0.10 | 0.01571 | PASS |
| Normal-frame proposals = 0 | 0 | PASS |
| Guard alignment >= 0.95 | 1.00000 | PASS |
| `lakeSide` detector request = 0 or <= 0.02 | 0.00000 | PASS |
| `lakeSide` unprotected FN improves materially versus 21 | 21 -> 0 | PASS |
| Preferred `lakeSide` unprotected FN <= 8 | 0 | PASS |
| Acceptable `lakeSide` unprotected FN <= 12 | 0 | PASS |
| Hard fail if `lakeSide` unprotected FN >= 21 | 0 | PASS |
| `lakeSide` proposal pressure accepted up to 0.50 | 0.60000 | FAIL |
| No final-normal suppressor regression | normal proposals 0, rescue final-normal suppressions 0 | PASS |
| Parking remains within protection-aware gate | proposal 0.50000, detector 0.00000, unprotected FN 4 | PASS |
| copyMachine remains within accepted gate | detector 0.00000, unprotected FN 4 | PASS |
| turbulence2 remains within accepted gate | proposal 0.31000, detector 0.00000, unprotected FN 0 | PASS |
| tunnelExit remains within accepted gate | proposal 0.31000, detector 0.00000, unprotected FN 1 | PASS |
| cubicle recall >= 0.80 and FN 0 | recall 0.90909, unprotected FN 0 | PASS |
| continuousPan remains controlled | proposal 0.05000, detector 0.01000 | PASS |
| intermittentPan remains controlled | proposal 0.01000, unprotected FN 0 | PASS |
| fountain01 remains quiet | proposal/detector 0.00000/0.00000 | PASS |
| fountain02 normal-frame false interventions = 0 | 0 | PASS |
| bridgeEntry event FN = 0 | 0 | PASS |
| No forbidden validation launched | dry-run subset only | PASS |

Overall: Step 4B subset dry-run fails as a clean phase gate because `thermal/lakeSide` proposal pressure exceeded the accepted 0.50000 ceiling.

## Decision

Step 4B subset dry-run does not pass cleanly. The thermal rescue is effective and detector-sparse, but too broad in proposal pressure.

Recommended next action:

1. Add a `thermal/lakeSide` rescue proposal-pressure ceiling or lower effective thermal rescue cap.
2. Preserve exact-video scope, no-detector behavior, final-normal suppressor ordering, and all 8C-2Q2 carry-over guards.
3. Rerun only the Step 4B residual-risk subset dry-run after the narrow cap correction.

Full CDnet rerun remains held. Full CDnet live, cross-dataset validation, and edge profiling remain held.
