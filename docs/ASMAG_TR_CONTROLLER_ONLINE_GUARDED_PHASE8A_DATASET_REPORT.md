# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8A Dataset Report

Phase 8A is research-only. No experiment runner was launched and no production pipeline behavior was modified.

## Dataset Size

- frame rows: 731526
- window rows: 2194578
- teacher label rows: 100
- oracle label rows: 122856
- inventory rows: 543
- videos: 53
- categories: 11
- pipelines: 15

## Label Distributions

### Action Bucket
```csv
label,count
OTHER,722332
DETECT_ACC,2940
REUSE_ACC,1496
CLOSED_EMPTY,1397
LIGHTWEIGHT_MASK_P3_FALLBACK,1020
FALLBACK_P3_GUARD,1015
LIGHTWEIGHT_MASK_ACC,928
LEGACY_SAFE_P3_GUARD,398
```

### Risk Class
```csv
label,count
medium,609827
low,119063
unsafe,2636
```

### Oracle Best Action
```csv
label,count
OTHER,121258
DETECT_ACC,349
REUSE_ACC,342
LIGHTWEIGHT_MASK_P3_FALLBACK,329
LIGHTWEIGHT_MASK_ACC,315
FALLBACK_P3_GUARD,113
CLOSED_EMPTY,103
LEGACY_SAFE_P3_GUARD,47
```

## Missing Feature Report

Top missing columns:
```csv
column,missing_rate
motion_comp_trust_band_reason,1.0
zoom_scale_reason,1.0
continuous_pan_trust_relaxation_reason,1.0
geometry_trust_band,1.0
continuous_pan_lightweight_acc_block_reason,1.0
low_framerate_cadence_guard_reason,1.0
teacher_ranker_trust_state,1.0
motion_comp_trust_band,1.0
continuous_pan_inter_anchor_action,0.999993164972947
continuous_pan_geometry_inter_anchor_action,0.999993164972947
continuous_pan_reuse_block_reason,0.999993164972947
continuous_pan_reuse_replacement_action,0.999993164972947
continuous_pan_teacher_anchor_action,0.9999876969513045
ptz_cadence_thinning_reason,0.9999644578593242
continuous_pan_teacher_inter_anchor_action,0.9999589898376817
ptz_detector_floor_reason,0.9999521548106287
closed_empty_replacement_quality,0.9999384847565227
ptz_closed_empty_kill_reason,0.9999384847565227
closed_empty_replacement_source,0.9999384847565227
closed_empty_replacement_action,0.9999384847565227
```

## Unsafe Action Distribution
```csv
label,count
,728890
closed_empty_during_event_or_motion,1268
reuse_under_low_trust,917
lightweight_p3_under_ptz,429
legacy_safe_without_detector_cadence,22
```

## PTZ Samples
- PTZ frame rows: 37404
- PTZ videos: 4

## Non-PTZ Samples
- non-PTZ frame rows: 694122
- non-PTZ videos: 49

## Leakage Checks
- leave-one-video train/test video-disjoint: True
- `split_smoke_vs_targeted.csv` holds out any video that appears in targeted, across all datasets, to avoid same-video leakage.

## Utility Sanity Checks
```csv
action_bucket,count,mean,median
CLOSED_EMPTY,1397,0.16009777240505446,0.17316612884441385
DETECT_ACC,2940,0.48011444128340125,0.34418843097230295
FALLBACK_P3_GUARD,1015,0.3192464222840768,0.15450969600077696
LEGACY_SAFE_P3_GUARD,398,0.5463178214634307,0.43769388217456273
LIGHTWEIGHT_MASK_ACC,928,0.6331387786668368,0.7250902877013943
LIGHTWEIGHT_MASK_P3_FALLBACK,1020,0.29353245840584063,0.2033105582407076
OTHER,722332,0.39634914573759145,0.19388701517706575
REUSE_ACC,1496,0.3019346994383589,0.23231398020035182
```

## Teacher Label Summary
```csv
label,count
P3_MOG2,42
ASMAG_TR_CONTROLLER,38
ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED,7
ASMAG_TR_CONTROLLER_ONLINE_GUARDED,5
CP_ANCHOR_EVERY_1,4
ONLINE_CALIBRATED,2
TP_PHASE6C_ONLY,1
CP_ANCHOR_EVERY_2,1
```

## Oracle Label Summary
```csv
label,count
OTHER,121457
DETECT_ACC,379
LIGHTWEIGHT_MASK_ACC,319
REUSE_ACC,289
LIGHTWEIGHT_MASK_P3_FALLBACK,161
FALLBACK_P3_GUARD,115
CLOSED_EMPTY,89
LEGACY_SAFE_P3_GUARD,47
```

## Baseline Model Probe

The probe is research-only and uses a target-aware 10,000-row sample from `frame_state_dataset.parquet` joined with `oracle_action_dataset.parquet`. It evaluates majority baseline, logistic regression, decision tree, random forest, and gradient boosting on video-grouped and category-holdout splits.

Outputs:

- `outputs/phase8a_policy_dataset/model_probe_results.csv`
- `outputs/phase8a_policy_dataset/policy_feature_importance.csv`
- `outputs/phase8a_policy_dataset/policy_rule_candidates.txt`

Best observed probe results by target:

```csv
target,split_name,best_model,accuracy,balanced_accuracy,f1_macro
best_action_by_utility,video_grouped,gradient_boosting,0.7407407407407407,0.5249024751143395,0.429010989010989
best_action_by_utility,category_holdout,gradient_boosting,0.5848670756646217,0.4924817777932245,0.4296198828418556
risk_class,video_grouped,decision_tree/logistic_regression/gradient_boosting,0.9629629629629629,0.6563573883161512,0.6597222222222222
risk_class,category_holdout,gradient_boosting,0.9488752556237219,0.9045225677676904,0.8795198360415751
unsafe_action,video_grouped,decision_tree/random_forest/gradient_boosting,0.8425925925925926,0.6851851851851851,0.7227842367507172
unsafe_action,category_holdout,logistic_regression,0.7842535787321063,0.6806758461215052,0.696915220331963
detector_needed,video_grouped,decision_tree/logistic_regression/random_forest/gradient_boosting,1.0,1.0,1.0
detector_needed,category_holdout,random_forest,0.9887525562372188,0.9828660436137071,0.9871327333074187
```

Interpretation:

- `detector_needed` is easy to recover from logged controller state features.
- `risk_class` is learnable in this offline probe, including under PTZ/category holdout.
- `unsafe_action` is learnable but remains imperfect, so deterministic safety guards should remain primary.
- `best_action_by_utility` is harder and imbalanced toward `OTHER`; Phase 8B should treat this as a ranking/reweighting problem, not a deployable direct classifier.

## Phase 8B Readiness

The dataset is good enough for Phase 8B research probes and offline policy learning experiments. It is not good enough for deployment. Labels mix observational baselines, ablation outputs, and derived utilities, and the strongest probe target (`detector_needed`) is not the same as a complete action policy. Any Phase 8B learned model must remain behind deterministic safety guards and be validated separately before runtime integration.

Deployment recommendation: do not deploy a learned policy from Phase 8A artifacts alone.
