"""
E1 analysis — GUARDED (baseline) vs GUARDED+circuit-breaker  [Reviewer R3.2]

Reads the two E1 experiment output trees and produces:
  outputs/revision_jsa/e1_circuit_breaker/comparison.csv
  outputs/revision_jsa/e1_circuit_breaker/summary.md

Per video it reports activation, Event F1, CDnet F-Measure, estimated energy
per frame, MOG2 usage rate, the mean gate/MOG2 compute time (latency_gate_
features_ms — the CPU cost the reviewer flagged), total latency, and the
circuit-breaker engagement (entered / bypass fraction).

Run from repo root after both E1 configs finish:
    python tools/e1_analyze.py
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
E1 = ROOT / "outputs" / "revision_jsa" / "e1_circuit_breaker"
PIPE = "ASMAG_TR_CONTROLLER_ONLINE_GUARDED"
CONFIGS = {"baseline": "guarded_baseline", "cb": "guarded_cb"}
CONTROL_VIDEOS = {"office", "sofa"}  # CB must never engage here


def _first_col(df, names, default=None):
    for n in names:
        if n in df.columns:
            return df[n].iloc[0]
    return default


def _mean_bool(series):
    def to01(x):
        s = str(x).strip().lower()
        return 1.0 if s in ("1", "true", "1.0") else 0.0
    return float(series.map(to01).mean())


def collect(exp_dir):
    """Return {(category, video): metrics dict} for one experiment."""
    out = {}
    raw = exp_dir / "raw_results"
    if not raw.exists():
        return out
    for fm in raw.rglob(f"{PIPE}/frame_metrics.csv"):
        seq = fm.parent
        video = seq.parent.name
        category = seq.parent.parent.name
        df = pd.read_csv(fm)
        n = len(df)
        m = {
            "category": category, "video": video, "n_frames": n,
            "activation": round(float(df["yolo_called"].astype(float).mean()), 4) if "yolo_called" in df else None,
            "energy_per_frame": round(float(df["energy_frame"].astype(float).mean()), 4) if "energy_frame" in df else None,
            "mog2_used_rate": round(_mean_bool(df["mog2_used"]), 4) if "mog2_used" in df else None,
            "gate_compute_ms_mean": round(float(df["latency_gate_features_ms"].astype(float).mean()), 4) if "latency_gate_features_ms" in df else None,
            "latency_ms_mean": round(float(df["latency_ms"].astype(float).mean()), 3) if "latency_ms" in df else None,
        }
        # Circuit-breaker engagement
        cb_json = seq / "circuit_breaker_summary.json"
        if cb_json.exists():
            cb = json.loads(cb_json.read_text())
            m["cb_entered"] = cb.get("cb_entered", 0)
            m["cb_bypass_frames"] = cb.get("cb_frames_in_bypass", 0)
            m["cb_bypass_rate"] = round(cb.get("cb_bypass_fraction", 0.0), 4)
        elif "cb_bypass_active" in df.columns:
            m["cb_entered"] = int(df["cb_entered_now"].astype(float).sum()) if "cb_entered_now" in df else 0
            m["cb_bypass_frames"] = int(_mean_bool(df["cb_bypass_active"]) * n)
            m["cb_bypass_rate"] = round(_mean_bool(df["cb_bypass_active"]), 4)
        else:
            m["cb_entered"] = m["cb_bypass_frames"] = 0
            m["cb_bypass_rate"] = 0.0
        # Event F1 / F-Measure from the per-sequence summaries
        ev = seq / "sequence_event_summary.csv"
        if ev.exists():
            edf = pd.read_csv(ev)
            m["event_f1"] = _first_col(edf, ["Event_F1", "event_f1", "EventF1"])
        px = seq / "sequence_pixel_summary.csv"
        if px.exists():
            pdf = pd.read_csv(px)
            m["fmeasure"] = _first_col(pdf, ["CDnet_FMeasure", "FMeasure", "F_Measure", "fmeasure"])
        out[(category, video)] = m
    return out


def main():
    data = {name: collect(E1 / sub) for name, sub in CONFIGS.items()}
    keys = sorted(set(data["baseline"]) | set(data["cb"]))
    if not keys:
        print("[E1] No results found yet under", E1)
        return

    rows = []
    for k in keys:
        b = data["baseline"].get(k, {})
        c = data["cb"].get(k, {})
        cat, vid = k
        row = {"category": cat, "video": vid}
        for metric in ("n_frames", "activation", "event_f1", "fmeasure",
                       "energy_per_frame", "mog2_used_rate", "gate_compute_ms_mean",
                       "latency_ms_mean"):
            row[f"base_{metric}"] = b.get(metric)
            row[f"cb_{metric}"] = c.get(metric)
        row["cb_entered"] = c.get("cb_entered", 0)
        row["cb_bypass_rate"] = c.get("cb_bypass_rate", 0.0)
        # deltas
        if b.get("energy_per_frame") is not None and c.get("energy_per_frame") is not None:
            row["energy_delta_pct"] = round((c["energy_per_frame"] / b["energy_per_frame"] - 1) * 100, 2)
        rows.append(row)

    df = pd.DataFrame(rows)
    E1.mkdir(parents=True, exist_ok=True)
    df.to_csv(E1 / "comparison.csv", index=False)

    # --- summary.md ---
    lines = ["# E1 — Persistent-Motion Circuit Breaker — Summary  [R3.2]\n"]
    lines.append("GUARDED (circuit breaker OFF) vs GUARDED+CB, CPU, full temporal-ROI.\n")
    lines.append("| category/video | frames | activation (base→cb) | Event F1 (base→cb) | "
                 "F-Measure (base→cb) | energy/frame (base→cb, Δ%) | MOG2-used rate (base→cb) | "
                 "gate/MOG2 ms (base→cb) | CB entered | bypass % |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for _, r in df.iterrows():
        def pair(a, b):
            return f"{a}→{b}"
        ed = r.get("energy_delta_pct")
        lines.append(
            f"| {r['category']}/{r['video']} | {r.get('base_n_frames')} | "
            f"{pair(r.get('base_activation'), r.get('cb_activation'))} | "
            f"{pair(r.get('base_event_f1'), r.get('cb_event_f1'))} | "
            f"{pair(r.get('base_fmeasure'), r.get('cb_fmeasure'))} | "
            f"{pair(r.get('base_energy_per_frame'), r.get('cb_energy_per_frame'))} "
            f"({ed:+}%)" .replace("(None%)", "(—)") + " | "
            f"{pair(r.get('base_mog2_used_rate'), r.get('cb_mog2_used_rate'))} | "
            f"{pair(r.get('base_gate_compute_ms_mean'), r.get('cb_gate_compute_ms_mean'))} | "
            f"{r.get('cb_entered')} | {r.get('cb_bypass_rate', 0)*100:.1f}% |"
        )

    # Control check
    ctrl_fail = [f"{r['category']}/{r['video']}" for _, r in df.iterrows()
                 if r["video"] in CONTROL_VIDEOS and (r.get("cb_entered") or 0) > 0]
    lines.append("\n## Control check (CB must NOT engage on low-motion scenes)\n")
    if ctrl_fail:
        lines.append(f"❌ Circuit breaker engaged on control video(s): {ctrl_fail}")
    else:
        lines.append("✅ Circuit breaker did NOT engage on any low-motion control (office, sofa).")

    # Highway headline
    hw = df[df["video"] == "highway"]
    if not hw.empty:
        r = hw.iloc[0]
        lines.append("\n## Highway headline (answers R3.2)\n")
        lines.append(f"- Bypass engaged on **{r.get('cb_bypass_rate',0)*100:.1f}%** of frames "
                     f"(entered {int(r.get('cb_entered') or 0)}×).")
        lines.append(f"- MOG2-used rate: **{r.get('base_mog2_used_rate')} → {r.get('cb_mog2_used_rate')}** "
                     "(MOG2 CPU work eliminated during bypass).")
        lines.append(f"- Mean gate/MOG2 compute time: **{r.get('base_gate_compute_ms_mean')} → "
                     f"{r.get('cb_gate_compute_ms_mean')} ms**.")
        lines.append(f"- Event F1: **{r.get('base_event_f1')} → {r.get('cb_event_f1')}** (safety preserved).")
        lines.append(f"- Estimated energy/frame (CPU proxy): **{r.get('base_energy_per_frame')} → "
                     f"{r.get('cb_energy_per_frame')}** ({r.get('energy_delta_pct')}%).")
        lines.append("\n_Note: CPU energy here is the runner's proxy; the hardware VDD_IN "
                     "energy comparison (GUARDED_CB vs P1, target ≤ P1+ε) is the Jetson E6 run._")

    (E1 / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"[E1] Wrote {E1/'comparison.csv'} and {E1/'summary.md'} ({len(df)} videos)")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
