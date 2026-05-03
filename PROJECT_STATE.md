# PROJECT STATE - ASMAG-TRC

## Project

- Ten project: ASMAG-TRC
- Dataset chinh: CDnet2014
- Dinh vi bai bao: adaptive inference-control framework for efficient YOLO inference in Edge AI video surveillance

## Muc Tieu Nghien Cuu

ASMAG-TRC huong toi mot framework dieu khien suy luan thich nghi cho video surveillance tren Edge AI. Muc tieu khong phai thay the hoan toan foreground segmentation co dien, ma la dieu phoi khi nao dung YOLO, khi nao reuse prediction, va khi nao fallback ve baseline on dinh de giu FMeasure/Event quality trong khi giam activation va energy.

## Ket Qua Da Hoan Thanh

- Full CDnet2014 sampled metrics da chay va tong hop.
- ASMAG_TR_CONTROLLER category-aware da tao va danh gia.
- Controller gain summary da tao cho category-aware controller.
- 9C online controller smoke da hoan thanh bang checkpoint simulation.
- 9C-Fix cho `ASMAG_TR_CONTROLLER_ONLINE_P3TUNED` da hoan thanh `128/128`.
- 9D calibrated online controller `ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED` da hoan thanh `128/128`.
- G2G3 setup cho official-like CDnet2014 frame_step=1 + Edge CPU-only profiling da tao.
- G2G3 Step 2 smoke test da chay xong cho `baseline/highway/P3_MOG2` voi `max_frames=50`.
- G2G3 Test1Video-Safe da chay xong cho `baseline/highway` voi 6 pipeline cot loi va `max_frames=100`.
- G2G3 Test1Video-300 da chay xong cho `baseline/highway` voi 6 pipeline cot loi va `max_frames=300`.
- G2G3 Representative da chay xong 6 video dai dien x 6 pipeline, `max_frames=300`, `frame_step=1`, Edge CPU-only.
- G2G3 progress monitor da duoc nang cap truoc khi resume: live JSON/Markdown, ETA, frame-level heartbeat, `--progress-only`, va `--show-live-progress`.
- G2G3 full official-like da hoan thanh video dau tien `badWeather/blizzard` voi day du 6/6 pipeline cot loi.
- G2G3 runner da bo sung che do `--max-jobs-per-run 1` de chay tung job rieng le qua nhieu ngay/dem, kem live progress sinh dong voi progress bar, CPU/RAM, energy va fun status line.

## Output Folders Quan Trong

- `outputs/full_cdnet2014_sampled_full_metrics`
- `outputs/full_cdnet2014_controller_sampled_metrics`
- `outputs/q2_core_extended_online_controller_p3tuned`
- `outputs/q2_core_extended_online_controller_calibrated`
- `outputs/full_cdnet2014_official_edge_profile_pc`

## Buoc Dang Lam

- Current task: G2G3 Official-like CDnet2014 frame_step=1 + Edge CPU-only profiling
- Current output: `outputs/full_cdnet2014_official_edge_profile_pc`
- Current config: `configs/full_cdnet2014_official_edge_profile_pc.yaml`
- Current run plan: `configs/full_cdnet2014_official_edge_video_run_plan.csv`
- Pipelines: 6 core pipelines (`P1_YOLO_Only`, `P2_FrameDiff`, `P3_MOG2`, `ASMAG_TR_FAST`, `ASMAG_TR_CONTROLLER`, `ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED`)
- Current phase: Full official-like CDnet2014 dang tam dung an toan sau 1 video; san sang resume video tiep theo.
- Progress hien tai cho full official-like uncapped resume: `completed=6`, `pending=312`, `running=0`, `failed=0`
- Completed videos: `1/53`
- Representative 300-frame artifacts van duoc giu rieng; chung khong duoc tinh la completed cho full official-like uncapped de tranh skip sai.
- Current job: `-`
- Last completed job: `badWeather/blizzard/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED`
- Next pending job: `badWeather/skating/P1_YOLO_Only`
- Post-stop check 2026-04-29 15:19: `run_progress.csv` va live files thong nhat; khong co job `running`, khong can auto-recover.
- Latest commits: `39ba931` for 9C p3tuned, `cb809b5` for 9D calibrated, `de45035` for G2G3 setup + smoke.

## Lenh Resume Chinh

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --run-plan configs/full_cdnet2014_official_edge_video_run_plan.csv --max-videos-per-run 1
```

## Lenh Resume Tung Job

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --run-plan configs/full_cdnet2014_official_edge_video_run_plan.csv --max-jobs-per-run 1
```

## Lenh Chay Qua Dem

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --run-plan configs/full_cdnet2014_official_edge_video_run_plan.csv --max-videos-per-run 10
```

## Lenh Check Progress Khong Chay

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --progress-only
```

## Lenh Xem Live Progress Khong Chay

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --show-live-progress
```

## Smoke Test G2G3

Command da chay:

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --category baseline --video highway --pipeline P3_MOG2 --max-frames 50
```

Ket qua:

- Category/video/pipeline: `baseline/highway/P3_MOG2`
- Frames processed: `50`
- CDnet_FMeasure: `0.8727`
- Event_F1: `1.0000`
- mAP_50: `0.4465`
- Activation: `1.0000`
- Avg_FPS: `4.1100`
- P95_latency_ms: `313.8325`
- Avg CPU: `145.0540`
- Avg RAM MB: `550.8272`
- Energy/frame: `6.7000`
- Simulated_runtime_energy/frame: `7.9084`

Luu y: smoke artifact chi co 50 frame. Runner da duoc chinh de khi resume full official-like se khong skip job nay nhu mot completed official job neu `frames_done < frames_expected`.

## Test1Video-Safe G2G3

Command da chay:

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --category baseline --video highway --max-frames 100
```

Output:

- `outputs/full_cdnet2014_official_edge_profile_pc/test1video_summary.csv`
- `outputs/full_cdnet2014_official_edge_profile_pc/test1video_summary.md`

Ket qua noi bat:

- Slowest pipeline: `P1_YOLO_Only` (`47.40s` runtime).
- Fastest pipeline: `ASMAG_TR_FAST` (`74.52 FPS`).
- Highest FMeasure: `P3_MOG2` (`0.9141`).
- Lowest P95 latency: `P2_FrameDiff` (`2.01 ms`).
- Lowest activation: `P2_FrameDiff` (`0.0100`).
- Deployable candidate behavior: `ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED` dat FMeasure `0.8392`, Event_F1 `0.9691`, Activation `0.4500`, Energy/frame `4.0960`.

Nhan xet: co the tang len `max_frames=300` cho cung video truoc khi chay representative/full, nhung khong chay neu user chua xac nhan.

## Test1Video-300 G2G3

Command da chay:

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --category baseline --video highway --max-frames 300
```

Output:

- `outputs/full_cdnet2014_official_edge_profile_pc/test1video_summary_300.csv`
- `outputs/full_cdnet2014_official_edge_profile_pc/test1video_summary_300.md`
- `outputs/full_cdnet2014_official_edge_profile_pc/test1video_100_vs_300_comparison.csv`

Ket qua noi bat 300 frames:

- Slowest pipeline: `P3_MOG2` (`111.26s` runtime).
- Fastest pipeline: `P2_FrameDiff` (`89.75 FPS`).
- Highest FMeasure: `P3_MOG2` (`0.9678`).
- Lowest P95 latency: `P2_FrameDiff` (`306.36 ms`).
- Lowest activation: `P2_FrameDiff` (`0.5033`).
- `ONLINE_CALIBRATED`: FMeasure `0.9593`, Event_F1 `0.9899`, Activation `0.7167`, Energy/frame `5.4087`.

Ket luan 300-frame: ket qua on dinh hon 100-frame; `P2_FrameDiff` khong con FMeasure qua thap nhung Event_F1 van thap hon ro, `P3_MOG2` van activation `1.0000`, va `ONLINE_CALIBRATED` van giu loi the activation/energy so voi `P3_MOG2`. Nen chuyen sang representative 6 video neu user xac nhan.

## Representative G2G3

Scope da chay:

- `baseline/highway`
- `baseline/office`
- `dynamicBackground/canoe`
- `cameraJitter/traffic`
- `thermal/library`
- `turbulence/turbulence2`

Output:

- `outputs/full_cdnet2014_official_edge_profile_pc/representative_final_main.csv`
- `outputs/full_cdnet2014_official_edge_profile_pc/representative_edge_profile_summary.csv`
- `outputs/full_cdnet2014_official_edge_profile_pc/representative_per_video_summary.csv`
- `outputs/full_cdnet2014_official_edge_profile_pc/representative_per_category_summary.csv`
- `outputs/full_cdnet2014_official_edge_profile_pc/representative_gain_summary.csv`
- `outputs/full_cdnet2014_official_edge_profile_pc/representative_auto_research_summary.md`

Ket qua representative:

- Best FMeasure: `P3_MOG2` (`0.8536`).
- Best Event_F1: `P3_MOG2` (`0.9323`).
- Fastest: `P2_FrameDiff` (`104.10 FPS`).
- Lowest P95 latency: `P2_FrameDiff` (`261.43 ms`).
- Lowest activation: `P2_FrameDiff` (`0.5511`).
- Lowest Energy/frame: `P2_FrameDiff` (`4.0556`).
- `ASMAG_TR_CONTROLLER`: FMeasure `0.8486`, Event_F1 `0.9149`, Activation `0.7239`, Energy/frame `5.3777`.
- `ONLINE_CALIBRATED`: FMeasure `0.7675`, Event_F1 `0.8948`, Activation `0.6683`, Energy/frame `5.1159`.
- Representative runtime sum: `2194.39s` for 6 videos x 6 pipelines at 300 frames.
- Estimated 53-video run with the same 300-frame cap: `5.38h`.

Ket luan: representative set xac nhan P3_MOG2 la quality leader, category-aware controller gan P3 voi activation/energy thap hon, con `ONLINE_CALIBRATED` giu duoc efficiency advantage nhung mat quality tren turbulence/hard scenes. Nen chay full official-like theo batch nho neu co runtime budget.

## Dieu Kien Hoan Tat G2G3 Full

- Full run plan co 53 video x 6 pipeline = 318 jobs.
- Full official-like target: `completed=318`, `pending=0`, `running=0`, `failed=0`.
- Sau progress monitor upgrade, `run_progress.csv` da duoc normalize theo full official-like uncapped: `completed=0`, `pending=318`, `running=0`, `failed=0`.
- Output chinh can co: `final_main_comparison.csv`, `best_by_metric.csv`, `gain_summary.csv`, `mode_usage_summary.csv`, `auto_research_summary.md`, charts trong `outputs/full_cdnet2014_official_edge_profile_pc/charts`.

## Sau Khi Hoan Tat 9D

`ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED` dung classifier nhe duoc calibrate tu pseudo-label category-aware policy, nhung inference chi dung rolling features va khong dung category label.

Ket qua q2_core_extended:

- `ONLINE_CALIBRATED`: FMeasure `0.4196`, Event_F1 `0.7445`, Activation `0.7163`, Energy/frame `5.2610`, AE_Score `0.4573`.
- So voi `ONLINE_P3TUNED`: FMeasure gain `+0.0085`, Event_F1 gain `+0.0025`, AE_Score gain `+0.0102`.
- So voi `P3_MOG2`: Activation gain `+0.0818`, Energy gain `+0.3504`.
- Hard-category P3_FALLBACK_rate tang tu `0.2207` len `0.6322`.

Ket luan hien tai: `ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED` la online-controller variant tot hon p3tuned ve quality/AE, van tiet kiem activation va energy so voi `P3_MOG2`, nhung efficiency margin nho hon p3tuned.

## Trang Thai Git / Luu Y Lan Sau

Da commit cac moc chinh:

- `39ba931 Complete 9C online controller p3tuned experiment`
- `cb809b5 Add calibrated online controller for ASMAG-TRC`

Khong xoa hoac ghi de cac thu muc output/checkpoint cu, dac biet:

- `outputs/full_cdnet2014_sampled_full_metrics`
- `outputs/full_cdnet2014_controller_sampled_metrics`
- `outputs/q2_core_extended_online_controller_p3tuned`
- `outputs/q2_core_extended_online_controller_calibrated`

Con mot so file khong nam trong commit 9D vi la thay doi ngoai scope hoac output phu. Khong revert neu user chua yeu cau.

## 2026-04-29 G2G3 Run 10 Jobs

- Da resume G2G3 full official-like theo run plan hien tai voi lenh:
  `python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --run-plan configs/full_cdnet2014_official_edge_video_run_plan.csv --max-jobs-per-run 10`
- Truoc khi chay: `completed=7/318`, `pending=311`, `running=0`, `failed=0`.
- Da chay them dung `10` jobs va tat ca deu `completed`.
- Cac job da hoan tat them:
  `badWeather/skating/P2_FrameDiff`,
  `badWeather/skating/P3_MOG2`,
  `badWeather/skating/ASMAG_TR_FAST`,
  `badWeather/skating/ASMAG_TR_CONTROLLER`,
  `badWeather/skating/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED`,
  `badWeather/snowFall/P1_YOLO_Only`,
  `badWeather/snowFall/P2_FrameDiff`,
  `badWeather/snowFall/P3_MOG2`,
  `badWeather/snowFall/ASMAG_TR_FAST`,
  `badWeather/snowFall/ASMAG_TR_CONTROLLER`.
- Sau khi chay: `completed=17/318`, `pending=301`, `running=0`, `failed=0`, overall `5.3459%`.
- Completed videos: `2/53` (`badWeather/blizzard`, `badWeather/skating`).
- Last completed job: `badWeather/snowFall/ASMAG_TR_CONTROLLER`.
- Next pending job: `badWeather/snowFall/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED`.
- Da cap nhat `run_progress.csv`, `daily_progress_report.md`, `experiment_log.md`, `live_progress.json`, `live_progress.md`.
- Khong xoa output/checkpoint completed; khong chay representative/full khac ngoai run plan hien tai; khong thay doi 6 pipeline cot loi.
- Resume tiep theo an toan:
  `python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --run-plan configs/full_cdnet2014_official_edge_video_run_plan.csv --max-jobs-per-run 10`
<!-- G2G3_AUTO_STATUS_START -->
## G2G3 Auto Resume Status

- Updated at: `2026-05-03T17:29:45`
- Event: run completed or paused after selected batch
- Completed: `318 / 318`
- Pending: `0`
- Running: `0`
- Failed: `0`
- Overall progress: `100.0000%`
- Completed videos: `53 / 53`
- Jobs completed this session: `13`
- Last completed job: `turbulence/turbulence3/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED`
- Next pending job: `-`
- Resume command: `python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --run-plan configs/full_cdnet2014_official_edge_video_run_plan.csv --max-jobs-per-run 13`

### Failed Jobs

- None
<!-- G2G3_AUTO_STATUS_END -->

<!-- G2G3_FINAL_STATUS_START -->
## G2G3 Final Official-like Status

- Updated at: `2026-05-03T17:33:21`
- Completed jobs: `318 / 318`
- Pending: `0`
- Running: `0`
- Failed: `0`
- Completed videos: `53 / 53`
- Best CDnet_FMeasure: `ASMAG_TR_CONTROLLER` = `0.5939`
- Best Event_F1: `ASMAG_TR_CONTROLLER` = `0.7114`
- Fastest Avg_FPS: `P2_FrameDiff` = `73.9393`
- Final reports: `outputs/full_cdnet2014_official_edge_profile_pc/final_main_comparison.csv`, `gain_summary.csv`, `auto_research_summary.md`, `charts/`
- Next step: use these artifacts for paper main tables, appendix heatmaps, and limitations discussion.
<!-- G2G3_FINAL_STATUS_END -->
