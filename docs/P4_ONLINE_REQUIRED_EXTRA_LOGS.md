# P4-Online Required Extra Logs

Date: 2026-05-09

The current logs are useful, but not sufficient for precise causality. This file lists the minimum extra diagnostics needed before implementing a high-confidence P4-Online v1.7 optimization pass.

## Missing CSV Columns

Add these to online `frame_metrics.csv` and `edge_profile.csv`:

| Column | Why needed |
|:--|:--|
| `action_label` | One of `DETECT`, `REUSE`, `FALLBACK_P3`, `FORCED_REFRESH`, `CLOSED_EMPTY`, `WARMUP`. |
| `action_reason` | Human-readable or enum reason: policy, hard guard, periodic sample, reuse age, closed gate, disagreement. |
| `selected_mode_before_guard` | Separates learned policy from safety override. |
| `selected_mode_after_guard` | Final mode used for mask/detector decision. |
| `mode_switch_reason` | Explains switches: policy change, hysteresis release, hard guard, cooldown. |
| `candidate_FAST_gate_open` | Candidate FAST decision before final mode selection. |
| `candidate_ACC_gate_open` | Candidate ACC decision before final mode selection. |
| `candidate_P3_gate_open` | Candidate P3 decision before final mode selection. |
| `candidate_FAST_gate_score` | Needed for policy/gate debugging. |
| `candidate_ACC_gate_score` | Needed for policy/gate debugging. |
| `candidate_P3_gate_score` | Needed for fallback debugging. |
| `candidate_FAST_area` | Candidate mask size. |
| `candidate_ACC_area` | Candidate mask size. |
| `candidate_P3_area` | Candidate mask size. |
| `cache_hit_gate_features` | Confirms whether shared features were reused. |
| `gate_compute_resolution` | Confirms whether configured gate resize is active. |

## Missing Per-Frame Action Logs

Current logs include `gate_open`, `yolo_called`, `reused_prediction`, and `selected_mode`, but not a single explicit action label. Add a compact action log so failure tables can distinguish:

- Detector ran because selected gate opened.
- Prediction was reused because selected gate closed.
- Empty mask emitted because reuse was not allowed.
- P3 fallback was selected by policy.
- P3 fallback was forced by hard guard.
- Forced refresh overrode reuse.

## Missing Latency Breakdown

Current `latency_ms` is too coarse. Add per-frame timings:

| Timing column | Scope |
|:--|:--|
| `latency_gate_features_ms` | FrameDiff/MOG2/KNN/morphology/shared feature extraction. |
| `latency_policy_ms` | Rolling feature aggregation and policy prediction. |
| `latency_gate_select_ms` | Candidate mode selection and guards. |
| `latency_detector_ms` | Detector inference only. |
| `latency_mask_postprocess_ms` | Mask fusion, components, morphology, box conversion. |
| `latency_metrics_ms` | Pixel/event/object metric calculation. |
| `latency_logging_ms` | Any progress/log write included in wall-clock timing. |

This is critical because current evidence strongly suggests repeated gate computation, but exact percentages are not logged.

## Missing DETECT / REUSE / FALLBACK Labels

Add explicit labels rather than inferring from `yolo_called`, `reused_prediction`, and `selected_mode`.

Recommended enum:

- `DETECT_FAST`
- `DETECT_ACC`
- `DETECT_P3`
- `REUSE_FAST`
- `REUSE_ACC`
- `FORCED_REFRESH_FAST`
- `FORCED_REFRESH_ACC`
- `CLOSED_EMPTY_FAST`
- `CLOSED_EMPTY_ACC`
- `FALLBACK_P3_POLICY`
- `FALLBACK_P3_GUARD`

## Missing Mode-Switch Logs

Add per-frame and per-video switch diagnostics:

- `previous_mode`
- `desired_mode`
- `candidate_mode`
- `candidate_frames`
- `mode_duration`
- `mode_switch_count`
- `switches_per_100_frames`
- `switch_blocked_by_hysteresis`
- `switch_blocked_by_budget`

The current calibrated run disables hysteresis and shows failure videos with high switch rates. v1.7 needs direct switch reason logs.

## Missing Controller Feature Values

Current frame metrics include many rolling features, which is good. Add or standardize:

- Raw per-frame `motion_density`, `component_count`, `fd_area`, `mog_area`, `knn_area`.
- Rolling window size actually used.
- Normalized feature values used by the policy.
- Policy probabilities or decision scores if the model supports them.
- Hard guard thresholds active on that frame.

## Missing Per-Video Activation / Reuse Breakdown

`online_mode_usage_by_video.csv` is useful but should add:

- Activation by selected mode.
- Reuse by selected mode.
- Empty-output rate by selected mode.
- Forced-refresh count by selected mode.
- Mean/P95 latency by selected mode.
- FMeasure/Event_F1 by selected mode if attribution is possible.
- Detector-call count by selected mode.
- Cache hit/miss count by selected mode.

## Minimum Logging Acceptance Criteria

Before another full CDnet2014 P4-Online run:

- A one-video smoke run must show all new columns present.
- `action_label` must be non-empty on every evaluated frame.
- Per-frame timing components must sum close to total `latency_ms`.
- Per-video summaries must include mode-level activation, reuse, and latency.
- The new run must write to a new output folder.
