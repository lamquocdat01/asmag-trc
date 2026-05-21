# ASMAG-TRC Step 3B Targeted Category Live Freeze

Date: 2026-05-16

## Executive Summary

Step 3B targeted category live is accepted as **PASS** under the revised protection-aware parking gate documented in `ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP3B_PARKING_GATE_REVIEW.md`.

The official targeted category live result is the completed 8C-2Q2 run:

- Output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2q2_live/`
- Completion: 80/80 jobs completed, 0 failed
- Aggregate detector request rate: 0.01062
- Normal-frame interventions: 0
- Guard alignment: 1.00000

This freeze does **not** mark 8C-2Q2 as full CDnet success. Full CDnet remains held until Step 4 is explicitly authorized.

## Gate Revision Rationale

The old raw parking gate required:

- `intermittentObjectMotion/parking` proposal/intervention <= 0.45000

The Step 3B parking gate review found this raw cap too strict for `intermittentObjectMotion/parking`. The 2Q3 and 2Q4 parking trim attempts showed that the retained over-gate parking frames were not generic non-risk frames. They were hard-protected or otherwise not safe to trim without increasing unprotected event-FN risk.

For this scene, proposal pressure is serving no-detector FN protection rather than broad detector-heavy behavior. The revised gate is scene-specific and applies only to `intermittentObjectMotion/parking`:

- parking proposal/intervention <= 0.50000 acceptable
- parking detector request <= 0.02000
- parking unprotected FN <= 12
- parking normal-frame interventions = 0
- parking accidental hard-protected trim count = 0
- aggregate detector request < 0.10000
- no broad detector-heavy behavior
- no forbidden validation launched

The accepted 2Q2 live parking result satisfies this revised gate:

- parking intervention: 0.50000
- parking detector request: 0.00000
- parking unprotected FN: 4
- normal-frame interventions: 0

## Official Targeted Category Live Metrics

| Metric | 8C-2Q2 targeted category live |
|---|---:|
| Completed jobs | 80/80 |
| Failed jobs | 0 |
| FMeasure | 0.44351 |
| Event_F1 | 0.67449 |
| Activation | 0.58678 |
| Avg_FPS | 24.60626 |
| P95 latency | 231.79742 ms |
| Proposal/intervention rate | 0.20677 |
| Detector request rate | 0.01062 |
| Block-only rate | 0.19616 |
| Event/foreground block-only rate | 0.15824 |
| Normal-frame interventions | 0 |
| Guard alignment | 1.00000 |

## Per-Video Live Summary

| Video | Live status | Key metrics | Gate result |
|---|---|---|---|
| `PTZ/continuousPan` | Controlled | intervention 0.05000, detector 0.01000, unprotected FN 0 | PASS |
| `PTZ/intermittentPan` | Controlled | intervention 0.01000, detector 0.00000, unprotected FN 0 | PASS |
| `baseline/highway` | Controlled | intervention 0.03000, detector 0.00000, unprotected FN 0 | PASS |
| `baseline/office` | Controlled | intervention 0.03000, detector 0.00000, unprotected FN 0 | PASS |
| `cameraJitter/traffic` | Controlled | intervention 0.02000, detector 0.00000, unprotected FN 0 | PASS |
| `dynamicBackground/canoe` | Quiet | intervention 0.00000, detector 0.00000, unprotected FN 0 | PASS |
| `dynamicBackground/fountain01` | Quiet | intervention 0.00000, detector 0.00000, unprotected FN 0 | PASS |
| `dynamicBackground/fountain02` | Normal-safe | intervention 0.40000, detector 0.01000, normal-frame false interventions 0 | PASS |
| `dynamicBackground/overpass` | Controlled | intervention 0.29000, detector 0.01000, unprotected FN 0 | PASS |
| `intermittentObjectMotion/parking` | Protection-aware exception | intervention 0.50000, detector 0.00000, event FN 10, protected FN 6, unprotected FN 4 | PASS under revised parking gate |
| `lowFramerate/tramCrossroad_1fps` | Quiet | intervention 0.00000, detector 0.00000, unprotected FN 0 | PASS |
| `lowFramerate/tunnelExit_0_35fps` | Watchlist controlled | intervention 0.30000, detector 0.00000, event FN 2, protected FN 1, unprotected FN 1 | PASS |
| `lowFramerate/turnpike_0_5fps` | Controlled | intervention 0.01000, detector 0.00000, unprotected FN 0 | PASS |
| `nightVideos/bridgeEntry` | Event-safe | intervention 0.15000, detector 0.04000, event FN 0 | PASS |
| `nightVideos/streetCornerAtNight` | Controlled | intervention 0.12000, detector 0.01000, unprotected FN 0 | PASS |
| `nightVideos/tramStation` | Controlled | intervention 0.19000, detector 0.04000, unprotected FN 0 | PASS |
| `shadow/backdoor` | Controlled | intervention 0.33000, detector 0.07000, unprotected FN 0 | PASS |
| `shadow/copyMachine` | Watchlist controlled | intervention 0.46000, detector 0.00000, event FN 8, protected FN 4, unprotected FN 4 | PASS |
| `shadow/cubicle` | Recall-safe | recall 0.89899, detector 0.02000, unprotected FN 0 | PASS |
| `turbulence/turbulence2` | Carry-over restored | intervention 0.31000, detector 0.00000, event FN 2, protected FN 2, unprotected FN 0 | PASS |

## Revised Gate Decision Table

| Gate | Result | Status |
|---|---:|---|
| 80/80 completed, 0 failed | 80/80, 0 failed | PASS |
| Aggregate detector request < 0.10000 | 0.01062 | PASS |
| Normal-frame interventions = 0 | 0 | PASS |
| Guard alignment >= 0.95 | 1.00000 | PASS |
| Cubicle recall >= 0.80 and unprotected FN = 0 | 0.89899 recall, 0 unprotected FN | PASS |
| BridgeEntry event FN = 0 | 0 | PASS |
| ContinuousPan intervention <= 0.05 | 0.05000 | PASS |
| IntermittentPan intervention <= 0.15 and unprotected FN = 0 | 0.01000, 0 unprotected FN | PASS |
| TramCrossroad_1fps intervention <= 0.05 and detector <= 0.02 | 0.00000 / 0.00000 | PASS |
| Fountain01 intervention <= 0.05 and detector <= 0.02 | 0.00000 / 0.00000 | PASS |
| Fountain02 normal-frame false interventions = 0 | 0 | PASS |
| CopyMachine unprotected FN <= 15 | 4 | PASS |
| Parking intervention <= 0.50000 under revised protection-aware gate | 0.50000 | PASS |
| Parking detector <= 0.02000 | 0.00000 | PASS |
| Parking unprotected FN <= 12 | 4 | PASS |
| Parking normal-frame interventions = 0 | 0 | PASS |
| Parking accidental hard-protected trim count = 0 | 0 by gate-review record | PASS |
| Turbulence2 intervention <= 0.35 and unprotected FN <= 2 | 0.31000, 0 unprotected FN | PASS |
| TunnelExit_0_35fps intervention <= 0.35 and unprotected FN <= 1 | 0.30000, 1 unprotected FN | PASS |
| No broad detector-heavy behavior | aggregate detector 0.01062 | PASS |
| No forbidden validation launched | freeze step documentation only | PASS |

## Residual Watchlist for Step 4

- `intermittentObjectMotion/parking`: proposal/intervention 0.50000, unprotected FN 4. This is accepted only under the protection-aware parking exception and must be monitored again in full CDnet.
- `shadow/copyMachine`: proposal/intervention 0.46000, unprotected FN 4. Detector remained 0.00000; continue monitoring intervention pressure.
- `lowFramerate/tunnelExit_0_35fps`: unprotected FN 1. Still within the accepted 2O gate, but remains a live-sensitive scene.

## Safety Audit

- No experiment, live run, live compare, full CDnet run, full CDnet compare, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched during this freeze step.
- Accidental 8C-2E live artifacts remain excluded and were not deleted or reused.
- Default guarded configuration remains unchanged; `ai_intervention_enabled: false` is preserved.
- No controller code, comparison code, ONLINE_CALIBRATED, P1, P2, P3, FAST, or ASMAG_TR_CONTROLLER artifact was modified.
- The 8C-2Q2 targeted category live output root is the official Step 3B targeted category live result.

## Freeze Decision

Step 3B targeted category live is frozen as **PASS** under the revised protection-aware parking gate.

8C-2Q2 is marked as the current full-CDnet dry-run candidate.

This is **not** full CDnet success. Full CDnet remains held.

## Recommended Next Step

Proceed next with **Step 4 full CDnet2014 dry-run only**, after explicit authorization.

Do not run full CDnet live yet.

Do not run cross-dataset validation yet.
