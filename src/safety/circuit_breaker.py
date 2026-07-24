"""
ASMAG-TRC: Persistent-Motion Circuit Breaker  [answers Reviewer R3.2]
====================================================================
Deterministic hysteresis bypass for scenes with persistent (~100%) motion
(e.g. `baseline/highway` at rush hour), where MOG2 background subtraction is
CPU-bound and runs continuously alongside the GPU-bound detector, wasting CPU
cycles for no accuracy benefit.

Design (no training; consistent with the paper's no-training philosophy):

  * Track a rolling activation rate ᾱ over a window of `window` (W) frames,
    ᾱ = mean of the per-frame activation indicator a_t ∈ {0,1}.
  * ENTER BYPASS when ᾱ > `theta_high` (a W-frame moving average exceeding
    θ_high encodes sustained high activation across the window). In BYPASS the
    MOG2 subtractor and adaptive gate are suspended and the detector runs on
    every frame (identical to the P1 detector-only pipeline). Because every
    frame is detected in BYPASS, the safety invariants I1–I3 hold trivially and
    the pure-function arbiter is untouched.
  * PROBE periodically: every `probe_every` (K) frames spent in BYPASS, re-enable
    the gate for a short `probe_len` (P) window and measure the probe activation
    rate ᾱ_probe.
  * EXIT BYPASS (back to ACTIVE) when ᾱ_probe < `theta_low`. Hysteresis
    (θ_low < θ_high) prevents oscillation at the boundary.

Worst-case overhead in BYPASS is bounded by the probe duty cycle ≈ P/K
(default 30/300 = 10%): only ~10% of frames re-run the gate.

Pure state machine: no video, no NumPy, no external state. Deterministic —
identical input sequence ⇒ identical decisions. Config-driven, default DISABLED.
"""
from collections import deque


DEFAULTS = {
    "enabled": False,
    "theta_high": 0.85,
    "theta_low": 0.60,
    "window": 60,        # W  — rolling activation window
    "probe_every": 300,  # K  — frames between probes while bypassed
    "probe_len": 30,     # P  — probe duration
}


class PersistentMotionCircuitBreaker:
    """Deterministic hysteresis bypass. See module docstring.

    Parameters
    ----------
    cfg : dict | None
        Values under the `circuit_breaker:` config key. Missing keys fall back
        to :data:`DEFAULTS`. When ``enabled`` is false the breaker is inert:
        every :meth:`step` reports ACTIVE / run_full=True and no bypass ever
        occurs, so the guarded pipeline behaves exactly as before.
    """

    ACTIVE = "ACTIVE"
    BYPASS = "BYPASS"

    def __init__(self, cfg=None):
        cfg = dict(DEFAULTS, **(cfg or {}))
        self.enabled = bool(cfg["enabled"])
        self.theta_high = float(cfg["theta_high"])
        self.theta_low = float(cfg["theta_low"])
        self.window = int(cfg["window"])
        self.probe_every = int(cfg["probe_every"])
        self.probe_len = int(cfg["probe_len"])
        if self.enabled:
            if not (0.0 <= self.theta_low < self.theta_high <= 1.0):
                raise ValueError(
                    f"circuit_breaker requires 0 <= theta_low < theta_high <= 1 "
                    f"(got theta_low={self.theta_low}, theta_high={self.theta_high})"
                )
            for k in ("window", "probe_every", "probe_len"):
                if int(cfg[k]) <= 0:
                    raise ValueError(f"circuit_breaker.{k} must be a positive integer")
        self.reset()

    def reset(self):
        self.state = self.ACTIVE
        self._acts = deque(maxlen=self.window)  # recent instantaneous activations
        self._bypass_age = 0                    # frames spent in bypass since entry
        self._in_probe = False
        self._probe_left = 0
        self._probe_acts = []
        # cumulative statistics (reported per sequence)
        self.cb_entered = 0
        self.cb_exited = 0
        self.frames_in_bypass = 0
        self.frames_in_probe = 0
        self.frame_count = 0

    @property
    def rolling_activation(self):
        if not self._acts:
            return 0.0
        return sum(self._acts) / len(self._acts)

    def _decision(self, phase, run_full, bypass_active, entered_now, exited_now):
        return {
            "cb_enabled": self.enabled,
            "cb_state": self.state,
            "cb_phase": phase,               # "active" | "bypass" | "probe"
            "run_full": run_full,            # caller runs MOG2+gate this frame?
            "cb_bypass_active": bypass_active,  # detector-only this frame?
            "cb_rolling_activation": round(self.rolling_activation, 6),
            "cb_entered_now": entered_now,
            "cb_exited_now": exited_now,
            "cb_bypass_age": self._bypass_age,
        }

    def step(self, activation):
        """Advance the breaker by one frame.

        Parameters
        ----------
        activation : float | int | bool
            The instantaneous activation indicator a_t for a *measured* frame
            (1 if the detector/motion was active, else 0). Only meaningful on
            ACTIVE or PROBE frames; the value passed on pure-bypass frames is
            ignored for the exit decision (the detector runs unconditionally
            there, so it carries no information about whether motion subsided).

        Returns
        -------
        dict
            Keys: ``cb_state`` (ACTIVE/BYPASS), ``cb_phase``
            (active/bypass/probe), ``run_full`` (bool — run MOG2+gate),
            ``cb_bypass_active`` (bool — detector-only), ``cb_rolling_activation``,
            ``cb_entered_now``, ``cb_exited_now``, ``cb_bypass_age``.
        """
        self.frame_count += 1
        a = 1.0 if bool(activation) else 0.0

        # Inert when disabled: always full processing, never bypass.
        if not self.enabled:
            self._acts.append(a)
            return self._decision("active", True, False, False, False)

        if self.state == self.ACTIVE:
            self._acts.append(a)
            # ENTER: rolling activation over a full window exceeds theta_high.
            if len(self._acts) >= self.window and self.rolling_activation > self.theta_high:
                self.state = self.BYPASS
                self._bypass_age = 0
                self._in_probe = False
                self._probe_acts = []
                self.cb_entered += 1
                self.frames_in_bypass += 1
                return self._decision("bypass", False, True, True, False)
            return self._decision("active", True, False, False, False)

        # ---- state == BYPASS ----
        self._bypass_age += 1

        # Schedule a probe every K frames of bypass.
        if not self._in_probe and self._bypass_age % self.probe_every == 0:
            self._in_probe = True
            self._probe_left = self.probe_len
            self._probe_acts = []

        if self._in_probe:
            # PROBE frame: gate is re-enabled (run_full), activation is measured.
            self._probe_acts.append(a)
            self.frames_in_probe += 1
            self._probe_left -= 1
            if self._probe_left <= 0:
                probe_rate = (
                    sum(self._probe_acts) / len(self._probe_acts)
                    if self._probe_acts else 0.0
                )
                self._in_probe = False
                if probe_rate < self.theta_low:
                    # EXIT bypass; reseed the rolling window with the low probe
                    # activations so the breaker does not immediately re-enter.
                    self.state = self.ACTIVE
                    self.cb_exited += 1
                    self._acts = deque(self._probe_acts[-self.window:], maxlen=self.window)
                    self._bypass_age = 0
                    return self._decision("active", True, False, False, True)
            return self._decision("probe", True, False, False, False)

        # Pure BYPASS frame: detector-only, MOG2+gate skipped.
        self.frames_in_bypass += 1
        return self._decision("bypass", False, True, False, False)

    def stats(self):
        """Return per-sequence summary counters."""
        return {
            "cb_enabled": self.enabled,
            "cb_entered": self.cb_entered,
            "cb_exited": self.cb_exited,
            "cb_frames_in_bypass": self.frames_in_bypass,
            "cb_frames_in_probe": self.frames_in_probe,
            "cb_frames_total": self.frame_count,
            "cb_bypass_fraction": round(self.frames_in_bypass / self.frame_count, 6)
            if self.frame_count else 0.0,
        }
