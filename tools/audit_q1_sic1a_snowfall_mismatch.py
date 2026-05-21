"""Audit Q1-SIC-1 snowFall frame-1150 runtime mismatch.

Analysis-only helper. Reads existing output CSVs and writes a compact audit
bundle under a caller-provided output directory.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


VIDEO_CATEGORY = "badWeather"
VIDEO_NAME = "snowFall"
PIPELINE = "ASMAG_TR_CONTROLLER_ONLINE_GUARDED"
PRIMARY_FRAME = 1150
CONTEXT_FRAMES = list(range(1120, 1171, 5))

Q1_COLUMNS = [
    "q1_sic_final_arbitration_enabled",
    "q1_sic_shadow_only",
    "q1_sic_arbitration_active",
    "q1_sic_arbitration_label",
    "q1_sic_arbitration_reason",
    "q1_sic_owner",
    "q1_sic_reference_step",
    "q1_sic_enforcement_class",
    "q1_sic_would_touch_normal_frame",
    "q1_sic_watch_only",
    "q1_sic_invariants_triggered",
    "q1_sic_pre_action",
    "q1_sic_post_action",
    "q1_sic_pre_detector_request",
    "q1_sic_post_detector_request",
    "q1_sic_pre_protection_label",
    "q1_sic_post_protection_label",
]

BASE_COLUMNS = [
    "category",
    "video",
    "pipeline",
    "frame",
    "frame_id",
    "frame_idx",
    "raw_frame_id",
    "evaluated_index",
    "gt_state",
    "frame_state",
    "Event_State",
    "Is_Active",
    "is_normal_frame",
    "is_event_frame",
    "event_fn",
    "protected_fn",
    "unprotected_fn",
    "false_intervention",
    "proposal_on_normal",
    "action_label",
    "final_action",
    "ai_intervention_final_action",
    "selected_mode",
    "selected_mode_before_guard",
    "selected_mode_after_guard",
    "detector_request",
    "ai_intervention_detector_requested",
    "yolo_called",
    "proposal",
    "ai_intervention_applied",
    "reused_prediction",
    "closed_empty_action",
    "fallback_action",
    "reuse_action",
    "detect_action",
    "runtime_unsafe_action_by_q1_sic",
    "active_event_memory",
    "event_memory_age",
    "frames_since_active_prediction",
    "risk_high",
    "ai_intervention_risk_high",
    "likely_unprotected_fn",
    "guard_active",
    "ai_intervention_guard_active",
    "hard_guard",
    "ai_intervention_guard_reason",
    "ai_detector_needed_pred",
    "ai_detector_needed_score",
    "ai_detector_request_blocked_no_refresh_model",
    "forced_refresh_cooldown_active",
    "frames_since_last_detector",
    "frames_since_last_forced_refresh",
    "last_detection_frame_id",
] + Q1_COLUMNS

SIGNAL_KEYWORDS = [
    "snow",
    "lake",
    "carry",
    "rescue",
    "lock",
    "holdout",
    "restore",
    "trim",
    "suppress",
]

DIFF_COLUMNS = [
    "Event_State",
    "Is_Active",
    "action_label",
    "ai_intervention_final_action",
    "selected_mode",
    "selected_mode_before_guard",
    "selected_mode_after_guard",
    "ai_intervention_applied",
    "ai_intervention_detector_requested",
    "yolo_called",
    "active_event_memory",
    "ai_intervention_risk_high",
    "ai_intervention_guard_active",
    "ai_intervention_guard_reason",
    "ai_detector_needed_pred",
    "ai_detector_needed_score",
    "ai_detector_request_blocked_no_refresh_model",
    "forced_refresh_cooldown_active",
    "q1_sic_arbitration_active",
    "q1_sic_arbitration_label",
    "q1_sic_arbitration_reason",
    "q1_sic_pre_protection_label",
    "q1_sic_post_protection_label",
]


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = [dict(row) for row in reader]
        return rows, list(reader.fieldnames or [])


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fieldnames: Sequence[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys: List[str] = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        fieldnames = keys or ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def guarded_metrics_path(root: Path) -> Path:
    return root / "raw_results" / VIDEO_CATEGORY / VIDEO_NAME / PIPELINE / "frame_metrics.csv"


def frame_value(row: Dict[str, str]) -> int | None:
    for key in ("frame", "frame_id", "frame_idx", "raw_frame_id"):
        value = row.get(key, "")
        try:
            if value not in ("", None):
                return int(float(value))
        except ValueError:
            continue
    return None


def truthy(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def get_any(row: Dict[str, str], keys: Iterable[str], default: str = "NA") -> str:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return default


def action_of(row: Dict[str, str]) -> str:
    return get_any(row, ("action_label", "final_action", "ai_intervention_final_action"), "")


def is_unsafe_by_q1(action: str) -> bool:
    upper = action.upper()
    return upper.startswith("CLOSED_EMPTY") or upper.startswith("REUSE") or "FALLBACK" in upper


def event_state(row: Dict[str, str]) -> str:
    return get_any(row, ("frame_state", "gt_state", "Event_State"), "")


def proposal(row: Dict[str, str]) -> bool:
    return truthy(get_any(row, ("proposal", "ai_intervention_applied"), "0"))


def detector_request(row: Dict[str, str]) -> str:
    return get_any(row, ("detector_request", "ai_intervention_detector_requested", "yolo_called"), "NA")


def has_activity(row: Dict[str, str], fields: Sequence[str]) -> bool:
    if event_state(row).upper() == "FN":
        return True
    for key in fields:
        if key in row and truthy(row.get(key, "")):
            return True
    for key, value in row.items():
        lower = key.lower()
        if any(word in lower for word in SIGNAL_KEYWORDS) and truthy(value):
            return True
    return False


def dynamic_columns(fieldnames: Sequence[str]) -> List[str]:
    cols: List[str] = []
    for col in fieldnames:
        lower = col.lower()
        if any(word in lower for word in SIGNAL_KEYWORDS) and col not in cols:
            cols.append(col)
    return cols


def normalize_row(
    row: Dict[str, str],
    source: str,
    fieldnames: Sequence[str],
    missing: Dict[str, set],
) -> Dict[str, object]:
    state = event_state(row)
    active = truthy(get_any(row, ("Is_Active", "is_event_frame"), "0"))
    prop = proposal(row)
    action = action_of(row)
    normal = (not active) and state.upper() not in {"FN", "TP"}
    event_fn = state.upper() == "FN"
    out: Dict[str, object] = {
        "source": source,
        "category": row.get("category") or VIDEO_CATEGORY,
        "video": row.get("video") or VIDEO_NAME,
        "pipeline": row.get("pipeline") or PIPELINE,
        "frame_id_normalized": frame_value(row),
        "is_normal_frame": int(normal),
        "is_event_frame": int(active or state.upper() in {"FN", "TP"}),
        "event_fn": int(event_fn),
        "protected_fn": int(event_fn and prop),
        "unprotected_fn": int(event_fn and not prop),
        "false_intervention": int(normal and prop),
        "proposal_on_normal": int(normal and prop),
        "detector_request": detector_request(row),
        "proposal": int(prop),
        "closed_empty_action": int(action.upper().startswith("CLOSED_EMPTY")),
        "fallback_action": int("FALLBACK" in action.upper()),
        "reuse_action": int(action.upper().startswith("REUSE")),
        "detect_action": int(action.upper().startswith("DETECT")),
        "runtime_unsafe_action_by_q1_sic": int(is_unsafe_by_q1(action)),
        "risk_high": get_any(row, ("risk_high", "ai_intervention_risk_high"), "NA"),
        "guard_active": get_any(row, ("guard_active", "ai_intervention_guard_active"), "NA"),
    }
    wanted = list(BASE_COLUMNS)
    for col in dynamic_columns(fieldnames):
        if col not in wanted:
            wanted.append(col)
    for col in wanted:
        if col in out:
            continue
        if col in row:
            out[col] = row.get(col, "")
        else:
            out[col] = "NA"
            missing[source].add(col)
    return out


def rows_by_frame(rows: Sequence[Dict[str, str]]) -> Dict[int, Dict[str, str]]:
    by_frame: Dict[int, Dict[str, str]] = {}
    for row in rows:
        frame = frame_value(row)
        if frame is not None:
            by_frame[frame] = row
    return by_frame


def select_context_and_activity(
    rows: Sequence[Dict[str, str]],
    activity_fields: Sequence[str],
) -> List[Dict[str, str]]:
    selected = []
    for row in rows:
        frame = frame_value(row)
        if frame == PRIMARY_FRAME or frame in CONTEXT_FRAMES or has_activity(row, activity_fields):
            selected.append(row)
    return selected


def make_diff(
    reference_rows: Sequence[Dict[str, str]],
    sic_rows: Sequence[Dict[str, str]],
    reference_name: str,
    missing: Dict[str, set],
) -> List[Dict[str, object]]:
    ref_by_frame = rows_by_frame(reference_rows)
    sic_by_frame = rows_by_frame(sic_rows)
    frames = sorted(set(CONTEXT_FRAMES) | {PRIMARY_FRAME} | set(ref_by_frame) | set(sic_by_frame))
    rows: List[Dict[str, object]] = []
    for frame in frames:
        ref = ref_by_frame.get(frame, {})
        sic = sic_by_frame.get(frame, {})
        if frame not in CONTEXT_FRAMES and frame != PRIMARY_FRAME:
            if not (has_activity(ref, DIFF_COLUMNS) or has_activity(sic, DIFF_COLUMNS)):
                continue
        out: Dict[str, object] = {"frame_id": frame, "reference": reference_name}
        for col in DIFF_COLUMNS:
            ref_key = f"{reference_name}_{col}"
            sic_key = f"q1sic1_{col}"
            if col in ref:
                out[ref_key] = ref.get(col, "")
            else:
                out[ref_key] = "NA"
                missing[reference_name].add(col)
            if col in sic:
                out[sic_key] = sic.get(col, "")
            else:
                out[sic_key] = "NA"
                missing["q1sic1"].add(col)
        out["reference_unprotected_fn"] = int(event_state(ref).upper() == "FN" and not proposal(ref)) if ref else "NA"
        out["q1sic1_unprotected_fn"] = int(event_state(sic).upper() == "FN" and not proposal(sic)) if sic else "NA"
        out["action_changed"] = int(action_of(ref) != action_of(sic)) if ref and sic else "NA"
        out["q1sic1_runtime_unsafe_action_by_q1_sic"] = int(is_unsafe_by_q1(action_of(sic))) if sic else "NA"
        rows.append(out)
    return rows


def filter_replay_rows(path: Path, source: str) -> Tuple[List[Dict[str, object]], List[str]]:
    rows, fields = read_csv(path)
    out: List[Dict[str, object]] = []
    for row in rows:
        text = " ".join(str(v) for v in row.values())
        frame = frame_value(row)
        if "snowFall" in text and (frame in set(CONTEXT_FRAMES) or frame == PRIMARY_FRAME or frame is None):
            copy = {"source": source}
            copy.update(row)
            out.append(copy)
    return out, fields


def classify(runtime_row: Dict[str, str]) -> Dict[str, object]:
    q1_enabled = truthy(runtime_row.get("q1_sic_final_arbitration_enabled", "0"))
    q1_label = runtime_row.get("q1_sic_arbitration_label", "NA")
    state = event_state(runtime_row)
    act = action_of(runtime_row)
    prop = proposal(runtime_row)
    active_event = truthy(runtime_row.get("active_event_memory", "0"))
    risk_high = truthy(get_any(runtime_row, ("risk_high", "ai_intervention_risk_high"), "0"))
    guard_active = truthy(get_any(runtime_row, ("guard_active", "ai_intervention_guard_active"), "0"))
    detector_blocked = truthy(runtime_row.get("ai_detector_request_blocked_no_refresh_model", "0"))
    detector_needed = truthy(runtime_row.get("ai_detector_needed_pred", "0"))
    unsafe = is_unsafe_by_q1(act)
    event_fn = state.upper() == "FN"
    no_change_unprotected = q1_label == "NO_CHANGE" and event_fn and not prop

    if no_change_unprotected and act.upper().startswith("DETECT") and not unsafe:
        primary = "FINAL_PROTECTION_ACCOUNTING_MISMATCH"
        secondary = [
            "ARBITRATION_CONDITION_TOO_WEAK",
            "POSTHOC_ONLY_SIGNAL_NOT_RUNTIME_SAFE",
        ]
        recommendation = "Q1-SIC-1B telemetry repair / risk proxy addition"
        reason = (
            "Runtime had event/risk/guard context but selected action DETECT_ACC was not "
            "classified unsafe, so final_safety_arbitration returned NO_CHANGE while "
            "post-hoc protection accounting remained unprotected_fn."
        )
    elif no_change_unprotected:
        primary = "ARBITRATION_CONDITION_TOO_WEAK"
        secondary = ["TELEMETRY_INSUFFICIENT"]
        recommendation = "Q1-SIC-1B small arbitration-condition repair"
        reason = "Runtime row was an unprotected FN and Q1-SIC returned NO_CHANGE."
    else:
        primary = "UNKNOWN_NEEDS_MORE_TELEMETRY"
        secondary = []
        recommendation = "Q1-SIC-1B telemetry repair / risk proxy addition"
        reason = "Primary failure row did not match the expected NO_CHANGE unprotected-FN pattern."

    return {
        "frame_id": PRIMARY_FRAME,
        "primary_class": primary,
        "secondary_classes": ";".join(secondary),
        "recommended_next_action": recommendation,
        "event_safety_owned": 1,
        "port_detector_retighten_owned": 0,
        "would_risk_touching_normal_frames": "low_if_gated_to_runtime_event_risk_rows",
        "q1_sic_final_arbitration_enabled": int(q1_enabled),
        "q1_sic_event_safety_enabled": "see_config_true",
        "q1_sic_arbitration_label": q1_label,
        "frame_state": state,
        "action_label": act,
        "q1_unsafe_action": int(unsafe),
        "active_event_memory": int(active_event),
        "risk_high": int(risk_high),
        "guard_active": int(guard_active),
        "ai_detector_needed_pred": int(detector_needed),
        "ai_detector_request_blocked_no_refresh_model": int(detector_blocked),
        "reason": reason,
    }


def signal_classification(runtime_row: Dict[str, str]) -> List[Dict[str, object]]:
    signals = [
        ("active_event_memory", "runtime-available before final action", "present"),
        ("ai_intervention_risk_high", "runtime-available before final action", "present"),
        ("ai_intervention_guard_active", "runtime-available before final action", "present"),
        ("ai_detector_needed_pred", "runtime-available before final action", "present"),
        ("ai_detector_request_blocked_no_refresh_model", "runtime-available after branch decision but before metrics", "present"),
        ("forced_refresh_cooldown_active", "runtime-available after branch decision but before metrics", "present"),
        ("action_label", "runtime-available after branch decision but before metrics", "present"),
        ("selected_mode_after_guard", "runtime-available after branch decision but before metrics", "present"),
        ("q1_sic_pre_protection_label", "post-hoc metric only", "present but not runtime-safe input"),
        ("q1_sic_post_protection_label", "post-hoc metric only", "present but not runtime-safe input"),
        ("Event_State", "ground-truth-only", "present for audit/reporting"),
        ("event_fn", "ground-truth-only", "derived for audit/reporting"),
        ("protected_fn", "ground-truth-only", "derived for audit/reporting"),
        ("unprotected_fn", "ground-truth-only", "derived for audit/reporting"),
        ("snowfall_weather_likely_unprotected_fn", "runtime-available before final action", "missing or not exported if NA"),
    ]
    rows: List[Dict[str, object]] = []
    for name, availability, note in signals:
        if name == "event_fn":
            value = int(event_state(runtime_row).upper() == "FN")
        elif name == "protected_fn":
            value = int(event_state(runtime_row).upper() == "FN" and proposal(runtime_row))
        elif name == "unprotected_fn":
            value = int(event_state(runtime_row).upper() == "FN" and not proposal(runtime_row))
        else:
            value = runtime_row.get(name, "NA")
        rows.append(
            {
                "frame_id": PRIMARY_FRAME,
                "signal": name,
                "value": value,
                "availability_class": availability,
                "audit_note": note,
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sic1-root", required=True)
    parser.add_argument("--step4d6-root", required=True)
    parser.add_argument("--step4e6-root", required=True)
    parser.add_argument("--sic0-replay-root", required=True)
    parser.add_argument("--sic1-shadow-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    sic1_root = Path(args.sic1_root)
    step4d6_root = Path(args.step4d6_root)
    step4e6_root = Path(args.step4e6_root)
    sic0_root = Path(args.sic0_replay_root)
    shadow_root = Path(args.sic1_shadow_root)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    missing: Dict[str, set] = defaultdict(set)

    sic_rows, sic_fields = read_csv(guarded_metrics_path(sic1_root))
    d6_rows, d6_fields = read_csv(guarded_metrics_path(step4d6_root))
    e6_rows, e6_fields = read_csv(guarded_metrics_path(step4e6_root))

    sic_by_frame = rows_by_frame(sic_rows)
    runtime_1150 = sic_by_frame.get(PRIMARY_FRAME, {})

    normalized_runtime = [normalize_row(runtime_1150, "q1sic1_runtime", sic_fields, missing)] if runtime_1150 else []
    write_csv(out / "snowfall_1150_runtime_row.csv", normalized_runtime)

    context_rows = [
        normalize_row(row, "q1sic1_runtime", sic_fields, missing)
        for row in sic_rows
        if frame_value(row) in set(CONTEXT_FRAMES)
    ]
    write_csv(out / "snowfall_context_1120_1170.csv", context_rows)

    d6_selected = select_context_and_activity(d6_rows, DIFF_COLUMNS)
    e6_selected = select_context_and_activity(e6_rows, DIFF_COLUMNS)
    sic_selected = select_context_and_activity(sic_rows, DIFF_COLUMNS)

    write_csv(
        out / "snowfall_step4d6_vs_q1sic1_diff.csv",
        make_diff(d6_selected, sic_selected, "step4d6", missing),
    )
    write_csv(
        out / "snowfall_step4e6_vs_q1sic1_diff.csv",
        make_diff(e6_selected, sic_selected, "step4e6", missing),
    )

    replay_rows: List[Dict[str, object]] = []
    for filename, source in [
        ("carryover_trajectory_diff.csv", "sic0_carryover_trajectory_diff"),
        ("counterfactual_arbitration_candidates.csv", "sic0_counterfactual_candidates"),
        ("counterfactual_summary.csv", "sic0_counterfactual_summary"),
    ]:
        rows, _ = filter_replay_rows(sic0_root / filename, source)
        replay_rows.extend(rows)
    for filename, source in [
        ("shadow_arbitration_verdict.csv", "sic1_shadow_verdict"),
        ("shadow_arbitration_summary.csv", "sic1_shadow_summary"),
    ]:
        rows, _ = filter_replay_rows(shadow_root / filename, source)
        replay_rows.extend(rows)
    if runtime_1150:
        replay_rows.append(normalize_row(runtime_1150, "q1sic1_runtime_1150", sic_fields, missing))
    write_csv(out / "snowfall_sic0_shadow_vs_runtime.csv", replay_rows)

    classification_rows: List[Dict[str, object]] = []
    if runtime_1150:
        classification_rows.append(classify(runtime_1150))
        classification_rows.extend(signal_classification(runtime_1150))
    write_csv(out / "snowfall_mismatch_classification.csv", classification_rows)

    missing_rows = []
    for source, cols in sorted(missing.items()):
        for col in sorted(cols):
            missing_rows.append({"source": source, "missing_column": col})
    write_csv(out / "snowfall_missing_columns_summary.csv", missing_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
