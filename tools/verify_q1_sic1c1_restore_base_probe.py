"""Verify Q1-SIC-1C1 restored base behavior and detector-action probe telemetry."""

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
PORT_FRAMES = [1350, 1355]


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Q1-SIC-1C1 restored base and probe telemetry.")
    parser.add_argument("--sic1-root", required=True)
    parser.add_argument("--sic1c1-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    sic1_root = Path(args.sic1_root)
    c1_root = Path(args.sic1c1_root)
    out = Path(args.out)

    sic1_parking = load_video(sic1_root, PARKING)
    c1_parking = load_video(c1_root, PARKING)
    sic1_copy = load_video(sic1_root, COPY)
    c1_copy = load_video(c1_root, COPY)
    sic1_port = by_frame(load_video(sic1_root, PORT))
    c1_port = by_frame(load_video(c1_root, PORT))
    c1_snow = by_frame(load_video(c1_root, SNOW))
    c1_all = all_guarded_rows(c1_root)

    sic1_parking_summary = video_summary(sic1_root, *PARKING)
    c1_parking_summary = video_summary(c1_root, *PARKING)
    c1_all_summaries = read_csv(c1_root / "ai_intervention_video_summary.csv")

    sic1_parking_unprotected = sum(int(unprotected(row)) for row in sic1_parking)
    c1_parking_unprotected = sum(int(unprotected(row)) for row in c1_parking)
    sic1_parking_proposal = number(sic1_parking_summary.get("intervention_rate"), rate(sic1_parking, "ai_intervention_applied"))
    c1_parking_proposal = number(c1_parking_summary.get("intervention_rate"), rate(c1_parking, "ai_intervention_applied"))
    c1_parking_detector = number(c1_parking_summary.get("detector_request_rate"), rate(c1_parking, "ai_intervention_detector_requested"))
    parking_restore_ok = int(
        c1_parking_unprotected == sic1_parking_unprotected == 0
        and c1_parking_detector == 0.0
        and c1_parking_proposal <= sic1_parking_proposal + 0.0001
    )

    port_rows = []
    port_watch_restore_ok = 1
    for frame_id in PORT_FRAMES:
        row = c1_port.get(frame_id, {})
        ok = int(
            row.get("q1_sic_arbitration_label") == "WATCH_ONLY_PORT_RETIGHTEN"
            and truthy(row.get("q1_sic_watch_only"))
            and row.get("q1_sic_owner") == "detector_retighten"
        )
        port_watch_restore_ok = int(bool(port_watch_restore_ok and ok))
        port_rows.append({
            "check": "port_watch",
            "frame_id": frame_id,
            "sic1_label": sic1_port.get(frame_id, {}).get("q1_sic_arbitration_label", ""),
            "sic1_watch": sic1_port.get(frame_id, {}).get("q1_sic_watch_only", ""),
            "sic1c1_label": row.get("q1_sic_arbitration_label", ""),
            "sic1c1_watch": row.get("q1_sic_watch_only", ""),
            "sic1c1_owner": row.get("q1_sic_owner", ""),
            "passed": ok,
        })

    copy_by_frame = by_frame(c1_copy)
    copy_failures = []
    for row in sic1_copy:
        frame_id = frame(row)
        c1_row = copy_by_frame.get(frame_id, {})
        if protected(row) and unprotected(c1_row):
            copy_failures.append(frame_id)
    copy_machine_restore_ok = int(len(copy_failures) == 0)

    snow1150 = c1_snow.get(1150, {})
    probe_reject_present = str(snow1150.get("q1_sic_detector_action_probe_reject_reason", "")).strip() != ""
    probe_active = truthy(snow1150.get("q1_sic_detector_action_probe_active"))
    snowfall_probe_persist_ok = int(
        bool(snow1150)
        and (probe_active or probe_reject_present)
        and not truthy(snow1150.get("q1_sic_detector_action_probe_gt_signal_used"))
    )

    normal_frame_interventions = sum(int(number(row.get("normal_frame_intervention_count")) > 0) for row in c1_all_summaries)
    normal_safety_ok = int(
        max([number(row.get("q1_sic_would_touch_normal_frame")) for row in c1_all] or [0]) == 0
        and max([number(row.get("q1_sic_detector_action_probe_would_touch_normal_frame")) for row in c1_all] or [0]) == 0
        and normal_frame_interventions == 0
    )

    q1_sic1b_proxy_sum = sum(int(truthy(row.get("q1_sic_event_risk_empty_detect_proxy"))) for row in c1_all)
    q1_sic1b_label_count = sum(
        int(row.get("q1_sic_arbitration_label") == "FORCE_EVENT_RISK_EMPTY_DETECT_PROTECTION")
        for row in c1_all
    )
    no_q1_sic1b_enforcement_ok = int(q1_sic1b_proxy_sum == 0 and q1_sic1b_label_count == 0)

    row_checks = []
    row_checks.extend(port_rows)
    row_checks.append({
        "check": "snowfall_1150_probe",
        "frame_id": 1150,
        "sic1c1_label": snow1150.get("q1_sic_arbitration_label", ""),
        "probe_active": snow1150.get("q1_sic_detector_action_probe_active", ""),
        "probe_would_select_shadow": snow1150.get("q1_sic_detector_action_probe_would_select_shadow", ""),
        "probe_gt_signal_used": snow1150.get("q1_sic_detector_action_probe_gt_signal_used", ""),
        "probe_reject_reason": snow1150.get("q1_sic_detector_action_probe_reject_reason", ""),
        "passed": snowfall_probe_persist_ok,
    })
    for frame_id in copy_failures[:20]:
        row_checks.append({
            "check": "copyMachine_restore",
            "frame_id": frame_id,
            "sic1c1_label": copy_by_frame.get(frame_id, {}).get("q1_sic_arbitration_label", ""),
            "passed": 0,
        })

    all_pass = int(all([
        parking_restore_ok,
        port_watch_restore_ok,
        copy_machine_restore_ok,
        snowfall_probe_persist_ok,
        normal_safety_ok,
        no_q1_sic1b_enforcement_ok,
    ]))
    summary = [{
        "parking_restore_ok": parking_restore_ok,
        "sic1_parking_unprotected_fn": sic1_parking_unprotected,
        "sic1c1_parking_unprotected_fn": c1_parking_unprotected,
        "sic1_parking_proposal": f"{sic1_parking_proposal:.5f}",
        "sic1c1_parking_proposal": f"{c1_parking_proposal:.5f}",
        "sic1c1_parking_detector": f"{c1_parking_detector:.5f}",
        "port_watch_restore_ok": port_watch_restore_ok,
        "copyMachine_restore_ok": copy_machine_restore_ok,
        "copyMachine_restore_failures": len(copy_failures),
        "snowfall_probe_persist_ok": snowfall_probe_persist_ok,
        "snowfall_1150_probe_active": int(probe_active),
        "snowfall_1150_probe_would_select_shadow": int(truthy(snow1150.get("q1_sic_detector_action_probe_would_select_shadow"))),
        "snowfall_1150_probe_gt_signal_used": int(truthy(snow1150.get("q1_sic_detector_action_probe_gt_signal_used"))),
        "normal_safety_ok": normal_safety_ok,
        "normal_frame_interventions": normal_frame_interventions,
        "q1_sic_would_touch_normal_frame_max": max([number(row.get("q1_sic_would_touch_normal_frame")) for row in c1_all] or [0]),
        "probe_would_touch_normal_frame_max": max([number(row.get("q1_sic_detector_action_probe_would_touch_normal_frame")) for row in c1_all] or [0]),
        "no_q1_sic1b_enforcement_ok": no_q1_sic1b_enforcement_ok,
        "q1_sic1b_proxy_active_rows": q1_sic1b_proxy_sum,
        "q1_sic1b_enforcement_label_rows": q1_sic1b_label_count,
        "decision": "PASS_RESTORE_BASE_WITH_KNOWN_SNOWFALL_BLOCKER" if all_pass else "FAIL_RESTORE_BASE_OR_PROBE",
    }]

    write_csv(
        out / "q1_sic1c1_restore_base_probe_summary.csv",
        summary,
        list(summary[0].keys()),
    )
    fields = [
        "check",
        "frame_id",
        "sic1_label",
        "sic1_watch",
        "sic1c1_label",
        "sic1c1_watch",
        "sic1c1_owner",
        "probe_active",
        "probe_would_select_shadow",
        "probe_gt_signal_used",
        "probe_reject_reason",
        "passed",
    ]
    write_csv(out / "q1_sic1c1_restore_base_probe_row_checks.csv", row_checks, fields)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
