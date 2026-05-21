# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 7B Implementation Plan

## Goal

Implement the smallest safe teacher-distilled PTZ action-ranking bundle for `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`, without changing old baselines or non-PTZ behavior.

## Minimal Bundle

1. Keep deterministic safety guards first.
2. Add a PTZ action ranker for confirmed global motion states only.
3. Treat low geometry trust as a detector-anchor state, not as permission for weak substitutes.
4. Rank actions as:
   - high trust: `LIGHTWEIGHT_MASK_ACC` between anchors; tightly gated `REUSE_ACC` only if real high trust is present.
   - medium trust: `LIGHTWEIGHT_MASK_ACC` inter-anchor only when ACC quality and temporal/geometric consistency are acceptable.
   - low trust: `FALLBACK_P3_GUARD` or `DETECT_ACC` detector-like anchor.
5. Hard-block `LIGHTWEIGHT_MASK_P3_FALLBACK` and `REUSE_ACC` in PTZ low-trust states.
6. Preserve Phase 6C position-switch handling for twoPosition-like scenes.
7. Preserve bridgeEntry event safety and non-PTZ suppression.
8. Add diagnostics that log ranked candidates, selected teacher, ranker reason, and safety override reason.

## ContinuousPan Rule Draft

When confirmed camera motion is persistent and closed-empty is unsafe:

- If geometry trust is low, force detector-like anchor. Do not use `LEGACY_SAFE_P3_GUARD` unless it is known to execute detector-like refresh.
- If geometry trust is medium and an anchor is recent, allow `LIGHTWEIGHT_MASK_ACC` only if ACC quality is above threshold and disagreement is not extreme.
- If geometry trust is high, allow `LIGHTWEIGHT_MASK_ACC`; allow `REUSE_ACC` only under real high trust and short reuse age.

## twoPosition Rule Draft

If camera jump, position-switch reset, high shift instability, or low inlier-ratio geometry is active:

- Suppress continuous-pan policies.
- Run a short detector burst.
- Invalidate reuse.
- Exit to fast path or quality-gated `LIGHTWEIGHT_MASK_ACC` only after geometry stabilizes.

## Validation Sequence

Phase 7B should start with py_compile and smoke only. PTZ-targeted should remain blocked until smoke passes all aggregate, continuousPan, twoPosition, bridgeEntry, and non-PTZ gates.

## Risk

The largest risk is overfitting observational teacher/oracle labels into rules that improve continuousPan but regress twoPosition or bridgeEntry. The implementation should be narrow, diagnostic-heavy, and rollback-configurable.

## Decision

Implement a distilled deterministic ranked policy first, not an online learned classifier. Keep the learned-policy artifacts as research evidence and future teacher-label schema.
