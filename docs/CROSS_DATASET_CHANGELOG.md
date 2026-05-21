# Cross-Dataset Change Log

## 2026-05-08

- Added dataset adapters for LASIESTA, SBI/SBMI2015, BMC2012, and a CDnet2014 smoke path.
- Added a unified `run_cross_dataset.py` runner with `--config`, `--dataset_root`, `--pipelines`, `--videos`, `--max_frames`, `--resume`, and `--output_dir`.
- Added binary mask normalization, ignore-mask utilities, and aggregate binary mask metrics.
- Added resumable `run_progress.csv` support for cross-dataset jobs.
- Added requested cross-dataset outputs: `per_frame_log.csv`, `per_video_summary.csv`, `final_summary.csv`, `failure_cases.csv`, and `charts/`.
- Added aggregation, plotting, and paired-stat utility scripts under `tools/`.
- Added full-run configs for LASIESTA, SBI/SBMI2015, BMC2012, plus a CDnet smoke-test config.

The frozen ASMAG-TRC v1.6 processing path is not modified. Cross-dataset runs materialize normalized adapter caches inside `outputs/cross_dataset_full_v1_6/...` and call the existing `src/run_experiment.py::process_sequence` entry point.
