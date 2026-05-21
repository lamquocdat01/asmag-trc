# ASMAG-TRC Phase 8C-2M3 Parking Post-Preservation Trim Report

Date: 2026-05-15

## Scope

Phase 8C-2M3 is a dry-run-only parking pressure trim on top of 8C-2M2. The patch is scoped to `intermittentObjectMotion/parking` and keeps the 2M2 parking FN-risk preservation and no-detector rescue behavior before applying a generic non-risk post-preservation trim.

No live validation, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched. Accidental 8C-2E live artifacts were left untouched. `ONLINE_CALIBRATED`, P1/P2/P3/FAST/ASMAG_TR_CONTROLLER, and frozen CDnet2014 v1.6 outputs were not modified.

## Files

- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2m3_dryrun.yaml`
- Created output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2m3_dryrun/`
- Updated controller logic: `src/run_experiment.py`
- Updated compare reporting: `tools/compare_asmag_tr_controller_online_guarded.py`
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2M3_PARKING_POST_TRIM_REPORT.md`
- Updated daily status: `docs/DAILY_STATUS.md`

## Implementation

The new post-preservation trim is controlled by:

```yaml
online_controller_guarded:
  ai_parking_iom_post_preservation_trim_enabled: true
  ai_parking_iom_post_preservation_trim_target_video: intermittentObjectMotion/parking
  ai_parking_iom_post_preservation_trim_max_proposal_rate: 0.44
  ai_parking_iom_post_preservation_trim_hard_max_proposal_rate: 0.45
  ai_parking_iom_post_preservation_trim_generic_only: true
  ai_parking_iom_post_preservation_trim_do_not_trim_preserved_fn_risk: true
  ai_parking_iom_post_preservation_trim_do_not_trim_rescue_frames: true
  ai_parking_iom_post_preservation_trim_do_not_trim_likely_unprotected_fn: true
  ai_parking_iom_post_preservation_trim_no_detector: true
  ai_parking_iom_post_preservation_trim_min_trim_frames: 3
  ai_parking_iom_post_preservation_trim_max_trim_frames: 6
```

Execution order is preservation first, no-detector rescue second, protected-frame marking third, and only then generic non-risk trimming. The final normal-frame suppressor still runs after proposal paths.

Added logs:

- `ai_parking_iom_post_preservation_trim_active`
- `ai_parking_iom_post_preservation_trim_reason`
- `ai_parking_iom_post_preservation_trim_rejected_reason`
- `ai_parking_iom_post_preservation_trim_candidate`
- `ai_parking_iom_post_preservation_trim_suppressed_generic_nonrisk`
- `ai_parking_iom_post_preservation_trim_skipped_preserved_fn_risk`
- `ai_parking_iom_post_preservation_trim_skipped_rescue_frame`
- `ai_parking_iom_post_preservation_trim_skipped_likely_unprotected_fn`
- `ai_parking_iom_post_preservation_trim_count`
- `ai_parking_iom_post_preservation_trim_final_rate`

Compare now emits `ai_intervention_2m3_parking_summary.csv` with parking proposal/detector/FN, preservation, rescue, trim, final-rate, and accidental protected-frame trim metrics.

## Commands Run

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2m3_dryrun.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2m3_dryrun
```

The targeted category dry-run was resumed until all jobs completed. A stale dry-run compare process from the first timed-out shell invocation was stopped and the same dry-run compare was rerun to completion.

## Aggregate Result

- Jobs: 80/80 completed, 0 failed
- FMeasure: 0.42369
- Event_F1: 0.66607
- Activation: 0.49428
- Avg_FPS: 23.91514
- P95 latency: 328.76947 ms
- Proposed intervention rate: 0.24065
- Detector request rate: 0.02022
- Block-only rate: 0.22042
- Event/foreground block-only rate: 0.18605
- Normal-frame proposals: 0
- Guard alignment: 1.00000

## Parking Comparison

| Phase | Proposal | Detector | Unprotected FN |
| --- | ---: | ---: | ---: |
| 8C-2L2 | 0.40000 | 0.00000 | 16 |
| 8C-2M | 0.20000 | 0.00000 | 31 |
| 8C-2M2 | 0.48000 | 0.00000 | 9 |
| 8C-2M3 | 0.39000 | 0.00000 | 9 |

2M3 keeps the 2M2 FN protection result while bringing parking proposal pressure below the 0.45 hard gate.

## Parking Trim Behavior

- Preserved FN-risk active frames: 24
- Active no-detector rescue frames: 24
- Rescue protected event-FN frames: 24
- Rescue false-positive activations: 0
- Post-preservation trim active frames: 43
- Trim candidates: 41
- Generic non-risk proposals trimmed: 4
- Trim count max: 4
- Post-preservation final proposal rate: 0.39000
- Existing generic cap suppressions after preservation: 8
- Preserved FN-risk cap skips: 24
- Normal-frame proposed interventions: 0

Safety checks:

- Preserved FN-risk frames skipped by trim: 24
- Rescue frames skipped by trim: 24
- Likely unprotected-FN frames skipped by trim: 24
- Preserved/rescue frames accidentally trimmed: 0

## Carry-Over Status

| Video | 2M2 status | 2M3 status | Result |
| --- | --- | --- | --- |
| `shadow/copyMachine` | proposal/detector 0.38000/0.00000, unprotected FN 12 | proposal/detector 0.38000/0.00000, unprotected FN 12 | Pass |
| `PTZ/intermittentPan` | proposal/detector 0.10000/0.00000, unprotected FN 0 | proposal/detector 0.01000/0.00000, unprotected FN 0 | Pass |
| `PTZ/continuousPan` | proposal/detector 0.04000/0.01000, unprotected FN 0 | reuse-proposal/detector 0.04000/0.01000, block-only proposal 0.05000, unprotected FN 0 | Pass |
| `shadow/cubicle` | recall 0.87879, unprotected FN 0 | recall 0.87879, unprotected FN 0 | Pass |
| `nightVideos/bridgeEntry` | event FN 0 | event FN 0 | Pass |
| `lowFramerate/tramCrossroad_1fps` | proposal/detector 0.00000/0.00000 | proposal/detector 0.00000/0.00000 | Pass |
| `dynamicBackground/fountain01` | proposal/detector 0.00000/0.00000 | proposal/detector 0.00000/0.00000 | Pass |
| `dynamicBackground/fountain02` | normal-frame false interventions 0 | normal-frame false interventions 0 | Pass |

## Remaining Risks

These were intentionally not fixed in 8C-2M3:

- `turbulence/turbulence2`: proposal/detector 0.39000/0.03000, unprotected FN 3
- `lowFramerate/tunnelExit_0_35fps`: proposal/detector 0.28000/0.00000, unprotected FN 1

## Gates

| Gate | Result | Status |
| --- | --- | --- |
| 80/80 completed, 0 failed | 80/80 completed, 0 failed | Pass |
| Aggregate detector request rate < 0.10 | 0.02022 | Pass |
| Aggregate normal-frame proposals = 0 | 0 | Pass |
| Guard alignment >= 0.95 | 1.00000 | Pass |
| Cubicle recall >= 0.80 and unprotected FN = 0 | 0.87879, 0 | Pass |
| BridgeEntry event FN = 0 | 0 | Pass |
| ContinuousPan proposal <= 0.05 | block-only 0.05000 | Pass |
| IntermittentPan proposal <= 0.15 and unprotected FN = 0 | 0.01000, 0 | Pass |
| TramCrossroad_1fps proposal <= 0.05 and detector <= 0.02 | 0.00000, 0.00000 | Pass |
| Fountain01 proposal <= 0.05 and detector <= 0.02 | 0.00000, 0.00000 | Pass |
| Fountain02 normal-frame false interventions = 0 | 0 | Pass |
| CopyMachine unprotected FN <= 15 acceptable, preferred <= 10 | 12 | Pass acceptable, misses preferred |
| CopyMachine detector <= 0.05 | 0.00000 | Pass |
| Parking detector <= 0.02 | 0.00000 | Pass |
| Parking proposal <= 0.45 | 0.39000 | Pass |
| Parking preserved/rescue frames accidentally trimmed = 0 | 0 | Pass |
| Parking unprotected FN <= 12 acceptable, preferred <= 8 | 9 | Pass acceptable, misses preferred |
| Hard fail if parking unprotected FN >= 16 | 9 | Pass |
| No forbidden validation launched | none launched | Pass |

## Conclusion

8C-2M3 passes the targeted category dry-run gates. Live remains held because this phase was explicitly dry-run-only and because `turbulence2` and `tunnelExit_0_35fps` remain monitored risks. The narrowest next dry-run patch should target `turbulence/turbulence2` first because it still has 3 unprotected FNs and elevated proposal/detector pressure; `tunnelExit_0_35fps` remains a smaller follow-up risk with 1 unprotected FN.
