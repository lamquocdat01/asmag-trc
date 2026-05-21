# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 7A Oracle Policy Diagnosis

## Scope

This is a research-only diagnosis built from existing Phase 6C smoke outputs, earlier targeted PTZ diagnosis, and logic-outcome mining artifacts. No source code, configs, smoke runs, targeted runs, full CDnet runs, LASIESTA, SBI2015, or BMC runs were executed.

## Utility Definition

Frame utility was computed as:

```text
utility = FMeasure + 0.3 * Event_proxy - 0.05 * normalized_latency - 0.03 * yolo_called - 0.05 * unsafe_action_penalty
```

`Event_proxy` uses per-video `Event_F1` joined onto frames because the available frame metrics do not expose a direct event-F1 per frame. `normalized_latency` is `latency_ms / 300`, clipped to `[0, 2]`. Unsafe penalties flag closed-empty during event/global-motion contexts, reuse under low trust, lightweight P3 in PTZ, and legacy-safe P3 when detector cadence is not actually preserved.

## ContinuousPan Oracle Gap

ContinuousPan remains a wrong-action-ranking failure, not a closed-empty failure. Phase 6C already blocks closed-empty, and geometry probing succeeds, but low geometry trust causes the stack to choose expensive or weak substitutes too often.

Top observed continuousPan guarded actions by utility:

| action_bucket        |   frames |   frequency |   mean_utility |   mean_FMeasure |   mean_latency_ms |   unsafe_penalty_rate |
|:---------------------|---------:|------------:|---------------:|----------------:|------------------:|----------------------:|
| FALLBACK_P3_GUARD    |        3 |        0.03 |         0.5031 |          0.4848 |          233.762  |                0      |
| FALLBACK_P3_GUARD    |       31 |        0.31 |         0.151  |          0.118  |          207.539  |                0      |
| LEGACY_SAFE_P3_GUARD |       29 |        0.29 |         0.0804 |          0.0775 |          305.024  |                0.1034 |
| LIGHTWEIGHT_MASK_ACC |        5 |        0.05 |         0.0775 |          0.0007 |           67.2811 |                0      |
| LEGACY_SAFE_P3_GUARD |       62 |        0.62 |         0.0518 |          0.0449 |          272.529  |                0.1129 |
| OTHER                |       68 |        0.68 |         0.0509 |          0.0211 |           45.6353 |                0.9853 |
| OTHER                |        2 |        0.02 |         0.0167 |          0      |          187.646  |                0.5    |

Largest replaceable gaps:

| dataset   | category   | video         | current_action_bucket   |   current_frequency |   current_mean_utility |   current_mean_FMeasure |   current_mean_latency_ms | oracle_replacement_action   |   oracle_mean_utility |   oracle_mean_FMeasure |   estimated_utility_gap |   estimated_F_gap | replaceable_low_utility   |
|:----------|:-----------|:--------------|:------------------------|--------------------:|-----------------------:|------------------------:|--------------------------:|:----------------------------|----------------------:|-----------------------:|------------------------:|------------------:|:--------------------------|
| smoke     | PTZ        | continuousPan | OTHER                   |                0.02 |                 0.0167 |                  0      |                  187.646  | FALLBACK_P3_GUARD           |                0.5031 |                 0.4848 |                  0.4864 |            0.4848 | True                      |
| targeted  | PTZ        | continuousPan | OTHER                   |                0.68 |                 0.0509 |                  0.0211 |                   45.6353 | FALLBACK_P3_GUARD           |                0.5031 |                 0.4848 |                  0.4521 |            0.4638 | True                      |
| smoke     | PTZ        | continuousPan | LEGACY_SAFE_P3_GUARD    |                0.62 |                 0.0518 |                  0.0449 |                  272.529  | FALLBACK_P3_GUARD           |                0.5031 |                 0.4848 |                  0.4513 |            0.4399 | True                      |
| smoke     | PTZ        | continuousPan | LIGHTWEIGHT_MASK_ACC    |                0.05 |                 0.0775 |                  0.0007 |                   67.2811 | FALLBACK_P3_GUARD           |                0.5031 |                 0.4848 |                  0.4256 |            0.4841 | True                      |
| targeted  | PTZ        | continuousPan | LEGACY_SAFE_P3_GUARD    |                0.29 |                 0.0804 |                  0.0775 |                  305.024  | FALLBACK_P3_GUARD           |                0.5031 |                 0.4848 |                  0.4227 |            0.4073 | True                      |
| smoke     | PTZ        | continuousPan | FALLBACK_P3_GUARD       |                0.31 |                 0.151  |                  0.118  |                  207.539  | FALLBACK_P3_GUARD           |                0.5031 |                 0.4848 |                  0.3521 |            0.3669 | True                      |
| targeted  | PTZ        | continuousPan | FALLBACK_P3_GUARD       |                0.03 |                 0.5031 |                  0.4848 |                  233.762  | FALLBACK_P3_GUARD           |                0.5031 |                 0.4848 |                  0      |            0      | False                     |

The best safe observed replacement in the current evidence is `FALLBACK_P3_GUARD` with mean utility `0.5031` and mean frame FMeasure `0.4848`. The targeted PTZ diagnosis still warns that `LIGHTWEIGHT_MASK_ACC` can be high-F when candidate quality is genuinely good, but it should be inter-anchor only and never a replacement for low-trust geometry.

## PTZ Action Ranking

PTZ aggregate action utility from smoke and targeted guarded frame metrics:

| action_bucket        |   frames |   mean_utility |   mean_FMeasure |   mean_latency_ms |   unsafe_penalty_rate |
|:---------------------|---------:|---------------:|----------------:|------------------:|----------------------:|
| DETECT_ACC           |       90 |         0.9202 |          0.7582 |          255.07   |                0      |
| LIGHTWEIGHT_MASK_ACC |       25 |         0.7225 |          0.5309 |           36.932  |                0      |
| FALLBACK_P3_GUARD    |       54 |         0.5937 |          0.4762 |          240.114  |                0      |
| OTHER                |      214 |         0.3393 |          0.2167 |          124.154  |                0.591  |
| REUSE_ACC            |       46 |         0.2994 |          0.1217 |           36.6547 |                1      |
| LEGACY_SAFE_P3_GUARD |      147 |         0.2753 |          0.1833 |          312.074  |                0.0898 |
| CLOSED_EMPTY_ACC     |       24 |         0.1819 |          0      |           15.7625 |                1      |

Interpretation:

- `DETECT_ACC`, `FALLBACK_P3_GUARD`, and selected `LIGHTWEIGHT_MASK_ACC` remain the safest useful PTZ buckets.
- `REUSE_ACC`, `LIGHTWEIGHT_MASK_P3_FALLBACK`, `CLOSED_EMPTY_ACC`, and weak `LEGACY_SAFE_P3_GUARD` are unsafe or low-utility under PTZ/global motion unless protected by stronger trust evidence.
- Phase 6C confirms the remaining continuousPan gap is not geometry probe availability; it is how the policy interprets low geometry trust and ranks actions after the probe.

## Shallow Policy Prototype

A shallow policy tree was trained only as a diagnostic on high-utility observed guarded actions, with video-grouped validation when sklearn was available. It uses runtime features only and excludes category/video/ground-truth metrics from deployment features.

Top policy features:

| feature                            |   importance |
|:-----------------------------------|-------------:|
| frames_since_last_detector         |       0.384  |
| gmq_background_reliability         |       0.3791 |
| candidate_P3_area_ratio            |       0.1232 |
| geometry_trust_score               |       0.0856 |
| gmq_event_continuity_risk          |       0.0281 |
| gmq_global_motion_risk             |       0      |
| camera_jump_suspect                |       0      |
| geometry_rotation_deg              |       0      |
| geometry_shift_mag                 |       0      |
| geometry_comp_iou_best             |       0      |
| geometry_residual_ratio            |       0      |
| geometry_improves_over_translation |       0      |

Rules are exported to `outputs/policy_diagnosis/shallow_policy_rules.txt`.

## Answers

1. ContinuousPan failure is primarily wrong action ranking under PTZ/global motion. The stack has enough safety guards and geometry probe signal to avoid closed-empty, but it does not choose the right detector-anchor/lightweight-ACC balance when geometry trust stays low.
2. Replace low-utility continuousPan actions with detector-like anchors first, especially `FALLBACK_P3_GUARD`/`DETECT_ACC`, and allow `LIGHTWEIGHT_MASK_ACC` only as a quality-gated inter-anchor action. Do not replace with `REUSE_ACC` or `LIGHTWEIGHT_MASK_P3_FALLBACK`.
3. A shallow policy can explain the observed high-utility choices well enough for diagnosis, but the labels are observational and sparse. Treat it as a distillation aid, not as a deployable learned model yet.
