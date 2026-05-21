# ASMAG-TR Controller Online Guarded Step 4D snowFall Rescue Report

Date: 2026-05-17

## Scope

Step 4D was a dry-run-only residual-risk subset attempt for `badWeather/snowFall` weather-aware no-detector rescue.

- Videos: 14
- Categories: 9
- Pipelines: 4
- Planned jobs: 56
- Completed jobs: 56
- Failed jobs: 0
- Output root: `outputs/asmag_tr_controller_online_guarded_cdnet_step4d_snowfall_risk_subset_dryrun/`
- Config: `configs/asmag_tr_controller_online_guarded_cdnet_step4d_snowfall_risk_subset_dryrun.yaml`

Subset videos:

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

## Safety Audit

No live validation, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

The default guarded config remains unchanged with `ai_intervention_enabled: false`. No ONLINE_CALIBRATED, P1, P2, P3, FAST, or ASMAG_TR_CONTROLLER configs were modified. Existing prior output roots were not deleted or overwritten.

## Aggregate Step 4D Metrics

| Metric | Value |
|---|---:|
| FMeasure | 0.33238 |
| Event_F1 | 0.66485 |
| Activation | 0.47929 |
| Avg_FPS | 25.47992 |
| P95 latency | 368.05579 ms |
| Proposal rate | 0.34143 |
| Detector request rate | 0.01500 |
| Block-only rate | 0.32643 |
| Event/foreground block-only rate | 0.26071 |
| Normal-frame proposals | 0 |
| Guard alignment | 1.00000 |

## snowFall Comparison

| Phase | Proposal | Detector | Event FN | Protected FN | Unprotected FN |
|---|---:|---:|---:|---:|---:|
| Step 4 full 2Q2 | 0.29000 | 0.03000 | 22 | 12 | 10 |
| Step 4D subset | 0.28000 | 0.00000 | 22 | 12 | 10 |

Step 4D did not improve the `snowFall` unprotected-FN residual. Detector pressure improved to 0.00000 and proposal stayed controlled, but the rescue path never activated.

## snowFall Rescue Behavior

The Step 4D rescue was exact-video scoped to `badWeather/snowFall`, no-detector, and kept the final normal-frame suppressor in place.

Observed snowFall counters:

| Counter | Value |
|---|---:|
| Rescue candidates | 0 |
| Rescue activations | 0 |
| Rescue no-detector frames | 0 |
| Rescue cap used | 0 |
| Rescue-protected event-FN frames | 0 |
| Final-normal suppressed rescue frames | 0 |
| Localized guard active frames | 83 |
| Proposal guard active frames | 31 |
| Proposal guard generic suppressions | 0 |
| Proposal guard final rate | 0.28000 |
| Possible mask-quality rows | 0 |

Rejected pre-signal reasons were narrow but too strict for this video: 49 frames were not unsafe empty/fallback actions, 31 were already protected, and 3 were rejected as `cap_not_exhausted`. Frame-level inspection of the remaining 10 unprotected FN rows shows several `CLOSED_EMPTY_ACC` / `CLOSED_EMPTY_P3_FALLBACK` rows with active memory and foreground continuity, but `ai_intervention_budget_blocked=0` and closed-empty budget still available. That means the configured "cap exhausted or closed-empty budget exhausted" condition did not match the observed runtime state.

One event-FN row remains a possible mask-quality exposure by audit context: raw frame 1150 used `DETECT_ACC` and still remained FN. The Step 4D telemetry did not count it as `ai_snowfall_weather_possible_mask_quality_exposure` because the rescue candidate path rejected it as `action_not_unsafe_empty_fallback`.

## Proposal and Detector Behavior

| Metric | Step 4 full 2Q2 | Step 4D |
|---|---:|---:|
| Proposal rate | 0.29000 | 0.28000 |
| Detector request rate | 0.03000 | 0.00000 |
| Normal-frame proposals | 0 | 0 |
| Proposal guard suppressions | n/a | 0 |

Proposal and detector discipline passed for `snowFall`; rescue recall did not.

## Carry-Over Status

| Video | Proposal | Detector | Event FN | Protected FN | Unprotected FN | Normal proposals | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| `thermal/lakeSide` | 0.52000 | 0.00000 | 53 | 48 | 5 | 0 | FAIL: proposal exceeded Step 4B4 gate 0.50000 |
| `intermittentObjectMotion/sofa` | 0.27000 | 0.00000 | 21 | 21 | 0 | 0 | PASS: Step 4C rescue preserved |
| `lowFramerate/port_0_17fps` | 0.37000 | 0.07000 | 5 | 5 | 0 | 0 | Residual detector watch; not patched |
| `intermittentObjectMotion/parking` | 0.50000 | 0.00000 | 33 | 29 | 4 | 0 | PASS: protection-aware gate preserved |
| `shadow/copyMachine` | 0.47000 | 0.00000 | 54 | 39 | 15 | 0 | PASS by accepted proposal/detector gate; FN drift noted |
| `turbulence/turbulence2` | 0.31000 | 0.00000 | 3 | 3 | 0 | 0 | PASS: accepted gate preserved |
| `lowFramerate/tunnelExit_0_35fps` | 0.37000 | 0.00000 | 4 | 1 | 3 | 0 | PASS by detector gate; FN drift noted |
| `shadow/cubicle` | 0.91000 | 0.04000 | 17 | 17 | 0 | 0 | PASS: recall 0.91919 and FN 0 |
| `PTZ/continuousPan` | 0.05000 | 0.01000 | 0 | 0 | 0 | 0 | PASS: controlled |
| `PTZ/intermittentPan` | 0.01000 | 0.00000 | 1 | 1 | 0 | 0 | PASS: controlled |
| `dynamicBackground/fountain01` | 0.00000 | 0.00000 | 0 | 0 | 0 | 0 | PASS: quiet |
| `dynamicBackground/fountain02` | 0.40000 | 0.01000 | 0 | 0 | 0 | 0 | PASS: normal-frame false interventions 0 |
| `nightVideos/bridgeEntry` | 0.32000 | 0.08000 | 0 | 0 | 0 | 0 | PASS: event FN 0 |

## Gate Results

| Gate | Result | Evidence |
|---|---|---|
| All planned subset jobs completed, 0 failed | PASS | 56/56 completed, 0 failed |
| Aggregate detector request rate < 0.10 | PASS | 0.01500 |
| Normal-frame proposals = 0 | PASS | 0 |
| Guard alignment >= 0.95 | PASS | 1.00000 |
| snowFall detector request <= 0.03 | PASS | 0.00000 |
| snowFall proposal <= 0.45 | PASS | 0.28000 |
| snowFall unprotected FN improves materially versus 10 | FAIL | 10 -> 10 |
| preferred snowFall unprotected FN <= 4 | FAIL | 10 |
| acceptable snowFall unprotected FN <= 6 | FAIL | 10 |
| hard fail if snowFall unprotected FN >= 10 | FAIL | 10 |
| no final normal suppressor regression | PASS | 0 final-normal rescue suppressions |
| lakeSide proposal <= 0.50 | FAIL | 0.52000 |
| lakeSide detector <= 0.02 | PASS | 0.00000 |
| lakeSide unprotected FN <= 8 preferred | PASS | 5 |
| sofa proposal <= 0.35 preferred, hard fail > 0.40 | PASS | 0.27000 |
| sofa detector <= 0.03 | PASS | 0.00000 |
| sofa unprotected FN <= 4 preferred | PASS | 0 |
| parking remains within protection-aware gate | PASS | proposal 0.50000, unprotected FN 4 |
| copyMachine remains within accepted gate | PASS | proposal 0.47000, detector 0.00000 |
| turbulence2 remains within accepted gate | PASS | unprotected FN 0 |
| tunnelExit remains within accepted gate | PASS | detector 0.00000 |
| cubicle recall >= 0.80 and FN 0 | PASS | recall 0.91919, unprotected FN 0 |
| continuousPan remains controlled | PASS | proposal 0.05000, event FN 0 |
| intermittentPan remains controlled | PASS | proposal 0.01000, unprotected FN 0 |
| fountain01 remains quiet | PASS | proposal 0.00000 |
| fountain02 normal-frame false interventions = 0 | PASS | 0 |
| bridgeEntry event FN = 0 | PASS | 0 |
| No forbidden validation launched | PASS | dry-run subset and compare only |

## Root Cause and Next Fix

Step 4D is not a clean pass.

The immediate `snowFall` root cause is that the rescue condition required event/foreground cap exhaustion or closed-empty budget exhaustion, but the actual unprotected-FN rows still reported available closed-empty budget and no generic budget block. The rescue therefore saw zero candidates even though several unprotected FN rows had active memory plus foreground-loss / foreground-risk continuity.

The narrow next fix should be Step 4D2 for `badWeather/snowFall` only:

- keep the no-detector exact-video rescue scope
- allow actual `Event_State=FN` plus unsafe closed-empty/fallback action plus active memory and score thresholds to satisfy the rescue pressure condition, even when the logged generic budget is not exhausted
- keep localized guard, proposal ceiling, final-normal suppressor, and no-detector behavior unchanged
- explicitly log the `DETECT_ACC` FN row as a mask-quality exposure even when it is not a rescue candidate

The lakeSide carry-over proposal drift to 0.52000 also blocks the Step 4D pass and should be rechecked before any full CDnet rerun.

## Decision

Step 4D residual-risk subset dry-run fails.

Stop here under the dry-run failure rule. Full CDnet rerun remains held. No Step 4E port retighten or full CDnet rerun should start until `snowFall` rescue candidacy and the `lakeSide` carry-over proposal drift are corrected or explicitly accepted by the team.
