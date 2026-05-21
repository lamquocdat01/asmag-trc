# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 4 Validation Protocol

Date: 2026-05-09

Scope: validation protocol for a future Phase 4 implementation of `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`. This document does not run or authorize any experiment by itself.

## Validation Principles

- Do not modify old `ONLINE_CALIBRATED`.
- Do not overwrite frozen CDnet2014 v1.6 outputs.
- Do not run targeted CDnet until smoke passes.
- Do not run full CDnet until targeted CDnet passes.
- Do not run LASIESTA, SBI2015, or BMC until full CDnet validates the guarded design.
- Every validation stage must write to a new output folder.
- If aggregate improves but `PTZ/continuousPan` remains catastrophic, stop.

## Stage 0: Research-to-Implementation Readiness

Before implementation starts, confirm that the design includes:

- GMQ-Guard score logging.
- Candidate mask quality estimator.
- P3 fallback/lightweight veto.
- Event-continuity guard.
- Narrow legacy-online safe branch.
- Optional, disabled-by-default motion compensation probe.

Do not proceed if the implementation plan is only threshold tuning.

## Stage 1: Smoke Test

Smoke videos:

| Category | Video | Purpose |
|---|---|---|
| PTZ | continuousPan | Primary hard blocker; persistent global motion. |
| PTZ | twoPositionPTZCam | PTZ control case that should not be harmed. |
| nightVideos | bridgeEntry | Low-light/event-continuity blocker. |
| dynamicBackground | fountain02 | Dynamic background where Phase 3 speed helps. |
| shadow | backdoor | Runtime/action safety check; low FMeasure across pipelines. |
| shadow | cubicle | Shadow plus event/mask fragmentation. |
| turbulence | turbulence2 | Dynamic/turbulence benefit case. |
| lowFramerate | tramCrossroad_1fps | High-refresh low-frame-rate case. |

Required command shape after implementation is explicitly requested:

```bash
python src/run_experiment.py --config configs/asmag_tr_controller_online_guarded_cdnet_smoke.yaml --max-jobs-per-run 8
python tools/compare_asmag_tr_controller_online_guarded.py --root outputs/asmag_tr_controller_online_guarded_cdnet_smoke
```

No smoke rerun was performed for this research-only task.

## Smoke Acceptance Criteria

Hard requirements:

- No crashes.
- All Phase 2 and Phase 3 diagnostic columns still present.
- All GMQ-Guard diagnostic columns present.
- Aggregate FMeasure >= old `ONLINE_CALIBRATED`.
- Aggregate Event_F1 >= old `ONLINE_CALIBRATED`.
- Aggregate FPS >= 35.
- Aggregate P95 latency <= old `ONLINE_CALIBRATED + 30 ms`; prefer <= 300 ms.
- `PTZ/continuousPan` FMeasure no worse than old `ONLINE_CALIBRATED` by more than 0.02.
- `PTZ/continuousPan` activation >= 0.50 unless FMeasure is already recovered.
- `PTZ/continuousPan` closed-empty rate remains 0 or near 0.
- `nightVideos/bridgeEntry` Event_F1 no worse than old `ONLINE_CALIBRATED` by more than 0.02.
- `nightVideos/bridgeEntry` must not have long `CLOSED_EMPTY_ACC` runs during active-event memory.

Soft preferences:

- `bridgeEntry` FMeasure gap vs old online shrinks or remains within 0.01.
- `twoPositionPTZCam` FMeasure does not regress by more than 0.02 vs Phase 3.
- `fountain02` keeps most Phase 3 FPS improvement.
- `turbulence2` remains better than old online.

Stop conditions:

- Any crash.
- Missing GMQ diagnostics.
- `continuousPan` FMeasure remains below old online by more than 0.02.
- `continuousPan` recovers only by pushing aggregate FPS below 35 or aggregate P95 above acceptance.
- `bridgeEntry` Event_F1 remains materially below old online because of closed-empty event FNs.
- Any old `ONLINE_CALIBRATED` output changes unexpectedly.

## Required GMQ Diagnostic Columns

Minimum new columns expected after implementation:

| Column | Purpose |
|---|---|
| `gmq_guard_active` | Whether the Phase 4 arbitration layer affected action selection. |
| `gmq_action_score` | Final risk score of chosen action. |
| `gmq_action_reason` | Short reason for selected action. |
| `gmq_global_motion_risk` | Risk that raw motion is camera/background dominated. |
| `gmq_background_reliability` | Trust in background model candidates. |
| `gmq_p3_quality` | P3 candidate mask quality. |
| `gmq_acc_quality` | ACC candidate mask quality. |
| `gmq_fast_quality` | FAST candidate mask quality. |
| `gmq_candidate_disagreement` | Cross-candidate mask disagreement. |
| `gmq_temporal_consistency` | Candidate consistency with prior accepted mask. |
| `gmq_spatial_spread` | Whole-frame/scattered spread indicator. |
| `gmq_event_continuity_risk` | Risk of breaking an active event. |
| `gmq_p3_veto_active` | Whether P3/lightweight P3 was blocked. |
| `gmq_closed_empty_veto_active` | Whether closed-empty was blocked. |
| `gmq_legacy_safe_branch_active` | Whether guarded approximated old online behavior. |
| `gmq_motion_compensation_enabled` | Whether optional compensation was used. |
| `gmq_motion_residual_ratio` | Residual motion after optional alignment. |

## Targeted CDnet Criteria

Targeted CDnet is allowed only after smoke passes all hard requirements.

Targeted scope should include smoke videos plus nearby hard videos from:

- PTZ
- cameraJitter
- dynamicBackground
- turbulence
- shadow
- nightVideos
- lowFramerate
- badWeather if runtime budget allows

Targeted acceptance:

- No crash.
- No frozen output overwrite.
- Aggregate targeted FMeasure >= old online.
- Aggregate targeted Event_F1 >= old online.
- `continuousPan` remains non-catastrophic.
- No new severe per-video regression greater than -0.05 FMeasure vs old online unless old online is also near-zero and the failure is documented.
- P95 latency does not exceed old online by more than 30 ms.
- GMQ branch usage is explainable: it should activate in PTZ/global motion and low-light/event-risk cases, not everywhere.

Failure stop conditions:

- `continuousPan` regresses after passing smoke.
- GMQ legacy-safe branch becomes a broad P3-always policy.
- Event continuity improves but aggregate latency collapses.
- New failures appear in dynamicBackground or turbulence due to overzealous PTZ logic.

## Full CDnet Criteria

Full CDnet is allowed only after targeted CDnet passes.

Full CDnet target criteria:

- FMeasure >= old `ONLINE_CALIBRATED`.
- Event_F1 >= old `ONLINE_CALIBRATED`.
- Prefer FMeasure within 0.02 of `P3_MOG2` or `ASMAG_TR_CONTROLLER`.
- Activation lower than P3/controller.
- FPS substantially higher than old online.
- P95 latency lower than old online.
- No category-specific catastrophic regression.
- No dependency on CDnet category names inside guarded action logic.
- GMQ diagnostics complete enough to explain top per-video wins and losses.

Full CDnet stop conditions:

- Any hard category, especially PTZ, turbulence, dynamicBackground, nightVideos, shadow, or lowFramerate, regresses catastrophically.
- GMQ behavior cannot be explained by label-free signals.
- Runtime gains disappear because legacy-safe branch is overused.

## Cross-Dataset Gate Criteria

Run LASIESTA, SBI2015, and BMC only after full CDnet validates Phase 4.

Cross-dataset prerequisites:

- Full CDnet Phase 4 report exists.
- No known unresolved PTZ/global-motion blocker.
- No known unresolved low-light/event-continuity blocker.
- GMQ features do not use CDnet category or video names.
- Config is frozen except for dataset paths/output roots.

Cross-dataset acceptance:

- No crash.
- No output overwrite.
- GMQ logs present.
- Accuracy-efficiency trade-off remains better than old online where comparable.
- Failures are explainable by label-free signals, not dataset-name assumptions.

## Reporting Template

Every validation report should include:

1. Aggregate comparison table.
2. `continuousPan` before/after with FMeasure, Event_F1, activation, FPS, P95, closed-empty, and GMQ actions.
3. `bridgeEntry` before/after with FMeasure, Event_F1, activation, FPS, P95, closed-empty event FNs.
4. Hard-scene taxonomy table.
5. GMQ action distribution.
6. GMQ score distributions.
7. Stop/pass decision.
8. Whether the next validation stage is allowed.

## Current Decision

Based on Phase 3 evidence, targeted CDnet is not allowed yet. Phase 4 implementation should begin only with the smallest GMQ-Guard bundle and then rerun smoke.
