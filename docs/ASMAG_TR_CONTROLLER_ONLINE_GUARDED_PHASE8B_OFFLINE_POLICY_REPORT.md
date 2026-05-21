# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8B Offline Policy Report

Phase 8B is offline research only. No runtime deployment was performed.

## Phase 8A Dataset Recap

- frame rows: 731526
- window rows: 2194578
- teacher label rows: 100
- oracle label rows: 122856
- videos/categories/pipelines: 53 / 11 / 15

## Targets Trained

- `detector_needed`
- `risk_class`
- `unsafe_action`
- `reuse_allowed`
- `lightweight_allowed`
- `detector_floor_needed`
- `action_ranker_high_risk_only`
- `action_ranker_ptz_only`

No direct all-frame `best_action_by_utility` classifier was trained as the main model.

## Splits Used

- `video_grouped` from `split_leave_one_video.csv`
- `category_holdout` from `split_leave_one_category.csv`
- `ptz_holdout` from `split_ptz_holdout.csv`
- `smoke_vs_targeted` from `split_smoke_vs_targeted.csv`

Skipped split/target combinations:
```csv
target,split_name,split_detail,reason,train_rows,test_rows,train_labels,test_labels,train_label_distribution,test_label_distribution
detector_needed,smoke_vs_targeted,direct,train_has_single_label,7743,12257,1.0,2.0,"{""0"": 7743}","{""0"": 11656, ""1"": 601}"
unsafe_action,smoke_vs_targeted,direct,train_has_single_label,7730,12270,1.0,2.0,"{""0"": 7730}","{""0"": 11611, ""1"": 659}"
reuse_allowed,smoke_vs_targeted,direct,train_has_single_label,7753,12247,1.0,2.0,"{""0"": 7753}","{""0"": 11710, ""1"": 537}"
lightweight_allowed,smoke_vs_targeted,direct,train_has_single_label,7746,12254,1.0,2.0,"{""0"": 7746}","{""0"": 11673, ""1"": 581}"
detector_floor_needed,smoke_vs_targeted,direct,train_has_single_label,7733,12267,1.0,2.0,"{""0"": 7733}","{""0"": 11737, ""1"": 530}"
action_ranker_high_risk_only,smoke_vs_targeted,direct,train_has_single_label,5716,14284,1.0,8.0,"{""OTHER"": 5716}","{""CLOSED_EMPTY"": 669, ""DETECT_ACC"": 1436, ""FALLBACK_P3_GUARD"": 643, ""LEGACY_SAFE_P3_GUARD"": 203, ""LIGHTWEIGHT_MASK_ACC"": 1401, ""LIGHTWEIGHT_MASK_P3_FALLBACK"": 745, ""OTHER"": 8195, ""REUSE_ACC"": 992}"
action_ranker_ptz_only,category_holdout,unavailable,too_few_rows,0,0,,,,
action_ranker_ptz_only,ptz_holdout,direct,too_few_rows,0,7792,,,,
action_ranker_ptz_only,smoke_vs_targeted,direct,too_few_rows,0,7792,,,,
```

## Label Imbalance Handling

- Used `class_weight='balanced'` for logistic regression, decision tree, and random forest.
- Used target-aware capped sampling to preserve rare labels.
- Downsampled `OTHER` for high-risk and PTZ action rankers.
- Excluded sparse near-empty features and used robust numeric controller-state features.

## Best Model Per Target

```csv
target,model,mean_accuracy,mean_balanced_accuracy,mean_f1_macro,evaluated_splits
action_ranker_high_risk_only,random_forest,0.7071858605734692,0.5847927330254968,0.47981117539249,3
action_ranker_ptz_only,logistic_regression,0.6850332161000391,0.3524980652312058,0.27988694168445644,1
detector_floor_needed,decision_tree,0.9284436532201538,0.9048175526521488,0.7621645586794062,3
detector_needed,logistic_regression,0.9993896321070235,0.999654493376298,0.9980341190229464,3
lightweight_allowed,random_forest,0.9442835042875366,0.9677107279410286,0.7636083923954793,3
reuse_allowed,logistic_regression,0.9163871600324566,0.9481831970908542,0.6713268367995253,3
risk_class,random_forest,0.8828880347635153,0.8264145086766214,0.8023981277099114,4
unsafe_action,random_forest,0.938319368975227,0.9644201158005575,0.7834534492447401,3
```

## Best Results By Split

```csv
target,split_name,model,accuracy,balanced_accuracy,f1_macro
action_ranker_high_risk_only,category_holdout,random_forest,0.7744585511575803,0.5624133037698651,0.5193888377551303
action_ranker_high_risk_only,ptz_holdout,random_forest,0.5533395176252319,0.492501221048323,0.32338311429346583
action_ranker_high_risk_only,video_grouped,random_forest,0.7937595129375952,0.6994636742583025,0.5966615741288739
action_ranker_ptz_only,video_grouped,logistic_regression,0.6850332161000391,0.3524980652312058,0.27988694168445644
detector_floor_needed,category_holdout,gradient_boosting,0.9941782355575459,0.9970878136200717,0.5652063206770014
detector_floor_needed,ptz_holdout,decision_tree,0.8292181069958847,0.7553159628631327,0.7801135403499484
detector_floor_needed,video_grouped,decision_tree,0.9655172413793104,0.9638409961685823,0.9652651428808255
detector_needed,category_holdout,logistic_regression,1.0,1.0,1.0
detector_needed,ptz_holdout,logistic_regression,0.9991304347826087,0.9994736842105263,0.9984898207351554
detector_needed,video_grouped,logistic_regression,0.9990384615384615,0.9994897959183673,0.9956125363336835
lightweight_allowed,category_holdout,random_forest,0.9777015437392796,0.9888277758679959,0.5722728514315513
lightweight_allowed,ptz_holdout,random_forest,0.8906917164816396,0.9331243469174504,0.8490578198135781
lightweight_allowed,video_grouped,random_forest,0.9644572526416907,0.9811800610376399,0.8694945059413086
reuse_allowed,category_holdout,logistic_regression,0.9727798570942497,0.9862211505339304,0.7298564259058404
reuse_allowed,ptz_holdout,logistic_regression,0.8405215646940822,0.8915276359096584,0.5439407583006562
reuse_allowed,video_grouped,gradient_boosting,0.9961127308066083,0.9979879275653923,0.9719649084568439
risk_class,category_holdout,decision_tree,0.8980582524271845,0.9225746917174314,0.9111582951575938
risk_class,ptz_holdout,random_forest,0.9442922374429223,0.8988328622371258,0.8892050307345963
risk_class,smoke_vs_targeted,random_forest,0.7874138496882179,0.549950510272562,0.4968488903778132
risk_class,video_grouped,logistic_regression,0.9166666666666666,0.9556470050297211,0.9266960321858974
unsafe_action,category_holdout,random_forest,0.9746835443037974,0.9872633390705681,0.6571858754913148
unsafe_action,ptz_holdout,random_forest,0.8731884057971014,0.9235953520164046,0.803321745061411
unsafe_action,video_grouped,decision_tree,0.9670861568247822,0.9824016563146998,0.8898527271814943
```

## Detector-Needed Result

`detector_needed` remains the strongest target and is suitable for Phase 8C shadow-mode observation, not runtime control.

## Risk-Class Result

`risk_class` is learnable across held-out splits, with strongest category-holdout performance from the best split-level model listed above.

## Unsafe-Action Result

`unsafe_action` improves over majority baselines but is still imperfect. Deterministic guards must remain authoritative.

## Reuse/Lightweight Allowed Result

`reuse_allowed` and `lightweight_allowed` provide useful offline signals, but they should be interpreted as advisory labels until shadow-mode validation measures false negatives directly.

## PTZ Holdout Result

```csv
target,split_name,split_detail,model,train_rows,test_rows,train_labels,test_labels,majority_class,leakage_ok,accuracy,balanced_accuracy,f1_macro
detector_needed,ptz_holdout,direct,majority_baseline,18850,1150,2,2,0,True,0.8260869565217391,0.5,0.4523809523809524
detector_needed,ptz_holdout,direct,logistic_regression,18850,1150,2,2,,True,0.9991304347826087,0.9994736842105263,0.9984898207351554
detector_needed,ptz_holdout,direct,decision_tree,18850,1150,2,2,,True,0.9947826086956522,0.985,0.9908118098870251
detector_needed,ptz_holdout,direct,random_forest,18850,1150,2,2,,True,0.9956521739130435,0.9875,0.9923585501179442
detector_needed,ptz_holdout,direct,gradient_boosting,18850,1150,2,2,,True,0.9956521739130435,0.9875,0.9923585501179442
risk_class,ptz_holdout,direct,majority_baseline,18905,1095,3,3,medium,True,0.8182648401826484,0.3333333333333333,0.3000167420056923
risk_class,ptz_holdout,direct,logistic_regression,18905,1095,3,3,,True,0.7899543378995434,0.8386789151680615,0.7354449697316904
risk_class,ptz_holdout,direct,decision_tree,18905,1095,3,3,,True,0.8383561643835616,0.8743313772330703,0.756026916415871
risk_class,ptz_holdout,direct,random_forest,18905,1095,3,3,,True,0.9442922374429223,0.8988328622371258,0.8892050307345963
risk_class,ptz_holdout,direct,gradient_boosting,18905,1095,3,3,,True,0.9342465753424658,0.8551490444536767,0.8628893975724341
unsafe_action,ptz_holdout,direct,majority_baseline,18896,1104,2,2,0,True,0.8605072463768116,0.5,0.4625121713729309
unsafe_action,ptz_holdout,direct,logistic_regression,18896,1104,2,2,,True,0.8623188405797102,0.9036773752563226,0.7871753246753247
unsafe_action,ptz_holdout,direct,decision_tree,18896,1104,2,2,,True,0.875,0.9137662337662338,0.8028040673473191
unsafe_action,ptz_holdout,direct,random_forest,18896,1104,2,2,,True,0.8731884057971014,0.9235953520164046,0.803321745061411
unsafe_action,ptz_holdout,direct,gradient_boosting,18896,1104,2,2,,True,0.8940217391304348,0.6799794941900205,0.7214135510239295
reuse_allowed,ptz_holdout,direct,majority_baseline,19003,997,2,2,0,True,0.9819458375125376,0.5,0.49544534412955465
reuse_allowed,ptz_holdout,direct,logistic_regression,19003,997,2,2,,True,0.8405215646940822,0.8915276359096584,0.5439407583006562
reuse_allowed,ptz_holdout,direct,decision_tree,19003,997,2,2,,True,0.8756268806419257,0.7730677562138236,0.5474949489033996
reuse_allowed,ptz_holdout,direct,random_forest,19003,997,2,2,,True,0.8696088264794383,0.7700034048348655,0.5425959909655562
reuse_allowed,ptz_holdout,direct,gradient_boosting,19003,997,2,2,,True,0.970912738214644,0.6852513903075701,0.6553586115647313
lightweight_allowed,ptz_holdout,direct,majority_baseline,18829,1171,2,2,0,True,0.8172502134927413,0.5,0.44971804511278196
lightweight_allowed,ptz_holdout,direct,logistic_regression,18829,1171,2,2,,True,0.8727583262169086,0.9003847693825136,0.8236369131431078
lightweight_allowed,ptz_holdout,direct,decision_tree,18829,1171,2,2,,True,0.888129803586678,0.9315569487983282,0.8460906373752505
lightweight_allowed,ptz_holdout,direct,random_forest,18829,1171,2,2,,True,0.8906917164816396,0.9331243469174504,0.8490578198135781
lightweight_allowed,ptz_holdout,direct,gradient_boosting,18829,1171,2,2,,True,0.8958155422715628,0.7457909745212356,0.7901187048245872
detector_floor_needed,ptz_holdout,direct,majority_baseline,18542,1458,2,2,0,True,0.654320987654321,0.5,0.39552238805970147
detector_floor_needed,ptz_holdout,direct,logistic_regression,18542,1458,2,2,,True,0.678326474622771,0.5379979035639413,0.47671111063494703
detector_floor_needed,ptz_holdout,direct,decision_tree,18542,1458,2,2,,True,0.8292181069958847,0.7553159628631327,0.7801135403499484
detector_floor_needed,ptz_holdout,direct,random_forest,18542,1458,2,2,,True,0.7050754458161865,0.5748165618448637,0.5396537747597453
detector_floor_needed,ptz_holdout,direct,gradient_boosting,18542,1458,2,2,,True,0.663923182441701,0.5152927523210542,0.4300179989277234
action_ranker_high_risk_only,ptz_holdout,direct,majority_baseline,17844,2156,8,7,OTHER,True,0.36178107606679033,0.14285714285714285,0.0759050214091086
action_ranker_high_risk_only,ptz_holdout,direct,logistic_regression,17844,2156,8,7,,True,0.5250463821892394,0.4919427478923084,0.30918961195296113
action_ranker_high_risk_only,ptz_holdout,direct,decision_tree,17844,2156,8,7,,True,0.5477736549165121,0.47650575824013913,0.3177523833820381
action_ranker_high_risk_only,ptz_holdout,direct,random_forest,17844,2156,8,7,,True,0.5533395176252319,0.492501221048323,0.32338311429346583
action_ranker_high_risk_only,ptz_holdout,direct,gradient_boosting,17844,2156,8,7,,True,0.5524118738404453,0.4748335895183455,0.31278161471499405
```

## Smoke-Vs-Targeted Result

```csv
target,split_name,split_detail,model,train_rows,test_rows,train_labels,test_labels,majority_class,leakage_ok,accuracy,balanced_accuracy,f1_macro
risk_class,smoke_vs_targeted,direct,majority_baseline,7812,12188,2,3,medium,True,0.7701837873318018,0.3333333333333333,0.2900579374275782
risk_class,smoke_vs_targeted,direct,logistic_regression,7812,12188,2,3,,True,0.580735149327207,0.4865747150084297,0.3789163125077981
risk_class,smoke_vs_targeted,direct,decision_tree,7812,12188,2,3,,True,0.7701837873318018,0.5461210969992155,0.48534526788524374
risk_class,smoke_vs_targeted,direct,random_forest,7812,12188,2,3,,True,0.7874138496882179,0.549950510272562,0.4968488903778132
risk_class,smoke_vs_targeted,direct,gradient_boosting,7812,12188,2,3,,True,0.7634558582212012,0.41646621063067163,0.4127103115905515
```

## Offline Utility Gain

```csv
target,model,offline_utility_gain_mean,offline_utility_gain_median,unsafe_action_avoidance_rate,detector_needed_recall,reuse_unsafe_false_negative_rate,ptz_high_risk_recall
action_ranker_high_risk_only,random_forest,0.0004791656795143358,0.0,0.20665083135391923,0.9748953974895398,1.0,
action_ranker_ptz_only,logistic_regression,0.05150568301769463,0.04380455369554437,0.8008048289738431,0.9,0.10204081632653061,0.4069965870307167
detector_floor_needed,gradient_boosting,0.03912539306770595,0.017017324765523312,0.25,0.8571428571428571,0.0,
detector_needed,logistic_regression,0.044030620990394405,0.02563935594089172,0.0,1.0,,
lightweight_allowed,random_forest,0.04326499516448793,0.02597371812986675,1.0,0.0,,
reuse_allowed,gradient_boosting,0.00461735756497254,0.0,0.35714285714285715,0.0,1.0,
risk_class,logistic_regression,0.0012401635926200369,0.0,0.9805825242718447,1.0,0.0,
unsafe_action,random_forest,0.043155021540220356,0.026293596390161336,1.0,1.0,,
```

## Failure Cases

- `best_safe_action` remains imbalanced toward `OTHER`, so rankers are trained only on high-risk/PTZ subsets with OTHER downsampling.
- `unsafe_action` is learnable but imperfect; false negatives remain unacceptable for runtime authority.
- Some diagnostic columns from Phase 8A have near-100% missingness and are excluded from training.
- Offline utility gain is estimated from logged action utilities, not from a live counterfactual run.

## Phase 8C Readiness

Phase 8B is strong enough to proceed to Phase 8C shadow-mode logging and comparison. It is not strong enough for runtime deployment. Phase 8C should run learned-policy predictions side by side with the deterministic guarded controller, log disagreements, and require explicit safety thresholds before any integration discussion.

Explicit deployment statement: no learned model is deployed into the runtime pipeline yet.
