# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 4 Proposed Design

Date: 2026-05-09

Design name: GMQ-Guard, Global-Motion and Mask-Quality Guard.

Pipeline ID remains unchanged: `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`.

This is a design document only. Do not implement until explicitly requested.

## Design Goal

Phase 4 should preserve Phase 3 aggregate gains while fixing the remaining hard-scene failure: `PTZ/continuousPan` no longer fails because of closed-empty/reuse collapse, but because global motion invalidates simple P3/lightweight fallback trust. GMQ-Guard adds a label-free arbitration layer that scores candidate reliability before deciding whether to use P3, ACC, FAST, legacy-online-like fallback, detector refresh, lightweight update, or reuse.

## Architecture Diagram

```text
Frame t, Previous frame, Previous accepted mask, Runtime state
        |
        v
Shared Gate Feature Bank
  - FrameDiff, MOG2, KNN
  - candidate FAST/ACC/P3 masks and scores
  - motion area, disagreement, component stats
  - illumination and low-light proxies
        |
        v
GMQ-Guard Feature Layer
  1. Global-motion reliability estimator
  2. Candidate mask quality estimator
  3. Temporal consistency estimator
  4. Detector staleness estimator
  5. Event-continuity estimator
  6. Latency/energy risk estimator
        |
        v
Risk Arbitration
  - score P3 detector refresh
  - score ACC detector refresh
  - score FAST detector refresh
  - score lightweight mask update
  - score reuse
  - score closed-empty
  - score legacy-online safe branch
        |
        v
Selected action
  - DETECT_ACC / DETECT_FAST / FALLBACK_P3_GUARD
  - LIGHTWEIGHT_MASK_* only if quality is acceptable
  - REUSE_* only if temporal propagation is reliable
  - CLOSED_EMPTY_* only if event-continuity risk is low
  - LEGACY_SAFE_P3 if global motion makes guarded arbitration unsafe
```

## New Scores and Features

### 1. Global-Motion Reliability Estimator

Purpose: detect when raw motion and background subtraction are likely dominated by camera motion.

Inputs already available or cheap:

- `motion_disagreement`
- `motion_density_mean`
- `fd_area`, `mog_area`, `knn_area`
- `candidate_P3_area`, `candidate_ACC_area`, `candidate_FAST_area`
- `component_count_mean`, `component_count_std`
- `global_motion_proxy`
- `frames_since_last_detector`
- optional downscaled global shift/affine residual

Proposed features:

| Feature | Meaning |
|---|---|
| `gm_motion_coverage` | normalized widespread motion estimate |
| `gm_candidate_spread` | spatial spread of candidate mask across coarse grid cells |
| `gm_background_disagreement` | disagreement among FD/MOG/KNN and P3/ACC/FAST |
| `gm_temporal_persistence` | consecutive frames with high global motion risk |
| `gm_residual_motion_ratio` | optional ratio after global alignment |
| `background_reliability_score` | inverse risk that P3/ACC/FAST background models are invalid |

Key distinction: `global_motion_proxy` should remain a risk detector, but GMQ-Guard needs `background_reliability_score` to decide whether P3 is trustworthy.

### 2. Candidate Mask Quality Estimator

Purpose: score candidate FAST, ACC, and P3 masks before trusting them.

Candidate score terms:

| Score | Desired behavior |
|---|---|
| `area_plausibility` | Penalize tiny masks when event risk is high and whole-frame masks when global motion is high. |
| `component_plausibility` | Prefer a small number of object-like components over scattered fragments. |
| `spatial_spread_penalty` | Penalize masks spread across many coarse grid cells under global motion. |
| `edge_touch_penalty` | Penalize masks dominated by borders during pan/tilt. |
| `temporal_iou` | Compare candidate to previous accepted mask after optional global compensation. |
| `candidate_agreement` | Reward overlap or compatible evidence among P3/ACC/FAST, penalize total disagreement. |
| `foreground_density_consistency` | Penalize sudden candidate area jumps unless detector confirms. |
| `lightweight_quality_gate` | Allow lightweight mask only if quality score is above a minimum. |

Candidate mask quality:

```text
quality(mask, mode) =
    + object_like_components
    + temporal_iou_or_compensated_iou
    + candidate_agreement
    + stable_area_score
    - whole_frame_motion_penalty
    - scattered_fragment_penalty
    - edge_touch_penalty
    - stale_background_penalty
```

### 3. P3 Fallback Veto

Purpose: avoid blindly trusting P3 under global camera motion.

Veto conditions:

- global motion risk is persistent
- P3 quality is low
- P3/ACC/FAST disagreement is high
- P3 area or spread indicates background-dominated motion
- previous P3/lightweight actions had low proxy confidence or poor continuity

Actions after veto:

- If legacy-safe criteria are met: use legacy-online-like full P3 detector cadence briefly.
- If ACC quality is better and event risk is moderate: use `DETECT_ACC`.
- If all masks are low quality: force detector refresh with strongest candidate proposal or hold previous accepted mask after motion compensation.
- Do not emit `LIGHTWEIGHT_MASK_P3_FALLBACK` when quality is low.

### 4. Legacy-Online Safe Branch

Purpose: recover the one behavior old online had right: in `continuousPan`, it stayed P3 fallback with full activation and recovered substantially more FMeasure, despite high latency.

Rules:

- Do not modify old `ONLINE_CALIBRATED`.
- Add a guarded-only branch that approximates old online behavior under narrow conditions.
- Enable only when persistent global motion, P3/ACC/FAST quality conflict, and recent guarded actions underperform proxy expectations.

Proposed action label:

- `LEGACY_SAFE_P3_GUARD`

Branch behavior:

- Use P3 fallback detector refresh cadence closer to old online for a short burst.
- Exit when global motion risk drops or mask quality stabilizes.
- Keep latency guard: max burst length and recovery cooldown.

### 5. Event-Continuity Guard

Purpose: prevent `bridgeEntry`-like event fragmentation.

Inputs:

- recent `Event_State` proxy from predictions, not ground truth in production
- recent accepted foreground presence
- candidate mask area and quality
- low-light risk
- frames since last accepted active detection
- closed-empty streak

Rules:

- If recent accepted mask indicates active event and candidate quality is not confidently empty, block `CLOSED_EMPTY_*`.
- In low-light scenes, require stronger evidence before closing an event.
- Permit reuse or lightweight update if quality is acceptable; otherwise cadence-limited detector refresh.

Proposed score:

```text
event_continuity_risk =
    active_event_memory
  + low_light_risk
  + frames_since_last_detector_norm
  + closed_empty_streak_norm
  - confident_empty_evidence
```

### 6. Relative-Motion / Motion-Compensation Option

Motion compensation is important, but it should start optional.

Options:

| Option | Cost | Benefit | Risk | Recommendation |
|---|---:|---|---|---|
| Downscaled phase correlation shift | Low | Good for translation-like pan | Fails on zoom/rotation | Best first probe |
| Sparse optical flow plus affine estimate | Medium | Handles pan/tilt/limited rotation | Low-texture/night instability | Good optional Phase 4b |
| ECC alignment | Medium to high | Strong global alignment | Can fail or spike latency | Optional after smoke |
| Feature matching homography/affine | Medium | Handles larger camera motion | Feature scarcity and outliers | Optional, not first bundle |
| Dense optical flow | High | Best local motion detail | Too slow/noisy for edge | Postpone |

First implementation should add a config-gated downscaled global shift estimator and log residual motion. It should not be required for acceptance of the first GMQ-Guard bundle.

### 7. Multi-Objective Risk Score

GMQ-Guard should choose the action with minimum expected risk subject to latency constraints.

```text
risk(action) =
    w_f  * expected_fmeasure_risk(action)
  + w_e  * event_continuity_risk(action)
  + w_s  * reuse_staleness_risk(action)
  + w_g  * global_motion_unreliability(action)
  + w_l  * latency_overload_risk(action)
  + w_en * energy_cost(action)
  + w_a  * activation_cost(action)
```

Action-specific notes:

- `CLOSED_EMPTY_*`: low latency, high event risk if active-event memory exists.
- `REUSE_*`: low latency, high staleness risk under motion or long age.
- `LIGHTWEIGHT_MASK_*`: low latency, high FMeasure risk if mask quality low.
- `DETECT_ACC/FAST`: medium/high latency, lower event risk if candidate quality is plausible.
- `FALLBACK_P3_GUARD`: high latency, useful only if P3 quality and background reliability are acceptable.
- `LEGACY_SAFE_P3_GUARD`: highest cost, allowed only for persistent PTZ/global-motion danger.

## Decision Flow

```text
1. Build candidates from shared gate features.
2. Compute global motion risk and background reliability.
3. Compute mask quality for P3, ACC, FAST.
4. Compute temporal consistency against previous accepted mask.
5. Compute event-continuity risk.
6. If global motion is persistent:
      a. Veto low-quality P3/lightweight masks.
      b. If old-online-like P3 is safer, enter short legacy-safe burst.
      c. Else choose best-quality candidate with cadence limit.
7. Else if low-light/event continuity risk is high:
      a. Block closed-empty unless confident empty evidence exists.
      b. Prefer reuse/lightweight only if temporal consistency is high.
      c. Otherwise allow cadence-limited ACC refresh.
8. Else:
      a. Preserve Phase 3 latency controls.
      b. Choose lowest multi-objective risk action.
9. Log all scores and final action reason.
```

## Pseudo-Code

```python
features = shared_gate_bank.process(frame, prev_frame)
candidates = build_candidates(features)  # P3, ACC, FAST

gm = estimate_global_motion_reliability(features, prev_state)
quality = {
    mode: estimate_mask_quality(candidates[mode], prev_state, gm)
    for mode in ["P3_FALLBACK", "ACC", "FAST"]
}
event_risk = estimate_event_continuity_risk(prev_state, features, quality)
latency_risk = estimate_latency_risk(prev_state)

actions = enumerate_candidate_actions(candidates, prev_state)

if gm.persistent and quality["P3_FALLBACK"].low:
    actions.remove("LIGHTWEIGHT_MASK_P3_FALLBACK")
    if legacy_safe_branch_allowed(gm, quality, prev_state, latency_risk):
        actions.add("LEGACY_SAFE_P3_GUARD")

if event_risk.high:
    actions.remove_matching("CLOSED_EMPTY_*")

for action in actions:
    score[action] = multi_objective_risk(action, gm, quality, event_risk, latency_risk, prev_state)

selected_action = argmin(score)
execute(selected_action)
log_gmq_scores(gm, quality, event_risk, score, selected_action)
```

## Proposed Config Parameters

Keep existing Phase 2 and Phase 3 parameters. Add Phase 4 guarded-only parameters:

```yaml
online_controller_guarded:
  gmq_guard_enabled: true
  gmq_quality_enabled: true
  gmq_legacy_safe_branch_enabled: true
  gmq_event_continuity_enabled: true

  gmq_min_mask_quality_for_lightweight: 0.45
  gmq_min_mask_quality_for_p3_trust: 0.50
  gmq_max_spatial_spread_for_p3_trust: 0.70
  gmq_candidate_disagreement_threshold: 0.45
  gmq_whole_frame_motion_penalty_threshold: 0.35

  gmq_global_motion_persistence_frames: 3
  gmq_background_reliability_min: 0.40
  gmq_legacy_safe_min_interval_frames: 2
  gmq_legacy_safe_max_burst_frames: 8
  gmq_legacy_safe_cooldown_frames: 8

  gmq_event_memory_frames: 6
  gmq_max_closed_empty_during_active_event: 0
  gmq_low_light_event_risk_boost: 0.25

  gmq_motion_compensation_enabled: false
  gmq_motion_compensation_method: "phase_correlation_shift"
  gmq_motion_compensation_resize_width: 160
```

Threshold values above are placeholders for design review only, not tuning instructions.

## Table 6: Proposed Phase 4 Mechanisms and Expected Metric Impact

| Mechanism | FMeasure | Event_F1 | Activation | FPS | P95 latency | Main benefit |
|---|---|---|---|---|---|---|
| Candidate mask quality estimator | Up on PTZ/shadow/night | Up if fewer broken events | Neutral/slightly up | Slight down | Slight up | Avoid low-quality lightweight/fallback masks |
| P3 fallback veto | Up on global motion | Neutral/up | Neutral | Neutral/up | Neutral/down if veto avoids bad P3 | Prevent harmful P3 trust |
| Legacy-online safe branch | Up strongly on continuousPan | Neutral | Up on PTZ only | Down on PTZ | Up on PTZ | Recover old online safety only when needed |
| Event-continuity guard | Neutral/up | Up on bridgeEntry/night | Slight up | Slight down | Slight up | Prevent active-event closed-empty gaps |
| Optional motion compensation | Up if camera motion dominates | Neutral/up | Neutral/down | Down if enabled | Up if too frequent | Distinguish global from residual motion |
| Multi-objective risk score | Up by avoiding wrong actions | Up | Neutral/down globally | Neutral/up globally | Neutral/down globally | Replaces brittle independent rules |

## Table 7: Risk and Implementation Complexity

| Change | Complexity | Risk | Reason |
|---|---|---|---|
| Add GMQ logging | Low | Low | Read-only diagnostics from existing masks/features |
| Mask area/spread/component quality | Low-medium | Low | Uses existing candidate masks |
| Temporal mask consistency | Medium | Low-medium | Needs previous accepted mask bookkeeping |
| P3 lightweight veto | Medium | Medium | Could reduce useful cheap masks if quality score is wrong |
| Event-continuity closed-empty block | Low-medium | Low | Directly addresses observed bridgeEntry FNs |
| Legacy-safe P3 branch | Medium | Medium | Improves PTZ safety but can hurt latency if not capped |
| Downscaled shift compensation | Medium | Medium-high | Adds new vision primitive and failure cases |
| Sparse optical flow/ECC/dense flow | High | High | Postpone until quality arbitration is tested |
| Policy retraining | High | Medium-high | Needs clean targets and validation split |
| New deep segmentation model | Very high | High | Incompatible with current low-risk stabilization |

## Ablation Plan

Run smoke only after implementation is explicitly requested:

1. GMQ logging only.
2. Candidate quality estimator with no behavior changes.
3. Quality-gated lightweight/P3 veto.
4. Event-continuity guard.
5. Legacy-safe branch for global motion.
6. Optional motion compensation probe, disabled by default.

Acceptance must be judged incrementally. If a step improves aggregate but leaves `continuousPan` catastrophic, stop.

## Expected Outcome

The smallest useful Phase 4 implementation should aim for:

- `continuousPan` FMeasure within 0.02 of old online, preferably by using a capped legacy-safe P3 branch only when GMQ quality is low.
- `bridgeEntry` Event_F1 close to old online by eliminating `CLOSED_EMPTY_ACC` event FNs.
- Aggregate FMeasure and Event_F1 above old online.
- Aggregate FPS at or above 35.
- Aggregate P95 at or below 300 ms, preferably near Phase 3's 262.71 ms.

The breakthrough is not another threshold. It is making the guarded controller aware of when its own candidate masks are untrustworthy.
