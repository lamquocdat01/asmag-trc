"""Verify Q1-SIC-1B runtime-safe empty-detect proxy before dry-run.

Analysis-only. Reads existing Q1-SIC-1 and Q1-SIC-1A outputs and writes a
verdict bundle for deciding whether the scoped Q1-SIC-1B dry-run is allowed.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, Iterable, List


PIPELINE = "ASMAG_TR_CONTROLLER_ONLINE_GUARDED"
SNOW_PATH = Path("raw_results") / "badWeather" / "snowFall" / PIPELINE / "frame_metrics.csv"
PORT_PATH = Path("raw_results") / "lowFramerate" / "port_0_17fps" / PIPELINE / "frame_metrics.csv"
CONTEXT_FRAMES = {1120, 1125, 1130, 1135, 1140, 1145, 1150, 1155, 1160, 1165, 1170}
QUIET_TN_FRAMES = {1160, 1165, 1170}
PORT_WATCH_FRAMES = {1350, 1355}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
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
    for key in ("frame_id", "frame", "raw_frame_id", "frame_idx"):
        if row.get(key) not in (None, ""):
            return int(float(row[key]))
    return -1


def action(row: Dict[str, str]) -> str:
    return str(row.get("action_label") or row.get("ai_intervention_final_action") or "")


def is_detect_action(row: Dict[str, str]) -> bool:
    return action(row).upper().startswith("DETECT_")


def proxy_parts(row: Dict[str, str]) -> Dict[str, int]:
    detector_pressure = int(
        truthy(row.get("ai_detector_needed_pred"))
        or truthy(row.get("ai_detector_request_blocked_no_refresh_model"))
        or truthy(row.get("forced_refresh_cooldown_active"))
    )
    detector_empty = int(
        number(row.get("pred_object_count")) <= 0
        and number(row.get("candidate_ACC_area")) <= 0
        and number(row.get("candidate_P3_area")) <= 0
        and number(row.get("candidate_FAST_area")) <= 0
    )
    proposal_absent = int(
        not truthy(row.get("ai_intervention_applied"))
        and not truthy(row.get("ai_intervention_detector_requested"))
    )
    return {
        "active_event_memory": int(truthy(row.get("active_event_memory"))),
        "risk_high": int(truthy(row.get("ai_intervention_risk_high"))),
        "guard_active": int(truthy(row.get("ai_intervention_guard_active"))),
        "detector_pressure": detector_pressure,
        "recent_active_event": int(number(row.get("frames_since_active_prediction"), 999.0) <= 1),
        "detect_action": int(is_detect_action(row)),
        "proposal_absent": proposal_absent,
        "detector_empty": detector_empty,
        "gt_signal_used_for_decision": 0,
    }


def proxy_selected(row: Dict[str, str]) -> bool:
    parts = proxy_parts(row)
    return bool(
        parts["active_event_memory"]
        and parts["risk_high"]
        and parts["guard_active"]
        and parts["detector_pressure"]
        and parts["recent_active_event"]
        and parts["detect_action"]
        and parts["proposal_absent"]
        and parts["detector_empty"]
    )


def state(row: Dict[str, str]) -> str:
    return str(row.get("Event_State") or row.get("frame_state") or "")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Q1-SIC-1B runtime proxy on existing outputs.")
    parser.add_argument("--sic1-root", required=True)
    parser.add_argument("--sic1a-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    sic1_root = Path(args.sic1_root)
    sic1a_root = Path(args.sic1a_root)
    out = Path(args.out)

    snow_rows = read_csv(sic1_root / SNOW_PATH)
    port_rows = read_csv(sic1_root / PORT_PATH)
    sic1a_classification = read_csv(sic1a_root / "snowfall_mismatch_classification.csv")

    snow_by_frame = {frame(row): row for row in snow_rows}
    port_by_frame = {frame(row): row for row in port_rows}

    verdict_rows: List[Dict[str, object]] = []
    candidate_rows: List[Dict[str, object]] = []
    for frame_id in sorted(CONTEXT_FRAMES):
        row = snow_by_frame.get(frame_id, {})
        parts = proxy_parts(row)
        selected = int(bool(row) and proxy_selected(row))
        candidate_rows.append({
            "category": "badWeather",
            "video": "snowFall",
            "frame_id": frame_id,
            "Event_State_audit_only": state(row),
            "action_label": action(row),
            "selected": selected,
            **parts,
        })

    frame_1150_selected = int(proxy_selected(snow_by_frame.get(1150, {})))
    quiet_tn_selected = sum(
        int(proxy_selected(snow_by_frame.get(frame_id, {})))
        for frame_id in QUIET_TN_FRAMES
    )
    active_event_memory_only_selected = sum(
        int(
            proxy_selected(row)
            and truthy(row.get("active_event_memory"))
            and not truthy(row.get("ai_intervention_risk_high"))
        )
        for row in snow_rows
    )
    detect_acc_rows = [row for row in snow_rows if action(row).upper() == "DETECT_ACC"]
    detect_acc_selected = [row for row in detect_acc_rows if proxy_selected(row)]
    all_detect_acc_classified_unsafe = int(bool(detect_acc_rows) and len(detect_acc_selected) == len(detect_acc_rows))
    gt_signal_used_for_decision = 0
    would_touch_normal_frame = sum(
        int(proxy_selected(row) and state(row) not in {"FN", "TP"})
        for row in snow_rows
    )
    port_watch_only_preserved = int(all(
        port_by_frame.get(frame_id, {}).get("q1_sic_arbitration_label") == "WATCH_ONLY_PORT_RETIGHTEN"
        and port_by_frame.get(frame_id, {}).get("q1_sic_watch_only") in {"1", 1}
        for frame_id in PORT_WATCH_FRAMES
    ))
    split_branch_ok = port_watch_only_preserved

    checks = {
        "snowfall_1150_selected": frame_1150_selected,
        "quiet_tn_1160_1165_1170_selected": quiet_tn_selected,
        "active_event_memory_only_selected": active_event_memory_only_selected,
        "all_detect_acc_classified_unsafe": all_detect_acc_classified_unsafe,
        "gt_signal_used_for_decision": gt_signal_used_for_decision,
        "would_touch_normal_frame": would_touch_normal_frame,
        "port_watch_only_preserved": port_watch_only_preserved,
        "split_branch_ok": split_branch_ok,
    }
    expectations = {
        "snowfall_1150_selected": 1,
        "quiet_tn_1160_1165_1170_selected": 0,
        "active_event_memory_only_selected": 0,
        "all_detect_acc_classified_unsafe": 0,
        "gt_signal_used_for_decision": 0,
        "would_touch_normal_frame": 0,
        "port_watch_only_preserved": 1,
        "split_branch_ok": 1,
    }
    for check, observed in checks.items():
        expected = expectations[check]
        verdict_rows.append({
            "check": check,
            "observed": observed,
            "expected": expected,
            "passed": int(observed == expected),
            "details": "runtime proxy uses active_event_memory/risk_high/guard/detector_pressure/detect_action/proposal_absent/detector_empty only",
        })

    dryrun_allowed = int(all(checks[key] == expectations[key] for key in expectations))
    summary = [{
        **checks,
        "detect_acc_rows_checked": len(detect_acc_rows),
        "detect_acc_rows_selected": len(detect_acc_selected),
        "sic1a_classification_rows_read": len(sic1a_classification),
        "decision": "PASS_SHADOW" if dryrun_allowed else "FAIL_SHADOW",
    }]

    write_csv(
        out / "q1_sic1b_proxy_verdict.csv",
        verdict_rows,
        ["check", "observed", "expected", "passed", "details"],
    )
    write_csv(
        out / "q1_sic1b_proxy_candidates.csv",
        candidate_rows,
        [
            "category",
            "video",
            "frame_id",
            "Event_State_audit_only",
            "action_label",
            "selected",
            "active_event_memory",
            "risk_high",
            "guard_active",
            "detector_pressure",
            "recent_active_event",
            "detect_action",
            "proposal_absent",
            "detector_empty",
            "gt_signal_used_for_decision",
        ],
    )
    write_csv(
        out / "q1_sic1b_proxy_summary.csv",
        summary,
        [
            "snowfall_1150_selected",
            "quiet_tn_1160_1165_1170_selected",
            "active_event_memory_only_selected",
            "all_detect_acc_classified_unsafe",
            "gt_signal_used_for_decision",
            "would_touch_normal_frame",
            "port_watch_only_preserved",
            "split_branch_ok",
            "detect_acc_rows_checked",
            "detect_acc_rows_selected",
            "sic1a_classification_rows_read",
            "decision",
        ],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
