# ASMAG-TRC Phase 8C-2Q2 Targeted Category Retry Freeze

Date: 2026-05-16

## Executive Summary

Phase 8C-2Q2 is frozen as the current targeted category Step 3B live-retry candidate. This freeze is based on the completed 2Q2 targeted category dry-run: 80/80 jobs completed, 0 failed, normal-frame proposals remained 0, guard alignment stayed 1.00000, detector requests stayed sparse, and all targeted carry-over gates passed.

This document is an audit and consolidation artifact only. No experiment, live validation, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched for this freeze step.

## Why 2Q2 Is The Current Live-Retry Candidate

8C-2Q2 is the strongest current targeted category live-retry candidate because it preserves the successful 2Q live-sensitive reserves for `shadow/copyMachine` and `intermittentObjectMotion/parking` while restoring the turbulence2 carry-over gate that failed in 2Q.

The candidate has the live-retry properties the Step 3B audit asked for:

- Detector request rate remains low: 0.01163 aggregate, 0.00000 on copyMachine, parking, turbulence2, and tunnelExit.
- Normal-frame proposals remain 0.
- The four Step 3B live failure groups now have dry-run protection in place: cubicle, intermittentPan, copyMachine, and parking.
- The 2Q turbulence2 regression is fixed: unprotected FN improves from 3 in 2Q to 0 in 2Q2.
- Core guard carry-over remains intact for PTZ, lowFramerate, dynamicBackground, bridgeEntry, tunnelExit, and turbulence2.

## Phase Lineage

| Phase | Result | Role In Retry Readiness |
| --- | --- | --- |
| 8C-2O | Passed targeted category dry-run | Established tunnelExit preserve/rescue/trim and an accepted targeted dry-run baseline. |
| Step 3B live | Failed targeted category live gates | Live completed technically, but live-sensitive FN gaps appeared in cubicle, intermittentPan, copyMachine, and parking. |
| Step 3B audit | Found localized live-sensitive FN gaps | Classified failures as cap exhaustion, dry-run/live final-action mismatch, threshold, and candidate-context gaps. Full CDnet remained held. |
| 8C-2P | Fixed cubicle/intermittentPan mismatch group in dry-run | Added exact live mismatch protections for cubicle and intermittentPan while preserving core gates. |
| 8C-2Q | Fixed copyMachine/parking in dry-run but regressed turbulence2 | copyMachine and parking improved materially, but turbulence2 unprotected FN regressed to 3. Live remained held. |
| 8C-2Q2 | Restored turbulence2 and passed all targeted dry-run gates | Added exact no-detector turbulence2 carry-over reserve for rescue-cap-exhausted frames. Current live-retry candidate. |

## Aggregate 2Q2 Metrics

| Metric | 8C-2Q2 dry-run |
| --- | ---: |
| Jobs completed / failed | 80 / 0 |
| FMeasure | 0.43068 |
| Event_F1 | 0.66657 |
| Activation | 0.57292 |
| Avg_FPS | 28.34227 |
| P95 latency | 227.01209 ms |
| Proposal rate | 0.21335 |
| Detector request rate | 0.01163 |
| Block-only rate | 0.20172 |
| Event/foreground block-only rate | 0.16481 |
| Normal-frame proposals | 0 |
| Guard alignment | 1.00000 |

## Per-Video Gate Table

| Video | 2Q2 result | Gate status |
| --- | --- | --- |
| `shadow/cubicle` | recall 0.90909, unprotected FN 0 | Pass |
| `PTZ/intermittentPan` | proposal 0.01000, unprotected FN 0 | Pass |
| `PTZ/continuousPan` | proposal 0.04000 | Pass |
| `nightVideos/bridgeEntry` | event FN 0 | Pass |
| `lowFramerate/tramCrossroad_1fps` | proposal/detector 0.00000/0.00000 | Pass |
| `dynamicBackground/fountain01` | proposal/detector 0.00000/0.00000 | Pass |
| `dynamicBackground/fountain02` | normal-frame false interventions 0 | Pass |
| `shadow/copyMachine` | proposal 0.46000, detector 0.00000, unprotected FN 4 | Pass acceptable |
| `intermittentObjectMotion/parking` | proposal 0.45000, detector 0.00000, unprotected FN 5 | Pass acceptable |
| `turbulence/turbulence2` | proposal 0.31000, detector 0.00000, unprotected FN 0 | Pass preferred |
| `lowFramerate/tunnelExit_0_35fps` | proposal 0.31000, unprotected FN 1 | Pass acceptable |

## Residual Watchlist

These residuals are acceptable for the targeted category live retry, but they must be monitored closely during the live retry review:

| Video | Residual | Live retry watch item |
| --- | --- | --- |
| `shadow/copyMachine` | proposal 0.46000, unprotected FN 4 | Watch for live cap exhaustion recurrence and detector remaining 0.00000 to <= 0.02000. |
| `intermittentObjectMotion/parking` | proposal 0.45000, unprotected FN 5 | Watch for live-sensitive burst gaps and ensure unprotected FN remains <= 12. |
| `lowFramerate/tunnelExit_0_35fps` | unprotected FN 1 | Watch the accepted residual; gate remains proposal <= 0.35 and unprotected FN <= 1. |

## Safety Audit

- This freeze step launched no experiments.
- No live validation was run.
- No live compare was run.
- No full CDnet validation was run.
- No PTZ-targeted standalone validation was run.
- No LASIESTA, SBI2015, BMC, or cross-dataset validation was run.
- Accidental 8C-2E live artifacts were excluded from this decision and were not deleted or overwritten.
- No previous outputs were overwritten by this freeze step.
- Controller code was not modified in this freeze step.
- The default guarded config remains unchanged with `ai_intervention_enabled: false`.

Evidence reviewed:

- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2Q2_TURBULENCE_CARRYOVER_REPORT.md`
- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2Q_LIVE_CAP_RESERVE_REPORT.md`
- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP3B_LIVE_FAILURE_AUDIT.md`
- Existing output root `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2q2_dryrun/`

## Freeze Decision

8C-2Q2 is frozen as the targeted category Step 3B live-retry candidate.

This freeze does not mark 8C-2Q2 as a full CDnet success. Full CDnet remains held. The next validation step is limited to a Step 3B targeted category live retry, and only after explicit authorization.

## Recommended Next Step

Proceed next with Step 3B targeted category live retry using the 2Q2 policy stack after explicit authorization.

Do not start full CDnet until targeted category live passes and the live residuals are reviewed.

## Step 3B Targeted Category Live Retry Result

The authorized 8C-2Q2 targeted category live retry was run after this freeze. It used the separate config `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2q2_live.yaml` and output root `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2q2_live/`.

The run completed technically: 80/80 jobs completed, 0 failed. Live compare was run only on the 2Q2 live output root. No full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, or PTZ-targeted standalone validation was launched.

The live retry does not pass Step 3B gates because `intermittentObjectMotion/parking` reached proposal/intervention 0.50000, above the live gate of <= 0.45000. All other requested live gates passed.

### Aggregate Dry-Run Versus Live

| Metric | 2Q2 dry-run | 2Q2 live |
| --- | ---: | ---: |
| Jobs completed / failed | 80 / 0 | 80 / 0 |
| FMeasure | 0.43068 | 0.44351 |
| Event_F1 | 0.66657 | 0.67449 |
| Activation | 0.57292 | 0.58678 |
| Avg_FPS | 28.34227 | 24.60626 |
| P95 latency | 227.01209 ms | 231.79742 ms |
| Proposal/intervention rate | 0.21335 | 0.20677 |
| Detector request rate | 0.01163 | 0.01062 |
| Block-only rate | 0.20172 | 0.19616 |
| Event/foreground block-only rate | 0.16481 | 0.15824 |
| Normal-frame proposals/interventions | 0 | 0 |
| Guard alignment | 1.00000 | 1.00000 |

### Live Per-Video Risk Summary

| Video | Live risk summary |
| --- | --- |
| `PTZ/continuousPan` | intervention 0.05000, detector 0.01000, unprotected FN 0 |
| `PTZ/intermittentPan` | intervention 0.01000, detector 0.00000, unprotected FN 0 |
| `baseline/highway` | intervention 0.03000, detector 0.00000, unprotected FN 0 |
| `baseline/office` | intervention 0.03000, detector 0.00000, unprotected FN 0 |
| `cameraJitter/traffic` | intervention 0.02000, detector 0.00000, unprotected FN 0 |
| `dynamicBackground/canoe` | intervention 0.00000, detector 0.00000, unprotected FN 0 |
| `dynamicBackground/fountain01` | intervention 0.00000, detector 0.00000, unprotected FN 0 |
| `dynamicBackground/fountain02` | intervention 0.40000, detector 0.01000, normal-frame false interventions 0 |
| `dynamicBackground/overpass` | intervention 0.29000, detector 0.01000, unprotected FN 0 |
| `intermittentObjectMotion/parking` | intervention 0.50000, detector 0.00000, event FN 10, protected FN 6, unprotected FN 4 |
| `lowFramerate/tramCrossroad_1fps` | intervention 0.00000, detector 0.00000, unprotected FN 0 |
| `lowFramerate/tunnelExit_0_35fps` | intervention 0.30000, detector 0.00000, event FN 2, protected FN 1, unprotected FN 1 |
| `lowFramerate/turnpike_0_5fps` | intervention 0.01000, detector 0.00000, unprotected FN 0 |
| `nightVideos/bridgeEntry` | intervention 0.15000, detector 0.04000, event FN 0 |
| `nightVideos/streetCornerAtNight` | intervention 0.12000, detector 0.01000, unprotected FN 0 |
| `nightVideos/tramStation` | intervention 0.19000, detector 0.04000, unprotected FN 0 |
| `shadow/backdoor` | intervention 0.33000, detector 0.07000, unprotected FN 0 |
| `shadow/copyMachine` | intervention 0.46000, detector 0.00000, event FN 8, protected FN 4, unprotected FN 4 |
| `shadow/cubicle` | recall 0.89899, detector 0.02000, unprotected FN 0 |
| `turbulence/turbulence2` | intervention 0.31000, detector 0.00000, event FN 2, protected FN 2, unprotected FN 0 |

### Live Gate Table

| Gate | Live result | Status |
| --- | --- | --- |
| 80/80 completed, 0 failed | 80/80, 0 failed | Pass |
| Aggregate detector request rate < 0.10 | 0.01062 | Pass |
| Normal-frame interventions = 0 | 0 | Pass |
| Guard alignment >= 0.95 | 1.00000 | Pass |
| Cubicle recall >= 0.80 and unprotected FN = 0 | recall 0.89899, unprotected FN 0 | Pass |
| BridgeEntry event FN = 0 | 0 | Pass |
| ContinuousPan intervention <= 0.05 | 0.05000 | Pass |
| IntermittentPan intervention <= 0.15 and unprotected FN = 0 | 0.01000, unprotected FN 0 | Pass |
| TramCrossroad_1fps intervention <= 0.05 and detector <= 0.02 | 0.00000 / 0.00000 | Pass |
| Fountain01 intervention <= 0.05 and detector <= 0.02 | 0.00000 / 0.00000 | Pass |
| Fountain02 normal-frame false interventions = 0 | 0 | Pass |
| CopyMachine unprotected FN <= 15 | 4 | Pass |
| Parking intervention <= 0.45 and unprotected FN <= 12 | intervention 0.50000, unprotected FN 4 | Fail |
| Turbulence2 intervention <= 0.35 and unprotected FN <= 2 | 0.31000, unprotected FN 0 | Pass |
| TunnelExit_0_35fps intervention <= 0.35 and unprotected FN <= 1 | 0.30000, unprotected FN 1 | Pass |
| No broad detector-heavy behavior | aggregate detector 0.01062 | Pass |
| No forbidden validation launched | confirmed | Pass |

### Live Root Cause

`intermittentObjectMotion/parking` improved FN protection live but exceeded the proposal cap:

- Dry-run parking: proposal 0.45000, detector 0.00000, event FN 33, protected FN 28, unprotected FN 5.
- Live parking: proposal 0.50000, detector 0.00000, event FN 10, protected FN 6, unprotected FN 4.
- Parking live reserve stayed no-detector and used 8 reserve activations.
- Parking post-preservation trim reached `post_trim_final_rate_max` 0.50000 live versus 0.45000 dry-run.
- Live preserved/protected parking context caused more frames to be retained by the live reserve/cap path than the live gate allows.

The next fix should be narrow and parking-only: retighten the parking live post-preservation trim or cap accounting so live parking intervention returns to <= 0.45000 while preserving no-detector behavior and keeping unprotected FN <= 12. Do not broaden detector policy and do not touch copyMachine, turbulence2, PTZ, lowFramerate, dynamicBackground, or bridgeEntry unless needed to avoid direct regression.

### Live Decision

Step 3B targeted category live retry with 8C-2Q2 fails due to the parking proposal/intervention gate. Full CDnet remains held. Step 4 full CDnet dry-run is not recommended until a narrow parking live proposal-retighten dry-run and live retry pass after review.
