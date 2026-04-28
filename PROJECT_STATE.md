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
- Current phase: Setup + Smoke Test completed; waiting for user confirmation before `G2G3-Test1Video`.
- Progress hien tai: `completed=1`, `pending=317`, `running=0`, `failed=0`
- Current job: `-`
- Latest commits: `39ba931` for 9C p3tuned, `cb809b5` for 9D calibrated.

## Lenh Resume Chinh

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --run-plan configs/full_cdnet2014_official_edge_video_run_plan.csv --max-videos-per-run 1
```

## Lenh Chay Qua Dem

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --run-plan configs/full_cdnet2014_official_edge_video_run_plan.csv --max-videos-per-run 10
```

## Lenh Check Progress Khong Chay

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --progress-only
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

## Dieu Kien Hoan Tat G2G3 Full

- Full run plan co 53 video x 6 pipeline = 318 jobs.
- Full official-like target: `completed=318`, `pending=0`, `running=0`, `failed=0`.
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
