# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8C-2H2 Pre-Signal Report

Date: 2026-05-13

Status: smoke dry-run passed; targeted mini dry-run failed. Live remains held.

## Scope

Phase 8C-2H2 adds an exact-cubicle event-FN pre-signal before the early normal-frame suppressor. The pre-signal only bypasses the early suppressor for exact `shadow/cubicle` event-FN risk frames so they can continue into the 8C-2H no-detector stabilizer. The final normal-frame suppressor remains enabled after all proposal paths.

No live, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.

## Files And Outputs

Configs:

- `configs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2h2_dryrun.yaml`
- `configs/asmag_tr_controller_online_guarded_cdnet_targeted_mini_2h2_dryrun.yaml`

Output roots:

- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2h2_dryrun/`
- `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_mini_2h2_dryrun/`

## Commands

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2h2_dryrun.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2h2_dryrun
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_targeted_mini_2h2_dryrun.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_targeted_mini_2h2_dryrun
```

The targeted mini dry-run was launched only after the smoke dry-run passed.

## Smoke Dry-Run Metrics

| Metric | 8C-2H | 8C-2H2 |
|---|---:|---:|
| Completed / failed jobs | 32 / 0 | 32 / 0 |
| Proposed intervention rate | 0.30875 | 0.31625 |
| Proposed detector request rate | 0.02875 | 0.02625 |
| Block-only rate | n/a | 0.29000 |
| Event/foreground block-only rate | n/a | 0.24750 |
| Normal-frame proposed interventions | 0 | 0 |
| Guard alignment | 1.00000 | 1.00000 |
| Cubicle recall | 0.81818 | 0.83838 |
| Cubicle unprotected event FN | 2 | 0 |
| bridgeEntry event FN | 0 | 0 |
| bridgeEntry detector budget max | 5 | 8 |
| continuousPan proposal rate | 0.05000 | 0.05000 |
| tramCrossroad_1fps proposal rate | 0.02000 | 0.01000 |
| LowFramerate trim reclaimed proposals | 7 | 7 |
| Exact-cubicle pre-signal frames | n/a | 2 |
| Exact-cubicle stabilizer frames | n/a | 2 |

Smoke gate decision: pass. The original 8C-2H blocker is fixed.

## Cubicle Frames 1340 And 1345

| Frame | Event state | Original action | Pre-signal | Early normal bypassed | Stabilizer active | Detector requested | Final normal suppressed | Protected |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1340 | FN | CLOSED_EMPTY_ACC | 1 | 1 | 1 | 0 | 0 | 1 |
| 1345 | FN | CLOSED_EMPTY_ACC | 1 | 1 | 1 | 0 | 0 | 1 |

Both missed 8C-2H frames are now protected by `exact_cubicle_event_fn_stabilizer_no_detector_fallback`.

## Targeted Mini Dry-Run Metrics

| Metric | 8C-2G targeted mini | 8C-2H2 targeted mini |
|---|---:|---:|
| Completed / failed jobs | 24 / 0 | 24 / 0 |
| FMeasure | 0.14941 | 0.32892 |
| Event_F1 | 0.56895 | 0.57127 |
| Activation / proposed activation | 0.72000 | 0.51667 |
| Avg_FPS | 21.37793 | 19.26090 |
| P95 latency ms | 265.74483 | 422.70620 |
| Proposed intervention rate | 0.22167 | 0.35833 |
| Proposed detector request rate | 0.01500 | 0.05833 |
| Block-only rate | 0.20667 | 0.30000 |
| Event/foreground block-only rate | 0.17500 | 0.26333 |
| Normal-frame proposed interventions | 0 | 0 |
| Guard alignment | 1.00000 | 1.00000 |
| Cubicle recall | 0.71717 | 0.82828 |
| Cubicle event FN | 18 | 17 |
| Cubicle proposed event FN | 11 | 17 |
| Cubicle unprotected event FN | 7 | 0 |
| bridgeEntry event FN | 0 | 0 |
| bridgeEntry detector budget max | 4 | 8 |
| continuousPan proposal rate | 0.04000 | 0.05000 |
| tramCrossroad_1fps proposal rate | 0.01000 | 0.18000 |
| LowFramerate trim reclaimed proposals | 7 | 9 |

## Targeted Per-Video Risk Summary

| Video | Proposed intervention | Detector request | Normal-frame proposals | Known-event recall | Event FN / unprotected FN | Detector budget max | Notes |
|---|---:|---:|---:|---:|---:|---:|---|
| `cubicle` | 0.82000 | 0.05000 | 0 | 0.82828 | 17 / 0 | 5 | Cubicle gate recovered; micro-bump remained 8 frames. |
| `bridgeEntry` | 0.32000 | 0.08000 | 0 | 0.32000 | 0 / 0 | 8 | Event FN stayed 0; detector budget at safety max. |
| `continuousPan` | 0.05000 | 0.01000 | 0 | 0.05000 | 0 / 0 | 1 | At preferred cap. |
| `tramCrossroad_1fps` | 0.18000 | 0.05000 | 0 | 0.18182 | 0 / 0 | 5 | LowFramerate trim active, but proposal rate regressed from 0.01000 to 0.18000. |
| `fountain02` | 0.40000 | 0.01000 | 0 | 0.47059 | 0 / 0 | 1 | No normal-frame false interventions. |
| `fountain01` | 0.38000 | 0.15000 | 0 | 0.38000 | 0 / 0 | 15 | Regressed from quiet 8C-2G behavior; generic event/foreground block-only and non-cubicle budget reclaim produced 38 proposals. |

## Gate Table

| Gate | Result |
|---|---|
| Smoke 32/32 completed, 0 failed | pass |
| Smoke proposed intervention rate < 0.35 | pass: 0.31625 |
| Smoke detector request rate < 0.10 | pass: 0.02625 |
| Smoke normal-frame proposed interventions = 0 | pass |
| Smoke cubicle recall >= 0.80 | pass: 0.83838 |
| Smoke cubicle unprotected event FN = 0 | pass |
| Smoke frames 1340 and 1345 protected | pass |
| Smoke bridgeEntry event FN = 0 | pass |
| Smoke continuousPan <= 0.05 | pass: 0.05000 |
| Smoke tramCrossroad_1fps controlled | pass: 0.01000 |
| Targeted 24/24 completed, 0 failed | pass |
| Targeted detector request rate < 0.10 | pass: 0.05833 |
| Targeted normal-frame proposed interventions = 0 | pass |
| Targeted cubicle recall >= 0.80 | pass: 0.82828 |
| Targeted cubicle unprotected event FN = 0 | pass |
| Targeted bridgeEntry event FN = 0 | pass |
| Targeted continuousPan <= 0.05 | pass: 0.05000 |
| Targeted tramCrossroad_1fps remains controlled | fail: 0.18000 versus 0.01000 in 8C-2G targeted mini |
| Targeted fountain02 has 0 normal-frame false interventions | pass |
| Targeted fountain01 does not become noisy | fail: 0.38000 proposals and 0.15000 detector request rate |
| No broad detector-heavy behavior | partial: aggregate detector request is 0.05833, but fountain01 is 0.15000 |
| No forbidden validation launched | pass |

## Root Cause

The 8C-2H2 pre-signal itself is exact-cubicle scoped and did not activate outside `shadow/cubicle`. It fixed the intended smoke failure and recovered targeted cubicle protection.

The targeted mini failure is now non-cubicle pressure:

- `dynamicBackground/fountain01` changed from quiet in 8C-2G targeted mini to 38 proposed interventions and 15 detector requests.
- The fountain01 proposals are generic event/foreground block-only plus non-cubicle budget-reclaim proposals, not exact-cubicle pre-signal/stabilizer proposals.
- `lowFramerate/tramCrossroad_1fps` remained under the aggregate detector gate, but proposal rate rose from 0.01000 to 0.18000 even with 9 trim reclaims.

The next fix should be a narrow non-cubicle targeted-stability cleanup that restores fountain01 quiet behavior and tightens targeted lowFramerate preservation without touching cubicle, bridgeEntry, continuousPan, sparse detector policy, or final normal-frame suppression.

## Decision

8C-2H2 passes smoke dry-run but fails targeted mini dry-run. Live remains held.

Recommended next step: do not authorize targeted mini live yet. Add a follow-up dry-run-only patch focused on non-cubicle proposal pressure:

- Restore quiet behavior for `dynamicBackground/fountain01` by suppressing generic event/foreground block-only and non-cubicle budget-reclaim proposals when they are FP-memory driven and not known safety-critical.
- Re-tighten `lowFramerate/tramCrossroad_1fps` targeted preservation so the trim does not preserve 18 proposals in the targeted mini set.
- Keep exact-cubicle pre-signal and stabilizer unchanged because they fixed the cubicle gate.
- Re-run smoke dry-run first, then targeted mini dry-run only if smoke passes.
