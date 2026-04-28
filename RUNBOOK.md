# RUNBOOK - ASMAG-TRC

## G2G3 Official-like Edge CPU-only Profiling

Current G2G3 output:

- Config: `configs/full_cdnet2014_official_edge_profile_pc.yaml`
- Run plan: `configs/full_cdnet2014_official_edge_video_run_plan.csv`
- Output: `outputs/full_cdnet2014_official_edge_profile_pc`
- Pipelines: `P1_YOLO_Only`, `P2_FrameDiff`, `P3_MOG2`, `ASMAG_TR_FAST`, `ASMAG_TR_CONTROLLER`, `ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED`
- Full plan size: 53 videos x 6 pipelines = 318 jobs

Do not delete old checkpoints or outputs. Do not touch/delete:

- `outputs/full_cdnet2014_sampled_full_metrics`
- `outputs/full_cdnet2014_controller_sampled_metrics`
- `outputs/q2_core_extended_online_controller_p3tuned`
- `outputs/q2_core_extended_online_controller_calibrated`

### G2G3 Progress-only

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --progress-only
```

### G2G3 Smoke Test

Already completed for `baseline/highway/P3_MOG2` with `max_frames=50`.

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --category baseline --video highway --pipeline P3_MOG2 --max-frames 50
```

Latest smoke result:

- Frames processed: `50`
- CDnet_FMeasure: `0.8727`
- Event_F1: `1.0000`
- Activation: `1.0000`
- Avg_FPS: `4.1100`
- P95 latency: `313.8325 ms`
- Avg CPU: `145.0540`
- Avg RAM: `550.8272 MB`
- Energy/frame: `6.7000`
- Simulated_runtime_energy/frame: `7.9084`

### G2G3 Test One Video

Run only after user confirmation.

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --category baseline --video highway --max-frames 300
```

### G2G3 Representative Run

Run only after user confirmation. Target videos:

- `baseline/highway`
- `baseline/office`
- `dynamicBackground/canoe`
- `cameraJitter/traffic`
- `thermal/library`
- `turbulence/turbulence2`

Recommended approach: run the selected videos one by one with `--max-frames 300`, or temporarily mark other run-plan rows as not pending before using `--max-videos-per-run 6`.

### G2G3 Full Official-like Resume

Safe default, one video per run:

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --run-plan configs/full_cdnet2014_official_edge_video_run_plan.csv --max-videos-per-run 1
```

Overnight mode:

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --run-plan configs/full_cdnet2014_official_edge_video_run_plan.csv --max-videos-per-run 10
```

Runner behavior:

- Completed jobs are skipped only when output is complete and `frames_done >= frames_expected`.
- Stale `running` jobs older than 10 minutes are recovered to `pending`.
- `run_progress.csv` is updated after every completed or failed job.
- `daily_progress_report.md` is updated after runs.

## Resume 9C-Fix

```bat
python src/run_experiment.py --config configs/q2_core_extended_online_controller_p3tuned.yaml
```

The config enables stale job recovery:

```yaml
progress:
  auto_recover_stale_jobs: true
  stale_running_minutes: 10
```

## Check Progress

```bat
python - <<PY
import pandas as pd
df = pd.read_csv("outputs/q2_core_extended_online_controller_p3tuned/run_progress.csv")
print(df.status.value_counts())
print(df[df.status == "running"])
print(df[df.status == "pending"].head(1))
PY
```

PowerShell-friendly alternative:

```powershell
Import-Csv outputs/q2_core_extended_online_controller_p3tuned/run_progress.csv |
  Group-Object status | Select-Object Name,Count
```

## Generate Final Report

Run after progress reaches `completed=128`, `pending=0`, `running=0`, `failed=0`.

Expected outputs:

- `outputs/q2_core_extended_online_controller_p3tuned/final_main_comparison.csv`
- `outputs/q2_core_extended_online_controller_p3tuned/best_by_metric.csv`
- `outputs/q2_core_extended_online_controller_p3tuned/gain_summary.csv`
- `outputs/q2_core_extended_online_controller_p3tuned/mode_usage_summary.csv`
- `outputs/q2_core_extended_online_controller_p3tuned/scene_difficulty_distribution.csv`
- `outputs/q2_core_extended_online_controller_p3tuned/category_wise_mode_usage.csv`
- `outputs/q2_core_extended_online_controller_p3tuned/auto_research_summary.md`

## Run Edge Profiling

```bat
python src/run_experiment.py --config configs/<edge_profile_config>.yaml
```

Use selected final pipelines only to reduce runtime.

## Run Official-like CDnet One-video Mode

Use a temporary config with:

```yaml
evaluation:
  use_temporal_roi: true
  warmup_frames: 50
  frame_step: 1
  max_frames_per_video: null
videos:
  <category>: [<video>]
```

Then run:

```bat
python src/run_experiment.py --config configs/<official_like_one_video>.yaml
```

## Commit Results

```bat
git status
git add PROJECT_STATE.md TASK_BOARD.md RUNBOOK.md NEXT_PROMPT_FOR_CODEX.md logs outputs/q2_core_extended_online_controller_p3tuned
git commit -m "Update ASMAG-TRC 9C-Fix state and results"
```
