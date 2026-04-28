from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

def short_pipeline(name):
    return str(name).replace("P4_ASMAG_PLUS_EFFICIENT_REUSE", "P4_EFFICIENT_REUSE")

def save_bar(df, x, y, title, out_path):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(10,5))
    labels = df[x].astype(str).tolist()
    vals = df[y].astype(float).tolist()
    plt.bar(labels, vals)
    plt.title(title)
    plt.ylabel(y)
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()

def save_pareto(df, out_path):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8, 6))
    x = df["YOLO_activation_rate"].astype(float)
    y = df["FMeasure"].astype(float)
    plt.scatter(x, y, s=80)
    for _, row in df.iterrows():
        plt.annotate(short_pipeline(row["pipeline"]), (row["YOLO_activation_rate"], row["FMeasure"]), fontsize=8)
    plt.xlabel("YOLO activation rate (lower is better)")
    plt.ylabel("FMeasure (higher is better)")
    plt.title("Accuracy-efficiency Pareto")
    plt.grid(True, alpha=0.25)
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()

def save_bubble_pareto(df, x_col, y_col, size_col, title, out_path):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    values = df[size_col].astype(float)
    min_v = float(values.min())
    max_v = float(values.max())
    if max_v <= min_v:
        sizes = [220] * len(values)
    else:
        sizes = (120 + 520 * (values - min_v) / (max_v - min_v)).tolist()
    plt.figure(figsize=(8, 6))
    plt.scatter(df[x_col].astype(float), df[y_col].astype(float), s=sizes, alpha=0.72)
    for _, row in df.iterrows():
        plt.annotate(short_pipeline(row["pipeline"]), (row[x_col], row[y_col]), fontsize=8)
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.title(title)
    plt.grid(True, alpha=0.25)
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()

def save_category_pipeline_chart(df, out_path):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    pivot = df.pivot(index="category", columns="pipeline", values="FMeasure")
    pivot = pivot.rename(columns={c: short_pipeline(c) for c in pivot.columns})
    ax = pivot.plot(kind="bar", figsize=(14, 6))
    ax.set_title("FMeasure by Category and Pipeline")
    ax.set_ylabel("FMeasure")
    ax.set_xlabel("Category")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()

def save_category_fmeasure_heatmap(df, out_path):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    pivot = df.pivot(index="category", columns="pipeline", values="FMeasure")
    pivot = pivot.rename(columns={c: short_pipeline(c) for c in pivot.columns})
    plt.figure(figsize=(14, 6))
    plt.imshow(pivot.values.astype(float), aspect="auto", cmap="viridis", vmin=0, vmax=1)
    plt.colorbar(label="FMeasure")
    plt.xticks(range(len(pivot.columns)), pivot.columns, rotation=25, ha="right")
    plt.yticks(range(len(pivot.index)), pivot.index)
    plt.title("Category FMeasure Heatmap")
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()

def create_summary_charts(out_dir):
    out_dir = Path(out_dir)
    charts = out_dir / "charts"
    ev_path = out_dir / "summary_event_metrics.csv"
    px_path = out_dir / "summary_pixel_metrics.csv"
    edge_path = out_dir / "summary_edge_metrics.csv"
    energy_path = out_dir / "summary_edge_energy_metrics.csv"
    pareto_path = out_dir / "summary_pareto_metrics.csv"
    object_path = out_dir / "summary_object_metrics.csv"
    research_path = out_dir / "summary_research_metrics.csv"
    category_path = out_dir / "summary_by_category.csv"
    if ev_path.exists():
        df = pd.read_csv(ev_path)
        dfg = df.groupby("pipeline", as_index=False)["Event_F1"].mean()
        save_bar(dfg, "pipeline", "Event_F1", "Event F1 by Pipeline", charts/"event_f1_by_pipeline.png")
        dfg = df.groupby("pipeline", as_index=False)["MCC"].mean()
        save_bar(dfg, "pipeline", "MCC", "MCC by Pipeline", charts/"mcc_by_pipeline.png")
    if px_path.exists():
        df = pd.read_csv(px_path)
        dfg = df.groupby("pipeline", as_index=False)["FMeasure"].mean()
        save_bar(dfg, "pipeline", "FMeasure", "CDnet F-Measure by Pipeline", charts/"cdnet_fmeasure_by_pipeline.png")
        save_bar(dfg, "pipeline", "FMeasure", "FMeasure by Pipeline", charts/"fmeasure_by_pipeline.png")
    if object_path.exists():
        df = pd.read_csv(object_path)
        if {"pipeline", "mAP_50"}.issubset(df.columns):
            dfg = df.groupby("pipeline", as_index=False)["mAP_50"].mean()
            save_bar(dfg, "pipeline", "mAP_50", "mAP_50 by Pipeline", charts/"map50_by_pipeline.png")
    if edge_path.exists():
        df = pd.read_csv(edge_path)
        dfg = df.groupby("pipeline", as_index=False)["YOLO_activation_rate"].mean()
        save_bar(dfg, "pipeline", "YOLO_activation_rate", "YOLO Activation Rate by Pipeline", charts/"activation_rate_by_pipeline.png")
        save_bar(dfg, "pipeline", "YOLO_activation_rate", "Activation by Pipeline", charts/"activation_by_pipeline.png")
        dfg = df.groupby("pipeline", as_index=False)["P95_latency_ms"].mean()
        save_bar(dfg, "pipeline", "P95_latency_ms", "P95 Latency by Pipeline", charts/"p95_latency_by_pipeline.png")
        dfg = df.groupby("pipeline", as_index=False)["avg_FPS"].mean()
        save_bar(dfg, "pipeline", "avg_FPS", "Avg FPS by Pipeline", charts/"avg_fps_by_pipeline.png")
    if energy_path.exists():
        df = pd.read_csv(energy_path)
        if "aggregation_level" in df.columns:
            dfg = df[df["aggregation_level"] == "pipeline"].copy()
        else:
            dfg = df.groupby("pipeline", as_index=False).mean(numeric_only=True)
        if not dfg.empty and {"pipeline", "Estimated_energy_per_frame"}.issubset(dfg.columns):
            save_bar(
                dfg,
                "pipeline",
                "Estimated_energy_per_frame",
                "Energy per Frame by Pipeline",
                charts/"energy_per_frame_by_pipeline.png",
            )
        reduction_col = "Energy_reduction_rate_vs_P1_YOLO_Only"
        if not dfg.empty and {"pipeline", reduction_col}.issubset(dfg.columns):
            save_bar(
                dfg,
                "pipeline",
                reduction_col,
                "Energy Reduction Rate by Pipeline",
                charts/"energy_reduction_rate_by_pipeline.png",
            )
    if pareto_path.exists():
        df = pd.read_csv(pareto_path)
        if not df.empty:
            save_bubble_pareto(
                df,
                "Activation",
                "FMeasure",
                "Avg_FPS",
                "Pareto 1: Activation vs FMeasure",
                charts/"pareto_1_activation_fmeasure_fps.png",
            )
            save_bubble_pareto(
                df,
                "Activation",
                "FMeasure",
                "Avg_FPS",
                "Pareto: Activation vs FMeasure",
                charts/"pareto_activation_fmeasure.png",
            )
            save_bubble_pareto(
                df,
                "Estimated_energy_per_frame",
                "Event_F1",
                "mAP_50",
                "Pareto 2: Energy vs Event F1",
                charts/"pareto_2_energy_event_f1_map50.png",
            )
            save_bubble_pareto(
                df,
                "Estimated_energy_per_frame",
                "Event_F1",
                "mAP_50",
                "Pareto: Energy vs Event F1",
                charts/"pareto_energy_eventf1.png",
            )
            df = df.copy()
            df["Activation_saving"] = 1.0 - df["Activation"].astype(float)
            save_bubble_pareto(
                df,
                "Avg_FPS",
                "mAP_50",
                "Activation_saving",
                "Pareto 3: Avg FPS vs mAP_50",
                charts/"pareto_3_fps_map50_activation_saving.png",
            )
    if research_path.exists():
        df = pd.read_csv(research_path)
        dfg = df.groupby("pipeline", as_index=False)[["FMeasure", "YOLO_activation_rate"]].mean()
        save_pareto(dfg, charts/"accuracy_efficiency_pareto.png")
        dfg = df.groupby("pipeline", as_index=False)[["FMeasure", "YOLO_activation_rate", "avg_FPS"]].mean()
        save_bubble_pareto(
            dfg,
            "YOLO_activation_rate",
            "FMeasure",
            "avg_FPS",
            "Pareto: Activation vs FMeasure",
            charts/"pareto_activation_fmeasure_bubble.png",
        )
        dfg = df.groupby("pipeline", as_index=False)[["Event_F1", "YOLO_activation_rate", "avg_FPS"]].mean()
        dfg["activation_saving"] = 1.0 - dfg["YOLO_activation_rate"].astype(float)
        save_bubble_pareto(
            dfg,
            "avg_FPS",
            "Event_F1",
            "activation_saving",
            "Pareto: Avg FPS vs Event F1",
            charts/"pareto_fps_event_f1_bubble.png",
        )
    if category_path.exists():
        df = pd.read_csv(category_path)
        if {"category", "pipeline", "FMeasure"}.issubset(df.columns):
            save_category_pipeline_chart(df, charts/"fmeasure_by_category_pipeline.png")
            save_category_fmeasure_heatmap(df, charts/"category_fmeasure_heatmap.png")
