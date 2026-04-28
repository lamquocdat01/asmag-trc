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
- Status: in progress.
- Current progress: `completed=111`, `pending=17`, `running=0`, `failed=0`.
- Resume command: `python src/run_experiment.py --config configs/q2_core_extended_online_controller_p3tuned.yaml`.

