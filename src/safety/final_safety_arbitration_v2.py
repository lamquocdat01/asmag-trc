"""
ASMAG-TRC: Pure-Function Safety Arbitration v2
===============================================
This is the complete source code for the safety arbitration function
described in Section 3.4 of the manuscript.

The function is a pure function: it receives only copied values (not
references to shared state) and returns a new dictionary without
reading or writing any external state.

Three invariants are evaluated:
  I1: Normal-frame protection (never intervene on quiet frames)
  I2: Event memory preservation (protect active events from missed detections)
  I3: Risk-high rescue (protect emerging events)

Author: Dat Lam Quoc
Date: 2026-05-22

--------------------------------------------------------------------------
Provenance (JSA revision, 2026-07-24): vendored verbatim from the submitted
supplementary package `ASMAG_TRC_Supplementary_Materials_v2.zip`
(`code/final_safety_arbitration_v2.py`). This is the reference / manuscript
implementation. The online runner (`src/run_experiment.py`) additionally
carries an *inline reduction* that emits only the I2 override
(FORCE_PROTECT_EVENT_MEMORY) for the empty-DETECT_ACC case — the only
override type observed in the 53-video CDnet2014 run (all 304 overrides were
I2; see Table A1). `tests/test_arbitration_exhaustive.py` exhaustively
validates this reference implementation and cross-checks the runner reduction.
--------------------------------------------------------------------------
"""


def final_safety_arbitration_v2(
    frame_idx,
    action_label,
    detector_request,
    proposal,
    active_event_memory,
    risk_high,
    guard_active,
    pred_object_count,
    event_safety_enabled=False,
):
    """
    Pure-function safety arbitration for ONLINE_GUARDED controller.

    Parameters
    ----------
    frame_idx : int
        Current frame index within the evaluation window.
    action_label : str
        Controller's chosen action (e.g., DETECT_ACC, REUSE_ACC,
        CLOSED_EMPTY_ACC, LIGHTWEIGHT_MASK_ACC, FALLBACK_P3_GUARD).
    detector_request : int
        Whether the controller requested detector activation (0 or 1).
    proposal : int
        Current protective proposal value (0 = no protection, 1 = proposed).
    active_event_memory : int
        Whether an active foreground event is being tracked (0 or 1).
    risk_high : int
        Whether the frame is flagged as high-risk (0 or 1).
    guard_active : int
        Whether the safety guard is currently engaged (0 or 1).
    pred_object_count : int
        Number of objects detected in the most recent YOLO call.
    event_safety_enabled : bool
        Master switch for safety arbitration (default: False).

    Returns
    -------
    dict
        Arbitration result with keys:
        - arb_v2_label: str (DISABLED, NO_CHANGE, FORCE_PROTECT_EVENT_MEMORY,
                              FORCE_RISK_HIGH_RESCUE)
        - arb_v2_proposal: int (0 or 1)
        - arb_v2_override: int (0 or 1, whether proposal was changed)
        - arb_v2_reason: str (human-readable reason)
    """
    result = {
        "arb_v2_label": "DISABLED",
        "arb_v2_proposal": proposal,
        "arb_v2_override": 0,
        "arb_v2_reason": "disabled",
    }

    if not event_safety_enabled:
        return result

    # === INVARIANT I1: Normal-frame protection ===
    # Never intervene on quiet normal frames where no event, risk, or guard is active.
    # This prevents false interventions on the vast majority of stable frames.
    is_normal_quiet = (
        active_event_memory == 0
        and risk_high == 0
        and guard_active == 0
    )
    if is_normal_quiet:
        result["arb_v2_label"] = "NO_CHANGE"
        result["arb_v2_reason"] = "I1_normal_frame_protected"
        return result

    # === Define unsafe action set ===
    # Actions where the detector is NOT providing fresh detection output
    UNSAFE_REUSE_ACTIONS = {
        "CLOSED_EMPTY_ACC",
        "CLOSED_EMPTY_P3_FALLBACK",
        "REUSE_ACC",
        "LIGHTWEIGHT_MASK_ACC",
        "FALLBACK_P3_GUARD",
        "FALLBACK_P3_POLICY",
    }

    # DETECT_ACC with pred_object_count=0 is also unsafe:
    # the detector ran but found nothing during an active event
    is_empty_detect = (
        action_label == "DETECT_ACC"
        and pred_object_count == 0
    )

    is_unsafe = action_label in UNSAFE_REUSE_ACTIONS or is_empty_detect

    if not is_unsafe:
        result["arb_v2_label"] = "NO_CHANGE"
        result["arb_v2_reason"] = "action_not_unsafe"
        return result

    # === INVARIANT I2: Event memory preservation ===
    # When an active event is at risk with no existing protection, force protect.
    # This is the primary safety mechanism (fired 304 times on CDnet2014).
    if (
        active_event_memory == 1
        and risk_high == 1
        and proposal == 0
    ):
        result["arb_v2_label"] = "FORCE_PROTECT_EVENT_MEMORY"
        result["arb_v2_proposal"] = 1
        result["arb_v2_override"] = 1
        if is_empty_detect:
            result["arb_v2_reason"] = "I2_empty_detect_active_event_memory_risk_high"
        else:
            result["arb_v2_reason"] = "I2_unsafe_action_active_event_memory_risk_high"
        return result

    # === INVARIANT I3: Risk-high rescue ===
    # When risk is high and guard is active but no event memory yet,
    # protect emerging events that haven't established memory tracking.
    if (
        risk_high == 1
        and guard_active == 1
        and proposal == 0
    ):
        result["arb_v2_label"] = "FORCE_RISK_HIGH_RESCUE"
        result["arb_v2_proposal"] = 1
        result["arb_v2_override"] = 1
        result["arb_v2_reason"] = "I3_risk_high_guard_active_unprotected"
        return result

    # No unsafe pattern matched
    result["arb_v2_label"] = "NO_CHANGE"
    result["arb_v2_reason"] = "unsafe_but_already_proposed_or_no_risk"
    return result
