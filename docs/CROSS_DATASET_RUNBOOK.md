# ASMAG-TRC Cross-Dataset Runbook

This runner evaluates the frozen ASMAG-TRC v1.6 pipelines on LASIESTA, SBI/SBMI2015, BMC2012, and CDnet smoke data without writing into the existing CDnet result folders.

## Smoke Test

From the project root:

```powershell
python run_cross_dataset.py --config configs/cdnet_smoke_test.yaml
```

Expected output:

```text
outputs/cross_dataset_full_v1_6/cdnet_smoke_test/
  config.yaml
  run_progress.csv
  per_frame_log.csv
  per_video_summary.csv
  final_summary.csv
  failure_cases.csv
  charts/
```

For a smaller parser/runtime check that writes into a separate output folder:

```powershell
python run_cross_dataset.py --config configs/cdnet_smoke_test.yaml --max_frames 5 --pipelines P2_FrameDiff P3_MOG2 --output_dir outputs/cross_dataset_full_v1_6/cdnet_smoke_mock
```

## Full Runs

Update `dataset_root` in the matching config, or override it from the command line:

```powershell
python run_cross_dataset.py --config configs/cross_lasiesta_full.yaml --dataset_root D:/datasets/LASIESTA
python run_cross_dataset.py --config configs/cross_sbi2015_full.yaml --dataset_root D:/datasets/SBI2015
python run_cross_dataset.py --config configs/cross_bmc_full.yaml --dataset_root D:/datasets/BMC2012
```

Resume is enabled by default. Re-run the same command to continue from `run_progress.csv`.

Useful overrides:

```powershell
python run_cross_dataset.py --config configs/cross_lasiesta_full.yaml --videos category/video_a category/video_b
python run_cross_dataset.py --config configs/cross_lasiesta_full.yaml --pipelines P3_MOG2 ASMAG_TR_CONTROLLER_ONLINE
python run_cross_dataset.py --config configs/cross_lasiesta_full.yaml --max_frames 100
python run_cross_dataset.py --config configs/cross_lasiesta_full.yaml --resume false
```

## Aggregation Only

If a run was interrupted after raw sequence outputs were written:

```powershell
python tools/aggregate_cross_dataset.py --output_dir outputs/cross_dataset_full_v1_6/lasiesta_full --dataset_name lasiesta
python tools/plot_cross_dataset.py --output_dir outputs/cross_dataset_full_v1_6/lasiesta_full
python tools/stat_cross_dataset.py --output_dir outputs/cross_dataset_full_v1_6/lasiesta_full
```

## Dataset Layout

Adapters search for common sequence layouts such as:

```text
<dataset>/<category>/<video>/input/*
<dataset>/<category>/<video>/groundtruth/*
```

They also recognize common alternatives like `frames`, `images`, `gt`, `GT`, `masks`, and `Foreground`. Ground truth is normalized into an internal CDnet-style cache under the cross-output directory, using foreground `255`, background `0`, and ignore `85`. Existing CDnet2014 outputs are not touched.
