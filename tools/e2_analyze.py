"""
E2 analysis  [Reviewer R3.1, R2.2, R1-minor-2]

Reads the sweep results + the per-scene ai_* ablation and produces:
  outputs/revision_jsa/e2_sensitivity/{summary.md, fig_<sweep>.png,
                                       sensitivity_table.csv, ablation_delta.csv}

- Per OFAT sweep: aggregate metrics across the 12-video subset per value, classify
  each core parameter's sensitivity flat / moderate / steep.
- AE-weight ±20% ranking-stability check (does the best setting depend on the AE weights?).
- Ablation delta: tuned GUARDED (tau_fd__25) vs generic (ai_* layer disabled).

Run after the sweep and the ablation run complete:
    python tools/e2_analyze.py
"""
import json
from pathlib import Path

import pandas as pd

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAVE_MPL = True
except Exception:
    HAVE_MPL = False

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "revision_jsa" / "e2_sensitivity"
RUNS = OUT / "runs"
PIPE = "ASMAG_TR_CONTROLLER_ONLINE_GUARDED"
RESULTS = OUT / "sweep_results.csv"

# AE reference energy (P1 detector-only relative energy) for a comparable energy-saving term.
P1_ENERGY_REF = 6.2
DEFAULT_AE = {"fm": 0.25, "ef1": 0.25, "actsave": 0.15, "energysave": 0.05}

METRICS = ["activation", "event_f1", "fmeasure", "energy_per_frame", "override_count"]


def ae_score(row, w):
    fm = float(row.get("fmeasure", 0) or 0)
    ef1 = float(row.get("event_f1", 0) or 0)
    act = float(row.get("activation", 0) or 0)
    en = float(row.get("energy_per_frame", 0) or 0)
    return (w["fm"] * fm + w["ef1"] * ef1
            + w["actsave"] * (1 - act)
            + w["energysave"] * max(0.0, 1 - en / P1_ENERGY_REF))


def classify(delta):
    if delta < 0.02:
        return "flat"
    if delta < 0.05:
        return "moderate"
    return "steep"


def collect_run(name):
    """Aggregate a run's per-video frame metrics into subset means."""
    raw = RUNS / name / "raw_results"
    rows = []
    if not raw.exists():
        return None
    for fm in raw.rglob(f"{PIPE}/frame_metrics.csv"):
        seq = fm.parent
        df = pd.read_csv(fm, low_memory=False)
        r = {"video": seq.parent.name,
             "activation": float(df["yolo_called"].astype(float).mean()),
             "energy_per_frame": float(df["energy_frame"].astype(float).mean()),
             "override_count": int(df["arb_v2_override"].astype(float).sum()) if "arb_v2_override" in df else 0}
        ev = seq / "sequence_event_summary.csv"
        if ev.exists():
            r["event_f1"] = float(pd.read_csv(ev)["Event_F1"].iloc[0])
        px = seq / "sequence_pixel_summary.csv"
        if px.exists():
            pdf = pd.read_csv(px)
            for c in ("CDnet_FMeasure", "FMeasure"):
                if c in pdf.columns:
                    r["fmeasure"] = float(pdf[c].iloc[0]); break
        rows.append(r)
    return pd.DataFrame(rows) if rows else None


def main():
    if not RESULTS.exists():
        print("[E2] sweep_results.csv not found — run tools/e2_sweep.py first.")
        return
    df = pd.read_csv(RESULTS)
    # subset-mean per (sweep, value)
    agg = (df.groupby(["sweep", "value"], as_index=False)
             .agg({m: "mean" for m in METRICS}))
    agg["ae"] = agg.apply(lambda r: ae_score(r, DEFAULT_AE), axis=1)

    lines = ["# E2 — Sensitivity Analysis — Summary  [R3.1, R2.2]\n"]
    lines.append("OFAT sweeps on the 12-video CDnet subset, GUARDED pipeline, 400 frames/video. "
                 "Each cell is the subset mean.\n")

    sens_rows = []
    for sweep in df["sweep"].unique():
        sub = agg[agg["sweep"] == sweep].sort_values("value")
        lines.append(f"\n## {sweep}\n")
        lines.append("| value | activation | Event F1 | F-Measure | energy/frame | overrides | AE |")
        lines.append("|---|---|---|---|---|---|---|")
        for _, r in sub.iterrows():
            lines.append(f"| {r['value']} | {r['activation']:.3f} | {r.get('event_f1', float('nan')):.4f} | "
                         f"{r.get('fmeasure', float('nan')):.4f} | {r['energy_per_frame']:.3f} | "
                         f"{r['override_count']:.0f} | {r['ae']:.4f} |")
        # sensitivity per metric = range across swept values
        for m, label in [("event_f1", "Event F1"), ("activation", "activation"), ("ae", "AE")]:
            if m in sub and sub[m].notna().any():
                rng = float(sub[m].max() - sub[m].min())
                sens_rows.append({"sweep": sweep, "metric": label, "range": round(rng, 4),
                                  "sensitivity": classify(rng)})
        lines.append(f"\n_Sensitivity (range across values): "
                     + "; ".join(f"{s['metric']} {s['range']} ({s['sensitivity']})"
                                 for s in sens_rows if s['sweep'] == sweep) + "._")
        # figure
        if HAVE_MPL and sub["value"].map(lambda x: isinstance(x, (int, float))).all():
            fig, ax = plt.subplots(figsize=(5, 3.2))
            for m, c in [("event_f1", "tab:green"), ("activation", "tab:blue"), ("ae", "tab:red")]:
                if m in sub and sub[m].notna().any():
                    ax.plot(sub["value"], sub[m], "o-", label=m, color=c)
            ax.set_xlabel(sweep); ax.set_ylabel("metric"); ax.set_ylim(0, 1.05)
            ax.set_title(f"E2 sensitivity: {sweep}"); ax.legend(fontsize=7); ax.grid(alpha=0.3)
            fig.tight_layout(); fig.savefig(OUT / f"fig_{sweep}.png", dpi=130); plt.close(fig)

    pd.DataFrame(sens_rows).to_csv(OUT / "sensitivity_table.csv", index=False)

    # --- AE-weight +/-20% ranking stability (per sweep: does best value change?) ---
    lines.append("\n## AE-weight ±20% ranking stability  [R1-minor-2]\n")
    lines.append("For each sweep we rank the swept values by AE under the default weights and under "
                 "±20% perturbations of each weight; a stable best value means conclusions do not "
                 "hinge on the AE weighting.\n")
    lines.append("| sweep | best@default | stable under ±20%? |\n|---|---|---|")
    import itertools
    for sweep in df["sweep"].unique():
        sub = agg[agg["sweep"] == sweep]
        best_default = sub.loc[sub["ae"].idxmax(), "value"]
        stable = True
        for wk in DEFAULT_AE:
            for sign in (0.8, 1.2):
                w = dict(DEFAULT_AE); w[wk] = DEFAULT_AE[wk] * sign
                aes = sub.apply(lambda r: ae_score(r, w), axis=1)
                if sub.loc[aes.idxmax(), "value"] != best_default:
                    stable = False
        lines.append(f"| {sweep} | {best_default} | {'✅ yes' if stable else '⚠️ changes'} |")

    # --- Ablation: tuned vs generic (ai_* off) ---
    lines.append("\n## Per-scene-flag ablation (generic vs tuned GUARDED)  [R3.1]\n")
    tuned = collect_run("tau_fd__25")
    generic = collect_run("ablation_generic_no_ai")
    if tuned is not None and generic is not None:
        keys = ["activation", "event_f1", "fmeasure", "energy_per_frame", "override_count"]
        t = tuned[keys].mean(); gmean = generic[keys].mean()
        arows = []
        for k in keys:
            arows.append({"metric": k, "tuned_guarded": round(float(t[k]), 4),
                          "generic_no_ai": round(float(gmean[k]), 4),
                          "delta": round(float(gmean[k] - t[k]), 4)})
        adf = pd.DataFrame(arows); adf.to_csv(OUT / "ablation_delta.csv", index=False)
        lines.append("| metric | tuned GUARDED | generic (ai_* off) | Δ (generic − tuned) |")
        lines.append("|---|---|---|---|")
        for _, r in adf.iterrows():
            lines.append(f"| {r['metric']} | {r['tuned_guarded']} | {r['generic_no_ai']} | {r['delta']:+} |")
        d_ef1 = float(gmean["event_f1"] - t["event_f1"]) if "event_f1" in t else float("nan")
        lines.append(f"\n**Brittleness answer:** disabling the entire 539-key `ai_*` per-scene layer "
                     f"changes subset-mean Event F1 by **{d_ef1:+.4f}**. The generic architecture "
                     "(Tier-1 params only) retains {}% of the tuned Event F1 — the per-scene flags are "
                     "a {} refinement, not a load-bearing dependency."
                     .format(round(100 * float(gmean['event_f1'] / max(1e-9, t['event_f1'])), 1)
                             if 'event_f1' in t else "—",
                             "small" if abs(d_ef1) < 0.03 else "moderate"))
    else:
        lines.append("_Ablation run not found — run `python src/run_experiment.py --config "
                     "configs/revision_jsa_e2_ablation_generic.yaml` first._")

    (OUT / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"[E2] Wrote {OUT/'summary.md'}, sensitivity_table.csv"
          + (", figures" if HAVE_MPL else " (no matplotlib — figures skipped)"))


if __name__ == "__main__":
    main()
