import argparse
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.errors import PerformanceWarning


OUTPUT_ROOT = Path("outputs/phase8a_policy_dataset")
GUARDED = "ASMAG_TR_CONTROLLER_ONLINE_GUARDED"
TEACHER_PIPELINES = {
    "P3_MOG2",
    "ASMAG_TR_CONTROLLER",
    "ONLINE_CALIBRATED",
    "ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED",
    GUARDED,
}
ACTION_BUCKETS = [
    "DETECT_ACC",
    "FALLBACK_P3_GUARD",
    "LIGHTWEIGHT_MASK_ACC",
    "LIGHTWEIGHT_MASK_P3_FALLBACK",
    "REUSE_ACC",
    "CLOSED_EMPTY",
    "LEGACY_SAFE_P3_GUARD",
    "OTHER",
]
SOURCE_ROOTS = [
    {
        "run_name": "online_guarded_smoke",
        "dataset": "smoke",
        "root": Path("outputs/asmag_tr_controller_online_guarded_cdnet_smoke"),
    },
    {
        "run_name": "online_guarded_targeted",
        "dataset": "targeted",
        "root": Path("outputs/asmag_tr_controller_online_guarded_cdnet_targeted"),
    },
    {
        "run_name": "full_cdnet2014_official_edge_profile_pc",
        "dataset": "full_cdnet2014",
        "root": Path("outputs/full_cdnet2014_official_edge_profile_pc"),
    },
]
PHASE7C_ROOT = Path("outputs/asmag_tr_controller_online_guarded_ablation_phase7c")
NUMERIC_HINTS = (
    "latency",
    "frames_since",
    "frame",
    "count",
    "rate",
    "risk",
    "quality",
    "score",
    "trust",
    "ratio",
    "iou",
    "dx",
    "dy",
    "shift",
    "scale",
    "rotation",
    "response",
    "density",
    "area",
    "precision",
    "recall",
    "fmeasure",
    "proxy",
)
FEATURE_PREFIXES = (
    "gmq_",
    "motion_comp_",
    "geometry_",
    "continuous_pan_",
    "position_switch_",
    "ptz_",
    "candidate_",
    "rolling_",
    "teacher_",
)
FEATURE_KEYWORDS = (
    "frames_since",
    "reuse_",
    "closed_empty",
    "event_",
    "active_event",
    "global_motion",
    "camera_jump",
    "zoom_scale",
    "low_framerate",
    "detector_floor",
    "cadence",
    "safety",
    "guard",
    "veto",
    "blocked",
    "invalidated",
    "sanitizer",
)


warnings.simplefilter("ignore", PerformanceWarning)


def boolish(series):
    return pd.to_numeric(series, errors="coerce").fillna(0.0).astype(float)


def read_csv_safe(path, **kwargs):
    try:
        return pd.read_csv(path, **kwargs)
    except Exception as exc:
        print(f"[WARN] skipped unreadable CSV {path}: {exc}")
        return pd.DataFrame()


def normalize_pipeline_columns(df):
    if df.empty:
        return df
    df = df.copy()
    if "Pipeline" in df.columns and "pipeline" not in df.columns:
        df = df.rename(columns={"Pipeline": "pipeline"})
    if "CDnet_FMeasure" in df.columns and "FMeasure" not in df.columns:
        df = df.rename(columns={"CDnet_FMeasure": "FMeasure"})
    if "Avg_FPS" in df.columns and "avg_FPS" not in df.columns:
        df["avg_FPS"] = df["Avg_FPS"]
    return df


def source_specs():
    specs = [s for s in SOURCE_ROOTS if s["root"].exists()]
    if PHASE7C_ROOT.exists():
        for policy_dir in sorted([p for p in PHASE7C_ROOT.iterdir() if p.is_dir()]):
            specs.append(
                {
                    "run_name": policy_dir.name,
                    "dataset": "phase7c_ablation",
                    "root": policy_dir,
                }
            )
    return specs


def parse_frame_path(spec, path):
    raw = spec["root"] / "raw_results"
    rel = path.relative_to(raw)
    parts = rel.parts
    if len(parts) < 4:
        return None
    return {
        "run_name": spec["run_name"],
        "dataset": spec["dataset"],
        "category": parts[0],
        "video": parts[1],
        "pipeline": parts[2],
        "frame_path": path,
        "source_folder": str(path.parent),
    }


def per_video_summary_path(root):
    for name in ["per_video_summary.csv", "summary_by_video.csv", "representative_per_video_summary.csv"]:
        path = root / name
        if path.exists():
            return path
    return None


def load_per_video(specs):
    frames = []
    for spec in specs:
        path = per_video_summary_path(spec["root"])
        if not path:
            continue
        df = normalize_pipeline_columns(read_csv_safe(path))
        if df.empty:
            continue
        for col, value in [("run_name", spec["run_name"]), ("dataset", spec["dataset"])]:
            df[col] = value
        df["source_summary"] = str(path)
        frames.append(df)
    return pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()


def discover_frame_files(specs):
    rows = []
    for spec in specs:
        raw = spec["root"] / "raw_results"
        if not raw.exists():
            continue
        for path in raw.rglob("frame_metrics.csv"):
            parsed = parse_frame_path(spec, path)
            if parsed:
                rows.append(parsed)
    return rows


def action_bucket(label):
    text = "" if pd.isna(label) else str(label).upper()
    if "DETECT_ACC" in text or text == "DETECTOR":
        return "DETECT_ACC"
    if "FALLBACK_P3_GUARD" in text or "FALLBACK_P3_POLICY" in text:
        return "FALLBACK_P3_GUARD"
    if "LIGHTWEIGHT_MASK_ACC" in text:
        return "LIGHTWEIGHT_MASK_ACC"
    if "LIGHTWEIGHT_MASK_P3_FALLBACK" in text or "REUSE_P3_FALLBACK" in text or "CLOSED_EMPTY_P3_FALLBACK" in text:
        return "LIGHTWEIGHT_MASK_P3_FALLBACK"
    if "REUSE_ACC" in text:
        return "REUSE_ACC"
    if text.startswith("CLOSED_EMPTY") or "CLOSED_EMPTY" in text:
        return "CLOSED_EMPTY"
    if "LEGACY_SAFE_P3_GUARD" in text:
        return "LEGACY_SAFE_P3_GUARD"
    return "OTHER"


def feature_columns(columns):
    keep = []
    for col in columns:
        lower = col.lower()
        if lower.startswith(FEATURE_PREFIXES) or any(keyword in lower for keyword in FEATURE_KEYWORDS):
            keep.append(col)
    base = [
        "category",
        "video",
        "pipeline",
        "frame_id",
        "raw_frame_id",
        "evaluated_index",
        "action_label",
        "FMeasure",
        "Recall",
        "Precision",
        "Event_State",
        "latency_ms",
        "yolo_called",
        "reused_prediction",
    ]
    return list(dict.fromkeys([c for c in base + keep if c in columns]))


def event_proxy_map(per_video):
    if per_video.empty:
        return {}
    required = {"run_name", "dataset", "category", "video", "pipeline"}
    if not required.issubset(per_video.columns):
        return {}
    proxy = {}
    for _, row in per_video.iterrows():
        key = (
            str(row.get("run_name", "")),
            str(row.get("dataset", "")),
            str(row.get("category", "")),
            str(row.get("video", "")),
            str(row.get("pipeline", "")),
        )
        proxy[key] = float(pd.to_numeric(pd.Series([row.get("Event_F1", 0.0)]), errors="coerce").fillna(0.0).iloc[0])
    return proxy


def build_inventory(frame_files, per_video):
    per_video_keys = set()
    if not per_video.empty and {"run_name", "dataset", "category", "video", "pipeline"}.issubset(per_video.columns):
        for _, row in per_video.iterrows():
            per_video_keys.add(
                (
                    str(row["run_name"]),
                    str(row["dataset"]),
                    str(row["category"]),
                    str(row["video"]),
                    str(row["pipeline"]),
                )
            )

    rows = []
    frame_keys = set()
    for item in frame_files:
        header = read_csv_safe(item["frame_path"], nrows=0)
        count = 0
        if not header.empty or item["frame_path"].exists():
            try:
                count = sum(1 for _ in item["frame_path"].open("r", encoding="utf-8", errors="ignore")) - 1
            except Exception:
                count = 0
        key = (item["run_name"], item["dataset"], item["category"], item["video"], item["pipeline"])
        frame_keys.add(key)
        rows.append(
            {
                "run_name": item["run_name"],
                "dataset": item["dataset"],
                "category": item["category"],
                "video": item["video"],
                "pipeline": item["pipeline"],
                "has_frame_metrics": True,
                "has_per_video_summary": key in per_video_keys,
                "frame_count": max(0, count),
                "source_folder": item["source_folder"],
            }
        )
    for key in sorted(per_video_keys - frame_keys):
        rows.append(
            {
                "run_name": key[0],
                "dataset": key[1],
                "category": key[2],
                "video": key[3],
                "pipeline": key[4],
                "has_frame_metrics": False,
                "has_per_video_summary": True,
                "frame_count": 0,
                "source_folder": "",
            }
        )
    return pd.DataFrame(rows)


def coerce_runtime_columns(df):
    for col in df.columns:
        lower = col.lower()
        if col in {"category", "video", "pipeline", "action_label", "action_bucket", "Event_State", "source_folder", "dataset", "run_name", "run_id", "risk_class"}:
            continue
        if any(hint in lower for hint in NUMERIC_HINTS):
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def unsafe_flags(df):
    bucket = df["action_bucket"].astype(str)
    category = df["category"].astype(str)
    event_state = df.get("Event_State", pd.Series("", index=df.index)).fillna("").astype(str)
    event_context = event_state.isin(["TP", "FP", "FN"])
    event_context |= boolish(df.get("active_event_memory", pd.Series(0, index=df.index))).gt(0)
    motion_context = boolish(df.get("gmq_global_motion_risk", pd.Series(0, index=df.index))).gt(0.5)
    motion_context |= boolish(df.get("global_motion_proxy", pd.Series(0, index=df.index))).gt(0.5)
    motion_context |= boolish(df.get("continuous_pan_signature_active", pd.Series(0, index=df.index))).gt(0)
    low_comp = boolish(df.get("motion_comp_compensated_trust_low", pd.Series(0, index=df.index))).gt(0)
    geom_score = pd.to_numeric(df.get("geometry_trust_score", pd.Series(np.nan, index=df.index)), errors="coerce")
    geom_band = df.get("geometry_trust_band", pd.Series("", index=df.index)).fillna("").astype(str).str.lower()
    low_geom = geom_score.lt(0.35) | geom_band.isin(["low", "bad", "poor"])
    frames_since = pd.to_numeric(df.get("frames_since_last_detector", pd.Series(np.nan, index=df.index)), errors="coerce")
    cadence_broken = frames_since.fillna(999).gt(3)
    ptz_context = category.eq("PTZ") | motion_context

    closed_empty_unsafe = bucket.eq("CLOSED_EMPTY") & (event_context | motion_context)
    reuse_unsafe = bucket.eq("REUSE_ACC") & (low_comp | low_geom)
    light_p3_unsafe = bucket.eq("LIGHTWEIGHT_MASK_P3_FALLBACK") & ptz_context
    legacy_unsafe = bucket.eq("LEGACY_SAFE_P3_GUARD") & cadence_broken
    unsafe = closed_empty_unsafe | reuse_unsafe | light_p3_unsafe | legacy_unsafe

    reasons = np.select(
        [closed_empty_unsafe, reuse_unsafe, light_p3_unsafe, legacy_unsafe],
        [
            "closed_empty_during_event_or_motion",
            "reuse_under_low_trust",
            "lightweight_p3_under_ptz",
            "legacy_safe_without_detector_cadence",
        ],
        default="",
    )
    risk = np.where(unsafe, "unsafe", np.where(event_context | motion_context | low_comp | low_geom, "medium", "low"))
    return unsafe.astype(int), pd.Series(reasons, index=df.index), pd.Series(risk, index=df.index)


def build_frame_dataset(frame_files, per_video):
    proxy = event_proxy_map(per_video)
    frames = []
    label_values = set()
    for idx, item in enumerate(frame_files):
        header = read_csv_safe(item["frame_path"], nrows=0)
        if header.empty and not item["frame_path"].exists():
            continue
        cols = feature_columns(list(header.columns))
        df = read_csv_safe(item["frame_path"], usecols=cols if cols else None)
        if df.empty:
            continue
        for key in ["category", "video", "pipeline"]:
            df[key] = item[key]
        df["run_name"] = item["run_name"]
        df["dataset"] = item["dataset"]
        df["run_id"] = f"{item['dataset']}::{item['run_name']}"
        df["source_folder"] = item["source_folder"]
        if "frame_id" not in df.columns:
            df["frame_id"] = np.arange(len(df))
        if "action_label" not in df.columns:
            df["action_label"] = ""
        df["action_bucket"] = df["action_label"].map(action_bucket)
        label_values.update(df["action_label"].dropna().astype(str).unique().tolist())
        df["Event_proxy"] = proxy.get(
            (item["run_name"], item["dataset"], item["category"], item["video"], item["pipeline"]),
            0.0,
        )
        for col in ["FMeasure", "Recall", "Precision", "latency_ms", "yolo_called", "reused_prediction"]:
            if col not in df.columns:
                df[col] = 0.0
        df = coerce_runtime_columns(df)
        df["normalized_latency"] = pd.to_numeric(df["latency_ms"], errors="coerce").fillna(0.0).div(300.0).clip(0.0, 2.0)
        unsafe_penalty, unsafe_reason, risk_class = unsafe_flags(df)
        df["unsafe_action_penalty"] = unsafe_penalty
        df["unsafe_action_label"] = unsafe_reason
        df["risk_class"] = risk_class
        df["detector_needed"] = df["action_bucket"].isin(["DETECT_ACC", "FALLBACK_P3_GUARD", "LEGACY_SAFE_P3_GUARD"]).astype(int)
        df["utility_score"] = (
            pd.to_numeric(df["FMeasure"], errors="coerce").fillna(0.0)
            + 0.3 * pd.to_numeric(df["Event_proxy"], errors="coerce").fillna(0.0)
            - 0.05 * df["normalized_latency"]
            - 0.03 * boolish(df["yolo_called"])
            - 0.05 * df["unsafe_action_penalty"]
        )
        frames.append(df)
        if (idx + 1) % 100 == 0:
            print(f"[INFO] loaded {idx + 1}/{len(frame_files)} frame metric files")

    if not frames:
        return pd.DataFrame(), []
    dataset = pd.concat(frames, ignore_index=True, sort=False)
    leading = [
        "run_id",
        "run_name",
        "source_folder",
        "dataset",
        "category",
        "video",
        "frame_id",
        "pipeline",
        "action_label",
        "action_bucket",
        "FMeasure",
        "Recall",
        "Precision",
        "Event_proxy",
        "latency_ms",
        "normalized_latency",
        "yolo_called",
        "reused_prediction",
        "utility_score",
        "unsafe_action_penalty",
        "unsafe_action_label",
        "risk_class",
        "detector_needed",
    ]
    cols = list(dict.fromkeys([c for c in leading if c in dataset.columns] + [c for c in dataset.columns if c not in leading]))
    return dataset[cols], sorted(label_values)


def write_action_mapping(labels):
    rows = [{"raw_action_label": label, "action_bucket": action_bucket(label)} for label in sorted(labels)]
    for bucket in ACTION_BUCKETS:
        rows.append({"raw_action_label": f"__BUCKET__{bucket}", "action_bucket": bucket})
    mapping = pd.DataFrame(rows).drop_duplicates()
    mapping.to_csv(OUTPUT_ROOT / "action_label_mapping.csv", index=False)
    return mapping


def build_window_dataset(frame_df):
    if frame_df.empty:
        return pd.DataFrame()
    base = frame_df.copy()
    sort_id = pd.to_numeric(base["frame_id"], errors="coerce")
    fallback_sort = pd.Series(np.arange(len(base)), index=base.index)
    base["frame_id_sort"] = sort_id.where(sort_id.notna(), fallback_sort)
    sort_cols = ["run_id", "category", "video", "pipeline", "frame_id_sort"]
    base = base.sort_values(sort_cols)
    rows = []
    for _, group in base.groupby(["run_id", "dataset", "category", "video", "pipeline"], dropna=False):
        group = group.sort_values("frame_id_sort").copy()
        for size in [3, 5, 10]:
            out = group[["run_id", "dataset", "category", "video", "pipeline", "frame_id", "action_bucket"]].copy()
            out["window_size"] = size
            frames_since = pd.to_numeric(group.get("frames_since_last_detector", pd.Series(np.nan, index=group.index)), errors="coerce")
            out["window_frames_since_last_detector_mean"] = frames_since.rolling(size, min_periods=1).mean().values
            out["window_frames_since_last_detector_max"] = frames_since.rolling(size, min_periods=1).max().values
            out["window_detector_count"] = group["action_bucket"].isin(["DETECT_ACC", "FALLBACK_P3_GUARD", "LEGACY_SAFE_P3_GUARD"]).astype(int).rolling(size, min_periods=1).sum().values
            out["window_reuse_count"] = group["action_bucket"].eq("REUSE_ACC").astype(int).rolling(size, min_periods=1).sum().values
            out["window_closed_empty_count"] = group["action_bucket"].eq("CLOSED_EMPTY").astype(int).rolling(size, min_periods=1).sum().values
            out["window_mean_utility"] = pd.to_numeric(group["utility_score"], errors="coerce").fillna(0.0).rolling(size, min_periods=1).mean().values
            for bucket in ACTION_BUCKETS:
                out[f"window_action_rate_{bucket}"] = group["action_bucket"].eq(bucket).astype(int).rolling(size, min_periods=1).mean().values
            next_bucket = group["action_bucket"].shift(-1).fillna("END")
            next_unsafe = group["unsafe_action_penalty"].shift(-1).fillna(0).astype(float).gt(0)
            out["next_action_needed"] = np.where(next_unsafe, "SAFETY_INTERVENTION", next_bucket)
            rows.append(out)
    return pd.concat(rows, ignore_index=True, sort=False) if rows else pd.DataFrame()


def per_video_teacher_rows(per_video, frame_df):
    if per_video.empty:
        return pd.DataFrame()
    pv = normalize_pipeline_columns(per_video).copy()
    for col in ["FMeasure", "Event_F1", "avg_latency_ms", "P95_latency_ms"]:
        if col not in pv.columns:
            pv[col] = 0.0
        pv[col] = pd.to_numeric(pv[col], errors="coerce").fillna(0.0)
    pv["teacher_id"] = np.where(pv["dataset"].eq("phase7c_ablation"), pv["run_name"], pv["pipeline"])
    teacher_mask = pv["pipeline"].isin(TEACHER_PIPELINES) | pv["dataset"].eq("phase7c_ablation")
    pv = pv[teacher_mask].copy()
    if pv.empty:
        return pd.DataFrame()
    dominant_action = {}
    if not frame_df.empty:
        grouped = frame_df.groupby(["run_name", "dataset", "category", "video", "pipeline"])["action_bucket"]
        dominant_action = grouped.agg(lambda s: s.value_counts().idxmax() if len(s) else "OTHER").to_dict()
    rows = []
    group_cols = ["dataset", "category", "video"]
    for key, group in pv.groupby(group_cols, dropna=False):
        group = group.copy()
        group["AE_proxy"] = group["FMeasure"] + 0.3 * group["Event_F1"] - 0.05 * group["P95_latency_ms"].div(300.0).clip(0, 2)
        guarded = group[group["pipeline"].eq(GUARDED)]
        guarded_f = float(guarded["FMeasure"].max()) if not guarded.empty else np.nan
        best_f = group.sort_values(["FMeasure", "Event_F1"], ascending=False).iloc[0]
        best_e = group.sort_values(["Event_F1", "FMeasure"], ascending=False).iloc[0]
        best_ae = group.sort_values(["AE_proxy", "FMeasure"], ascending=False).iloc[0]
        action_key = (
            str(best_f["run_name"]),
            str(best_f["dataset"]),
            str(best_f["category"]),
            str(best_f["video"]),
            str(best_f["pipeline"]),
        )
        rows.append(
            {
                "dataset": key[0],
                "category": key[1],
                "video": key[2],
                "best_teacher_by_FMeasure": best_f["teacher_id"],
                "best_teacher_by_Event_F1": best_e["teacher_id"],
                "best_teacher_by_AE_proxy": best_ae["teacher_id"],
                "teacher_action_group": dominant_action.get(action_key, "OTHER"),
                "teacher_beats_guarded": bool(pd.notna(guarded_f) and float(best_f["FMeasure"]) > guarded_f),
                "best_teacher_FMeasure": float(best_f["FMeasure"]),
                "guarded_FMeasure": guarded_f,
                "best_teacher_Event_F1": float(best_e["Event_F1"]),
                "best_teacher_AE_proxy": float(best_ae["AE_proxy"]),
                "candidate_teacher_count": int(len(group)),
            }
        )
    return pd.DataFrame(rows)


def build_oracle_dataset(frame_df):
    if frame_df.empty:
        return pd.DataFrame()
    group_cols = ["dataset", "category", "video", "frame_id"]
    work = frame_df.copy()
    work["utility_score"] = pd.to_numeric(work["utility_score"], errors="coerce").fillna(-999.0)
    work["FMeasure"] = pd.to_numeric(work["FMeasure"], errors="coerce").fillna(0.0)
    work["unsafe_action_penalty"] = pd.to_numeric(work["unsafe_action_penalty"], errors="coerce").fillna(0.0)

    best_idx = work.groupby(group_cols, dropna=False)["utility_score"].idxmax()
    best = work.loc[best_idx, group_cols + ["action_bucket", "utility_score", "FMeasure", "pipeline", "run_id"]].copy()
    best = best.rename(
        columns={
            "action_bucket": "best_action_by_utility",
            "utility_score": "best_utility_score",
            "FMeasure": "best_FMeasure",
            "pipeline": "best_oracle_pipeline",
            "run_id": "best_oracle_run_id",
        }
    )

    safe_work = work[work["unsafe_action_penalty"].eq(0)].copy()
    if safe_work.empty:
        safe = best[group_cols + ["best_action_by_utility"]].rename(columns={"best_action_by_utility": "best_safe_action"})
    else:
        safe_idx = safe_work.groupby(group_cols, dropna=False)["utility_score"].idxmax()
        safe = safe_work.loc[safe_idx, group_cols + ["action_bucket"]].rename(columns={"action_bucket": "best_safe_action"})
        safe = best[group_cols].merge(safe, on=group_cols, how="left").merge(
            best[group_cols + ["best_action_by_utility"]],
            on=group_cols,
            how="left",
        )
        safe["best_safe_action"] = safe["best_safe_action"].fillna(safe["best_action_by_utility"])
        safe = safe[group_cols + ["best_safe_action"]]

    unsafe = (
        work.groupby(group_cols, dropna=False)["unsafe_action_penalty"]
        .max()
        .reset_index()
        .rename(columns={"unsafe_action_penalty": "unsafe_action"})
    )
    unsafe["unsafe_action"] = unsafe["unsafe_action"].gt(0)

    guarded = work[work["pipeline"].eq(GUARDED)].drop_duplicates(group_cols)
    fallback = work.drop_duplicates(group_cols)
    guarded = fallback[group_cols + ["utility_score", "FMeasure"]].merge(
        guarded[group_cols + ["utility_score", "FMeasure"]],
        on=group_cols,
        how="left",
        suffixes=("_fallback", "_guarded"),
    )
    guarded["guarded_utility_score"] = guarded["utility_score_guarded"].fillna(guarded["utility_score_fallback"])
    guarded["guarded_FMeasure"] = guarded["FMeasure_guarded"].fillna(guarded["FMeasure_fallback"])
    guarded = guarded[group_cols + ["guarded_utility_score", "guarded_FMeasure"]]

    oracle = best.merge(safe, on=group_cols, how="left").merge(unsafe, on=group_cols, how="left").merge(guarded, on=group_cols, how="left")
    oracle["expected_utility_gain"] = oracle["best_utility_score"] - oracle["guarded_utility_score"]
    oracle["expected_FMeasure_gain"] = oracle["best_FMeasure"] - oracle["guarded_FMeasure"]
    return oracle[
        group_cols
        + [
            "best_action_by_utility",
            "best_safe_action",
            "unsafe_action",
            "expected_utility_gain",
            "expected_FMeasure_gain",
            "best_oracle_pipeline",
            "best_oracle_run_id",
        ]
    ]


def write_splits(frame_df):
    split_root = OUTPUT_ROOT / "splits"
    split_root.mkdir(parents=True, exist_ok=True)
    videos = frame_df[["dataset", "category", "video"]].drop_duplicates().sort_values(["category", "video", "dataset"])
    video_names = sorted(videos["video"].astype(str).unique())
    rows = []
    for fold, heldout in enumerate(video_names):
        for _, row in videos.iterrows():
            rows.append({**row.to_dict(), "fold_id": fold, "heldout_video": heldout, "role": "test" if str(row["video"]) == heldout else "train"})
    pd.DataFrame(rows).to_csv(split_root / "split_leave_one_video.csv", index=False)

    categories = sorted(videos["category"].astype(str).unique())
    rows = []
    for fold, heldout in enumerate(categories):
        for _, row in videos.iterrows():
            rows.append({**row.to_dict(), "fold_id": fold, "heldout_category": heldout, "role": "test" if str(row["category"]) == heldout else "train"})
    pd.DataFrame(rows).to_csv(split_root / "split_leave_one_category.csv", index=False)

    ptz = videos.copy()
    ptz["role"] = np.where(ptz["category"].astype(str).eq("PTZ"), "test", "train")
    ptz["split_name"] = "ptz_holdout"
    ptz.to_csv(split_root / "split_ptz_holdout.csv", index=False)

    targeted_videos = set(videos[videos["dataset"].astype(str).eq("targeted")]["video"].astype(str))
    smoke_targeted = videos.copy()
    smoke_targeted["role"] = np.where(smoke_targeted["video"].astype(str).isin(targeted_videos), "test", "train")
    smoke_targeted["split_name"] = "smoke_vs_targeted_video_safe"
    smoke_targeted["targeted_video_holdout"] = smoke_targeted["video"].astype(str).isin(targeted_videos)
    smoke_targeted.to_csv(split_root / "split_smoke_vs_targeted.csv", index=False)


def value_counts_table(series):
    if series.empty:
        return "none"
    rows = series.fillna("").astype(str).value_counts().reset_index()
    rows.columns = ["label", "count"]
    return rows.to_csv(index=False).strip()


def write_report(frame_df, window_df, teacher_df, oracle_df, inventory):
    missing = frame_df.isna().mean().sort_values(ascending=False).head(30) if not frame_df.empty else pd.Series(dtype=float)
    feature_cols = [c for c in frame_df.columns if c.startswith(FEATURE_PREFIXES) or any(k in c.lower() for k in FEATURE_KEYWORDS)]
    missing_feature_report = pd.DataFrame(
        {
            "feature": feature_cols,
            "missing_rate": [float(frame_df[c].isna().mean()) for c in feature_cols],
        }
    ).sort_values("missing_rate", ascending=False)
    missing_feature_report.to_csv(OUTPUT_ROOT / "missing_feature_report.csv", index=False)

    leakage_video = pd.read_csv(OUTPUT_ROOT / "splits" / "split_leave_one_video.csv")
    leakage_ok = bool((leakage_video.groupby("fold_id").apply(lambda g: set(g[g.role == "train"].video).isdisjoint(set(g[g.role == "test"].video))).all()))
    utility_by_bucket = frame_df.groupby("action_bucket")["utility_score"].agg(["count", "mean", "median"]).reset_index() if not frame_df.empty else pd.DataFrame()
    utility_by_bucket.to_csv(OUTPUT_ROOT / "utility_sanity_by_action.csv", index=False)

    lines = [
        "# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8A Dataset Report",
        "",
        "Phase 8A is research-only. No experiment runner was launched and no production pipeline behavior was modified.",
        "",
        "## Dataset Size",
        "",
        f"- frame rows: {len(frame_df)}",
        f"- window rows: {len(window_df)}",
        f"- teacher label rows: {len(teacher_df)}",
        f"- oracle label rows: {len(oracle_df)}",
        f"- inventory rows: {len(inventory)}",
        f"- videos: {frame_df['video'].nunique() if not frame_df.empty else 0}",
        f"- categories: {frame_df['category'].nunique() if not frame_df.empty else 0}",
        f"- pipelines: {frame_df['pipeline'].nunique() if not frame_df.empty else 0}",
        "",
        "## Label Distributions",
        "",
        "### Action Bucket",
        "```csv",
        value_counts_table(frame_df["action_bucket"] if "action_bucket" in frame_df else pd.Series(dtype=str)),
        "```",
        "",
        "### Risk Class",
        "```csv",
        value_counts_table(frame_df["risk_class"] if "risk_class" in frame_df else pd.Series(dtype=str)),
        "```",
        "",
        "### Oracle Best Action",
        "```csv",
        value_counts_table(oracle_df["best_action_by_utility"] if "best_action_by_utility" in oracle_df else pd.Series(dtype=str)),
        "```",
        "",
        "## Missing Feature Report",
        "",
        "Top missing columns:",
        "```csv",
        missing.head(20).reset_index().rename(columns={"index": "column", 0: "missing_rate"}).to_csv(index=False).strip(),
        "```",
        "",
        "## Unsafe Action Distribution",
        "```csv",
        value_counts_table(frame_df["unsafe_action_label"] if "unsafe_action_label" in frame_df else pd.Series(dtype=str)),
        "```",
        "",
        "## PTZ Samples",
        f"- PTZ frame rows: {int(frame_df['category'].astype(str).eq('PTZ').sum()) if not frame_df.empty else 0}",
        f"- PTZ videos: {frame_df.loc[frame_df['category'].astype(str).eq('PTZ'), 'video'].nunique() if not frame_df.empty else 0}",
        "",
        "## Non-PTZ Samples",
        f"- non-PTZ frame rows: {int((~frame_df['category'].astype(str).eq('PTZ')).sum()) if not frame_df.empty else 0}",
        f"- non-PTZ videos: {frame_df.loc[~frame_df['category'].astype(str).eq('PTZ'), 'video'].nunique() if not frame_df.empty else 0}",
        "",
        "## Leakage Checks",
        f"- leave-one-video train/test video-disjoint: {leakage_ok}",
        "- `split_smoke_vs_targeted.csv` holds out any video that appears in targeted, across all datasets, to avoid same-video leakage.",
        "",
        "## Utility Sanity Checks",
        "```csv",
        utility_by_bucket.to_csv(index=False).strip(),
        "```",
        "",
        "## Teacher Label Summary",
        "```csv",
        value_counts_table(teacher_df["best_teacher_by_FMeasure"] if "best_teacher_by_FMeasure" in teacher_df else pd.Series(dtype=str)),
        "```",
        "",
        "## Oracle Label Summary",
        "```csv",
        value_counts_table(oracle_df["best_safe_action"] if "best_safe_action" in oracle_df else pd.Series(dtype=str)),
        "```",
        "",
        "## Phase 8B Readiness",
        "",
        "The dataset is sufficient for Phase 8B research probes and offline policy learning experiments, but not for deployment. Labels mix observational baselines, ablation outputs, and derived utilities, so any learned model must remain behind deterministic safety guards and smoke validation.",
        "",
        "Deployment recommendation: do not deploy a learned policy from Phase 8A artifacts alone.",
        "",
    ]
    Path("docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8A_DATASET_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    global OUTPUT_ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default=str(OUTPUT_ROOT))
    args = parser.parse_args()
    OUTPUT_ROOT = Path(args.output_root)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    specs = source_specs()
    per_video = load_per_video(specs)
    frame_files = discover_frame_files(specs)
    print(f"[INFO] sources={len(specs)} frame_metric_files={len(frame_files)}")

    inventory = build_inventory(frame_files, per_video)
    inventory.to_csv(OUTPUT_ROOT / "data_inventory.csv", index=False)

    frame_df, labels = build_frame_dataset(frame_files, per_video)
    write_action_mapping(labels)
    frame_df.to_parquet(OUTPUT_ROOT / "frame_state_dataset.parquet", index=False)
    frame_df.head(5000).to_csv(OUTPUT_ROOT / "frame_state_dataset_sample.csv", index=False)

    window_df = build_window_dataset(frame_df)
    window_df.to_parquet(OUTPUT_ROOT / "window_state_dataset.parquet", index=False)
    window_df.head(5000).to_csv(OUTPUT_ROOT / "window_state_dataset_sample.csv", index=False)

    teacher_df = per_video_teacher_rows(per_video, frame_df)
    teacher_df.to_parquet(OUTPUT_ROOT / "teacher_label_dataset.parquet", index=False)

    oracle_df = build_oracle_dataset(frame_df)
    oracle_df.to_parquet(OUTPUT_ROOT / "oracle_action_dataset.parquet", index=False)

    write_splits(frame_df)
    write_report(frame_df, window_df, teacher_df, oracle_df, inventory)
    print(f"[DONE] wrote Phase 8A policy dataset under {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
