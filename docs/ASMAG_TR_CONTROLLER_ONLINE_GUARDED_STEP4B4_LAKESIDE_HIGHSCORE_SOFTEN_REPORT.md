# ASMAG-TR Controller Online Guarded Step 4B4 lakeSide High-Score Softening Report

Date: 2026-05-17

## Scope

Step 4B4 was a dry-run-only residual-risk subset pass for `thermal/lakeSide` high-score non-FN hard-protection review and softening.

- Videos: 14
- Categories: 9
- Pipelines: 4
- Planned jobs: 56
- Completed jobs: 56
- Failed jobs: 0
- Output root: `outputs/asmag_tr_controller_online_guarded_cdnet_step4b4_lakeside_risk_subset_dryrun/`
- Config: `configs/asmag_tr_controller_online_guarded_cdnet_step4b4_lakeside_risk_subset_dryrun.yaml`

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

## Pre-Change Hard-Protected Candidate Audit

Before changing logic, the Step 4B3 `thermal/lakeSide` frame log was inspected for proposed hard-protected frames that were not event-state FN, not active rescue frames, not early-memory rescue frames, not newly protected event-FN frames, not likely-unprotected-FN, not deterministic emergency safeguards, and not final-normal suppressor frames.

Seven Step 4B3 frames matched the safe review pool. They were retained by high event score plus foreground-loss score, but were TP frames rather than event-FN protection frames:

| Frame | Eval index | Event state | Event score | FG-loss score | Active memory | Recent prediction age | Reuse age | Action | Step 4B3 hard reason |
|---:|---:|---|---:|---:|---:|---:|---:|---|---|
| 1090 | 18 | TP | 0.98309 | 1.00000 | 1 | 1 | 3 | REUSE_ACC | event score + foreground loss |
| 1095 | 19 | TP | 0.98309 | 1.00000 | 1 | 1 | 4 | REUSE_ACC | event score + foreground loss |
| 1105 | 21 | TP | 0.98499 | 1.00000 | 1 | 1 | 1 | REUSE_ACC | event score + foreground loss |
| 1155 | 31 | TP | 0.85962 | 1.00000 | 1 | 1 | 1 | REUSE_ACC | event score + foreground loss |
| 1180 | 36 | TP | 0.99886 | 1.00000 | 1 | 1 | 1 | REUSE_ACC | event score + foreground loss |
| 1255 | 51 | TP | 0.99878 | 1.00000 | 1 | 1 | 1 | REUSE_ACC | event score + foreground loss |
| 1330 | 66 | TP | 0.98396 | 1.00000 | 1 | 1 | 1 | REUSE_ACC | event score + foreground loss |

Step 4B4 treats this class as soft only when it is not event-FN, not rescue-protected, not likely-unprotected-FN, not deterministic emergency, not final-normal, and not tied to a nearby rescue-protected FN context.

## Aggregate Step 4B4 Metrics

| Metric | Value |
|---|---:|
| FMeasure | 0.34462 |
| Event_F1 | 0.65472 |
| Activation | 0.48000 |
| Avg_FPS | 23.35906 |
| P95 latency | 391.63325 ms |
| Proposal rate | 0.32571 |
| Detector request rate | 0.02000 |
| Block-only rate | 0.30571 |
| Event/foreground block-only rate | 0.25143 |
| Normal-frame proposals | 0 |
| Guard alignment | 1.00000 |

## thermal/lakeSide Comparison

| Phase | Proposal | Detector | Event FN | Protected FN | Unprotected FN |
|---|---:|---:|---:|---:|---:|
| Step 4 full 2Q2 | 0.40000 | 0.00000 | 48 | 27 | 21 |
| Step 4B subset | 0.60000 | 0.00000 | 48 | 48 | 0 |
| Step 4B2 subset | 0.63000 | 0.01000 | 52 | 50 | 2 |
| Step 4B3 subset | 0.55000 | 0.00000 | 48 | 48 | 0 |
| Step 4B4 subset | 0.50000 | 0.00000 | 48 | 48 | 0 |

Step 4B4 preserves the successful Step 4B/4B3 lakeSide event-FN protection while meeting the accepted lakeSide proposal ceiling exactly.

## lakeSide High-Score Softening Behavior

The Step 4B4 high-score refinement applies only to `thermal/lakeSide`. Event-FN, rescue-protected, early-memory rescue, likely-unprotected-FN, and deterministic emergency frames remain hard-protected.

Observed lakeSide counters:

| Counter | Value |
|---|---:|
| Hard-protect refine active frames | 62 |
| Final hard-protected frames | 48 |
| Rescue-protected event-FN frames | 15 |
| Early-memory protected event-FN frames | 3 |
| Newly protected event-FN frames | 18 |
| Foreground-loss-only soft candidates | 7 |
| Foreground-loss-only soft trims | 7 |
| High-score soften active frames | 62 |
| High-score soft candidates | 7 |
| High-score soft trims | 5 |
| Total lakeSide trims | 12 |
| Final proposal rate | 0.50000 |

The high-score softener exposed the audited non-FN high-score class without touching the 48 likely-unprotected-FN hard frames. Five of the seven high-score soft candidates were trimmed, which was enough to bring lakeSide from the Step 4B3 0.55000 proposal rate to 0.50000.

## lakeSide Trim Safety

| Safety counter | Value |
|---|---:|
| Accidental hard-protected trims | 0 |
| Accidental rescue-protected trims | 0 |
| Foreground-loss trim accidental hard-protected trims | 0 |
| Foreground-loss trim accidental rescue trims | 0 |
| High-score trim accidental hard-protected trims | 0 |
| High-score trim accidental rescue trims | 0 |
| Final-normal suppressor regressions | 0 |

Skip counters show the protection walls remained active:

| Skip reason | Frames |
|---|---:|
| Foreground-loss trim skipped hard-protected | 48 |
| Foreground-loss trim skipped likely-unprotected-FN | 48 |
| Foreground-loss trim skipped rescue frame | 18 |
| High-score trim skipped hard-protected | 48 |
| High-score trim skipped likely-unprotected-FN | 48 |
| High-score trim skipped rescue frame | 18 |

Detector pressure did not increase from lakeSide logic. lakeSide detector request rate ended at 0.00000 and detector retighten had 0 active frames.

## Carry-Over Status

| Video | Proposal | Detector | Event FN | Protected FN | Unprotected FN | Normal proposals | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| `intermittentObjectMotion/sofa` | 0.21000 | 0.04000 | 22 | 12 | 10 | 0 | Residual watch/Step 4C patch item |
| `badWeather/snowFall` | 0.29000 | 0.03000 | 22 | 12 | 10 | 0 | Residual watch/patch item |
| `lowFramerate/port_0_17fps` | 0.40000 | 0.07000 | 14 | 10 | 4 | 0 | Residual watch/patch item |
| `intermittentObjectMotion/parking` | 0.46000 | 0.00000 | 34 | 27 | 7 | 0 | Within protection-aware gate |
| `shadow/copyMachine` | 0.46000 | 0.00000 | 47 | 42 | 5 | 0 | Within accepted gate |
| `turbulence/turbulence2` | 0.31000 | 0.00000 | 3 | 3 | 0 | 0 | Within accepted gate |
| `lowFramerate/tunnelExit_0_35fps` | 0.31000 | 0.00000 | 2 | 1 | 1 | 0 | Within accepted gate |
| `shadow/cubicle` | 0.92000 | 0.06000 | 19 | 19 | 0 | 0 | Recall 0.92929, unprotected FN 0 |
| `PTZ/continuousPan` | 0.05000 | 0.01000 | 0 | 0 | 0 | 0 | Controlled |
| `PTZ/intermittentPan` | 0.03000 | 0.00000 | 3 | 3 | 0 | 0 | Controlled |
| `dynamicBackground/fountain01` | 0.00000 | 0.00000 | 0 | 0 | 0 | 0 | Quiet |
| `dynamicBackground/fountain02` | 0.40000 | 0.02000 | 0 | 0 | 0 | 0 | Normal-frame false interventions 0 |
| `nightVideos/bridgeEntry` | 0.22000 | 0.05000 | 0 | 0 | 0 | 0 | Event FN 0 |

## Gate Table

| Gate | Result | Status |
|---|---:|---|
| Planned subset jobs completed | 56/56 | PASS |
| Failed jobs | 0 | PASS |
| Aggregate detector request rate < 0.10 | 0.02000 | PASS |
| Normal-frame proposals = 0 | 0 | PASS |
| Guard alignment >= 0.95 | 1.00000 | PASS |
| lakeSide detector request = 0 or <= 0.02 | 0.00000 | PASS |
| lakeSide proposal <= 0.50 | 0.50000 | PASS |
| lakeSide unprotected FN materially improves vs 21 | 0 | PASS |
| Preferred lakeSide unprotected FN <= 8 | 0 | PASS |
| Accidental hard-protected trim count = 0 | 0 | PASS |
| Accidental rescue-protected trim count = 0 | 0 | PASS |
| No final-normal suppressor regression | 0 | PASS |
| parking within protection-aware gate | proposal 0.46000, detector 0.00000 | PASS |
| copyMachine within accepted gate | proposal 0.46000, detector 0.00000 | PASS |
| turbulence2 within accepted gate | proposal 0.31000, detector 0.00000 | PASS |
| tunnelExit within accepted gate | proposal 0.31000, detector 0.00000 | PASS |
| cubicle recall >= 0.80 and unprotected FN 0 | recall 0.92929, unprotected FN 0 | PASS |
| continuousPan controlled | proposal 0.05000 | PASS |
| intermittentPan controlled | proposal 0.03000 | PASS |
| fountain01 quiet | proposal 0.00000 | PASS |
| fountain02 normal-frame false interventions = 0 | 0 | PASS |
| bridgeEntry event FN = 0 | 0 | PASS |
| No forbidden validation launched | dry-run subset only | PASS |

## Decision

Step 4B4 residual-risk subset dry-run passes.

The lakeSide stabilization target is met: proposal 0.50000, detector 0.00000, event FN 48, protected FN 48, unprotected FN 0, accidental hard-protected trims 0, accidental rescue-protected trims 0, and no final-normal suppressor regression.

Full CDnet rerun remains held. The recommended next step is Step 4C sofa patch before a full CDnet rerun, unless the team chooses an interim full dry-run specifically to freeze lakeSide stabilization.
