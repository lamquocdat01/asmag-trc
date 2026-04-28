import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


PIPELINE_ORDER = [
    "P1_YOLO_Only",
    "P2_FrameDiff",
    "P3_MOG2",
    "P4_ASMAG_PLUS",
    "ASMAG_TR_ACC",
    "ASMAG_TR_FAST",
    "ASMAG_TR_CONTROLLER",
]


def read_csv(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def pipeline_level(df, value_cols):
    if "aggregation_level" in df.columns:
        d = df[df["aggregation_level"] == "pipeline"].copy()
        if d.empty:
            d = df.copy()
    else:
        d = df.copy()
    cols = ["pipeline"] + [c for c in value_cols if c in d.columns]
    return d[cols].groupby("pipeline", as_index=False).mean(numeric_only=True)


def video_level(df, value_cols):
    if "aggregation_level" in df.columns:
        d = df[df["aggregation_level"] == "video"].copy()
        if d.empty:
            d = df.copy()
    else:
        d = df.copy()
    cols = ["category", "video", "pipeline"] + [c for c in value_cols if c in d.columns]
    return d[cols].groupby(["category", "video", "pipeline"], as_index=False).mean(numeric_only=True)


def category_level(df, value_cols):
    if "aggregation_level" in df.columns:
        d = df[df["aggregation_level"] == "category"].copy()
        if d.empty:
            d = df.copy()
    else:
        d = df.copy()
    cols = ["category", "pipeline"] + [c for c in value_cols if c in d.columns]
    return d[cols].groupby(["category", "pipeline"], as_index=False).mean(numeric_only=True)


def merge_frames(frames, keys):
    merged = frames[0]
    for df in frames[1:]:
        merged = merged.merge(df, on=keys, how="outer")
    return merged


def build_main(out_dir):
    cdnet = read_csv(out_dir / "summary_cdnet_metrics.csv")
    objects = read_csv(out_dir / "summary_object_metrics.csv")
    events = read_csv(out_dir / "summary_event_metrics.csv")
    edge = read_csv(out_dir / "summary_edge_metrics.csv")
    energy = read_csv(out_dir / "summary_edge_energy_metrics.csv")
    pareto = read_csv(out_dir / "summary_pareto_metrics.csv")

    cdnet_p = pipeline_level(cdnet, ["Precision", "Recall", "FMeasure", "PWC"]).rename(
        columns={
            "Precision": "CDnet_Precision",
            "Recall": "CDnet_Recall",
            "FMeasure": "CDnet_FMeasure",
            "PWC": "CDnet_PWC",
        }
    )
    obj_p = pipeline_level(
        objects,
        ["Object_Precision", "Object_Recall", "Object_F1", "mAP_50", "mAP_50_95_proxy"],
    )
    event_p = pipeline_level(events, ["Event_F1", "MCC"])
    edge_p = pipeline_level(edge, ["YOLO_activation_rate", "avg_FPS", "P95_latency_ms", "reused_prediction_rate"]).rename(
        columns={
            "YOLO_activation_rate": "Activation",
            "avg_FPS": "Avg_FPS",
            "reused_prediction_rate": "Reuse_rate",
        }
    )
    energy_p = pipeline_level(
        energy,
        [
            "Estimated_energy_per_frame",
            "Energy_reduction_rate_vs_P1_YOLO_Only",
            "Energy_reduction_rate_vs_P4_ASMAG_PLUS",
        ],
    ).rename(
        columns={
            "Energy_reduction_rate_vs_P1_YOLO_Only": "Energy_reduction_rate_vs_P1",
            "Energy_reduction_rate_vs_P4_ASMAG_PLUS": "Energy_reduction_rate_vs_P4",
        }
    )
    pareto_p = pareto[["pipeline", "AE_Score", "Pareto_Efficient"]].copy()

    main = merge_frames([cdnet_p, event_p, obj_p, edge_p, energy_p, pareto_p], ["pipeline"])
    main = main.rename(columns={"pipeline": "Pipeline"})
    main["Pipeline"] = pd.Categorical(main["Pipeline"], categories=PIPELINE_ORDER, ordered=True)
    main = main.sort_values("Pipeline")
    main["Pipeline"] = main["Pipeline"].astype(str)
    cols = [
        "Pipeline",
        "CDnet_Precision",
        "CDnet_Recall",
        "CDnet_FMeasure",
        "CDnet_PWC",
        "Event_F1",
        "MCC",
        "Object_Precision",
        "Object_Recall",
        "Object_F1",
        "mAP_50",
        "mAP_50_95_proxy",
        "Activation",
        "Avg_FPS",
        "P95_latency_ms",
        "Estimated_energy_per_frame",
        "Energy_reduction_rate_vs_P1",
        "Energy_reduction_rate_vs_P4",
        "Reuse_rate",
        "AE_Score",
        "Pareto_Efficient",
    ]
    return main[cols]


def build_best_by_metric(main):
    specs = [
        ("Best CDnet_FMeasure", "CDnet_FMeasure", False),
        ("Best CDnet_PWC", "CDnet_PWC", True),
        ("Best Event_F1", "Event_F1", False),
        ("Best MCC", "MCC", False),
        ("Best Object_F1", "Object_F1", False),
        ("Best mAP_50", "mAP_50", False),
        ("Best mAP_50_95_proxy", "mAP_50_95_proxy", False),
        ("Lowest Activation", "Activation", True),
        ("Highest Avg_FPS", "Avg_FPS", False),
        ("Lowest P95_latency_ms", "P95_latency_ms", True),
        ("Lowest Estimated_energy_per_frame", "Estimated_energy_per_frame", True),
        ("Highest Energy_reduction_rate_vs_P1", "Energy_reduction_rate_vs_P1", False),
        ("Highest AE_Score", "AE_Score", False),
    ]
    rows = []
    for label, col, ascending in specs:
        row = main.sort_values(col, ascending=ascending).iloc[0]
        rows.append({"metric": label, "Pipeline": row["Pipeline"], "value": row[col]})
    return pd.DataFrame(rows)


def build_rankings(main):
    ranking = main[["Pipeline"]].copy()
    rank_specs = [
        ("CDnet_FMeasure_rank", "CDnet_FMeasure", False),
        ("Event_F1_rank", "Event_F1", False),
        ("mAP_50_rank", "mAP_50", False),
        ("Activation_rank", "Activation", True),
        ("Avg_FPS_rank", "Avg_FPS", False),
        ("Energy_rank", "Estimated_energy_per_frame", True),
        ("AE_Score_rank", "AE_Score", False),
    ]
    for rank_col, metric_col, ascending in rank_specs:
        ranking[rank_col] = main[metric_col].rank(method="min", ascending=ascending)
    rank_cols = [spec[0] for spec in rank_specs]
    ranking["Average_rank"] = ranking[rank_cols].mean(axis=1)
    return ranking.sort_values("Average_rank")


def build_category_insight(out_dir):
    cdnet = category_level(read_csv(out_dir / "summary_cdnet_metrics.csv"), ["FMeasure"])
    event = category_level(read_csv(out_dir / "summary_event_metrics.csv"), ["Event_F1"])
    obj = category_level(read_csv(out_dir / "summary_object_metrics.csv"), ["mAP_50"])
    edge = category_level(read_csv(out_dir / "summary_edge_metrics.csv"), ["YOLO_activation_rate", "avg_FPS"])
    energy = category_level(read_csv(out_dir / "summary_edge_energy_metrics.csv"), ["Estimated_energy_per_frame"])

    categories = sorted(set(cdnet["category"]))
    rows = []
    for category in categories:
        c_cd = cdnet[cdnet["category"] == category].copy()
        c_ev = event[event["category"] == category].copy()
        c_obj = obj[obj["category"] == category].copy()
        c_edge = edge[edge["category"] == category].copy()
        c_energy = energy[energy["category"] == category].copy()
        acc_rank = _rank_pipeline(c_cd, "ASMAG_TR_ACC", "FMeasure", ascending=False)
        fast_activation_rank = _rank_pipeline(c_edge, "ASMAG_TR_FAST", "YOLO_activation_rate", ascending=True)
        best_f = _best_pipeline(c_cd, "FMeasure", False)
        best_fast = _best_pipeline(c_edge, "YOLO_activation_rate", True)
        note = []
        if best_f in {"ASMAG_TR_ACC", "ASMAG_TR_FAST"}:
            note.append("ASMAG-TR leads FMeasure")
        if best_fast == "ASMAG_TR_FAST":
            note.append("FAST leads activation saving")
        if acc_rank and acc_rank <= 2:
            note.append("ACC is competitive")
        rows.append(
            {
                "category": category,
                "best_cdnet_fmeasure_pipeline": best_f,
                "best_event_f1_pipeline": _best_pipeline(c_ev, "Event_F1", False),
                "best_map50_pipeline": _best_pipeline(c_obj, "mAP_50", False),
                "best_activation_pipeline": best_fast,
                "best_fps_pipeline": _best_pipeline(c_edge, "avg_FPS", False),
                "best_energy_pipeline": _best_pipeline(c_energy, "Estimated_energy_per_frame", True),
                "ASMAG_TR_ACC_rank_by_FMeasure": acc_rank,
                "ASMAG_TR_FAST_rank_by_Activation": fast_activation_rank,
                "note": "; ".join(note) if note else "baseline pipelines lead primary accuracy",
            }
        )
    return pd.DataFrame(rows)


def build_video_cases(out_dir):
    cdnet = video_level(read_csv(out_dir / "summary_cdnet_metrics.csv"), ["FMeasure"])
    event = video_level(read_csv(out_dir / "summary_event_metrics.csv"), ["Event_F1"])
    edge = video_level(read_csv(out_dir / "summary_edge_metrics.csv"), ["YOLO_activation_rate"])
    energy = video_level(
        read_csv(out_dir / "summary_edge_energy_metrics.csv"),
        ["Energy_reduction_rate_vs_P1_YOLO_Only"],
    )

    cd_p = cdnet.pivot_table(index=["category", "video"], columns="pipeline", values="FMeasure")
    ev_p = event.pivot_table(index=["category", "video"], columns="pipeline", values="Event_F1")
    act_p = edge.pivot_table(index=["category", "video"], columns="pipeline", values="YOLO_activation_rate")
    en_p = energy.pivot_table(index=["category", "video"], columns="pipeline", values="Energy_reduction_rate_vs_P1_YOLO_Only")

    rows = []
    rows += _case_rows(cd_p, "ASMAG_TR_ACC", "P3_MOG2", "FMeasure", "Top 10 ASMAG_TR_ACC worse than P3_MOG2", ascending=True, diff_name="delta_vs_P3")
    rows += _case_rows(cd_p, "ASMAG_TR_FAST", "P3_MOG2", "FMeasure", "Top 10 ASMAG_TR_FAST worse than P3_MOG2", ascending=True, diff_name="delta_vs_P3")
    rows += _single_pipeline_rows(act_p, "ASMAG_TR_FAST", "YOLO_activation_rate", "Top 10 ASMAG_TR_FAST best activation saving", ascending=True)
    rows += _case_rows(ev_p, "ASMAG_TR_ACC", "P4_ASMAG_PLUS", "Event_F1", "Top 10 ASMAG_TR_ACC Event_F1 better than P4_ASMAG_PLUS", ascending=False, diff_name="delta_vs_P4")
    rows += _single_pipeline_rows(en_p, "ASMAG_TR_ACC", "Energy_reduction_rate_vs_P1", "Top 10 highest energy reduction vs P1", ascending=False)
    rows += _case_rows(cd_p, "P2_FrameDiff", "P3_MOG2", "FMeasure", "Top 10 P2_FrameDiff strongest wins", ascending=False, diff_name="delta_vs_P3")
    rows += _case_rows(cd_p, "P2_FrameDiff", "P3_MOG2", "FMeasure", "Top 10 P2_FrameDiff largest failures", ascending=True, diff_name="delta_vs_P3")
    return pd.DataFrame(rows)


def make_charts(out_dir, main):
    charts = out_dir / "charts"
    charts.mkdir(parents=True, exist_ok=True)
    _bar(main, "Pipeline", "CDnet_FMeasure", charts / "final_fmeasure_by_pipeline.png")
    _bar(main, "Pipeline", "Event_F1", charts / "final_event_f1_by_pipeline.png")
    _bar(main, "Pipeline", "mAP_50", charts / "final_map50_by_pipeline.png")
    _bar(main, "Pipeline", "Activation", charts / "final_activation_by_pipeline.png")
    _bar(main, "Pipeline", "Estimated_energy_per_frame", charts / "final_energy_by_pipeline.png")
    _bubble(main, "Activation", "CDnet_FMeasure", "Avg_FPS", charts / "pareto_activation_fmeasure_bubble_fps.png")
    _bubble(main, "Estimated_energy_per_frame", "Event_F1", "mAP_50", charts / "pareto_energy_eventf1_bubble_map50.png")

    cat = category_level(read_csv(out_dir / "summary_cdnet_metrics.csv"), ["FMeasure"])
    act = category_level(read_csv(out_dir / "summary_edge_metrics.csv"), ["YOLO_activation_rate"])
    _heatmap(cat, "FMeasure", charts / "category_fmeasure_heatmap.png", "Category FMeasure Heatmap")
    _heatmap(act, "YOLO_activation_rate", charts / "category_activation_heatmap.png", "Category Activation Heatmap")


def write_summary_md(out_dir, main, best, rankings, category_insight, video_cases):
    acc = main[main["Pipeline"] == "ASMAG_TR_ACC"].iloc[0]
    fast = main[main["Pipeline"] == "ASMAG_TR_FAST"].iloc[0]
    controller = main[main["Pipeline"] == "ASMAG_TR_CONTROLLER"]
    p3 = main[main["Pipeline"] == "P3_MOG2"].iloc[0]

    acc_ok = (p3["CDnet_FMeasure"] - acc["CDnet_FMeasure"] <= 0.05) and (acc["Activation"] < p3["Activation"] - 0.05)
    fast_ok = (
        fast["Activation"] == main["Activation"].min()
        and fast["Estimated_energy_per_frame"] == main["Estimated_energy_per_frame"].min()
    )
    tr = main[main["Pipeline"].isin(["ASMAG_TR_ACC", "ASMAG_TR_FAST", "ASMAG_TR_CONTROLLER"])]
    baselines = main[main["Pipeline"].isin(["P1_YOLO_Only", "P2_FrameDiff", "P3_MOG2", "P4_ASMAG_PLUS"])]
    tr_best = tr.sort_values("AE_Score", ascending=False).iloc[0]
    baseline_best = baselines.sort_values("AE_Score", ascending=False).iloc[0]
    controller_line = ""
    if not controller.empty:
        ctrl = controller.iloc[0]
        controller_line = (
            f"- ASMAG_TR_CONTROLLER: FMeasure {ctrl['CDnet_FMeasure']:.4f} vs P3_MOG2 {p3['CDnet_FMeasure']:.4f}, "
            f"activation {ctrl['Activation']:.4f} vs {p3['Activation']:.4f}, "
            f"energy/frame {ctrl['Estimated_energy_per_frame']:.4f} vs {p3['Estimated_energy_per_frame']:.4f}, "
            f"AE_Score {ctrl['AE_Score']:.4f}."
        )
    strong_cats = category_insight[
        category_insight["note"].str.contains("ASMAG-TR|FAST|ACC", regex=True, na=False)
    ]["category"].tolist()

    weakest_videos = video_cases[
        video_cases["case_type"].isin(
            ["Top 10 ASMAG_TR_ACC worse than P3_MOG2", "Top 10 ASMAG_TR_FAST worse than P3_MOG2"]
        )
    ].head(8)

    lines = [
        f"# Auto Research Summary: {out_dir.name}",
        "",
        f"- Best CDnet FMeasure: **{_best_name(best, 'Best CDnet_FMeasure')}**.",
        f"- Best Object mAP_50: **{_best_name(best, 'Best mAP_50')}**.",
        f"- Best Event F1: **{_best_name(best, 'Best Event_F1')}**.",
        f"- Best edge efficiency: **{_best_name(best, 'Lowest Estimated_energy_per_frame')}** by energy/frame; **{_best_name(best, 'Lowest Activation')}** by activation.",
        f"- Best AE_Score: **{_best_name(best, 'Highest AE_Score')}**.",
        "",
        "## ASMAG-TR Selection",
        f"- ASMAG_TR_ACC recommendation: {'yes, use as accuracy-preserving mode' if acc_ok else 'not as the primary accuracy mode yet'} "
        f"(FMeasure {acc['CDnet_FMeasure']:.4f} vs P3_MOG2 {p3['CDnet_FMeasure']:.4f}, activation {acc['Activation']:.4f} vs {p3['Activation']:.4f}).",
        f"- ASMAG_TR_FAST recommendation: {'yes, use as efficiency-oriented mode' if fast_ok else 'use only as an aggressive efficiency mode with accuracy trade-off'} "
        f"(activation {fast['Activation']:.4f}, energy/frame {fast['Estimated_energy_per_frame']:.4f}).",
        controller_line,
        "- ASMAG-TR should be positioned as an adaptive inference-control framework, not as a SOTA foreground segmentation method, because P2_FrameDiff/P3_MOG2 still lead several accuracy metrics.",
        "- ASMAG_TR_FAST has a visible FMeasure/mAP trade-off; this is the expected cost of lower activation and energy.",
        "",
        "## Baseline Comparison",
        f"- ASMAG-TR best AE pipeline: **{tr_best['Pipeline']}** with AE_Score {tr_best['AE_Score']:.4f}.",
        f"- Best baseline by AE_Score: **{baseline_best['Pipeline']}** with AE_Score {baseline_best['AE_Score']:.4f}.",
        f"- ASMAG-TR beats P1_YOLO_Only on activation and energy, but does not beat it on CDnet FMeasure or mAP_50.",
        f"- ASMAG-TR trails P2_FrameDiff/P3_MOG2 on the aggregate AE_Score in this sampled 6-category run.",
        "",
        "## Strengths And Weaknesses",
        f"- Strong categories/videos: {', '.join(strong_cats) if strong_cats else 'none clearly dominant at category level'}.",
        "- Weak cases include the largest FMeasure gaps against P3_MOG2:",
    ]
    for _, row in weakest_videos.iterrows():
        lines.append(
            f"  - {row['case_type']}: {row['category']}/{row['video']} "
            f"({row.get('pipeline', '')}={row.get('pipeline_value', 0):.4f}, reference={row.get('reference_value', 0):.4f}, delta={row.get('delta', 0):.4f})"
        )
    lines += [
        "",
        "## Should We Run Full CDnet2014?",
        "- Yes, but with the current framing: report ASMAG-TR as adaptive inference-control with clear efficiency gains, not as a pure segmentation accuracy winner.",
        "- Next steps: tune gate thresholds per category, add a learned confidence/reuse policy, report confidence intervals, and run full CDnet2014 with the checkpoint/resume flow now added.",
    ]
    (out_dir / "auto_research_summary.md").write_text("\n".join(lines), encoding="utf-8")


def _best_pipeline(df, col, ascending):
    if df.empty or col not in df:
        return ""
    return df.sort_values(col, ascending=ascending).iloc[0]["pipeline"]


def _rank_pipeline(df, pipeline, col, ascending):
    if df.empty or col not in df:
        return None
    d = df.copy()
    d["rank"] = d[col].rank(method="min", ascending=ascending)
    row = d[d["pipeline"] == pipeline]
    return int(row["rank"].iloc[0]) if not row.empty else None


def _case_rows(pivot, pipeline, reference, metric, case_type, ascending, diff_name):
    rows = []
    if pipeline not in pivot.columns or reference not in pivot.columns:
        return rows
    d = pd.DataFrame(
        {
            "pipeline_value": pivot[pipeline],
            "reference_value": pivot[reference],
        }
    ).dropna()
    d["delta"] = d["pipeline_value"] - d["reference_value"]
    d = d.sort_values("delta", ascending=ascending).head(10)
    for (category, video), row in d.iterrows():
        rows.append(
            {
                "case_type": case_type,
                "category": category,
                "video": video,
                "pipeline": pipeline,
                "reference_pipeline": reference,
                "metric": metric,
                "pipeline_value": row["pipeline_value"],
                "reference_value": row["reference_value"],
                "delta": row["delta"],
                "rank_metric": diff_name,
            }
        )
    return rows


def _single_pipeline_rows(pivot, pipeline, metric, case_type, ascending):
    rows = []
    if pipeline not in pivot.columns:
        return rows
    d = pivot[[pipeline]].dropna().sort_values(pipeline, ascending=ascending).head(10)
    for (category, video), row in d.iterrows():
        rows.append(
            {
                "case_type": case_type,
                "category": category,
                "video": video,
                "pipeline": pipeline,
                "reference_pipeline": "",
                "metric": metric,
                "pipeline_value": row[pipeline],
                "reference_value": "",
                "delta": "",
                "rank_metric": metric,
            }
        )
    return rows


def _bar(df, x, y, out_path):
    plt.figure(figsize=(10, 5))
    plt.bar(df[x].astype(str), df[y].astype(float))
    plt.ylabel(y)
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()


def _bubble(df, x, y, size, out_path):
    vals = df[size].astype(float)
    denom = vals.max() - vals.min()
    sizes = [240] * len(vals) if denom <= 0 else (120 + 580 * (vals - vals.min()) / denom).tolist()
    plt.figure(figsize=(8, 6))
    plt.scatter(df[x].astype(float), df[y].astype(float), s=sizes, alpha=0.72)
    for _, row in df.iterrows():
        plt.annotate(row["Pipeline"], (row[x], row[y]), fontsize=8)
    plt.xlabel(x)
    plt.ylabel(y)
    plt.grid(True, alpha=0.25)
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()


def _heatmap(df, value_col, out_path, title):
    pivot = df.pivot(index="category", columns="pipeline", values=value_col).reindex(columns=PIPELINE_ORDER)
    plt.figure(figsize=(14, 6))
    plt.imshow(pivot.values.astype(float), aspect="auto", cmap="viridis")
    plt.colorbar(label=value_col)
    plt.xticks(range(len(pivot.columns)), pivot.columns, rotation=25, ha="right")
    plt.yticks(range(len(pivot.index)), pivot.index)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()


def _best_name(best, metric):
    row = best[best["metric"] == metric]
    return row["Pipeline"].iloc[0] if not row.empty else ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="outputs/q2_core_full_metrics")
    args = parser.parse_args()
    out_dir = Path(args.out_dir)

    main_cmp = build_main(out_dir)
    best = build_best_by_metric(main_cmp)
    rankings = build_rankings(main_cmp)
    category_insight = build_category_insight(out_dir)
    video_cases = build_video_cases(out_dir)

    main_cmp.to_csv(out_dir / "final_main_comparison.csv", index=False)
    best.to_csv(out_dir / "best_by_metric.csv", index=False)
    rankings.to_csv(out_dir / "final_rankings.csv", index=False)
    category_insight.to_csv(out_dir / "category_wise_insight.csv", index=False)
    video_cases.to_csv(out_dir / "video_wise_failure_cases.csv", index=False)
    make_charts(out_dir, main_cmp)
    write_summary_md(out_dir, main_cmp, best, rankings, category_insight, video_cases)

    print("\n[final_main_comparison]")
    print(main_cmp.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print("\n[best_by_metric]")
    print(best.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print("\n[short conclusion]")
    lines = (out_dir / "auto_research_summary.md").read_text(encoding="utf-8").splitlines()
    bullets = [line for line in lines if line.startswith("- ")][:7]
    print("\n".join(bullets))


if __name__ == "__main__":
    main()
