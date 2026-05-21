import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from tools.compare_asmag_tr_controller_online_guarded import read_per_video  # noqa: E402


GUARDED = "ASMAG_TR_CONTROLLER_ONLINE_GUARDED"
POLICIES = [
    "CP_ANCHOR_EVERY_1",
    "CP_ANCHOR_EVERY_2",
    "CP_ANCHOR_EVERY_3_ACC_INTER",
    "CP_DETECT_ACC_EVERY_2",
    "CP_FALLBACK_P3_EVERY_2",
    "TP_BURST_2_THEN_FAST",
    "TP_BURST_3_THEN_FAST",
    "TP_PHASE6C_ONLY",
    "NONPTZ_TEACHER_OFF",
]
NON_PTZ_VIDEOS = {"bridgeEntry", "cubicle", "fountain02", "turbulence2"}


def p95(series):
    if series.empty:
        return 0.0
    return float(series.quantile(0.95))


def safe_mean(df, col):
    if df.empty or col not in df.columns:
        return 0.0
    return float(pd.to_numeric(df[col], errors="coerce").fillna(0.0).mean())


def safe_sum(df, col):
    if df.empty or col not in df.columns:
        return 0
    return int(pd.to_numeric(df[col], errors="coerce").fillna(0.0).sum())


def read_frames(policy_root):
    raw = policy_root / "raw_results"
    frames = []
    usecols = [
        "category",
        "video",
        "pipeline",
        "action_label",
        "Event_State",
        "latency_ms",
        "FMeasure",
        "teacher_ranker_active",
        "teacher_ranker_behavior_applied",
        "teacher_non_ptz_suppressed",
        "phase7c_ablation_active",
        "phase7c_ablation_policy",
        "phase7c_ablation_action",
        "motion_comp_behavior_applied",
        "geometry_action_selection_active",
        "event_closed_empty_final_count",
    ]
    for path in raw.rglob(f"{GUARDED}/frame_metrics.csv"):
        header = pd.read_csv(path, nrows=0)
        cols = [c for c in usecols if c in header.columns]
        if cols:
            frames.append(pd.read_csv(path, usecols=cols))
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    for col in usecols:
        if col not in df.columns:
            df[col] = 0 if col not in {"category", "video", "pipeline", "action_label", "Event_State", "phase7c_ablation_policy", "phase7c_ablation_action"} else ""
    return df


def video_metric(per_video, video):
    rows = per_video[
        (per_video["Pipeline"].astype(str) == GUARDED)
        & (per_video["video"].astype(str) == video)
    ]
    if rows.empty:
        return {}
    row = rows.iloc[0]
    return {
        "FMeasure": float(row.get("CDnet_FMeasure", row.get("FMeasure", 0.0)) or 0.0),
        "Event_F1": float(row.get("Event_F1", 0.0) or 0.0),
        "FPS": float(row.get("Avg_FPS", row.get("avg_FPS", 0.0)) or 0.0),
        "P95": float(row.get("P95_latency_ms", 0.0) or 0.0),
    }


def action_distribution(frames, video):
    rows = frames[frames["video"].astype(str) == video].copy()
    if rows.empty or "action_label" not in rows.columns:
        return ""
    counts = rows["action_label"].fillna("").astype(str).value_counts()
    total = max(1, int(counts.sum()))
    return ";".join(f"{action}:{count / total:.3f}" for action, count in counts.items())


def closed_empty_rate(frames, video):
    rows = frames[frames["video"].astype(str) == video].copy()
    if rows.empty or "action_label" not in rows.columns:
        return 0.0
    labels = rows["action_label"].fillna("").astype(str)
    return float(labels.str.startswith("CLOSED_EMPTY").mean())


def summarize_policy(root, policy):
    policy_root = root / policy
    per_video = read_per_video(policy_root)
    frames = read_frames(policy_root)
    guarded_video = per_video[per_video["Pipeline"].astype(str) == GUARDED].copy() if not per_video.empty else pd.DataFrame()

    row = {"policy_name": policy}
    if not guarded_video.empty:
        row.update({
            "aggregate_FMeasure": safe_mean(guarded_video.rename(columns={"CDnet_FMeasure": "FMeasure"}), "FMeasure"),
            "aggregate_Event_F1": safe_mean(guarded_video, "Event_F1"),
            "aggregate_FPS": safe_mean(guarded_video.rename(columns={"Avg_FPS": "FPS"}), "FPS"),
            "aggregate_P95": safe_mean(guarded_video, "P95_latency_ms"),
        })
    else:
        row.update({
            "aggregate_FMeasure": 0.0,
            "aggregate_Event_F1": 0.0,
            "aggregate_FPS": 0.0,
            "aggregate_P95": 0.0,
        })

    for video, prefix in [
        ("continuousPan", "continuousPan"),
        ("twoPositionPTZCam", "twoPosition"),
        ("bridgeEntry", "bridgeEntry"),
        ("cubicle", "cubicle"),
    ]:
        metrics = video_metric(per_video, video)
        for metric_name in ["FMeasure", "Event_F1", "FPS", "P95"]:
            row[f"{prefix}_{metric_name}"] = metrics.get(metric_name, 0.0)

    row["continuousPan_action_distribution"] = action_distribution(frames, "continuousPan")
    row["continuousPan_closed_empty_rate"] = closed_empty_rate(frames, "continuousPan")
    row["twoPosition_action_distribution"] = action_distribution(frames, "twoPositionPTZCam")

    bridge = frames[frames["video"].astype(str) == "bridgeEntry"].copy() if not frames.empty else pd.DataFrame()
    if not bridge.empty:
        closed_empty = bridge["action_label"].fillna("").astype(str).str.startswith("CLOSED_EMPTY")
        event_fn = bridge["Event_State"].fillna("").astype(str).eq("FN")
        row["bridgeEntry_closed_empty_event_fn"] = int((closed_empty & event_fn).sum())
        row["bridgeEntry_event_closed_empty_final_count"] = safe_sum(bridge, "event_closed_empty_final_count")
    else:
        row["bridgeEntry_closed_empty_event_fn"] = 0
        row["bridgeEntry_event_closed_empty_final_count"] = 0

    cubicle = frames[frames["video"].astype(str) == "cubicle"].copy() if not frames.empty else pd.DataFrame()
    row["cubicle_teacher_behavior_rate"] = safe_mean(cubicle, "teacher_ranker_behavior_applied")

    non_ptz = frames[frames["video"].astype(str).isin(NON_PTZ_VIDEOS)].copy() if not frames.empty else pd.DataFrame()
    row["non_ptz_teacher_behavior_rate"] = safe_mean(non_ptz, "teacher_ranker_behavior_applied")
    row["non_ptz_teacher_active_rate"] = safe_mean(non_ptz, "teacher_ranker_active")
    row["non_ptz_motion_comp_behavior_rate"] = safe_mean(non_ptz, "motion_comp_behavior_applied")
    row["non_ptz_phase7c_behavior_rate"] = safe_mean(non_ptz, "phase7c_ablation_active")

    return row, frames, per_video


def write_report(root, summary):
    cp = summary.sort_values(["continuousPan_FMeasure", "continuousPan_Event_F1"], ascending=False).head(1)
    tp = summary.sort_values(["twoPosition_FMeasure", "twoPosition_Event_F1"], ascending=False).head(1)
    safe = summary.sort_values(["non_ptz_teacher_behavior_rate", "cubicle_teacher_behavior_rate"], ascending=True).head(1)

    cp_policy = cp.iloc[0]["policy_name"] if not cp.empty else "NONE"
    tp_policy = tp.iloc[0]["policy_name"] if not tp.empty else "NONE"
    safe_policy = safe.iloc[0]["policy_name"] if not safe.empty else "NONE"

    candidates = summary[
        (summary["continuousPan_FMeasure"] >= 0.3693)
        & (summary["continuousPan_closed_empty_rate"] <= 0.02)
        & (summary["twoPosition_FMeasure"] >= 0.78)
        & (summary["bridgeEntry_closed_empty_event_fn"] == 0)
        & (summary["cubicle_teacher_behavior_rate"] <= 0.02)
        & (summary["non_ptz_teacher_behavior_rate"] <= 0.02)
        & (summary["aggregate_FPS"] >= 30.0)
    ].copy()
    causal_exists = not candidates.empty
    recommended = candidates.sort_values(
        ["continuousPan_FMeasure", "twoPosition_FMeasure", "aggregate_FPS"],
        ascending=False,
    ).iloc[0]["policy_name"] if causal_exists else "NONE"

    report_cols = [
        "policy_name",
        "aggregate_FMeasure",
        "aggregate_Event_F1",
        "aggregate_FPS",
        "aggregate_P95",
        "continuousPan_FMeasure",
        "continuousPan_closed_empty_rate",
        "twoPosition_FMeasure",
        "bridgeEntry_closed_empty_event_fn",
        "cubicle_teacher_behavior_rate",
        "non_ptz_teacher_behavior_rate",
    ]
    report_cols = [c for c in report_cols if c in summary.columns]
    table = summary[report_cols].to_csv(index=False).strip() if report_cols else ""
    lines = [
        "# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 7C Ablation Report",
        "",
        f"- Best continuousPan policy: {cp_policy}",
        f"- Best twoPosition policy: {tp_policy}",
        f"- Lowest non-PTZ teacher-behavior policy: {safe_policy}",
        f"- Causal schedule meeting Phase 7D criteria: {'yes' if causal_exists else 'no'}",
        f"- Recommended Phase 7D production policy: {recommended}",
        "",
        "PTZ-targeted remains disallowed until Phase 7D is implemented and smoke passes.",
        "",
        "## Policy Summary",
        "",
        "```csv",
        table,
        "```",
        "",
    ]
    (root / "phase7c_ablation_report.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        default="outputs/asmag_tr_controller_online_guarded_ablation_phase7c",
    )
    args = parser.parse_args()
    root = Path(args.root)
    root.mkdir(parents=True, exist_ok=True)

    rows = []
    all_frames = []
    for policy_dir in sorted([p for p in root.iterdir() if p.is_dir()]):
        if policy_dir.name not in POLICIES:
            continue
        row, frames, _ = summarize_policy(root, policy_dir.name)
        rows.append(row)
        if not frames.empty:
            frames = frames.copy()
            frames["policy_name"] = policy_dir.name
            all_frames.append(frames)

    summary = pd.DataFrame(rows)
    if summary.empty:
        summary = pd.DataFrame(columns=["policy_name"])
    summary.to_csv(root / "phase7c_ablation_summary.csv", index=False)

    cp_cols = [
        "policy_name",
        "continuousPan_FMeasure",
        "continuousPan_Event_F1",
        "continuousPan_FPS",
        "continuousPan_P95",
        "continuousPan_closed_empty_rate",
        "continuousPan_action_distribution",
    ]
    summary[[c for c in cp_cols if c in summary.columns]].to_csv(root / "continuousPan_ablation_summary.csv", index=False)

    tp_cols = [
        "policy_name",
        "twoPosition_FMeasure",
        "twoPosition_Event_F1",
        "twoPosition_FPS",
        "twoPosition_P95",
        "twoPosition_action_distribution",
    ]
    summary[[c for c in tp_cols if c in summary.columns]].to_csv(root / "twoPosition_ablation_summary.csv", index=False)

    nonptz_cols = [
        "policy_name",
        "bridgeEntry_FMeasure",
        "bridgeEntry_Event_F1",
        "bridgeEntry_closed_empty_event_fn",
        "bridgeEntry_event_closed_empty_final_count",
        "cubicle_FMeasure",
        "cubicle_Event_F1",
        "cubicle_teacher_behavior_rate",
        "non_ptz_teacher_behavior_rate",
        "non_ptz_teacher_active_rate",
        "non_ptz_motion_comp_behavior_rate",
        "non_ptz_phase7c_behavior_rate",
    ]
    summary[[c for c in nonptz_cols if c in summary.columns]].to_csv(root / "nonptz_safety_summary.csv", index=False)
    write_report(root, summary)
    print(f"[DONE] wrote Phase 7C ablation summaries under {root}")


if __name__ == "__main__":
    main()
