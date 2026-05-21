# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Changelog

Date: 2026-05-09

## Phase 7B Teacher-Distilled PTZ Ranked Action Policy

Phase 7B is scoped only to `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`. It implements a deterministic, rollback-configurable teacher-distilled action ranker for confirmed PTZ/global-motion states; it does not deploy a learned classifier and does not add new heavy geometry or deep models.

Added guarded-only mechanisms:

- Added `teacher_ranker_enabled`, `teacher_ranker_behavior_enabled`, and `teacher_ranker_scope` controls.
- Added deterministic safety guards that block closed-empty under active event/global motion, block `REUSE_ACC` under non-high trust, block `LIGHTWEIGHT_MASK_P3_FALLBACK` under PTZ low/medium trust, and require detector-like execution for `LEGACY_SAFE_P3_GUARD`.
- Added trust-state action ranking: low trust prefers `FALLBACK_P3_GUARD`/`DETECT_ACC`, medium trust allows quality-gated `LIGHTWEIGHT_MASK_ACC`, and high trust allows quality-gated `LIGHTWEIGHT_MASK_ACC` plus tightly gated short-age `REUSE_ACC`.
- Added continuous-pan teacher telemetry and anchor/inter-anchor action logging.
- Preserved Phase 6C position-switch protection by suppressing continuous-pan ranker behavior during jump/reset/low-inlier states and forcing detector bursts.
- Preserved bridgeEntry and non-PTZ safety by suppressing teacher behavior when there is no confirmed camera-motion scope.
- Added comparison outputs: `teacher_ranker_summary.csv`, `teacher_action_summary.csv`, `teacher_safety_guard_summary.csv`, and `teacher_continuous_pan_summary.csv`.

Added Phase 7B diagnostic columns:

- `teacher_ranker_active`
- `teacher_ranker_scope_reason`
- `teacher_ranker_behavior_applied`
- `teacher_safety_guard_active`
- `teacher_safety_guard_reason`
- `teacher_blocked_action`
- `teacher_blocked_reason`
- `teacher_ranker_trust_state`
- `teacher_ranked_candidates`
- `teacher_top_candidate`
- `teacher_selected_action_before`
- `teacher_selected_action_after`
- `teacher_ranker_reason`
- `continuous_pan_teacher_policy_active`
- `continuous_pan_teacher_anchor_action`
- `continuous_pan_teacher_inter_anchor_action`
- `continuous_pan_teacher_blocked_reuse`
- `continuous_pan_teacher_blocked_lightweight_p3`
- `continuous_pan_teacher_blocked_legacy_weak`
- `teacher_position_switch_protection_active`
- `teacher_position_switch_reason`
- `teacher_position_switch_detector_burst`
- `teacher_position_switch_exit_to_fast_path`
- `teacher_event_behavior_suppressed`
- `teacher_bridge_event_safety_preserved`
- `teacher_non_ptz_suppressed`
- `teacher_non_ptz_suppression_reason`

## Phase 6C Bounded PTZ Geometry Compensation

Phase 6C is scoped only to `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`. It adds a bounded ORB + partial-affine geometry probe for confirmed PTZ/camera-motion risk frames after Phase 6B-5 showed that reuse, closed-empty, and anchor cadence were no longer the remaining blockers.

Added guarded-only mechanisms:

- Added `orb_affine_partial` geometry probing on downscaled grayscale frames with ORB features, RANSAC partial affine estimation, inlier checks, and a compute budget.
- Added affine-compensated mask trust metrics against P3/ACC/FAST candidates, including residual ratio, trust score, trust band, and improvement over translation-only compensation.
- Added geometry-aware action selection so high trust can allow reuse, medium trust can allow `LIGHTWEIGHT_MASK_ACC`, and low trust blocks reuse/lightweight P3 in favor of detector-like anchors.
- Added geometry-aware position-switch telemetry and detector-burst support for jump/scale/rotation instability.
- Preserved event safety and non-PTZ suppression with explicit event-only and non-PTZ behavior suppression diagnostics.
- Added comparison outputs: `geometry_probe_summary.csv`, `geometry_trust_summary.csv`, and `geometry_action_summary.csv`.

Dense optical flow and deep models remain excluded.

## Phase 6B-5 Continuous-Pan No-Reuse Anchor Policy

Phase 6B-5 is scoped only to `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`. It keeps the Phase 6B-4 aggregate wins, bridgeEntry event safety, and non-PTZ suppression while correcting the continuous-pan and position-switch video failures.

Added guarded-only mechanisms:

- Split continuous-pan trust into real high trust, relaxed medium trust, and low trust. `REUSE_ACC` is allowed only under real high trust.
- Added a continuous-pan reuse cap and replacement path so relaxed-trust reuse is converted to `LIGHTWEIGHT_MASK_ACC` when candidate quality is acceptable, otherwise to a detector-like anchor.
- Restored a stronger detector-like anchor cadence for continuous-pan scenes with an interval of 2 frames and a target anchor band near 0.50 to 0.60.
- Preferred `LIGHTWEIGHT_MASK_ACC` between anchors and kept `LIGHTWEIGHT_MASK_P3_FALLBACK` blocked in continuous-pan.
- Strengthened position-switch exclusion so jump/reset or unstable shift windows suppress continuous-pan signature, trust relaxation, and anchor cadence.
- Added `continuous_pan_policy_summary.csv` with action-rate, trust-rate, reuse-block, and position-switch suppression telemetry.

New Phase 6B-5 diagnostic columns include:

- `continuous_pan_real_high_trust`
- `continuous_pan_relaxed_medium_trust`
- `continuous_pan_reuse_blocked_by_relaxed_trust`
- `continuous_pan_reuse_block_reason`
- `continuous_pan_reuse_cap_active`
- `continuous_pan_reuse_replaced`
- `continuous_pan_reuse_replacement_action`
- `continuous_pan_reuse_rate_window`
- `continuous_pan_detector_anchor_rate_window`
- `continuous_pan_anchor_rate_too_low`
- `continuous_pan_anchor_rate_too_high`
- `continuous_pan_anchor_rate_corrected`
- `continuous_pan_inter_anchor_lightweight_acc_selected`
- `continuous_pan_suppressed_by_shift_instability`
- `continuous_pan_suppressed_by_position_switch`
- `position_switch_override_used`

Affine, scale, ECC, homography, sparse matching, dense optical flow, and new deep models remain postponed.

## Phase 6B-4 Continuous-Pan Trust Calibration and Anchor Cadence

Phase 6B-4 is scoped only to `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`. It keeps Phase 6B-3 event safety, position-switch reset, and non-PTZ suppression intact while targeting the narrow continuousPan smoke blocker.

Added guarded-only mechanisms:

- Added a runtime continuous-pan signature from persistent confirmed camera motion and stable translation shift history, with suppression for position-switch resets, strong jump-like behavior, zoom/scale suspicion, and non-PTZ scenes.
- Added continuous-pan trust relaxation so recent detector anchors plus stable shift trends can promote otherwise low compensated trust to medium trust without changing the normal trust-band rules.
- Added continuous-pan anchor cadence so detector-like legacy-safe frames are retained as periodic anchors while inter-anchor frames prefer `LIGHTWEIGHT_MASK_ACC`.
- Blocked `LIGHTWEIGHT_MASK_P3_FALLBACK` in continuous-pan inter-anchor frames and restricted `REUSE_ACC` to a short recent-anchor window.
- Added comparison summary fields for continuous-pan signature, trust relaxation, anchor cadence, inter-anchor replacement, legacy-safe thinning, lightweight-P3 blocking, and position-switch suppression.

New Phase 6B-4 diagnostic columns include:

- `continuous_pan_signature_active`
- `continuous_pan_signature_reason`
- `continuous_pan_shift_stability`
- `continuous_pan_blocked_by_position_switch`
- `continuous_pan_blocked_by_zoom_scale`
- `continuous_pan_trust_relaxed`
- `continuous_pan_trust_relaxation_reason`
- `continuous_pan_anchor_recent`
- `continuous_pan_frames_since_anchor`
- `continuous_pan_anchor_cadence_active`
- `continuous_pan_anchor_due`
- `continuous_pan_anchor_action`
- `continuous_pan_inter_anchor_action`
- `continuous_pan_legacy_safe_rate_window`
- `continuous_pan_legacy_safe_thinned`
- `continuous_pan_lightweight_acc_used`
- `continuous_pan_lightweight_p3_blocked`
- `continuous_pan_reuse_acc_used`
- `continuous_pan_rules_suppressed_for_position_switch`
- `continuous_pan_rules_suppressed_non_ptz`

Affine, scale, ECC, homography, sparse matching, dense optical flow, and new deep models remain postponed.

## Phase 6B-3 Detector Cadence Thinning + Trust-Band Action Selection

Phase 6B-3 keeps all behavior scoped to `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`. Old `ONLINE_CALIBRATED`, P1/P2/P3, `ASMAG_TR_FAST`, and `ASMAG_TR_CONTROLLER` remain unchanged.

Added guarded-only mechanisms:

- Replaced binary compensated-trust handling with `high`, `medium`, `low`, and `unknown` trust bands using compensated IoU, residual ratio, phase response, and candidate disagreement.
- Added PTZ detector-cadence thinning so medium/high trust camera-motion frames can replace repeated `LEGACY_SAFE_P3_GUARD` with `LIGHTWEIGHT_MASK_ACC` or `REUSE_ACC` between detector-like refreshes.
- Added event-safe cadence thinning so active low-light event windows can use `REUSE_ACC` or `LIGHTWEIGHT_MASK_ACC` between `DETECT_ACC` refreshes while preserving closed-empty event safety.
- Added short position-switch reset telemetry and detector-burst arbitration for jump-like camera motion, without adding affine, scale, ECC, homography, sparse matching, or optical flow.
- Tightened non-PTZ motion-comp behavior with a forced-off cap so cubicle-like non-PTZ scenes do not receive broad PTZ-style behavior.
- Added comparison summary fields and `cadence_thinning_summary.csv` for trust bands, detector-like action rates, thinning replacements, event-safe thinning, position-switch reset, and non-PTZ forced-off counts.

Added Phase 6B-3 diagnostic columns:

- `motion_comp_trust_band`
- `motion_comp_trust_band_reason`
- `ptz_cadence_thinning_active`
- `ptz_cadence_thinning_reason`
- `detector_like_action_thinned`
- `replacement_action_after_thinning`
- `ptz_legacy_safe_rate_window`
- `event_safe_cadence_thinning_active`
- `event_detect_acc_thinned`
- `event_replacement_action`
- `event_detect_acc_rate_window`
- `position_switch_reset_active`
- `position_switch_reset_reason`
- `position_switch_reset_age`
- `position_switch_exit_to_fast_path`
- `position_switch_detector_burst_active`
- `non_ptz_motion_comp_behavior_forced_off`
- `non_ptz_motion_comp_behavior_reason`

Phase 6B-3 must be validated by smoke only before PTZ-targeted validation is considered.

## Phase 6B Motion-Compensation-Informed Trust Layer

- Added guarded-only, risk-gated phase-correlation diagnostics for `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`.
- Added compensated temporal IoU and residual-motion diagnostics.
- Added PTZ detector-floor arbitration when camera-motion risk is high and compensation is unreliable.
- Added zoom/scale and camera-jump suspicion flags without implementing affine, ECC, homography, dense optical flow, or scale compensation.
- Added motion-compensation-based stale reuse and lightweight-mask invalidation.
- Added label-free non-PTZ GMQ restriction diagnostics so broad GMQ behavior can be held back when camera-motion/event evidence is weak.
- Added a separate low-framerate cadence guard.
- Added comparison summaries: `motion_comp_summary.csv`, `ptz_motion_comp_summary.csv`, and `low_framerate_guard_summary.csv`.
- Updated only the guarded smoke config behavior parameters for Phase 6B validation.
- Old `ONLINE_CALIBRATED`, P1/P2/P3, `ASMAG_TR_FAST`, and `ASMAG_TR_CONTROLLER` remain unchanged.

## Summary

`ASMAG_TR_CONTROLLER_ONLINE_GUARDED` is an upgraded version of P4-Online / `ONLINE_CALIBRATED`. It is added as a new side-by-side pipeline so the old calibrated online behavior remains available for direct comparison.

## What Changed

- Added the new pipeline ID `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`.
- Preserved old `ONLINE_CALIBRATED` behavior unchanged.
- Added a shared guarded gate feature path for the new pipeline only.
- Added hard P3 guards driven by label-free motion disagreement, scene uncertainty, gate instability, and foreground-risk proxies.
- Restored hysteresis and mode-switch budgeting for the guarded path.
- Added low-activation forced refresh logic.
- Added reuse age decay through `max_reuse_age` and `reuse_confidence`.
- Added per-frame diagnostics required for guarded online debugging.
- Added smoke and full CDnet configs that write only to new output folders.
- Added a comparison tool for guarded-vs-old-online/P3/controller reporting.

## Safety Notes

- `P1_YOLO_Only` was not changed.
- `P2_FrameDiff` was not changed.
- `P3_MOG2` was not changed.
- `ASMAG_TR_FAST` was not changed.
- `ASMAG_TR_CONTROLLER` was not changed.
- Old `ONLINE_CALIBRATED` behavior is preserved unchanged.
- Frozen CDnet2014 v1.6 outputs are not overwritten.
- New smoke outputs go to `outputs/asmag_tr_controller_online_guarded_cdnet_smoke/`.
- New full outputs are configured for `outputs/asmag_tr_controller_online_guarded_cdnet_full/`, but the full run must not be launched until smoke and targeted validation pass.

## Purpose

The purpose of `ASMAG_TR_CONTROLLER_ONLINE_GUARDED` is to validate a more robust guarded online controller before running LASIESTA, SBI2015, and BMC. The guarded path targets better hard-scene robustness, less mode thrashing, lower stale reuse risk, and better runtime stability than old `ONLINE_CALIBRATED`.

## New Diagnostics

The guarded path logs:

- `action_label`
- `action_reason`
- `selected_mode_before_guard`
- `selected_mode_after_guard`
- `previous_mode`
- `desired_mode`
- `mode_switch_reason`
- `candidate_FAST_gate_open`
- `candidate_ACC_gate_open`
- `candidate_P3_gate_open`
- `candidate_FAST_gate_score`
- `candidate_ACC_gate_score`
- `candidate_P3_gate_score`
- `candidate_FAST_area`
- `candidate_ACC_area`
- `candidate_P3_area`
- `cache_hit_gate_features`
- `gate_compute_resolution`
- `reuse_age`
- `reuse_confidence`
- `motion_disagreement`
- `latency_gate_features_ms`
- `latency_policy_ms`
- `latency_gate_select_ms`
- `latency_detector_ms`
- `latency_mask_postprocess_ms`
- `latency_metrics_ms`
- `latency_logging_ms`

## New Files

- `configs/asmag_tr_controller_online_guarded_cdnet_smoke.yaml`
- `configs/asmag_tr_controller_online_guarded_cdnet_full.yaml`
- `tools/compare_asmag_tr_controller_online_guarded.py`
- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_CHANGELOG.md`
- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_VALIDATION_PLAN.md`

## Phase 2 Stabilization

Phase 2 was added after the first smoke run showed that `ASMAG_TR_CONTROLLER_ONLINE_GUARDED` improved FPS over old `ONLINE_CALIBRATED` but missed smoke acceptance because P95 latency spiked in `PTZ/continuousPan` and `nightVideos/bridgeEntry`.

Added guarded-only stabilization controls:

- `guard_min_interval_frames` to prevent hard P3 guard detector refresh on every frame.
- `forced_refresh_min_interval_frames` to prevent consecutive forced refresh spikes.
- `max_consecutive_p3_guard_frames` and `guard_exit_disagreement_threshold` to cap hard P3 guard duration.
- `overload_latency_threshold_ms` and `overload_cooldown_frames` to suppress non-critical detector calls after slow detector frames.
- `critical_reuse_confidence_threshold` so overload/cooldown reuse can be less aggressive than normal reuse decay.
- Lightweight mask update during guarded cooldown when reuse is unavailable but a current gate mask is available.

Added Phase 2 diagnostic columns:

- `guard_triggered`
- `guard_reason`
- `guard_cooldown_active`
- `forced_refresh_cooldown_active`
- `overload_guard_active`
- `consecutive_p3_guard_frames`
- `frames_since_last_detector`
- `frames_since_last_forced_refresh`
- `previous_detector_latency_ms`
- `previous_total_latency_ms`

The old `ONLINE_CALIBRATED` pipeline remains unchanged.

## Phase 3 Stabilization

Phase 3 added guarded-only accuracy escape telemetry and controls for PTZ/global-motion and night-like scenes. The old `ONLINE_CALIBRATED` path remains unchanged, and no frozen CDnet2014 v1.6 output folders are used.

Added guarded-only controls:

- `global_motion_escape_enabled`
- `global_motion_area_threshold`
- `global_motion_disagreement_threshold`
- `global_motion_min_activation_floor`
- `global_motion_refresh_interval_frames`
- `max_consecutive_closed_empty_global_motion`
- `ptz_safe_fallback_interval_frames`
- `max_ptz_safe_fallback_burst`
- `low_light_guard_enabled`
- `low_light_threshold`
- `night_refresh_interval_frames`

Added Phase 3 diagnostic columns:

- `global_motion_proxy`
- `global_motion_escape_active`
- `global_motion_reason`
- `global_motion_refresh_triggered`
- `frames_since_global_motion_refresh`
- `consecutive_closed_empty_frames`
- `closed_empty_guard_active`
- `ptz_safe_fallback_active`
- `ptz_safe_fallback_reason`
- `low_light_guard_active`
- `illumination_proxy`
- `night_refresh_triggered`

Final guarded-smoke outcome after Phase 3 remains blocked. The aggregate result passes the requested smoke thresholds:

| Pipeline | FMeasure | Event_F1 | Activation | FPS | P95 latency ms |
|---|---:|---:|---:|---:|---:|
| ONLINE_CALIBRATED | 0.4155 | 0.5636 | 0.6150 | 18.56 | 405.04 |
| ASMAG_TR_CONTROLLER_ONLINE_GUARDED | 0.4476 | 0.5793 | 0.5338 | 37.32 | 262.71 |

However, `PTZ/continuousPan` remains below the required per-video recovery target:

| Video | FMeasure | delta vs old online | Event_F1 | Activation | FPS | P95 latency ms | closed-empty rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| PTZ/continuousPan | 0.1226 | -0.1121 | 0.2906 | 0.49 | 12.64 | 346.78 | 0.00 |
| nightVideos/bridgeEntry | 0.2339 | -0.0058 | 0.9130 | 0.76 | 15.89 | 276.11 | 0.11 |

The original `continuousPan` failure mode changed from closed-empty/stale-reuse collapse to a PTZ/global-motion fallback mask-quality and cadence failure. All requested Phase 3 diagnostic columns are present, but Phase 3 does not pass. Do not proceed to targeted CDnet, full CDnet, LASIESTA, SBI2015, or BMC until the remaining guarded-controller PTZ accuracy issue is fixed.

## Phase 4 GMQ-Guard Implementation

Phase 4 added a guarded-only GMQ-Guard bundle to `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`. The old `ONLINE_CALIBRATED` pipeline and the non-guarded baseline/controller pipelines remain unchanged.

Added guarded-only mechanisms:

- Candidate mask quality scoring for P3, ACC, and FAST.
- GMQ global-motion/background-reliability risk logging.
- P3/lightweight fallback veto telemetry and action blocking.
- Capped `LEGACY_SAFE_P3_GUARD` branch for persistent global-motion quality conflict.
- Prediction-history event-continuity guard for low-light active-event risk.
- Disabled motion-compensation placeholders.

Added GMQ output summaries:

- `gmq_action_summary.csv`
- `gmq_quality_summary.csv`
- `gmq_legacy_safe_summary.csv`
- `gmq_event_continuity_summary.csv`

Phase 4 smoke completed without crashes and all required GMQ columns were present, but Phase 4 does not pass acceptance:

| Pipeline | FMeasure | Event_F1 | Activation | FPS | P95 latency ms |
|---|---:|---:|---:|---:|---:|
| ONLINE_CALIBRATED | 0.4155 | 0.5636 | 0.6150 | 18.56 | 405.04 |
| ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 4 | 0.4305 | 0.5576 | 0.4562 | 22.25 | 308.64 |

Key blocker videos:

| Video | FMeasure | delta vs old online | Event_F1 | Activation | FPS | P95 latency ms | Notes |
|---|---:|---:|---:|---:|---:|---:|---|
| PTZ/continuousPan | 0.1505 | -0.0842 | 0.2523 | 0.43 | 11.83 | 407.59 | P3 veto rate 0.96, legacy-safe rate 0.30, still not recovered |
| nightVideos/bridgeEntry | 0.1854 | -0.0543 | 0.8506 | 0.56 | 11.92 | 314.65 | 21 closed-empty event FNs remain |

Do not proceed to targeted CDnet, full CDnet, LASIESTA, SBI2015, or BMC. The next research step should focus on why GMQ selected ACC as best in `continuousPan` while old/P3-like behavior remains more accurate, and why the first event-continuity guard failed to suppress most `bridgeEntry` closed-empty event gaps.

## Phase 4B GMQ Safe Override

Phase 4B keeps the pipeline ID `ASMAG_TR_CONTROLLER_ONLINE_GUARDED` and modifies only the guarded controller path. Old `ONLINE_CALIBRATED`, P1/P2/P3, FAST, and `ASMAG_TR_CONTROLLER` behavior remain unchanged.

Added guarded-only repairs:

- Split the broad P3 veto into `gmq_lightweight_p3_veto_active` and `gmq_full_p3_veto_active`.
- Preserved full P3 / `LEGACY_SAFE_P3_GUARD` as a valid branch under persistent global-motion conflict instead of blocking it with lightweight-mask quality.
- Added PTZ-safe override logging and behavior: `gmq_ptz_safe_override_active`, `gmq_ptz_safe_branch_forced`, and `gmq_recent_low_trust_action_rate`.
- Added ACC blocking under persistent global motion when ACC temporal consistency or background reliability is too weak.
- Added a hard event-continuity veto for active low-light event memory before final closed-empty action selection.
- Added ablation switches: `gmq_behavior_enabled`, `gmq_quality_behavior_enabled`, and `gmq_logging_only`.
- Kept motion compensation disabled and logged as a placeholder only.
- Reduced GMQ mask-quality overhead by measuring component/spread/edge quality on a downscaled binary mask while preserving original-frame area ratios.

Added Phase 4B diagnostic columns:

- `gmq_lightweight_p3_veto_active`
- `gmq_full_p3_veto_active`
- `gmq_p3_veto_scope`
- `gmq_p3_veto_reason`
- `gmq_ptz_safe_override_active`
- `gmq_ptz_safe_override_reason`
- `gmq_ptz_safe_branch_forced`
- `gmq_recent_low_trust_action_rate`
- `gmq_acc_blocked_under_global_motion`
- `gmq_acc_block_reason`
- `gmq_event_hard_veto_active`
- `gmq_event_hard_veto_reason`
- `gmq_confident_empty_evidence`

Phase 4B must be validated by smoke only before any targeted CDnet run is considered.

## Phase 5 Emergency Safe Action Arbitration

Phase 5 keeps all changes scoped to `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`. Old `ONLINE_CALIBRATED`, P1/P2/P3, FAST, and `ASMAG_TR_CONTROLLER` remain unchanged.

Added guarded-only mechanisms:

- GMQ lazy evaluation so full candidate quality is computed only on global-motion, low-light event, disagreement, or recent low-trust risk frames.
- PTZ emergency conservative override for persistent global-motion frames where ACC remains dominant but unstable.
- Final action sanitizer that blocks unsafe `CLOSED_EMPTY_*` after all cadence, reuse, GMQ, and emergency decisions.
- Rolling label-free runtime signatures for continuousPan-like behavior: global-motion persistence, ACC dominance under global motion, low-trust action rate, and closed-empty under motion.
- Enforcement-safe event guard counters for attempted, blocked, and final closed-empty event-risk frames.

Added Phase 5 diagnostic columns:

- `gmq_lazy_eval_active`
- `gmq_lazy_eval_reason`
- `gmq_quality_compute_ms`
- `ptz_emergency_active`
- `ptz_emergency_reason`
- `ptz_emergency_burst_age`
- `ptz_emergency_cooldown_active`
- `ptz_emergency_forced_action`
- `final_action_before_emergency`
- `final_action_after_emergency`
- `final_action_before_sanitizer`
- `final_action_after_sanitizer`
- `final_sanitizer_active`
- `final_sanitizer_reason`
- `closed_empty_blocked_final`
- `reuse_blocked_final`
- `lightweight_blocked_final`
- `acc_blocked_final`
- `rolling_global_motion_persistence`
- `rolling_acc_dominance_under_global_motion`
- `rolling_low_trust_action_rate`
- `rolling_closed_empty_under_motion_rate`
- `event_closed_empty_attempt_count`
- `event_closed_empty_blocked_count`
- `event_closed_empty_final_count`
- `event_fn_risk_frames`

Motion compensation remains disabled. Phase 5 smoke must pass before any targeted CDnet run is allowed.

## Phase 5B PTZ Closed-Empty Hard Kill Switch

Phase 5B keeps all behavior scoped to `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`. Old `ONLINE_CALIBRATED`, P1/P2/P3, FAST, and `ASMAG_TR_CONTROLLER` remain unchanged.

Phase 5 recovered `PTZ/continuousPan` FMeasure to old-online level and fixed `nightVideos/bridgeEntry` closed-empty event FNs, but still leaked `CLOSED_EMPTY_P3_FALLBACK` on 13% of `continuousPan` frames. Diagnosis showed those frames occurred during global-motion escape with `selected_mode_after_guard=P3_FALLBACK`, but outside explicit `ptz_emergency_active` bursts, so the Phase 5 PTZ sanitizer did not fire.

Added a guarded-only last-step PTZ closed-empty kill switch. If the final action is `CLOSED_EMPTY_*` under a label-free PTZ/global-motion signature, the output is replaced with a non-empty candidate, safe reuse, or capped legacy-safe P3 fallback. Motion compensation remains disabled.

Added Phase 5B diagnostic columns:

- `ptz_closed_empty_kill_active`
- `ptz_closed_empty_kill_reason`
- `closed_empty_attempted_under_ptz`
- `closed_empty_blocked_under_ptz`
- `closed_empty_replacement_action`
- `closed_empty_replacement_source`
- `closed_empty_replacement_quality`
- `closed_empty_kill_cadence_override_used`

Added `ptz_closed_empty_summary.csv` to the guarded comparison tool for closed-empty rate, PTZ kill-switch rate, replacement distribution, and event closed-empty counts.

Phase 5B guarded smoke completed without crashes. The final P3-first replacement correction reduced `PTZ/continuousPan` closed-empty to 0.00 while keeping aggregate guarded FMeasure and Event_F1 above old online and aggregate FPS above 35. Targeted CDnet may proceed from a smoke-gate perspective, with `PTZ/twoPositionPTZCam` marked as a watch item because its FMeasure remains slightly below old online.

## Phase 6B Motion-Compensation-Informed Trust Layer

Phase 6B keeps all behavior scoped to `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`. Old `ONLINE_CALIBRATED`, P1/P2/P3, FAST, and `ASMAG_TR_CONTROLLER` remain unchanged.

Added a guarded-only, risk-gated phase-correlation translation probe and motion-compensation-informed trust signals:

- Downscaled phase-correlation probe with response, shift magnitude, residual ratio, and compute-time diagnostics.
- Compensated temporal IoU between the shifted previous accepted mask and P3, ACC, FAST, and final masks.
- Zoom/scale suspicion and camera-jump suspicion flags.
- Stale reuse and lightweight-mask invalidation when motion compensation is unreliable.
- PTZ detector floor for high camera-motion risk and poor compensation reliability.
- Non-PTZ GMQ behavior restriction and a separate low-framerate cadence guard.

Added Phase 6B summary files in the comparison tool:

- `motion_comp_summary.csv`
- `ptz_motion_comp_summary.csv`
- `low_framerate_guard_summary.csv`

Phase 6B smoke completed without crashes, but failed the smoke gate. Guarded aggregate FMeasure and Event_F1 fell below old online, aggregate FPS fell to `16.95`, and the motion-comp detector floor activated too broadly. `PTZ/continuousPan` remained recovered with closed-empty at `0.00`, but the broader aggregate regression means PTZ-targeted validation was not run.

## Phase 6B-2 Logic-Outcome-Constrained Guard Narrowing

Phase 6B-2 applies the logic-outcome mining constraints from `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_LOGIC_OUTCOME_ANALYSIS.md`.

Implementation changes:

- Added compensated-trust diagnostics and `motion_comp_min_compensated_iou_for_trust`.
- Made compensated IoU the primary reuse/lightweight trust signal.
- Restricted GMQ behavioral branches outside confirmed camera motion, event risk, or low-framerate cadence risk.
- Required confirmed camera motion plus low trust/cadence failure before detector-like PTZ refresh.
- Tightened PTZ emergency, PTZ override, and legacy-safe behavior so `LEGACY_SAFE_P3_GUARD` is not considered automatically safe.
- Preserved Phase 5B fast-path behavior for stable non-PTZ scenes.
