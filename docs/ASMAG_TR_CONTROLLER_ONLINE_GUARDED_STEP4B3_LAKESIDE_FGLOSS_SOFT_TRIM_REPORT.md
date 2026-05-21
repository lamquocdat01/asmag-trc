# ASMAG-TR Controller Online Guarded Step 4B3 lakeSide Foreground-Loss Soft Trim Report

Date: 2026-05-17

## Scope

Step 4B3 was a dry-run-only residual-risk subset pass for `thermal/lakeSide` foreground-loss-only softening.

- Videos: 14
- Categories: 9
- Pipelines: 4
- Planned jobs: 56
- Completed jobs: 56
- Failed jobs: 0
- Output root: `outputs/asmag_tr_controller_online_guarded_cdnet_step4b3_lakeside_risk_subset_dryrun/`
- Config: `configs/asmag_tr_controller_online_guarded_cdnet_step4b3_lakeside_risk_subset_dryrun.yaml`

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

The default guarded config remains unchanged with `ai_intervention_enabled: false`. No ONLINE_CALIBRATED, P1, P2, P3, FAST, or ASMAG_TR_CONTROLLER configs were modified. Existing prior output roots were not deleted.

## Aggregate Step 4B3 Metrics

| Metric | Value |
|---|---:|
| FMeasure | 0.34953 |
| Event_F1 | 0.67446 |
| Activation | 0.52071 |
| Avg_FPS | 30.79529 |
| P95 latency | 293.49922 ms |
| Proposal rate | 0.32286 |
| Detector request rate | 0.01643 |
| Block-only rate | 0.30643 |
| Event/foreground block-only rate | 0.25000 |
| Normal-frame proposals | 0 |
| Guard alignment | 1.00000 |

## thermal/lakeSide Comparison

| Phase | Proposal | Detector | Event FN | Protected FN | Unprotected FN |
|---|---:|---:|---:|---:|---:|
| Step 4 full 2Q2 | 0.40000 | 0.00000 | 48 | 27 | 21 |
| Step 4B subset | 0.60000 | 0.00000 | 48 | 48 | 0 |
| Step 4B2 subset | 0.63000 | 0.01000 | 52 | 50 | 2 |
| Step 4B3 subset | 0.55000 | 0.00000 | 48 | 48 | 0 |

Step 4B3 restored the Step 4B no-detector FN protection behavior and removed the Step 4B2 lakeSide detector request. It did not satisfy the lakeSide proposal ceiling because final lakeSide proposal remained 0.55000 versus the required <= 0.50000.

## lakeSide Hard-Protection Refinement

The Step 4B3 refinement no longer hard-protected foreground-loss by itself. Foreground-loss frames required event score support to remain hard-protected, unless they were likely unprotected-FN risk, rescue-protected, event-FN protected, or deterministic emergency safeguards.

Observed lakeSide counts:

| Counter | Value |
|---|---:|
| Hard-protect refine active frames | 62 |
| Final hard-protected frames | 55 |
| Foreground-loss-only soft candidates | 7 |
| Likely-unprotected-FN hard frames | 48 |
| Event-score + foreground-loss hard frames, not likely-unprotected-FN | 7 |

Hard-protection reason counts:

| Reason | Frames |
|---|---:|
| `likely_unprotected_fn_hard` | 30 |
| `foreground_loss_with_event_score_hard+likely_unprotected_fn_hard` | 5 |
| `event_score_hard+foreground_loss_with_event_score_hard+likely_unprotected_fn_hard` | 13 |
| `event_score_hard+foreground_loss_with_event_score_hard` | 7 |
| `foreground_loss_only_soft` | 7 |

The refinement worked in the intended direction: the prior foreground-loss-only hard bucket became soft, but only 7 such frames existed under the configured event-score split. Reaching the 0.50000 proposal ceiling required suppressing at least 12 frames from the pre-trim proposal set; Step 4B3 exposed only 7 safe soft candidates.

## lakeSide Soft Trim Behavior

| Counter | Value |
|---|---:|
| Main rescue activations | 15 |
| Early-memory activations | 3 |
| Newly protected event-FN frames | 18 |
| Post-rescue trim candidates | 7 |
| Foreground-loss soft trim candidates | 7 |
| Foreground-loss soft trim suppressions | 7 |
| Final proposal rate | 0.55000 |
| Accidental hard-protected trims | 0 |
| Accidental rescue-protected trims | 0 |
| Final-normal suppressor regressions | 0 |

All trimmed frames were low event-score foreground-loss-only candidates. No hard-protected frame was trimmed, no rescue-protected event-FN frame was trimmed, and lakeSide protected event-FN stayed at 48/48.

Soft-trim skip counts:

| Skip reason | Frames |
|---|---:|
| Hard-protected | 55 |
| Likely unprotected FN | 48 |
| Rescue frame | 18 |

## lakeSide Detector Retighten

Step 4B3 lakeSide detector request rate was 0.00000. Detector retighten did not need to suppress any lakeSide detector frame:

| Counter | Value |
|---|---:|
| Detector retighten active frames | 0 |
| Detector retighten count | 0 |
| Final lakeSide detector request rate | 0.00000 |

## Carry-Over Status

| Video | Proposal | Detector | Event FN | Protected FN | Unprotected FN | Normal proposals | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| `intermittentObjectMotion/sofa` | 0.20000 | 0.04000 | 21 | 11 | 10 | 0 | Residual watch/patch item; unchanged phase scope |
| `badWeather/snowFall` | 0.29000 | 0.03000 | 22 | 12 | 10 | 0 | Residual watch/patch item; unchanged phase scope |
| `lowFramerate/port_0_17fps` | 0.40000 | 0.08000 | 6 | 4 | 2 | 0 | Residual watch/patch item; unchanged phase scope |
| `intermittentObjectMotion/parking` | 0.46000 | 0.00000 | 33 | 28 | 5 | 0 | Within protection-aware gate |
| `shadow/copyMachine` | 0.46000 | 0.00000 | 46 | 42 | 4 | 0 | Within accepted gate |
| `turbulence/turbulence2` | 0.31000 | 0.00000 | 3 | 3 | 0 | 0 | Within accepted gate |
| `lowFramerate/tunnelExit_0_35fps` | 0.31000 | 0.00000 | 2 | 1 | 1 | 0 | Within accepted gate |
| `shadow/cubicle` | 0.90000 | 0.02000 | 14 | 14 | 0 | 0 | Recall 0.90909, FN protected |
| `PTZ/continuousPan` | 0.04000 | 0.01000 | 0 | 0 | 0 | 0 | Controlled |
| `PTZ/intermittentPan` | 0.01000 | 0.00000 | 1 | 1 | 0 | 0 | Controlled |
| `dynamicBackground/fountain01` | 0.00000 | 0.00000 | 0 | 0 | 0 | 0 | Quiet |
| `dynamicBackground/fountain02` | 0.40000 | 0.01000 | 0 | 0 | 0 | 0 | Normal-frame false interventions 0 |
| `nightVideos/bridgeEntry` | 0.19000 | 0.04000 | 0 | 0 | 0 | 0 | Event FN 0 |

## Gate Decision

| Gate | Result | Evidence |
|---|---|---|
| All planned subset jobs completed, 0 failed | PASS | 56/56 completed, 0 failed |
| Aggregate detector request rate < 0.10 | PASS | 0.01643 |
| Normal-frame proposals = 0 | PASS | 0 |
| Guard alignment >= 0.95 | PASS | 1.00000 |
| lakeSide detector request = 0 or <= 0.02 | PASS | 0.00000 |
| lakeSide proposal <= 0.50 | FAIL | 0.55000 |
| lakeSide unprotected FN materially improves versus 21 | PASS | 0 |
| Preferred lakeSide unprotected FN <= 8 | PASS | 0 |
| Acceptable lakeSide unprotected FN <= 12 | PASS | 0 |
| Accidental hard-protected trim count = 0 | PASS | 0 |
| Accidental rescue-protected trim count = 0 | PASS | 0 |
| No final-normal suppressor regression | PASS | 0 |
| parking remains within protection-aware gate | PASS | Proposal 0.46000, detector 0.00000, unprotected FN 5 |
| copyMachine remains within accepted gate | PASS | Proposal 0.46000, detector 0.00000, unprotected FN 4 |
| turbulence2 remains within accepted gate | PASS | Proposal 0.31000, detector 0.00000, unprotected FN 0 |
| tunnelExit remains within accepted gate | PASS | Proposal 0.31000, detector 0.00000, unprotected FN 1 |
| cubicle recall >= 0.80 and FN 0 | PASS | Recall 0.90909, unprotected FN 0 |
| continuousPan remains controlled | PASS | Proposal 0.04000 |
| intermittentPan remains controlled | PASS | Proposal 0.01000, unprotected FN 0 |
| fountain01 remains quiet | PASS | Proposal 0.00000 |
| fountain02 normal-frame false interventions = 0 | PASS | 0 |
| bridgeEntry event FN = 0 | PASS | 0 |
| No forbidden validation launched | PASS | Safety audit clean |

Step 4B3 is not a clean subset pass because `thermal/lakeSide` proposal remained above the accepted ceiling.

## Root Cause and Narrow Next Fix

Root cause: the hard-protection refinement exposed only 7 foreground-loss-only soft candidates. All 7 were safely trimmed, but final lakeSide proposal stopped at 0.55000. The remaining five trims needed to reach 0.50000 are inside the residual hard-protected set, especially the 7 `event_score_hard+foreground_loss_with_event_score_hard` frames that are not marked likely-unprotected-FN.

Narrow next fix: audit only those 7 non-likely, non-rescue high-event-score foreground-loss hard frames and introduce a bounded second-tier soft path only if they are not event-FN risk, not rescue-protected, not likely-unprotected-FN, not deterministic emergency safeguards, and not final-normal safety frames. The next patch should target 5 to 7 additional safe lakeSide suppressions, preserve 48/48 protected event FN, and keep detector request at 0.

Full CDnet rerun remains held. Step 4C sofa patch should not start from this exact Step 4B3 state unless the team accepts lakeSide 0.55000 as a temporary residual failure; otherwise the next action should be a narrow Step 4B4 lakeSide high-event foreground-loss audit/soften pass.
