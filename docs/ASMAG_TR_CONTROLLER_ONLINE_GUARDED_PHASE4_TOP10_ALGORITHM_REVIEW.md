# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 4 Top 10 Algorithm Review

Date: 2026-05-09

Scope: research-only review for `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`. This document does not authorize code changes, threshold tuning, targeted CDnet, full CDnet, LASIESTA, SBI2015, or BMC runs.

## Executive Finding

The strongest outside methods do not suggest "activate more often" as the core Phase 4 answer. They suggest a more structural idea: robust foreground systems separate motion observation, background reliability, temporal propagation, and mask arbitration. Phase 3 has motion cues and cadence rules, but it does not yet have a mask-quality arbitration layer. In PTZ/global-motion scenes, that missing layer causes P3 fallback and raw motion masks to be trusted even when background motion dominates the frame.

## Table 5: Top 10 Algorithm Family Comparison

| Family | Core principle | Strength | Weakness | Relevance to ASMAG | Deployability | Borrow | Avoid |
|---|---|---|---|---|---|---|---|
| LTS / temporal distribution and spatial correlation | Model pixel/block temporal distributions plus spatial support relationships | Handles local dynamic background better than single-pixel subtraction | Online updates can deadlock if wrong masks guide the model | Very relevant for candidate reliability and background trust | Medium if reduced to statistics | Spatial support confidence and temporal distribution drift | Heavy per-pixel model replacement |
| DeepFTSG | Fuse appearance with hand-crafted motion/change cues in multi-stream architecture | Strong hard-scene robustness and cross-dataset generalization | Deep model is too heavy for current guarded edge loop | Very relevant as a conceptual template | Low as full network, high as design pattern | Multi-cue arbitration and separate motion/change streams | Adding a new supervised network now |
| BSUV-Net / BSUV-Net 2.0 | Supervised video-agnostic BGS with spatiotemporal augmentation | Learns PTZ, illumination, jitter robustness from augmentation | Requires training data and background/semantic inputs | Useful for PTZ augmentation idea and stress tests | Medium to low for edge, unless fast variant | Synthetic PTZ/jitter perturbation for validation and proxy design | Scene-supervised deployment dependency |
| FgSegNet / FgSegNet_v2 | Multi-scale encoder-decoder foreground segmentation | Excellent scene-dependent CDnet scores | Often scene/video specific and supervised | Useful for mask plausibility and multi-scale object shape priors | Low for current pipeline | Multi-scale compactness/objectness concepts | Per-video training or ensemble dependence |
| 3DCD / 3D spatiotemporal CNN / STPNet-like | Learn spatial and temporal features jointly from clips | Captures temporal consistency and short-term propagation | Expensive and supervised | Relevant to event-continuity and temporal stability scoring | Low as full model | Clip-level temporal consistency score | 3D CNN in the guarded online loop |
| Optical-flow / Siamese / motion-compensation | Estimate relative motion or align frames before differencing | Directly addresses camera motion and PTZ | Flow can be expensive and noisy in low texture/night scenes | Highly relevant to continuousPan | Medium if sparse/downscaled | Optional global affine/shift compensation and residual motion masks | Dense flow per frame as required path |
| SuBSENSE / PAWCS / WeSamBE / IUTIS | Robust classical background subtraction with local binary features, persistence, sample consensus, ensembles | Strong unsupervised robustness and low supervision | Still assumes mostly stationary camera; ensembles add cost | Very relevant to label-free reliability and sample persistence | High to medium | Background model reliability, update inhibition, consensus | Replacing the whole controller with an ensemble |
| LDB / Learning Dynamic Background | Learn dynamic background patterns or background generators | Separates repetitive background motion from foreground | Can require training or slow adaptation | Relevant to fountain/turbulence and dynamic regions | Medium if reduced to dynamic-region memory | Dynamic-background reliability map | Heavy generative model |
| Cross-scene supervised-unsupervised communication | Use supervised coarse masks to guide unsupervised background updates | Avoids update deadlock and improves cross-scene flexibility | Still depends on a supervised guide | Relevant because ASMAG already has detector and BGS candidates | Medium | Detector-guided selective update and mask arbitration | Training a new semantic guide now |
| Edge adaptive video analytics | Select configurations by content, budget, and risk | Balances accuracy/latency with adaptive scheduling | Difference detectors fail when scene drift violates assumptions | Directly aligned with ASMAG-TRC | High | Multi-objective risk scheduler and safety gates | Accuracy-agnostic latency-only scheduling |

## 1. LTS / Learning Temporal Distribution and Spatial Correlation

Core idea: instead of treating each pixel independently, estimate temporal distributions and spatial support/correlation. A foreground decision is more reliable when it is consistent with local spatial neighborhoods and temporal behavior, not merely different from the current background estimate.

Problems solved:

- Dynamic background with repeated local motion.
- Background-update drift.
- Isolated noise and fragmented masks.

Challenge coverage:

| Challenge | Expected behavior |
|---|---|
| PTZ/global motion | Limited unless paired with motion compensation; spatial correlations can detect widespread invalidity. |
| dynamicBackground | Strong conceptual fit. |
| shadow | Helps if features are not only intensity. |
| night | Helps if temporal distributions adapt slowly and avoid flicker. |
| lowFramerate | Risky because temporal continuity is sparse. |
| turbulence | Useful for modeling repetitive non-object motion. |

Deployability: medium. A full per-pixel correlation model is too costly, but small rolling features are feasible.

Borrow for ASMAG:

- A `background_reliability_score` based on temporal stability and local support.
- A `spatial_support_score` that penalizes masks with scattered full-frame activity.
- A rule that background model updates should be inhibited when global motion invalidates the model.

Do not borrow:

- Expensive per-pixel correlation update as the main online mechanism.

## 2. DeepFTSG

Core idea: fuse appearance, motion, and change cues in a learned multi-stream architecture. The important lesson is not just "use deep learning"; it is the separation of cue types before fusion.

Problems solved:

- Complex backgrounds where raw motion is ambiguous.
- Scenes where appearance helps distinguish object-like foreground from background motion.
- Cross-dataset robustness through multi-cue reasoning.

Challenge coverage:

| Challenge | Expected behavior |
|---|---|
| PTZ/global motion | Better than raw BGS because multiple cues can veto unreliable motion. |
| dynamicBackground | Strong. |
| shadow | Strong if trained with sufficient examples. |
| night | Moderate to strong. |
| lowFramerate | Moderate. |
| turbulence | Strong relative to simple BGS. |

Deployability: full DeepFTSG is too heavy for Phase 4, but its architecture is a direct blueprint for a lightweight arbitration layer.

Borrow for ASMAG:

- Separate streams: current frame appearance, motion/change masks, temporal consistency, detector memory.
- Fuse cues into a reliability decision before choosing P3/ACC/FAST/reuse.

Do not borrow:

- New supervised multi-stream network in the guarded online path before smoke is stable.

## 3. BSUV-Net / BSUV-Net 2.0

Core idea: train a video-agnostic supervised BGS network using spatiotemporal augmentations that mimic real deployment stressors such as PTZ, camera jitter, intermittent objects, and illumination variation.

Problems solved:

- Generalization to unseen videos.
- PTZ-like perturbations and camera jitter.
- Illumination variation.

Challenge coverage:

| Challenge | Expected behavior |
|---|---|
| PTZ/global motion | Stronger than non-augmented supervised BGS. |
| dynamicBackground | Strong. |
| shadow | Moderate to strong. |
| night | Depends on training distribution. |
| lowFramerate | Needs temporal augmentation. |
| turbulence | Moderate. |

Deployability: full model is not the right next step for the guarded pipeline; a fast variant is interesting but still a new model dependency.

Borrow for ASMAG:

- Use synthetic PTZ/jitter/illumination perturbation as a design principle for label-free stress proxies.
- Make smoke acceptance include perturbation-like behavior: global motion, widespread masks, and background unreliability.

Do not borrow:

- Supervised scene/video-specific model training.

## 4. FgSegNet / FgSegNet_v2

Core idea: multi-scale encoder-decoder networks learn object-like spatial structure and foreground boundaries. They are highly effective when trained for the target scene/video distribution.

Problems solved:

- Fine foreground boundaries.
- Camouflage and complex spatial context.
- Multi-scale object segmentation.

Challenge coverage:

| Challenge | Expected behavior |
|---|---|
| PTZ/global motion | Strong if trained for it; weak if the scene distribution shifts. |
| dynamicBackground | Strong in trained scenes. |
| shadow | Strong in trained scenes. |
| night | Strong if represented in training. |
| lowFramerate | Depends on training. |
| turbulence | Strong if represented. |

Deployability: low for the current edge loop because scene-specific training and heavy inference conflict with ASMAG-TRC's deployment goal.

Borrow for ASMAG:

- Multi-scale mask quality: object-like blobs should have plausible area, compactness, and persistence.
- Whole-frame or texture-like masks should receive low trust under global motion.

Do not borrow:

- Per-video trained networks or ensembles.

## 5. 3DCD / 3D Spatiotemporal CNN / STPNet-like Temporal Propagation

Core idea: process short clips instead of isolated frames so the model can reason about temporal consistency and object persistence.

Problems solved:

- Temporal flicker.
- Broken event continuity.
- Short-term motion ambiguity.

Challenge coverage:

| Challenge | Expected behavior |
|---|---|
| PTZ/global motion | Helpful if it learns relative motion, but not sufficient alone. |
| dynamicBackground | Strong if trained well. |
| shadow | Moderate. |
| night | Moderate. |
| lowFramerate | Challenging because clip continuity is sparse. |
| turbulence | Stronger than frame-only methods. |

Deployability: low as a 3D CNN. High as a small temporal score over existing masks.

Borrow for ASMAG:

- `temporal_mask_consistency_score`.
- `event_continuity_risk`.
- Rolling disagreement between current candidate masks and previous accepted masks.

Do not borrow:

- Full 3D CNN inference inside every smoke frame.

## 6. Optical-Flow / Siamese / Motion-Compensation Methods

Core idea: estimate frame-to-frame camera or object motion, align frames or propagate masks, then evaluate residual motion. Siamese/change networks learn cross-frame differences; optical-flow methods explicitly model motion.

Problems solved:

- Camera motion.
- Reuse staleness.
- Object-mask propagation when detector is skipped.

Challenge coverage:

| Challenge | Expected behavior |
|---|---|
| PTZ/global motion | Best direct match. |
| dynamicBackground | Useful if foreground and background motion separate. |
| shadow | Limited. |
| night | Risky if low texture/noisy flow. |
| lowFramerate | Risky if displacement is large. |
| turbulence | Can confuse local flow. |

Deployability: medium if downscaled and optional; low if dense flow is mandatory.

Borrow for ASMAG:

- Downscaled global shift or affine estimate.
- Residual motion mask after compensation.
- Reuse propagation by global transform.

Do not borrow:

- Full dense optical flow on every frame.
- Heavy Siamese network training.

## 7. SuBSENSE / PAWCS / WeSamBE / IUTIS

Core idea: classical robust BGS methods combine local binary features, color/texture samples, persistence weighting, local adaptation, and ensemble consensus.

Problems solved:

- Illumination and shadow robustness.
- Dynamic backgrounds.
- Sample persistence and update reliability.

Challenge coverage:

| Challenge | Expected behavior |
|---|---|
| PTZ/global motion | Limited unless global motion is handled separately. |
| dynamicBackground | Strong. |
| shadow | Stronger than plain MOG2. |
| night | Moderate. |
| lowFramerate | Moderate. |
| turbulence | Stronger than plain MOG2 but still imperfect. |

Deployability: high to medium. Classical cue summaries are cheap; full ensemble is heavier.

Borrow for ASMAG:

- Consensus across P3/ACC/FAST/FrameDiff/KNN/MOG2 before trusting a mask.
- Persistence-weighted background reliability.
- Update inhibition during unreliable periods.

Do not borrow:

- Replacing ASMAG with a full classical ensemble before Phase 4 smoke diagnosis is solved.

## 8. LDB / Learning Dynamic Background

Core idea: learn patterns of dynamic background and separate repetitive background motion from foreground motion.

Problems solved:

- Water, trees, turbulence-like repetitive motion.
- Dynamic background false positives.

Challenge coverage:

| Challenge | Expected behavior |
|---|---|
| PTZ/global motion | Not primary unless camera motion is modeled. |
| dynamicBackground | Strong. |
| shadow | Limited. |
| night | Depends on features. |
| lowFramerate | Can be unstable. |
| turbulence | Strong conceptual fit. |

Deployability: medium if implemented as a dynamic-region memory map; low if implemented as a generative model.

Borrow for ASMAG:

- `dynamic_background_risk` and `dynamic_region_memory` to distinguish repeated background from object motion.
- Avoid escalating simply because motion is present in known dynamic background regions.

Do not borrow:

- Heavy generative dynamic-background model.

## 9. Cross-Scene Supervised-Unsupervised Model Communication

Core idea: use a supervised model for coarse guidance while an unsupervised background model handles fine-grained online adaptation. The two models communicate so one does not blindly poison the other.

Problems solved:

- Background update deadlock.
- Cross-scene adaptation.
- Coarse-to-fine segmentation.

Challenge coverage:

| Challenge | Expected behavior |
|---|---|
| PTZ/global motion | Helpful if the supervised guide is robust to PTZ. |
| dynamicBackground | Strong. |
| shadow | Moderate to strong. |
| night | Depends on guide. |
| lowFramerate | Moderate. |
| turbulence | Stronger than unsupervised alone. |

Deployability: medium because ASMAG already has detector outputs and classical candidates.

Borrow for ASMAG:

- Detector output should guide when P3/ACC/FAST candidates are allowed to update or be reused.
- Candidate masks should be treated as proposals, not truth.

Do not borrow:

- Training a separate semantic segmentation guide for Phase 4.

## 10. Edge Adaptive Video Analytics

Core idea: systems such as NoScope, Chameleon, and ApproxNet-style adaptive inference select cheaper or heavier configurations based on content, accuracy budgets, and resource constraints.

Problems solved:

- High inference cost.
- Stream-specific redundancy.
- Dynamic compute scheduling.

Challenge coverage:

| Challenge | Expected behavior |
|---|---|
| PTZ/global motion | Only if the scheduler has a reliability signal. |
| dynamicBackground | Only if configuration search observes drift. |
| shadow | Needs quality-aware rules. |
| night | Needs event-continuity and confidence signals. |
| lowFramerate | Needs cadence-aware scheduling. |
| turbulence | Needs failure-aware fallback. |

Deployability: high. This family is closest to ASMAG-TRC's engineering identity.

Borrow for ASMAG:

- Make Phase 4 a multi-objective risk scheduler, not a set of one-off gates.
- Expose accuracy-risk, latency-risk, energy-risk, and event-risk terms.

Do not borrow:

- Fixed-camera difference-detector assumptions without a global-motion reliability veto.

## Sources Used

Local project sources:

- `docs/P4_ONLINE_DIAGNOSTIC_REPORT.md`
- `docs/P4_ONLINE_TOP10_IMPROVEMENTS.md`
- `manuscript/ASMAG_2026_submission_ready_v1.md`
- `outputs/submission_package/references_ready.bib`

External references checked during research:

- BSUV-Net 2.0: https://papers.cool/arxiv/2101.09585
- BSUV-Net 2.0 project summary: https://vip.bu.edu/projects/vsns/background-subtraction/bsuv-net-2/
- DeepFTSG: https://link.springer.com/article/10.1007/s11263-023-01910-x
- FgSegNet_v2: https://github.com/lim-anggun/FgSegNet_v2
- Foreground detection with multi-scale spatiotemporal features: https://pmc.ncbi.nlm.nih.gov/articles/PMC6308466/
- 3D atrous ConvLSTM BGS: https://researchwith.njit.edu/en/publications/a-3d-atrous-convolutional-long-short-term-memory-network-for-back
- Cross-scene supervised-unsupervised communication: https://www.sciencedirect.com/science/article/abs/pii/S0031320321001825
- CDnet classical method ranking context: https://www.telecom.uliege.be/summarization/CDNET/CDNET-2014-summarized-performances.html
