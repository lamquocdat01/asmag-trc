"""
E2 sensitivity sweep driver  [Reviewer R3.1, R2.2]

OFAT (one-factor-at-a-time) sweeps of the core gating hyperparameters + input
robustness, on a 12-video representative CDnet subset, running the GUARDED
pipeline at max_frames_per_video=400. Each sweep point writes a temporary config
(inheriting the guarded clean config) and runs the runner as a subprocess.

Resumable: a point whose 12 sequences are already complete is skipped.
Metrics per (sweep, value, video) are appended to sweep_results.csv.

Run from repo root (long — ~2 h):
    python tools/e2_sweep.py
"""
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "revision_jsa" / "e2_sensitivity"
RUNS = OUT / "runs"
TMP_CFG = ROOT / "configs" / "_e2_tmp"
RESULTS = OUT / "sweep_results.csv"
PIPE = "ASMAG_TR_CONTROLLER_ONLINE_GUARDED"
MAX_FRAMES = 400

SUBSET = {
    "baseline": ["highway", "office"],
    "dynamicBackground": ["canoe", "fountain02"],
    "nightVideos": ["bridgeEntry", "streetCornerAtNight"],
    "badWeather": ["snowFall", "blizzard"],
    "cameraJitter": ["traffic"],
    "thermal": ["library"],
    "turbulence": ["turbulence2"],
    "PTZ": ["continuousPan"],
}
N_SEQ = sum(len(v) for v in SUBSET.values())  # 12


def _deep(d):
    return {k: (_deep(v) if isinstance(v, dict) else v) for k, v in d.items()}


# Each sweep: (name, override-builder(value) -> nested cfg dict, values)
SWEEPS = [
    ("tau_fd",        lambda v: {"online_controller_guarded": {"framediff_tau": v}}, [15, 20, 25, 30, 35]),
    ("max_reuse_age", lambda v: {"online_controller_guarded": {"max_reuse_age": v}}, [5, 10, 15, 20]),
    ("open_threshold", lambda v: {"p4_efficient": {"open_threshold_acc": v, "open_threshold_fast": v}}, [0.44, 0.55, 0.66]),
    ("close_threshold", lambda v: {"p4_efficient": {"close_threshold": v}}, [0.24, 0.30, 0.36]),
    ("gate_ratio",    lambda v: {"p4_asmag_plus": {"min_area_ratio": v}}, [0.01, 0.02, 0.04]),
    ("noise_sigma",   lambda v: {"input_perturbation": {"noise_sigma": v}}, [0, 2, 5]),
    ("downscale",     lambda v: {"input_perturbation": {"downscale": v}}, [1.0, 0.75, 0.5]),
]


def point_name(sweep, value):
    return f"{sweep}__{str(value).replace('.', 'p')}"


def build_config(sweep, value):
    override = SWEEPS_BY_NAME[sweep](value)
    cfg = {
        # temp configs live in configs/_e2_tmp/, base resolves one level up
        "base_config": "../full_cdnet2014_guarded_v2_clean.yaml",
        "experiment_name": point_name(sweep, value),
        "output_root": str(RUNS).replace("\\", "/"),
        "resume_existing_results": False,
        "checkpoint_resume": True,
        "categories": list(SUBSET.keys()),
        "videos": {k: list(v) for k, v in SUBSET.items()},
        "evaluation": {"use_temporal_roi": True, "warmup_frames": 50,
                       "frame_step": 1, "max_frames_per_video": MAX_FRAMES},
        "pipelines": [PIPE],
        "circuit_breaker": {"enabled": False},
    }
    cfg.update(override)
    return cfg


SWEEPS_BY_NAME = {name: fn for name, fn, _ in SWEEPS}


def is_complete(name):
    raw = RUNS / name / "raw_results"
    if not raw.exists():
        return False
    done = list(raw.rglob(f"{PIPE}/sequence_event_summary.csv"))
    return len(done) >= N_SEQ


def run_point(sweep, value):
    name = point_name(sweep, value)
    if is_complete(name):
        print(f"[E2] skip (complete): {name}")
        return
    TMP_CFG.mkdir(parents=True, exist_ok=True)
    cfg = build_config(sweep, value)
    cfg_path = TMP_CFG / f"{name}.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    print(f"[E2] running {name} ...", flush=True)
    subprocess.run([sys.executable, "src/run_experiment.py", "--config", str(cfg_path)],
                   cwd=str(ROOT), check=False)


def _mean_bool(series):
    return float(series.map(lambda x: 1.0 if str(x).strip().lower() in ("1", "true", "1.0") else 0.0).mean())


def collect_point(sweep, value):
    name = point_name(sweep, value)
    rows = []
    raw = RUNS / name / "raw_results"
    for fm in raw.rglob(f"{PIPE}/frame_metrics.csv"):
        seq = fm.parent
        video = seq.parent.name
        category = seq.parent.parent.name
        df = pd.read_csv(fm, low_memory=False)
        row = {
            "sweep": sweep, "value": value, "category": category, "video": video,
            "n_frames": len(df),
            "activation": round(float(df["yolo_called"].astype(float).mean()), 5),
            "energy_per_frame": round(float(df["energy_frame"].astype(float).mean()), 5),
            "override_count": int(df["arb_v2_override"].astype(float).sum()) if "arb_v2_override" in df else 0,
        }
        ev = seq / "sequence_event_summary.csv"
        if ev.exists():
            edf = pd.read_csv(ev)
            row["event_f1"] = float(edf["Event_F1"].iloc[0]) if "Event_F1" in edf else None
        px = seq / "sequence_pixel_summary.csv"
        if px.exists():
            pdf = pd.read_csv(px)
            for c in ("CDnet_FMeasure", "FMeasure"):
                if c in pdf.columns:
                    row["fmeasure"] = float(pdf[c].iloc[0])
                    break
        rows.append(row)
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    all_rows = []
    total = sum(len(vals) for _, _, vals in SWEEPS)
    done = 0
    for sweep, _fn, values in SWEEPS:
        for value in values:
            run_point(sweep, value)
            all_rows.extend(collect_point(sweep, value))
            done += 1
            # incremental checkpoint
            pd.DataFrame(all_rows).to_csv(RESULTS, index=False)
            print(f"[E2] {done}/{total} points done ({point_name(sweep, value)}); "
                  f"{len(all_rows)} rows -> {RESULTS}", flush=True)
    print(f"[E2] DONE. {len(all_rows)} rows written to {RESULTS}")


if __name__ == "__main__":
    main()
