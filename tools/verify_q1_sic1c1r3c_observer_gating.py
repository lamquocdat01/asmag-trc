"""Verify Q1-SIC-1C1R3C same-source observer gating."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
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
    "selected_mode",
    "selected_mode_before_guard",
    "selected_mode_after_guard",
    "yolo_called",
    "ai_intervention_detector_requested",
    "ai_intervention_applied",
    "q1_sic_arbitration_active",
    "q1_sic_arbitration_label",
    "q1_sic_owner",
    "q1_sic_watch_only",
]
NUMERIC_COLUMNS = {
    "yolo_called",
    "ai_intervention_detector_requested",
    "ai_intervention_applied",
    "q1_sic_arbitration_active",
    "q1_sic_watch_only",
}
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
LIVE_PROBE_COLUMNS = [
    "q1_sic_detector_action_probe_enabled",
    "q1_sic_detector_action_probe_active",
    "q1_sic_detector_action_probe_video_owner",
    "q1_sic_detector_action_probe_action_is_detect",
    "q1_sic_detector_action_probe_event_risk_pressure",
    "q1_sic_detector_action_probe_detector_pressure",
    "q1_sic_detector_action_probe_detector_blocked",
    "q1_sic_detector_action_probe_cooldown_active",
    "q1_sic_detector_action_probe_proposal_absent",
    "q1_sic_detector_action_probe_runtime_empty_proxy",
    "q1_sic_detector_action_probe_would_select_shadow",
    "q1_sic_detector_action_probe_reject_reason",
    "q1_sic_detector_action_probe_gt_signal_used",
    "q1_sic_detector_action_probe_would_touch_normal_frame",
    "q1_sic_detector_action_probe_stable_snapshot_enabled",
    "q1_sic_detector_action_probe_pressure_memory_active",
]


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str] | None = None) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    fields.append(key)
                    seen.add(key)
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


def norm(value: object, numeric: bool = False) -> str:
    if value in (None, "NA"):
        return ""
    text = str(value).strip()
    if numeric and text != "":
        return "1" if number(text) > 0 else "0"
    return text


def frame(row: Dict[str, str]) -> int:
    for key in ("raw_frame_id", "frame_id", "frame", "frame_idx"):
        if row.get(key) not in (None, ""):
            return int(float(row[key]))
    return -1


def row_key(row: Dict[str, str]) -> Tuple[str, str, int, str]:
    return (
        row.get("category", ""),
        row.get("video", ""),
        frame(row),
        row.get("pipeline", PIPELINE),
    )


def guarded_path(root: Path, video: Sequence[str]) -> Path:
    return root / "raw_results" / video[0] / video[1] / PIPELINE / "frame_metrics.csv"


def load_video(root: Path, video: Sequence[str]) -> List[Dict[str, str]]:
    return read_csv(guarded_path(root, video))


def by_frame(rows: Iterable[Dict[str, str]]) -> Dict[int, Dict[str, str]]:
    return {frame(row): row for row in rows}


def all_guarded_rows(root: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path in sorted(root.glob(f"raw_results/*/*/{PIPELINE}/frame_metrics.csv")):
        try:
            raw_idx = path.parts.index("raw_results")
            category = path.parts[raw_idx + 1]
            video = path.parts[raw_idx + 2]
        except (ValueError, IndexError):
            category = ""
            video = ""
        for row in read_csv(path):
            row.setdefault("category", category)
            row.setdefault("video", video)
            row.setdefault("pipeline", PIPELINE)
            rows.append(row)
    return rows


def video_summary(root: Path, category: str, video: str) -> Dict[str, str]:
    for row in read_csv(root / "ai_intervention_video_summary.csv"):
        if row.get("category") == category and row.get("video") == video:
            return row
    return {}


def rate(rows: List[Dict[str, str]], column: str) -> float:
    if not rows:
        return 0.0
    return sum(int(truthy(row.get(column))) for row in rows) / float(len(rows))


def is_fn(row: Dict[str, str]) -> bool:
    return str(row.get("Event_State") or row.get("frame_state") or "") == "FN"


def is_normal(row: Dict[str, str]) -> bool:
    state = str(row.get("Event_State") or row.get("frame_state") or "").strip().lower()
    return state in {"tn", "normal", "background"}


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


def normal_intervention(row: Dict[str, str]) -> bool:
    return bool(is_normal(row) and (truthy(row.get("ai_intervention_applied")) or truthy(row.get("ai_intervention_detector_requested"))))


def max_col(rows: List[Dict[str, str]], column: str) -> float:
    return max([number(row.get(column)) for row in rows] or [0.0])


def count_duplicates(rows: List[Dict[str, str]]) -> Tuple[int, int]:
    counts = Counter(row_key(row) for row in rows)
    duplicate_counts = [count for count in counts.values() if count > 1]
    return len(duplicate_counts), sum(count - 1 for count in duplicate_counts)


def compare_behavior(left_rows: List[Dict[str, str]], right_rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    left = {row_key(row): row for row in left_rows}
    right = {row_key(row): row for row in right_rows}
    deltas: List[Dict[str, object]] = []
    for key in sorted(set(left) | set(right)):
        lrow = left.get(key, {})
        rrow = right.get(key, {})
        if not lrow or not rrow:
            deltas.append({
                "category": key[0],
                "video": key[1],
                "frame": key[2],
                "pipeline": key[3],
                "field": "row_presence",
                "fresh_c1r": "present" if lrow else "missing",
                "r3c": "present" if rrow else "missing",
            })
            continue
        for column in BEHAVIOR_COLUMNS:
            lval = norm(lrow.get(column, ""), column in NUMERIC_COLUMNS)
            rval = norm(rrow.get(column, ""), column in NUMERIC_COLUMNS)
            if lval != rval:
                deltas.append({
                    "category": key[0],
                    "video": key[1],
                    "frame": key[2],
                    "pipeline": key[3],
                    "field": column,
                    "fresh_c1r": lrow.get(column, ""),
                    "r3c": rrow.get(column, ""),
                })
        for field, lval, rval in [
            ("protected_fn_accounting", int(protected(lrow)), int(protected(rrow))),
            ("unprotected_fn_accounting", int(unprotected(lrow)), int(unprotected(rrow))),
            ("normal_frame_intervention_indicator", int(normal_intervention(lrow)), int(normal_intervention(rrow))),
        ]:
            if lval != rval:
                deltas.append({
                    "category": key[0],
                    "video": key[1],
                    "frame": key[2],
                    "pipeline": key[3],
                    "field": field,
                    "fresh_c1r": lval,
                    "r3c": rval,
                })
    return deltas


def summarize_deltas(deltas: List[Dict[str, object]], left_rows: List[Dict[str, str]], right_rows: List[Dict[str, str]]) -> Dict[str, object]:
    by_field = Counter(str(row.get("field", "")) for row in deltas)
    left_dup_keys, left_dup_extra = count_duplicates(left_rows)
    right_dup_keys, right_dup_extra = count_duplicates(right_rows)
    left_keys = {row_key(row) for row in left_rows}
    right_keys = {row_key(row) for row in right_rows}
    return {
        "fresh_c1r_guarded_rows": len(left_rows),
        "r3c_guarded_rows": len(right_rows),
        "row_count_match": int(len(left_rows) == len(right_rows)),
        "overlapping_keys": len(left_keys & right_keys),
        "row_presence_deltas": by_field.get("row_presence", 0),
        "fresh_c1r_duplicate_keys": left_dup_keys,
        "fresh_c1r_duplicate_extra_rows": left_dup_extra,
        "r3c_duplicate_keys": right_dup_keys,
        "r3c_duplicate_extra_rows": right_dup_extra,
        "behavior_delta_rows": len(deltas),
        "action_label_deltas": by_field.get("action_label", 0),
        "proposal_deltas": by_field.get("ai_intervention_applied", 0),
        "detector_request_deltas": by_field.get("ai_intervention_detector_requested", 0),
        "yolo_called_deltas": by_field.get("yolo_called", 0),
        "selected_mode_deltas": by_field.get("selected_mode", 0)
            + by_field.get("selected_mode_before_guard", 0)
            + by_field.get("selected_mode_after_guard", 0),
        "q1_label_deltas": by_field.get("q1_sic_arbitration_label", 0),
        "q1_active_deltas": by_field.get("q1_sic_arbitration_active", 0),
        "q1_owner_deltas": by_field.get("q1_sic_owner", 0),
        "q1_watch_only_deltas": by_field.get("q1_sic_watch_only", 0),
        "protected_accounting_deltas": by_field.get("protected_fn_accounting", 0),
        "unprotected_accounting_deltas": by_field.get("unprotected_fn_accounting", 0),
        "normal_frame_intervention_indicator_deltas": by_field.get("normal_frame_intervention_indicator", 0),
    }


def progress_summary(root: Path) -> Dict[str, object]:
    rows = read_csv(root / "run_progress.csv")
    completed = sum(1 for row in rows if row.get("status") == "completed")
    failed = sum(1 for row in rows if row.get("status") == "failed")
    compare_completed = int((root / "asmag_tr_final_comparison.csv").exists() and (root / "comparison_summary.csv").exists())
    return {
        "jobs_total": len(rows),
        "jobs_completed": completed,
        "jobs_failed": failed,
        "compare_completed": compare_completed,
        "execution_ok": int(len(rows) == 56 and completed == 56 and failed == 0 and compare_completed),
    }


def live_probe_delta_count(fresh_rows: List[Dict[str, str]], r3c_rows: List[Dict[str, str]]) -> int:
    left = {row_key(row): row for row in fresh_rows}
    right = {row_key(row): row for row in r3c_rows}
    delta_count = 0
    for key in sorted(set(left) & set(right)):
        for column in LIVE_PROBE_COLUMNS:
            if norm(left[key].get(column, ""), column not in {"q1_sic_detector_action_probe_video_owner", "q1_sic_detector_action_probe_reject_reason"}) != norm(
                right[key].get(column, ""),
                column not in {"q1_sic_detector_action_probe_video_owner", "q1_sic_detector_action_probe_reject_reason"},
            ):
                delta_count += 1
    return delta_count


def observer_summary(fresh_rows: List[Dict[str, str]], r3c_rows: List[Dict[str, str]]) -> Dict[str, object]:
    columns = set()
    for row in r3c_rows:
        columns.update(row.keys())
    present = int(all(column in columns for column in OBSERVER_COLUMNS))
    probe_deltas = live_probe_delta_count(fresh_rows, r3c_rows)
    return {
        "observer_columns_present": present,
        "observer_enabled_max": max_col(r3c_rows, "q1_sic_observer_isolated_enabled"),
        "observer_post_decision_only_max": max_col(r3c_rows, "q1_sic_observer_post_decision_only"),
        "observer_used_immutable_snapshot_max": max_col(r3c_rows, "q1_sic_observer_used_immutable_snapshot"),
        "observer_mutated_control_state_max": max_col(r3c_rows, "q1_sic_observer_mutated_control_state"),
        "observer_gt_signal_used_max": max_col(r3c_rows, "q1_sic_observer_gt_signal_used"),
        "observer_would_touch_normal_frame_max": max_col(r3c_rows, "q1_sic_observer_would_touch_normal_frame"),
        "observer_pressure_memory_enabled_max": max_col(r3c_rows, "q1_sic_observer_pressure_memory_enabled"),
        "observer_pressure_memory_used_max": max_col(r3c_rows, "q1_sic_observer_pressure_memory_used"),
        "live_probe_delta_count": probe_deltas,
        "live_probe_behavior_preserved": int(probe_deltas == 0),
    }


def local_gates(root: Path, fresh_root: Path) -> Tuple[Dict[str, object], List[Dict[str, object]]]:
    rows = all_guarded_rows(root)
    parking = load_video(root, PARKING)
    fresh_parking = load_video(fresh_root, PARKING)
    parking_summary = video_summary(root, *PARKING)
    fresh_parking_summary = video_summary(fresh_root, *PARKING)
    parking_proposal = number(parking_summary.get("intervention_rate"), rate(parking, "ai_intervention_applied"))
    fresh_parking_proposal = number(fresh_parking_summary.get("intervention_rate"), rate(fresh_parking, "ai_intervention_applied"))
    parking_detector = number(parking_summary.get("detector_request_rate"), rate(parking, "ai_intervention_detector_requested"))
    parking_unprotected = sum(int(unprotected(row)) for row in parking)
    parking_ok = int(parking_unprotected == 0 and parking_detector == 0.0 and parking_proposal <= fresh_parking_proposal + 0.0001)

    row_checks: List[Dict[str, object]] = []
    copy_rows = by_frame(load_video(root, COPY))
    copy_ok = 1
    for frame_id in COPY_FRAMES:
        row = copy_rows.get(frame_id, {})
        ok = int(protected(row) and not unprotected(row))
        copy_ok = int(copy_ok and ok)
        row_checks.append({
            "check": "copyMachine_protected",
            "category": COPY[0],
            "video": COPY[1],
            "frame": frame_id,
            "action_label": row.get("action_label", ""),
            "q1_sic_arbitration_label": row.get("q1_sic_arbitration_label", ""),
            "ai_intervention_applied": row.get("ai_intervention_applied", ""),
            "protected": int(protected(row)),
            "unprotected": int(unprotected(row)),
            "passed": ok,
        })

    port_rows = by_frame(load_video(root, PORT))
    port_ok = 1
    no_port_enforce_ok = 1
    for frame_id in PORT_FRAMES:
        row = port_rows.get(frame_id, {})
        watch_ok = int(
            row.get("q1_sic_arbitration_label") == "WATCH_ONLY_PORT_RETIGHTEN"
            and truthy(row.get("q1_sic_watch_only"))
            and row.get("q1_sic_owner") == "detector_retighten"
            and row.get("q1_sic_reference_step") == "Step4E4"
        )
        no_enforce = int(
            number(row.get("q1_sic_pre_detector_request")) == number(row.get("q1_sic_post_detector_request"))
            and number(row.get("ai_intervention_detector_requested")) == 0
        )
        port_ok = int(port_ok and watch_ok)
        no_port_enforce_ok = int(no_port_enforce_ok and no_enforce)
        row_checks.append({
            "check": "port_watch_preserved",
            "category": PORT[0],
            "video": PORT[1],
            "frame": frame_id,
            "q1_sic_arbitration_label": row.get("q1_sic_arbitration_label", ""),
            "q1_sic_watch_only": row.get("q1_sic_watch_only", ""),
            "q1_sic_owner": row.get("q1_sic_owner", ""),
            "q1_sic_reference_step": row.get("q1_sic_reference_step", ""),
            "detector_unchanged": no_enforce,
            "passed": int(watch_ok and no_enforce),
        })

    normal_frame_interventions = sum(
        int(number(row.get("normal_frame_intervention_count")) > 0)
        for row in read_csv(root / "ai_intervention_video_summary.csv")
    )
    q1_touch_max = max_col(rows, "q1_sic_would_touch_normal_frame")
    gt_decision_max = max_col(rows, "q1_sic_gt_signal_used_for_decision")
    normal_ok = int(normal_frame_interventions == 0 and q1_touch_max == 0 and gt_decision_max == 0)

    q1b_proxy_rows = sum(int(truthy(row.get("q1_sic_event_risk_empty_detect_proxy"))) for row in rows)
    q1b_label_rows = sum(
        int(row.get("q1_sic_arbitration_label") == "FORCE_EVENT_RISK_EMPTY_DETECT_PROTECTION")
        for row in rows
    )
    snow_ok = int(q1b_proxy_rows == 0 and q1b_label_rows == 0)
    local_ok = int(all([parking_ok, copy_ok, port_ok, no_port_enforce_ok, normal_ok, snow_ok]))
    return {
        "parking_preserved_ok": parking_ok,
        "fresh_c1r_parking_proposal": f"{fresh_parking_proposal:.5f}",
        "r3c_parking_proposal": f"{parking_proposal:.5f}",
        "r3c_parking_detector": f"{parking_detector:.5f}",
        "r3c_parking_unprotected_fn": parking_unprotected,
        "copyMachine_preserved_ok": copy_ok,
        "port_watch_preserved_ok": port_ok,
        "no_port_retighten_enforcement_ok": no_port_enforce_ok,
        "normal_safety_ok": normal_ok,
        "normal_frame_interventions": normal_frame_interventions,
        "q1_sic_would_touch_normal_frame_max": q1_touch_max,
        "q1_sic_gt_signal_used_for_decision_max": gt_decision_max,
        "no_new_snowfall_enforcement_ok": snow_ok,
        "q1_sic1b_proxy_active_rows": q1b_proxy_rows,
        "q1_sic1b_enforcement_label_rows": q1b_label_rows,
        "local_gates_ok": local_ok,
    }, row_checks


def snowfall_1150_check(fresh_root: Path, r3c_root: Path) -> Dict[str, object]:
    fresh = by_frame(load_video(fresh_root, SNOW)).get(1150, {})
    r3c = by_frame(load_video(r3c_root, SNOW)).get(1150, {})
    fields = ["action_label", "ai_intervention_applied", "ai_intervention_detector_requested", "q1_sic_arbitration_label"]
    match = int(bool(fresh and r3c) and all(norm(fresh.get(field, ""), field != "action_label" and field != "q1_sic_arbitration_label") == norm(r3c.get(field, ""), field != "action_label" and field != "q1_sic_arbitration_label") for field in fields))
    observer_ok = int(
        bool(r3c)
        and truthy(r3c.get("q1_sic_observer_isolated_enabled"))
        and truthy(r3c.get("q1_sic_observer_post_decision_only"))
        and truthy(r3c.get("q1_sic_observer_used_immutable_snapshot"))
        and not truthy(r3c.get("q1_sic_observer_gt_signal_used"))
        and not truthy(r3c.get("q1_sic_observer_would_touch_normal_frame"))
        and not truthy(r3c.get("q1_sic_observer_mutated_control_state"))
    )
    return {
        "frame": 1150,
        "fresh_action": fresh.get("action_label", ""),
        "r3c_action": r3c.get("action_label", ""),
        "fresh_proposal": fresh.get("ai_intervention_applied", ""),
        "r3c_proposal": r3c.get("ai_intervention_applied", ""),
        "fresh_detector_request": fresh.get("ai_intervention_detector_requested", ""),
        "r3c_detector_request": r3c.get("ai_intervention_detector_requested", ""),
        "fresh_q1_label": fresh.get("q1_sic_arbitration_label", ""),
        "r3c_q1_label": r3c.get("q1_sic_arbitration_label", ""),
        "r3c_live_probe_enabled": r3c.get("q1_sic_detector_action_probe_enabled", ""),
        "r3c_observer_enabled": r3c.get("q1_sic_observer_isolated_enabled", ""),
        "r3c_observer_gt_signal_used": r3c.get("q1_sic_observer_gt_signal_used", ""),
        "r3c_observer_would_touch_normal_frame": r3c.get("q1_sic_observer_would_touch_normal_frame", ""),
        "r3c_observer_reject_reason": r3c.get("q1_sic_observer_reject_reason", ""),
        "same_source_row_match": match,
        "observer_safe": observer_ok,
        "snowFall_1150_same_source_ok": int(match and observer_ok),
    }


def failure_rows(decision: str, summary: Dict[str, object], observer: Dict[str, object], gates: Dict[str, object]) -> List[Dict[str, object]]:
    return [
        {"classification": "live probe behavior not preserved", "is_primary": int(observer.get("live_probe_behavior_preserved") == 0), "evidence": f"live_probe_delta_count={observer.get('live_probe_delta_count')}"},
        {"classification": "observer still changes behavior", "is_primary": int(decision == "FAIL_SAME_SOURCE_IDENTITY"), "evidence": f"behavior_delta_rows={summary.get('behavior_delta_rows')}"},
        {"classification": "observer telemetry missing", "is_primary": int(decision == "FAIL_OBSERVER_TELEMETRY"), "evidence": f"observer_columns_present={observer.get('observer_columns_present')}"},
        {"classification": "config mismatch", "is_primary": 0, "evidence": "R3C intentionally differs from fresh C1R only by name/profile and observer flags"},
        {"classification": "verifier mismatch", "is_primary": int(decision == "FAIL_ALIGNMENT"), "evidence": f"row_presence_deltas={summary.get('row_presence_deltas')};duplicate_extra={summary.get('fresh_c1r_duplicate_extra_rows')}/{summary.get('r3c_duplicate_extra_rows')}"},
        {"classification": "normal-frame safety violation", "is_primary": 0, "evidence": f"normal_safety_ok={gates.get('normal_safety_ok')}"},
        {"classification": "GT leakage", "is_primary": 0, "evidence": f"q1_sic_gt_signal_used_for_decision_max={gates.get('q1_sic_gt_signal_used_for_decision_max')};observer_gt={observer.get('observer_gt_signal_used_max')}"},
        {"classification": "parking regression", "is_primary": 0, "evidence": f"parking_preserved_ok={gates.get('parking_preserved_ok')}"},
        {"classification": "copyMachine regression", "is_primary": 0, "evidence": f"copyMachine_preserved_ok={gates.get('copyMachine_preserved_ok')}"},
        {"classification": "port watch regression", "is_primary": 0, "evidence": f"port_watch_preserved_ok={gates.get('port_watch_preserved_ok')}"},
        {"classification": "unintended new snowFall enforcement beyond fresh C1R", "is_primary": 0, "evidence": f"no_new_snowfall_enforcement_ok={gates.get('no_new_snowfall_enforcement_ok')}"},
        {"classification": "unintended port retighten", "is_primary": 0, "evidence": f"no_port_retighten_enforcement_ok={gates.get('no_port_retighten_enforcement_ok')}"},
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Q1-SIC-1C1R3C observer gating.")
    parser.add_argument("--fresh-c1r-root", required=True)
    parser.add_argument("--r3c-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    fresh_root = Path(args.fresh_c1r_root)
    r3c_root = Path(args.r3c_root)
    out = Path(args.out)

    fresh_rows = all_guarded_rows(fresh_root)
    r3c_rows = all_guarded_rows(r3c_root)
    deltas = compare_behavior(fresh_rows, r3c_rows)
    summary = summarize_deltas(deltas, fresh_rows, r3c_rows)
    execution = progress_summary(r3c_root)
    observer = observer_summary(fresh_rows, r3c_rows)
    gates, row_checks = local_gates(r3c_root, fresh_root)
    snow = snowfall_1150_check(fresh_root, r3c_root)

    alignment_ok = int(
        summary["row_count_match"]
        and summary["row_presence_deltas"] == 0
        and summary["fresh_c1r_duplicate_extra_rows"] == 0
        and summary["r3c_duplicate_extra_rows"] == 0
    )
    identity_ok = int(summary["behavior_delta_rows"] == 0 and observer["live_probe_behavior_preserved"] == 1)
    observer_ok = int(
        observer["observer_columns_present"]
        and observer["observer_enabled_max"] == 1
        and observer["observer_mutated_control_state_max"] == 0
        and observer["observer_gt_signal_used_max"] == 0
        and observer["observer_would_touch_normal_frame_max"] == 0
        and observer["observer_pressure_memory_enabled_max"] == 0
        and observer["observer_pressure_memory_used_max"] == 0
    )
    local_ok = int(gates["local_gates_ok"] and snow["snowFall_1150_same_source_ok"])

    if not alignment_ok:
        decision = "FAIL_ALIGNMENT"
    elif not identity_ok:
        decision = "FAIL_SAME_SOURCE_IDENTITY"
    elif not observer_ok:
        decision = "FAIL_OBSERVER_TELEMETRY"
    elif not int(execution["execution_ok"]) or not local_ok:
        decision = "FAIL_LOCAL_GATES"
    else:
        decision = "PASS_SAME_SOURCE_OBSERVER_GATING"

    summary.update({
        **execution,
        "same_source_identity_ok": identity_ok,
        "observer_telemetry_ok": observer_ok,
        "local_gates_ok": local_ok,
        "alignment_ok": alignment_ok,
        "decision": decision,
    })
    local_summary = {**execution, **gates, "snowFall_1150_same_source_ok": snow["snowFall_1150_same_source_ok"], "decision": decision}

    write_csv(out / "fresh_c1r_vs_r3c_behavior_delta.csv", deltas)
    write_csv(out / "fresh_c1r_vs_r3c_summary.csv", [summary])
    write_csv(out / "fresh_c1r_vs_r3c_local_gates.csv", [local_summary])
    write_csv(out / "fresh_c1r_vs_r3c_local_gate_row_checks.csv", row_checks)
    write_csv(out / "r3c_observer_telemetry_summary.csv", [observer])
    write_csv(out / "r3c_snowfall_1150_same_source_check.csv", [snow])
    write_csv(out / "r3c_failure_classification.csv", failure_rows(decision, summary, observer, gates))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
