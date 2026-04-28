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
