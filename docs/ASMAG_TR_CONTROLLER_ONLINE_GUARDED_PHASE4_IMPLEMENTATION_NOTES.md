# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 4 Implementation Notes

Date: 2026-05-09

Scope: guarded-only Phase 4 GMQ-Guard implementation for `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`.

## What Was Implemented

Phase 4 added the smallest GMQ-Guard bundle to the guarded pipeline only:

- GMQ diagnostic columns in guarded `frame_metrics.csv` and `edge_profile.csv`.
- Label-free candidate mask quality scoring for P3, ACC, and FAST candidate masks.
- P3/lightweight fallback veto telemetry and action blocking under persistent global-motion risk.
- Capped legacy-online safe branch labeled `LEGACY_SAFE_P3_GUARD`.
- Prediction-history event-continuity guard for low-light active-event risk.
- Motion-compensation config placeholders, disabled by default.
- Comparison-tool GMQ summaries:
  - `gmq_action_summary.csv`
  - `gmq_quality_summary.csv`
  - `gmq_legacy_safe_summary.csv`
  - `gmq_event_continuity_summary.csv`

The implementation is guarded by `online_controller_guarded` config parameters and is only executed when `pipeline_name == "ASMAG_TR_CONTROLLER_ONLINE_GUARDED"`.

## What Was Not Implemented

- No dense optical flow.
- No ECC alignment.
- No sparse optical-flow affine estimator.
- No deep segmentation model.
- No policy retraining.
- No modification to old `ONLINE_CALIBRATED`.
- No modification to P1/P2/P3/FAST/controller source behavior.
- No targeted CDnet, full CDnet, LASIESTA, SBI2015, or BMC run.

## GMQ Quality Computation

For each P3, ACC, and FAST candidate mask, GMQ computes:

- area ratio
- connected-component count
- largest-component ratio
- coarse-grid occupancy
- border/edge-touch ratio
- temporal IoU with the previous accepted prediction mask
- cross-candidate disagreement
- final candidate quality score

The quality score rewards object-like components, temporal consistency, candidate agreement, stable area, and limited spread. It penalizes whole-frame motion, scattered components, border-dominated masks, and high candidate disagreement under global-motion risk.

## P3 Veto

P3/lightweight fallback is vetoed when persistent global-motion risk is high and P3 trust is weak:

- low `gmq_p3_quality`
- high P3 spatial spread
- high P3/ACC/FAST disagreement
- low background reliability

When vetoed, `gmq_p3_veto_active=1` and the action reason includes `gmq_p3_veto`. If another candidate has better quality, the guarded controller may switch to that candidate. Otherwise the legacy-safe branch can be considered.

## Legacy-Safe Branch

The legacy-safe branch is guarded-only and does not call or modify old `ONLINE_CALIBRATED`. It approximates the old online behavior by allowing a capped P3 detector-refresh burst under persistent global-motion risk and candidate quality conflict.

Config caps:

- `gmq_legacy_safe_min_interval_frames`
- `gmq_legacy_safe_max_burst_frames`
- `gmq_legacy_safe_cooldown_frames`
- `gmq_legacy_safe_branch_quality_threshold`

Frames using this branch are labeled `LEGACY_SAFE_P3_GUARD` and log `gmq_legacy_safe_branch_active=1`.

## Event-Continuity Guard

The event-continuity guard uses prediction history, not ground truth or video names. It tracks recent active predictions with:

- `active_event_memory`
- `frames_since_active_prediction`
- `gmq_event_continuity_risk`

When low-light active-event risk is high and evidence is not confidently empty, the guard blocks closed-empty behavior if possible. It may request reuse, lightweight update, or a cadence-limited ACC refresh. It logs:

- `gmq_closed_empty_veto_active`
- `closed_empty_blocked_by_event_guard`
- `event_guard_reason`

## Motion Compensation

Motion compensation remains disabled in Phase 4:

- `gmq_motion_compensation_enabled: false`
- `gmq_motion_compensation_method: "phase_correlation_shift"`
- `gmq_motion_compensation_resize_width: 160`

Per-frame logs set `gmq_motion_compensation_enabled=0` and `gmq_motion_residual_ratio=0.0`. This keeps the first Phase 4 bundle focused on arbitration and avoids introducing optical-flow/ECC runtime or failure modes.

## Validation Run

Commands run:

```bash
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_smoke.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_smoke
```

Only the guarded smoke rows were reset to pending for the actual rerun. The comparison baselines in the guarded-smoke output folder were reused from the existing smoke run.

## Smoke Result

| Pipeline | FMeasure | Event_F1 | Activation | FPS | P95 latency ms |
|---|---:|---:|---:|---:|---:|
| ONLINE_CALIBRATED | 0.4155 | 0.5636 | 0.6150 | 18.56 | 405.04 |
| ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 4 | 0.4305 | 0.5576 | 0.4562 | 22.25 | 308.64 |

`PTZ/continuousPan`:

| FMeasure | Event_F1 | Activation | FPS | P95 latency ms | closed-empty rate | legacy-safe rate | P3 veto rate |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.1505 | 0.2523 | 0.43 | 11.83 | 407.59 | 0.06 | 0.30 | 0.96 |

`nightVideos/bridgeEntry`:

| FMeasure | Event_F1 | Activation | FPS | P95 latency ms | closed-empty rate | event-continuity veto rate |
|---:|---:|---:|---:|---:|---:|---:|
| 0.1854 | 0.8506 | 0.56 | 11.92 | 314.65 | 0.21 | 0.05 |

## Phase 4 Outcome

Phase 4 does not pass smoke acceptance.

Failure reasons:

- Aggregate Event_F1 is below old `ONLINE_CALIBRATED`.
- Aggregate FPS is below the required 35.
- `continuousPan` FMeasure improved from Phase 3 but remains 0.0842 below old online, exceeding the allowed 0.02 gap.
- `continuousPan` activation is 0.43, below the required 0.50 unless FMeasure is recovered.
- `bridgeEntry` Event_F1 regressed materially and still has 21 `CLOSED_EMPTY_ACC` event false negatives.

Root-cause interpretation:

- GMQ correctly identifies candidate conflict in `continuousPan` (`gmq_p3_veto_active=0.96`) and invokes the legacy-safe branch on 30% of frames, but the branch is not enough to recover old-online-like recall/precision and increases latency.
- The candidate quality estimator selects ACC as best for 98% of `continuousPan` frames, but ACC actions still do not recover P3/controller FMeasure.
- The event-continuity guard is too weak in the first implementation: it blocks only 5 `bridgeEntry` frames while 21 closed-empty event FNs remain.

Stop decision: do not proceed to targeted CDnet.
