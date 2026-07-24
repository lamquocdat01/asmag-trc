"""
E1 unit tests — Persistent-Motion Circuit Breaker  [Reviewer R3.2]

Pure-logic tests (no video, no NumPy) for
`src/safety/circuit_breaker.py::PersistentMotionCircuitBreaker`.

Runnable directly:  python tests/test_circuit_breaker.py
Under pytest:        pytest tests/test_circuit_breaker.py
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
for _p in (_ROOT / "src", _ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from safety.circuit_breaker import PersistentMotionCircuitBreaker as CB  # noqa: E402


def _run(cb, seq):
    """Feed a sequence of activations; return list of decision dicts."""
    return [cb.step(a) for a in seq]


# --- disabled breaker is inert ----------------------------------------------
def test_disabled_is_inert():
    cb = CB({"enabled": False})
    out = _run(cb, [1] * 500)
    assert all(d["run_full"] for d in out)
    assert all(not d["cb_bypass_active"] for d in out)
    assert cb.cb_entered == 0 and cb.frames_in_bypass == 0


# --- default parameters ------------------------------------------------------
def test_defaults_match_spec():
    cb = CB({"enabled": True})
    assert cb.theta_high == 0.85 and cb.theta_low == 0.60
    assert cb.window == 60 and cb.probe_every == 300 and cb.probe_len == 30


# --- never enters on low motion ---------------------------------------------
def test_low_motion_never_bypasses():
    cb = CB({"enabled": True, "window": 60})
    # rolling activation ~0.5 < theta_high 0.85
    out = _run(cb, [1, 0] * 500)
    assert cb.cb_entered == 0
    assert all(not d["cb_bypass_active"] for d in out)
    assert cb.state == CB.ACTIVE


# --- enters after a full window of high activation --------------------------
def test_enters_on_persistent_motion():
    W = 60
    cb = CB({"enabled": True, "window": W, "theta_high": 0.85})
    out = _run(cb, [1] * 120)
    assert cb.cb_entered == 1
    # No bypass before the window fills; entry no later than frame W.
    entry_idx = next(i for i, d in enumerate(out) if d["cb_entered_now"])
    assert entry_idx == W - 1, f"expected entry at frame {W}, got {entry_idx + 1}"
    assert not out[entry_idx - 1]["cb_bypass_active"]
    assert out[entry_idx]["cb_bypass_active"] and not out[entry_idx]["run_full"]
    # Subsequent non-probe frames are pure bypass (MOG2 skipped).
    assert out[entry_idx + 1]["cb_phase"] == "bypass"
    assert not out[entry_idx + 1]["run_full"]


# --- probe scheduling: probe fires K frames into bypass ----------------------
def test_probe_schedule_and_stay_when_still_busy():
    W, K, P = 10, 20, 5
    cb = CB({"enabled": True, "window": W, "probe_every": K, "probe_len": P,
             "theta_high": 0.85, "theta_low": 0.60})
    # Enter after W high frames, then stay high: probe should measure high and NOT exit.
    out = _run(cb, [1] * (W + K + P + 5))
    assert cb.cb_entered == 1
    probe_frames = [i for i, d in enumerate(out) if d["cb_phase"] == "probe"]
    assert len(probe_frames) == P, f"expected {P} probe frames, got {len(probe_frames)}"
    assert all(out[i]["run_full"] for i in probe_frames)  # gate re-enabled during probe
    assert cb.cb_exited == 0  # activation stayed high -> no exit
    assert cb.state == CB.BYPASS


# --- exit when probe activation drops below theta_low ------------------------
def test_exits_when_probe_low():
    W, K, P = 10, 20, 6
    cb = CB({"enabled": True, "window": W, "probe_every": K, "probe_len": P,
             "theta_high": 0.85, "theta_low": 0.60})
    # W high frames to enter; K-1 more high bypass frames; then P low (=0) probe frames.
    seq = [1] * W + [1] * (K - 1) + [0] * P + [0] * 5
    out = _run(cb, seq)
    assert cb.cb_entered == 1
    assert cb.cb_exited == 1, "breaker should exit when probe activation < theta_low"
    assert cb.state == CB.ACTIVE
    # After exit, low activation must NOT immediately re-enter bypass.
    assert out[-1]["cb_state"] == CB.ACTIVE
    assert not out[-1]["cb_bypass_active"]


# --- hysteresis: probe between theta_low and theta_high keeps bypass ---------
def test_hysteresis_midband_stays_bypassed():
    W, K, P = 10, 20, 10
    cb = CB({"enabled": True, "window": W, "probe_every": K, "probe_len": P,
             "theta_high": 0.85, "theta_low": 0.60})
    # Probe activation ~0.7 (7 of 10): between theta_low and theta_high -> stay.
    probe = ([1] * 7 + [0] * 3)  # 0.7
    seq = [1] * W + [1] * (K - 1) + probe + [1] * 5
    _run(cb, seq)
    assert cb.cb_exited == 0
    assert cb.state == CB.BYPASS


# --- determinism -------------------------------------------------------------
def test_determinism():
    seq = ([1] * 80 + [0] * 40 + [1] * 200)
    a = CB({"enabled": True})
    b = CB({"enabled": True})
    oa, ob = _run(a, seq), _run(b, seq)
    assert oa == ob
    assert a.stats() == b.stats()


# --- bypass invariant: bypass frames are detector-only (I1-I3 trivial) -------
def test_bypass_frames_are_detector_only():
    cb = CB({"enabled": True, "window": 30, "probe_every": 1000, "probe_len": 10})
    out = _run(cb, [1] * 300)
    bypass = [d for d in out if d["cb_phase"] == "bypass"]
    assert bypass, "expected some bypass frames"
    # In bypass the caller must run the detector every frame and skip MOG2+gate.
    assert all(d["cb_bypass_active"] and not d["run_full"] for d in bypass)


# --- config validation -------------------------------------------------------
def test_bad_thresholds_rejected():
    for bad in ({"enabled": True, "theta_low": 0.9, "theta_high": 0.8},
                {"enabled": True, "window": 0},
                {"enabled": True, "probe_len": -1}):
        try:
            CB(bad)
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for {bad}")


# --- stats sanity ------------------------------------------------------------
def test_stats_accounting():
    cb = CB({"enabled": True, "window": 20, "probe_every": 50, "probe_len": 10})
    n = 400
    _run(cb, [1] * n)
    s = cb.stats()
    assert s["cb_frames_total"] == n
    assert s["cb_entered"] == 1
    assert 0.0 < s["cb_bypass_fraction"] <= 1.0
    # bypass + probe + the pre-entry active frames account for all frames.
    assert cb.frames_in_bypass + cb.frames_in_probe + (cb.window) >= n - cb.window


ALL_TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]


def main():
    failures = 0
    for t in ALL_TESTS:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"  FAIL  {t.__name__}: {e}")
    if failures:
        print(f"[E1-CB] {failures} test(s) FAILED.")
        sys.exit(1)
    print(f"[E1-CB] All {len(ALL_TESTS)} circuit-breaker unit tests passed.")


if __name__ == "__main__":
    main()
