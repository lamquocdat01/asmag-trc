# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 4 Research Diagnosis

Date: 2026-05-09

Scope: research-only diagnosis for `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`. No source code, thresholds, old `ONLINE_CALIBRATED` behavior, frozen CDnet2014 v1.6 outputs, targeted CDnet, full CDnet, LASIESTA, SBI2015, or BMC runs were changed.

## Executive Summary

Phase 3 proves that the guarded online controller can improve aggregate accuracy-efficiency metrics, but it also proves that cadence rules alone are not a robust hard-scene mechanism. The aggregate smoke result beats old `ONLINE_CALIBRATED`, yet `PTZ/continuousPan` remains a severe failure. Phase 2 failed because activation was suppressed and closed-empty/reuse dominated. Phase 3 fixed that specific collapse: activation rose to 0.49, closed-empty dropped to 0, and reuse dropped to 0. The remaining failure is therefore not simply "run the detector more often." It is a global-motion and mask-quality failure.

The key research conclusion is that `ASMAG_TR_CONTROLLER_ONLINE_GUARDED` needs a new label-free arbitration layer: Global-Motion and Mask-Quality Guard, or GMQ-Guard. GMQ-Guard should estimate whether P3, ACC, FAST, detector refresh, legacy-online-like behavior, lightweight mask update, or reuse is least risky on the current frame. It must explicitly score global motion risk, background model reliability, candidate mask quality, temporal consistency, detector staleness, event-continuity risk, latency overload risk, and energy cost.

## Current Phase 3 Result Interpretation

### Table 1: Current Pipeline Comparison

Source: `outputs/asmag_tr_controller_online_guarded_cdnet_smoke/comparison_summary.csv`.

| Pipeline | FMeasure | Event_F1 | mAP_50 | Activation | FPS | P95 latency ms | Reuse | AE_Score |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| P3_MOG2 | 0.5063 | 0.6412 | 0.3037 | 0.6600 | 74.19 | 279.28 | 0.0000 | 0.7884 |
| ASMAG_TR_CONTROLLER | 0.5063 | 0.6412 | 0.3037 | 0.6600 | 81.00 | 314.27 | 0.0000 | 0.8010 |
| ONLINE_CALIBRATED | 0.4155 | 0.5636 | 0.2144 | 0.6150 | 18.56 | 405.04 | 0.0938 | 0.6024 |
| ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 3 | 0.4476 | 0.5793 | 0.2383 | 0.5338 | 37.32 | 262.71 | 0.1025 | 0.6853 |

Interpretation:

- The guarded pipeline improves FMeasure by +0.0322, Event_F1 by +0.0157, FPS by +18.77, and P95 latency by -142.33 ms versus old online.
- It still trails P3/controller by -0.0587 FMeasure and -0.0619 Event_F1.
- The aggregate gain is real but fragile because it hides one severe PTZ failure and several category-specific event/mask risks.
- The old online path is not globally better, but on `continuousPan` it behaves like full P3 fallback and preserves higher FMeasure.

## continuousPan Root-Cause Analysis

### Table 2: continuousPan Action/Mode Diagnosis

Source: guarded `frame_metrics.csv`, `summary_by_video.csv`, and `online_mode_usage_by_video.csv`.

| Measure | ONLINE_CALIBRATED | GUARDED Phase 3 |
|---|---:|---:|
| FMeasure | 0.2347 | 0.1226 |
| Event_F1 | 0.2906 | 0.2906 |
| Recall | 0.9639 | 0.7126 |
| Precision | 0.1336 | 0.0671 |
| Activation | 1.00 | 0.49 |
| FPS | 2.07 | 12.64 |
| P95 latency ms | 856.58 | 346.78 |
| Reuse rate | 0.00 | 0.00 |
| Closed-empty rate | 0.00 | 0.00 |
| P3 fallback selected-mode rate | 1.00 | 0.23 before guard, 1.00 after guard |
| ACC selected-mode rate | 0.00 | 0.77 before guard |
| global_motion_proxy mean | not logged | 1.000 |
| global_motion_escape_active rate | not logged | 0.760 |
| global_motion_refresh_triggered rate | not logged | 0.430 |
| candidate_P3_area mean | not logged | 28,615 |
| candidate_ACC/FAST_area mean | not logged | 89,054 |
| motion_disagreement mean | not logged | 0.164 |

Action-level guarded result:

| action_label | frames | rate | mean F | mean recall | mean precision | mean latency ms |
|---|---:|---:|---:|---:|---:|---:|
| LIGHTWEIGHT_MASK_P3_FALLBACK | 51 | 0.51 | 0.0241 | 0.0815 | 0.0190 | 56.33 |
| FALLBACK_P3_GUARD | 38 | 0.38 | 0.1017 | 0.1424 | 0.0889 | 280.05 |
| FORCED_REFRESH | 6 | 0.06 | 0.0816 | 0.2700 | 0.0538 | 285.67 |
| FALLBACK_P3_POLICY | 5 | 0.05 | 0.0000 | 0.0000 | 0.0000 | 292.97 |

Answers to the continuousPan diagnostic questions:

1. Main failure: global camera motion plus candidate/fallback mask quality. Cadence contributes, but the key issue is that the selected action is often a low-quality P3/lightweight mask under global motion.
2. Candidate P3 masks are not simply too large; they are temporally and semantically unreliable. High F frames and zero F frames can both have high candidate areas. The issue is not scalar area alone.
3. FAST and ACC candidate areas are much larger than P3 on average, so they are not clearly safer. They may contain useful object evidence, but the current logs do not include candidate mask quality metrics such as overlap, compactness, spatial spread, or temporal consistency.
4. Old `ONLINE_CALIBRATED` chooses `P3_FALLBACK` on 100% of frames and activates on 100%. It is slow, but safer for FMeasure because it matches plain P3/controller behavior.
5. Activation is now partially sufficient but directed to the wrong action mix. The 49% active frames do not recover old online quality; 51% lightweight P3 frames have mean FMeasure 0.0241.
6. `global_motion_proxy` is too coarse. It is saturated at 1.0 for all frames and cannot distinguish useful fallback frames from harmful fallback frames.
7. P3 fallback becomes conditionally harmful under global motion. Plain P3 still beats guarded on this smoke slice, but guarded's lightweight P3 and sparse fallback cadence do not reproduce plain P3 quality.
8. Candidate area does not have a stable negative relationship with FMeasure in `continuousPan`. `candidate_P3_area` correlates positively with frame FMeasure in this run, while many high-area frames still fail. Area needs to be combined with shape, spread, temporal stability, and candidate disagreement.
9. Yes. Frames with global motion proxy 1.0, motion disagreement above 0.12, and large candidate masks can have FMeasure 0.0. This is the core evidence that high motion is not high foreground quality.
10. Exact old-vs-guarded difference: old online is slow full P3 fallback with 1.00 activation, 0 reuse, 0 closed-empty, FMeasure 0.2347. Guarded Phase 3 is faster, 0.49 activation, 0 reuse, 0 closed-empty, P3 after-guard mode on every frame, but only 0.1226 FMeasure because lightweight/fallback outputs under global motion are lower quality.

Root cause statement:

`continuousPan` is no longer an activation-collapse failure. It is a global-motion reliability and mask-arbitration failure. The current controller detects global motion but lacks a label-free way to decide whether P3, ACC, FAST, detector refresh, lightweight update, or legacy-online-like behavior is trustworthy.

## bridgeEntry Root-Cause Analysis

### Table 3: bridgeEntry Action/Event Diagnosis

Source: guarded `frame_metrics.csv`, `summary_by_video.csv`, and action by event-state crosstab.

| Measure | ONLINE_CALIBRATED | GUARDED Phase 3 |
|---|---:|---:|
| FMeasure | 0.2398 | 0.2339 |
| Event_F1 | 0.9744 | 0.9130 |
| Recall | 0.5092 | 0.4900 |
| Precision | 0.1570 | 0.1536 |
| Activation | 0.85 | 0.76 |
| FPS | 4.54 | 15.89 |
| P95 latency ms | 476.38 | 276.11 |
| Reuse rate | 0.15 | 0.09 |
| Closed-empty rate | not labeled | 0.11 |
| low_light_guard_active rate | not logged | 1.00 |
| night_refresh_triggered rate | not logged | 0.21 |
| illumination_proxy mean | not logged | 0.0367 |

Guarded action/event crosstab:

| action_label | frames | Event TP | Event FP | Event FN | mean F |
|---|---:|---:|---:|---:|---:|
| DETECT_ACC | 75 | 72 | 3 | 0 | 0.2770 |
| CLOSED_EMPTY_ACC | 11 | 0 | 0 | 11 | 0.0000 |
| REUSE_ACC | 9 | 9 | 0 | 0 | 0.1544 |
| LIGHTWEIGHT_MASK_ACC | 4 | 3 | 1 | 0 | 0.1208 |
| FORCED_REFRESH | 1 | 0 | 1 | 0 | 0.0000 |

Answers to the bridgeEntry diagnostic questions:

1. FMeasure improves versus Phase 2 because guarded ACC detection is cheaper and still produces useful masks; Event_F1 drops because 11 `CLOSED_EMPTY_ACC` frames become event false negatives.
2. The low-light guard is active, but it does not fully prevent detector gaps. Frames since last detector reaches a P95 of 17.1 and max of 22.
3. Yes. Event continuity is broken by cadence decisions that permit closed-empty while the event is ongoing.
4. `CLOSED_EMPTY_ACC` causes all 11 event FNs. `DETECT_ACC` contributes 3 event FPs, `LIGHTWEIGHT_MASK_ACC` 1 FP, and `FORCED_REFRESH` 1 FP, but the event gap is specifically closed-empty.
5. Yes. The pipeline needs an event-continuity guard: if recent frames support an active event and low-light risk is present, closed-empty should be treated as high risk unless a reliable no-object signal exists.

Root cause statement:

`bridgeEntry` is an event-continuity problem under low light. It is not a global motion problem. The correct Phase 4 mechanism is not broad activation; it is continuity-aware suppression of closed-empty and stale gaps.

## Hard-Scene Taxonomy

### Table 4: Hard-Scene Taxonomy

| Category/video | Phase 3 result | Main failure or benefit | Reliable signals | Risky signals | Phase 4 implication |
|---|---|---|---|---|---|
| PTZ/continuousPan | Severe FMeasure loss vs old online | Global motion plus poor fallback/lightweight mask quality | global_motion_proxy, motion_disagreement, after-guard P3 fallback | mask area alone, raw P3 trust | Add global-motion reliability and P3 veto/arbitration |
| PTZ/twoPositionPTZCam | Improves vs old online, small loss vs P3 | Mixed PTZ but not catastrophic | activation, candidate disagreement, fallback mix | global_motion_proxy sometimes high but not fatal | Avoid overreacting to all PTZ-like cues |
| nightVideos/bridgeEntry | F gap nearly closed, Event_F1 down | Event continuity broken by closed-empty | low_light_guard, frames_since_last_detector, Event_State | activation alone | Add event-continuity guard |
| dynamicBackground/fountain02 | Improves over old online, trails P3/controller | Suppression helps speed, but P3/controller still stronger | low motion disagreement, low candidate area, closed-empty tolerated | global_motion_proxy spikes | Keep latency controls; do not force PTZ behavior |
| shadow/backdoor | All pipelines FMeasure 0 in smoke | Not an informative FMeasure differentiator; latency/action still useful | closed-empty rate, activation cost | FMeasure alone | Use as safety/runtime check, not primary accuracy target |
| shadow/cubicle | Slight frame F benefit, Event_F1 regression | Shadow/dynamic mask fragmentation and closed-empty | candidate area and motion disagreement correlate with useful frames | closed-empty during active frames | Need shadow/event continuity but avoid broad P3 escalation |
| turbulence/turbulence2 | Large improvement vs old online, still below P3 | Guarded suppression works; P3/controller still best | low global motion, small candidates, closed-empty tolerance | treating turbulence like PTZ | Keep dynamic-background-specific policy |
| lowFramerate/tramCrossroad_1fps | Matches P3 frame F, faster than old | High activation needed; reuse limited | frames_since_last_detector low, activation high | cadence gaps | Preserve high refresh floor for low frame rate |

General hard-scene answers:

1. Videos benefiting from Phase 3: `turbulence2`, `fountain02`, `cubicle` frame-level, `bridgeEntry` FMeasure/FPS, `twoPositionPTZCam` vs old online, and `tramCrossroad_1fps` speed. Benefits come from shared gate features, reduced detector calls, and better cooldown controls.
2. Videos regressing: `continuousPan` against old/P3/controller and `bridgeEntry` Event_F1. Regressions occur when cadence or lightweight outputs break foreground/event continuity.
3. Common failure signals: high global-motion proxy saturation, high motion disagreement with weak FMeasure, long `frames_since_last_detector`, `CLOSED_EMPTY_*` during active events, high lightweight-mask rate, and large candidate disagreement.
4. Reliable cross-category signals: frames since detector, event-state continuity, closed-empty/reuse rates, candidate disagreement, latency overload, and candidate mask temporal consistency. These are safer than category names.
5. Overfit-prone signals: category labels, a single global-motion threshold, raw mask area, and one fixed fallback interval.

## Comparison Against Current Pipelines

`P3_MOG2` and `ASMAG_TR_CONTROLLER` are still the accuracy reference in the smoke set. They reach 0.5063 FMeasure and 0.6412 Event_F1 but activate more than guarded. Old `ONLINE_CALIBRATED` is worse globally but safer on `continuousPan` because it behaves like full P3 fallback there. Guarded Phase 3 is the best aggregate online variant so far, but it lacks a safety branch for the precise case where old online's conservative behavior is useful.

This creates an important design principle: Phase 4 should not make guarded identical to old online. It should only approximate old online under a narrow reliability condition: persistent global camera motion, low mask-quality confidence, and unacceptable foreground risk.

## Comparison Against Top Algorithm Families

Full detail is in `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE4_TOP10_ALGORITHM_REVIEW.md`. The distilled lessons are:

- DeepFTSG teaches multi-cue fusion: separate motion, change, appearance, and temporal evidence before arbitration.
- BSUV-Net 2.0 teaches that PTZ and illumination robustness require explicit stress modeling, not accidental threshold tuning.
- FgSegNet teaches multi-scale object plausibility, but its scene-specific supervision should not be copied.
- 3DCD/STP-like methods teach temporal consistency and event continuity, but full 3D inference is too heavy.
- Optical-flow/motion-compensation methods are the direct answer to camera motion, but should start as an optional downscaled module.
- SuBSENSE/PAWCS/WeSamBE/IUTIS teach persistence, local reliability, and consensus.
- Dynamic-background learning teaches that not all motion is object motion.
- Supervised-unsupervised communication teaches that detector outputs can guide background updates and candidate trust.
- Edge adaptive systems teach multi-objective scheduling with accuracy-risk, latency-risk, and energy-risk.

## Why Current Rule/Cadence Approach Is Insufficient

The current approach uses thresholded guards and cadence caps. That is necessary but not sufficient because the same scalar signal means different things in different scenes:

- High motion area can mean true foreground, global camera motion, dynamic background, or shadow.
- High P3 area can be useful in one `continuousPan` frame and useless in another.
- Low activation is dangerous in Phase 2 but lowering activation is beneficial in `turbulence2`.
- Closed-empty is acceptable in `fountain02` background intervals but breaks `bridgeEntry` events.
- Global motion proxy saturates at 1.0 on `continuousPan`, so it detects risk but cannot rank actions.

The missing abstraction is candidate trust. Phase 4 needs to ask: "Given this scene state, which candidate output is likely to be least wrong?" not merely "Is motion high enough to run P3?"

## Recommended Research Hypothesis

In PTZ/global-motion scenes, raw motion magnitude and P3 fallback are unreliable because background motion dominates the frame. A deployable guarded controller needs a label-free global-motion-aware and mask-quality-aware arbitration layer that can decide whether to trust P3, ACC, FAST, legacy-online-like behavior, detector refresh, temporal reuse, or lightweight mask update.

The next version should estimate:

- global motion risk
- background model reliability
- candidate mask quality
- temporal consistency
- detector staleness
- event continuity risk
- latency overload risk
- energy cost

Then it should choose the least risky action.

## Final Research Decision

1. Implement GMQ-Guard rather than another round of threshold tuning.
2. Smallest high-impact Phase 4 bundle: candidate mask quality scoring, P3 fallback veto, event-continuity guard, and narrow legacy-online safe branch for persistent global-motion risk.
3. Low-risk changes: additional logging, mask-quality features from existing masks, closed-empty veto during active events, action arbitration using existing candidates.
4. High-risk changes to postpone: dense optical flow, new deep segmentation model, policy retraining, replacing MOG2/KNN/ACC/FAST internals.
5. Motion compensation is not mandatory for the first Phase 4 implementation, but an optional downscaled global shift/affine probe should be designed behind a config flag.
6. A legacy-online safe branch should be included narrowly because old online is safer on `continuousPan`; old `ONLINE_CALIBRATED` itself must remain unchanged.
7. Smoke acceptance before targeted CDnet: no crashes, all GMQ logs present, aggregate FMeasure/Event_F1 above old online, FPS >= 35, aggregate P95 <= 300 ms preferred, `continuousPan` FMeasure within 0.02 of old online, `continuousPan` activation >= 0.50 or FMeasure recovered, `bridgeEntry` no `CLOSED_EMPTY_ACC` event FN run, and `bridgeEntry` Event_F1 no worse than old online by more than 0.02.
8. It is still reasonable to try making `ASMAG_TR_CONTROLLER_ONLINE_GUARDED` deployable, but only if Phase 4 treats it as a risk-aware arbitration system. If it remains cadence-rule-based, it should become a supplementary variant rather than the deployable pipeline.
