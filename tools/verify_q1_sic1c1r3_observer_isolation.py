"""Verify Q1-SIC-1C1R3 observer isolation against the C1C1R baseline."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


PIPELINE = "ASMAG_TR_CONTROLLER_ONLINE_GUARDED"
PARKING = ("intermittentObjectMotion", "parking")
COPY = ("shadow", "copyMachine")
PORT = ("lowFramerate", "port_0_17fps")
SNOW = ("badWeather", "snowFall")
COPY_FRAMES = [810, 815, 820, 935, 940, 945]
PORT_FRAMES = [1350, 1355]
BEHAVIOR_COLUMNS = [
    "action_label",
    "ai_intervention_applied",
    "ai_intervention_detector_requested",
    "yolo_called",
    "selected_mode",
    "selected_mode_before_guard",
    "selected_mode_after_guard",
    "q1_sic_arbitration_active",
    "q1_sic_arbitration_label",
]
OBSERVER_COLUMNS = [
    "q1_sic_observer_isolated_enabled",
    "q1_sic_observer_post_decision_only",
    "q1_sic_observer_used_immutable_snapshot",
    "q1_sic_observer_mutated_control_state",
    "q1_sic_observer_gt_signal_used",
    "q1_sic_observer_would_touch_normal_frame",
    "q1_sic_observer_action_is_detect",
    "q1_sic_observer_event_risk_pressure",
    "q1_sic_observer_detector_pressure",
    "q1_sic_observer_proposal_absent",
    "q1_sic_observer_runtime_empty_proxy",
    "q1_sic_observer_would_select_shadow",
    "q1_sic_observer_reject_reason",
    "q1_sic_observer_pressure_memory_enabled",
    "q1_sic_observer_pressure_memory_used",
]


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def truthy(value: object) -> bool:
    if value in (None, "", "NA"):
        return False
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return str(value).strip().lower() in {"true", "yes", "active"}


def number(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def frame(row: Dict[str, str]) -> int:
    for key in ("raw_frame_id", "frame_id", "frame", "frame_idx"):
        if row.get(key) not in (None, ""):
            return int(float(row[key]))
    return -1


def row_key(row: Dict[str, str]) -> Tuple[str, str, int]:
    return (row.get("category", ""), row.get("video", ""), frame(row))


def guarded_path(root: Path, video: Sequence[str]) -> Path:
    return root / "raw_results" / video[0] / video[1] / PIPELINE / "frame_metrics.csv"


def load_video(root: Path, video: Sequence[str]) -> List[Dict[str, str]]:
    return read_csv(guarded_path(root, video))


def by_frame(rows: Iterable[Dict[str, str]]) -> Dict[int, Dict[str, str]]:
    return {frame(row): row for row in rows}


def all_guarded_rows(root: Path) -> List[Dict[str, str]]:
    return [
        row
        for path in root.glob(f"raw_results/*/*/{PIPELINE}/frame_metrics.csv")
        for row in read_csv(path)
    ]


def video_summary(root: Path, category: str, video: str) -> Dict[str, str]:
    for row in read_csv(root / "ai_intervention_video_summary.csv"):
        if row.get("category") == category and row.get("video") == video:
            return row
    return {}


def is_fn(row: Dict[str, str]) -> bool:
    return str(row.get("Event_State") or row.get("frame_state") or "") == "FN"


def protected(row: Dict[str, str]) -> bool:
    if truthy(row.get("protected_fn")) or row.get("q1_sic_post_protection_label") == "protected_event_fn":
        return True
    return bool(is_fn(row) and (truthy(row.get("ai_intervention_applied")) or truthy(row.get("ai_intervention_detector_requested"))))


def unprotected(row: Dict[str, str]) -> bool:
    if not row:
        return False
    if truthy(row.get("unprotected_fn")) or row.get("q1_sic_post_protection_label") == "unprotected_fn":
        return True
    return bool(is_fn(row) and not protected(row))


def max_col(rows: List[Dict[str, str]], column: str) -> float:
    return max([number(row.get(column)) for row in rows] or [0.0])


def rate(rows: List[Dict[str, str]], column: str) -> float:
    if not rows:
        return 0.0
    return sum(int(truthy(row.get(column))) for row in rows) / float(len(rows))


def count_normal_interventions(root: Path) -> int:
    return sum(
        int(number(row.get("normal_frame_intervention_count")) > 0)
        for row in read_csv(root / "ai_intervention_video_summary.csv")
    )


def compare_behavior(c1r_rows: List[Dict[str, str]], c1r3_rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    baseline = {row_key(row): row for row in c1r_rows}
    candidate = {row_key(row): row for row in c1r3_rows}
    deltas: List[Dict[str, object]] = []
    all_keys = sorted(set(baseline) | set(candidate))
    for key in all_keys:
        left = baseline.get(key, {})
        right = candidate.get(key, {})
        if not left or not right:
            deltas.append({
                "category": key[0],
                "video": key[1],
                "frame": key[2],
                "field": "row_presence",
                "c1r": "present" if left else "missing",
                "c1r3": "present" if right else "missing",
            })
            continue
        for column in BEHAVIOR_COLUMNS:
            if str(left.get(column, "")) != str(right.get(column, "")):
                deltas.append({
                    "category": key[0],
                    "video": key[1],
                    "frame": key[2],
                    "field": column,
                    "c1r": left.get(column, ""),
                    "c1r3": right.get(column, ""),
                })
        if protected(left) != protected(right):
            deltas.append({
                "category": key[0],
                "video": key[1],
                "frame": key[2],
                "field": "protected_fn_accounting",
                "c1r": int(protected(left)),
                "c1r3": int(protected(right)),
            })
        if unprotected(left) != unprotected(right):
            deltas.append({
                "category": key[0],
                "video": key[1],
                "frame": key[2],
                "field": "unprotected_fn_accounting",
                "c1r": int(unprotected(left)),
                "c1r3": int(unprotected(right)),
            })
    return deltas


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Q1-SIC-1C1R3 observer isolation.")
    parser.add_argument("--c1r-root", required=True)
    parser.add_argument("--c1r3-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    c1r_root = Path(args.c1r_root)
    c1r3_root = Path(args.c1r3_root)
    out = Path(args.out)

    c1r_all = all_guarded_rows(c1r_root)
    c1r3_all = all_guarded_rows(c1r3_root)
    behavior_deltas = compare_behavior(c1r_all, c1r3_all)

    c1r_parking = load_video(c1r_root, PARKING)
    c1r3_parking = load_video(c1r3_root, PARKING)
    c1r_parking_summary = video_summary(c1r_root, *PARKING)
    c1r3_parking_summary = video_summary(c1r3_root, *PARKING)
    c1r_parking_proposal = number(c1r_parking_summary.get("intervention_rate"), rate(c1r_parking, "ai_intervention_applied"))
    c1r3_parking_proposal = number(c1r3_parking_summary.get("intervention_rate"), rate(c1r3_parking, "ai_intervention_applied"))
    c1r3_parking_detector = number(c1r3_parking_summary.get("detector_request_rate"), rate(c1r3_parking, "ai_intervention_detector_requested"))
    c1r3_parking_unprotected = sum(int(unprotected(row)) for row in c1r3_parking)
    parking_preserved_ok = int(
        c1r3_parking_unprotected == 0
        and c1r3_parking_detector == 0.0
        and c1r3_parking_proposal <= c1r_parking_proposal + 0.0001
    )

    c1r_copy = by_frame(load_video(c1r_root, COPY))
    c1r3_copy = by_frame(load_video(c1r3_root, COPY))
    c1r_port = by_frame(load_video(c1r_root, PORT))
    c1r3_port = by_frame(load_video(c1r3_root, PORT))
    c1r_snow = by_frame(load_video(c1r_root, SNOW))
    c1r3_snow = by_frame(load_video(c1r3_root, SNOW))

    row_checks: List[Dict[str, object]] = []
    copy_preserved_ok = 1
    for frame_id in COPY_FRAMES:
        left = c1r_copy.get(frame_id, {})
        right = c1r3_copy.get(frame_id, {})
        ok = int(protected(left) == protected(right) and unprotected(left) == unprotected(right))
        copy_preserved_ok = int(copy_preserved_ok and ok)
        row_checks.append({
            "check": "copyMachine_preserved",
            "frame": frame_id,
            "c1r_label": left.get("q1_sic_arbitration_label", ""),
            "c1r3_label": right.get("q1_sic_arbitration_label", ""),
            "c1r_protected": int(protected(left)),
            "c1r3_protected": int(protected(right)),
            "c1r_unprotected": int(unprotected(left)),
            "c1r3_unprotected": int(unprotected(right)),
            "passed": ok,
        })

    port_watch_preserved_ok = 1
    no_port_retighten_enforcement_ok = 1
    for frame_id in PORT_FRAMES:
        left = c1r_port.get(frame_id, {})
        right = c1r3_port.get(frame_id, {})
        watch_ok = int(
            right.get("q1_sic_arbitration_label") == "WATCH_ONLY_PORT_RETIGHTEN"
            and truthy(right.get("q1_sic_watch_only"))
            and right.get("q1_sic_owner") == "detector_retighten"
            and right.get("q1_sic_reference_step") == "Step4E4"
        )
        no_enforce = int(
            number(right.get("q1_sic_pre_detector_request")) == number(right.get("q1_sic_post_detector_request"))
            and number(right.get("ai_intervention_detector_requested")) == 0
        )
        port_watch_preserved_ok = int(port_watch_preserved_ok and watch_ok)
        no_port_retighten_enforcement_ok = int(no_port_retighten_enforcement_ok and no_enforce)
        row_checks.append({
            "check": "port_watch_preserved",
            "frame": frame_id,
            "c1r_label": left.get("q1_sic_arbitration_label", ""),
            "c1r3_label": right.get("q1_sic_arbitration_label", ""),
            "c1r3_watch": right.get("q1_sic_watch_only", ""),
            "c1r3_owner": right.get("q1_sic_owner", ""),
            "c1r3_reference": right.get("q1_sic_reference_step", ""),
            "detector_unchanged": no_enforce,
            "passed": int(watch_ok and no_enforce),
        })

    snow_left = c1r_snow.get(1150, {})
    snow_right = c1r3_snow.get(1150, {})
    snowfall_1150_observer_ok = int(
        bool(snow_right)
        and snow_right.get("action_label", "") == snow_left.get("action_label", "")
        and snow_right.get("q1_sic_arbitration_label", "") == snow_left.get("q1_sic_arbitration_label", "")
        and "q1_sic_observer_isolated_enabled" in snow_right
        and truthy(snow_right.get("q1_sic_observer_isolated_enabled"))
        and truthy(snow_right.get("q1_sic_observer_post_decision_only"))
        and truthy(snow_right.get("q1_sic_observer_used_immutable_snapshot"))
        and not truthy(snow_right.get("q1_sic_observer_mutated_control_state"))
        and not truthy(snow_right.get("q1_sic_observer_gt_signal_used"))
        and not truthy(snow_right.get("q1_sic_observer_would_touch_normal_frame"))
    )
    row_checks.append({
        "check": "snowFall_1150_observer",
        "frame": 1150,
        "c1r_action": snow_left.get("action_label", ""),
        "c1r3_action": snow_right.get("action_label", ""),
        "c1r_label": snow_left.get("q1_sic_arbitration_label", ""),
        "c1r3_label": snow_right.get("q1_sic_arbitration_label", ""),
        "observer_enabled": snow_right.get("q1_sic_observer_isolated_enabled", ""),
        "observer_action_is_detect": snow_right.get("q1_sic_observer_action_is_detect", ""),
        "observer_event_risk_pressure": snow_right.get("q1_sic_observer_event_risk_pressure", ""),
        "observer_detector_pressure": snow_right.get("q1_sic_observer_detector_pressure", ""),
        "observer_would_select_shadow": snow_right.get("q1_sic_observer_would_select_shadow", ""),
        "observer_reject_reason": snow_right.get("q1_sic_observer_reject_reason", ""),
        "passed": snowfall_1150_observer_ok,
    })

    c1r3_columns = set().union(*(row.keys() for row in c1r3_all)) if c1r3_all else set()
    observer_columns_present = int(all(column in c1r3_columns for column in OBSERVER_COLUMNS))
    observer_mutated_max = max_col(c1r3_all, "q1_sic_observer_mutated_control_state")
    observer_gt_max = max_col(c1r3_all, "q1_sic_observer_gt_signal_used")
    observer_touch_max = max_col(c1r3_all, "q1_sic_observer_would_touch_normal_frame")
    observer_pressure_memory_enabled_max = max_col(c1r3_all, "q1_sic_observer_pressure_memory_enabled")
    old_pressure_memory_active_max = max_col(c1r3_all, "q1_sic_detector_action_probe_pressure_memory_active")
    old_stable_snapshot_enabled_max = max_col(c1r3_all, "q1_sic_detector_action_probe_stable_snapshot_enabled")
    q1b_enforcement_label_rows = sum(
        int(row.get("q1_sic_arbitration_label") == "FORCE_EVENT_RISK_EMPTY_DETECT_PROTECTION")
        for row in c1r3_all
    )
    observer_isolation_ok = int(
        observer_columns_present
        and observer_mutated_max == 0
        and observer_gt_max == 0
        and observer_touch_max == 0
        and observer_pressure_memory_enabled_max == 0
        and old_pressure_memory_active_max == 0
        and old_stable_snapshot_enabled_max == 0
        and q1b_enforcement_label_rows == 0
    )

    normal_frame_interventions = count_normal_interventions(c1r3_root)
    q1_touch_max = max_col(c1r3_all, "q1_sic_would_touch_normal_frame")
    gt_decision_max = max_col(c1r3_all, "q1_sic_gt_signal_used_for_decision")
    normal_safety_ok = int(normal_frame_interventions == 0 and q1_touch_max == 0 and gt_decision_max == 0)

    behavior_identity_ok = int(len(behavior_deltas) == 0)
    all_pass = int(all([
        behavior_identity_ok,
        parking_preserved_ok,
        copy_preserved_ok,
        port_watch_preserved_ok,
        observer_isolation_ok,
        snowfall_1150_observer_ok,
        normal_safety_ok,
        no_port_retighten_enforcement_ok,
    ]))
    if all_pass:
        decision = "PASS_OBSERVER_ISOLATION_WITH_KNOWN_SNOWFALL_BLOCKER"
    elif not behavior_identity_ok:
        decision = "FAIL_BEHAVIOR_IDENTITY"
    elif not observer_isolation_ok:
        decision = "FAIL_OBSERVER_ISOLATION"
    elif not parking_preserved_ok:
        decision = "FAIL_PARKING_REGRESSION"
    elif not copy_preserved_ok:
        decision = "FAIL_COPYMACHINE_REGRESSION"
    elif not port_watch_preserved_ok:
        decision = "FAIL_PORT_WATCH_REGRESSION"
    elif not normal_safety_ok:
        decision = "FAIL_NORMAL_SAFETY"
    else:
        decision = "FAIL_OBSERVER_ISOLATION"

    delta_counts: Dict[str, int] = {}
    for delta in behavior_deltas:
        field = str(delta.get("field", ""))
        delta_counts[field] = delta_counts.get(field, 0) + 1
    summary = [{
        "behavior_identity_ok": behavior_identity_ok,
        "behavior_delta_rows": len(behavior_deltas),
        "action_label_deltas": delta_counts.get("action_label", 0),
        "proposal_deltas": delta_counts.get("ai_intervention_applied", 0),
        "detector_request_deltas": delta_counts.get("ai_intervention_detector_requested", 0),
        "selected_mode_deltas": delta_counts.get("selected_mode", 0)
            + delta_counts.get("selected_mode_before_guard", 0)
            + delta_counts.get("selected_mode_after_guard", 0),
        "q1_label_deltas": delta_counts.get("q1_sic_arbitration_label", 0),
        "protected_accounting_deltas": delta_counts.get("protected_fn_accounting", 0),
        "unprotected_accounting_deltas": delta_counts.get("unprotected_fn_accounting", 0),
        "parking_preserved_ok": parking_preserved_ok,
        "c1r_parking_proposal": f"{c1r_parking_proposal:.5f}",
        "c1r3_parking_proposal": f"{c1r3_parking_proposal:.5f}",
        "c1r3_parking_detector": f"{c1r3_parking_detector:.5f}",
        "c1r3_parking_unprotected_fn": c1r3_parking_unprotected,
        "copyMachine_preserved_ok": copy_preserved_ok,
        "port_watch_preserved_ok": port_watch_preserved_ok,
        "observer_isolation_ok": observer_isolation_ok,
        "observer_columns_present": observer_columns_present,
        "observer_mutated_control_state_max": observer_mutated_max,
        "observer_gt_signal_used_max": observer_gt_max,
        "observer_would_touch_normal_frame_max": observer_touch_max,
        "observer_pressure_memory_enabled_max": observer_pressure_memory_enabled_max,
        "old_probe_pressure_memory_active_max": old_pressure_memory_active_max,
        "old_probe_stable_snapshot_enabled_max": old_stable_snapshot_enabled_max,
        "q1_sic1b_enforcement_label_rows": q1b_enforcement_label_rows,
        "snowfall_1150_observer_ok": snowfall_1150_observer_ok,
        "normal_safety_ok": normal_safety_ok,
        "normal_frame_interventions": normal_frame_interventions,
        "q1_sic_would_touch_normal_frame_max": q1_touch_max,
        "q1_sic_gt_signal_used_for_decision_max": gt_decision_max,
        "no_port_retighten_enforcement_ok": no_port_retighten_enforcement_ok,
        "decision": decision,
    }]

    write_csv(out / "q1_sic1c1r3_observer_isolation_summary.csv", summary, list(summary[0].keys()))
    check_fields = sorted({key for row in row_checks for key in row.keys()})
    write_csv(out / "q1_sic1c1r3_observer_isolation_row_checks.csv", row_checks, check_fields)
    delta_fields = ["category", "video", "frame", "field", "c1r", "c1r3"]
    write_csv(out / "q1_sic1c1r3_behavior_delta.csv", behavior_deltas, delta_fields)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
