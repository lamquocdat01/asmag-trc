"""Verify Q1-SIC-1C1R copyMachine restore and port watch telemetry."""

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


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Q1-SIC-1C1R copy restore and port watch telemetry.")
    parser.add_argument("--sic1-root", required=True)
    parser.add_argument("--sic1c1-root", required=True)
    parser.add_argument("--sic1c1r-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    sic1_root = Path(args.sic1_root)
    c1_root = Path(args.sic1c1_root)
    r_root = Path(args.sic1c1r_root)
    out = Path(args.out)

    sic1_parking = load_video(sic1_root, PARKING)
    r_parking = load_video(r_root, PARKING)
    sic1_copy = by_frame(load_video(sic1_root, COPY))
    c1_copy = by_frame(load_video(c1_root, COPY))
    r_copy = by_frame(load_video(r_root, COPY))
    sic1_port = by_frame(load_video(sic1_root, PORT))
    c1_port = by_frame(load_video(c1_root, PORT))
    r_port = by_frame(load_video(r_root, PORT))
    r_snow = by_frame(load_video(r_root, SNOW))
    r_all = all_guarded_rows(r_root)

    sic1_parking_summary = video_summary(sic1_root, *PARKING)
    r_parking_summary = video_summary(r_root, *PARKING)
    sic1_parking_proposal = number(sic1_parking_summary.get("intervention_rate"), rate(sic1_parking, "ai_intervention_applied"))
    r_parking_proposal = number(r_parking_summary.get("intervention_rate"), rate(r_parking, "ai_intervention_applied"))
    r_parking_detector = number(r_parking_summary.get("detector_request_rate"), rate(r_parking, "ai_intervention_detector_requested"))
    sic1_parking_unprotected = sum(int(unprotected(row)) for row in sic1_parking)
    r_parking_unprotected = sum(int(unprotected(row)) for row in r_parking)
    parking_preserved_ok = int(
        r_parking_unprotected == sic1_parking_unprotected == 0
        and r_parking_detector == 0.0
        and r_parking_proposal <= sic1_parking_proposal + 0.0001
    )

    row_checks: List[Dict[str, object]] = []
    copy_restore_ok = 1
    copy_failures = 0
    for frame_id in COPY_FRAMES:
        sic1_row = sic1_copy.get(frame_id, {})
        c1_row = c1_copy.get(frame_id, {})
        r_row = r_copy.get(frame_id, {})
        ok = int(protected(sic1_row) and protected(r_row) and not unprotected(r_row))
        copy_restore_ok = int(copy_restore_ok and ok)
        copy_failures += int(not ok)
        row_checks.append({
            "check": "copyMachine_restore",
            "frame_id": frame_id,
            "sic1_label": sic1_row.get("q1_sic_arbitration_label", ""),
            "sic1_applied": sic1_row.get("ai_intervention_applied", ""),
            "sic1c1_label": c1_row.get("q1_sic_arbitration_label", ""),
            "sic1c1_applied": c1_row.get("ai_intervention_applied", ""),
            "sic1c1r_label": r_row.get("q1_sic_arbitration_label", ""),
            "sic1c1r_applied": r_row.get("ai_intervention_applied", ""),
            "sic1c1r_type": r_row.get("ai_intervention_type", ""),
            "sic1c1r_restore_active": r_row.get("q1_sic1c1r_restore_copymachine_active", ""),
            "passed": ok,
        })

    port_watch_restore_ok = 1
    no_port_retighten_enforcement_ok = 1
    for frame_id in PORT_FRAMES:
        sic1_row = sic1_port.get(frame_id, {})
        c1_row = c1_port.get(frame_id, {})
        r_row = r_port.get(frame_id, {})
        watch_ok = int(
            r_row.get("q1_sic_arbitration_label") == "WATCH_ONLY_PORT_RETIGHTEN"
            and truthy(r_row.get("q1_sic_watch_only"))
            and r_row.get("q1_sic_owner") == "detector_retighten"
            and r_row.get("q1_sic_reference_step") == "Step4E4"
        )
        detector_unchanged = int(
            number(r_row.get("q1_sic_pre_detector_request")) == number(r_row.get("q1_sic_post_detector_request"))
            and number(r_row.get("ai_intervention_detector_requested")) == 0
        )
        port_watch_restore_ok = int(port_watch_restore_ok and watch_ok)
        no_port_retighten_enforcement_ok = int(no_port_retighten_enforcement_ok and detector_unchanged)
        row_checks.append({
            "check": "port_watch",
            "frame_id": frame_id,
            "sic1_label": sic1_row.get("q1_sic_arbitration_label", ""),
            "sic1c1_label": c1_row.get("q1_sic_arbitration_label", ""),
            "sic1c1r_label": r_row.get("q1_sic_arbitration_label", ""),
            "sic1c1r_watch": r_row.get("q1_sic_watch_only", ""),
            "sic1c1r_owner": r_row.get("q1_sic_owner", ""),
            "sic1c1r_reference": r_row.get("q1_sic_reference_step", ""),
            "sic1c1r_restore_active": r_row.get("q1_sic1c1r_restore_port_watch_active", ""),
            "detector_unchanged": detector_unchanged,
            "passed": int(watch_ok and detector_unchanged),
        })

    snow1150 = r_snow.get(1150, {})
    snowfall_probe_persist_ok = int(
        bool(snow1150)
        and truthy(snow1150.get("q1_sic_detector_action_probe_active"))
        and truthy(snow1150.get("q1_sic_detector_action_probe_would_select_shadow"))
        and not truthy(snow1150.get("q1_sic_detector_action_probe_gt_signal_used"))
        and not truthy(snow1150.get("q1_sic_detector_action_probe_would_touch_normal_frame"))
    )
    row_checks.append({
        "check": "snowfall_1150_probe",
        "frame_id": 1150,
        "sic1c1r_label": snow1150.get("q1_sic_arbitration_label", ""),
        "probe_active": snow1150.get("q1_sic_detector_action_probe_active", ""),
        "probe_would_select_shadow": snow1150.get("q1_sic_detector_action_probe_would_select_shadow", ""),
        "probe_gt_signal_used": snow1150.get("q1_sic_detector_action_probe_gt_signal_used", ""),
        "probe_would_touch_normal": snow1150.get("q1_sic_detector_action_probe_would_touch_normal_frame", ""),
        "passed": snowfall_probe_persist_ok,
    })

    normal_frame_interventions = count_normal_interventions(r_root)
    q1_touch_max = max_col(r_all, "q1_sic_would_touch_normal_frame")
    probe_touch_max = max_col(r_all, "q1_sic_detector_action_probe_would_touch_normal_frame")
    gt_decision_max = max_col(r_all, "q1_sic_gt_signal_used_for_decision")
    restore_copy_gt_max = max_col(r_all, "q1_sic1c1r_restore_copymachine_gt_signal_used")
    normal_safety_ok = int(
        normal_frame_interventions == 0
        and q1_touch_max == 0
        and probe_touch_max == 0
        and gt_decision_max == 0
        and restore_copy_gt_max == 0
    )

    q1_sic1b_proxy_sum = sum(int(truthy(row.get("q1_sic_event_risk_empty_detect_proxy"))) for row in r_all)
    q1_sic1b_label_count = sum(
        int(row.get("q1_sic_arbitration_label") == "FORCE_EVENT_RISK_EMPTY_DETECT_PROTECTION")
        for row in r_all
    )
    no_snowfall_enforcement_ok = int(q1_sic1b_proxy_sum == 0 and q1_sic1b_label_count == 0)

    sic1_copy_summary = video_summary(sic1_root, *COPY)
    r_copy_summary = video_summary(r_root, *COPY)
    sic1_copy_proposal = number(sic1_copy_summary.get("intervention_rate"), 0.0)
    r_copy_proposal = number(r_copy_summary.get("intervention_rate"), 0.0)
    sic1_copy_event_fn = number(sic1_copy_summary.get("event_fn_count"), number(sic1_copy_summary.get("FN_event_count"), 0.0))
    r_copy_event_fn = number(r_copy_summary.get("event_fn_count"), number(r_copy_summary.get("FN_event_count"), 0.0))

    all_pass = int(all([
        parking_preserved_ok,
        copy_restore_ok,
        port_watch_restore_ok,
        snowfall_probe_persist_ok,
        normal_safety_ok,
        no_snowfall_enforcement_ok,
        no_port_retighten_enforcement_ok,
    ]))
    decision = "PASS_RESTORE_BASE_WITH_KNOWN_SNOWFALL_BLOCKER" if all_pass else "FAIL_RESTORE_COPY_PORT"

    summary = [{
        "parking_preserved_ok": parking_preserved_ok,
        "sic1_parking_unprotected_fn": sic1_parking_unprotected,
        "sic1c1r_parking_unprotected_fn": r_parking_unprotected,
        "sic1_parking_proposal": f"{sic1_parking_proposal:.5f}",
        "sic1c1r_parking_proposal": f"{r_parking_proposal:.5f}",
        "sic1c1r_parking_detector": f"{r_parking_detector:.5f}",
        "copyMachine_restore_ok": copy_restore_ok,
        "copyMachine_restore_failures": copy_failures,
        "sic1_copyMachine_proposal": f"{sic1_copy_proposal:.5f}",
        "sic1c1r_copyMachine_proposal": f"{r_copy_proposal:.5f}",
        "sic1_copyMachine_event_fn": f"{sic1_copy_event_fn:.0f}",
        "sic1c1r_copyMachine_event_fn": f"{r_copy_event_fn:.0f}",
        "port_watch_restore_ok": port_watch_restore_ok,
        "snowfall_probe_persist_ok": snowfall_probe_persist_ok,
        "normal_safety_ok": normal_safety_ok,
        "normal_frame_interventions": normal_frame_interventions,
        "q1_sic_would_touch_normal_frame_max": q1_touch_max,
        "probe_would_touch_normal_frame_max": probe_touch_max,
        "q1_sic_gt_signal_used_for_decision_max": gt_decision_max,
        "restore_copymachine_gt_signal_used_max": restore_copy_gt_max,
        "no_snowfall_enforcement_ok": no_snowfall_enforcement_ok,
        "q1_sic1b_proxy_active_rows": q1_sic1b_proxy_sum,
        "q1_sic1b_enforcement_label_rows": q1_sic1b_label_count,
        "no_port_retighten_enforcement_ok": no_port_retighten_enforcement_ok,
        "decision": decision,
    }]

    write_csv(out / "q1_sic1c1r_restore_copy_port_summary.csv", summary, list(summary[0].keys()))
    fields = sorted({key for row in row_checks for key in row.keys()})
    write_csv(out / "q1_sic1c1r_restore_copy_port_row_checks.csv", row_checks, fields)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
