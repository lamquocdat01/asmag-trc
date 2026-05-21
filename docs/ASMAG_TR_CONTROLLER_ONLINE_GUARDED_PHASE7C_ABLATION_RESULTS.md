# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 7C Ablation Results

Generated summaries:

- `outputs/asmag_tr_controller_online_guarded_ablation_phase7c/phase7c_ablation_summary.csv`
- `outputs/asmag_tr_controller_online_guarded_ablation_phase7c/continuousPan_ablation_summary.csv`
- `outputs/asmag_tr_controller_online_guarded_ablation_phase7c/twoPosition_ablation_summary.csv`
- `outputs/asmag_tr_controller_online_guarded_ablation_phase7c/nonptz_safety_summary.csv`
- `outputs/asmag_tr_controller_online_guarded_ablation_phase7c/phase7c_ablation_report.md`

Smoke-only ablations were executed for all Phase 7C policies. No policy satisfied the Phase 7D promotion criteria.

Best observed continuousPan policy:

- `CP_ANCHOR_EVERY_1`
- FMeasure `0.2611`, Event_F1 `0.2906`, FPS `2.80`, P95 `455.57 ms`
- closed-empty rate `0.00`
- action mix: `FALLBACK_P3_GUARD:0.770;FALLBACK_P3_POLICY:0.230`

Best observed twoPosition policy:

- `TP_PHASE6C_ONLY`
- FMeasure `0.7955`, Event_F1 `0.7925`, FPS `11.90`, P95 `285.39 ms`

Non-PTZ safety:

- `TP_BURST_2_THEN_FAST`, `TP_BURST_3_THEN_FAST`, and `TP_PHASE6C_ONLY` suppress cubicle/non-PTZ teacher behavior to `0.00`.
- `NONPTZ_TEACHER_OFF` reduced but did not eliminate logged non-PTZ teacher behavior in this smoke run (`non_ptz_teacher_behavior_rate = 0.055`), because the policy is limited to the configured non-PTZ suppression signature.
- All policies kept `bridgeEntry_closed_empty_event_fn = 0`.

Decision:

- No causal action schedule exists yet for Phase 7D promotion.
- Recommended Phase 7D production policy: `NONE`; keep production guarded behavior unchanged.
- PTZ-targeted remains disallowed until Phase 7D is implemented and smoke passes.
