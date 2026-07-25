"""
E4 — Exhaustive arbitration-domain test  [answers Reviewer R1.3, R1.4]

Enumerates the FULL finite input domain of the reference pure-function safety
arbiter `final_safety_arbitration_v2` (Section 3.4, vendored to
`src/safety/final_safety_arbitration_v2.py`) and asserts five properties:

  P1  I1 (normal-frame protection): a quiet frame (no event memory, no
      risk_high, no guard_active) is never overridden -> NO_CHANGE, override=0.
  P2  Every override implies event_memory OR risk_high (reviewer's condition);
      we additionally verify the exact, stronger precondition of each override.
  P3  Totality + mutual exclusion: every input yields exactly one label from a
      fixed finite set, with a well-formed result dict, and (label, override)
      are mutually consistent (override iff a FORCE_* label).
  P4  Determinism: identical input -> identical output, with no state leakage
      across interleaved calls.
  P5  Inputs are not mutated and the returned dict aliases no input object.

Pure logic, no video, no torch. Runnable directly:
    python tests/test_arbitration_exhaustive.py
or under pytest:
    pytest tests/test_arbitration_exhaustive.py
"""
import sys
from itertools import product
from pathlib import Path

# Make `src/` importable whether run from repo root or tests/.
_ROOT = Path(__file__).resolve().parents[1]
for _p in (_ROOT / "src", _ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from safety.final_safety_arbitration_v2 import final_safety_arbitration_v2  # noqa: E402

VALID_LABELS = {
    "DISABLED",
    "NO_CHANGE",
    "FORCE_PROTECT_EVENT_MEMORY",
    "FORCE_RISK_HIGH_RESCUE",
}
FORCE_LABELS = {"FORCE_PROTECT_EVENT_MEMORY", "FORCE_RISK_HIGH_RESCUE"}
REQUIRED_KEYS = {"arb_v2_label", "arb_v2_proposal", "arb_v2_override", "arb_v2_reason"}

# --- The finite input domain -------------------------------------------------
# The arbiter partitions action_label into three equivalence classes:
#   (a) the six UNSAFE_REUSE_ACTIONS, (b) "DETECT_ACC" (safety depends on
#   pred_object_count), (c) every other ("safe") label. We enumerate all six
#   unsafe labels plus DETECT_ACC plus representative safe labels so every class
#   is exercised.
UNSAFE_REUSE_ACTIONS = [
    "CLOSED_EMPTY_ACC",
    "CLOSED_EMPTY_P3_FALLBACK",
    "REUSE_ACC",
    "LIGHTWEIGHT_MASK_ACC",
    "FALLBACK_P3_GUARD",
    "FALLBACK_P3_POLICY",
]
SAFE_ACTIONS = ["DETECT_FAST", "LIGHTWEIGHT_MASK_P3_FALLBACK", "REUSE_P3_FALLBACK"]
ACTION_LABELS = UNSAFE_REUSE_ACTIONS + ["DETECT_ACC"] + SAFE_ACTIONS

DETECTOR_REQUEST = [0, 1]
PROPOSAL = [None, 0, 1]          # prompt domain {None, present}, plus explicit 0
ACTIVE_EVENT_MEMORY = [0, 1]
RISK_HIGH = [0, 1]
GUARD_ACTIVE = [0, 1]
PRED_OBJECT_COUNT = [0, 1]       # {0, >0}
EVENT_SAFETY_ENABLED = [False, True]
FRAME_IDX = [0, 1, 999]          # must not affect the decision


def enumerate_domain():
    """Yield every kwargs dict in the finite input domain."""
    for (al, dr, pr, aem, rh, ga, poc, ese, fi) in product(
        ACTION_LABELS, DETECTOR_REQUEST, PROPOSAL, ACTIVE_EVENT_MEMORY,
        RISK_HIGH, GUARD_ACTIVE, PRED_OBJECT_COUNT, EVENT_SAFETY_ENABLED, FRAME_IDX,
    ):
        yield {
            "frame_idx": fi,
            "action_label": al,
            "detector_request": dr,
            "proposal": pr,
            "active_event_memory": aem,
            "risk_high": rh,
            "guard_active": ga,
            "pred_object_count": poc,
            "event_safety_enabled": ese,
        }


def _call(kw):
    return final_safety_arbitration_v2(**kw)


# --- P3: totality + mutual exclusion ----------------------------------------
def test_totality_and_mutual_exclusion():
    for kw in enumerate_domain():
        r = _call(kw)
        assert isinstance(r, dict), f"non-dict result for {kw}"
        assert REQUIRED_KEYS.issubset(r.keys()), f"missing keys for {kw}: {r}"
        assert r["arb_v2_label"] in VALID_LABELS, f"invalid label {r['arb_v2_label']} for {kw}"
        # (label, override) mutual consistency: override iff a FORCE_* label.
        is_force = r["arb_v2_label"] in FORCE_LABELS
        assert r["arb_v2_override"] in (0, 1), f"override not 0/1 for {kw}"
        assert bool(r["arb_v2_override"]) == is_force, (
            f"override/label mismatch for {kw}: {r}"
        )


# --- P1: I1 normal-frame protection -----------------------------------------
def test_p1_normal_frame_never_overridden():
    for kw in enumerate_domain():
        r = _call(kw)
        quiet = (
            kw["active_event_memory"] == 0
            and kw["risk_high"] == 0
            and kw["guard_active"] == 0
        )
        if kw["event_safety_enabled"] and quiet:
            assert r["arb_v2_label"] == "NO_CHANGE", f"I1 violated (label) for {kw}: {r}"
            assert r["arb_v2_override"] == 0, f"I1 violated (override) for {kw}: {r}"
            assert r["arb_v2_reason"].startswith("I1"), f"I1 reason for {kw}: {r}"
        if not kw["event_safety_enabled"]:
            assert r["arb_v2_label"] == "DISABLED", f"disabled path for {kw}: {r}"
            assert r["arb_v2_override"] == 0


# --- P2: override implies event_memory OR risk_high --------------------------
def test_p2_override_requires_event_or_risk():
    for kw in enumerate_domain():
        r = _call(kw)
        if r["arb_v2_override"] == 1:
            # Reviewer's stated condition:
            assert kw["active_event_memory"] == 1 or kw["risk_high"] == 1, (
                f"P2 violated (override without event/risk) for {kw}: {r}"
            )
            # Stronger exact preconditions actually enforced by the arbiter:
            assert kw["risk_high"] == 1, f"override without risk_high for {kw}: {r}"
            assert kw["proposal"] == 0, f"override despite existing proposal for {kw}: {r}"
            assert kw["event_safety_enabled"] is True
            if r["arb_v2_label"] == "FORCE_PROTECT_EVENT_MEMORY":  # I2
                assert kw["active_event_memory"] == 1, f"I2 without event memory: {kw}"
            elif r["arb_v2_label"] == "FORCE_RISK_HIGH_RESCUE":    # I3
                assert kw["guard_active"] == 1, f"I3 without guard_active: {kw}"
                # I3 only reached when I2 did not fire => no event memory.
                assert kw["active_event_memory"] == 0, f"I3 with event memory (I2 should win): {kw}"
            # An override always sets the protective proposal.
            assert r["arb_v2_proposal"] == 1, f"override did not set proposal=1 for {kw}: {r}"


# --- P4: determinism / no state leakage -------------------------------------
def test_p4_determinism():
    domain = list(enumerate_domain())
    first = {i: _call(kw) for i, kw in enumerate(domain)}
    # Re-run in reverse order to expose any hidden ordering/state dependence.
    for i in reversed(range(len(domain))):
        again = _call(domain[i])
        assert again == first[i], f"non-deterministic for {domain[i]}: {first[i]} != {again}"


# --- P5: inputs not mutated, result aliases nothing --------------------------
def test_p5_inputs_not_mutated():
    for kw in enumerate_domain():
        snapshot = dict(kw)
        r = _call(kw)
        assert kw == snapshot, f"inputs mutated for {snapshot}: now {kw}"
        # Returned dict must be a fresh object, not an argument alias.
        assert r is not kw
        # Mutating the result must not affect a subsequent call.
        r["arb_v2_label"] = "TAMPERED"
        r2 = _call(kw)
        assert r2["arb_v2_label"] != "TAMPERED", f"result shared across calls for {kw}"


ALL_TESTS = [
    test_totality_and_mutual_exclusion,
    test_p1_normal_frame_never_overridden,
    test_p2_override_requires_event_or_risk,
    test_p4_determinism,
    test_p5_inputs_not_mutated,
]


def main():
    total = sum(1 for _ in enumerate_domain())
    print(f"[E4] Enumerating {total} input combinations over the arbiter domain.")
    failures = 0
    for t in ALL_TESTS:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"  FAIL  {t.__name__}: {e}")
    if failures:
        print(f"[E4] {failures} property/properties FAILED.")
        sys.exit(1)
    print(f"[E4] All 5 properties (P1-P5) hold over all {total} combinations.")


if __name__ == "__main__":
    main()
