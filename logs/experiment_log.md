# Experiment Log

## q2_core_full_metrics

- Purpose: Core Q2 baseline/full metrics run.
- Output: `outputs/q2_core_full_metrics`
- Status: completed earlier.

## q2_core_extended_full_metrics

- Purpose: Extended category run used for ASMAG-TR analysis and online controller simulation.
- Output: `outputs/q2_core_extended_full_metrics`
- Status: completed.

## full_cdnet2014_sampled_full_metrics

- Purpose: Full sampled CDnet2014 metrics for P1/P2/P3/ASMAG_TR_ACC/ASMAG_TR_FAST.
- Output: `outputs/full_cdnet2014_sampled_full_metrics`
- Status: completed.
- Key artifacts: `asmag_vs_p3_gap_analysis.csv`, `asmag_vs_p3_gap_summary.md`.

## full_cdnet2014_controller_sampled_metrics

- Purpose: Category-aware `ASMAG_TR_CONTROLLER` evaluation.
- Output: `outputs/full_cdnet2014_controller_sampled_metrics`
- Status: completed.
- Key artifacts: `controller_mode_usage.csv`, `final_main_comparison.csv`, `controller_gain_summary.csv`, `asmag_trc_report_summary.md`.

## q2_core_extended_online_controller_p3tuned

- Purpose: 9C-Fix real run for `ASMAG_TR_CONTROLLER_ONLINE_P3TUNED`.
- Config: `configs/q2_core_extended_online_controller_p3tuned.yaml`
- Output: `outputs/q2_core_extended_online_controller_p3tuned`
- Status: completed.
- Final progress: `completed=128`, `pending=0`, `running=0`, `failed=0`.
- Resume command: `python src/run_experiment.py --config configs/q2_core_extended_online_controller_p3tuned.yaml`.

## q2_core_extended_online_controller_calibrated

- Purpose: 9D calibrated online controller using pseudo-labels from category-aware policy.
- Config: `configs/q2_core_extended_online_controller_calibrated.yaml`
- Output: `outputs/q2_core_extended_online_controller_calibrated`
- Status: completed.
- Final progress: `completed=128`, `pending=0`, `running=0`, `failed=0`.
- Key result: `ONLINE_CALIBRATED` FMeasure `0.4196`, Event_F1 `0.7445`, Activation `0.7163`, Energy/frame `5.2610`.

## full_cdnet2014_official_edge_profile_pc

- Purpose: G2G3 official-like CDnet2014 `frame_step=1` plus Edge CPU-only profiling on PC.
- Config: `configs/full_cdnet2014_official_edge_profile_pc.yaml`
- Run plan: `configs/full_cdnet2014_official_edge_video_run_plan.csv`
- Output: `outputs/full_cdnet2014_official_edge_profile_pc`
- Status: setup + smoke completed; waiting for user confirmation before one-video 6-pipeline test.
- Pipelines: `P1_YOLO_Only`, `P2_FrameDiff`, `P3_MOG2`, `ASMAG_TR_FAST`, `ASMAG_TR_CONTROLLER`, `ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED`.
- Full plan: 53 videos x 6 pipelines = 318 jobs.
- Current progress after smoke: `completed=1`, `pending=317`, `running=0`, `failed=0`.
- Smoke command: `python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --category baseline --video highway --pipeline P3_MOG2 --max-frames 50`.
- Smoke result: frames `50`, FMeasure `0.8727`, Event_F1 `1.0000`, Activation `1.0000`, Avg_FPS `4.1100`, P95 latency `313.8325 ms`, Energy/frame `6.7000`, Simulated_runtime_energy/frame `7.9084`.
