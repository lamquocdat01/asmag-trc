# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8C-2G Official Smoke Freeze

Date: 2026-05-13

Status: official smoke-live candidate. This is not a full validation success.

## Executive Summary

Phase 8C-2G is the first official smoke-live candidate to emerge from the Phase 8C-2B through 8C-2G refinement sequence.

8C-2G passes both the smoke dry-run gate and the official smoke-live gate. The official live smoke completed 32/32 jobs with 0 failed jobs, kept normal-frame interventions at 0, kept cubicle recall above 0.80, preserved bridgeEntry and continuousPan safeguards, and reduced live intervention pressure relative to dry-run.

This is a smoke-live freeze only. It is not full CDnet2014 validation, not cross-dataset validation, and not edge-device profiling.

## Scope

This report freezes the Phase 8C-2G smoke-stage result after the completed dry-run and official live smoke for:

- Dry-run root: `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2g_dryrun/`
- Official live root: `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2g_live/`

No new experiment was run for this consolidation step. Existing summary files were inspected only.

## Phase Lineage

| Phase | Outcome |
|---|---|
| 8C-2 | Failed because the intervention design was detector-heavy. |
| 8C-2B | Restored sparse detector behavior, but cubicle recall was too low. |
| 8C-2C | Added event/foreground block-only override, but cubicle recall remained insufficient. |
| 8C-2D | Added cubicle-like no-detector continuity and improved cubicle recall, but exceeded the intervention gate. |
| 8C-2E | Reclaimed non-cubicle budget, but still had normal-frame and cubicle-target issues. |
| 8C-2F | Fixed normal-frame behavior and cubicle recall, but exceeded the intervention gate by about 4 frames. |
| 8C-2G | Trimmed lowFramerate/tramCrossroad_1fps and passed both dry-run and official live smoke. |

## Official Dry-Run Summary

Sources:
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2g_dryrun/run_progress.csv`
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2g_dryrun/ai_intervention_2g_summary.csv`

| Metric | Dry-run value |
|---|---:|
| Completed jobs | 32 |
| Failed jobs | 0 |
| Proposed intervention rate | 0.31500 |
| Proposed detector request rate | 0.03000 |
| Block-only rate | 0.28500 |
| Event/foreground block-only rate | 0.23875 |
| Normal-frame proposed interventions | 0 |
| Guard alignment | 1.00000 |
| Cubicle proposed known-event recall | 0.84848 |
| Cubicle unprotected event FN | 0 |
| bridgeEntry event FN | 0 |
| bridgeEntry detector budget max | 8 |
| continuousPan proposal rate | 0.05000 |
| lowFramerate/tramCrossroad_1fps proposal rate | 0.02000 |
| LowFramerate trim reclaimed proposals | 7 |

Dry-run gate result: pass.

## Official Live Summary

Sources:
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2g_live/run_progress.csv`
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2g_live/summary_cdnet_metrics.csv`
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2g_live/summary_research_metrics.csv`
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2g_live/ai_intervention_2g_summary.csv`

| Metric | Live value |
|---|---:|
| Completed jobs | 32 |
| Failed jobs | 0 |
| FMeasure | 0.19806 |
| Event_F1 | 0.55372 |
| Activation | 0.61125 |
| Avg_FPS | 25.35154 |
| P95 latency ms | 242.01526 |
| Proposed intervention rate | 0.28125 |
| Proposed detector request rate | 0.02875 |
| Normal-frame interventions | 0 |
| Cubicle proposed known-event recall | 0.82828 |
| Cubicle unprotected event FN | 0 |
| bridgeEntry event FN | 0 |
| bridgeEntry detector budget max | 2 |
| continuousPan proposal rate | 0.05000 |
| lowFramerate/tramCrossroad_1fps proposal rate | 0.01000 |
| LowFramerate trim reclaimed proposals | 7 |

Official live smoke result: pass.

## Dry-Run Vs Live Interpretation

| Check | Dry-run | Live | Interpretation |
|---|---:|---:|---|
| Proposed intervention rate | 0.31500 | 0.28125 | Intervention pressure decreased. |
| Proposed detector request rate | 0.03000 | 0.02875 | Detector request pressure decreased. |
| Normal-frame interventions | 0 | 0 | Normal-frame behavior stayed clean. |
| Cubicle recall | 0.84848 | 0.82828 | Recall decreased slightly but remained above 0.80. |
| Cubicle unprotected event FN | 0 | 0 | Cubicle protection stayed intact. |
| bridgeEntry event FN | 0 | 0 | bridgeEntry stayed protected. |
| bridgeEntry detector budget max | 8 | 2 | Live detector budget pressure improved. |
| continuousPan proposal rate | 0.05000 | 0.05000 | continuousPan stayed capped. |
| lowFramerate/tramCrossroad_1fps proposal rate | 0.02000 | 0.01000 | LowFramerate pressure decreased further in live. |
| Avg_FPS | 16.22514 | 25.35154 | FPS improved. |
| P95 latency ms | 426.21586 | 242.01526 | P95 latency improved. |
| Event_F1 | 0.59213 | 0.55372 | Event_F1 decreased and should be monitored before wider validation. |

The live smoke behavior matches the dry-run proposal expectations on the key guarded safety gates. The main caution is the Event_F1 decrease versus dry-run despite better FPS, latency, intervention pressure, and detector request pressure.

## Safety And Artifact Audit

- Accidental 8C-2E live artifacts exist in `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2e_live/`; they are excluded from official results and were not deleted.
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2g_live/` is the only official live output root for this smoke-live freeze.
- The default guarded smoke config remains disabled: `configs/asmag_tr_controller_online_guarded_cdnet_smoke.yaml` has `ai_intervention_enabled: false`.
- ONLINE_CALIBRATED, P1, P2, P3, FAST, and base ASMAG_TR_CONTROLLER were not modified for this freeze step.
- No PTZ-targeted, targeted CDnet, full CDnet, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched for this freeze step.

## Freeze Decision

Phase 8C-2G is frozen as the official smoke-live candidate for ASMAG_TR_CONTROLLER_ONLINE_GUARDED.

This freeze does not mark 8C-2G as a full validation success. Larger validation remains held pending explicit authorization.

## Recommended Step 2 Targeted Mini-Validation Design

Do not jump directly to full CDnet.

Recommended next step, after explicit approval, is Step 2: targeted mini-validation on critical videos. It should run dry-run first. Live should run only if targeted dry-run gates pass. Full CDnet remains held.

Candidate targeted set:

| Category focus | Video |
|---|---|
| Cubicle continuity | `cubicle` |
| Night-video event protection | `bridgeEntry` |
| PTZ cap preservation | `continuousPan` |
| LowFramerate trim target | `tramCrossroad_1fps` |
| DynamicBackground smoke coverage | `fountain02` |
| Additional non-PTZ dynamicBackground coverage | one additional non-PTZ dynamicBackground video |

Targeted validation should preserve the smoke-live safety gates: normal-frame interventions remain 0, cubicle recall remains at or above 0.80, bridgeEntry event FN remains 0, continuousPan stays capped, detector request pressure does not increase unexpectedly, and Event_F1 is monitored closely before any wider validation.

No full CDnet validation should be launched at Step 2.

## Q1 Roadmap After Freeze

| Step | Stage | Purpose | Status |
|---|---|---|---|
| Step 2 | Targeted mini-validation on critical videos | Check the smoke-live candidate on the most sensitive videos before expanding scope. | Recommended next; dry-run first only after approval. |
| Step 3 | Targeted category validation | Broaden within relevant CDnet categories after mini-validation passes. | Held. |
| Step 4 | Full CDnet2014 validation | Establish full-dataset CDnet behavior. | Held. |
| Step 5 | Cross-dataset subset validation | Check transfer behavior on LASIESTA, SBI2015, BMC, or selected subsets. | Held. |
| Step 6 | Jetson/AI Box edge profiling | Measure deployment runtime, latency, activation, and energy behavior. | Held. |
| Step 7 | Paper writing and ablation packaging | Package final evidence, ablations, and reproducibility material for Q1 submission. | Held. |
