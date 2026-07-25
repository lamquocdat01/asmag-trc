"""
E3 — learned-policy baselines under identical conditions  [Reviewer R2.1]

Five "when-to-detect" policies compared on a common CDnet subset with the SAME
10-dim features, the SAME event-availability simulator (W=7 staleness), and the
SAME cost/energy model — an apples-to-apples comparison:

  P1                 detector on every frame (upper bound; no skipping)
  Periodic@matched   detect every N frames, N per-video to match GUARDED activation
  FrameHopper-style  tabular Q-learning on discretized change features, skip length
                     {0,1,2,4,8}, OFFLINE-trained on the first 30% of each video's ROI
                     (uses GT during training only), then deployed without GT
  DQN-gate           the trained DQN mode-selector (fair_dqn_lam0.20), 10-dim features
  GUARDED            deterministic motion-gate + forced periodic refresh (the paper's
                     mechanism) — NO training, NO ground truth at decision time

Reuses the AwP asmag_core + reward simulator + trained DQN policy (already validated).
Metrics: activation, Event F1, event_recall (detection-availability = safety),
unprotected event FNs, energy, training requirement.

Run:  python src/baselines/e3_compare.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AWP = Path(r"D:/PhD Program/02. Working/03_AwP_Frame_Scheduling/AwP-frame-scheduling-public/gates")
sys.path.insert(0, str(AWP))
from rl.reward_simulator import simulate            # noqa: E402
from rl.rl_gate import DQNGate                       # noqa: E402
from asmag_core.controllers import ACTION_TO_INDEX   # noqa: E402  FAST=0 ACC=1 P3_FALLBACK=2

FEAT = AWP / "data" / "features"
TRAIN_STATS = FEAT / "train_stats.json"
DQN_DIR = AWP / "outputs" / "rl" / "t4b"
DQN_NAME = "fair_dqn_lam0.20_seed0"
LAMBDA, W, P_MISS = 0.20, 7, 1.0
MD_COL = 0  # motion_density_mean
REFRESH = 10  # GUARDED forced-refresh period (frames)

OUT = Path(__file__).resolve().parents[2] / "outputs" / "revision_jsa" / "e3_learned_baseline"
OUT.mkdir(parents=True, exist_ok=True)

SUBSET = [
    "baseline/highway", "baseline/office",
    "dynamicBackground/canoe", "dynamicBackground/fountain02",
    "nightVideos/bridgeEntry", "nightVideos/busyBoulvard",
    "badWeather/snowFall", "badWeather/blizzard",
    "cameraJitter/traffic", "thermal/lakeSide",
    "turbulence/turbulence2", "PTZ/continuousPan",
]


def _episode(npz, *, yolo=None, actions=None):
    T = len(npz["temporal_roi"])
    if actions is not None:
        ep = simulate(npz, np.asarray(actions, int), LAMBDA, P_MISS, W)["episode"]
    else:
        ep = simulate(npz, np.ones(T, int), LAMBDA, P_MISS, W, yolo_called_sequence=yolo)["episode"]
    return {"activation": float(ep["activation"]), "event_f1": float(ep["event_f1"]),
            "event_recall": float(ep["event_recall"]), "event_fn": int(ep["event_fn"]),
            "energy": float(ep["energy"])}


def guarded_seq(md, T, tau):
    idx = np.arange(T)
    return ((md > tau) | (idx % REFRESH == 0)).astype(int)


def framehopper_seq(feats, roi, gt, skips=(0, 1, 2, 4, 8), n_bins=6, episodes=80, seed=0):
    """Tabular Q-learning; offline-trained on first 30% of ROI (GT used in training only)."""
    rng = np.random.default_rng(seed)
    md = feats[:, MD_COL]
    roi_idx = np.where(roi)[0]
    if len(roi_idx) < 20:
        return np.ones(len(feats), int)
    edges = np.quantile(md[roi_idx], np.linspace(0, 1, n_bins + 1)[1:-1])
    def st(i):
        return int(np.digitize(md[i], edges))
    train = roi_idx[: max(2, int(0.30 * len(roi_idx)))]
    Q = np.zeros((n_bins, len(skips)))
    alpha, gamma, eps = 0.3, 0.9, 0.2
    for _ in range(episodes):
        k = 0
        while k < len(train) - 1:
            i = train[k]; s = st(i)
            a = rng.integers(len(skips)) if rng.random() < eps else int(np.argmax(Q[s]))
            skip = skips[a]
            skipped = train[k + 1: k + 1 + skip]
            r = 1.0 - LAMBDA                       # detect this frame, pay cost
            if len(skipped) and gt[skipped].any():
                r -= P_MISS                        # a skip that hides an active event
            else:
                r += 0.05 * skip                   # reward efficient skipping in quiet
            k2 = min(k + 1 + skip, len(train) - 1)
            Q[s, a] += alpha * (r + gamma * np.max(Q[st(train[k2])]) - Q[s, a])
            k = k2
    # greedy deployment over the whole video (no GT)
    y = np.zeros(len(feats), int)
    i = 0
    while i < len(feats):
        y[i] = 1
        i += 1 + skips[int(np.argmax(Q[st(i)]))]
    return y


def dqn_actions(feats):
    gate = DQNGate.from_config(DQN_NAME, DQN_DIR, TRAIN_STATS, lambda_cost=LAMBDA)
    gate.reset()
    modes = gate.predict(feats.astype(np.float32))
    return np.array([ACTION_TO_INDEX[m] for m in modes], int)


def run():
    rows = []
    for vid in SUBSET:
        p = FEAT / f"{vid}.npz"
        if not p.exists():
            print(f"[E3] skip (no npz): {vid}")
            continue
        npz = np.load(str(p), allow_pickle=True)
        feats = npz["features"].astype(np.float32)
        roi = npz["temporal_roi"].astype(bool)
        gt = npz["gt_event"].astype(bool)
        T = len(feats)
        md = feats[:, MD_COL]

        tau = float(np.quantile(md[roi], 0.40)) if roi.any() else 0.01
        g = _episode(npz, yolo=guarded_seq(md, T, tau))
        N = max(1, int(round(1.0 / max(g["activation"], 1e-3))))
        seqs = {
            "P1": ("yolo", np.ones(T, int)),
            "Periodic@matched": ("yolo", (np.arange(T) % N == 0).astype(int)),
            "FrameHopper-style": ("yolo", framehopper_seq(feats, roi, gt)),
            "DQN-gate": ("act", dqn_actions(feats)),
            "GUARDED": ("yolo", guarded_seq(md, T, tau)),
        }
        for name, (kind, seq) in seqs.items():
            ep = _episode(npz, actions=seq) if kind == "act" else _episode(npz, yolo=seq)
            rows.append({"video": vid, "method": name, **{k: round(v, 4) for k, v in ep.items()}})
        print(f"[E3] {vid}: GUARDED act={g['activation']:.3f} recall={g['event_recall']:.3f}")

    df = pd.DataFrame(rows)
    df.rename(columns={"event_fn": "unprotected_event_fn"}, inplace=True)
    df.to_csv(OUT / "comparison_per_video.csv", index=False)

    TRAIN = {"P1": "none", "Periodic@matched": "none (activation matched offline)",
             "FrameHopper-style": "per-scene Q-learning (offline, first 30%, GT)",
             "DQN-gate": "offline RL training (per feature set)", "GUARDED": "none (deterministic)"}
    agg = df.groupby("method").agg(
        activation=("activation", "mean"), event_f1=("event_f1", "mean"),
        event_recall=("event_recall", "mean"),
        unprotected_event_fn=("unprotected_event_fn", "sum"),
        energy=("energy", "mean")).round(4).reset_index()
    agg["training_required"] = agg["method"].map(TRAIN)
    order = ["P1", "Periodic@matched", "FrameHopper-style", "DQN-gate", "GUARDED"]
    agg = agg.set_index("method").loc[order].reset_index()
    agg.to_csv(OUT / "comparison.csv", index=False)
    print("\n=== E3 aggregate (mean over subset) ===")
    print(agg.to_string(index=False))
    return agg, df


if __name__ == "__main__":
    run()
