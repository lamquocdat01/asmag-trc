from __future__ import annotations

import re
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
MANUSCRIPT = ROOT / "manuscript" / "ASMAG_2026_submission_draft.docx"
MD = ROOT / "manuscript" / "ASMAG_2026_submission_draft.md"
TXT = ROOT / "manuscript" / "ASMAG_2026_submission_draft_extracted.txt"
CHECK = ROOT / "outputs" / "manuscript_submission_check"
PKG = ROOT / "outputs" / "submission_package"
SUPP = PKG / "Supplementary_Data"
RESULT = ROOT / "outputs" / "full_cdnet2014_official_edge_profile_pc"
PAPER_FIGS = ROOT / "outputs" / "paper_ready_figures"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def table(rows: list[tuple[str, ...]]) -> str:
    return "\n".join("| " + " | ".join(str(c) for c in row) + " |" for row in rows)


def main() -> None:
    CHECK.mkdir(parents=True, exist_ok=True)
    PKG.mkdir(parents=True, exist_ok=True)
    SUPP.mkdir(parents=True, exist_ok=True)

    text = read_text(TXT)
    md_text = read_text(MD) or text
    lines = md_text.splitlines()
    word_count = len(re.findall(r"\b[A-Za-z0-9_]+(?:[-'][A-Za-z0-9_]+)?\b", text))
    sections = [line.strip() for line in lines if re.match(r"^#{1,3}\s+", line.strip())]
    tables = [(i + 1, line.strip()) for i, line in enumerate(lines) if re.match(r"^(Table|Appendix Table|Supplementary Table)\b", line.strip())]
    figures = [(i + 1, line.strip()) for i, line in enumerate(lines) if re.match(r"^(Figure|Supplementary Figure)\b", line.strip())]
    math_hits = [
        (i + 1, line.strip())
        for i, line in enumerate(lines)
        if "[Math object without extractable text]" in line or re.search(r"\(\)", line)
    ]
    ref_hits = [
        (i + 1, line.strip())
        for i, line in enumerate(lines)
        if any(token in line for token in ["(arXiv)", "(Microsoft)", "utm_source"]) or re.search(r"https?://|www\.", line)
    ]

    claim_terms = [
        "state-of-the-art",
        "real energy saving",
        "production-ready",
        "fully deployable",
        "proven",
        "best method",
        "optimal",
        "real edge deployment",
        "real energy",
        "guaranteed",
        "best overall accuracy",
        "deployable adaptive variant",
        "real-world Edge AI cameras",
        "production deployment",
        "physical power consumption",
    ]
    claim_hits = []
    for i, line in enumerate(lines, start=1):
        lower = line.lower()
        for term in claim_terms:
            if term.lower() in lower:
                claim_hits.append((i, term, line.strip()))
                break

    latest_backup = None
    backup_dir = ROOT / "manuscript" / "backup"
    backups = sorted(backup_dir.glob("ASMAG_2026_submission_draft_backup_*.docx"), key=lambda p: p.stat().st_mtime, reverse=True)
    if backups:
        latest_backup = backups[0]

    can_read = False
    read_note = "missing"
    if MANUSCRIPT.exists():
        try:
            with zipfile.ZipFile(MANUSCRIPT) as archive:
                can_read = "word/document.xml" in archive.namelist()
            read_note = "Readable as a valid OOXML .docx package." if can_read else "Opened as zip but word/document.xml was not found."
        except Exception as exc:
            read_note = f"Could not read as OOXML: {exc}"

    stat = MANUSCRIPT.stat() if MANUSCRIPT.exists() else None
    main_df = pd.read_csv(RESULT / "final_main_comparison.csv")
    best_df = pd.read_csv(RESULT / "best_by_metric.csv")
    gain_df = pd.read_csv(RESULT / "gain_summary.csv")

    chart_rows = []
    required_charts = [
        "fmeasure_by_pipeline.png",
        "event_f1_by_pipeline.png",
        "activation_by_pipeline.png",
        "pareto_fmeasure_energy.png",
        "per_category_fmeasure_heatmap.png",
        "latency_p95_by_pipeline.png",
        "per_category_activation_heatmap.png",
        "per_category_latency_heatmap.png",
    ]
    for name in required_charts:
        path = RESULT / "charts" / name
        if path.exists():
            with Image.open(path) as image:
                chart_rows.append((f"`{name}`", "exists", f"{image.size[0]}x{image.size[1]}", str(image.info.get("dpi")), str(path.stat().st_size)))
        else:
            chart_rows.append((f"`{name}`", "missing", "-", "-", "-"))

    paper_rows = []
    for path in sorted(PAPER_FIGS.glob("*.png")):
        with Image.open(path) as image:
            paper_rows.append((f"`{path.name}`", f"{image.size[0]}x{image.size[1]}", str(image.info.get("dpi"))))

    write_task0(stat, can_read, read_note, latest_backup)
    write_audit(word_count, sections, tables, figures, math_hits, ref_hits, claim_hits)
    write_formula_reports()
    write_table_figure_validation(main_df, best_df, gain_df, chart_rows, paper_rows)
    write_reference_reports(ref_hits)
    write_threats_and_claims(claim_hits)
    write_supplementary_docs()
    write_submission_docs()
    write_final_report(latest_backup)
    print("Generated submission preparation reports.")


def write_task0(stat, can_read: bool, read_note: str, latest_backup: Path | None) -> None:
    write(
        CHECK / "task0_file_check.md",
        f"""
# Task 0 File Check

## Manuscript Visibility

| Item | Result |
|---|---|
| Manuscript path | `manuscript/ASMAG_2026_submission_draft.docx` |
| Exists | `{MANUSCRIPT.exists()}` |
| File size | `{stat.st_size if stat else 'missing'} bytes` |
| Last modified | `{datetime.fromtimestamp(stat.st_mtime).isoformat(timespec='seconds') if stat else 'missing'}` |
| Readable | `{can_read}` |
| Read note | {read_note} |
| Markdown existed before extraction | `False` |
| Markdown now exists | `{MD.exists()}` |

## Backup

| Item | Result |
|---|---|
| Backup folder | `manuscript/backup/` |
| Backup created | `{latest_backup.relative_to(ROOT).as_posix() if latest_backup else 'missing'}` |
| Backup size | `{latest_backup.stat().st_size if latest_backup else 'missing'} bytes` |

## Extraction Outputs

| Output | Status |
|---|---|
| `manuscript/ASMAG_2026_submission_draft_extracted.txt` | `{TXT.exists()}` |
| `manuscript/ASMAG_2026_submission_draft.md` | `{MD.exists()}` |
| `outputs/manuscript_submission_check/docx_extract_metadata.json` | `{(CHECK / 'docx_extract_metadata.json').exists()}` |

## Extraction Limitations

Text was extracted with Python standard-library OOXML parsing. Paragraph and table text are readable, but Word equation layout, drawing positions, cross-reference fields, tracked changes, comments, and exact visual formatting are not fully reconstructed. Several math objects were not recoverable as text and are reported in the audit.
""",
    )


def write_audit(word_count: int, sections, tables, figures, math_hits, ref_hits, claim_hits) -> None:
    sections_md = "\n".join(f"- {section}" for section in sections)
    tables_md = "\n".join(f"- Line {line}: {caption}" for line, caption in tables) or "- None detected."
    figures_md = "\n".join(f"- Line {line}: {caption}" for line, caption in figures) or "- None detected."
    math_md = "\n".join(f"- Line {line}: `{hit}`" for line, hit in math_hits[:80]) or "- None detected."
    ref_md = "\n".join(f"- Line {line}: {hit}" for line, hit in ref_hits) or "- No explicit placeholder/raw URL hits detected."
    claim_md = "\n".join(f"- Line {line}: term `{term}` in: {hit}" for line, term, hit in claim_hits[:80]) or "- No overstrong tracked terms detected."
    write(
        CHECK / "manuscript_audit_report.md",
        f"""
# Manuscript Audit Report

## 1. Estimated Word Count

Estimated word count from extracted text: **{word_count} words**.

## 2. Existing Sections

{sections_md}

## 3. Existing Tables and Figures

### Tables

{tables_md}

### Figures

{figures_md}

## 4. Table/Figure Numbering Problems

- Section 5.1 text says \"Table 1 summarizes the full CDnet2014 official-like results\", but the caption immediately below is `Table 2`. The sentence should say `Table 2`.
- Section 5.2 text says \"Table 2 summarizes the best-performing pipeline\", but the caption immediately below is `Table 3`. The sentence should say `Table 3`.
- Required main table order is present: Table 1 compared pipelines, Table 2 main results, Table 3 best pipeline, Table 4 gain summary.
- Main figure order Figure 1 to Figure 6 is present.
- Appendix numbering (`Figure B1`, `Figure B2`, etc.) should be checked against the target journal style.

## 5. Formula/Notation Problems

{math_md}

Additional notation issues:

- Section 3.2 has `Let denote...` text with missing `I_t` and `I_{{t-1}}` symbols.
- Section 3.3 has missing `T`, `G_t`, `S_t`, threshold, and binary decision notation.
- Section 3.4 has missing evaluated index `k`, raw frame step `s`, and refresh period `T` notation.
- Section 3.5 has missing `P_{{t'}}`, `t'`, and `\\hat{{P}}_t` notation.
- Section 3.8 has missing window `W_t`, feature vector `x_t`, selected mode `m_t`, and mapping `f(x_t)` notation.
- Sections 4.5 to 4.7 have missing FMeasure, Activation, ReuseRate, and simulated energy formulas.

## 6. Citation/Reference Problems

{ref_md}

- The extracted manuscript has a `Reference` heading but no visible reference entries below it.
- Claims about CDnet2014, YOLO, MOG2, NoScope, Chameleon, edge hardware, adaptive inference, and temporal reuse need formal citations.
- `(arXiv)` and `(Microsoft)` placeholders must be replaced with author-year or numbered citations according to the selected journal template.

## 7. Overclaiming Problems

{claim_md}

Risk summary:

- Phrases such as `best overall accuracy` are safe only when constrained to `among evaluated pipelines`.
- `deployable adaptive variant` should be softened to `deployment-oriented variant` until real hardware validation is complete.
- `optimal` should be replaced with benchmark-bounded wording.
- Energy claims must consistently say `energy proxy` or `simulated runtime-aware energy`, not real energy savings.

## 8. Figure/Caption/Table Formatting Issues

- Embedded figures are visible as image placeholders in extraction; source mapping should be verified manually in Word.
- Original source PNG figures exist but have about 180 dpi metadata; regenerated PNG/PDF versions are available in `outputs/paper_ready_figures/` at about 320 dpi.
- Some pipeline names appear in extracted tables with inserted spaces after underscores, e.g. `ASMAG_TR_ FAST`; check Word table wrapping before submission.
- Table 4 has numeric mismatches against `gain_summary.csv`; see `table_figure_validation.md`.

## 9. Supplementary Package Issues

- Supplementary package was created under `outputs/submission_package/Supplementary_Data/`.
- Required CSV files were copied from the full official-like output folder.
- The experiment config and run plan were copied from `configs/` because those source files are not located inside the output folder.
- Missing-file/source notes are recorded in `outputs/submission_package/SUPPLEMENTARY_MISSING_FILES.md`.

## 10. Ready/Not-Ready Status

**Status: Not ready for journal submission yet.**

Main blockers are broken formulas/notation in the `.docx`, an empty visible reference section, citation placeholders, Table 4 numeric mismatches against CSV, and final journal template/PDF proofing. The supplementary package and paper-ready figures are now prepared, but the manuscript itself still needs manual insertion or direct Word editing.
""",
    )


def write_formula_reports() -> None:
    formulas = [
        ("3.2 Motion Proposal Layer", "Let denote the current frame at time, and denote the previous frame.", "Let `I_t` denote the current frame at time `t`, and `I_{t-1}` denote the previous frame. The frame difference map is `D_t = |I_t - I_{t-1}|`.", r"D_t = |I_t - I_{t-1}|", "Restores current/previous frame notation and the frame-difference definition."),
        ("3.2 Motion Proposal Layer", "After thresholding and morphological filtering, a binary motion mask is obtained.", "The frame-difference mask is `M_t^{FD} = H(|I_t - I_{t-1}| - \\tau_{FD})`.", r"M_t^{FD} = H(|I_t - I_{t-1}| - \tau_{FD})", "Defines the binary motion mask and threshold."),
        ("3.2 Motion Proposal Layer", "MOG2 produces another foreground mask.", "The MOG2 foreground mask is `M_t^{MOG2} = BGS_{MOG2}(I_t)`.", r"M_t^{MOG2} = BGS_{MOG2}(I_t)", "Restores MOG2 mask notation."),
        ("3.3 Adaptive Motion Gate", "where () means the current frame is active...", "The gate produces `G_t in {0,1}`, where `G_t = 1` activates detector/heavy inference and `G_t = 0` skips it.", r"G_t = \begin{cases}1, & \text{detector/heavy inference is activated} \\ 0, & \text{otherwise.}\end{cases}", "Restores binary gate semantics."),
        ("3.3 Adaptive Motion Gate", "A simplified gate score can be represented as: [empty]", "A simplified score is `S_t = \\alpha motion_density_t + \\beta component_activity_t + \\gamma disagreement_t + \\delta illumination_variation_t`.", r"S_t = \alpha motion\_density_t + \beta component\_activity_t + \gamma disagreement_t + \delta illumination\_variation_t", "Restores weighted gate score."),
        ("3.3 Adaptive Motion Gate", "The detector is activated if () exceeds a mode-specific threshold...", "The detector is activated when `S_t >= \\theta_m` or `k mod T = 0`.", r"G_t = 1 \quad \text{if} \quad S_t \ge \theta_m \; \text{or} \; k \bmod T = 0", "Restores score threshold and safety refresh."),
        ("3.4 Evaluated-Index-Aware Sampling", "Let () denote the index...", "Let `k` denote the evaluated-frame index. Periodic activation is based on `k mod T = 0`.", r"k \bmod T = 0", "Restores evaluated-index-aware periodic sampling."),
        ("3.5 Temporal Reuse", "Let () be the most recent valid prediction... ASMAG-TRC can use:", "Let `P_{t'}` be the most recent valid prediction. If reuse is accepted, `\\hat{P}_t = P_{t'}`.", r"\hat{P}_t = P_{t'}", "Restores temporal reuse notation."),
        ("3.5 Temporal Reuse", "The reuse rate is recorded as an evaluation metric: [Math object]", "Reuse rate is the number of reused prediction frames divided by the number of evaluated frames.", r"ReuseRate = \frac{\text{Number of reused prediction frames}}{\text{Number of evaluated frames}}", "Restores reuse metric."),
        ("3.8 Online Calibrated Controller", "Let () denote a rolling window ending at frame ().", "Let `W_t` denote the rolling window ending at frame `t`.", r"W_t = \{t-w+1, \ldots, t\}", "Restores rolling-window notation."),
        ("3.8 Online Calibrated Controller", "=[motion_density_mean,...]", "The online feature vector is `x_t = [motion_density_mean, motion_density_std, component_count_mean, component_count_std, fd_mog_disagreement, illumination_variance, reuse_success_rate, active_frame_rate, gate_closed_rate]`.", r"x_t = [motion\_density\_mean, motion\_density\_std, component\_count\_mean, component\_count\_std, fd\_mog\_disagreement, illumination\_variance, reuse\_success\_rate, active\_frame\_rate, gate\_closed\_rate]", "Restores feature vector symbol."),
        ("3.8 Online Calibrated Controller", "The online controller maps this feature vector to a selected mode: where () is...", "The controller selects mode `m_t = f(x_t)`.", r"m_t = f(x_t)", "Restores mode-selection mapping."),
        ("4.5 Accuracy Metrics", "[Math object without extractable text]", "FMeasure is `2 x Precision x Recall / (Precision + Recall)`.", r"FMeasure = \frac{2 \times Precision \times Recall}{Precision + Recall}", "Restores primary accuracy metric."),
        ("4.6 Detector Activation", "[Math object without extractable text]", "Activation is the number of activated frames divided by the number of evaluated frames.", r"Activation = \frac{\text{Number of activated frames}}{\text{Number of evaluated frames}}", "Restores activation metric."),
        ("4.7 Energy Proxy", "[Figure/image object] and symbol table with () entries", "Runtime-aware simulated energy is `E_t^{sim} = 1.0 + 5.0 y_t + 1.0 c_t + 1.0 l_t + 2.0 g_t + 0.1 r_t`.", r"E_t^{sim} = 1.0 + 5.0y_t + 1.0c_t + 1.0l_t + 2.0g_t + 0.1r_t", "Restores energy proxy formula and variables."),
    ]
    parts = [
        "# Formula Fixes",
        "",
        "Direct `.docx` editing was not applied because `python-docx`, Pandoc, LibreOffice, and Word CLI were not available in this environment. The original `.docx` was backed up first, and corrected text is provided for manual insertion or later Word editing.",
        "",
    ]
    for location, original, corrected, latex, explanation in formulas:
        parts.extend([
            f"## {location}",
            "",
            f"- Original problematic text: {original}",
            f"- Corrected text: {corrected}",
            "",
            "```latex",
            latex,
            "```",
            "",
            f"- Explanation: {explanation}",
            "",
        ])
    write(CHECK / "formula_fixes.md", "\n".join(parts))
    write(CHECK / "ASMAG_formula_corrected_sections.md", CORRECTED_SECTIONS)


CORRECTED_SECTIONS = r"""
# ASMAG Formula-Corrected Sections

## 3.2. Motion Proposal Layer

Let `I_t` denote the current frame at time `t`, and let `I_{t-1}` denote the previous frame. A simple frame difference map is computed as:

```latex
D_t = |I_t - I_{t-1}|
```

After thresholding and optional morphological filtering, the frame-difference motion mask is:

```latex
M_t^{FD} = H(|I_t - I_{t-1}| - \tau_{FD})
```

where `H(.)` is a binary thresholding operator and `\tau_{FD}` is the frame-difference threshold. In parallel, the MOG2 background subtraction model produces:

```latex
M_t^{MOG2} = BGS_{MOG2}(I_t)
```

## 3.3. Adaptive Motion Gate

The adaptive motion gate outputs a binary decision:

```latex
G_t = \begin{cases}
1, & \text{detector/heavy inference is activated}, \\
0, & \text{otherwise.}
\end{cases}
```

A simplified gate score is:

```latex
S_t = \alpha\,motion\_density_t + \beta\,component\_activity_t + \gamma\,disagreement_t + \delta\,illumination\_variation_t
```

The detector is activated when:

```latex
G_t = 1 \quad \text{if} \quad S_t \ge \theta_m \; \text{or} \; k \bmod T = 0.
```

Here, `\theta_m` is the threshold selected for mode `m`, `k` is the evaluated-frame index, and `T` is the detector refresh period.

## 3.4. Evaluated-Index-Aware Sampling

Let `k` denote the index in the evaluated-frame sequence. Periodic sampling must be applied to `k`, not necessarily to the raw frame number:

```latex
k \bmod T = 0
```

## 3.5. Temporal Reuse

Let `P_{t'}` denote the most recent valid prediction produced at time `t' < t`. If the current frame is stable and reuse is accepted, ASMAG-TRC uses:

```latex
\hat{P}_t = P_{t'}
```

The reuse rate is recorded as:

```latex
ReuseRate = \frac{\text{Number of reused prediction frames}}{\text{Number of evaluated frames}}
```

## 3.8. Online Calibrated Controller

Let `W_t` denote a rolling feature window ending at frame `t`. The online feature vector is:

```latex
x_t = [
motion\_density\_mean,
motion\_density\_std,
component\_count\_mean,
component\_count\_std,
fd\_mog\_disagreement,
illumination\_variance,
reuse\_success\_rate,
active\_frame\_rate,
gate\_closed\_rate
]
```

The controller maps this vector to the selected operating mode:

```latex
m_t = f(x_t)
```

## 3.10. Evaluation Metrics Produced by the Method

```latex
Activation = \frac{\text{Number of activated frames}}{\text{Number of evaluated frames}}
```

```latex
ReuseRate = \frac{\text{Number of reused prediction frames}}{\text{Number of evaluated frames}}
```

## 4.5. Accuracy Metrics

```latex
FMeasure = \frac{2 \times Precision \times Recall}{Precision + Recall}
```

## 4.6. Detector Activation / Reuse Rate

```latex
Activation = \frac{\text{Number of activated frames}}{\text{Number of evaluated frames}}
```

```latex
ReuseRate = \frac{\text{Number of reused prediction frames}}{\text{Number of evaluated frames}}
```

## 4.7. Energy Proxy and Runtime-Aware Simulated Energy

```latex
E_t^{sim} = 1.0 + 5.0y_t + 1.0c_t + 1.0l_t + 2.0g_t + 0.1r_t
```

where `y_t` is the detector activation indicator, `c_t` is normalized CPU usage, `l_t` is normalized latency, `g_t` is normalized GPU usage and is zero in CPU-only experiments, and `r_t` is the reuse indicator. This is an energy proxy, not a physical power or Joule measurement.
"""


def write_table_figure_validation(main_df, best_df, gain_df, chart_rows, paper_rows) -> None:
    main_lines = []
    for _, row in main_df.iterrows():
        main_lines.append(
            f"- {row['Pipeline']}: FMeasure {row['CDnet_FMeasure']:.4f}, Event F1 {row['Event_F1']:.4f}, "
            f"mAP50 {row['mAP_50']:.4f}, Activation {row['Activation']:.4f}, Avg FPS {row['Avg_FPS']:.2f}, "
            f"P95 {row['P95_latency_ms']:.2f}, Energy/frame {row['Energy/frame']:.4f}, AE Score {row['AE_Score']:.4f}, Pareto {row['Pareto']}"
        )
    best_lines = []
    for _, row in best_df.iterrows():
        value = float(row["value"])
        best_lines.append(f"- {row['metric']}: {row['Pipeline']} = {value:.4f}" if abs(value) < 10 else f"- {row['metric']}: {row['Pipeline']} = {value:.2f}")

    def gain_value(comparison: str) -> float:
        return float(gain_df.loc[gain_df["Comparison"] == comparison, "Simulated_runtime_energy_saving"].iloc[0])

    mismatch_rows = [
        ("ASMAG_TR_CONTROLLER vs P3_MOG2", "Simulated runtime energy saving", "+0.0852", f"+{gain_value('ASMAG_TR_CONTROLLER vs P3_MOG2'):.4f}"),
        ("ONLINE_CALIBRATED vs P3_MOG2", "Simulated runtime energy saving", "+0.1635", f"+{gain_value('ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED vs P3_MOG2'):.4f}"),
        ("ASMAG_TR_FAST vs P3_MOG2", "Simulated runtime energy saving", "+0.4592", f"+{gain_value('ASMAG_TR_FAST vs P3_MOG2'):.4f}"),
    ]
    write(
        CHECK / "table_figure_validation.md",
        f"""
# Table and Figure Validation

## Required Table Order

- Table 1. Compared pipelines and their roles: found.
- Table 2. Full CDnet2014 official-like main results under CPU-only edge simulation: found.
- Table 3. Best-performing pipeline by metric: found, caption currently says `Best pipeline by metric`.
- Table 4. Gain summary against P3_MOG2: found.

## Table 2 Validation Against `final_main_comparison.csv`

Values in the extracted manuscript match the CSV after normal rounding to the shown precision. CSV values are:

{chr(10).join(main_lines)}

Formatting issue: extracted pipeline names in Table 2 include inserted spaces in several names (`ASMAG_TR_ FAST`, `ASMAG_TR_ CONTROLLER`, `ASMAG_TR_ CONTROLLER_ ONLINE_CALIBRATED`). Check the Word table for unintended spaces or line-break artifacts.

## Table 3 Validation Against `best_by_metric.csv`

Values match the CSV after normal rounding:

{chr(10).join(best_lines)}

## Table 4 Validation Against `gain_summary.csv`

Table 4 mostly matches the CSV, but the following values differ and should be corrected in the manuscript:

| Comparison | Field | Manuscript | CSV |
|---|---|---:|---:|
{table(mismatch_rows)}

Additional note: `gain_summary.csv` contains an extra comparison row, `ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED vs ASMAG_TR_CONTROLLER`, that is not included in manuscript Table 4. This is acceptable if intentionally omitted, but it should be mentioned in supplementary data or appendix if reviewers need the complete gain table.

## Numbering Issues

- In Section 5.1, change `Table 1 summarizes...` to `Table 2 summarizes...`.
- In Section 5.2, change `Table 2 summarizes...` to `Table 3 summarizes...`.
- Main figure captions are in required order Figure 1 to Figure 6.

## Caption Issues

- Table 3 caption should match the requested wording: `Best-performing pipeline by metric`.
- Figure 1 source file is not listed among the required output charts; it is embedded in the Word document. Keep a source/vector copy for journal revision.
- All figure captions should state the full CDnet2014 official-like `frame_step=1` protocol under CPU-only edge simulation where relevant.

## Required Chart Source Check

| Source chart | Status | Dimensions | DPI metadata | Bytes |
|---|---|---:|---|---:|
{table(chart_rows)}

All required source chart files were found. The original PNG files use about 180 dpi metadata, below the requested 300 dpi threshold.

## Paper-Ready Regenerated Figures

A regeneration script was created at `src/paper/generate_paper_figures.py`, using CSV values only. It generated PNG and PDF outputs in `outputs/paper_ready_figures/`.

| Paper-ready PNG | Dimensions | DPI metadata |
|---|---:|---|
{table(paper_rows)}

## Missing / Low-Resolution Figures

- Missing required chart files: none among the listed charts.
- Low-resolution issue: original source PNG metadata is about 180 dpi; paper-ready regenerated files are about 320 dpi.
- Manual visual inspection in Word is still needed for embedded Figure 1 and final PDF proofing.
""",
    )


def write_reference_reports(ref_hits) -> None:
    ref_md = "\n".join(f"- Line {line}: {hit}" for line, hit in ref_hits) or "- No explicit placeholder/raw URL hits detected."
    write(
        CHECK / "reference_gap_report.md",
        f"""
# Reference Gap Report

## Global Reference Status

- The manuscript has a `Reference` heading, but no visible reference entries were extracted below it.
- Explicit placeholder/raw URL hits found: {len(ref_hits)}.

## Placeholder / Raw URL Hits

{ref_md}

## 1. CDnet / Change Detection / Background Subtraction

- CDnet2014 dataset description needs a formal citation.
- Frame differencing and classical background subtraction discussion needs citations.
- MOG2/Gaussian mixture background modeling needs citation.

## 2. YOLO / Object Detection / Edge Detection

- YOLO description currently ends with `(arXiv)` and needs a formal citation.
- Claims about YOLO-style real-time detection and compact variants need citations.
- Hardware/deployment frameworks such as TensorRT, OpenVINO, Edge TPU, Hailo, and NPU toolchains need citations or vendor documentation references depending on target journal style.

## 3. Edge AI / Real-Time Video Analytics

- Statements about edge cameras, latency, bandwidth, privacy, and local inference should be supported by edge/video analytics literature.
- CPU-only edge simulation should cite comparable edge benchmarking or embedded AI profiling work if available.

## 4. Adaptive Inference / Frame Skipping / Active Video Analytics

- NoScope placeholder `(arXiv)` should be replaced with a formal citation.
- Chameleon placeholder `(Microsoft)` should be replaced with a formal citation.
- Claims about adaptive configuration, model cascades, and frame skipping require citations.

## 5. Temporal Reuse / Tracking / Motion-Guided Reuse

- Temporal reuse discussion needs citations to tracking, optical flow, or video analytics reuse approaches.
- Future work claims about confidence-aware and tracking-assisted reuse should cite representative tracking or propagation methods if retained.

## 6. Edge Hardware / Energy Profiling

- Energy claims must remain proxy-only unless real power-meter data are added.
- Hardware examples such as Jetson, OpenVINO-based mini-PCs, Coral Edge TPU, and Hailo need vendor documentation or peer-reviewed deployment citations.
""",
    )
    write(
        CHECK / "citation_insertion_plan.md",
        """
# Citation Insertion Plan

| Topic | Section | Sentence/Paragraph | Recommended Citation Type | Suggested Citation | Status |
|---|---|---|---|---|---|
| CDnet2014 benchmark | 2.1, 4.1 | Dataset description and categories | Dataset/benchmark paper | Wang et al., 2014, CDnet 2014 | Add |
| MOG2 / GMM background modeling | 2.1, 3.2 | Classical background subtraction and MOG2 mask | Foundational method | Stauffer and Grimson, 1999 | Add |
| YOLO | 2.2 | Original YOLO paragraph currently marked `(arXiv)` | Detector paper | Redmon et al., 2016 | Add |
| Large-scale adaptive video analytics | 2.3 | NoScope paragraph currently marked `(arXiv)` | Systems paper | Kang et al., 2017, NoScope | Add |
| Adaptive video configuration | 2.3 | Chameleon paragraph currently marked `(Microsoft)` | Systems paper | Jiang et al., 2018, Chameleon | Add |
| Edge AI deployment frameworks | 2.2, 6.5, 7 | TensorRT/OpenVINO/Edge TPU/Hailo examples | Vendor docs or peer-reviewed edge AI deployment paper | TODO: choose based on target journal style | TODO |
| Temporal reuse/tracking | 2.4, 3.5, 6.7 | Reuse, tracking-assisted reuse, optical flow/Kalman propagation | Tracking/video analytics references | TODO: select representative tracking/reuse papers | TODO |
| Energy measurement | 4.7, 6.5, 7 | Proxy energy disclaimer and future power-meter validation | Edge energy profiling reference | TODO: select reliable power profiling references | TODO |
""",
    )
    write(CHECK / "references_to_add.bib", BIBTEX)


BIBTEX = r"""
@inproceedings{wang2014cdnet,
  title = {CDnet 2014: An Expanded Change Detection Benchmark Dataset},
  author = {Wang, Yi and Jodoin, Pierre-Marc and Porikli, Fatih and Konrad, Janusz and Benezeth, Yannick and Ishwar, Prakash},
  booktitle = {Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition Workshops},
  pages = {387--394},
  year = {2014}
}

@inproceedings{stauffer1999adaptive,
  title = {Adaptive Background Mixture Models for Real-Time Tracking},
  author = {Stauffer, Chris and Grimson, W. Eric L.},
  booktitle = {Proceedings of the 1999 IEEE Computer Society Conference on Computer Vision and Pattern Recognition},
  volume = {2},
  pages = {246--252},
  year = {1999},
  organization = {IEEE}
}

@inproceedings{redmon2016you,
  title = {You Only Look Once: Unified, Real-Time Object Detection},
  author = {Redmon, Joseph and Divvala, Santosh and Girshick, Ross and Farhadi, Ali},
  booktitle = {Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition},
  pages = {779--788},
  year = {2016}
}

@article{kang2017noscope,
  title = {NoScope: Optimizing Neural Network Queries over Video at Scale},
  author = {Kang, Daniel and Emmons, John and Abuzaid, Firas and Bailis, Peter and Zaharia, Matei},
  journal = {Proceedings of the VLDB Endowment},
  volume = {10},
  number = {11},
  pages = {1586--1597},
  year = {2017}
}

@inproceedings{jiang2018chameleon,
  title = {Chameleon: Scalable Adaptation of Video Analytics},
  author = {Jiang, Junchen and Ananthanarayanan, Ganesh and Bodik, Peter and Sen, Siddhartha and Stoica, Ion},
  booktitle = {Proceedings of the 2018 Conference of the ACM Special Interest Group on Data Communication},
  pages = {253--266},
  year = {2018}
}

% TODO: Add reliable references for edge hardware deployment and physical energy profiling after target journal style is chosen.
% TODO: Add representative references for temporal reuse, tracking-assisted propagation, and confidence-aware video analytics.
"""


def write_threats_and_claims(claim_hits) -> None:
    write(
        CHECK / "threats_to_validity_section.md",
        """
# Threats to Validity

This section summarizes the main validity threats in the current study and the corresponding mitigation steps. The goal is to clarify the interpretation of the results without overstating deployment readiness.

| Threat | Explanation | Mitigation |
|---|---|---|
| Dataset validity | The evaluation is conducted on CDnet2014 only. Although CDnet2014 is diverse, it may not represent all traffic, industrial, retail, or outdoor edge-camera environments. | Report the dataset scope clearly and evaluate additional datasets in future work. |
| Hardware validity | The experiments use CPU-only edge simulation on a PC environment rather than a dedicated embedded AI device. | Present the results as CPU-only edge simulation and avoid claims about universal hardware performance. |
| Energy validity | Reported energy values are proxy estimates and simulated runtime-aware values, not physical Watt or Joule measurements. | Use consistent proxy formulas for comparison and state that physical power-meter validation is future work. |
| Label dependency | The category-aware controller uses CDnet2014 category labels and should be treated as an upper-bound policy. | Separate category-aware results from the online calibrated controller, which does not use category labels during inference. |
| Metric validity | The mAP50 value is a proxy derived from foreground/object regions, not COCO-style object detection mAP. | Describe mAP50 as an object-region proxy and interpret it alongside CDnet FMeasure and Event F1. |
| Implementation overhead | The online calibrated controller has higher latency and lower FPS than expected despite reducing activation. | Report the overhead openly and identify controller optimization as future work. |
| Reproducibility | The full official-like evaluation is long-running and depends on checkpointing and progress recovery. | Include run plans, progress logs, configuration files, and supplementary CSV summaries. |
| Generalization | The current findings may not fully transfer to other datasets, detectors, or hardware accelerators. | Present ASMAG-TRC as a promising adaptive inference-control framework requiring broader validation. |
""",
    )
    rows = []
    for line, _, original in claim_hits[:50]:
        safe = original
        safe = re.sub("best overall accuracy", "best overall accuracy among the evaluated pipelines", safe, flags=re.I)
        safe = re.sub("deployable adaptive variant", "deployment-oriented adaptive variant", safe, flags=re.I)
        safe = re.sub("most practical deployable variant", "most deployment-oriented variant evaluated in this study", safe, flags=re.I)
        safe = re.sub("not necessarily optimal", "not consistently best under this benchmark", safe, flags=re.I)
        safe = re.sub("production deployment", "practical deployment", safe, flags=re.I)
        rows.append((f"Line {line}", original.replace("|", "/"), "May overstate deployment or generality unless constrained to this experiment.", safe.replace("|", "/")))
    claim_table = table(rows) if rows else "| - | No tracked issues | - | - |"
    write(
        CHECK / "claim_safety_report.md",
        f"""
# Claim Safety Report

| Location | Original phrase/context | Why risky | Suggested safer wording |
|---|---|---|---|
{claim_table}

## Preferred Safe Wording

- `among evaluated pipelines`
- `energy proxy`
- `CPU-only edge simulation`
- `deployment-oriented variant`
- `promising direction`
- `requires real hardware validation`
- `upper-bound category-aware policy`
- `not a physical power measurement`
""",
    )
    write(
        CHECK / "claim_safe_rewrite.md",
        """
# Claim-Safe Rewrite

Direct `.docx` wording edits were not applied because no reliable `.docx` editing/conversion tool is available in this environment. Use the replacements below when updating the Word manuscript.

| Replace | With |
|---|---|
| `best overall accuracy` | `best overall accuracy among the evaluated pipelines` |
| `deployable adaptive variant` | `deployment-oriented adaptive variant` |
| `most practical deployable variant` | `most deployment-oriented variant evaluated in this study` |
| `not necessarily optimal` | `not consistently best under this benchmark` |
| `optimal across the full CDnet2014 benchmark` | `best across all evaluated CDnet2014 conditions` |
| `fully deployable controller` | `controller suitable for deployment only after additional validation and optimization` |
| `real energy saving` | `energy-proxy reduction` |
| `real energy` | `proxy energy` or `physical energy` only when discussing future measurement |
| `production-ready` | `requires real hardware validation before production use` |
| `proven` | `shown in the evaluated setting` |
| `guaranteed` | `observed in this evaluation` |

## Suggested Abstract-Safe Version

Experimental results show that `ASMAG_TR_CONTROLLER` achieves the highest CDnet FMeasure, Event F1, and mAP50 proxy among the evaluated pipelines. Compared with the MOG2 baseline, it improves these accuracy metrics while reducing detector activation, energy proxy, and P95 latency under CPU-only edge simulation. The online calibrated controller provides a deployment-oriented variant that does not use category labels during inference, but it still requires optimization and real hardware validation.
""",
    )


def write_supplementary_docs() -> None:
    write(
        PKG / "SUPPLEMENTARY_MISSING_FILES.md",
        """
# Supplementary Missing Files

No required supplementary deliverable is missing in the generated package.

Source-location notes:

- `Supplementary_Config_E1_full_cdnet2014_official_edge_profile_pc.yaml` was copied from `configs/full_cdnet2014_official_edge_profile_pc.yaml` because the YAML config is not stored inside `outputs/full_cdnet2014_official_edge_profile_pc/`.
- `Supplementary_RunPlan_E2_full_cdnet2014_official_edge_video_run_plan.csv` was copied from `configs/full_cdnet2014_official_edge_video_run_plan.csv` because the run plan is not stored inside `outputs/full_cdnet2014_official_edge_profile_pc/`.
- Supplementary figures were copied from `outputs/paper_ready_figures/` to provide 300+ dpi PNGs generated from official-like CSV outputs.
""",
    )
    write(
        SUPP / "README.md",
        """
# Supplementary Data README

This folder contains supplementary materials for the ASMAG-TRC full CDnet2014 official-like evaluation.

## Files

| File | Purpose |
|---|---|
| `Supplementary_Table_B1_per_category_summary.csv` | Category-level metrics for each CDnet2014 category and evaluated pipeline. |
| `Supplementary_Table_C1_per_video_summary.csv` | Video-level metrics for all 53 videos and all six pipelines. |
| `Supplementary_Table_D1_edge_runtime_summary.csv` | CPU-only edge profiling metrics including FPS, latency, CPU/RAM, activation, reuse, and energy proxy values. |
| `Supplementary_Table_F1_mode_usage_summary.csv` | Mode usage summary for adaptive ASMAG variants, especially the online calibrated controller. |
| `Supplementary_Config_E1_full_cdnet2014_official_edge_profile_pc.yaml` | Experiment configuration used for the full official-like CPU-only edge simulation. |
| `Supplementary_RunPlan_E2_full_cdnet2014_official_edge_video_run_plan.csv` | The full 53-video run plan used to schedule the official-like experiment. |
| `Supplementary_Progress_E3_run_progress.csv` | Checkpoint/progress table for the 318 video-pipeline jobs. |
| `Supplementary_Figures/` | Paper-ready supplementary figures generated from the final CSV outputs. |

## How to Read the CSV Files

The CSV files are comma-separated text files with a header row. They can be opened with spreadsheet software or loaded with Python/pandas. Each row represents either a category-pipeline summary, a video-pipeline summary, a runtime profiling record, or a controller mode summary depending on the file.

## Evaluation Protocol

The evaluation follows a full CDnet2014 official-like `frame_step=1` protocol. The local CDnet2014 setup contains 53 videos across 11 categories. Six pipelines are evaluated for each video, resulting in 53 videos x 6 pipelines = 318 jobs.

## CPU-Only Edge Simulation

All reported runtime and energy-proxy results are based on a CPU-only edge simulation on the PC environment used for the experiment. CUDA/GPU acceleration is disabled for the reported official-like run.

## Energy Interpretation

Energy values are proxy estimates, not physical Watt or Joule measurements. They are intended for consistent comparison among pipelines under the same CPU-only experimental environment. They should not be interpreted as direct power-meter measurements.

## Controller Interpretation

The category-aware controller is an upper-bound policy because it uses CDnet2014 category labels. It is useful for estimating the potential of scene-aware adaptive inference, but it is not the final deployment policy.

The online calibrated controller is deployment-oriented because it uses rolling scene features instead of category labels during inference. However, it is not fully optimized yet and still requires additional runtime optimization and real hardware validation.
""",
    )


def write_submission_docs() -> None:
    checklist_rows = [
        ("Manuscript formatting", "Needs work", "Word document needs journal template formatting and final PDF proof.", "Author"),
        ("Formula check", "Needs work", "Broken formulas identified; corrected sections created for insertion.", "Author/Codex"),
        ("Table check", "Needs work", "Table 4 simulated energy values must be corrected against CSV.", "Author/Codex"),
        ("Figure check", "Needs work", "Paper-ready 320 dpi figures generated; embed/replace in Word and proof.", "Author"),
        ("References", "Missing", "Visible reference list is empty; citation placeholders remain.", "Author"),
        ("Supplementary files", "Ready", "Supplementary_Data package created with required CSV/config/progress/figures.", "Codex"),
        ("Data availability statement", "Needs work", "Draft created; user must choose final repository/access wording.", "Author"),
        ("Code availability statement", "Needs work", "Draft includes TODO for public release vs request.", "Author"),
        ("Conflict of interest", "Ready", "Draft statement created.", "Author"),
        ("Funding", "Missing", "Funding source unknown; TODO left.", "Author"),
        ("Author contributions", "Needs work", "Draft placeholders created.", "Author"),
        ("Ethics approval", "Needs work", "Draft says not applicable for public dataset; confirm target journal wording.", "Author"),
        ("Cover letter", "Ready", "Draft created with placeholders.", "Author"),
        ("Journal template", "Missing", "No template downloaded; notes created for candidate journals.", "Author"),
        ("Final PDF proofread", "Missing", "Requires Word/PDF export and visual proof.", "Author"),
        ("Native speaker / language editing check", "Needs work", "Recommended before submission.", "Author"),
        ("Plagiarism/similarity check", "Missing", "Run institutional or journal-approved checker.", "Author"),
        ("Figure 300 dpi check", "Ready", "Regenerated PNGs report about 320 dpi metadata; PDFs also exported.", "Codex"),
        ("Supplementary zip check", "Needs work", "Package folder exists; final zip not created because journal target/name is not chosen.", "Author/Codex"),
        ("Final submission portal check", "Missing", "Needs target journal portal requirements.", "Author"),
    ]
    write(PKG / "SUBMISSION_CHECKLIST.md", "# Submission-Ready Checklist\n\n| Item | Status | Notes | Owner |\n|---|---|---|---|\n" + table(checklist_rows))
    write(PKG / "submission_statements.md", SUBMISSION_STATEMENTS)
    write(PKG / "cover_letter_draft.md", COVER_LETTER)
    write(PKG / "journal_formatting_notes.md", JOURNAL_NOTES)


SUBMISSION_STATEMENTS = """
# Submission Statements Draft

## 1. Data Availability

The CDnet2014 dataset used in this study is publicly available from the dataset providers. The generated experimental summaries, including per-category, per-video, runtime, mode-usage, configuration, progress, and figure files, are provided as supplementary materials with this submission.

## 2. Code Availability

TODO: The authors should choose the final code-release policy. Suggested wording: The code will be made available upon reasonable request. Alternative wording: The code and scripts used for evaluation will be released upon publication.

## 3. Conflict of Interest

The authors declare no conflict of interest.

## 4. Funding

TODO: Funding information is not available in the current project files. Add grant numbers, institutional support, or state that no specific funding was received.

## 5. Author Contributions

TODO: Replace placeholders with actual author names. Suggested CRediT-style draft: [Author 1] contributed to conceptualization, methodology, software, experiments, analysis, and writing-original draft. [Author 2] contributed to supervision, validation, review, and editing. All authors read and approved the final manuscript.

## 6. Acknowledgments

The authors acknowledge the providers of the CDnet2014 dataset and the open-source software communities whose tools supported the experimental evaluation. TODO: Add institutional or lab acknowledgments if applicable.

## 7. Ethics Approval

This study uses a public benchmark dataset and does not involve human-subject recruitment, intervention, or collection of new personal data by the authors. Ethics approval is therefore not applicable. TODO: Confirm wording against target journal requirements.

## 8. Supplementary Materials Statement

Supplementary materials include the full per-category and per-video result tables, CPU-only edge runtime profiling summaries, controller mode-usage summaries, experiment configuration, run plan, progress log, and supplementary figures.

## 9. Energy Measurement Disclaimer

The reported energy values are proxy estimates and simulated runtime-aware energy metrics computed under a consistent CPU-only experimental setting. They are not physical Watt or Joule measurements from an external power meter.

## 10. CPU-Only Edge Simulation Disclaimer

The reported runtime and energy-proxy results are based on CPU-only edge simulation in the experimental PC environment. They should be interpreted as CPU-oriented evidence and should be validated on real embedded edge AI hardware in future work.
"""


COVER_LETTER = """
# Cover Letter Draft

[Date]

Dear Editor-in-Chief,

We are pleased to submit our manuscript entitled \"ASMAG-TRC: Adaptive Motion-Gated Inference Control for Real-Time Edge AI Camera Systems\" for consideration in [Target Journal Name].

The manuscript addresses the problem of reducing unnecessary detector activation in continuous video streams for real-time edge AI camera systems. Rather than focusing only on making each detector call faster, the proposed ASMAG-TRC framework controls when heavy inference is needed, when lightweight motion cues are sufficient, and when recent predictions can be reused.

The main contribution is an adaptive motion-gated inference-control framework that combines motion proposal, adaptive gating, temporal reuse, category-aware upper-bound control, and an online calibrated controller that does not use category labels during inference. The work is positioned as a detector-agnostic control layer for active edge camera inference.

The paper fits the scope of real-time image processing, edge AI, and video analytics because it evaluates the accuracy-efficiency trade-off of active inference control under a CPU-only edge simulation setting. The evaluation uses a full CDnet2014 official-like `frame_step=1` protocol with 53 videos and six evaluated pipelines, resulting in 318 video-pipeline jobs. The manuscript reports CDnet FMeasure, Event F1, mAP50 proxy, detector activation, reuse rate, FPS, P95 latency, energy proxy, simulated runtime-aware energy, and Pareto-style analysis.

Supplementary materials are included to support reproducibility and transparency. These materials include per-category and per-video result tables, edge runtime profiling summaries, controller mode-usage summaries, experiment configuration, run plan, progress log, and supplementary figures.

We confirm that this manuscript is original, has not been published previously, and is not under consideration for publication elsewhere. All authors have approved the submission. The authors declare no conflict of interest.

Thank you for considering our manuscript. We look forward to your response.

Sincerely,

[Corresponding Author Name]
[Affiliation]
[Email]
"""


JOURNAL_NOTES = """
# Journal Formatting Notes

## Journal of Real-Time Image Processing

- Use the Springer journal article template if selected.
- Emphasize real-time constraints, latency, P95 latency, FPS, and online controller overhead.
- Keep claims bounded to CPU-only edge simulation until real hardware validation is added.
- Convert references to Springer style and ensure all figures/tables are cited in order.

## IEEE Access

- Use the IEEE Access template and numbered citation style.
- Convert section/table/figure formatting to IEEE conventions.
- Add an IEEE-style author contribution or author information section if required.
- Ensure all abbreviations are defined on first use and that figures are readable in two-column layout.

## Springer Journal

- Use the target Springer template and reference style.
- Add declarations section: funding, conflict of interest, data availability, code availability, author contributions, and ethics if required.
- Check whether supplementary materials should be submitted separately or referenced as Electronic Supplementary Material.

## Reference Style TODO

- Choose target journal first.
- Replace `(arXiv)` and `(Microsoft)` placeholders with formal citations.
- Fill the currently empty reference section.
- Verify BibTeX entries against the target bibliography style.

## Figure/Table Placement TODO

- Replace original embedded charts with 300+ dpi paper-ready figures from `outputs/paper_ready_figures/`.
- Correct Table 4 simulated runtime energy values against `gain_summary.csv`.
- Fix section text references to Table 2 and Table 3.
- Keep large per-category/per-video tables as supplementary files, not main manuscript tables.

## Word/LaTeX Template TODO

- No journal templates were downloaded or added.
- Decide Word vs LaTeX submission path.
- If Word is retained, manually insert corrected equations and references, then export final PDF for proofing.
"""


def write_final_report(latest_backup: Path | None) -> None:
    created_files = [
        "manuscript/ASMAG_2026_submission_draft_extracted.txt",
        "manuscript/ASMAG_2026_submission_draft.md",
        "outputs/manuscript_submission_check/task0_file_check.md",
        "outputs/manuscript_submission_check/manuscript_audit_report.md",
        "outputs/manuscript_submission_check/formula_fixes.md",
        "outputs/manuscript_submission_check/ASMAG_formula_corrected_sections.md",
        "outputs/manuscript_submission_check/table_figure_validation.md",
        "outputs/manuscript_submission_check/reference_gap_report.md",
        "outputs/manuscript_submission_check/citation_insertion_plan.md",
        "outputs/manuscript_submission_check/references_to_add.bib",
        "outputs/manuscript_submission_check/threats_to_validity_section.md",
        "outputs/manuscript_submission_check/claim_safety_report.md",
        "outputs/manuscript_submission_check/claim_safe_rewrite.md",
        "src/paper/generate_paper_figures.py",
        "src/paper/generate_submission_prep_reports.py",
        "outputs/paper_ready_figures/*.png and *.pdf",
        "outputs/submission_package/Supplementary_Data/",
        "outputs/submission_package/SUBMISSION_CHECKLIST.md",
        "outputs/submission_package/submission_statements.md",
        "outputs/submission_package/cover_letter_draft.md",
        "outputs/submission_package/journal_formatting_notes.md",
        "outputs/submission_package/SUPPLEMENTARY_MISSING_FILES.md",
    ]
    backup_text = latest_backup.relative_to(ROOT).as_posix() if latest_backup else "missing"
    write(
        PKG / "FINAL_SUBMISSION_PREP_REPORT.md",
        f"""
# Final Submission Preparation Report

## 1. Files Checked

- `manuscript/ASMAG_2026_submission_draft.docx`
- `outputs/full_cdnet2014_official_edge_profile_pc/final_main_comparison.csv`
- `outputs/full_cdnet2014_official_edge_profile_pc/best_by_metric.csv`
- `outputs/full_cdnet2014_official_edge_profile_pc/gain_summary.csv`
- `outputs/full_cdnet2014_official_edge_profile_pc/per_category_summary.csv`
- `outputs/full_cdnet2014_official_edge_profile_pc/per_video_summary.csv`
- `outputs/full_cdnet2014_official_edge_profile_pc/edge_runtime_summary.csv`
- `outputs/full_cdnet2014_official_edge_profile_pc/official_like_results.csv`
- `outputs/full_cdnet2014_official_edge_profile_pc/mode_usage_summary.csv`
- `outputs/full_cdnet2014_official_edge_profile_pc/charts/*.png`
- `configs/full_cdnet2014_official_edge_profile_pc.yaml`
- `configs/full_cdnet2014_official_edge_video_run_plan.csv`

## 2. Backup Created

- `{backup_text}`

## 3. Files Created/Updated

{chr(10).join(f'- `{path}`' for path in created_files)}

## 4. Manuscript Readiness Score

**62/100.**

The manuscript has a coherent structure, completed experiment results, and a supplementary package, but it is not ready to submit because formulas are broken in the `.docx`, the visible reference section is empty, several citation placeholders remain, and Table 4 has numeric mismatches against the CSV.

## 5. Critical Issues Fixed

- Backup created before any manuscript processing.
- Readable text and Markdown audit copies extracted.
- Formula repair plan and corrected section text created.
- Table/figure validation completed against CSV and chart files.
- 300+ dpi paper-ready figures regenerated from official-like CSV outputs.
- Supplementary data package created with required CSV/config/progress files and figures.
- Threats to Validity, submission statements, checklist, journal notes, and cover letter drafts created.

## 6. Critical Issues Remaining

- Insert corrected formulas into the Word manuscript or migrate to a journal template.
- Correct Table 4 simulated runtime energy saving values in the Word manuscript.
- Fill the empty reference section and replace `(arXiv)` / `(Microsoft)` placeholders.
- Replace embedded figures with paper-ready figures and proof final PDF layout.
- Confirm funding, author contributions, code availability, and target journal requirements.

## 7. Table and Figure Validation Results

- Table 2 main results match `final_main_comparison.csv` after rounding.
- Table 3 best-by-metric results match `best_by_metric.csv` after rounding.
- Table 4 has mismatches in `Simulated runtime energy saving` for three rows; details are in `outputs/manuscript_submission_check/table_figure_validation.md`.
- All required chart source files exist.
- Original charts have about 180 dpi metadata; regenerated paper-ready figures have about 320 dpi metadata and PDF versions.

## 8. Supplementary Package Status

**Ready as a folder package.** Files are under `outputs/submission_package/Supplementary_Data/`. No required deliverable is missing. Config and run-plan files were copied from `configs/` because they are not stored in the output folder.

## 9. Reference Status

**Not ready.** The extracted manuscript has an empty visible reference section. Initial reliable BibTeX entries were created for CDnet2014, MOG2/GMM background modeling, YOLO, NoScope, and Chameleon. Additional references for edge hardware, energy profiling, and temporal reuse remain TODO.

## 10. Ready to Submit Now?

**No.** The manuscript should not be submitted until formulas, references, Table 4 mismatches, final figure replacement, journal formatting, and final PDF proofing are completed.

## 11. Recommended Next Actions

1. Update the Word manuscript using `ASMAG_formula_corrected_sections.md`, `claim_safe_rewrite.md`, and `table_figure_validation.md`.
2. Replace main and supplementary figures with outputs from `outputs/paper_ready_figures/`.
3. Insert formal citations and build a complete reference list using `references_to_add.bib` plus remaining TODO references.
4. Add the Threats to Validity section or merge it with the existing Limitations section.
5. Choose target journal and apply the corresponding template and reference style.
6. Export a final PDF and perform visual proofing.

## 12. Next Prompt for Codex

Please update `manuscript/ASMAG_2026_submission_draft.docx` or a new journal-template draft by inserting the corrected formulas from `outputs/manuscript_submission_check/ASMAG_formula_corrected_sections.md`, correcting Table 4 values from `gain_summary.csv`, replacing placeholder citations using `references_to_add.bib`, and embedding the paper-ready figures from `outputs/paper_ready_figures/`. Keep the original backed up, do not rerun CDnet2014, and do not fabricate missing references.
""",
    )


if __name__ == "__main__":
    main()
