# NEXT PROMPT FOR CODEX

Hay doc `PROJECT_STATE.md`, `TASK_BOARD.md`, `RUNBOOK.md`. Sau do kiem tra `run_progress.csv` trong `outputs/full_cdnet2014_official_edge_profile_pc`, auto-recover stale jobs neu co, va tiep tuc task dang In Progress.

Trang thai moi nhat:

- Current task: G2G3 Official-like CDnet2014 frame_step=1 + Edge CPU-only profiling.
- Current phase: Setup + Smoke Test completed.
- Current config: `configs/full_cdnet2014_official_edge_profile_pc.yaml`
- Current run plan: `configs/full_cdnet2014_official_edge_video_run_plan.csv`
- Current output: `outputs/full_cdnet2014_official_edge_profile_pc`
- Pipelines: `P1_YOLO_Only`, `P2_FrameDiff`, `P3_MOG2`, `ASMAG_TR_FAST`, `ASMAG_TR_CONTROLLER`, `ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED`.
- Current progress after smoke: `completed=1`, `pending=317`, `running=0`, `failed=0`, `current_job=-`.

Smoke test da chay:

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --category baseline --video highway --pipeline P3_MOG2 --max-frames 50
```

Smoke result:

- `baseline/highway/P3_MOG2`
- frames processed `50`
- CDnet_FMeasure `0.8727`
- Event_F1 `1.0000`
- Activation `1.0000`
- Avg_FPS `4.1100`
- P95_latency_ms `313.8325`
- Avg CPU `145.0540`
- Avg RAM MB `550.8272`
- Energy/frame `6.7000`
- Simulated_runtime_energy/frame `7.9084`

Quan trong:

- Khong xoa bat ky output/checkpoint cu nao.
- Khong dung/xoa: `outputs/full_cdnet2014_sampled_full_metrics`, `outputs/full_cdnet2014_controller_sampled_metrics`, `outputs/q2_core_extended_online_controller_p3tuned`, `outputs/q2_core_extended_online_controller_calibrated`.
- Khong chay `G2G3-Test1Video`, `G2G3-Representative`, hoac `G2G3-FullOfficialLike` neu user chua xac nhan.
- Smoke artifact chi co 50 frame; runner da co kiem tra `frames_done >= frames_expected` de full official resume khong bi skip sai.

Lenh resume chinh:

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --run-plan configs/full_cdnet2014_official_edge_video_run_plan.csv --max-videos-per-run 1
```

Lenh check progress khong chay:

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --progress-only
```

Neu user xac nhan chuyen sang one-video 6 pipeline, chay:

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --category baseline --video highway --max-frames 300
```
