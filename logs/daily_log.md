# Daily Log

## 2026-04-28

- Da co `ASMAG_TR_CONTROLLER` category-aware result trong `outputs/full_cdnet2014_controller_sampled_metrics`.
- Da co full CDnet2014 sampled result trong `outputs/full_cdnet2014_sampled_full_metrics`.
- Da tao controller gain summary va ASMAG-TRC final ablation report cho category-aware controller.
- Da thiet ke va smoke test `ASMAG_TR_CONTROLLER_ONLINE`.
- Da chay `ASMAG_TR_CONTROLLER_ONLINE_P3TUNED` trong `outputs/q2_core_extended_online_controller_p3tuned`.
- Auto-recover stale jobs da duoc them vao `run_experiment.py` va config p3tuned.
- Trang thai truoc resume: `completed=111`, `pending=17`, `running=0`, `failed=0`.
- Lenh resume:

```bat
python src/run_experiment.py --config configs/q2_core_extended_online_controller_p3tuned.yaml
```

- Da resume 9C-Fix p3tuned den hoan tat: `completed=128`, `pending=0`, `running=0`, `failed=0`, `current_job=-`.
- Timeout lan dau de lai `nightVideos/winterStreet/ASMAG_TR_CONTROLLER` o `running`; lan resume sau chay tiep job do va hoan tat 3 job cuoi ma khong xoa checkpoint/output completed.
- Da tao/cap nhat bao cao cuoi trong `outputs/q2_core_extended_online_controller_p3tuned`: `final_main_comparison.csv`, `best_by_metric.csv`, `gain_summary.csv`, `mode_usage_summary.csv`, `scene_difficulty_distribution.csv`, `category_wise_mode_usage.csv`, `summary_pareto_metrics.csv`, `auto_research_summary.md`.
- Da hoan tat 9D calibrated online controller trong `outputs/q2_core_extended_online_controller_calibrated`: `completed=128`, `pending=0`, `running=0`, `failed=0`.
- Trainer `src/controller/train_online_mode_policy.py` chon `logistic_regression` voi validation accuracy `0.6870`, macro F1 `0.5522`, P3 fallback recall `0.7379`.
- `ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED` dat FMeasure `0.4196`, Event_F1 `0.7445`, Activation `0.7163`, Energy/frame `5.2610`, AE_Score `0.4573`.
- So voi p3tuned: FMeasure gain `+0.0085`, Event_F1 gain `+0.0025`, AE_Score gain `+0.0102`; hard-category P3_FALLBACK_rate tang `0.2207 -> 0.6322`.
- Da commit moc 9C p3tuned: `39ba931 Complete 9C online controller p3tuned experiment`.
- Da commit moc 9D calibrated: `cb809b5 Add calibrated online controller for ASMAG-TRC`.
- Luu y lan sau: con file ngoai scope chua commit (`RUNBOOK.md`, smoke/sim outputs, mot so controller sampled reports, `gates.py`, analyzer/helper, `__pycache__`). Khong revert neu khong duoc yeu cau.
- Huong tiep theo hop ly: dinh vi ket qua 9D cho paper, sau do chon G2 edge profiling hoac G3 official-like frame_step=1.

## 2026-04-28 G2G3 Setup + Smoke

- Da tao/cap nhat config G2G3: `configs/full_cdnet2014_official_edge_profile_pc.yaml`.
- Da tao run plan full CDnet2014 official-like: `configs/full_cdnet2014_official_edge_video_run_plan.csv`.
- Run plan quet duoc `53` video hop le trong 11 category, tuong ung `318` job cho 6 pipeline cot loi.
- Output hien tai: `outputs/full_cdnet2014_official_edge_profile_pc`.
- Runner da ho tro `--run-plan`, `--max-videos-per-run`, `--progress-only`, `--category`, `--video`, `--pipeline`, `--max-frames`.
- Edge CPU-only settings: `cuda_enabled=false`, `batch_size=1`, OpenCV/Torch threads `4`, sequential video processing, `parallel_jobs=1`.
- Progress system co stale running recovery `10` phut va khong xoa output/checkpoint completed.
- Da chay smoke Step 2 dung yeu cau, khong chay Step 3/4/5.

Smoke command:

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --category baseline --video highway --pipeline P3_MOG2 --max-frames 50
```

Smoke result:

- Category/video/pipeline: `baseline/highway/P3_MOG2`
- Frames processed: `50`
- CDnet_FMeasure: `0.8727`
- Event_F1: `1.0000`
- Activation: `1.0000`
- Avg_FPS: `4.1100`
- P95_latency_ms: `313.8325`
- Avg CPU: `145.0540`
- Avg RAM MB: `550.8272`
- Energy/frame: `6.7000`
- Simulated_runtime_energy/frame: `7.9084`

Progress after smoke: `completed=1`, `pending=317`, `running=0`, `failed=0`, `current_job=-`.

Next step neu user xac nhan: `G2G3-Test1Video` cho `baseline/highway` voi 6 pipeline va `max_frames=300`.
