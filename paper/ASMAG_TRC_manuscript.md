# ASMAG-TRC Manuscript Outline

## Working Title

Adaptive Multi-Mode Inference Control for Real-Time Background Change Detection on Edge CPUs

## Abstract

- Problem: real-time video background change detection needs a balance between accuracy, latency, and energy on constrained edge CPUs.
- Method: ASMAG-TRC switches between lightweight reuse, fast motion cues, MOG2 fallback, and YOLO-based accurate inference.
- Evaluation: CDnet2014 official-like `frame_step=1` run with 53 videos and 318 pipeline jobs.
- Key result: `ASMAG_TR_CONTROLLER` gives the best CDnet_FMeasure and Event_F1, while `ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED` preserves most accuracy with lower activation and energy.
- Contribution: practical adaptive inference controller and reproducible edge profiling results.

## 1. Introduction

- Motivation: edge video systems cannot afford full detector inference on every frame.
- Gap: many background subtraction or detection approaches optimize quality, but do not expose a deployment-oriented control policy across accuracy, latency, and energy.
- Proposed idea: frame-level adaptive control that chooses between fast, accurate, and fallback modes.
- Research questions:
  - Can adaptive control preserve detection quality while reducing activation and energy?
  - Does the trend hold in full official-like CDnet2014, not only sampled runs?
  - What trade-offs appear under CPU-only edge profiling?

## 2. Related Work

- Background subtraction and CDnet2014.
- Object detection for change detection.
- Dynamic inference and early-exit/adaptive computation.
- Edge AI profiling: latency, CPU, memory, and energy proxies.

## 3. Method

### 3.1 Pipeline Set

- `P1_YOLO_Only`: full detector baseline.
- `P2_FrameDiff`: lightweight frame-difference baseline.
- `P3_MOG2`: classical background subtraction baseline.
- `ASMAG_TR_FAST`: fast adaptive variant.
- `ASMAG_TR_CONTROLLER`: upper-bound adaptive controller.
- `ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED`: deployable calibrated online controller.

### 3.2 Adaptive Control

- Inputs: motion/scene cues, reuse state, controller policy, and calibrated mode decisions.
- Outputs: selected mode and resulting mask/detection result.
- Deployment goal: reduce expensive activation while retaining event-level and CDnet quality.

### 3.3 Metrics

- Accuracy: CDnet_FMeasure, Event_F1, mAP_50 where available.
- Efficiency: Activation, Reuse_rate, Avg_FPS, latency P50/P95/P99.
- Resource profile: process CPU, RAM, Energy/frame, Simulated_runtime_energy/frame.
- Combined score: AE_Score and Pareto status.

## 4. Experimental Setup

- Dataset: CDnet2014 selected official-like run plan.
- Scope: 53 videos, 6 pipelines, 318 jobs.
- Configuration: `configs/full_cdnet2014_official_edge_profile_pc.yaml`.
- Output: `outputs/full_cdnet2014_official_edge_profile_pc`.
- Edge profile: CPU-only PC profiling with frame_step=1.
- Reproducibility:
  - Run plan: `configs/full_cdnet2014_official_edge_video_run_plan.csv`.
  - Progress file: `outputs/full_cdnet2014_official_edge_profile_pc/run_progress.csv`.

## 5. Results

### 5.1 Main Pipeline Comparison

- Use `paper/tables/table_2_main_results.csv`.
- Report CDnet_FMeasure, Event_F1, mAP_50, Activation, Reuse_rate, Avg_FPS, latency, CPU/RAM, energy, AE_Score, Pareto.
- Main takeaway: `ASMAG_TR_CONTROLLER` is the quality upper bound; `ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED` is the deployable adaptive variant.

### 5.2 Gains Against P3_MOG2

- Use `paper/tables/table_3_gain_vs_p3.csv`.
- Discuss:
  - `ASMAG_TR_CONTROLLER` vs `P3_MOG2`.
  - `ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED` vs `P3_MOG2`.
  - `ASMAG_TR_FAST` and `P2_FrameDiff` as efficiency-oriented baselines.

### 5.3 Best-by-Metric Summary

- Use `paper/tables/table_4_best_by_metric.csv`.
- Highlight:
  - Best CDnet_FMeasure.
  - Best Event_F1.
  - Fastest Avg_FPS.
  - Lowest P95 latency.
  - Lowest activation and energy.

### 5.4 Figures

- `paper/figures/fmeasure_by_pipeline.png`
- `paper/figures/event_f1_by_pipeline.png`
- `paper/figures/activation_by_pipeline.png`
- `paper/figures/latency_p95_by_pipeline.png`
- `paper/figures/pareto_fmeasure_energy.png`

## 6. Per-Category and Per-Video Analysis

- Use appendix files:
  - `paper/appendix/per_category_summary.csv`
  - `paper/appendix/per_video_summary.csv`
  - `paper/appendix/per_category_fmeasure_heatmap.png`
  - `paper/appendix/per_category_latency_heatmap.png`
  - `paper/appendix/per_category_activation_heatmap.png`
- Discuss category-specific robustness and failure modes.
- Emphasize that latency and FPS vary strongly by scene.

## 7. Discussion

- Does G2G3 official-like confirm sampled results?
  - Yes: quality-oriented controller variants remain strongest; FrameDiff remains fastest and lightest; calibrated online control provides a deployable balance.
- Is `ASMAG_TR_CONTROLLER` still a good upper bound?
  - Yes, it achieves the best CDnet_FMeasure and Event_F1.
- Is `ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED` deployable?
  - Yes, it trades a small FMeasure gap for activation and energy savings, with transparent latency overhead.
- Paper placement:
  - Main paper: `table_2_main_results.csv`, `table_3_gain_vs_p3.csv`, Pareto figure, FMeasure/Event_F1 figures.
  - Appendix: per-video/per-category summaries and heatmaps.

## 8. Limitations

- CDnet2014 is a background-subtraction benchmark, not a broad modern detection benchmark.
- Energy is estimated/simulated, not measured with hardware power instrumentation.
- Edge profiling was CPU-only on a PC profile, not a fixed embedded board.
- Controller behavior depends on calibration and scene distribution.
- The goal is adaptive inference efficiency, not absolute segmentation SOTA.

## 9. Conclusion

- ASMAG-TRC demonstrates that adaptive multi-mode inference can preserve strong change-detection quality while reducing activation and energy.
- Full G2G3 completed 318/318 jobs and supports paper-ready reporting.
- The recommended main deployable variant is `ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED`; the upper-bound reference is `ASMAG_TR_CONTROLLER`.

## Paper Artifact Map

- Main results table: `paper/tables/table_2_main_results.csv`
- Gain table: `paper/tables/table_3_gain_vs_p3.csv`
- Best-by-metric table: `paper/tables/table_4_best_by_metric.csv`
- Main figures: `paper/figures/`
- Appendix tables and heatmaps: `paper/appendix/`
