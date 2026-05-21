import argparse
import csv
from pathlib import Path


NA = "NA"

PORT_FRAMES = [1210, 1230, 1255, 1340, 1350, 1355, 1360, 1405, 1410, 1415, 1420, 1425, 1430, 1435, 1440]
PARKING_FRAMES = [1195, 1310, 1315, 1320, 1425, 1430, 1435, 1440, 1445]
CARRYOVER_VIDEOS = [
    ("badWeather", "snowFall"),
    ("thermal", "lakeSide"),
    ("shadow", "cubicle"),
    ("PTZ", "intermittentPan"),
    ("lowFramerate", "tunnelExit_0_35fps"),
]

BASE_FIELDS = [
    "category",
    "video",
    "frame_id",
    "Event_State",
    "action_label",
    "ai_intervention_original_action",
    "selected_mode_before_guard",
    "selected_mode_after_guard",
    "ai_intervention_detector_requested",
    "ai_intervention_applied",
    "active_event_memory",
    "ai_intervention_risk_high",
    "ai_intervention_guard_active",
    "ai_parking_iom_rescue_candidate",
    "ai_parking_iom_rescue_active",
    "ai_parking_iom_rescue_likely_unprotected_fn",
    "ai_parking_iom_preserve_fn_risk_candidate",
    "ai_parking_carryover_lock_active",
    "ai_port_lf_v4_hard_lock_active",
    "ai_port_lf_post_suppression_holdout_active",
    "ai_snowfall_carryover_gate_lock_status",
    "ai_lakeside_carryover_gate_lock_status",
    "ai_snowfall_actual_fn_rescue_active",
    "ai_thermal_lakeside_fn_rescue_active",
    "ai_exact_cubicle_late_event_rescue_active",
    "ai_ptz_intermittent_pan_fn_rescue_active",
    "ai_tunnel_exit_lf_rescue_active",
]

REASON_FIELDS = [
    "ai_port_lf_post_suppression_holdout_rejected_reason",
    "ai_parking_iom_rescue_rejected_reason",
    "ai_parking_carryover_lock_rejected_reason",
    "ai_snowfall_actual_fn_rescue_rejected_reason",
    "ai_thermal_lakeside_fn_rescue_rejected_reason",
    "ai_exact_cubicle_late_event_rescue_rejected_reason",
    "ai_ptz_intermittent_pan_fn_rescue_rejected_reason",
    "ai_tunnel_exit_lf_rescue_rejected_reason",
    "ai_final_normal_frame_suppressor_reason",
]

OUTPUT_FIELDS = [
    "analysis_group",
    "step",
    "reference_step",
    "reference_owner",
    "frame_id",
    "category",
    "video",
    "event_state",
    "action_label",
    "original_action",
    "selected_mode_before_guard",
    "selected_mode_after_guard",
    "detector_request",
    "proposal",
    "active_event_memory",
    "risk_high",
    "guard_active",
    "rescue_candidate",
    "rescue_active",
    "likely_unprotected_fn",
    "carryover_lock_active",
    "protected_fn",
    "unprotected_fn",
    "branch_active",
    "branch_status",
    "branch_reject_reason",
    "ref_event_state",
    "ref_action_label",
    "ref_detector_request",
    "ref_proposal",
    "ref_active_event_memory",
    "ref_risk_high",
    "ref_guard_active",
    "ref_rescue_candidate",
    "ref_rescue_active",
    "ref_likely_unprotected_fn",
    "ref_carryover_lock_active",
    "ref_protected_fn",
    "ref_unprotected_fn",
    "active_event_memory_lost",
    "risk_high_lost",
    "guard_active_lost",
    "rescue_candidate_lost",
    "rescue_active_lost",
    "carryover_lock_lost",
    "unsafe_final_action",
    "report_only_lock",
    "candidate_predicate_false",
    "trajectory_shift",
    "watch_only",
]


def read_csv(path):
    if not path.exists():
        return [], []
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def frame_metrics_path(root, category, video):
    return root / "raw_results" / category / video / "ASMAG_TR_CONTROLLER_ONLINE_GUARDED" / "frame_metrics.csv"


def to_int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def truthy(value):
    if value in (None, "", NA):
        return False
    try:
        return float(value) > 0
    except ValueError:
        return str(value).lower() in {"true", "yes", "active"}


def get(row, column):
    return row.get(column, NA)


def normalized_row(raw, step, group, reference_step, owner, missing_columns):
    for column in BASE_FIELDS + REASON_FIELDS:
        if column not in raw:
            missing_columns.add((step, get(raw, "category"), get(raw, "video"), column))
    event_state = get(raw, "Event_State")
    proposal = get(raw, "ai_intervention_applied")
    protected_fn = "1" if event_state == "FN" and truthy(proposal) else "0"
    unprotected_fn = "1" if event_state == "FN" and not truthy(proposal) else "0"
    rescue_candidate = first_present(raw, [
        "ai_parking_iom_rescue_candidate",
        "ai_snowfall_actual_fn_rescue_candidate",
        "ai_thermal_lakeside_fn_rescue_candidate",
        "ai_exact_cubicle_event_fn_pre_signal",
        "ai_ptz_intermittent_pan_fn_rescue_candidate",
        "ai_tunnel_exit_lf_rescue_candidate",
    ])
    rescue_active = first_present(raw, [
        "ai_parking_iom_rescue_active",
        "ai_snowfall_actual_fn_rescue_active",
        "ai_thermal_lakeside_fn_rescue_active",
        "ai_exact_cubicle_late_event_rescue_active",
        "ai_ptz_intermittent_pan_fn_rescue_active",
        "ai_tunnel_exit_lf_rescue_active",
    ])
    likely = first_present(raw, [
        "ai_parking_iom_rescue_likely_unprotected_fn",
        "ai_port_lf_detector_retighten_v3_explicit_likely_unprotected_fn",
        "ai_parking_iom_preserve_fn_risk_candidate",
    ])
    branch_status = first_nonempty(raw, [
        "ai_snowfall_carryover_gate_lock_status",
        "ai_lakeside_carryover_gate_lock_status",
        "ai_port_lf_v4_hard_lock_reason",
    ])
    reject_reason = first_nonempty(raw, REASON_FIELDS)
    branch_active = any(truthy(first_present(raw, [col])) for col in [
        "ai_port_lf_v4_hard_lock_active",
        "ai_port_lf_post_suppression_holdout_active",
        "ai_parking_iom_rescue_active",
        "ai_parking_carryover_lock_active",
        "ai_snowfall_actual_fn_rescue_active",
        "ai_thermal_lakeside_fn_rescue_active",
        "ai_exact_cubicle_late_event_rescue_active",
        "ai_ptz_intermittent_pan_fn_rescue_active",
        "ai_tunnel_exit_lf_rescue_active",
    ])
    return {
        "analysis_group": group,
        "step": step,
        "reference_step": reference_step,
        "reference_owner": owner,
        "frame_id": get(raw, "frame_id"),
        "category": get(raw, "category"),
        "video": get(raw, "video"),
        "event_state": event_state,
        "action_label": get(raw, "action_label"),
        "original_action": get(raw, "ai_intervention_original_action"),
        "selected_mode_before_guard": get(raw, "selected_mode_before_guard"),
        "selected_mode_after_guard": get(raw, "selected_mode_after_guard"),
        "detector_request": get(raw, "ai_intervention_detector_requested"),
        "proposal": proposal,
        "active_event_memory": get(raw, "active_event_memory"),
        "risk_high": get(raw, "ai_intervention_risk_high"),
        "guard_active": get(raw, "ai_intervention_guard_active"),
        "rescue_candidate": rescue_candidate,
        "rescue_active": rescue_active,
        "likely_unprotected_fn": likely,
        "carryover_lock_active": get(raw, "ai_parking_carryover_lock_active"),
        "protected_fn": protected_fn,
        "unprotected_fn": unprotected_fn,
        "branch_active": "1" if branch_active else "0",
        "branch_status": branch_status,
        "branch_reject_reason": reject_reason,
    }


def first_present(row, columns):
    for col in columns:
        if col in row:
            return row.get(col, NA)
    return NA


def first_nonempty(row, columns):
    values = []
    for col in columns:
        value = row.get(col, "")
        if value not in ("", NA, None):
            values.append(f"{col}={value}")
    return ";".join(values) if values else ""


def index_by_frame(rows):
    out = {}
    for row in rows:
        frame = to_int(row.get("frame_id"))
        if frame is not None:
            out[frame] = row
    return out


def attach_reference(rows, ref_by_frame):
    out = []
    for row in rows:
        ref = ref_by_frame.get(to_int(row["frame_id"]), {})
        merged = dict(row)
        for field in [
            "event_state",
            "action_label",
            "detector_request",
            "proposal",
            "active_event_memory",
            "risk_high",
            "guard_active",
            "rescue_candidate",
            "rescue_active",
            "likely_unprotected_fn",
            "carryover_lock_active",
            "protected_fn",
            "unprotected_fn",
        ]:
            merged[f"ref_{field}"] = ref.get(field, NA)
        merged["active_event_memory_lost"] = flag_lost(ref, row, "active_event_memory")
        merged["risk_high_lost"] = flag_lost(ref, row, "risk_high")
        merged["guard_active_lost"] = flag_lost(ref, row, "guard_active")
        merged["rescue_candidate_lost"] = flag_lost(ref, row, "rescue_candidate")
        merged["rescue_active_lost"] = flag_lost(ref, row, "rescue_active")
        merged["carryover_lock_lost"] = flag_lost(ref, row, "carryover_lock_active")
        merged["unsafe_final_action"] = "1" if unsafe_action(row.get("action_label", "")) and truthy(row.get("unprotected_fn")) else "0"
        merged["report_only_lock"] = "1" if "active_reporting_lock" in row.get("branch_status", "") else "0"
        merged["candidate_predicate_false"] = "1" if truthy(ref.get("rescue_candidate")) and not truthy(row.get("rescue_candidate")) else "0"
        merged["trajectory_shift"] = "1" if any(truthy(merged[k]) for k in [
            "active_event_memory_lost",
            "risk_high_lost",
            "guard_active_lost",
            "rescue_candidate_lost",
            "rescue_active_lost",
            "carryover_lock_lost",
        ]) or row.get("event_state") != ref.get("event_state", row.get("event_state")) else "0"
        merged["watch_only"] = "1" if row.get("analysis_group") == "port" else "0"
        out.append(merged)
    return out


def flag_lost(ref, row, field):
    return "1" if truthy(ref.get(field)) and not truthy(row.get(field)) else "0"


def unsafe_action(action):
    text = str(action or "")
    return text.startswith("CLOSED_EMPTY") or "REUSE" in text or "FALLBACK" in text


def load_step_rows(root, step, category, video, group, reference_step, owner, missing_columns):
    path = frame_metrics_path(root, category, video)
    rows, _ = read_csv(path)
    return [normalized_row(r, step, group, reference_step, owner, missing_columns) for r in rows]


def select_frames(rows, frames):
    wanted = set(frames)
    return [row for row in rows if to_int(row["frame_id"]) in wanted]


def carryover_filter(row):
    if row["event_state"] == "FN":
        return True
    if truthy(row["protected_fn"]) or truthy(row["unprotected_fn"]):
        return True
    activity_fields = [
        "proposal",
        "guard_active",
        "rescue_candidate",
        "rescue_active",
        "carryover_lock_active",
        "branch_active",
    ]
    return any(truthy(row.get(field)) for field in activity_fields)


def summarize_violations(all_rows):
    counts = {}
    for row in all_rows:
        if row["step"] != "step4e6":
            continue
        checks = {
            "I2_event_memory_lost": row.get("active_event_memory_lost"),
            "I3_unsafe_unprotected_fn": row.get("unsafe_final_action"),
            "I4_report_only_lock": row.get("report_only_lock"),
            "I5_candidate_predicate_false": row.get("candidate_predicate_false"),
            "I6_trajectory_shift": row.get("trajectory_shift"),
            "I7_split_branch_watch": row.get("watch_only"),
        }
        for name, value in checks.items():
            if truthy(value):
                key = (name, row["analysis_group"], row["category"], row["video"])
                counts[key] = counts.get(key, 0) + 1
    return [
        {
            "violation": key[0],
            "analysis_group": key[1],
            "category": key[2],
            "video": key[3],
            "count": count,
        }
        for key, count in sorted(counts.items())
    ]


def main():
    parser = argparse.ArgumentParser(description="Build Q1-SIC-0 safety trajectory diffs from existing outputs.")
    parser.add_argument("--step4d6-root", required=True)
    parser.add_argument("--step4e4-root", required=True)
    parser.add_argument("--step4e6-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    roots = {
        "step4d6": Path(args.step4d6_root),
        "step4e4": Path(args.step4e4_root),
        "step4e6": Path(args.step4e6_root),
    }
    out_dir = Path(args.out)
    missing = set()

    port_rows = []
    for step, root in roots.items():
        rows = load_step_rows(root, step, "lowFramerate", "port_0_17fps", "port", "step4e4", "detector_retighten", missing)
        port_rows.extend(select_frames(rows, PORT_FRAMES))
    port_ref = {to_int(r["frame_id"]): r for r in port_rows if r["step"] == "step4e4"}
    port_rows = attach_reference(port_rows, port_ref)

    parking_rows = []
    for step, root in roots.items():
        rows = load_step_rows(root, step, "intermittentObjectMotion", "parking", "parking", "step4d6", "event_safety", missing)
        parking_rows.extend(select_frames(rows, PARKING_FRAMES))
    parking_ref = {to_int(r["frame_id"]): r for r in parking_rows if r["step"] == "step4d6"}
    parking_rows = attach_reference(parking_rows, parking_ref)

    carry_rows = []
    for category, video in CARRYOVER_VIDEOS:
        per_video = []
        for step, root in roots.items():
            rows = load_step_rows(root, step, category, video, "carryover", "step4d6", "event_safety", missing)
            per_video.extend([row for row in rows if carryover_filter(row)])
        ref = {to_int(r["frame_id"]): r for r in per_video if r["step"] == "step4d6"}
        carry_rows.extend(attach_reference(per_video, ref))

    all_rows = port_rows + parking_rows + carry_rows
    write_csv(out_dir / "port_trajectory_diff.csv", port_rows, OUTPUT_FIELDS)
    write_csv(out_dir / "parking_trajectory_diff.csv", parking_rows, OUTPUT_FIELDS)
    write_csv(out_dir / "carryover_trajectory_diff.csv", carry_rows, OUTPUT_FIELDS)
    write_csv(out_dir / "invariant_violation_summary.csv", summarize_violations(all_rows), ["violation", "analysis_group", "category", "video", "count"])
    write_csv(
        out_dir / "missing_columns_summary.csv",
        [
            {"step": s, "category": c, "video": v, "missing_column": col}
            for s, c, v, col in sorted(missing)
        ],
        ["step", "category", "video", "missing_column"],
    )


if __name__ == "__main__":
    main()
