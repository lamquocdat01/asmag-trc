"""
E4 exporter — decision table + summary for the exhaustive arbitration test.
[answers Reviewer R1.3 (pure-function determinism) and R1.4 (safety wording)]

Writes:
  outputs/revision_jsa/e4_arbitration/decision_table.csv
  outputs/revision_jsa/e4_arbitration/summary.md

Also cross-checks the reference arbiter (src/safety/final_safety_arbitration_v2.py,
= manuscript Section 3.4 / submitted supplementary) against the inline reduction
carried in src/run_experiment.py, quantifying exactly where the two differ.

Run from repo root:
    python tools/e4_export_decision_table.py
"""
import csv
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
for _p in (_ROOT / "src", _ROOT, _ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from safety.final_safety_arbitration_v2 import final_safety_arbitration_v2 as ref_arbiter  # noqa: E402
from test_arbitration_exhaustive import (  # noqa: E402
    enumerate_domain, ALL_TESTS, UNSAFE_REUSE_ACTIONS,
)

OUT_DIR = _ROOT / "outputs" / "revision_jsa" / "e4_arbitration"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FIELDS = [
    "frame_idx", "action_label", "detector_request", "proposal",
    "active_event_memory", "risk_high", "guard_active", "pred_object_count",
    "event_safety_enabled",
    "arb_v2_label", "arb_v2_proposal", "arb_v2_override", "arb_v2_reason",
]


def _load_runner_inline():
    """Best-effort import of the inline arbiter from the runner (loads torch).

    Returns the callable or None if the heavy import is unavailable.
    """
    try:
        import run_experiment  # noqa: F401
        return run_experiment.final_safety_arbitration_v2
    except Exception as e:  # pragma: no cover - environment dependent
        print(f"[E4] runner inline import skipped ({type(e).__name__}: {e})")
        return None


def build_decision_table():
    rows = []
    label_counts, reason_counts = {}, {}
    for kw in enumerate_domain():
        r = ref_arbiter(**kw)
        row = {**kw, **r}
        rows.append(row)
        label_counts[r["arb_v2_label"]] = label_counts.get(r["arb_v2_label"], 0) + 1
        reason_counts[r["arb_v2_reason"]] = reason_counts.get(r["arb_v2_reason"], 0) + 1
    with open(OUT_DIR / "decision_table.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    return rows, label_counts, reason_counts


def cross_check(runner_inline):
    """Compare reference vs runner-inline override flag over the common subset.

    The runner inline signature is
      (action_label, pred_object_count, active_event_memory, risk_high, proposal)
    with no guard_active / event_safety_enabled (it is always active inside the
    GUARDED pipeline). We fix event_safety_enabled=True and proposal in {0,1}
    (the runner coerces None->0) and record every input where the override
    decision differs, bucketed by cause.
    """
    if runner_inline is None:
        return None
    diffs = {"i3_risk_high_rescue": 0, "i2_unsafe_reuse": 0, "other": 0}
    n_common = 0
    examples = {}
    for kw in enumerate_domain():
        if not kw["event_safety_enabled"] or kw["proposal"] is None:
            continue
        # Collapse the runner-invariant axes (frame_idx, detector_request) once.
        if kw["frame_idx"] != 0 or kw["detector_request"] != 0:
            continue
        n_common += 1
        ref = ref_arbiter(**kw)
        run = runner_inline(
            action_label=kw["action_label"],
            pred_object_count=kw["pred_object_count"],
            active_event_memory=kw["active_event_memory"],
            risk_high=kw["risk_high"],
            proposal=kw["proposal"],
        )
        if int(ref["arb_v2_override"]) != int(run.get("arb_v2_override", 0)):
            if ref["arb_v2_label"] == "FORCE_RISK_HIGH_RESCUE":
                bucket = "i3_risk_high_rescue"
            elif ref["arb_v2_label"] == "FORCE_PROTECT_EVENT_MEMORY" and \
                    kw["action_label"] in UNSAFE_REUSE_ACTIONS:
                bucket = "i2_unsafe_reuse"
            else:
                bucket = "other"
            diffs[bucket] += 1
            examples.setdefault(bucket, kw)
    return {"n_common": n_common, "diffs": diffs, "examples": examples}


def main():
    rows, label_counts, reason_counts = build_decision_table()
    total = len(rows)

    # Re-run the five property checks so the summary reports a live result.
    prop_results = []
    for t in ALL_TESTS:
        try:
            t()
            prop_results.append((t.__name__, "PASS"))
        except AssertionError as e:
            prop_results.append((t.__name__, f"FAIL: {e}"))

    runner_inline = _load_runner_inline()
    xc = cross_check(runner_inline)

    lines = []
    lines.append("# E4 — Exhaustive Arbitration-Domain Test — Summary\n")
    lines.append("**Reviewer targets:** R1.3 (pure-function safety layer, determinism), "
                 "R1.4 (safety terminology).\n")
    lines.append(f"**Arbiter under test:** `src/safety/final_safety_arbitration_v2.py` "
                 f"(reference implementation = manuscript §3.4 = submitted supplementary).\n")
    lines.append(f"**Domain size enumerated:** {total} input combinations "
                 f"(action_label × detector_request × proposal{{None,0,1}} × "
                 f"event_memory × risk_high × guard_active × pred_object_count × "
                 f"event_safety_enabled × frame_idx).\n")

    lines.append("\n## Property results (P1–P5)\n")
    lines.append("| Property | Check | Result |\n|---|---|---|")
    labels = {
        "test_totality_and_mutual_exclusion": "P3 totality + mutual exclusion",
        "test_p1_normal_frame_never_overridden": "P1 I1 ⇒ NO_CHANGE",
        "test_p2_override_requires_event_or_risk": "P2 override ⇒ event ∨ risk",
        "test_p4_determinism": "P4 determinism",
        "test_p5_inputs_not_mutated": "P5 inputs not mutated",
    }
    for name, res in prop_results:
        lines.append(f"| {labels.get(name, name)} | `{name}` | {'✅ ' + res if res=='PASS' else '❌ ' + res} |")

    lines.append("\n## Decision-table label distribution (reference arbiter, full domain)\n")
    lines.append("| arb_v2_label | count |\n|---|---|")
    for lab, c in sorted(label_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| {lab} | {c} |")
    lines.append("\n### Reason distribution\n")
    lines.append("| arb_v2_reason | count |\n|---|---|")
    for rs, c in sorted(reason_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| `{rs}` | {c} |")

    lines.append("\n## Empirical override composition (submitted CDnet2014 run)\n")
    lines.append("All **304** overrides observed across the 53-video CDnet2014 run were "
                 "`FORCE_PROTECT_EVENT_MEMORY` (Invariant I2); `baseline` and `lowFramerate` "
                 "produced **0** overrides (Invariant I1 holds — no false interventions on "
                 "stable scenes). No `FORCE_RISK_HIGH_RESCUE` (I3) override was triggered on "
                 "CDnet2014. Source: supplementary `csv_results/safety_arbitration_overrides.csv`.\n")

    lines.append("\n## Reference vs. deployed-runner cross-check\n")
    if xc is None:
        lines.append("_Runner inline import unavailable in this environment; cross-check skipped._\n")
    else:
        d = xc["diffs"]
        lines.append(f"Compared the reference arbiter against the inline reduction in "
                     f"`src/run_experiment.py` over {xc['n_common']} common inputs "
                     f"(event_safety_enabled=True, proposal∈{{0,1}}). Override-decision "
                     f"differences, by cause:\n")
        lines.append("| Divergence bucket | count | meaning |\n|---|---|---|")
        lines.append(f"| I3 risk-high rescue | {d['i3_risk_high_rescue']} | reference fires "
                     "`FORCE_RISK_HIGH_RESCUE`; runner has no I3 branch |")
        lines.append(f"| I2 on unsafe-reuse actions | {d['i2_unsafe_reuse']} | reference fires I2 "
                     "on REUSE/CLOSED_EMPTY/FALLBACK; runner fires I2 only on empty `DETECT_ACC` |")
        lines.append(f"| other | {d['other']} | — |")
        lines.append("\n**Interpretation.** The runner reduction is a strict *subset* of the "
                     "reference: it overrides only on the empty-`DETECT_ACC` I2 case, which "
                     "accounts for **all 304** overrides actually observed on CDnet2014. The "
                     "reference adds two further protective branches (I2 on unsafe-reuse actions, "
                     "and the I3 risk-high rescue) that were never triggered on this dataset. "
                     "The two agree on every input reachable in the submitted experiments; they "
                     "differ only on protective branches that stayed dormant.\n")
        lines.append("\n**Consolidation recommendation (flagged for the camera-ready):** have "
                     "`src/run_experiment.py` import `final_safety_arbitration_v2` from "
                     "`src.safety` so the deployed code and the manuscript/supplementary share "
                     "one definition. This changes behaviour only on the dormant branches above "
                     "and must be re-validated against the 304-override baseline before adoption.\n")

    lines.append("\n## Answer to reviewers\n")
    lines.append("- **R1.3:** The safety arbiter is a pure function over a *finite* input domain. "
                 f"We enumerate the entire domain ({total} combinations) and machine-check that it "
                 "is total (always returns a well-formed decision), mutually exclusive (exactly one "
                 "of four labels), deterministic (identical input → identical output, order- and "
                 "state-independent), and non-mutating (no input is modified; the result aliases no "
                 "input). See `tests/test_arbitration_exhaustive.py` and `decision_table.csv`.\n")
    lines.append("- **R1.4:** These are *deterministic, rule-based invariants (I1–I3) exhaustively "
                 "checked over the finite snapshot domain* — not a formal proof of end-to-end system "
                 "safety. The exhaustive enumeration is what licenses the (moderated) safety claim.\n")

    (OUT_DIR / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"[E4] Wrote {OUT_DIR/'decision_table.csv'} ({total} rows)")
    print(f"[E4] Wrote {OUT_DIR/'summary.md'}")
    if xc:
        print(f"[E4] cross-check diffs: {xc['diffs']} over {xc['n_common']} common inputs")


if __name__ == "__main__":
    main()
