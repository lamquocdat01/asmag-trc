"""Verify Q1-SIC-1C1R2 stable detector-action probe snapshot."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


PIPELINE = "ASMAG_TR_CONTROLLER_ONLINE_GUARDED"
PARKING = ("intermittentObjectMotion", "parking")
COPY = ("shadow", "copyMachine")
PORT = ("lowFramerate", "port_0_17fps")
SNOW = ("badWeather", "snowFall")
COPY_FRAMES = [810, 815, 820, 935, 940, 945]
PORT_FRAMES = [1350, 1355]
SNOW_CONTEXT_FRAMES = [1120, 1125, 1130, 1135, 1140, 1145, 1150, 1155, 1160, 1165, 1170]
SNOW_GUARD_FRAMES = [1160, 1165, 1170]


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
    for key in ("frame_id", "frame", "raw_frame_id", "frame_idx"):
        if row.get(key) not in (None, ""):
            return int(float(row[key]))
    return -1


def guarded_path(root: Path, video: Sequence[str]) -> Path:
    return root / "raw_results" / video[0] / video[1] / PIPELINE / "frame_metrics.csv"


def load_video(root: Path, video: Sequence[str]) -> List[Dict[str, str]]:
    return read_csv(guarded_path(root, video))


def by_frame(rows: Iterable[Dict[str, str]]) -> Dict[int, Dict[str, str]]:
    return {frame(row): row for row in rows}


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


def rate(rows: List[Dict[str, str]], column: str) -> float:
    if not rows:
        return 0.0
    return sum(int(truthy(row.get(column))) for row in rows) / float(len(rows))


def video_summary(root: Path, category: str, video: str) -> Dict[str, str]:
    for row in read_csv(root / "ai_intervention_video_summary.csv"):
        if row.get("category") == category and row.get("video") == video:
            return row
    return {}


def all_guarded_rows(root: Path) -> List[Dict[str, str]]:
    return [
        row
        for path in root.glob(f"raw_results/*/*/{PIPELINE}/frame_metrics.csv")
        for row in read_csv(path)
    ]


def max_col(rows: List[Dict[str, str]], column: str) -> float:
    return max([number(row.get(column)) for row in rows] or [0.0])


def count_normal_interventions(root: Path) -> int:
    return sum(
        int(number(row.get("normal_frame_intervention_count")) > 0)
        for row in read_csv(root / "ai_intervention_video_summary.csv")
    )


def detector_request(row: Dict[str, str]) -> float:
    return number(row.get("ai_intervention_detector_requested"), number(row.get("yolo_called"), 0.0))


def intervention_applied(row: Dict[str, str]) -> float:
    return number(row.get("ai_intervention_applied"), number(row.get("proposal"), 0.0))


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Q1-SIC-1C1R2 stable probe snapshot.")
    parser.add_argument("--sic1c1r-root", required=True)
    parser.add_argument("--sic1c1r2-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    r_root = Path(args.sic1c1r_root)
    r2_root = Path(args.sic1c1r2_root)
    out = Path(args.out)

    r_parking = load_video(r_root, PARKING)
    r2_parking = load_video(r2_root, PARKING)
    r_copy = by_frame(load_video(r_root, COPY))
    r2_copy = by_frame(load_video(r2_root, COPY))
    r_port = by_frame(load_video(r_root, PORT))
    r2_port = by_frame(load_video(r2_root, PORT))
    r_snow = by_frame(load_video(r_root, SNOW))
    r2_snow = by_frame(load_video(r2_root, SNOW))
    r2_all = all_guarded_rows(r2_root)

    row_checks: List[Dict[str, object]] = []

    snow1150 = r2_snow.get(1150, {})
    current_pressure_restored = int(
        truthy(snow1150.get("q1_sic_detector_action_probe_event_risk_pressure"))
        and truthy(snow1150.get("q1_sic_detector_action_probe_detector_pressure"))
    )
    memory_or_current_pressure = int(
        truthy(snow1150.get("q1_sic_detector_action_probe_pressure_memory_active"))
        or current_pressure_restored
    )
    snowfall_probe_restored_ok = int(
        bool(snow1150)
        and truthy(snow1150.get("q1_sic_detector_action_probe_active"))
        and truthy(snow1150.get("q1_sic_detector_action_probe_snapshot_active"))
        and memory_or_current_pressure
        and truthy(snow1150.get("q1_sic_detector_action_probe_would_select_shadow"))
        and not truthy(snow1150.get("q1_sic_detector_action_probe_gt_signal_used"))
        and not truthy(snow1150.get("q1_sic_detector_action_probe_would_touch_normal_frame"))
    )
    row_checks.append({
        "check": "snowfall_1150_probe_restored",
        "frame_id": 1150,
        "c1r_label": r_snow.get(1150, {}).get("q1_sic_arbitration_label", ""),
        "c1r_would_select_shadow": r_snow.get(1150, {}).get("q1_sic_detector_action_probe_would_select_shadow", ""),
        "c1r2_label": snow1150.get("q1_sic_arbitration_label", ""),
        "probe_active": snow1150.get("q1_sic_detector_action_probe_active", ""),
        "snapshot_active": snow1150.get("q1_sic_detector_action_probe_snapshot_active", ""),
        "snapshot_source": snow1150.get("q1_sic_detector_action_probe_snapshot_source", ""),
        "event_risk_pressure": snow1150.get("q1_sic_detector_action_probe_event_risk_pressure", ""),
        "detector_pressure": snow1150.get("q1_sic_detector_action_probe_detector_pressure", ""),
        "pressure_memory_active": snow1150.get("q1_sic_detector_action_probe_pressure_memory_active", ""),
        "pressure_memory_age": snow1150.get("q1_sic_detector_action_probe_pressure_memory_age", ""),
        "pressure_memory_reason": snow1150.get("q1_sic_detector_action_probe_pressure_memory_reason", ""),
        "would_select_shadow": snow1150.get("q1_sic_detector_action_probe_would_select_shadow", ""),
        "gt_signal_used": snow1150.get("q1_sic_detector_action_probe_gt_signal_used", ""),
        "would_touch_normal": snow1150.get("q1_sic_detector_action_probe_would_touch_normal_frame", ""),
        "passed": snowfall_probe_restored_ok,
    })

    snowfall_context_guard_ok = 1
    for frame_id in SNOW_CONTEXT_FRAMES:
        r_row = r_snow.get(frame_id, {})
        r2_row = r2_snow.get(frame_id, {})
        guard_frame = frame_id in SNOW_GUARD_FRAMES
        guard_ok = int(
            not guard_frame
            or (
                not truthy(r2_row.get("q1_sic_detector_action_probe_would_select_shadow"))
                and not truthy(r2_row.get("q1_sic_detector_action_probe_would_touch_normal_frame"))
                and intervention_applied(r2_row) == intervention_applied(r_row)
                and detector_request(r2_row) == detector_request(r_row)
            )
        )
        snowfall_context_guard_ok = int(snowfall_context_guard_ok and guard_ok)
        row_checks.append({
            "check": "snowfall_context",
            "frame_id": frame_id,
            "c1r_action": r_row.get("action_label", ""),
            "c1r2_action": r2_row.get("action_label", ""),
            "c1r_probe_would_select": r_row.get("q1_sic_detector_action_probe_would_select_shadow", ""),
            "c1r2_probe_would_select": r2_row.get("q1_sic_detector_action_probe_would_select_shadow", ""),
            "c1r2_snapshot_source": r2_row.get("q1_sic_detector_action_probe_snapshot_source", ""),
            "c1r2_memory_active": r2_row.get("q1_sic_detector_action_probe_pressure_memory_active", ""),
            "c1r2_would_touch_normal": r2_row.get("q1_sic_detector_action_probe_would_touch_normal_frame", ""),
            "c1r_intervention": intervention_applied(r_row),
            "c1r2_intervention": intervention_applied(r2_row),
            "c1r_detector": detector_request(r_row),
            "c1r2_detector": detector_request(r2_row),
            "passed": guard_ok,
        })

    r_parking_summary = video_summary(r_root, *PARKING)
    r2_parking_summary = video_summary(r2_root, *PARKING)
    r_parking_proposal = number(r_parking_summary.get("intervention_rate"), rate(r_parking, "ai_intervention_applied"))
    r2_parking_proposal = number(r2_parking_summary.get("intervention_rate"), rate(r2_parking, "ai_intervention_applied"))
    r2_parking_detector = number(r2_parking_summary.get("detector_request_rate"), rate(r2_parking, "ai_intervention_detector_requested"))
    r2_parking_unprotected = sum(int(unprotected(row)) for row in r2_parking)
    parking_preserved_ok = int(
        r2_parking_unprotected == 0
        and r2_parking_detector == 0.0
        and r2_parking_proposal <= r_parking_proposal + 0.0001
    )

    copyMachine_preserved_ok = 1
    for frame_id in COPY_FRAMES:
        r_row = r_copy.get(frame_id, {})
        r2_row = r2_copy.get(frame_id, {})
        ok = int(protected(r_row) and protected(r2_row) and not unprotected(r2_row))
        copyMachine_preserved_ok = int(copyMachine_preserved_ok and ok)
        row_checks.append({
            "check": "copyMachine_preserved",
            "frame_id": frame_id,
            "c1r_label": r_row.get("q1_sic_arbitration_label", ""),
            "c1r2_label": r2_row.get("q1_sic_arbitration_label", ""),
            "c1r_restore_active": r_row.get("q1_sic1c1r_restore_copymachine_active", ""),
            "c1r2_restore_active": r2_row.get("q1_sic1c1r_restore_copymachine_active", ""),
            "c1r2_intervention": intervention_applied(r2_row),
            "passed": ok,
        })

    port_watch_preserved_ok = 1
    no_port_retighten_enforcement_ok = 1
    for frame_id in PORT_FRAMES:
        r_row = r_port.get(frame_id, {})
        r2_row = r2_port.get(frame_id, {})
        watch_ok = int(
            r2_row.get("q1_sic_arbitration_label") == "WATCH_ONLY_PORT_RETIGHTEN"
            and truthy(r2_row.get("q1_sic_watch_only"))
            and r2_row.get("q1_sic_owner") == "detector_retighten"
            and r2_row.get("q1_sic_reference_step") == "Step4E4"
        )
        detector_unchanged = int(
            detector_request(r2_row) == detector_request(r_row)
            and intervention_applied(r2_row) == intervention_applied(r_row)
        )
        port_watch_preserved_ok = int(port_watch_preserved_ok and watch_ok)
        no_port_retighten_enforcement_ok = int(no_port_retighten_enforcement_ok and detector_unchanged)
        row_checks.append({
            "check": "port_watch_preserved",
            "frame_id": frame_id,
            "c1r_label": r_row.get("q1_sic_arbitration_label", ""),
            "c1r2_label": r2_row.get("q1_sic_arbitration_label", ""),
            "c1r2_watch": r2_row.get("q1_sic_watch_only", ""),
            "c1r2_owner": r2_row.get("q1_sic_owner", ""),
            "c1r2_reference": r2_row.get("q1_sic_reference_step", ""),
            "detector_unchanged": detector_unchanged,
            "passed": int(watch_ok and detector_unchanged),
        })

    normal_frame_interventions = count_normal_interventions(r2_root)
    q1_touch_max = max_col(r2_all, "q1_sic_would_touch_normal_frame")
    probe_touch_max = max_col(r2_all, "q1_sic_detector_action_probe_would_touch_normal_frame")
    gt_decision_max = max_col(r2_all, "q1_sic_gt_signal_used_for_decision")
    probe_gt_max = max_col(r2_all, "q1_sic_detector_action_probe_gt_signal_used")
    normal_safety_ok = int(
        normal_frame_interventions == 0
        and q1_touch_max == 0
        and probe_touch_max == 0
        and gt_decision_max == 0
        and probe_gt_max == 0
    )

    q1_sic1b_proxy_sum = sum(int(truthy(row.get("q1_sic_event_risk_empty_detect_proxy"))) for row in r2_all)
    q1_sic1b_label_count = sum(
        int(row.get("q1_sic_arbitration_label") == "FORCE_EVENT_RISK_EMPTY_DETECT_PROTECTION")
        for row in r2_all
    )
    snowfall_enforcement_label_rows = sum(
        int(
            (row.get("category"), row.get("video")) == SNOW
            and str(row.get("q1_sic_arbitration_label", "")).startswith("FORCE_")
            and truthy(row.get("ai_intervention_applied"))
        )
        for row in r2_all
    )
    no_snowfall_enforcement_ok = int(q1_sic1b_proxy_sum == 0 and q1_sic1b_label_count == 0)
    probe_enforcement_change_rows = sum(
        int(
            truthy(row.get("q1_sic_detector_action_probe_would_select_shadow"))
            and (
                row.get("q1_sic_arbitration_label") == "FORCE_EVENT_RISK_EMPTY_DETECT_PROTECTION"
                or truthy(row.get("q1_sic_event_risk_empty_detect_proxy"))
            )
        )
        for row in r2_all
    )
    no_enforcement_ok = int(
        no_snowfall_enforcement_ok
        and no_port_retighten_enforcement_ok
        and probe_enforcement_change_rows == 0
        and snowfall_enforcement_label_rows == 0
    )

    all_pass = int(all([
        snowfall_probe_restored_ok,
        snowfall_context_guard_ok,
        parking_preserved_ok,
        copyMachine_preserved_ok,
        port_watch_preserved_ok,
        normal_safety_ok,
        no_enforcement_ok,
    ]))
    if all_pass:
        decision = "PASS_STABLE_PROBE_WITH_KNOWN_SNOWFALL_BLOCKER"
    elif not snowfall_probe_restored_ok:
        decision = "FAIL_PROBE_SNAPSHOT"
    elif not snowfall_context_guard_ok:
        decision = "FAIL_PRESSURE_MEMORY_TOO_BROAD"
    elif not normal_safety_ok:
        decision = "FAIL_NORMAL_SAFETY"
    elif not parking_preserved_ok:
        decision = "FAIL_PARKING_REGRESSION"
    elif not copyMachine_preserved_ok:
        decision = "FAIL_COPYMACHINE_REGRESSION"
    elif not port_watch_preserved_ok:
        decision = "FAIL_PORT_WATCH_REGRESSION"
    else:
        decision = "FAIL_PROBE_SNAPSHOT"

    summary = [{
        "snowfall_probe_restored_ok": snowfall_probe_restored_ok,
        "snowfall_1150_probe_active": snow1150.get("q1_sic_detector_action_probe_active", ""),
        "snowfall_1150_snapshot_active": snow1150.get("q1_sic_detector_action_probe_snapshot_active", ""),
        "snowfall_1150_pressure_memory_active": snow1150.get("q1_sic_detector_action_probe_pressure_memory_active", ""),
        "snowfall_1150_current_pressure_restored": current_pressure_restored,
        "snowfall_1150_would_select_shadow": snow1150.get("q1_sic_detector_action_probe_would_select_shadow", ""),
        "snowfall_1150_gt_signal_used": snow1150.get("q1_sic_detector_action_probe_gt_signal_used", ""),
        "snowfall_1150_would_touch_normal": snow1150.get("q1_sic_detector_action_probe_would_touch_normal_frame", ""),
        "snowfall_context_guard_ok": snowfall_context_guard_ok,
        "parking_preserved_ok": parking_preserved_ok,
        "sic1c1r_parking_proposal": f"{r_parking_proposal:.5f}",
        "sic1c1r2_parking_proposal": f"{r2_parking_proposal:.5f}",
        "sic1c1r2_parking_detector": f"{r2_parking_detector:.5f}",
        "sic1c1r2_parking_unprotected_fn": r2_parking_unprotected,
        "copyMachine_preserved_ok": copyMachine_preserved_ok,
        "port_watch_preserved_ok": port_watch_preserved_ok,
        "normal_safety_ok": normal_safety_ok,
        "normal_frame_interventions": normal_frame_interventions,
        "q1_sic_would_touch_normal_frame_max": q1_touch_max,
        "probe_would_touch_normal_frame_max": probe_touch_max,
        "q1_sic_gt_signal_used_for_decision_max": gt_decision_max,
        "q1_sic_detector_action_probe_gt_signal_used_max": probe_gt_max,
        "no_enforcement_ok": no_enforcement_ok,
        "q1_sic1b_proxy_active_rows": q1_sic1b_proxy_sum,
        "q1_sic1b_enforcement_label_rows": q1_sic1b_label_count,
        "snowfall_enforcement_label_rows": snowfall_enforcement_label_rows,
        "probe_enforcement_change_rows": probe_enforcement_change_rows,
        "no_port_retighten_enforcement_ok": no_port_retighten_enforcement_ok,
        "decision": decision,
    }]

    write_csv(out / "q1_sic1c1r2_stable_probe_snapshot_summary.csv", summary, list(summary[0].keys()))
    fields = sorted({key for row in row_checks for key in row.keys()})
    write_csv(out / "q1_sic1c1r2_stable_probe_snapshot_row_checks.csv", row_checks, fields)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
