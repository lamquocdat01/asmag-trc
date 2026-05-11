# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8C-1B Latency Optimization Plan

Phase 8C-1 shadow-mode instrumentation passed, but the shadow path was too slow for any future intervention work:

- Phase 8C-1 mean / P95 shadow latency: 49.37 / 70.65 ms.
- Phase 8C-1 unsafe flag rate: 1.000 on smoke.
- AI intervention was disabled, and remains disabled.

## Current Runtime Path

The current shadow path loads model artifacts once per guarded sequence. Model loading is cached by `AIShadowPolicy` and is not repeated per frame.

The expensive per-frame path is:

1. Build a one-row pandas feature frame.
2. Run several sklearn pipelines sequentially.
3. Include random forest inference for unsafe, lightweight, and risk-class when all models are active.
4. Format the prediction fields for per-frame telemetry logging.

CSV writing is not counted directly inside `ai_shadow_latency_ms`, although whole-run wall time can still be affected by output volume and system load.

## 8C-1B Optimizations Applied

The smoke config now keeps intervention disabled and adds shadow-only runtime knobs:

- `ai_shadow_unsafe_threshold: 0.75`
- `ai_shadow_prediction_stride: 3`
- `ai_shadow_use_lightweight_runtime_models: true`
- `ai_shadow_behavior_enabled: false`

Runtime changes:

- Predictions are recomputed every 3 guarded frames and cached between prediction frames.
- Current-action comparison fields are still recomputed each frame from cached scores.
- Random forest `n_jobs` is forced to 1 at load/export time to avoid per-frame thread churn.
- Lightweight runtime mode skips `risk_class` random forest inference.

## Post-Optimization Smoke Latency

Smoke-only rerun completed 32/32 jobs with no failed jobs.

- 8C-1B mean / P95 shadow latency: 22.15 / 118.33 ms.
- Missing feature count: mean 0.0, P95 0.0.

The mean improved by about 55 percent, but P95 is still high because prediction frames still run multiple sklearn pipelines and because several videos experienced high system load during the smoke run.

## Expensive Models

The heavier runtime candidates are:

- `unsafe_action`: random forest.
- `lightweight_allowed`: random forest.
- `risk_class`: random forest, skipped in lightweight runtime mode.

The cheaper runtime candidates are:

- `detector_needed`: logistic regression.
- `reuse_allowed`: logistic regression.
- `detector_floor_needed`: decision tree.

## Recommended Runtime Model Set

For any future Phase 8C-2 shadow-to-intervention study, prefer this minimal model set:

- Keep `detector_needed` logistic regression.
- Keep `reuse_allowed` logistic regression only as an advisory signal.
- Keep `detector_floor_needed` decision tree.
- Replace or supplement monolithic `unsafe_action` random forest with sub-risk decision-tree rules.
- Keep `risk_class` random forest out of the frame-critical path unless it is sampled at a lower stride.
- Continue excluding PTZ/action rankers from runtime selection.

The sub-risk probes are promising as research candidates:

- `closed_empty_unsafe`: decision tree F1 0.9899.
- `reuse_unsafe`: decision tree F1 0.9831.
- `lightweight_p3_unsafe`: decision tree F1 0.8651.
- `legacy_cadence_unsafe`: random forest F1 0.8696.

These are not deployed.

## Next Optimization Targets

Recommended changes before Phase 8C-2:

1. Export shallow decision-tree sub-risk models or deterministic rules for closed-empty and reuse risk.
2. Increase prediction stride to 5-10 frames on low-risk videos, with event-triggered immediate inference on PTZ/global-motion transitions.
3. Replace per-frame pandas DataFrame construction with a preallocated numeric feature vector.
4. Add per-target latency counters to separate feature adapter, sklearn inference, and logging costs.
5. Keep all AI outputs advisory until a no-drift smoke comparison is reproduced.

## Target Latency for Phase 8C-2

Phase 8C-2 should require:

- Mean shadow prediction latency <= 10 ms.
- P95 shadow prediction latency <= 20 ms.
- Missing feature count near zero.
- No measurable final-action drift when AI behavior remains disabled.

Phase 8C-1B does not yet meet the latency or action-stability confidence bar for limited intervention.
