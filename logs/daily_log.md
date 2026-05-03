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

## 2026-04-28 G2G3 Test1Video-Safe

- Da chay `baseline/highway` voi du 6 pipeline cot loi, `max_frames=100`, `frame_step=1`, `use_temporal_roi=true`.
- Khong chay representative/full.
- Khong xoa checkpoint/output cu; artifact smoke `P3_MOG2` 50-frame da duoc backup trong `outputs/full_cdnet2014_official_edge_profile_pc/raw_results/baseline/highway/P3_MOG2_smoke50_backup`.
- Da tao `outputs/full_cdnet2014_official_edge_profile_pc/test1video_summary.csv`.
- Da tao `outputs/full_cdnet2014_official_edge_profile_pc/test1video_summary.md`.
- Progress sau run: `completed=6`, `pending=312`, `running=0`, `failed=0`, `current_job=-`.

Ket qua tom tat:

- `P1_YOLO_Only`: FMeasure `0.8974`, Event_F1 `0.9362`, Activation `1.0000`, Avg_FPS `3.1589`, P95 `1485.93 ms`.
- `P2_FrameDiff`: FMeasure `0.0041`, Event_F1 `0.0198`, Activation `0.0100`, Avg_FPS `74.2091`, P95 `2.01 ms`.
- `P3_MOG2`: FMeasure `0.9141`, Event_F1 `1.0000`, Activation `1.0000`, Avg_FPS `3.6588`, P95 `354.88 ms`.
- `ASMAG_TR_FAST`: FMeasure `0.8315`, Event_F1 `0.9744`, Activation `0.4900`, Avg_FPS `74.5167`, P95 `320.21 ms`.
- `ASMAG_TR_CONTROLLER`: FMeasure `0.8484`, Event_F1 `0.9848`, Activation `0.5900`, Avg_FPS `66.3592`, P95 `311.45 ms`.
- `ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED`: FMeasure `0.8392`, Event_F1 `0.9691`, Activation `0.4500`, Avg_FPS `30.1787`, P95 `358.90 ms`.

Nhan xet: nen tang len `max_frames=300` cho `baseline/highway` truoc khi representative/full, nhung chi chay khi user xac nhan.

## 2026-04-28 G2G3 Test1Video-300

- Da chay `baseline/highway` voi du 6 pipeline cot loi, `max_frames=300`, `frame_step=1`, `use_temporal_roi=true`.
- Khong chay representative/full.
- Khong xoa output cu; output 100-frame da backup thanh `test1video_summary_100.csv`, `test1video_summary_100.md`, va `raw_results/baseline/highway/<pipeline>_test100_backup`.
- Da tao `outputs/full_cdnet2014_official_edge_profile_pc/test1video_summary_300.csv`.
- Da tao `outputs/full_cdnet2014_official_edge_profile_pc/test1video_summary_300.md`.
- Da tao `outputs/full_cdnet2014_official_edge_profile_pc/test1video_100_vs_300_comparison.csv`.
- Progress sau run: `completed=6`, `pending=312`, `running=0`, `failed=0`, `current_job=-`.

Ket qua tom tat 300-frame:

- `P1_YOLO_Only`: FMeasure `0.9672`, Event_F1 `0.9796`, Activation `1.0000`, Avg_FPS `4.0409`, P95 `325.36 ms`.
- `P2_FrameDiff`: FMeasure `0.9169`, Event_F1 `0.6696`, Activation `0.5033`, Avg_FPS `89.7466`, P95 `306.36 ms`.
- `P3_MOG2`: FMeasure `0.9678`, Event_F1 `1.0000`, Activation `1.0000`, Avg_FPS `3.3157`, P95 `720.15 ms`.
- `ASMAG_TR_FAST`: FMeasure `0.9589`, Event_F1 `0.9916`, Activation `0.7300`, Avg_FPS `24.9539`, P95 `631.11 ms`.
- `ASMAG_TR_CONTROLLER`: FMeasure `0.9591`, Event_F1 `0.9933`, Activation `0.7333`, Avg_FPS `34.0486`, P95 `426.37 ms`.
- `ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED`: FMeasure `0.9593`, Event_F1 `0.9899`, Activation `0.7167`, Avg_FPS `14.7360`, P95 `563.81 ms`.

Ket luan: 300-frame on dinh hon 100-frame. `P2_FrameDiff` khong con FMeasure qua thap nhung Event_F1 van thap; `P3_MOG2` activation van `1.0000`; `ONLINE_CALIBRATED` van tiet kiem activation/energy so voi `P3_MOG2`. Nen chuyen sang representative 6 video neu user xac nhan.

## 2026-04-28 G2G3 Representative

- Da chay representative official-like frame_step=1 + Edge CPU-only profiling tren 6 video dai dien: `baseline/highway`, `baseline/office`, `dynamicBackground/canoe`, `cameraJitter/traffic`, `thermal/library`, `turbulence/turbulence2`.
- Moi video chay 6 pipeline cot loi voi `max_frames=300`, `warmup_frames=50`, `use_temporal_roi=true`, `parallel_jobs=1`.
- Khong chay full CDnet2014.
- Khong xoa output/checkpoint cu.
- Progress sau representative: `completed=36`, `pending=282`, `running=0`, `failed=0`, `current_job=-`.

Representative outputs:

- `representative_final_main.csv`
- `representative_edge_profile_summary.csv`
- `representative_per_video_summary.csv`
- `representative_per_category_summary.csv`
- `representative_gain_summary.csv`
- `representative_auto_research_summary.md`
- charts `representative_*.png` trong `outputs/full_cdnet2014_official_edge_profile_pc/charts/`

Ket qua representative:

- Best FMeasure: `P3_MOG2` (`0.8536`).
- Best Event_F1: `P3_MOG2` (`0.9323`).
- Fastest: `P2_FrameDiff` (`104.10 FPS`).
- Lowest P95 latency: `P2_FrameDiff` (`261.43 ms`).
- Lowest activation/energy: `P2_FrameDiff` (`Activation=0.5511`, `Energy/frame=4.0556`).
- `ASMAG_TR_CONTROLLER`: FMeasure `0.8486`, Event_F1 `0.9149`, Activation `0.7239`, Energy/frame `5.3777`.
- `ONLINE_CALIBRATED`: FMeasure `0.7675`, Event_F1 `0.8948`, Activation `0.6683`, Energy/frame `5.1159`.
- ONLINE_CALIBRATED giu efficiency advantage so voi P3_MOG2 (`Activation saving=0.1061`, `Energy saving=0.4563`) nhung mat quality tren hard scenes, dac biet turbulence.
- Estimated 53-video run voi cung cap 300-frame: `5.38h`; full official-like khong cap frame se lau hon dang ke.
- Recommendation: chi chuyen sang full official-like khi user xac nhan; neu chay, nen batch `6-10` videos moi dem voi resume enabled.

## 2026-04-29 Post-Restart G2G3 State Check

- Da doc lai project state, task board, runbook, next prompt, daily log, experiment log.
- Da kiem tra `outputs/full_cdnet2014_official_edge_profile_pc/run_progress.csv`.
- Progress hien tai: `total=318`, `completed=36`, `pending=282`, `running=0`, `failed=0`, `current_job=-`.
- Khong co stale `running` job can reset; khong co Python experiment process dang chay.
- Job completed cuoi cung: `turbulence/turbulence2/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED` luc `2026-04-28T23:43:30`.
- Job pending tiep theo: `badWeather/blizzard/P1_YOLO_Only`.
- Representative 6 video da hoan tat du `36/36`; khong thieu video/pipeline nao.
- Buoc hien tai: `G2G3-FullOfficialLike` dang `Pending`, cho user xac nhan truoc khi resume.

## 2026-04-29 G2G3 ProgressMonitor Upgrade

- Da nang cap `src/run_experiment.py` de in block `[G2G3 PROGRESS]` khi job dang chay.
- Da them `src/utils/progress_monitor.py` de tinh overall percent, ETA, ghi `live_progress.json`, ghi `live_progress.md`, va in progress-only report.
- Da cap nhat config G2G3 voi `print_progress_every_frames=25`, `write_progress_every_frames=25`, `progress_heartbeat_seconds=30`, `show_eta=true`, `show_current_frame=true`, `show_overall_percent=true`.
- Da them option `--show-live-progress` de doc live progress ma khong chay experiment.
- `run_progress.csv` se co them `progress_percent` va duoc heartbeat trong luc job chay.
- Khi chay `--progress-only` voi config full official-like uncapped, 36 job representative 300-frame duoc normalize ve `pending` vi `frames_done < frames_expected`; output/checkpoint representative khong bi xoa.
- Progress full official-like hien tai sau normalize: `completed=0`, `pending=318`, `running=0`, `failed=0`.
- Khong chay resume/full/representative trong buoc upgrade nay.

## 2026-04-29 G2G3 SingleJob Runner

- Da bo sung/kiem tra `--max-jobs-per-run 1` de moi lan chi chay dung 1 job: 1 category / 1 video / 1 pipeline.
- Da them block mo dau `G2G3 SINGLE-JOB RUN STARTED`.
- Da nang cap live progress terminal voi progress bar, current job index, completed videos, current video pipeline progress, FPS, latency, CPU/RAM process, energy/frame, simulated energy/frame, ETA va fun status line.
- Da mo rong `live_progress.json` va `live_progress.md` voi cac field single-job runner can theo doi.
- Da cap nhat `RUNBOOK.md`, `NEXT_PROMPT_FOR_CODEX.md`, `PROJECT_STATE.md`, `TASK_BOARD.md`.
- Chi chay `--progress-only` de kiem tra; khong chay experiment job.
- Progress hien tai: `completed=6/318`, `pending=312`, `running=0`, `failed=0`, completed videos `1/53`, next pending `badWeather/skating/P1_YOLO_Only`.

## 2026-04-29 G2G3 Run 10 Jobs

- Da doc `outputs/full_cdnet2014_official_edge_profile_pc/run_progress.csv` truoc khi chay.
- Pre-run progress: `completed=7/318`, `pending=311`, `running=0`, `failed=0`; khong co stale running process.
- Da resume bang lenh `python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --run-plan configs/full_cdnet2014_official_edge_video_run_plan.csv --max-jobs-per-run 10`.
- Da chay them `10` jobs, tat ca completed; khong co failed job.
- Jobs completed them: `badWeather/skating/P2_FrameDiff`, `badWeather/skating/P3_MOG2`, `badWeather/skating/ASMAG_TR_FAST`, `badWeather/skating/ASMAG_TR_CONTROLLER`, `badWeather/skating/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED`, `badWeather/snowFall/P1_YOLO_Only`, `badWeather/snowFall/P2_FrameDiff`, `badWeather/snowFall/P3_MOG2`, `badWeather/snowFall/ASMAG_TR_FAST`, `badWeather/snowFall/ASMAG_TR_CONTROLLER`.
- Post-run progress: `completed=17/318`, `pending=301`, `running=0`, `failed=0`, overall `5.3459%`, completed videos `2/53`.
- Last completed: `badWeather/snowFall/ASMAG_TR_CONTROLLER`.
- Next pending: `badWeather/snowFall/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED`.
- Files updated: `run_progress.csv`, `daily_progress_report.md`, `experiment_log.md`, `live_progress.json`, `live_progress.md`, `PROJECT_STATE.md`, `TASK_BOARD.md`, `logs/daily_log.md`.
- Resume tiep theo an toan voi cung lenh `--max-jobs-per-run 10`.

- `2026-04-29T21:34:56` G2G3 auto status: completed badWeather/snowFall/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=18/318, pending=300, running=0, failed=0, videos=3/53, session_completed=1, last=badWeather/snowFall/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=badWeather/wetSnow/P1_YOLO_Only

- `2026-04-29T21:49:32` G2G3 auto status: completed badWeather/wetSnow/P1_YOLO_Only; completed=19/318, pending=299, running=0, failed=0, videos=3/53, session_completed=2, last=badWeather/wetSnow/P1_YOLO_Only, next=badWeather/wetSnow/P2_FrameDiff

- `2026-04-29T21:54:13` G2G3 auto status: completed badWeather/wetSnow/P2_FrameDiff; completed=20/318, pending=298, running=0, failed=0, videos=3/53, session_completed=3, last=badWeather/wetSnow/P2_FrameDiff, next=badWeather/wetSnow/P3_MOG2

- `2026-04-29T22:05:09` G2G3 auto status: completed badWeather/wetSnow/P3_MOG2; completed=21/318, pending=297, running=0, failed=0, videos=3/53, session_completed=4, last=badWeather/wetSnow/P3_MOG2, next=badWeather/wetSnow/ASMAG_TR_FAST

- `2026-04-29T22:12:38` G2G3 auto status: completed badWeather/wetSnow/ASMAG_TR_FAST; completed=22/318, pending=296, running=0, failed=0, videos=3/53, session_completed=5, last=badWeather/wetSnow/ASMAG_TR_FAST, next=badWeather/wetSnow/ASMAG_TR_CONTROLLER

- `2026-04-29T22:22:11` G2G3 auto status: completed badWeather/wetSnow/ASMAG_TR_CONTROLLER; completed=23/318, pending=295, running=0, failed=0, videos=3/53, session_completed=6, last=badWeather/wetSnow/ASMAG_TR_CONTROLLER, next=badWeather/wetSnow/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-04-29T22:34:40` G2G3 auto status: completed badWeather/wetSnow/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=24/318, pending=294, running=0, failed=0, videos=4/53, session_completed=7, last=badWeather/wetSnow/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=baseline/highway/P1_YOLO_Only

- `2026-04-29T22:40:18` G2G3 auto status: completed baseline/highway/P1_YOLO_Only; completed=25/318, pending=293, running=0, failed=0, videos=4/53, session_completed=8, last=baseline/highway/P1_YOLO_Only, next=baseline/highway/P2_FrameDiff

- `2026-04-29T22:44:12` G2G3 auto status: completed baseline/highway/P2_FrameDiff; completed=26/318, pending=292, running=0, failed=0, videos=4/53, session_completed=9, last=baseline/highway/P2_FrameDiff, next=baseline/highway/P3_MOG2

- `2026-04-29T22:48:58` G2G3 auto status: completed baseline/highway/P3_MOG2; completed=27/318, pending=291, running=0, failed=0, videos=4/53, session_completed=10, last=baseline/highway/P3_MOG2, next=baseline/highway/ASMAG_TR_FAST

- `2026-04-29T22:53:02` G2G3 auto status: completed baseline/highway/ASMAG_TR_FAST; completed=28/318, pending=290, running=0, failed=0, videos=4/53, session_completed=11, last=baseline/highway/ASMAG_TR_FAST, next=baseline/highway/ASMAG_TR_CONTROLLER

- `2026-04-29T22:57:10` G2G3 auto status: completed baseline/highway/ASMAG_TR_CONTROLLER; completed=29/318, pending=289, running=0, failed=0, videos=4/53, session_completed=12, last=baseline/highway/ASMAG_TR_CONTROLLER, next=baseline/highway/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-04-29T23:01:33` G2G3 auto status: completed baseline/highway/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=30/318, pending=288, running=0, failed=0, videos=5/53, session_completed=13, last=baseline/highway/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=baseline/office/P1_YOLO_Only

- `2026-04-29T23:07:33` G2G3 auto status: completed baseline/office/P1_YOLO_Only; completed=31/318, pending=287, running=0, failed=0, videos=5/53, session_completed=14, last=baseline/office/P1_YOLO_Only, next=baseline/office/P2_FrameDiff

- `2026-04-29T23:09:19` G2G3 auto status: completed baseline/office/P2_FrameDiff; completed=32/318, pending=286, running=0, failed=0, videos=5/53, session_completed=15, last=baseline/office/P2_FrameDiff, next=baseline/office/P3_MOG2

- `2026-04-29T23:13:05` G2G3 auto status: completed baseline/office/P3_MOG2; completed=33/318, pending=285, running=0, failed=0, videos=5/53, session_completed=16, last=baseline/office/P3_MOG2, next=baseline/office/ASMAG_TR_FAST

- `2026-04-29T23:16:51` G2G3 auto status: completed baseline/office/ASMAG_TR_FAST; completed=34/318, pending=284, running=0, failed=0, videos=5/53, session_completed=17, last=baseline/office/ASMAG_TR_FAST, next=baseline/office/ASMAG_TR_CONTROLLER

- `2026-04-29T23:20:35` G2G3 auto status: completed baseline/office/ASMAG_TR_CONTROLLER; completed=35/318, pending=283, running=0, failed=0, videos=5/53, session_completed=18, last=baseline/office/ASMAG_TR_CONTROLLER, next=baseline/office/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-04-29T23:24:54` G2G3 auto status: completed baseline/office/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=36/318, pending=282, running=0, failed=0, videos=6/53, session_completed=19, last=baseline/office/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=baseline/pedestrians/P1_YOLO_Only

- `2026-04-29T23:28:13` G2G3 auto status: completed baseline/pedestrians/P1_YOLO_Only; completed=37/318, pending=281, running=0, failed=0, videos=6/53, session_completed=20, last=baseline/pedestrians/P1_YOLO_Only, next=baseline/pedestrians/P2_FrameDiff

- `2026-04-29T23:30:34` G2G3 auto status: completed baseline/pedestrians/P2_FrameDiff; completed=38/318, pending=280, running=0, failed=0, videos=6/53, session_completed=21, last=baseline/pedestrians/P2_FrameDiff, next=baseline/pedestrians/P3_MOG2

- `2026-04-29T23:32:43` G2G3 auto status: completed baseline/pedestrians/P3_MOG2; completed=39/318, pending=279, running=0, failed=0, videos=6/53, session_completed=22, last=baseline/pedestrians/P3_MOG2, next=baseline/pedestrians/ASMAG_TR_FAST

- `2026-04-29T23:35:02` G2G3 auto status: completed baseline/pedestrians/ASMAG_TR_FAST; completed=40/318, pending=278, running=0, failed=0, videos=6/53, session_completed=23, last=baseline/pedestrians/ASMAG_TR_FAST, next=baseline/pedestrians/ASMAG_TR_CONTROLLER

- `2026-04-29T23:36:59` G2G3 auto status: completed baseline/pedestrians/ASMAG_TR_CONTROLLER; completed=41/318, pending=277, running=0, failed=0, videos=6/53, session_completed=24, last=baseline/pedestrians/ASMAG_TR_CONTROLLER, next=baseline/pedestrians/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-04-29T23:39:28` G2G3 auto status: completed baseline/pedestrians/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=42/318, pending=276, running=0, failed=0, videos=7/53, session_completed=25, last=baseline/pedestrians/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=baseline/PETS2006/P1_YOLO_Only

- `2026-04-29T23:44:07` G2G3 auto status: completed baseline/PETS2006/P1_YOLO_Only; completed=43/318, pending=275, running=0, failed=0, videos=7/53, session_completed=26, last=baseline/PETS2006/P1_YOLO_Only, next=baseline/PETS2006/P2_FrameDiff

- `2026-04-29T23:46:35` G2G3 auto status: completed baseline/PETS2006/P2_FrameDiff; completed=44/318, pending=274, running=0, failed=0, videos=7/53, session_completed=27, last=baseline/PETS2006/P2_FrameDiff, next=baseline/PETS2006/P3_MOG2

- `2026-04-29T23:50:09` G2G3 auto status: completed baseline/PETS2006/P3_MOG2; completed=45/318, pending=273, running=0, failed=0, videos=7/53, session_completed=28, last=baseline/PETS2006/P3_MOG2, next=baseline/PETS2006/ASMAG_TR_FAST

- `2026-04-29T23:53:09` G2G3 auto status: completed baseline/PETS2006/ASMAG_TR_FAST; completed=46/318, pending=272, running=0, failed=0, videos=7/53, session_completed=29, last=baseline/PETS2006/ASMAG_TR_FAST, next=baseline/PETS2006/ASMAG_TR_CONTROLLER

- `2026-04-29T23:55:56` G2G3 auto status: completed baseline/PETS2006/ASMAG_TR_CONTROLLER; completed=47/318, pending=271, running=0, failed=0, videos=7/53, session_completed=30, last=baseline/PETS2006/ASMAG_TR_CONTROLLER, next=baseline/PETS2006/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-04-29T23:56:17` G2G3 auto status: run completed or paused after selected batch; completed=47/318, pending=271, running=0, failed=0, videos=7/53, session_completed=30, last=baseline/PETS2006/ASMAG_TR_CONTROLLER, next=baseline/PETS2006/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-04-30T07:38:21` G2G3 auto status: completed baseline/PETS2006/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=48/318, pending=270, running=0, failed=0, videos=8/53, session_completed=1, last=baseline/PETS2006/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=cameraJitter/badminton/P1_YOLO_Only

- `2026-04-30T07:39:44` G2G3 auto status: completed cameraJitter/badminton/P1_YOLO_Only; completed=49/318, pending=269, running=0, failed=0, videos=8/53, session_completed=2, last=cameraJitter/badminton/P1_YOLO_Only, next=cameraJitter/badminton/P2_FrameDiff

- `2026-04-30T07:41:00` G2G3 auto status: completed cameraJitter/badminton/P2_FrameDiff; completed=50/318, pending=268, running=0, failed=0, videos=8/53, session_completed=3, last=cameraJitter/badminton/P2_FrameDiff, next=cameraJitter/badminton/P3_MOG2

- `2026-04-30T07:42:32` G2G3 auto status: completed cameraJitter/badminton/P3_MOG2; completed=51/318, pending=267, running=0, failed=0, videos=8/53, session_completed=4, last=cameraJitter/badminton/P3_MOG2, next=cameraJitter/badminton/ASMAG_TR_FAST

- `2026-04-30T07:44:08` G2G3 auto status: completed cameraJitter/badminton/ASMAG_TR_FAST; completed=52/318, pending=266, running=0, failed=0, videos=8/53, session_completed=5, last=cameraJitter/badminton/ASMAG_TR_FAST, next=cameraJitter/badminton/ASMAG_TR_CONTROLLER

- `2026-04-30T07:45:35` G2G3 auto status: completed cameraJitter/badminton/ASMAG_TR_CONTROLLER; completed=53/318, pending=265, running=0, failed=0, videos=8/53, session_completed=6, last=cameraJitter/badminton/ASMAG_TR_CONTROLLER, next=cameraJitter/badminton/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-04-30T07:47:31` G2G3 auto status: completed cameraJitter/badminton/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=54/318, pending=264, running=0, failed=0, videos=9/53, session_completed=7, last=cameraJitter/badminton/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=cameraJitter/boulevard/P1_YOLO_Only

- `2026-04-30T07:54:06` G2G3 auto status: completed cameraJitter/boulevard/P1_YOLO_Only; completed=55/318, pending=263, running=0, failed=0, videos=9/53, session_completed=8, last=cameraJitter/boulevard/P1_YOLO_Only, next=cameraJitter/boulevard/P2_FrameDiff

- `2026-04-30T07:59:56` G2G3 auto status: completed cameraJitter/boulevard/P2_FrameDiff; completed=56/318, pending=262, running=0, failed=0, videos=9/53, session_completed=9, last=cameraJitter/boulevard/P2_FrameDiff, next=cameraJitter/boulevard/P3_MOG2

- `2026-04-30T08:05:21` G2G3 auto status: completed cameraJitter/boulevard/P3_MOG2; completed=57/318, pending=261, running=0, failed=0, videos=9/53, session_completed=10, last=cameraJitter/boulevard/P3_MOG2, next=cameraJitter/boulevard/ASMAG_TR_FAST

- `2026-04-30T08:05:43` G2G3 auto status: run completed or paused after selected batch; completed=57/318, pending=261, running=0, failed=0, videos=9/53, session_completed=10, last=cameraJitter/boulevard/P3_MOG2, next=cameraJitter/boulevard/ASMAG_TR_FAST

- `2026-04-30T08:50:24` G2G3 auto status: completed cameraJitter/boulevard/ASMAG_TR_FAST; completed=58/318, pending=260, running=0, failed=0, videos=9/53, session_completed=1, last=cameraJitter/boulevard/ASMAG_TR_FAST, next=cameraJitter/boulevard/ASMAG_TR_CONTROLLER

- `2026-04-30T08:55:48` G2G3 auto status: completed cameraJitter/boulevard/ASMAG_TR_CONTROLLER; completed=59/318, pending=259, running=0, failed=0, videos=9/53, session_completed=2, last=cameraJitter/boulevard/ASMAG_TR_CONTROLLER, next=cameraJitter/boulevard/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-04-30T09:01:59` G2G3 auto status: completed cameraJitter/boulevard/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=60/318, pending=258, running=0, failed=0, videos=10/53, session_completed=3, last=cameraJitter/boulevard/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=cameraJitter/sidewalk/P1_YOLO_Only

- `2026-04-30T09:03:32` G2G3 auto status: completed cameraJitter/sidewalk/P1_YOLO_Only; completed=61/318, pending=257, running=0, failed=0, videos=10/53, session_completed=4, last=cameraJitter/sidewalk/P1_YOLO_Only, next=cameraJitter/sidewalk/P2_FrameDiff

- `2026-04-30T09:04:51` G2G3 auto status: completed cameraJitter/sidewalk/P2_FrameDiff; completed=62/318, pending=256, running=0, failed=0, videos=10/53, session_completed=5, last=cameraJitter/sidewalk/P2_FrameDiff, next=cameraJitter/sidewalk/P3_MOG2

- `2026-04-30T09:06:23` G2G3 auto status: completed cameraJitter/sidewalk/P3_MOG2; completed=63/318, pending=255, running=0, failed=0, videos=10/53, session_completed=6, last=cameraJitter/sidewalk/P3_MOG2, next=cameraJitter/sidewalk/ASMAG_TR_FAST

- `2026-04-30T09:07:54` G2G3 auto status: completed cameraJitter/sidewalk/ASMAG_TR_FAST; completed=64/318, pending=254, running=0, failed=0, videos=10/53, session_completed=7, last=cameraJitter/sidewalk/ASMAG_TR_FAST, next=cameraJitter/sidewalk/ASMAG_TR_CONTROLLER

- `2026-04-30T09:09:16` G2G3 auto status: completed cameraJitter/sidewalk/ASMAG_TR_CONTROLLER; completed=65/318, pending=253, running=0, failed=0, videos=10/53, session_completed=8, last=cameraJitter/sidewalk/ASMAG_TR_CONTROLLER, next=cameraJitter/sidewalk/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-04-30T09:10:43` G2G3 auto status: completed cameraJitter/sidewalk/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=66/318, pending=252, running=0, failed=0, videos=11/53, session_completed=9, last=cameraJitter/sidewalk/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=cameraJitter/traffic/P1_YOLO_Only

- `2026-04-30T09:13:52` G2G3 auto status: completed cameraJitter/traffic/P1_YOLO_Only; completed=67/318, pending=251, running=0, failed=0, videos=11/53, session_completed=10, last=cameraJitter/traffic/P1_YOLO_Only, next=cameraJitter/traffic/P2_FrameDiff

- `2026-04-30T09:14:10` G2G3 auto status: run completed or paused after selected batch; completed=67/318, pending=251, running=0, failed=0, videos=11/53, session_completed=10, last=cameraJitter/traffic/P1_YOLO_Only, next=cameraJitter/traffic/P2_FrameDiff

- `2026-04-30T09:35:35` G2G3 auto status: completed cameraJitter/traffic/P2_FrameDiff; completed=68/318, pending=250, running=0, failed=0, videos=11/53, session_completed=1, last=cameraJitter/traffic/P2_FrameDiff, next=cameraJitter/traffic/P3_MOG2

- `2026-04-30T09:37:57` G2G3 auto status: completed cameraJitter/traffic/P3_MOG2; completed=69/318, pending=249, running=0, failed=0, videos=11/53, session_completed=2, last=cameraJitter/traffic/P3_MOG2, next=cameraJitter/traffic/ASMAG_TR_FAST

- `2026-04-30T09:40:30` G2G3 auto status: completed cameraJitter/traffic/ASMAG_TR_FAST; completed=70/318, pending=248, running=0, failed=0, videos=11/53, session_completed=3, last=cameraJitter/traffic/ASMAG_TR_FAST, next=cameraJitter/traffic/ASMAG_TR_CONTROLLER

- `2026-04-30T09:43:52` G2G3 auto status: completed cameraJitter/traffic/ASMAG_TR_CONTROLLER; completed=71/318, pending=247, running=0, failed=0, videos=11/53, session_completed=4, last=cameraJitter/traffic/ASMAG_TR_CONTROLLER, next=cameraJitter/traffic/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-04-30T09:46:54` G2G3 auto status: completed cameraJitter/traffic/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=72/318, pending=246, running=0, failed=0, videos=12/53, session_completed=5, last=cameraJitter/traffic/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=dynamicBackground/boats/P1_YOLO_Only

- `2026-04-30T10:17:49` G2G3 auto status: completed dynamicBackground/boats/P1_YOLO_Only; completed=73/318, pending=245, running=0, failed=0, videos=12/53, session_completed=6, last=dynamicBackground/boats/P1_YOLO_Only, next=dynamicBackground/boats/P2_FrameDiff

- `2026-04-30T10:35:03` G2G3 auto status: completed dynamicBackground/boats/P2_FrameDiff; completed=74/318, pending=244, running=0, failed=0, videos=12/53, session_completed=7, last=dynamicBackground/boats/P2_FrameDiff, next=dynamicBackground/boats/P3_MOG2

- `2026-04-30T11:00:11` G2G3 auto status: completed dynamicBackground/boats/P3_MOG2; completed=75/318, pending=243, running=0, failed=0, videos=12/53, session_completed=8, last=dynamicBackground/boats/P3_MOG2, next=dynamicBackground/boats/ASMAG_TR_FAST

- `2026-04-30T11:23:30` G2G3 auto status: completed dynamicBackground/boats/ASMAG_TR_FAST; completed=76/318, pending=242, running=0, failed=0, videos=12/53, session_completed=9, last=dynamicBackground/boats/ASMAG_TR_FAST, next=dynamicBackground/boats/ASMAG_TR_CONTROLLER

- `2026-04-30T11:48:28` G2G3 auto status: completed dynamicBackground/boats/ASMAG_TR_CONTROLLER; completed=77/318, pending=241, running=0, failed=0, videos=12/53, session_completed=10, last=dynamicBackground/boats/ASMAG_TR_CONTROLLER, next=dynamicBackground/boats/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-04-30T11:48:49` G2G3 auto status: run completed or paused after selected batch; completed=77/318, pending=241, running=0, failed=0, videos=12/53, session_completed=10, last=dynamicBackground/boats/ASMAG_TR_CONTROLLER, next=dynamicBackground/boats/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-04-30T12:19:51` G2G3 auto status: completed dynamicBackground/boats/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=78/318, pending=240, running=0, failed=0, videos=13/53, session_completed=1, last=dynamicBackground/boats/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=dynamicBackground/canoe/P1_YOLO_Only

- `2026-04-30T12:21:37` G2G3 auto status: completed dynamicBackground/canoe/P1_YOLO_Only; completed=79/318, pending=239, running=0, failed=0, videos=13/53, session_completed=2, last=dynamicBackground/canoe/P1_YOLO_Only, next=dynamicBackground/canoe/P2_FrameDiff

- `2026-04-30T12:23:17` G2G3 auto status: completed dynamicBackground/canoe/P2_FrameDiff; completed=80/318, pending=238, running=0, failed=0, videos=13/53, session_completed=3, last=dynamicBackground/canoe/P2_FrameDiff, next=dynamicBackground/canoe/P3_MOG2

- `2026-04-30T12:24:57` G2G3 auto status: completed dynamicBackground/canoe/P3_MOG2; completed=81/318, pending=237, running=0, failed=0, videos=13/53, session_completed=4, last=dynamicBackground/canoe/P3_MOG2, next=dynamicBackground/canoe/ASMAG_TR_FAST

- `2026-04-30T12:26:28` G2G3 auto status: completed dynamicBackground/canoe/ASMAG_TR_FAST; completed=82/318, pending=236, running=0, failed=0, videos=13/53, session_completed=5, last=dynamicBackground/canoe/ASMAG_TR_FAST, next=dynamicBackground/canoe/ASMAG_TR_CONTROLLER

- `2026-04-30T12:28:01` G2G3 auto status: completed dynamicBackground/canoe/ASMAG_TR_CONTROLLER; completed=83/318, pending=235, running=0, failed=0, videos=13/53, session_completed=6, last=dynamicBackground/canoe/ASMAG_TR_CONTROLLER, next=dynamicBackground/canoe/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-04-30T12:29:45` G2G3 auto status: completed dynamicBackground/canoe/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=84/318, pending=234, running=0, failed=0, videos=14/53, session_completed=7, last=dynamicBackground/canoe/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=dynamicBackground/fall/P1_YOLO_Only

- `2026-04-30T12:44:13` G2G3 auto status: completed dynamicBackground/fall/P1_YOLO_Only; completed=85/318, pending=233, running=0, failed=0, videos=14/53, session_completed=8, last=dynamicBackground/fall/P1_YOLO_Only, next=dynamicBackground/fall/P2_FrameDiff

- `2026-04-30T12:55:51` G2G3 auto status: completed dynamicBackground/fall/P2_FrameDiff; completed=86/318, pending=232, running=0, failed=0, videos=14/53, session_completed=9, last=dynamicBackground/fall/P2_FrameDiff, next=dynamicBackground/fall/P3_MOG2

- `2026-04-30T13:08:47` G2G3 auto status: completed dynamicBackground/fall/P3_MOG2; completed=87/318, pending=231, running=0, failed=0, videos=14/53, session_completed=10, last=dynamicBackground/fall/P3_MOG2, next=dynamicBackground/fall/ASMAG_TR_FAST

- `2026-04-30T13:09:15` G2G3 auto status: run completed or paused after selected batch; completed=87/318, pending=231, running=0, failed=0, videos=14/53, session_completed=10, last=dynamicBackground/fall/P3_MOG2, next=dynamicBackground/fall/ASMAG_TR_FAST

- `2026-04-30T15:25:45` G2G3 auto status: completed dynamicBackground/fall/ASMAG_TR_FAST; completed=88/318, pending=230, running=0, failed=0, videos=14/53, session_completed=1, last=dynamicBackground/fall/ASMAG_TR_FAST, next=dynamicBackground/fall/ASMAG_TR_CONTROLLER

- `2026-04-30T15:39:00` G2G3 auto status: completed dynamicBackground/fall/ASMAG_TR_CONTROLLER; completed=89/318, pending=229, running=0, failed=0, videos=14/53, session_completed=2, last=dynamicBackground/fall/ASMAG_TR_CONTROLLER, next=dynamicBackground/fall/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-04-30T15:57:22` G2G3 auto status: completed dynamicBackground/fall/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=90/318, pending=228, running=0, failed=0, videos=15/53, session_completed=3, last=dynamicBackground/fall/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=dynamicBackground/fountain01/P1_YOLO_Only

- `2026-04-30T16:00:52` G2G3 auto status: completed dynamicBackground/fountain01/P1_YOLO_Only; completed=91/318, pending=227, running=0, failed=0, videos=15/53, session_completed=4, last=dynamicBackground/fountain01/P1_YOLO_Only, next=dynamicBackground/fountain01/P2_FrameDiff

- `2026-04-30T16:03:58` G2G3 auto status: completed dynamicBackground/fountain01/P2_FrameDiff; completed=92/318, pending=226, running=0, failed=0, videos=15/53, session_completed=5, last=dynamicBackground/fountain01/P2_FrameDiff, next=dynamicBackground/fountain01/P3_MOG2

- `2026-04-30T16:07:47` G2G3 auto status: completed dynamicBackground/fountain01/P3_MOG2; completed=93/318, pending=225, running=0, failed=0, videos=15/53, session_completed=6, last=dynamicBackground/fountain01/P3_MOG2, next=dynamicBackground/fountain01/ASMAG_TR_FAST

- `2026-04-30T16:10:55` G2G3 auto status: completed dynamicBackground/fountain01/ASMAG_TR_FAST; completed=94/318, pending=224, running=0, failed=0, videos=15/53, session_completed=7, last=dynamicBackground/fountain01/ASMAG_TR_FAST, next=dynamicBackground/fountain01/ASMAG_TR_CONTROLLER

- `2026-04-30T16:13:45` G2G3 auto status: completed dynamicBackground/fountain01/ASMAG_TR_CONTROLLER; completed=95/318, pending=223, running=0, failed=0, videos=15/53, session_completed=8, last=dynamicBackground/fountain01/ASMAG_TR_CONTROLLER, next=dynamicBackground/fountain01/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-04-30T16:17:27` G2G3 auto status: completed dynamicBackground/fountain01/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=96/318, pending=222, running=0, failed=0, videos=16/53, session_completed=9, last=dynamicBackground/fountain01/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=dynamicBackground/fountain02/P1_YOLO_Only

- `2026-04-30T16:21:28` G2G3 auto status: completed dynamicBackground/fountain02/P1_YOLO_Only; completed=97/318, pending=221, running=0, failed=0, videos=16/53, session_completed=10, last=dynamicBackground/fountain02/P1_YOLO_Only, next=dynamicBackground/fountain02/P2_FrameDiff

- `2026-04-30T16:21:56` G2G3 auto status: run completed or paused after selected batch; completed=97/318, pending=221, running=0, failed=0, videos=16/53, session_completed=10, last=dynamicBackground/fountain02/P1_YOLO_Only, next=dynamicBackground/fountain02/P2_FrameDiff

- `2026-04-30T22:11:57` G2G3 auto status: completed dynamicBackground/fountain02/P2_FrameDiff; completed=98/318, pending=220, running=0, failed=0, videos=16/53, session_completed=1, last=dynamicBackground/fountain02/P2_FrameDiff, next=dynamicBackground/fountain02/P3_MOG2

- `2026-04-30T22:15:47` G2G3 auto status: completed dynamicBackground/fountain02/P3_MOG2; completed=99/318, pending=219, running=0, failed=0, videos=16/53, session_completed=1, last=dynamicBackground/fountain02/P3_MOG2, next=dynamicBackground/fountain02/ASMAG_TR_FAST

- `2026-04-30T22:19:20` G2G3 auto status: completed dynamicBackground/fountain02/ASMAG_TR_FAST; completed=100/318, pending=218, running=0, failed=0, videos=16/53, session_completed=1, last=dynamicBackground/fountain02/ASMAG_TR_FAST, next=dynamicBackground/fountain02/ASMAG_TR_CONTROLLER

- `2026-04-30T22:20:50` G2G3 auto status: completed dynamicBackground/fountain02/ASMAG_TR_CONTROLLER; completed=101/318, pending=217, running=0, failed=0, videos=16/53, session_completed=2, last=dynamicBackground/fountain02/ASMAG_TR_CONTROLLER, next=dynamicBackground/fountain02/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-04-30T22:23:14` G2G3 auto status: completed dynamicBackground/fountain02/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=102/318, pending=216, running=0, failed=0, videos=17/53, session_completed=3, last=dynamicBackground/fountain02/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=dynamicBackground/overpass/P1_YOLO_Only

- `2026-04-30T22:36:53` G2G3 auto status: completed dynamicBackground/overpass/P1_YOLO_Only; completed=103/318, pending=215, running=0, failed=0, videos=17/53, session_completed=4, last=dynamicBackground/overpass/P1_YOLO_Only, next=dynamicBackground/overpass/P2_FrameDiff

- `2026-04-30T22:39:37` G2G3 auto status: completed dynamicBackground/overpass/P2_FrameDiff; completed=104/318, pending=214, running=0, failed=0, videos=17/53, session_completed=5, last=dynamicBackground/overpass/P2_FrameDiff, next=dynamicBackground/overpass/P3_MOG2

- `2026-04-30T22:49:41` G2G3 auto status: completed dynamicBackground/overpass/P3_MOG2; completed=105/318, pending=213, running=0, failed=0, videos=17/53, session_completed=6, last=dynamicBackground/overpass/P3_MOG2, next=dynamicBackground/overpass/ASMAG_TR_FAST

- `2026-04-30T22:58:57` G2G3 auto status: completed dynamicBackground/overpass/ASMAG_TR_FAST; completed=106/318, pending=212, running=0, failed=0, videos=17/53, session_completed=7, last=dynamicBackground/overpass/ASMAG_TR_FAST, next=dynamicBackground/overpass/ASMAG_TR_CONTROLLER

- `2026-04-30T23:06:14` G2G3 auto status: completed dynamicBackground/overpass/ASMAG_TR_CONTROLLER; completed=107/318, pending=211, running=0, failed=0, videos=17/53, session_completed=8, last=dynamicBackground/overpass/ASMAG_TR_CONTROLLER, next=dynamicBackground/overpass/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-04-30T23:12:52` G2G3 auto status: completed dynamicBackground/overpass/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=108/318, pending=210, running=0, failed=0, videos=18/53, session_completed=9, last=dynamicBackground/overpass/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=intermittentObjectMotion/abandonedBox/P1_YOLO_Only

- `2026-05-01T07:41:07` G2G3 auto status: completed intermittentObjectMotion/abandonedBox/P1_YOLO_Only; completed=109/318, pending=209, running=0, failed=0, videos=18/53, session_completed=1, last=intermittentObjectMotion/abandonedBox/P1_YOLO_Only, next=intermittentObjectMotion/abandonedBox/P2_FrameDiff

- `2026-05-01T07:47:47` G2G3 auto status: completed intermittentObjectMotion/abandonedBox/P2_FrameDiff; completed=110/318, pending=208, running=0, failed=0, videos=18/53, session_completed=2, last=intermittentObjectMotion/abandonedBox/P2_FrameDiff, next=intermittentObjectMotion/abandonedBox/P3_MOG2

- `2026-05-01T07:56:18` G2G3 auto status: completed intermittentObjectMotion/abandonedBox/P3_MOG2; completed=111/318, pending=207, running=0, failed=0, videos=18/53, session_completed=3, last=intermittentObjectMotion/abandonedBox/P3_MOG2, next=intermittentObjectMotion/abandonedBox/ASMAG_TR_FAST

- `2026-05-01T08:04:36` G2G3 auto status: completed intermittentObjectMotion/abandonedBox/ASMAG_TR_FAST; completed=112/318, pending=206, running=0, failed=0, videos=18/53, session_completed=4, last=intermittentObjectMotion/abandonedBox/ASMAG_TR_FAST, next=intermittentObjectMotion/abandonedBox/ASMAG_TR_CONTROLLER

- `2026-05-01T08:13:43` G2G3 auto status: completed intermittentObjectMotion/abandonedBox/ASMAG_TR_CONTROLLER; completed=113/318, pending=205, running=0, failed=0, videos=18/53, session_completed=5, last=intermittentObjectMotion/abandonedBox/ASMAG_TR_CONTROLLER, next=intermittentObjectMotion/abandonedBox/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-01T08:22:01` G2G3 auto status: completed intermittentObjectMotion/abandonedBox/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=114/318, pending=204, running=0, failed=0, videos=19/53, session_completed=6, last=intermittentObjectMotion/abandonedBox/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=intermittentObjectMotion/parking/P1_YOLO_Only

- `2026-05-01T08:29:25` G2G3 auto status: completed intermittentObjectMotion/parking/P1_YOLO_Only; completed=115/318, pending=203, running=0, failed=0, videos=19/53, session_completed=7, last=intermittentObjectMotion/parking/P1_YOLO_Only, next=intermittentObjectMotion/parking/P2_FrameDiff

- `2026-05-01T08:29:46` G2G3 auto status: completed intermittentObjectMotion/parking/P2_FrameDiff; completed=116/318, pending=202, running=0, failed=0, videos=19/53, session_completed=8, last=intermittentObjectMotion/parking/P2_FrameDiff, next=intermittentObjectMotion/parking/P3_MOG2

- `2026-05-01T10:22:10` G2G3 auto status: completed intermittentObjectMotion/parking/P3_MOG2; completed=117/318, pending=201, running=0, failed=0, videos=19/53, session_completed=1, last=intermittentObjectMotion/parking/P3_MOG2, next=intermittentObjectMotion/parking/ASMAG_TR_FAST

- `2026-05-01T10:23:51` G2G3 auto status: completed intermittentObjectMotion/parking/ASMAG_TR_FAST; completed=118/318, pending=200, running=0, failed=0, videos=19/53, session_completed=2, last=intermittentObjectMotion/parking/ASMAG_TR_FAST, next=intermittentObjectMotion/parking/ASMAG_TR_CONTROLLER

- `2026-05-01T10:26:18` G2G3 auto status: completed intermittentObjectMotion/parking/ASMAG_TR_CONTROLLER; completed=119/318, pending=199, running=0, failed=0, videos=19/53, session_completed=3, last=intermittentObjectMotion/parking/ASMAG_TR_CONTROLLER, next=intermittentObjectMotion/parking/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-01T10:29:47` G2G3 auto status: completed intermittentObjectMotion/parking/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=120/318, pending=198, running=0, failed=0, videos=20/53, session_completed=4, last=intermittentObjectMotion/parking/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=intermittentObjectMotion/sofa/P1_YOLO_Only

- `2026-05-01T10:42:24` G2G3 auto status: completed intermittentObjectMotion/sofa/P1_YOLO_Only; completed=121/318, pending=197, running=0, failed=0, videos=20/53, session_completed=5, last=intermittentObjectMotion/sofa/P1_YOLO_Only, next=intermittentObjectMotion/sofa/P2_FrameDiff

- `2026-05-01T10:47:25` G2G3 auto status: completed intermittentObjectMotion/sofa/P2_FrameDiff; completed=122/318, pending=196, running=0, failed=0, videos=20/53, session_completed=6, last=intermittentObjectMotion/sofa/P2_FrameDiff, next=intermittentObjectMotion/sofa/P3_MOG2

- `2026-05-01T10:54:04` G2G3 auto status: completed intermittentObjectMotion/sofa/P3_MOG2; completed=123/318, pending=195, running=0, failed=0, videos=20/53, session_completed=7, last=intermittentObjectMotion/sofa/P3_MOG2, next=intermittentObjectMotion/sofa/ASMAG_TR_FAST

- `2026-05-01T11:01:04` G2G3 auto status: completed intermittentObjectMotion/sofa/ASMAG_TR_FAST; completed=124/318, pending=194, running=0, failed=0, videos=20/53, session_completed=8, last=intermittentObjectMotion/sofa/ASMAG_TR_FAST, next=intermittentObjectMotion/sofa/ASMAG_TR_CONTROLLER

- `2026-05-01T11:08:41` G2G3 auto status: completed intermittentObjectMotion/sofa/ASMAG_TR_CONTROLLER; completed=125/318, pending=193, running=0, failed=0, videos=20/53, session_completed=9, last=intermittentObjectMotion/sofa/ASMAG_TR_CONTROLLER, next=intermittentObjectMotion/sofa/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-01T11:16:17` G2G3 auto status: completed intermittentObjectMotion/sofa/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=126/318, pending=192, running=0, failed=0, videos=21/53, session_completed=10, last=intermittentObjectMotion/sofa/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=intermittentObjectMotion/streetLight/P1_YOLO_Only

- `2026-05-01T11:50:04` G2G3 auto status: completed intermittentObjectMotion/streetLight/P1_YOLO_Only; completed=127/318, pending=191, running=0, failed=0, videos=21/53, session_completed=1, last=intermittentObjectMotion/streetLight/P1_YOLO_Only, next=intermittentObjectMotion/streetLight/P2_FrameDiff

- `2026-05-01T12:04:38` G2G3 auto status: completed intermittentObjectMotion/streetLight/P2_FrameDiff; completed=128/318, pending=190, running=0, failed=0, videos=21/53, session_completed=2, last=intermittentObjectMotion/streetLight/P2_FrameDiff, next=intermittentObjectMotion/streetLight/P3_MOG2

- `2026-05-01T12:20:18` G2G3 auto status: completed intermittentObjectMotion/streetLight/P3_MOG2; completed=129/318, pending=189, running=0, failed=0, videos=21/53, session_completed=3, last=intermittentObjectMotion/streetLight/P3_MOG2, next=intermittentObjectMotion/streetLight/ASMAG_TR_FAST

- `2026-05-01T12:54:00` G2G3 auto status: completed intermittentObjectMotion/streetLight/ASMAG_TR_FAST; completed=130/318, pending=188, running=0, failed=0, videos=21/53, session_completed=1, last=intermittentObjectMotion/streetLight/ASMAG_TR_FAST, next=intermittentObjectMotion/streetLight/ASMAG_TR_CONTROLLER

- `2026-05-01T13:08:28` G2G3 auto status: completed intermittentObjectMotion/streetLight/ASMAG_TR_CONTROLLER; completed=131/318, pending=187, running=0, failed=0, videos=21/53, session_completed=2, last=intermittentObjectMotion/streetLight/ASMAG_TR_CONTROLLER, next=intermittentObjectMotion/streetLight/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-01T13:22:57` G2G3 auto status: completed intermittentObjectMotion/streetLight/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=132/318, pending=186, running=0, failed=0, videos=22/53, session_completed=3, last=intermittentObjectMotion/streetLight/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=intermittentObjectMotion/tramstop/P1_YOLO_Only

- `2026-05-01T13:32:54` G2G3 auto status: completed intermittentObjectMotion/tramstop/P1_YOLO_Only; completed=133/318, pending=185, running=0, failed=0, videos=22/53, session_completed=4, last=intermittentObjectMotion/tramstop/P1_YOLO_Only, next=intermittentObjectMotion/tramstop/P2_FrameDiff

- `2026-05-01T13:39:27` G2G3 auto status: completed intermittentObjectMotion/tramstop/P2_FrameDiff; completed=134/318, pending=184, running=0, failed=0, videos=22/53, session_completed=5, last=intermittentObjectMotion/tramstop/P2_FrameDiff, next=intermittentObjectMotion/tramstop/P3_MOG2

- `2026-05-01T15:44:05` G2G3 auto status: completed intermittentObjectMotion/tramstop/P3_MOG2; completed=135/318, pending=183, running=0, failed=0, videos=22/53, session_completed=1, last=intermittentObjectMotion/tramstop/P3_MOG2, next=intermittentObjectMotion/tramstop/ASMAG_TR_FAST

- `2026-05-01T15:51:33` G2G3 auto status: completed intermittentObjectMotion/tramstop/ASMAG_TR_FAST; completed=136/318, pending=182, running=0, failed=0, videos=22/53, session_completed=2, last=intermittentObjectMotion/tramstop/ASMAG_TR_FAST, next=intermittentObjectMotion/tramstop/ASMAG_TR_CONTROLLER

- `2026-05-01T15:58:59` G2G3 auto status: completed intermittentObjectMotion/tramstop/ASMAG_TR_CONTROLLER; completed=137/318, pending=181, running=0, failed=0, videos=22/53, session_completed=3, last=intermittentObjectMotion/tramstop/ASMAG_TR_CONTROLLER, next=intermittentObjectMotion/tramstop/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-01T16:06:59` G2G3 auto status: completed intermittentObjectMotion/tramstop/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=138/318, pending=180, running=0, failed=0, videos=23/53, session_completed=4, last=intermittentObjectMotion/tramstop/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=intermittentObjectMotion/winterDriveway/P1_YOLO_Only

- `2026-05-01T16:15:22` G2G3 auto status: completed intermittentObjectMotion/winterDriveway/P1_YOLO_Only; completed=139/318, pending=179, running=0, failed=0, videos=23/53, session_completed=5, last=intermittentObjectMotion/winterDriveway/P1_YOLO_Only, next=intermittentObjectMotion/winterDriveway/P2_FrameDiff

- `2026-05-01T16:15:44` G2G3 auto status: completed intermittentObjectMotion/winterDriveway/P2_FrameDiff; completed=140/318, pending=178, running=0, failed=0, videos=23/53, session_completed=6, last=intermittentObjectMotion/winterDriveway/P2_FrameDiff, next=intermittentObjectMotion/winterDriveway/P3_MOG2

- `2026-05-01T16:19:55` G2G3 auto status: completed intermittentObjectMotion/winterDriveway/P3_MOG2; completed=141/318, pending=177, running=0, failed=0, videos=23/53, session_completed=7, last=intermittentObjectMotion/winterDriveway/P3_MOG2, next=intermittentObjectMotion/winterDriveway/ASMAG_TR_FAST

- `2026-05-01T16:23:03` G2G3 auto status: completed intermittentObjectMotion/winterDriveway/ASMAG_TR_FAST; completed=142/318, pending=176, running=0, failed=0, videos=23/53, session_completed=8, last=intermittentObjectMotion/winterDriveway/ASMAG_TR_FAST, next=intermittentObjectMotion/winterDriveway/ASMAG_TR_CONTROLLER

- `2026-05-01T16:26:57` G2G3 auto status: completed intermittentObjectMotion/winterDriveway/ASMAG_TR_CONTROLLER; completed=143/318, pending=175, running=0, failed=0, videos=23/53, session_completed=9, last=intermittentObjectMotion/winterDriveway/ASMAG_TR_CONTROLLER, next=intermittentObjectMotion/winterDriveway/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-01T16:30:30` G2G3 auto status: completed intermittentObjectMotion/winterDriveway/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=144/318, pending=174, running=0, failed=0, videos=24/53, session_completed=10, last=intermittentObjectMotion/winterDriveway/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=lowFramerate/port_0_17fps/P1_YOLO_Only

- `2026-05-01T16:51:29` G2G3 auto status: completed lowFramerate/port_0_17fps/P1_YOLO_Only; completed=145/318, pending=173, running=0, failed=0, videos=24/53, session_completed=1, last=lowFramerate/port_0_17fps/P1_YOLO_Only, next=lowFramerate/port_0_17fps/P2_FrameDiff

- `2026-05-01T16:57:28` G2G3 auto status: completed lowFramerate/port_0_17fps/P2_FrameDiff; completed=146/318, pending=172, running=0, failed=0, videos=24/53, session_completed=2, last=lowFramerate/port_0_17fps/P2_FrameDiff, next=lowFramerate/port_0_17fps/P3_MOG2

- `2026-05-01T17:05:26` G2G3 auto status: completed lowFramerate/port_0_17fps/P3_MOG2; completed=147/318, pending=171, running=0, failed=0, videos=24/53, session_completed=3, last=lowFramerate/port_0_17fps/P3_MOG2, next=lowFramerate/port_0_17fps/ASMAG_TR_FAST

- `2026-05-01T17:13:27` G2G3 auto status: completed lowFramerate/port_0_17fps/ASMAG_TR_FAST; completed=148/318, pending=170, running=0, failed=0, videos=24/53, session_completed=4, last=lowFramerate/port_0_17fps/ASMAG_TR_FAST, next=lowFramerate/port_0_17fps/ASMAG_TR_CONTROLLER

- `2026-05-01T17:20:56` G2G3 auto status: completed lowFramerate/port_0_17fps/ASMAG_TR_CONTROLLER; completed=149/318, pending=169, running=0, failed=0, videos=24/53, session_completed=5, last=lowFramerate/port_0_17fps/ASMAG_TR_CONTROLLER, next=lowFramerate/port_0_17fps/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-01T17:30:53` G2G3 auto status: completed lowFramerate/port_0_17fps/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=150/318, pending=168, running=0, failed=0, videos=25/53, session_completed=6, last=lowFramerate/port_0_17fps/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=lowFramerate/tramCrossroad_1fps/P1_YOLO_Only

- `2026-05-01T17:33:24` G2G3 auto status: completed lowFramerate/tramCrossroad_1fps/P1_YOLO_Only; completed=151/318, pending=167, running=0, failed=0, videos=25/53, session_completed=7, last=lowFramerate/tramCrossroad_1fps/P1_YOLO_Only, next=lowFramerate/tramCrossroad_1fps/P2_FrameDiff

- `2026-05-01T17:35:25` G2G3 auto status: completed lowFramerate/tramCrossroad_1fps/P2_FrameDiff; completed=152/318, pending=166, running=0, failed=0, videos=25/53, session_completed=8, last=lowFramerate/tramCrossroad_1fps/P2_FrameDiff, next=lowFramerate/tramCrossroad_1fps/P3_MOG2

- `2026-05-01T17:37:20` G2G3 auto status: completed lowFramerate/tramCrossroad_1fps/P3_MOG2; completed=153/318, pending=165, running=0, failed=0, videos=25/53, session_completed=9, last=lowFramerate/tramCrossroad_1fps/P3_MOG2, next=lowFramerate/tramCrossroad_1fps/ASMAG_TR_FAST

- `2026-05-01T17:39:17` G2G3 auto status: completed lowFramerate/tramCrossroad_1fps/ASMAG_TR_FAST; completed=154/318, pending=164, running=0, failed=0, videos=25/53, session_completed=10, last=lowFramerate/tramCrossroad_1fps/ASMAG_TR_FAST, next=lowFramerate/tramCrossroad_1fps/ASMAG_TR_CONTROLLER

- `2026-05-01T17:41:12` G2G3 auto status: completed lowFramerate/tramCrossroad_1fps/ASMAG_TR_CONTROLLER; completed=155/318, pending=163, running=0, failed=0, videos=25/53, session_completed=11, last=lowFramerate/tramCrossroad_1fps/ASMAG_TR_CONTROLLER, next=lowFramerate/tramCrossroad_1fps/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-01T18:27:10` G2G3 auto status: completed lowFramerate/tramCrossroad_1fps/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=156/318, pending=162, running=0, failed=0, videos=26/53, session_completed=1, last=lowFramerate/tramCrossroad_1fps/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=lowFramerate/tunnelExit_0_35fps/P1_YOLO_Only

- `2026-05-01T18:36:08` G2G3 auto status: completed lowFramerate/tunnelExit_0_35fps/P1_YOLO_Only; completed=157/318, pending=161, running=0, failed=0, videos=26/53, session_completed=2, last=lowFramerate/tunnelExit_0_35fps/P1_YOLO_Only, next=lowFramerate/tunnelExit_0_35fps/P2_FrameDiff

- `2026-05-01T18:43:13` G2G3 auto status: completed lowFramerate/tunnelExit_0_35fps/P2_FrameDiff; completed=158/318, pending=160, running=0, failed=0, videos=26/53, session_completed=3, last=lowFramerate/tunnelExit_0_35fps/P2_FrameDiff, next=lowFramerate/tunnelExit_0_35fps/P3_MOG2

- `2026-05-01T18:50:34` G2G3 auto status: completed lowFramerate/tunnelExit_0_35fps/P3_MOG2; completed=159/318, pending=159, running=0, failed=0, videos=26/53, session_completed=4, last=lowFramerate/tunnelExit_0_35fps/P3_MOG2, next=lowFramerate/tunnelExit_0_35fps/ASMAG_TR_FAST

- `2026-05-01T18:56:11` G2G3 auto status: completed lowFramerate/tunnelExit_0_35fps/ASMAG_TR_FAST; completed=160/318, pending=158, running=0, failed=0, videos=26/53, session_completed=5, last=lowFramerate/tunnelExit_0_35fps/ASMAG_TR_FAST, next=lowFramerate/tunnelExit_0_35fps/ASMAG_TR_CONTROLLER

- `2026-05-01T19:03:38` G2G3 auto status: completed lowFramerate/tunnelExit_0_35fps/ASMAG_TR_CONTROLLER; completed=161/318, pending=157, running=0, failed=0, videos=26/53, session_completed=6, last=lowFramerate/tunnelExit_0_35fps/ASMAG_TR_CONTROLLER, next=lowFramerate/tunnelExit_0_35fps/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-01T19:12:31` G2G3 auto status: completed lowFramerate/tunnelExit_0_35fps/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=162/318, pending=156, running=0, failed=0, videos=27/53, session_completed=7, last=lowFramerate/tunnelExit_0_35fps/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=lowFramerate/turnpike_0_5fps/P1_YOLO_Only

- `2026-05-01T19:16:17` G2G3 auto status: completed lowFramerate/turnpike_0_5fps/P1_YOLO_Only; completed=163/318, pending=155, running=0, failed=0, videos=27/53, session_completed=8, last=lowFramerate/turnpike_0_5fps/P1_YOLO_Only, next=lowFramerate/turnpike_0_5fps/P2_FrameDiff

- `2026-05-01T19:19:18` G2G3 auto status: completed lowFramerate/turnpike_0_5fps/P2_FrameDiff; completed=164/318, pending=154, running=0, failed=0, videos=27/53, session_completed=9, last=lowFramerate/turnpike_0_5fps/P2_FrameDiff, next=lowFramerate/turnpike_0_5fps/P3_MOG2

- `2026-05-01T19:22:42` G2G3 auto status: completed lowFramerate/turnpike_0_5fps/P3_MOG2; completed=165/318, pending=153, running=0, failed=0, videos=27/53, session_completed=10, last=lowFramerate/turnpike_0_5fps/P3_MOG2, next=lowFramerate/turnpike_0_5fps/ASMAG_TR_FAST

- `2026-05-01T20:13:39` G2G3 auto status: completed lowFramerate/turnpike_0_5fps/ASMAG_TR_FAST; completed=166/318, pending=152, running=0, failed=0, videos=27/53, session_completed=1, last=lowFramerate/turnpike_0_5fps/ASMAG_TR_FAST, next=lowFramerate/turnpike_0_5fps/ASMAG_TR_CONTROLLER

- `2026-05-01T20:16:19` G2G3 auto status: completed lowFramerate/turnpike_0_5fps/ASMAG_TR_CONTROLLER; completed=167/318, pending=151, running=0, failed=0, videos=27/53, session_completed=2, last=lowFramerate/turnpike_0_5fps/ASMAG_TR_CONTROLLER, next=lowFramerate/turnpike_0_5fps/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-01T20:19:31` G2G3 auto status: completed lowFramerate/turnpike_0_5fps/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=168/318, pending=150, running=0, failed=0, videos=28/53, session_completed=3, last=lowFramerate/turnpike_0_5fps/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=nightVideos/bridgeEntry/P1_YOLO_Only

- `2026-05-01T20:27:21` G2G3 auto status: completed nightVideos/bridgeEntry/P1_YOLO_Only; completed=169/318, pending=149, running=0, failed=0, videos=28/53, session_completed=4, last=nightVideos/bridgeEntry/P1_YOLO_Only, next=nightVideos/bridgeEntry/P2_FrameDiff

- `2026-05-01T20:29:27` G2G3 auto status: completed nightVideos/bridgeEntry/P2_FrameDiff; completed=170/318, pending=148, running=0, failed=0, videos=28/53, session_completed=5, last=nightVideos/bridgeEntry/P2_FrameDiff, next=nightVideos/bridgeEntry/P3_MOG2

- `2026-05-01T20:36:13` G2G3 auto status: completed nightVideos/bridgeEntry/P3_MOG2; completed=171/318, pending=147, running=0, failed=0, videos=28/53, session_completed=6, last=nightVideos/bridgeEntry/P3_MOG2, next=nightVideos/bridgeEntry/ASMAG_TR_FAST

- `2026-05-01T20:42:38` G2G3 auto status: completed nightVideos/bridgeEntry/ASMAG_TR_FAST; completed=172/318, pending=146, running=0, failed=0, videos=28/53, session_completed=7, last=nightVideos/bridgeEntry/ASMAG_TR_FAST, next=nightVideos/bridgeEntry/ASMAG_TR_CONTROLLER

- `2026-05-01T20:49:21` G2G3 auto status: completed nightVideos/bridgeEntry/ASMAG_TR_CONTROLLER; completed=173/318, pending=145, running=0, failed=0, videos=28/53, session_completed=8, last=nightVideos/bridgeEntry/ASMAG_TR_CONTROLLER, next=nightVideos/bridgeEntry/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-01T20:57:26` G2G3 auto status: completed nightVideos/bridgeEntry/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=174/318, pending=144, running=0, failed=0, videos=29/53, session_completed=9, last=nightVideos/bridgeEntry/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=nightVideos/busyBoulvard/P1_YOLO_Only

- `2026-05-01T21:07:06` G2G3 auto status: completed nightVideos/busyBoulvard/P1_YOLO_Only; completed=175/318, pending=143, running=0, failed=0, videos=29/53, session_completed=10, last=nightVideos/busyBoulvard/P1_YOLO_Only, next=nightVideos/busyBoulvard/P2_FrameDiff

- `2026-05-01T21:35:54` G2G3 auto status: completed nightVideos/busyBoulvard/P2_FrameDiff; completed=176/318, pending=142, running=0, failed=0, videos=29/53, session_completed=1, last=nightVideos/busyBoulvard/P2_FrameDiff, next=nightVideos/busyBoulvard/P3_MOG2

- `2026-05-01T21:44:08` G2G3 auto status: completed nightVideos/busyBoulvard/P3_MOG2; completed=177/318, pending=141, running=0, failed=0, videos=29/53, session_completed=2, last=nightVideos/busyBoulvard/P3_MOG2, next=nightVideos/busyBoulvard/ASMAG_TR_FAST

- `2026-05-01T21:50:46` G2G3 auto status: completed nightVideos/busyBoulvard/ASMAG_TR_FAST; completed=178/318, pending=140, running=0, failed=0, videos=29/53, session_completed=3, last=nightVideos/busyBoulvard/ASMAG_TR_FAST, next=nightVideos/busyBoulvard/ASMAG_TR_CONTROLLER

- `2026-05-01T21:59:16` G2G3 auto status: completed nightVideos/busyBoulvard/ASMAG_TR_CONTROLLER; completed=179/318, pending=139, running=0, failed=0, videos=29/53, session_completed=4, last=nightVideos/busyBoulvard/ASMAG_TR_CONTROLLER, next=nightVideos/busyBoulvard/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-01T22:09:14` G2G3 auto status: completed nightVideos/busyBoulvard/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=180/318, pending=138, running=0, failed=0, videos=30/53, session_completed=5, last=nightVideos/busyBoulvard/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=nightVideos/fluidHighway/P1_YOLO_Only

- `2026-05-01T22:13:59` G2G3 auto status: completed nightVideos/fluidHighway/P1_YOLO_Only; completed=181/318, pending=137, running=0, failed=0, videos=30/53, session_completed=6, last=nightVideos/fluidHighway/P1_YOLO_Only, next=nightVideos/fluidHighway/P2_FrameDiff

- `2026-05-01T22:16:32` G2G3 auto status: completed nightVideos/fluidHighway/P2_FrameDiff; completed=182/318, pending=136, running=0, failed=0, videos=30/53, session_completed=7, last=nightVideos/fluidHighway/P2_FrameDiff, next=nightVideos/fluidHighway/P3_MOG2

- `2026-05-01T22:20:57` G2G3 auto status: completed nightVideos/fluidHighway/P3_MOG2; completed=183/318, pending=135, running=0, failed=0, videos=30/53, session_completed=8, last=nightVideos/fluidHighway/P3_MOG2, next=nightVideos/fluidHighway/ASMAG_TR_FAST

- `2026-05-01T22:25:21` G2G3 auto status: completed nightVideos/fluidHighway/ASMAG_TR_FAST; completed=184/318, pending=134, running=0, failed=0, videos=30/53, session_completed=9, last=nightVideos/fluidHighway/ASMAG_TR_FAST, next=nightVideos/fluidHighway/ASMAG_TR_CONTROLLER

- `2026-05-01T22:29:40` G2G3 auto status: completed nightVideos/fluidHighway/ASMAG_TR_CONTROLLER; completed=185/318, pending=133, running=0, failed=0, videos=30/53, session_completed=10, last=nightVideos/fluidHighway/ASMAG_TR_CONTROLLER, next=nightVideos/fluidHighway/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-02T16:18:43` G2G3 auto status: completed nightVideos/fluidHighway/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=186/318, pending=132, running=0, failed=0, videos=31/53, session_completed=1, last=nightVideos/fluidHighway/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=nightVideos/streetCornerAtNight/P1_YOLO_Only

- `2026-05-02T16:32:18` G2G3 auto status: completed nightVideos/streetCornerAtNight/P1_YOLO_Only; completed=187/318, pending=131, running=0, failed=0, videos=31/53, session_completed=2, last=nightVideos/streetCornerAtNight/P1_YOLO_Only, next=nightVideos/streetCornerAtNight/P2_FrameDiff

- `2026-05-02T16:37:07` G2G3 auto status: completed nightVideos/streetCornerAtNight/P2_FrameDiff; completed=188/318, pending=130, running=0, failed=0, videos=31/53, session_completed=3, last=nightVideos/streetCornerAtNight/P2_FrameDiff, next=nightVideos/streetCornerAtNight/P3_MOG2

- `2026-05-02T16:44:04` G2G3 auto status: completed nightVideos/streetCornerAtNight/P3_MOG2; completed=189/318, pending=129, running=0, failed=0, videos=31/53, session_completed=4, last=nightVideos/streetCornerAtNight/P3_MOG2, next=nightVideos/streetCornerAtNight/ASMAG_TR_FAST

- `2026-05-02T16:50:36` G2G3 auto status: completed nightVideos/streetCornerAtNight/ASMAG_TR_FAST; completed=190/318, pending=128, running=0, failed=0, videos=31/53, session_completed=5, last=nightVideos/streetCornerAtNight/ASMAG_TR_FAST, next=nightVideos/streetCornerAtNight/ASMAG_TR_CONTROLLER

- `2026-05-02T16:57:24` G2G3 auto status: completed nightVideos/streetCornerAtNight/ASMAG_TR_CONTROLLER; completed=191/318, pending=127, running=0, failed=0, videos=31/53, session_completed=6, last=nightVideos/streetCornerAtNight/ASMAG_TR_CONTROLLER, next=nightVideos/streetCornerAtNight/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-02T17:07:04` G2G3 auto status: completed nightVideos/streetCornerAtNight/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=192/318, pending=126, running=0, failed=0, videos=32/53, session_completed=7, last=nightVideos/streetCornerAtNight/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=nightVideos/tramStation/P1_YOLO_Only

- `2026-05-02T17:19:34` G2G3 auto status: completed nightVideos/tramStation/P1_YOLO_Only; completed=193/318, pending=125, running=0, failed=0, videos=32/53, session_completed=8, last=nightVideos/tramStation/P1_YOLO_Only, next=nightVideos/tramStation/P2_FrameDiff

- `2026-05-02T17:27:58` G2G3 auto status: completed nightVideos/tramStation/P2_FrameDiff; completed=194/318, pending=124, running=0, failed=0, videos=32/53, session_completed=9, last=nightVideos/tramStation/P2_FrameDiff, next=nightVideos/tramStation/P3_MOG2

- `2026-05-02T17:36:56` G2G3 auto status: completed nightVideos/tramStation/P3_MOG2; completed=195/318, pending=123, running=0, failed=0, videos=32/53, session_completed=10, last=nightVideos/tramStation/P3_MOG2, next=nightVideos/tramStation/ASMAG_TR_FAST

- `2026-05-02T17:45:11` G2G3 auto status: completed nightVideos/tramStation/ASMAG_TR_FAST; completed=196/318, pending=122, running=0, failed=0, videos=32/53, session_completed=11, last=nightVideos/tramStation/ASMAG_TR_FAST, next=nightVideos/tramStation/ASMAG_TR_CONTROLLER

- `2026-05-02T17:54:02` G2G3 auto status: completed nightVideos/tramStation/ASMAG_TR_CONTROLLER; completed=197/318, pending=121, running=0, failed=0, videos=32/53, session_completed=12, last=nightVideos/tramStation/ASMAG_TR_CONTROLLER, next=nightVideos/tramStation/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-02T18:03:55` G2G3 auto status: completed nightVideos/tramStation/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=198/318, pending=120, running=0, failed=0, videos=33/53, session_completed=13, last=nightVideos/tramStation/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=nightVideos/winterStreet/P1_YOLO_Only

- `2026-05-02T18:07:35` G2G3 auto status: completed nightVideos/winterStreet/P1_YOLO_Only; completed=199/318, pending=119, running=0, failed=0, videos=33/53, session_completed=14, last=nightVideos/winterStreet/P1_YOLO_Only, next=nightVideos/winterStreet/P2_FrameDiff

- `2026-05-02T18:09:44` G2G3 auto status: completed nightVideos/winterStreet/P2_FrameDiff; completed=200/318, pending=118, running=0, failed=0, videos=33/53, session_completed=15, last=nightVideos/winterStreet/P2_FrameDiff, next=nightVideos/winterStreet/P3_MOG2

- `2026-05-02T18:13:10` G2G3 auto status: completed nightVideos/winterStreet/P3_MOG2; completed=201/318, pending=117, running=0, failed=0, videos=33/53, session_completed=16, last=nightVideos/winterStreet/P3_MOG2, next=nightVideos/winterStreet/ASMAG_TR_FAST

- `2026-05-02T18:16:33` G2G3 auto status: completed nightVideos/winterStreet/ASMAG_TR_FAST; completed=202/318, pending=116, running=0, failed=0, videos=33/53, session_completed=17, last=nightVideos/winterStreet/ASMAG_TR_FAST, next=nightVideos/winterStreet/ASMAG_TR_CONTROLLER

- `2026-05-02T18:19:57` G2G3 auto status: completed nightVideos/winterStreet/ASMAG_TR_CONTROLLER; completed=203/318, pending=115, running=0, failed=0, videos=33/53, session_completed=18, last=nightVideos/winterStreet/ASMAG_TR_CONTROLLER, next=nightVideos/winterStreet/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-02T18:24:24` G2G3 auto status: completed nightVideos/winterStreet/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=204/318, pending=114, running=0, failed=0, videos=34/53, session_completed=19, last=nightVideos/winterStreet/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=PTZ/continuousPan/P1_YOLO_Only

- `2026-05-02T18:29:05` G2G3 auto status: completed PTZ/continuousPan/P1_YOLO_Only; completed=205/318, pending=113, running=0, failed=0, videos=34/53, session_completed=20, last=PTZ/continuousPan/P1_YOLO_Only, next=PTZ/continuousPan/P2_FrameDiff

- `2026-05-02T18:33:18` G2G3 auto status: completed PTZ/continuousPan/P2_FrameDiff; completed=206/318, pending=112, running=0, failed=0, videos=34/53, session_completed=21, last=PTZ/continuousPan/P2_FrameDiff, next=PTZ/continuousPan/P3_MOG2

- `2026-05-02T18:37:48` G2G3 auto status: completed PTZ/continuousPan/P3_MOG2; completed=207/318, pending=111, running=0, failed=0, videos=34/53, session_completed=22, last=PTZ/continuousPan/P3_MOG2, next=PTZ/continuousPan/ASMAG_TR_FAST

- `2026-05-02T18:42:24` G2G3 auto status: completed PTZ/continuousPan/ASMAG_TR_FAST; completed=208/318, pending=110, running=0, failed=0, videos=34/53, session_completed=23, last=PTZ/continuousPan/ASMAG_TR_FAST, next=PTZ/continuousPan/ASMAG_TR_CONTROLLER

- `2026-05-02T18:46:54` G2G3 auto status: completed PTZ/continuousPan/ASMAG_TR_CONTROLLER; completed=209/318, pending=109, running=0, failed=0, videos=34/53, session_completed=24, last=PTZ/continuousPan/ASMAG_TR_CONTROLLER, next=PTZ/continuousPan/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-02T18:53:45` G2G3 auto status: completed PTZ/continuousPan/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=210/318, pending=108, running=0, failed=0, videos=35/53, session_completed=25, last=PTZ/continuousPan/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=PTZ/intermittentPan/P1_YOLO_Only

- `2026-05-02T19:03:11` G2G3 auto status: completed PTZ/intermittentPan/P1_YOLO_Only; completed=211/318, pending=107, running=0, failed=0, videos=35/53, session_completed=26, last=PTZ/intermittentPan/P1_YOLO_Only, next=PTZ/intermittentPan/P2_FrameDiff

- `2026-05-02T19:08:57` G2G3 auto status: completed PTZ/intermittentPan/P2_FrameDiff; completed=212/318, pending=106, running=0, failed=0, videos=35/53, session_completed=27, last=PTZ/intermittentPan/P2_FrameDiff, next=PTZ/intermittentPan/P3_MOG2

- `2026-05-02T19:16:37` G2G3 auto status: completed PTZ/intermittentPan/P3_MOG2; completed=213/318, pending=105, running=0, failed=0, videos=35/53, session_completed=28, last=PTZ/intermittentPan/P3_MOG2, next=PTZ/intermittentPan/ASMAG_TR_FAST

- `2026-05-02T19:23:35` G2G3 auto status: completed PTZ/intermittentPan/ASMAG_TR_FAST; completed=214/318, pending=104, running=0, failed=0, videos=35/53, session_completed=29, last=PTZ/intermittentPan/ASMAG_TR_FAST, next=PTZ/intermittentPan/ASMAG_TR_CONTROLLER

- `2026-05-02T19:31:11` G2G3 auto status: completed PTZ/intermittentPan/ASMAG_TR_CONTROLLER; completed=215/318, pending=103, running=0, failed=0, videos=35/53, session_completed=30, last=PTZ/intermittentPan/ASMAG_TR_CONTROLLER, next=PTZ/intermittentPan/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-02T19:32:09` G2G3 auto status: run completed or paused after selected batch; completed=215/318, pending=103, running=0, failed=0, videos=35/53, session_completed=30, last=PTZ/intermittentPan/ASMAG_TR_CONTROLLER, next=PTZ/intermittentPan/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-02T20:47:06` G2G3 auto status: completed PTZ/intermittentPan/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=216/318, pending=102, running=0, failed=0, videos=36/53, session_completed=1, last=PTZ/intermittentPan/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=PTZ/twoPositionPTZCam/P1_YOLO_Only

- `2026-05-02T20:54:01` G2G3 auto status: completed PTZ/twoPositionPTZCam/P1_YOLO_Only; completed=217/318, pending=101, running=0, failed=0, videos=36/53, session_completed=2, last=PTZ/twoPositionPTZCam/P1_YOLO_Only, next=PTZ/twoPositionPTZCam/P2_FrameDiff

- `2026-05-02T20:57:00` G2G3 auto status: completed PTZ/twoPositionPTZCam/P2_FrameDiff; completed=218/318, pending=100, running=0, failed=0, videos=36/53, session_completed=3, last=PTZ/twoPositionPTZCam/P2_FrameDiff, next=PTZ/twoPositionPTZCam/P3_MOG2

- `2026-05-02T21:02:14` G2G3 auto status: completed PTZ/twoPositionPTZCam/P3_MOG2; completed=219/318, pending=99, running=0, failed=0, videos=36/53, session_completed=4, last=PTZ/twoPositionPTZCam/P3_MOG2, next=PTZ/twoPositionPTZCam/ASMAG_TR_FAST

- `2026-05-02T21:06:24` G2G3 auto status: completed PTZ/twoPositionPTZCam/ASMAG_TR_FAST; completed=220/318, pending=98, running=0, failed=0, videos=36/53, session_completed=5, last=PTZ/twoPositionPTZCam/ASMAG_TR_FAST, next=PTZ/twoPositionPTZCam/ASMAG_TR_CONTROLLER

- `2026-05-02T21:11:15` G2G3 auto status: completed PTZ/twoPositionPTZCam/ASMAG_TR_CONTROLLER; completed=221/318, pending=97, running=0, failed=0, videos=36/53, session_completed=6, last=PTZ/twoPositionPTZCam/ASMAG_TR_CONTROLLER, next=PTZ/twoPositionPTZCam/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-02T21:17:44` G2G3 auto status: completed PTZ/twoPositionPTZCam/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=222/318, pending=96, running=0, failed=0, videos=37/53, session_completed=7, last=PTZ/twoPositionPTZCam/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=PTZ/zoomInZoomOut/P1_YOLO_Only

- `2026-05-02T21:20:33` G2G3 auto status: completed PTZ/zoomInZoomOut/P1_YOLO_Only; completed=223/318, pending=95, running=0, failed=0, videos=37/53, session_completed=8, last=PTZ/zoomInZoomOut/P1_YOLO_Only, next=PTZ/zoomInZoomOut/P2_FrameDiff

- `2026-05-02T21:21:55` G2G3 auto status: completed PTZ/zoomInZoomOut/P2_FrameDiff; completed=224/318, pending=94, running=0, failed=0, videos=37/53, session_completed=9, last=PTZ/zoomInZoomOut/P2_FrameDiff, next=PTZ/zoomInZoomOut/P3_MOG2

- `2026-05-02T21:24:22` G2G3 auto status: completed PTZ/zoomInZoomOut/P3_MOG2; completed=225/318, pending=93, running=0, failed=0, videos=37/53, session_completed=10, last=PTZ/zoomInZoomOut/P3_MOG2, next=PTZ/zoomInZoomOut/ASMAG_TR_FAST

- `2026-05-02T21:26:20` G2G3 auto status: completed PTZ/zoomInZoomOut/ASMAG_TR_FAST; completed=226/318, pending=92, running=0, failed=0, videos=37/53, session_completed=11, last=PTZ/zoomInZoomOut/ASMAG_TR_FAST, next=PTZ/zoomInZoomOut/ASMAG_TR_CONTROLLER

- `2026-05-02T21:28:41` G2G3 auto status: completed PTZ/zoomInZoomOut/ASMAG_TR_CONTROLLER; completed=227/318, pending=91, running=0, failed=0, videos=37/53, session_completed=12, last=PTZ/zoomInZoomOut/ASMAG_TR_CONTROLLER, next=PTZ/zoomInZoomOut/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-02T21:31:07` G2G3 auto status: completed PTZ/zoomInZoomOut/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=228/318, pending=90, running=0, failed=0, videos=38/53, session_completed=13, last=PTZ/zoomInZoomOut/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=shadow/backdoor/P1_YOLO_Only

- `2026-05-02T21:39:05` G2G3 auto status: completed shadow/backdoor/P1_YOLO_Only; completed=229/318, pending=89, running=0, failed=0, videos=38/53, session_completed=14, last=shadow/backdoor/P1_YOLO_Only, next=shadow/backdoor/P2_FrameDiff

- `2026-05-02T21:41:14` G2G3 auto status: completed shadow/backdoor/P2_FrameDiff; completed=230/318, pending=88, running=0, failed=0, videos=38/53, session_completed=15, last=shadow/backdoor/P2_FrameDiff, next=shadow/backdoor/P3_MOG2

- `2026-05-02T21:44:03` G2G3 auto status: completed shadow/backdoor/P3_MOG2; completed=231/318, pending=87, running=0, failed=0, videos=38/53, session_completed=16, last=shadow/backdoor/P3_MOG2, next=shadow/backdoor/ASMAG_TR_FAST

- `2026-05-02T21:46:34` G2G3 auto status: completed shadow/backdoor/ASMAG_TR_FAST; completed=232/318, pending=86, running=0, failed=0, videos=38/53, session_completed=17, last=shadow/backdoor/ASMAG_TR_FAST, next=shadow/backdoor/ASMAG_TR_CONTROLLER

- `2026-05-02T21:49:18` G2G3 auto status: completed shadow/backdoor/ASMAG_TR_CONTROLLER; completed=233/318, pending=85, running=0, failed=0, videos=38/53, session_completed=18, last=shadow/backdoor/ASMAG_TR_CONTROLLER, next=shadow/backdoor/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-02T21:52:20` G2G3 auto status: completed shadow/backdoor/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=234/318, pending=84, running=0, failed=0, videos=39/53, session_completed=19, last=shadow/backdoor/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=shadow/bungalows/P1_YOLO_Only

- `2026-05-02T21:58:19` G2G3 auto status: completed shadow/bungalows/P1_YOLO_Only; completed=235/318, pending=83, running=0, failed=0, videos=39/53, session_completed=20, last=shadow/bungalows/P1_YOLO_Only, next=shadow/bungalows/P2_FrameDiff

- `2026-05-02T22:01:07` G2G3 auto status: completed shadow/bungalows/P2_FrameDiff; completed=236/318, pending=82, running=0, failed=0, videos=39/53, session_completed=21, last=shadow/bungalows/P2_FrameDiff, next=shadow/bungalows/P3_MOG2

- `2026-05-02T22:04:07` G2G3 auto status: completed shadow/bungalows/P3_MOG2; completed=237/318, pending=81, running=0, failed=0, videos=39/53, session_completed=22, last=shadow/bungalows/P3_MOG2, next=shadow/bungalows/ASMAG_TR_FAST

- `2026-05-02T22:07:05` G2G3 auto status: completed shadow/bungalows/ASMAG_TR_FAST; completed=238/318, pending=80, running=0, failed=0, videos=39/53, session_completed=23, last=shadow/bungalows/ASMAG_TR_FAST, next=shadow/bungalows/ASMAG_TR_CONTROLLER

- `2026-05-02T22:10:02` G2G3 auto status: completed shadow/bungalows/ASMAG_TR_CONTROLLER; completed=239/318, pending=79, running=0, failed=0, videos=39/53, session_completed=24, last=shadow/bungalows/ASMAG_TR_CONTROLLER, next=shadow/bungalows/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-02T22:13:40` G2G3 auto status: completed shadow/bungalows/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=240/318, pending=78, running=0, failed=0, videos=40/53, session_completed=25, last=shadow/bungalows/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=shadow/busStation/P1_YOLO_Only

- `2026-05-02T22:17:16` G2G3 auto status: completed shadow/busStation/P1_YOLO_Only; completed=241/318, pending=77, running=0, failed=0, videos=40/53, session_completed=26, last=shadow/busStation/P1_YOLO_Only, next=shadow/busStation/P2_FrameDiff

- `2026-05-02T22:18:45` G2G3 auto status: completed shadow/busStation/P2_FrameDiff; completed=242/318, pending=76, running=0, failed=0, videos=40/53, session_completed=27, last=shadow/busStation/P2_FrameDiff, next=shadow/busStation/P3_MOG2

- `2026-05-02T22:21:59` G2G3 auto status: completed shadow/busStation/P3_MOG2; completed=243/318, pending=75, running=0, failed=0, videos=40/53, session_completed=28, last=shadow/busStation/P3_MOG2, next=shadow/busStation/ASMAG_TR_FAST

- `2026-05-02T22:24:22` G2G3 auto status: completed shadow/busStation/ASMAG_TR_FAST; completed=244/318, pending=74, running=0, failed=0, videos=40/53, session_completed=29, last=shadow/busStation/ASMAG_TR_FAST, next=shadow/busStation/ASMAG_TR_CONTROLLER

- `2026-05-02T22:27:34` G2G3 auto status: completed shadow/busStation/ASMAG_TR_CONTROLLER; completed=245/318, pending=73, running=0, failed=0, videos=40/53, session_completed=30, last=shadow/busStation/ASMAG_TR_CONTROLLER, next=shadow/busStation/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-02T22:28:54` G2G3 auto status: run completed or paused after selected batch; completed=245/318, pending=73, running=0, failed=0, videos=40/53, session_completed=30, last=shadow/busStation/ASMAG_TR_CONTROLLER, next=shadow/busStation/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-02T22:41:51` G2G3 auto status: completed shadow/busStation/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=246/318, pending=72, running=0, failed=0, videos=41/53, session_completed=1, last=shadow/busStation/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=shadow/copyMachine/P1_YOLO_Only

- `2026-05-02T22:54:59` G2G3 auto status: completed shadow/copyMachine/P1_YOLO_Only; completed=247/318, pending=71, running=0, failed=0, videos=41/53, session_completed=2, last=shadow/copyMachine/P1_YOLO_Only, next=shadow/copyMachine/P2_FrameDiff

- `2026-05-02T23:02:48` G2G3 auto status: completed shadow/copyMachine/P2_FrameDiff; completed=248/318, pending=70, running=0, failed=0, videos=41/53, session_completed=3, last=shadow/copyMachine/P2_FrameDiff, next=shadow/copyMachine/P3_MOG2

- `2026-05-02T23:13:08` G2G3 auto status: completed shadow/copyMachine/P3_MOG2; completed=249/318, pending=69, running=0, failed=0, videos=41/53, session_completed=4, last=shadow/copyMachine/P3_MOG2, next=shadow/copyMachine/ASMAG_TR_FAST

- `2026-05-02T23:23:01` G2G3 auto status: completed shadow/copyMachine/ASMAG_TR_FAST; completed=250/318, pending=68, running=0, failed=0, videos=41/53, session_completed=5, last=shadow/copyMachine/ASMAG_TR_FAST, next=shadow/copyMachine/ASMAG_TR_CONTROLLER

- `2026-05-02T23:33:24` G2G3 auto status: completed shadow/copyMachine/ASMAG_TR_CONTROLLER; completed=251/318, pending=67, running=0, failed=0, videos=41/53, session_completed=6, last=shadow/copyMachine/ASMAG_TR_CONTROLLER, next=shadow/copyMachine/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-02T23:45:40` G2G3 auto status: completed shadow/copyMachine/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=252/318, pending=66, running=0, failed=0, videos=42/53, session_completed=7, last=shadow/copyMachine/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=shadow/cubicle/P1_YOLO_Only

- `2026-05-03T00:12:40` G2G3 auto status: completed shadow/cubicle/P1_YOLO_Only; completed=253/318, pending=65, running=0, failed=0, videos=42/53, session_completed=8, last=shadow/cubicle/P1_YOLO_Only, next=shadow/cubicle/P2_FrameDiff

- `2026-05-03T00:19:19` G2G3 auto status: completed shadow/cubicle/P2_FrameDiff; completed=254/318, pending=64, running=0, failed=0, videos=42/53, session_completed=9, last=shadow/cubicle/P2_FrameDiff, next=shadow/cubicle/P3_MOG2

- `2026-05-03T00:31:01` G2G3 auto status: completed shadow/cubicle/P3_MOG2; completed=255/318, pending=63, running=0, failed=0, videos=42/53, session_completed=10, last=shadow/cubicle/P3_MOG2, next=shadow/cubicle/ASMAG_TR_FAST

- `2026-05-03T00:42:33` G2G3 auto status: completed shadow/cubicle/ASMAG_TR_FAST; completed=256/318, pending=62, running=0, failed=0, videos=42/53, session_completed=11, last=shadow/cubicle/ASMAG_TR_FAST, next=shadow/cubicle/ASMAG_TR_CONTROLLER

- `2026-05-03T00:53:52` G2G3 auto status: completed shadow/cubicle/ASMAG_TR_CONTROLLER; completed=257/318, pending=61, running=0, failed=0, videos=42/53, session_completed=12, last=shadow/cubicle/ASMAG_TR_CONTROLLER, next=shadow/cubicle/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-03T01:07:06` G2G3 auto status: completed shadow/cubicle/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=258/318, pending=60, running=0, failed=0, videos=43/53, session_completed=13, last=shadow/cubicle/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=shadow/peopleInShade/P1_YOLO_Only

- `2026-05-03T01:10:43` G2G3 auto status: completed shadow/peopleInShade/P1_YOLO_Only; completed=259/318, pending=59, running=0, failed=0, videos=43/53, session_completed=14, last=shadow/peopleInShade/P1_YOLO_Only, next=shadow/peopleInShade/P2_FrameDiff

- `2026-05-03T01:12:09` G2G3 auto status: completed shadow/peopleInShade/P2_FrameDiff; completed=260/318, pending=58, running=0, failed=0, videos=43/53, session_completed=15, last=shadow/peopleInShade/P2_FrameDiff, next=shadow/peopleInShade/P3_MOG2

- `2026-05-03T01:14:23` G2G3 auto status: completed shadow/peopleInShade/P3_MOG2; completed=261/318, pending=57, running=0, failed=0, videos=43/53, session_completed=16, last=shadow/peopleInShade/P3_MOG2, next=shadow/peopleInShade/ASMAG_TR_FAST

- `2026-05-03T01:16:18` G2G3 auto status: completed shadow/peopleInShade/ASMAG_TR_FAST; completed=262/318, pending=56, running=0, failed=0, videos=43/53, session_completed=17, last=shadow/peopleInShade/ASMAG_TR_FAST, next=shadow/peopleInShade/ASMAG_TR_CONTROLLER

- `2026-05-03T01:18:32` G2G3 auto status: completed shadow/peopleInShade/ASMAG_TR_CONTROLLER; completed=263/318, pending=55, running=0, failed=0, videos=43/53, session_completed=18, last=shadow/peopleInShade/ASMAG_TR_CONTROLLER, next=shadow/peopleInShade/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-03T01:20:59` G2G3 auto status: completed shadow/peopleInShade/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=264/318, pending=54, running=0, failed=0, videos=44/53, session_completed=19, last=shadow/peopleInShade/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=thermal/corridor/P1_YOLO_Only

- `2026-05-03T01:43:32` G2G3 auto status: completed thermal/corridor/P1_YOLO_Only; completed=265/318, pending=53, running=0, failed=0, videos=44/53, session_completed=20, last=thermal/corridor/P1_YOLO_Only, next=thermal/corridor/P2_FrameDiff

- `2026-05-03T01:47:10` G2G3 auto status: completed thermal/corridor/P2_FrameDiff; completed=266/318, pending=52, running=0, failed=0, videos=44/53, session_completed=21, last=thermal/corridor/P2_FrameDiff, next=thermal/corridor/P3_MOG2

- `2026-05-03T01:57:05` G2G3 auto status: completed thermal/corridor/P3_MOG2; completed=267/318, pending=51, running=0, failed=0, videos=44/53, session_completed=22, last=thermal/corridor/P3_MOG2, next=thermal/corridor/ASMAG_TR_FAST

- `2026-05-03T02:06:52` G2G3 auto status: completed thermal/corridor/ASMAG_TR_FAST; completed=268/318, pending=50, running=0, failed=0, videos=44/53, session_completed=23, last=thermal/corridor/ASMAG_TR_FAST, next=thermal/corridor/ASMAG_TR_CONTROLLER

- `2026-05-03T02:18:05` G2G3 auto status: completed thermal/corridor/ASMAG_TR_CONTROLLER; completed=269/318, pending=49, running=0, failed=0, videos=44/53, session_completed=24, last=thermal/corridor/ASMAG_TR_CONTROLLER, next=thermal/corridor/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-03T02:30:02` G2G3 auto status: completed thermal/corridor/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=270/318, pending=48, running=0, failed=0, videos=45/53, session_completed=25, last=thermal/corridor/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=thermal/diningRoom/P1_YOLO_Only

- `2026-05-03T02:44:05` G2G3 auto status: completed thermal/diningRoom/P1_YOLO_Only; completed=271/318, pending=47, running=0, failed=0, videos=45/53, session_completed=26, last=thermal/diningRoom/P1_YOLO_Only, next=thermal/diningRoom/P2_FrameDiff

- `2026-05-03T02:49:01` G2G3 auto status: completed thermal/diningRoom/P2_FrameDiff; completed=272/318, pending=46, running=0, failed=0, videos=45/53, session_completed=27, last=thermal/diningRoom/P2_FrameDiff, next=thermal/diningRoom/P3_MOG2

- `2026-05-03T02:59:37` G2G3 auto status: completed thermal/diningRoom/P3_MOG2; completed=273/318, pending=45, running=0, failed=0, videos=45/53, session_completed=28, last=thermal/diningRoom/P3_MOG2, next=thermal/diningRoom/ASMAG_TR_FAST

- `2026-05-03T03:09:12` G2G3 auto status: completed thermal/diningRoom/ASMAG_TR_FAST; completed=274/318, pending=44, running=0, failed=0, videos=45/53, session_completed=29, last=thermal/diningRoom/ASMAG_TR_FAST, next=thermal/diningRoom/ASMAG_TR_CONTROLLER

- `2026-05-03T03:19:16` G2G3 auto status: completed thermal/diningRoom/ASMAG_TR_CONTROLLER; completed=275/318, pending=43, running=0, failed=0, videos=45/53, session_completed=30, last=thermal/diningRoom/ASMAG_TR_CONTROLLER, next=thermal/diningRoom/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-03T03:20:12` G2G3 auto status: run completed or paused after selected batch; completed=275/318, pending=43, running=0, failed=0, videos=45/53, session_completed=30, last=thermal/diningRoom/ASMAG_TR_CONTROLLER, next=thermal/diningRoom/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-03T07:47:14` G2G3 auto status: completed thermal/diningRoom/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=276/318, pending=42, running=0, failed=0, videos=46/53, session_completed=1, last=thermal/diningRoom/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=thermal/lakeSide/P1_YOLO_Only

- `2026-05-03T08:13:06` G2G3 auto status: completed thermal/lakeSide/P1_YOLO_Only; completed=277/318, pending=41, running=0, failed=0, videos=46/53, session_completed=2, last=thermal/lakeSide/P1_YOLO_Only, next=thermal/lakeSide/P2_FrameDiff

- `2026-05-03T08:14:47` G2G3 auto status: completed thermal/lakeSide/P2_FrameDiff; completed=278/318, pending=40, running=0, failed=0, videos=46/53, session_completed=3, last=thermal/lakeSide/P2_FrameDiff, next=thermal/lakeSide/P3_MOG2

- `2026-05-03T08:31:11` G2G3 auto status: completed thermal/lakeSide/P3_MOG2; completed=279/318, pending=39, running=0, failed=0, videos=46/53, session_completed=4, last=thermal/lakeSide/P3_MOG2, next=thermal/lakeSide/ASMAG_TR_FAST

- `2026-05-03T08:41:48` G2G3 auto status: completed thermal/lakeSide/ASMAG_TR_FAST; completed=280/318, pending=38, running=0, failed=0, videos=46/53, session_completed=5, last=thermal/lakeSide/ASMAG_TR_FAST, next=thermal/lakeSide/ASMAG_TR_CONTROLLER

- `2026-05-03T08:53:49` G2G3 auto status: completed thermal/lakeSide/ASMAG_TR_CONTROLLER; completed=281/318, pending=37, running=0, failed=0, videos=46/53, session_completed=6, last=thermal/lakeSide/ASMAG_TR_CONTROLLER, next=thermal/lakeSide/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-03T09:05:11` G2G3 auto status: completed thermal/lakeSide/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=282/318, pending=36, running=0, failed=0, videos=47/53, session_completed=7, last=thermal/lakeSide/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=thermal/library/P1_YOLO_Only

- `2026-05-03T09:24:51` G2G3 auto status: completed thermal/library/P1_YOLO_Only; completed=283/318, pending=35, running=0, failed=0, videos=47/53, session_completed=8, last=thermal/library/P1_YOLO_Only, next=thermal/library/P2_FrameDiff

- `2026-05-03T09:29:23` G2G3 auto status: completed thermal/library/P2_FrameDiff; completed=284/318, pending=34, running=0, failed=0, videos=47/53, session_completed=9, last=thermal/library/P2_FrameDiff, next=thermal/library/P3_MOG2

- `2026-05-03T09:42:05` G2G3 auto status: completed thermal/library/P3_MOG2; completed=285/318, pending=33, running=0, failed=0, videos=47/53, session_completed=10, last=thermal/library/P3_MOG2, next=thermal/library/ASMAG_TR_FAST

- `2026-05-03T09:52:55` G2G3 auto status: completed thermal/library/ASMAG_TR_FAST; completed=286/318, pending=32, running=0, failed=0, videos=47/53, session_completed=11, last=thermal/library/ASMAG_TR_FAST, next=thermal/library/ASMAG_TR_CONTROLLER

- `2026-05-03T10:05:44` G2G3 auto status: completed thermal/library/ASMAG_TR_CONTROLLER; completed=287/318, pending=31, running=0, failed=0, videos=47/53, session_completed=12, last=thermal/library/ASMAG_TR_CONTROLLER, next=thermal/library/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-03T10:20:17` G2G3 auto status: completed thermal/library/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=288/318, pending=30, running=0, failed=0, videos=48/53, session_completed=13, last=thermal/library/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=thermal/park/P1_YOLO_Only

- `2026-05-03T10:21:48` G2G3 auto status: completed thermal/park/P1_YOLO_Only; completed=289/318, pending=29, running=0, failed=0, videos=48/53, session_completed=14, last=thermal/park/P1_YOLO_Only, next=thermal/park/P2_FrameDiff

- `2026-05-03T10:22:59` G2G3 auto status: completed thermal/park/P2_FrameDiff; completed=290/318, pending=28, running=0, failed=0, videos=48/53, session_completed=15, last=thermal/park/P2_FrameDiff, next=thermal/park/P3_MOG2

- `2026-05-03T10:24:27` G2G3 auto status: completed thermal/park/P3_MOG2; completed=291/318, pending=27, running=0, failed=0, videos=48/53, session_completed=16, last=thermal/park/P3_MOG2, next=thermal/park/ASMAG_TR_FAST

- `2026-05-03T10:25:42` G2G3 auto status: completed thermal/park/ASMAG_TR_FAST; completed=292/318, pending=26, running=0, failed=0, videos=48/53, session_completed=17, last=thermal/park/ASMAG_TR_FAST, next=thermal/park/ASMAG_TR_CONTROLLER

- `2026-05-03T10:27:01` G2G3 auto status: completed thermal/park/ASMAG_TR_CONTROLLER; completed=293/318, pending=25, running=0, failed=0, videos=48/53, session_completed=18, last=thermal/park/ASMAG_TR_CONTROLLER, next=thermal/park/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-03T10:28:33` G2G3 auto status: completed thermal/park/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=294/318, pending=24, running=0, failed=0, videos=49/53, session_completed=19, last=thermal/park/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=turbulence/turbulence0/P1_YOLO_Only

- `2026-05-03T10:46:35` G2G3 auto status: completed turbulence/turbulence0/P1_YOLO_Only; completed=295/318, pending=23, running=0, failed=0, videos=49/53, session_completed=20, last=turbulence/turbulence0/P1_YOLO_Only, next=turbulence/turbulence0/P2_FrameDiff

- `2026-05-03T11:02:30` G2G3 auto status: completed turbulence/turbulence0/P2_FrameDiff; completed=296/318, pending=22, running=0, failed=0, videos=49/53, session_completed=21, last=turbulence/turbulence0/P2_FrameDiff, next=turbulence/turbulence0/P3_MOG2

- `2026-05-03T11:18:54` G2G3 auto status: completed turbulence/turbulence0/P3_MOG2; completed=297/318, pending=21, running=0, failed=0, videos=49/53, session_completed=22, last=turbulence/turbulence0/P3_MOG2, next=turbulence/turbulence0/ASMAG_TR_FAST

- `2026-05-03T11:36:40` G2G3 auto status: completed turbulence/turbulence0/ASMAG_TR_FAST; completed=298/318, pending=20, running=0, failed=0, videos=49/53, session_completed=23, last=turbulence/turbulence0/ASMAG_TR_FAST, next=turbulence/turbulence0/ASMAG_TR_CONTROLLER

- `2026-05-03T11:53:19` G2G3 auto status: completed turbulence/turbulence0/ASMAG_TR_CONTROLLER; completed=299/318, pending=19, running=0, failed=0, videos=49/53, session_completed=24, last=turbulence/turbulence0/ASMAG_TR_CONTROLLER, next=turbulence/turbulence0/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-03T12:15:36` G2G3 auto status: completed turbulence/turbulence0/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=300/318, pending=18, running=0, failed=0, videos=50/53, session_completed=25, last=turbulence/turbulence0/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=turbulence/turbulence1/P1_YOLO_Only

- `2026-05-03T12:28:38` G2G3 auto status: completed turbulence/turbulence1/P1_YOLO_Only; completed=301/318, pending=17, running=0, failed=0, videos=50/53, session_completed=26, last=turbulence/turbulence1/P1_YOLO_Only, next=turbulence/turbulence1/P2_FrameDiff

- `2026-05-03T12:40:33` G2G3 auto status: completed turbulence/turbulence1/P2_FrameDiff; completed=302/318, pending=16, running=0, failed=0, videos=50/53, session_completed=27, last=turbulence/turbulence1/P2_FrameDiff, next=turbulence/turbulence1/P3_MOG2

- `2026-05-03T12:54:03` G2G3 auto status: completed turbulence/turbulence1/P3_MOG2; completed=303/318, pending=15, running=0, failed=0, videos=50/53, session_completed=28, last=turbulence/turbulence1/P3_MOG2, next=turbulence/turbulence1/ASMAG_TR_FAST

- `2026-05-03T13:07:42` G2G3 auto status: completed turbulence/turbulence1/ASMAG_TR_FAST; completed=304/318, pending=14, running=0, failed=0, videos=50/53, session_completed=29, last=turbulence/turbulence1/ASMAG_TR_FAST, next=turbulence/turbulence1/ASMAG_TR_CONTROLLER

- `2026-05-03T13:20:05` G2G3 auto status: completed turbulence/turbulence1/ASMAG_TR_CONTROLLER; completed=305/318, pending=13, running=0, failed=0, videos=50/53, session_completed=30, last=turbulence/turbulence1/ASMAG_TR_CONTROLLER, next=turbulence/turbulence1/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-03T13:21:29` G2G3 auto status: run completed or paused after selected batch; completed=305/318, pending=13, running=0, failed=0, videos=50/53, session_completed=30, last=turbulence/turbulence1/ASMAG_TR_CONTROLLER, next=turbulence/turbulence1/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-03T16:10:53` G2G3 auto status: completed turbulence/turbulence1/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=306/318, pending=12, running=0, failed=0, videos=51/53, session_completed=1, last=turbulence/turbulence1/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=turbulence/turbulence2/P1_YOLO_Only

- `2026-05-03T16:24:23` G2G3 auto status: completed turbulence/turbulence2/P1_YOLO_Only; completed=307/318, pending=11, running=0, failed=0, videos=51/53, session_completed=2, last=turbulence/turbulence2/P1_YOLO_Only, next=turbulence/turbulence2/P2_FrameDiff

- `2026-05-03T16:25:22` G2G3 auto status: completed turbulence/turbulence2/P2_FrameDiff; completed=308/318, pending=10, running=0, failed=0, videos=51/53, session_completed=3, last=turbulence/turbulence2/P2_FrameDiff, next=turbulence/turbulence2/P3_MOG2

- `2026-05-03T16:31:57` G2G3 auto status: completed turbulence/turbulence2/P3_MOG2; completed=309/318, pending=9, running=0, failed=0, videos=51/53, session_completed=4, last=turbulence/turbulence2/P3_MOG2, next=turbulence/turbulence2/ASMAG_TR_FAST

- `2026-05-03T16:35:44` G2G3 auto status: completed turbulence/turbulence2/ASMAG_TR_FAST; completed=310/318, pending=8, running=0, failed=0, videos=51/53, session_completed=5, last=turbulence/turbulence2/ASMAG_TR_FAST, next=turbulence/turbulence2/ASMAG_TR_CONTROLLER

- `2026-05-03T16:42:18` G2G3 auto status: completed turbulence/turbulence2/ASMAG_TR_CONTROLLER; completed=311/318, pending=7, running=0, failed=0, videos=51/53, session_completed=6, last=turbulence/turbulence2/ASMAG_TR_CONTROLLER, next=turbulence/turbulence2/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-03T16:51:02` G2G3 auto status: completed turbulence/turbulence2/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=312/318, pending=6, running=0, failed=0, videos=52/53, session_completed=7, last=turbulence/turbulence2/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=turbulence/turbulence3/P1_YOLO_Only

- `2026-05-03T16:57:21` G2G3 auto status: completed turbulence/turbulence3/P1_YOLO_Only; completed=313/318, pending=5, running=0, failed=0, videos=52/53, session_completed=8, last=turbulence/turbulence3/P1_YOLO_Only, next=turbulence/turbulence3/P2_FrameDiff

- `2026-05-03T17:03:08` G2G3 auto status: completed turbulence/turbulence3/P2_FrameDiff; completed=314/318, pending=4, running=0, failed=0, videos=52/53, session_completed=9, last=turbulence/turbulence3/P2_FrameDiff, next=turbulence/turbulence3/P3_MOG2

- `2026-05-03T17:09:08` G2G3 auto status: completed turbulence/turbulence3/P3_MOG2; completed=315/318, pending=3, running=0, failed=0, videos=52/53, session_completed=10, last=turbulence/turbulence3/P3_MOG2, next=turbulence/turbulence3/ASMAG_TR_FAST

- `2026-05-03T17:15:08` G2G3 auto status: completed turbulence/turbulence3/ASMAG_TR_FAST; completed=316/318, pending=2, running=0, failed=0, videos=52/53, session_completed=11, last=turbulence/turbulence3/ASMAG_TR_FAST, next=turbulence/turbulence3/ASMAG_TR_CONTROLLER

- `2026-05-03T17:20:58` G2G3 auto status: completed turbulence/turbulence3/ASMAG_TR_CONTROLLER; completed=317/318, pending=1, running=0, failed=0, videos=52/53, session_completed=12, last=turbulence/turbulence3/ASMAG_TR_CONTROLLER, next=turbulence/turbulence3/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED

- `2026-05-03T17:28:19` G2G3 auto status: completed turbulence/turbulence3/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED; completed=318/318, pending=0, running=0, failed=0, videos=53/53, session_completed=13, last=turbulence/turbulence3/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=-

- `2026-05-03T17:29:45` G2G3 auto status: run completed or paused after selected batch; completed=318/318, pending=0, running=0, failed=0, videos=53/53, session_completed=13, last=turbulence/turbulence3/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED, next=-

- `2026-05-03T17:33:21` G2G3 final official-like completed: completed=318/318, pending=0, running=0, failed=0, videos=53/53, best_fmeasure=ASMAG_TR_CONTROLLER:0.5939, best_event=ASMAG_TR_CONTROLLER:0.7114.
