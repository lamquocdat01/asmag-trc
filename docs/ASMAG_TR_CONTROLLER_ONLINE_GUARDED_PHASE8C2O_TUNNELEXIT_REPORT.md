# ASMAG-TRC Phase 8C-2O TunnelExit Stability Cleanup Report

Date: 2026-05-15

## Scope

Phase 8C-2O is a dry-run-only cleanup for `lowFramerate/tunnelExit_0_35fps`. The change adds tunnelExit FN-risk preservation, a narrow no-detector event-FN rescue, and a post-preservation generic trim while preserving the 8C-2N parking and turbulence2 policies, copyMachine rescue-first ordering, PTZ caps/rescues, cubicle rescue, fountain01 quiet guard, tramCrossroad lowFramerate retighten, continuousPan cap, sparse detector policy, bridgeEntry protection, and final normal-frame suppressor.

No live validation, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched. Accidental 8C-2E live artifacts were left untouched. `ONLINE_CALIBRATED`, P1/P2/P3/FAST/ASMAG_TR_CONTROLLER, and frozen CDnet2014 v1.6 outputs were not modified.

## Files

- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2o_dryrun.yaml`
- Created output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2o_dryrun/`
- Updated controller logic: `src/run_experiment.py`
- Updated compare reporting: `tools/compare_asmag_tr_controller_online_guarded.py`
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2O_TUNNELEXIT_REPORT.md`
- Updated daily status: `docs/DAILY_STATUS.md`

## Implementation

The 2O config inherits from 2N and enables only the tunnelExit cleanup:

```yaml
online_controller_guarded:
  ai_tunnel_exit_lf_preserve_fn_risk_enabled: true
  ai_tunnel_exit_lf_target_video: lowFramerate/tunnelExit_0_35fps
  ai_tunnel_exit_lf_preserve_before_trim: true
  ai_tunnel_exit_lf_allow_detector: false
  ai_tunnel_exit_lf_requires_not_normal_frame: true
  ai_tunnel_exit_lf_event_score_threshold: 0.60
  ai_tunnel_exit_lf_foreground_loss_threshold: 0.45
  ai_tunnel_exit_lf_persistence_threshold: 0.40
  ai_tunnel_exit_lf_recent_memory_min: 1
  ai_tunnel_exit_lf_rescue_enabled: true
  ai_tunnel_exit_lf_rescue_allow_detector: false
  ai_tunnel_exit_lf_rescue_extra_cap_per_video: 6
  ai_tunnel_exit_lf_rescue_cooldown: 1
  ai_tunnel_exit_lf_rescue_requires_not_normal_frame: true
  ai_tunnel_exit_lf_rescue_requires_localized_risk: true
  ai_tunnel_exit_lf_rescue_event_score_threshold: 0.60
  ai_tunnel_exit_lf_rescue_foreground_loss_threshold: 0.45
  ai_tunnel_exit_lf_rescue_prioritize_likely_unprotected_fn: true
  ai_tunnel_exit_lf_post_preservation_trim_enabled: true
  ai_tunnel_exit_lf_post_preservation_trim_max_proposal_rate: 0.30
  ai_tunnel_exit_lf_post_preservation_trim_hard_max_proposal_rate: 0.35
  ai_tunnel_exit_lf_post_preservation_trim_generic_only: true
  ai_tunnel_exit_lf_post_preservation_trim_do_not_trim_preserved_fn_risk: true
  ai_tunnel_exit_lf_post_preservation_trim_do_not_trim_rescue_frames: true
  ai_tunnel_exit_lf_post_preservation_trim_no_detector: true
```

Ordering is preserve/rescue first for `lowFramerate/tunnelExit_0_35fps`: mark likely rescue candidates before the intervention high-risk gate, protect rescue/FN-risk proposals, then trim only generic non-risk proposals if pressure exceeds the post-preservation cap. The final normal-frame suppressor still runs after all proposal paths.

Compare now emits `ai_intervention_2o_tunnel_exit_summary.csv` with tunnelExit proposal/detector/FN, preservation, rescue, post-trim, and accidental protected-frame trim metrics.

## Commands Run

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2o_dryrun.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2o_dryrun
```

The targeted category dry-run was resumed until all 80 jobs completed.

## Aggregate Result

- Jobs: 80/80 completed, 0 failed
- FMeasure: 0.40060
- Event_F1: 0.66904
- Activation: 0.47128
- Avg_FPS: 22.57987
- P95 latency: 418.20077 ms
- Proposed intervention rate: 0.21587
- Detector request rate: 0.01921
- Block-only rate: 0.19666
- Event/foreground block-only rate: 0.15875
- Normal-frame proposals: 0
- Guard alignment: 1.00000

## TunnelExit Comparison

| Phase | Proposal | Detector | Event FN | Unprotected FN |
| --- | ---: | ---: | ---: | ---: |
| 8C-2N | 0.24000 | 0.00000 | 2 | 2 |
| 8C-2O | 0.30000 | 0.00000 | 2 | 1 |

2O improves tunnelExit unprotected event FNs from 2 to 1 while keeping detector requests at 0.00000 and proposal pressure at the 0.30000 target.

## TunnelExit Preserve, Rescue, And Trim Behavior

- Preserved FN-risk candidate frames: 30
- Preserved FN-risk active frames: 30
- Rescue candidate frames: 2
- Rescue active frames: 6
- Rescue no-detector frames: 6
- Rescue protected event-FN frames: 1
- Rescue final-normal suppressions: 0
- Generic post-trim suppressions: 0
- Post-trim active frames: 30
- Post-trim final rate max: 0.30000
- Preserved/rescue frames accidentally trimmed: 0
- Post-trim skipped preserved FN-risk frames: 30
- Post-trim skipped rescue frames: 6

The remaining tunnelExit unprotected FN is raw frame 2485. It was a rescue candidate with active memory and foreground-loss persistence, but it was not rescued because the configured no-detector rescue cap of 6 frames was exhausted. This is acceptable under the 2O gate because proposal and detector gates pass and tunnelExit improves versus 2N, but it misses the preferred FN=0 target.

## Carry-Over Status

| Video | 8C-2N status | 8C-2O status | Result |
| --- | --- | --- | --- |
| `shadow/cubicle` | recall 0.87879, unprotected FN 0 | recall 0.87879, unprotected FN 0 | Pass |
| `nightVideos/bridgeEntry` | event FN 0 | event FN 0 | Pass |
| `PTZ/continuousPan` | proposal/detector 0.05000/0.01000, unprotected FN 0 | proposal/detector 0.05000/0.01000, unprotected FN 0 | Pass |
| `PTZ/intermittentPan` | proposal/detector 0.01000/0.00000, unprotected FN 0 | proposal/detector 0.01000/0.00000, unprotected FN 0 | Pass |
| `shadow/copyMachine` | proposal/detector 0.38000/0.00000, unprotected FN 12 | proposal/detector 0.38000/0.00000, unprotected FN 12 | Pass acceptable, misses preferred |
| `intermittentObjectMotion/parking` | proposal/detector 0.43000/0.00000, unprotected FN 9 | proposal/detector 0.43000/0.00000, unprotected FN 9 | Pass |
| `turbulence/turbulence2` | proposal/detector 0.30000/0.00000, unprotected FN 1 | proposal/detector 0.11000/0.00000, unprotected FN 2 | Pass acceptable, review caveat |
| `lowFramerate/tramCrossroad_1fps` | proposal/detector 0.00000/0.00000 | proposal/detector 0.00000/0.00000 | Pass |
| `lowFramerate/turnpike_0_5fps` | not a 2N risk item | proposal/detector 0.01000/0.00000, unprotected FN 0 | Pass |
| `dynamicBackground/fountain01` | proposal/detector 0.00000/0.00000 | proposal/detector 0.00000/0.00000 | Pass |
| `dynamicBackground/fountain02` | normal-frame false interventions 0 | normal-frame false interventions 0 | Pass |

Turbulence2 remains inside the 2O gate, but it should be reviewed before live because unprotected FN increased from the 2N residual of 1 to 2 in this 2O dry-run.

## Gates

| Gate | Result | Status |
| --- | --- | --- |
| 80/80 completed, 0 failed | 80/80 completed, 0 failed | Pass |
| Aggregate detector request rate < 0.10 | 0.01921 | Pass |
| Aggregate normal-frame proposals = 0 | 0 | Pass |
| Guard alignment >= 0.95 | 1.00000 | Pass |
| Cubicle recall >= 0.80 and unprotected FN = 0 | 0.87879, 0 | Pass |
| BridgeEntry event FN = 0 | 0 | Pass |
| ContinuousPan proposal <= 0.05 | 0.05000 | Pass |
| IntermittentPan proposal <= 0.15 and unprotected FN = 0 | 0.01000, 0 | Pass |
| TramCrossroad_1fps proposal <= 0.05 and detector <= 0.02 | 0.00000, 0.00000 | Pass |
| Fountain01 proposal <= 0.05 and detector <= 0.02 | 0.00000, 0.00000 | Pass |
| Fountain02 normal-frame false interventions = 0 | 0 | Pass |
| CopyMachine unprotected FN <= 15 acceptable | 12 | Pass acceptable |
| Parking proposal <= 0.45 and unprotected FN <= 12 | 0.43000, 9 | Pass |
| Turbulence2 proposal <= 0.35 and unprotected FN <= 2 | 0.11000, 2 | Pass acceptable |
| TunnelExit detector <= 0.02 | 0.00000 | Pass |
| TunnelExit proposal <= 0.35 | 0.30000 | Pass |
| TunnelExit unprotected FN improves versus 2N | 2 -> 1 | Pass |
| TunnelExit preferred unprotected FN = 0 | 1 | Miss preferred |
| TunnelExit acceptable unprotected FN <= 1 if proposal/detector gates pass and root cause documented | 1, cap exhausted at raw frame 2485 | Pass acceptable |
| Hard fail if tunnelExit unprotected FN >= 2 | 1 | Pass |
| No forbidden validation launched | none launched | Pass |

## Conclusion

8C-2O passes the targeted category dry-run gates. Live remains held because this phase was explicitly dry-run-only and because the review should accept the residual tunnelExit FN=1 and the turbulence2 carry-over caveat before any Step 3B targeted category live authorization.
