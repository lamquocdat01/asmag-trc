# P4-Online Top 10 Improvements

Date: 2026-05-09

All validation commands below should write to new experiment folders. Do not overwrite frozen CDnet2014 v1.6 outputs.

## 1. Shared Gate Feature Cache

Problem addressed: ONLINE_CALIBRATED computes candidate gates for P3, ACC, and FAST every evaluated frame. ACC and FAST each recompute FrameDiff, MOG2, KNN, morphology, component filtering, and telemetry.

Expected effect:

- FMeasure: neutral to slightly positive because selected masks become more consistent.
- Event_F1: neutral.
- Activation: neutral.
- FPS/P95 latency: large improvement. This is the highest-confidence runtime fix.
- Implementation risk: medium, because shared masks must preserve each mode's filtering semantics.
- Likely files/functions: `src/run_experiment.py::process_sequence`, `src/gating/gates.py::ASMAGPlusGate`, `src/gating/gates.py::ASMAGPlusEfficientGate`.
- CDnet2014 P4 rerun required: yes.
- Expected validation command: `python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc_p4_v1_7.yaml`.

## 2. Hard P3 Guards for Motion Disagreement and Known Hard Scenes

Problem addressed: the calibrated model can predict FAST/ACC even when motion-source disagreement is high. In the current code, a non-empty calibrated prediction bypasses the handcrafted `force_p3` path.

Expected effect:

- FMeasure: medium gain, especially `turbulence2`, `fountain02`, `backdoor`, PTZ, night, and dynamic background.
- Event_F1: medium gain.
- Activation: likely increases on hard scenes.
- FPS/P95 latency: may worsen unless paired with feature caching.
- Implementation risk: low to medium.
- Likely files/functions: `OnlineSceneDifficultyEstimator.update`, calibrated controller config.
- CDnet2014 P4 rerun required: yes.
- Expected validation command: same new v1.7 config, with a P4-only pipeline list.

## 3. Restore Hysteresis for Calibrated Policy

Problem addressed: official calibrated config has `use_hysteresis: false`, and high mode-switch videos overlap with failure cases. `backdoor`, `turbulence2`, `fountain02`, and `cubicle` switch 8 to 9 times per 100 frames.

Expected effect:

- FMeasure: medium gain by reducing stale/mismatched mode transitions.
- Event_F1: small to medium gain.
- Activation: neutral to slightly lower.
- FPS/P95 latency: smoother P95, fewer transition spikes.
- Implementation risk: low.
- Likely files/functions: `configs/*online*_v1_7.yaml`, `OnlineSceneDifficultyEstimator`.
- CDnet2014 P4 rerun required: yes.
- Expected validation command: `python src/run_experiment.py --config configs/q2_core_extended_online_controller_calibrated_v1_7.yaml`.

## 4. Retrain Policy on Empirical Winners, Not Category Pseudo Labels

Problem addressed: `train_online_mode_policy.py` maps every frame to a category-level pseudo label. That does not learn which mode actually won on that video/frame. Validation macro F1 is only 0.5522.

Expected effect:

- FMeasure: medium to high gain if targets use per-video/per-frame quality and cost.
- Event_F1: medium gain.
- Activation: depends on the selected objective.
- FPS/P95 latency: depends on objective; can improve if cost-sensitive.
- Implementation risk: medium.
- Likely files/functions: `src/controller/train_online_mode_policy.py`, policy training data generation, config `mode_policy_path`.
- CDnet2014 P4 rerun required: yes.
- Expected validation command: train new policy, then run the new v1.7 P4 config.

## 5. Low-Activation Forced Refresh

Problem addressed: low activation correlates with missed foreground in `turbulence2`, `blizzard`, `fountain02`, and `backdoor`.

Expected effect:

- FMeasure: medium gain on low-activation failure videos.
- Event_F1: medium gain.
- Activation: slight increase.
- FPS/P95 latency: slight cost, controllable with interval caps.
- Implementation risk: low.
- Likely files/functions: `ASMAGPlusEfficientGate.process`, reuse branch in `process_sequence`.
- CDnet2014 P4 rerun required: yes.
- Expected validation command: new v1.7 config on failure-video smoke, then full P4-only.

## 6. Reuse Age Decay and Scene-Aware Reuse Caps

Problem addressed: reuse helps runtime but can preserve stale masks. `cubicle`, `parking`, and `turbulence2` show suspicious reuse with accuracy loss.

Expected effect:

- FMeasure: small to medium gain.
- Event_F1: small gain.
- Activation: slight increase because stale reuse is replaced by refresh.
- FPS/P95 latency: slight cost.
- Implementation risk: low.
- Likely files/functions: reuse branch in `src/run_experiment.py::process_sequence`, `p4_efficient` config.
- CDnet2014 P4 rerun required: yes.
- Expected validation command: new v1.7 config with per-category reuse caps.

## 7. Implement Configured Gate Downscaling

Problem addressed: official config includes `resize_width_for_gating: 320`, but no implementation use was found. Full-resolution gate computation is costly.

Expected effect:

- FMeasure: neutral to slight loss unless mask upscaling and component thresholds are tuned.
- Event_F1: neutral.
- Activation: neutral.
- FPS/P95 latency: large gain if implemented safely.
- Implementation risk: medium.
- Likely files/functions: `src/gating/gates.py`, possibly `process_sequence` for frame scale metadata.
- CDnet2014 P4 rerun required: yes.
- Expected validation command: smoke on small/thin-object videos, then full P4-only.

## 8. Cheap Fallback Path

Problem addressed: P3 fallback inside online mode is slower than plain P3 because online telemetry still computes the other gates before selecting fallback.

Expected effect:

- FMeasure: neutral.
- Event_F1: neutral.
- Activation: neutral.
- FPS/P95 latency: large gain in P3-heavy categories.
- Implementation risk: medium.
- Likely files/functions: online gate scheduling in `process_sequence`.
- CDnet2014 P4 rerun required: yes.
- Expected validation command: new v1.7 full CDnet P4-only config.

## 9. Per-Category Safety Profiles

Problem addressed: one global calibrated model is too blunt. Hard categories need conservative fallback; baseline/intermittent/thermal can tolerate more FAST/ACC/reuse.

Expected effect:

- FMeasure: medium gain.
- Event_F1: medium gain.
- Activation: increases in hard categories, decreases or stays lower in easy categories.
- FPS/P95 latency: mixed; improved if paired with cheap fallback/cache.
- Implementation risk: low.
- Likely files/functions: config and `OnlineSceneDifficultyEstimator`.
- CDnet2014 P4 rerun required: yes.
- Expected validation command: new v1.7 config with category priors.

## 10. Add Required Extra Logs

Problem addressed: current logs permit high-level diagnosis but not exact causal attribution for latency or stale reuse.

Expected effect:

- FMeasure: no direct effect.
- Event_F1: no direct effect.
- Activation: no direct effect.
- FPS/P95 latency: no direct effect, but enables targeted optimization.
- Implementation risk: low.
- Likely files/functions: frame row assembly in `process_sequence`, `edge_profile.csv`, `write_online_controller_diagnostics`.
- CDnet2014 P4 rerun required: smoke-only for logging changes; full rerun only after algorithm changes.
- Expected validation command: `python src/run_experiment.py --config configs/cdnet_smoke_test.yaml`.

## Recommended Minimal v1.7 Bundle

Implement together:

- Shared gate feature cache.
- Hard P3 guards.
- Calibrated hysteresis.
- Low-activation forced refresh.
- Required extra logs.

Then retrain the policy on empirical winners as the next step if the minimal bundle does not close most of the FMeasure gap.
