#!/usr/bin/env python
"""Post-hoc budgeted drift simulation for Phase 8C event/foreground risks."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from train_phase8c_event_foreground_risk import GUARDED_PIPELINE, read_existing_columns


SMOKE_ROOT = Path("outputs/asmag_tr_controller_online_guarded_cdnet_smoke")
EVENT_ROOT = Path("outputs/phase8c_event_foreground_risk")
SUBRISK_TUNING_ROOT = Path("outputs/phase8c_subrisk_models/threshold_tuning")

HARD_VIDEOS = {
    "continuousPan",
    "twoPositionPTZCam",
    "bridgeEntry",
    "cubicle",
    "fountain02",
    "turbulence2",
    "tramCrossroad_1fps",
}

USECOLS = [
    "category",
    "video",
    "pipeline",
    "frame_id",
    "raw_frame_id",
    "evaluated_index",
    "action_label",
    "closed_empty_blocked_final",
    "reuse_blocked_final",
    "lightweight_blocked_final",
    "ptz_closed_empty_kill_active",
    "closed_empty_blocked_under_ptz",
    "ai_closed_empty_risk_score",
    "ai_reuse_risk_score",
    "ai_lightweight_p3_risk_score",
    "ai_legacy_cadence_risk_score",
    "ai_detector_needed_score",
]

SUBRISK_THRESHOLDS = {
    "closed_empty_risk": 0.9999,
    "reuse_risk": 0.9999,
    "lightweight_p3_risk": 0.99,
    "legacy_cadence_risk": 0.99,
    "detector_needed": 0.99,
}


@dataclass(frozen=True)
class Budget:
    name: str
    max_detector_requests_per_100_frames: int
    min_detector_interval_frames: int
    max_reuse_blocks_per_100_frames: int
    max_lightweight_blocks_per_100_frames: int
    event_override_budget: int
    ptz_override_budget: int


BUDGETS = [
    Budget("conservative", 12, 8, 8, 3, 10, 12),
    Budget("balanced", 30, 3, 25, 8, 45, 45),
    Budget("aggressive", 80, 1, 40, 15, 100, 100),
]


def read_guarded_frames(root: Path) -> pd.DataFrame:
    frames = []
    for path in sorted(root.glob(f"raw_results/*/*/{GUARDED_PIPELINE}/frame_metrics.csv")):
        existing = set(read_existing_columns(path))
        cols = [col for col in USECOLS if col in existing]
        if cols:
            frames.append(pd.read_csv(path, usecols=cols, low_memory=False))
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    for col in USECOLS:
        if col not in df.columns:
            df[col] = 0
    for col in df.columns:
        if col in {"category", "video", "pipeline", "action_label"}:
            df[col] = df[col].fillna("").astype(str)
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df["known_guarded_safety_event"] = (
        df["closed_empty_blocked_final"].gt(0)
        | df["reuse_blocked_final"].gt(0)
        | df["lightweight_blocked_final"].gt(0)
        | df["ptz_closed_empty_kill_active"].gt(0)
        | df["closed_empty_blocked_under_ptz"].gt(0)
    )
    df["known_hard_video"] = df["video"].isin(HARD_VIDEOS)
    df["normal_frame"] = ~df["known_guarded_safety_event"]
    return df


def load_event_scores(event_root: Path) -> tuple[pd.DataFrame, dict[str, float]]:
    scores = pd.read_csv(event_root / "event_foreground_frame_scores.csv")
    recs = pd.read_csv(event_root / "event_foreground_runtime_recommendation.csv")
    thresholds = {
        str(row["target"]): float(row["recommended_threshold"])
        for _, row in recs.iterrows()
    }
    return scores, thresholds


def merge_scores(frames: pd.DataFrame, scores: pd.DataFrame) -> pd.DataFrame:
    key = ["category", "video", "frame_id", "raw_frame_id", "evaluated_index"]
    score_cols = [col for col in scores.columns if col.endswith("_score") or col.endswith("_pred")]
    return frames.merge(scores[key + score_cols], on=key, how="left")


def risk_flags(df: pd.DataFrame, event_thresholds: dict[str, float]) -> pd.DataFrame:
    flags = pd.DataFrame(index=df.index)
    flags["closed_empty_risk"] = df["ai_closed_empty_risk_score"].ge(SUBRISK_THRESHOLDS["closed_empty_risk"])
    flags["reuse_risk"] = df["ai_reuse_risk_score"].ge(SUBRISK_THRESHOLDS["reuse_risk"])
    flags["lightweight_p3_risk"] = df["ai_lightweight_p3_risk_score"].ge(SUBRISK_THRESHOLDS["lightweight_p3_risk"])
    flags["legacy_cadence_risk"] = df["ai_legacy_cadence_risk_score"].ge(SUBRISK_THRESHOLDS["legacy_cadence_risk"])
    flags["detector_needed"] = df["ai_detector_needed_score"].ge(SUBRISK_THRESHOLDS["detector_needed"])
    for target, threshold in event_thresholds.items():
        col = f"{target}_score"
        flags[target] = df[col].fillna(0.0).ge(threshold) if col in df.columns else False
    flags["event_any"] = flags[[
        "event_foreground_risk",
        "foreground_loss_risk",
        "event_continuity_risk",
        "detector_refresh_needed_for_event",
    ]].any(axis=1)
    flags["subrisk_any"] = flags[[
        "closed_empty_risk",
        "reuse_risk",
        "lightweight_p3_risk",
        "legacy_cadence_risk",
    ]].any(axis=1)
    flags["ai_risk_high"] = flags["event_any"] | flags["subrisk_any"] | flags["detector_needed"]
    return flags


def simulate_budget(df: pd.DataFrame, flags: pd.DataFrame, budget: Budget) -> pd.DataFrame:
    rows = []
    for (_, video), group in df.groupby(["category", "video"], sort=False):
        detector_used = reuse_used = lightweight_used = event_used = ptz_used = 0
        last_detector_eval = -10**9
        for idx, row in group.sort_values("evaluated_index").iterrows():
            action = str(row["action_label"])
            deterministic = bool(row["known_guarded_safety_event"])
            high = bool(flags.at[idx, "ai_risk_high"])
            is_ptz = row["category"] == "PTZ"
            allowed = deterministic and high
            kinds = []
            detector_request = False
            block_reuse = False
            block_lightweight = False
            block_closed_empty = False
            block_legacy = False
            if allowed:
                eval_idx = int(row["evaluated_index"])
                event_ok = event_used < budget.event_override_budget
                ptz_ok = (not is_ptz) or ptz_used < budget.ptz_override_budget
                if event_ok and ptz_ok:
                    if (
                        (flags.at[idx, "detector_needed"] or flags.at[idx, "detector_refresh_needed_for_event"] or flags.at[idx, "event_foreground_risk"])
                        and detector_used < budget.max_detector_requests_per_100_frames
                        and eval_idx - last_detector_eval >= budget.min_detector_interval_frames
                    ):
                        detector_request = True
                        detector_used += 1
                        last_detector_eval = eval_idx
                        kinds.append("request_detector")
                    if "REUSE" in action and flags.at[idx, "reuse_risk"] and reuse_used < budget.max_reuse_blocks_per_100_frames:
                        block_reuse = True
                        reuse_used += 1
                        kinds.append("block_reuse")
                    if action == "LIGHTWEIGHT_MASK_P3_FALLBACK" and flags.at[idx, "lightweight_p3_risk"] and lightweight_used < budget.max_lightweight_blocks_per_100_frames:
                        block_lightweight = True
                        lightweight_used += 1
                        kinds.append("block_lightweight_p3")
                    if action == "CLOSED_EMPTY" and (flags.at[idx, "closed_empty_risk"] or flags.at[idx, "event_foreground_risk"]):
                        block_closed_empty = True
                        kinds.append("block_closed_empty")
                    if action == "LEGACY_SAFE_P3_GUARD" and flags.at[idx, "legacy_cadence_risk"]:
                        block_legacy = True
                        kinds.append("block_legacy_cadence")
                    if kinds:
                        event_used += 1
                        if is_ptz:
                            ptz_used += 1
            intervention = bool(kinds)
            rows.append({
                "budget": budget.name,
                "category": row["category"],
                "video": row["video"],
                "frame_id": int(row["frame_id"]),
                "raw_frame_id": int(row["raw_frame_id"]),
                "evaluated_index": int(row["evaluated_index"]),
                "ai_sim_original_action": action,
                "ai_budget_deterministic_guard_active": int(deterministic),
                "ai_budget_risk_high": int(high),
                "ai_budget_would_intervene": int(intervention),
                "ai_budget_would_request_detector": int(detector_request),
                "ai_budget_would_block_reuse": int(block_reuse),
                "ai_budget_would_block_lightweight": int(block_lightweight),
                "ai_budget_would_block_closed_empty": int(block_closed_empty),
                "ai_budget_would_block_legacy": int(block_legacy),
                "ai_budget_intervention_type": "+".join(kinds) if kinds else "none",
                "ai_budget_recommended_safe_action": "DETECT_ACC" if intervention else action,
                "known_guarded_safety_event": int(row["known_guarded_safety_event"]),
                "known_hard_video": int(row["known_hard_video"]),
                "normal_frame": int(row["normal_frame"]),
            })
    return pd.DataFrame(rows)


def summary_for(sim: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (budget, category, video), group in sim.groupby(["budget", "category", "video"], dropna=False):
        rows.append(summary_row(budget, category, video, group))
    for budget, group in sim.groupby("budget"):
        rows.append(summary_row(budget, "ALL", "ALL", group))
    return pd.DataFrame(rows).sort_values(["budget", "category", "video"])


def summary_row(budget: str, category: str, video: str, group: pd.DataFrame) -> dict:
    intervention = group["ai_budget_would_intervene"].gt(0)
    detector = group["ai_budget_would_request_detector"].gt(0)
    known = group["known_guarded_safety_event"].gt(0)
    hard = group["known_hard_video"].gt(0)
    normal = group["normal_frame"].gt(0)
    hard_known = known & hard
    return {
        "budget": budget,
        "category": category,
        "video": video,
        "frames": int(len(group)),
        "hard_video": bool(hard.any()),
        "simulated_intervention_rate": float(intervention.mean()),
        "detector_request_rate": float(detector.mean()),
        "reuse_block_rate": float(group["ai_budget_would_block_reuse"].mean()),
        "lightweight_block_rate": float(group["ai_budget_would_block_lightweight"].mean()),
        "closed_empty_block_rate": float(group["ai_budget_would_block_closed_empty"].mean()),
        "interventions_on_known_safety_event_frames": int((intervention & known).sum()),
        "interventions_on_normal_frames": int((intervention & normal).sum()),
        "deterministic_guard_alignment_rate": float(group.loc[intervention, "ai_budget_deterministic_guard_active"].mean()) if intervention.any() else 0.0,
        "over_intervention_risk_score": float((intervention & normal).mean()),
        "hard_video_warning_recall_all_frames": float(intervention[hard].mean()) if hard.any() else 0.0,
        "hard_video_known_event_recall": float(intervention[hard_known].mean()) if hard_known.any() else 0.0,
        "cubicle_recall": float(intervention[group["video"].eq("cubicle") & known].mean()) if (group["video"].eq("cubicle") & known).any() else 0.0,
        "bridgeEntry_event_recall": float(intervention[group["video"].eq("bridgeEntry") & known].mean()) if (group["video"].eq("bridgeEntry") & known).any() else 0.0,
        "expected_activation_increase_proxy": float(detector.mean() * 0.60 + group["ai_budget_would_block_reuse"].mean() * 0.15 + group["ai_budget_would_block_lightweight"].mean() * 0.10),
    }


def budget_recommendations(summary: pd.DataFrame) -> pd.DataFrame:
    all_rows = summary[summary["category"].eq("ALL") & summary["video"].eq("ALL")].copy()
    rows = []
    for _, row in all_rows.iterrows():
        passes = (
            row["hard_video_known_event_recall"] >= 0.90
            and row["cubicle_recall"] >= 0.80
            and row["deterministic_guard_alignment_rate"] > 0.2767
            and row["over_intervention_risk_score"] < 0.60125
            and row["simulated_intervention_rate"] <= 0.50
        )
        rows.append({
            "budget": row["budget"],
            "recommended": bool(passes),
            "phase8c2_decision": "candidate_for_limited_intervention_design" if passes else "blocked",
            "hard_video_known_event_recall": row["hard_video_known_event_recall"],
            "cubicle_recall": row["cubicle_recall"],
            "simulated_intervention_rate": row["simulated_intervention_rate"],
            "detector_request_rate": row["detector_request_rate"],
            "deterministic_guard_alignment_rate": row["deterministic_guard_alignment_rate"],
            "over_intervention_risk_score": row["over_intervention_risk_score"],
            "expected_activation_increase_proxy": row["expected_activation_increase_proxy"],
        })
    recs = pd.DataFrame(rows)
    passing = recs[recs["recommended"]]
    if not passing.empty:
        best_idx = passing.sort_values(["simulated_intervention_rate", "detector_request_rate"]).index[0]
        recs.loc[recs.index != best_idx, "recommended"] = False
        recs.loc[recs.index != best_idx, "phase8c2_decision"] = "not_preferred"
    return recs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=SMOKE_ROOT)
    parser.add_argument("--event-root", type=Path, default=EVENT_ROOT)
    args = parser.parse_args()

    frames = read_guarded_frames(args.root)
    if frames.empty:
        raise SystemExit(f"No guarded frame metrics found under {args.root}")
    scores, event_thresholds = load_event_scores(args.event_root)
    df = merge_scores(frames, scores)
    flags = risk_flags(df, event_thresholds)

    sims = [simulate_budget(df, flags, budget) for budget in BUDGETS]
    sim = pd.concat(sims, ignore_index=True)
    summary = summary_for(sim)
    recs = budget_recommendations(summary)

    args.event_root.mkdir(parents=True, exist_ok=True)
    sim.to_csv(args.event_root / "budgeted_drift_simulation.csv", index=False)
    summary.to_csv(args.event_root / "budgeted_drift_summary.csv", index=False)
    recs.to_csv(args.event_root / "budget_recommendations.csv", index=False)

    print(f"[DONE] wrote budgeted drift outputs to {args.event_root}")
    print(recs.to_string(index=False))


if __name__ == "__main__":
    main()
