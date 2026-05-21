# ASMAG-TRC Step 4B2 lakeSide Rescue Pressure Trim Report

Date: 2026-05-17

## Executive Summary

Step 4B2 added a dry-run-only `thermal/lakeSide` post-rescue pressure trim and optional rescue-cap refine path on top of the frozen 8C-2Q2 guarded policy stack plus Step 4B lakeSide rescue behavior.

The residual-risk subset dry-run completed technically: 56/56 planned jobs completed, 0 failed. The run is not a clean phase pass. `thermal/lakeSide` event-FN protection remained materially improved versus Step 4 full CDnet, but proposal pressure worsened to 0.63000, above the accepted 0.50000 ceiling. The trim found 0 safe soft candidates and suppressed 0 frames because every proposed lakeSide frame was hard-protected by the configured safety rules.

Decision: Step 4B2 subset dry-run fails. Full CDnet rerun remains held. The narrow next fix should not run full CDnet; it should first separate foreground-loss-only generic pressure from true event-FN protection on `thermal/lakeSide`, or explicitly revise the cap-refine policy with an accepted FN/proposal tradeoff.

## Safety Audit

No live validation, live compare, full CDnet run, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

The run used a separate Step 4B2 residual-risk subset dry-run config and output root:

- `configs/asmag_tr_controller_online_guarded_cdnet_step4b2_lakeside_risk_subset_dryrun.yaml`
- `outputs/asmag_tr_controller_online_guarded_cdnet_step4b2_lakeside_risk_subset_dryrun/`

The default guarded config remained unchanged with `ai_intervention_enabled: false`. Existing Step 4 and Step 4B outputs were not deleted or overwritten.

## Planned Subset Scope

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

| Metric | Value |
|---|---:|
| FMeasure | 0.34097 |
| Event_F1 | 0.67414 |
| Activation / proposed activation | 0.49929 |
| Avg_FPS | 27.38296 |
| P95 latency | 305.14125 ms |
| Proposed intervention rate | 0.34286 |
| Proposed detector request rate | 0.01786 |
| Block-only rate | 0.32500 |
| Event/foreground block-only rate | 0.26714 |
| Normal-frame proposals | 0 |
| Guard alignment | 1.00000 |

The aggregate detector, normal-frame, and guard-alignment gates stayed intact. The phase failed on the lakeSide proposal gate.

## lakeSide Step 4 / Step 4B / Step 4B2

| Run | Proposal | Detector | Event FN | Protected FN | Unprotected FN | Normal proposals |
|---|---:|---:|---:|---:|---:|---:|
| Step 4 full CDnet 2Q2 dry-run | 0.40000 | 0.00000 | 48 | 27 | 21 | 0 |
| Step 4B subset dry-run | 0.60000 | 0.00000 | 48 | 48 | 0 | 0 |
| Step 4B2 subset dry-run | 0.63000 | 0.01000 | 52 | 50 | 2 | 0 |

Step 4B2 still materially improves unprotected event FN versus Step 4 full CDnet, from 21 to 2. It does not preserve the Step 4B proposal discipline problem; instead, proposal rises further from 0.60000 to 0.63000. The lakeSide detector request rate is within the explicit <=0.02000 gate, but the rescue and trim paths themselves remained no-detector.

## lakeSide Trim Behavior

| Metric | Value |
|---|---:|
| Main rescue active frames | 16 |
| Main rescue no-detector frames | 16 |
| Main rescue protected event-FN frames | 16 |
| Early-memory rescue active frames | 4 |
| Early-memory protected event-FN frames | 4 |
| Newly protected event-FN frames | 20 |
| Trim candidate frames | 0 |
| Soft trim candidate frames | 0 |
| Trim suppressed frames | 0 |
| Trim count | 0 |
| Hard-protected frames | 63 |
| Skipped hard-protected frames | 63 |
| Skipped FN-protected frames | 0 |
| Accidental hard-protected trim count | 0 |
| Final proposal rate | 0.63000 |
| Rescue cap refine active frames | 0 |
| Final-normal suppressions | 0 |

Root cause:

- 50 lakeSide proposed frames were rejected from trimming as hard-protected likely event-FN / unprotected-FN risk.
- 12 additional proposed frames were rejected as hard-protected only. Frame audit shows these had `active_event_memory = 1` and `ai_foreground_loss_risk_score = 1.0`, which matches the Step 4B2 hard-protect rule `foreground_loss >= 0.90` with active memory.
- 1 proposed frame also carried an existing detector request and was rejected by the no-detector trim rule.
- Therefore, the trim had zero legal soft candidates under the requested hard-protection rules.
- Optional cap refine did not fire because the configured cap `18` is above the actual main-rescue activation count `16`, and all active main rescues protected event-FN frames.

The hard-protected safety check worked: accidental hard-protected trim count stayed 0. The pressure-reduction objective did not work because the policy made all over-ceiling proposals non-trimmable.

## Carry-Over Status

| Video | Proposal | Detector | Event FN | Protected FN | Unprotected FN | Status |
|---|---:|---:|---:|---:|---:|---|
| `sofa` | 0.27000 | 0.05000 | 21 | 11 | 10 | Residual watch/patch item, unchanged in scope |
| `snowFall` | 0.35000 | 0.04000 | 23 | 13 | 10 | Residual watch/patch item, unchanged in scope |
| `port_0_17fps` | 0.37000 | 0.07000 | 5 | 5 | 0 | Residual watch/patch item, detector watch remains |
| `parking` | 0.50000 | 0.00000 | 33 | 29 | 4 | Within protection-aware gate |
| `copyMachine` | 0.46000 | 0.00000 | 46 | 42 | 4 | Within accepted gate |
| `turbulence2` | 0.31000 | 0.00000 | 3 | 3 | 0 | Within accepted gate |
| `tunnelExit_0_35fps` | 0.37000 | 0.00000 | 2 | 2 | 0 | Within accepted gate |
| `cubicle` | 0.90000 | 0.02000 | 14 | 14 | 0 | Recall 0.90909, FN protection gate passes |
| `continuousPan` | 0.04000 | 0.01000 | 0 | 0 | 0 | Controlled |
| `intermittentPan` | 0.01000 | 0.00000 | 1 | 1 | 0 | Controlled |
| `fountain01` | 0.00000 | 0.00000 | 0 | 0 | 0 | Quiet |
| `fountain02` | 0.40000 | 0.01000 | 0 | 0 | 0 | Normal-frame false interventions 0 |
| `bridgeEntry` | 0.19000 | 0.04000 | 0 | 0 | 0 | Event FN 0 |

## Gate Result

| Gate | Result | Evidence |
|---|---|---|
| All planned subset jobs completed, 0 failed | PASS | 56/56 completed, 0 failed |
| Aggregate detector request rate < 0.10 | PASS | 0.01786 |
| Normal-frame proposals = 0 | PASS | 0 |
| Guard alignment >= 0.95 | PASS | 1.00000 |
| lakeSide detector request = 0 or <= 0.02 | PASS | 0.01000 |
| lakeSide proposal <= 0.50 | FAIL | 0.63000 |
| lakeSide unprotected FN improves materially versus 21 | PASS | 2 |
| Preferred lakeSide unprotected FN <= 8 | PASS | 2 |
| Accidental hard-protected trim count = 0 | PASS | 0 |
| No final normal suppressor regression | PASS | 0 final-normal suppressions |
| parking protection-aware gate | PASS | proposal 0.50000, detector 0.00000, unprotected FN 4 |
| copyMachine accepted gate | PASS | proposal 0.46000, detector 0.00000, unprotected FN 4 |
| turbulence2 accepted gate | PASS | proposal 0.31000, detector 0.00000, unprotected FN 0 |
| tunnelExit accepted gate | PASS | proposal 0.37000, detector 0.00000, unprotected FN 0 |
| cubicle recall/FN gate | PASS | recall 0.90909, unprotected FN 0 |
| continuousPan controlled | PASS | proposal 0.04000 |
| intermittentPan controlled | PASS | proposal 0.01000, unprotected FN 0 |
| fountain01 quiet | PASS | proposal 0.00000 |
| fountain02 normal-frame false interventions = 0 | PASS | 0 |
| bridgeEntry event FN = 0 | PASS | 0 |
| No forbidden validation launched | PASS | dry-run subset + compare only |

## Next Fix Recommendation

Stop here for Step 4B2. Do not run full CDnet from this result.

The narrow next patch should address the no-candidate condition before another subset dry-run:

1. Audit the 12 over-ceiling `lakeSide` frames that are hard-protected only by foreground-loss score and active memory.
2. If those frames are accepted as non-critical pressure, add an explicit `thermal/lakeSide` foreground-loss-only pressure reducer before hard-protect classification, with no detector request and no effect on event-FN, likely-unprotected-FN, early-memory FN, emergency, or final-normal behavior.
3. If the foreground-loss hard-protect rule is non-negotiable, proposal <= 0.50000 is not reachable by post-rescue trim under the current safety definition. The only remaining lever is an explicit accepted tradeoff in the main rescue cap, likely raising unprotected FN from 2 toward the acceptable ceiling.

Recommendation: Step 4C sofa patch should wait until the lakeSide pressure definition is resolved, because Step 4B2 did not stabilize lakeSide. Full CDnet rerun remains held.
