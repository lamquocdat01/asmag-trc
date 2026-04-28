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

## Output Folders Quan Trong

- `outputs/full_cdnet2014_sampled_full_metrics`
- `outputs/full_cdnet2014_controller_sampled_metrics`
- `outputs/q2_core_extended_online_controller_p3tuned`

## Buoc Dang Lam

- Current task: G1 - Finish 9C-Fix completed
- Current config: `configs/q2_core_extended_online_controller_p3tuned.yaml`
- Current output: `outputs/q2_core_extended_online_controller_p3tuned`
- Progress hien tai: `completed=128`, `pending=0`, `running=0`, `failed=0`
- Current job: `-`

## Lenh Resume Hien Tai

```bat
python src/run_experiment.py --config configs/q2_core_extended_online_controller_p3tuned.yaml
```

## Dieu Kien Hoan Tat

- completed = 128
- pending = 0
- running = 0
- failed = 0

## Sau Khi Hoan Tat 9C-Fix

Thanh cong. Cac file cuoi da tao trong `outputs/q2_core_extended_online_controller_p3tuned`:

- `final_main_comparison.csv`
- `best_by_metric.csv`
- `gain_summary.csv`
- `mode_usage_summary.csv`
- `scene_difficulty_distribution.csv`
- `category_wise_mode_usage.csv`
- `summary_pareto_metrics.csv`
- `auto_research_summary.md`

Ket luan hien tai: `ASMAG_TR_CONTROLLER_ONLINE_P3TUNED` la bien the 9C-Fix huu ich, nhung chua nen dua lam headline result vi FMeasure/AE_Score van thap hon `P3_MOG2` va `ASMAG_TR_CONTROLLER`.
