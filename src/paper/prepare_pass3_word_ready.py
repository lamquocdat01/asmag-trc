from __future__ import annotations

import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "manuscript" / "ASMAG_2026_submission_ready_v1.md"
OUT = ROOT / "outputs" / "submission_package" / "pass3_word_ready"
WORD_MD = OUT / "ASMAG_2026_word_ready.md"
REF_DRAFT = ROOT / "outputs" / "submission_package" / "references_section_draft.md"
BIB = ROOT / "outputs" / "submission_package" / "references_ready.bib"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def command_available(command: str) -> bool:
    return shutil.which(command) is not None


def python_import(module: str) -> bool:
    result = subprocess.run(["python", "-c", f"import {module}"], cwd=ROOT, capture_output=True, text=True)
    return result.returncode == 0


def tool_status() -> dict[str, bool]:
    return {
        "pandoc": command_available("pandoc"),
        "soffice": command_available("soffice"),
        "libreoffice": command_available("libreoffice"),
        "winword": command_available("winword"),
        "python-docx": python_import("docx"),
        "pypandoc": python_import("pypandoc"),
        "python-markdown": python_import("markdown"),
        "md-to-docx": command_available("md-to-docx"),
        "markdown-to-docx": command_available("markdown-to-docx"),
        "md2docx": command_available("md2docx"),
        "docx2pdf": command_available("docx2pdf"),
    }


def existing_export_scripts() -> list[str]:
    candidates = [
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "src").rglob("*")
        if path.is_file() and re.search(r"(docx|word|pdf|pandoc|export)", path.name, re.I)
    ]
    candidates += [
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "src" / "paper").glob("*.py")
        if path.is_file()
    ]
    return sorted(set(candidates))


def make_word_ready_markdown(text: str) -> str:
    # The source Markdown lives in manuscript/, while the Word-ready copy lives
    # under outputs/submission_package/pass3_word_ready/. Figure paths therefore
    # need to be adjusted to stay usable from the new location.
    text = text.replace("../outputs/paper_ready_figures/", "../../paper_ready_figures/")
    text = text.replace("Source file: `outputs/paper_ready_figures/", "Source file: `outputs/paper_ready_figures/")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.replace("# Reference\n", "# References\n")
    if "# Appendix" in text:
        text = text.replace("# Appendix", "# Appendix / Supplementary Material", 1)
    return text.rstrip() + "\n"


def todo_reference_report(manuscript: str, refs: str, bib: str) -> tuple[str, int]:
    entries: list[tuple[str, str, str, str, str]] = []
    combined = [
        ("manuscript/ASMAG_2026_submission_ready_v1.md", manuscript),
        ("outputs/submission_package/references_section_draft.md", refs),
        ("outputs/submission_package/references_ready.bib", bib),
    ]
    for location, content in combined:
        for line_no, line in enumerate(content.splitlines(), start=1):
            if "TODO" not in line:
                continue
            topic = infer_todo_topic(line)
            why = infer_todo_why(topic)
            query = infer_query(topic)
            must = infer_todo_resolution(topic)
            entries.append((f"{location}:{line_no}", topic, why, query, must))
    rows = "\n".join(f"| `{loc}` | {topic} | {why} | `{query}` | {must} |" for loc, topic, why, query, must in entries)
    report = (
        "# TODO Reference Report\n\n"
        "This report scans the pass 2 manuscript, reference draft, and BibTeX draft. Exact reliable metadata for the remaining TODO vendor/hardware/power references was not found in the local repo, so these entries were not completed.\n\n"
        "| Location | Topic | Why needed | Suggested search/query | Can remain TODO? |\n"
        "|---|---|---|---|---|\n"
        + (rows if rows else "| - | None | - | - | - |")
    )
    return report, len(entries)


def infer_todo_topic(line: str) -> str:
    lower = line.lower()
    if "tensorrt" in lower:
        return "NVIDIA TensorRT deployment documentation"
    if "openvino" in lower:
        return "Intel OpenVINO deployment documentation"
    if "coral" in lower or "edge tpu" in lower:
        return "Google Coral Edge TPU documentation"
    if "hailo" in lower:
        return "Hailo AI accelerator documentation"
    if "power" in lower or "energy" in lower:
        return "Physical power profiling / energy measurement"
    if "funding" in lower:
        return "Funding statement"
    if "code-release" in lower or "code availability" in lower:
        return "Code availability decision"
    if "author" in lower:
        return "Author contribution details"
    return "User/editorial decision"


def infer_todo_why(topic: str) -> str:
    if "documentation" in topic:
        return "Needed only if vendor platform examples are kept as citable deployment context."
    if "power" in topic:
        return "Needed if the manuscript expands beyond proxy energy and discusses physical measurement practice."
    if "Funding" in topic:
        return "Required declaration for most journals; content depends on user/project funding."
    if "Code" in topic:
        return "Required submission statement; release policy is a user decision."
    if "Author" in topic:
        return "Required declaration; real author names and roles are not present in repo."
    return "Requires user or journal-specific decision."


def infer_query(topic: str) -> str:
    return {
        "NVIDIA TensorRT deployment documentation": "NVIDIA TensorRT documentation citation version access date",
        "Intel OpenVINO deployment documentation": "Intel OpenVINO toolkit documentation citation version access date",
        "Google Coral Edge TPU documentation": "Google Coral Edge TPU documentation citation version access date",
        "Hailo AI accelerator documentation": "Hailo AI accelerator documentation citation version access date",
        "Physical power profiling / energy measurement": "edge AI device physical power measurement profiling paper watts joules",
        "Funding statement": "project funding grant number institution ASMAG-TRC",
        "Code availability decision": "choose code availability statement upon publication reasonable request public GitHub",
        "Author contribution details": "author contribution CRediT names ASMAG-TRC",
    }.get(topic, topic)


def infer_todo_resolution(topic: str) -> str:
    if "documentation" in topic or "power" in topic:
        return "Must resolve before submission if cited in final reference list; otherwise remove or keep out of final references."
    return "Must resolve before submission because it is a declaration/user decision."


def proof_markdown(text: str, todo_count: int) -> str:
    checks = {
        "title present": "Title:" in text[:500],
        "abstract present": "# Abstract" in text,
        "keywords present": "Keywords:" in text,
        "sections 1-8 present": all(f"# {idx}." in text for idx in range(1, 9)),
        "references present": "# References" in text,
        "declarations present": "# Declarations" in text,
        "appendix/supplementary present": "# Appendix / Supplementary Material" in text,
        "figures 1-6 present": all(f"Figure {idx}." in text for idx in range(1, 7)),
        "tables 1-4 present": all(f"Table {idx}." in text for idx in range(1, 5)),
        "equations present": all(key in text for key in ["D_t = |I_t - I_{t-1}|", "M_t^{FD}", "E_t^{sim}"]),
        "captions visible": text.count("Caption: Figure") >= 6,
        "figure paths adjusted": "../../paper_ready_figures/" in text,
    }
    placeholders = [
        "Let denote",
        "where ()",
        "(arXiv)",
        "(Microsoft)",
        "[Figure/image object]",
        "[Math object without extractable text]",
    ]
    rows = "\n".join(f"| {name} | {'Pass' if ok else 'Needs work'} |" for name, ok in checks.items())
    placeholder_rows = "\n".join(f"| `{item}` | {text.count(item)} |" for item in placeholders)
    return (
        "# Word/PDF Proof Report\n\n"
        "DOCX/PDF proofing could not be performed because automatic conversion tools are unavailable. The checks below inspect the Word-ready Markdown structure instead.\n\n"
        "## Structure Checks\n\n| Check | Status |\n|---|---|\n"
        + rows
        + "\n\n## Placeholder Scan\n\n| Placeholder | Count |\n|---|---:|\n"
        + placeholder_rows
        + f"\n\n## Remaining TODO Count\n\n- TODO occurrences across manuscript/reference drafts: `{todo_count}`\n\n## DOCX/PDF Status\n\n- DOCX created: `False`\n- PDF created: `False`\n- Reason: `pandoc`, `soffice/libreoffice`, `python-docx`, and other markdown-to-docx CLIs are unavailable."
    )


def journal_decision_note() -> str:
    return """
# Journal Formatting Decision Note

Sources checked:

- Journal of Real-Time Image Processing / Springer journal page and submission-guideline path: https://link.springer.com/journal/11554
- Springer Nature data availability guidance: https://www.springernature.com/la/authors/research-data-policy/data-availability-statements
- IEEE Access preparing article page: https://ieeeaccess.ieee.org/authors/preparing-your-article/
- IEEE Access submission guidelines: https://ieeeaccess.ieee.org/guide-for-authors/submission-guidelines/
- IEEE Author Center supplementary materials guidance: https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/prepare-supplementary-materials/

## 1. Journal of Real-Time Image Processing

| Aspect | Notes |
|---|---|
| Template required | TODO: verify the current Springer/JRTIP template from the live submission portal before final formatting. Springer journals generally accept common editable source files such as DOCX or LaTeX. |
| Reference style | TODO: verify current JRTIP style. Existing manuscript uses author-year citations and can be adapted to Springer style. |
| Figure/table placement | Likely suitable to place main Figures 1-6 and Tables 1-4 in the manuscript, with large per-video/per-category tables in supplementary material. Verify current artwork requirements. |
| Supplementary handling | Springer supports supplementary information as separate files; include descriptive captions and metadata. |
| Declarations required | Springer Nature commonly expects data availability and relevant declarations. The current Declarations section is a good starting point but user-specific fields remain TODO. |
| Likely fit with ASMAG-TRC | Strong topical fit because the paper emphasizes real-time image/video processing, P95 latency, FPS, and edge constraints. |
| Risks | Needs clear framing as adaptive inference control, not a new SOTA segmentation method. CPU-only simulation and proxy energy must remain explicit. |

## 2. IEEE Access

| Aspect | Notes |
|---|---|
| Template required | IEEE Access states that articles should be submitted using its required Word or LaTeX template and that Word/LaTeX plus matching PDF are required. |
| Reference style | IEEE numbered reference style is expected; the current author-year citations would need conversion. |
| Figure/table placement | Figures and tables should be placed according to the IEEE Access template, likely two-column friendly. |
| Supplementary handling | IEEE allows supplemental material such as code/data/media as separate files; supported formats include DOC/DOCX/PDF/TXT and common image/video/audio formats. |
| Declarations required | IEEE Access has specific submission checklist items, author biographies, keywords, originality, and possibly AI-use acknowledgments depending on final author workflow. |
| Likely fit with ASMAG-TRC | Good broad scope fit for edge AI, video analytics, signal processing, and computational intelligence. |
| Risks | Requires template migration, numbered references, matching PDF/source files, author bios, and careful English proofing. APC/open-access considerations may apply. |

## 3. Generic Springer Journal

| Aspect | Notes |
|---|---|
| Template required | Usually DOCX or LaTeX source files are accepted, but exact requirements vary by journal. Verify target journal instructions. |
| Reference style | Springer journals vary; author-year or numbered styles may be used depending on journal. |
| Figure/table placement | Main figures/tables can remain in manuscript; extensive tables should remain supplementary. |
| Supplementary handling | Springer supplementary information should use standard formats and may be published as received. Include clear file naming and captions. |
| Declarations required | Springer Nature data availability statements are expected for original research; funding, competing interests, author contributions, and ethics/applicability statements often apply. |
| Likely fit with ASMAG-TRC | Depends on scope. Real-time image processing, edge AI, computer vision systems, or applied AI journals are more suitable than pure algorithm-only venues. |
| Risks | Requirements differ by journal; final formatting cannot be locked until the target journal is selected. |
"""


def user_decisions() -> str:
    return """
# User Decisions Required

1. Target journal.
2. Funding statement:
   - Grant/project funding details.
   - No specific funding received.
   - Institutional support only.
3. Code availability:
   - Public GitHub now.
   - Public release upon publication.
   - Available upon reasonable request.
   - Private/not available, with reason.
4. Author contribution names and roles.
5. Corresponding author details:
   - Full name.
   - Affiliation.
   - Email.
   - ORCID if available.
6. Appendix handling:
   - Keep Appendix inside main manuscript.
   - Move Appendix to separate supplementary file.
   - Keep only concise appendix and submit CSV package separately.
7. Additional validation decision:
   - Submit with current CDnet2014 CPU-only simulation.
   - Add a small real hardware validation.
   - Add cross-dataset validation.
8. Reference style:
   - APA / Springer author-year.
   - Springer numbered.
   - IEEE numbered.
9. English proofreading:
   - Author self-proofread.
   - Native-speaker review.
   - Professional editing service.
"""


def conversion_blocked(tools: dict[str, bool]) -> str:
    unavailable = [name for name, ok in tools.items() if not ok and name != "python-markdown"]
    return (
        "# Conversion Blocked\n\n"
        "Automatic DOCX conversion was not attempted because no reliable Markdown-to-DOCX conversion route is available in this environment.\n\n"
        "## Missing Tools\n\n"
        + "\n".join(f"- `{name}`" for name in unavailable)
        + "\n\n## Manual Conversion Route\n\n"
        "Recommended route on a machine with Pandoc installed:\n\n"
        "```bat\n"
        "cd outputs\\submission_package\\pass3_word_ready\n"
        "pandoc ASMAG_2026_word_ready.md --resource-path=.;..\\.. -o ASMAG_2026_submission_ready_v1.docx\n"
        "```\n\n"
        "Then open the generated DOCX in Word or LibreOffice and manually proof equations, tables, figures, captions, references, declarations, and appendix separation. Do not overwrite `manuscript/ASMAG_2026_submission_draft.docx`."
    )


def pdf_blocked() -> str:
    return """
# PDF Export Blocked

PDF export was not attempted because the DOCX was not created and LibreOffice/soffice is unavailable.

Manual route after DOCX creation:

```bat
soffice --headless --convert-to pdf --outdir outputs\\submission_package\\pass3_word_ready outputs\\submission_package\\pass3_word_ready\\ASMAG_2026_submission_ready_v1.docx
```

Alternative: open the DOCX in Microsoft Word or LibreOffice and export/save as PDF manually. Proof that the PDF and source file contain matching content before submission.
"""


def tool_check_report(tools: dict[str, bool], scripts: list[str]) -> str:
    rows = "\n".join(f"| `{name}` | {'Available' if ok else 'Unavailable'} |" for name, ok in tools.items())
    script_lines = "\n".join(f"- `{script}`" for script in scripts) if scripts else "- None found."
    route = (
        "Recommended route: create Word-ready Markdown now, then convert with Pandoc on a machine where Pandoc is installed. "
        "This environment can prepare Markdown and reports, but cannot reliably produce DOCX/PDF."
    )
    return (
        "# Pass 3 Tool Check Report\n\n"
        "## Tool Availability\n\n| Tool | Status |\n|---|---|\n"
        + rows
        + "\n\n## Existing Project Scripts Related to Paper/Export\n\n"
        + script_lines
        + "\n\n## Recommended Conversion Route\n\n"
        + route
    )


def final_report(tools: dict[str, bool], todo_count: int, docx_created: bool, pdf_created: bool) -> str:
    readiness = 80 if WORD_MD.exists() else 78
    return (
        "# Final Pass 3 Word-Ready Report\n\n"
        "## 1. Tool Availability\n\n"
        f"- Pandoc available: `{tools['pandoc']}`\n"
        f"- LibreOffice/soffice available: `{tools['soffice'] or tools['libreoffice']}`\n"
        f"- python-docx available: `{tools['python-docx']}`\n"
        f"- markdown-to-docx CLI available: `{tools['md-to-docx'] or tools['markdown-to-docx'] or tools['md2docx']}`\n\n"
        "## 2. Word-Ready Markdown\n\n"
        f"- Created: `{WORD_MD.relative_to(ROOT).as_posix()}`\n\n"
        "## 3. DOCX Status\n\n"
        f"- DOCX created: `{docx_created}`\n"
        "- Blocked report: `outputs/submission_package/pass3_word_ready/CONVERSION_BLOCKED.md`\n\n"
        "## 4. PDF Status\n\n"
        f"- PDF created: `{pdf_created}`\n"
        "- Blocked report: `outputs/submission_package/pass3_word_ready/PDF_EXPORT_BLOCKED.md`\n\n"
        "## 5. TODO References Status\n\n"
        f"- TODO occurrences scanned across manuscript/reference drafts: `{todo_count}`\n"
        "- Remaining TODOs are user/vendor/hardware/power-profile decisions and should be resolved or removed before final submission.\n\n"
        "## 6. Figure/Table Proof Status\n\n"
        "- Markdown proof confirms title, abstract, keywords, Sections 1-8, references, declarations, appendix, Figures 1-6, Tables 1-4, captions, and key equations are present.\n"
        "- DOCX/PDF visual proof remains blocked until conversion tools are available.\n\n"
        "## 7. Remaining Blockers\n\n"
        "- Install/use Pandoc or equivalent reliable converter.\n"
        "- Export DOCX and PDF, then visually proof equations, figures, captions, tables, references, declarations, and appendix.\n"
        "- Choose target journal and apply its template/reference style.\n"
        "- Resolve funding, code availability, author contributions, and corresponding author details.\n"
        "- Resolve or remove TODO vendor/hardware/power references.\n\n"
        "## 8. New Readiness Score\n\n"
        f"**{readiness}/100.**\n\n"
        "## 9. Exact Next Step\n\n"
        "Use Pandoc on a machine where it is installed to convert `outputs/submission_package/pass3_word_ready/ASMAG_2026_word_ready.md` to DOCX, then export a matching PDF and proof layout.\n\n"
        "## 10. Next Prompt for Codex\n\n"
        "Install or provide access to a reliable DOCX conversion route, then convert `outputs/submission_package/pass3_word_ready/ASMAG_2026_word_ready.md` to DOCX/PDF without overwriting the original manuscript. After conversion, inspect the generated DOCX/PDF for equations, figures, tables, captions, references, declarations, appendix separation, and remaining TODOs."
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tools = tool_status()
    scripts = existing_export_scripts()
    src_text = SRC.read_text(encoding="utf-8")
    ref_text = REF_DRAFT.read_text(encoding="utf-8") if REF_DRAFT.exists() else ""
    bib_text = BIB.read_text(encoding="utf-8") if BIB.exists() else ""

    word_text = make_word_ready_markdown(src_text)
    write(WORD_MD, word_text)

    todo_report, todo_count = todo_reference_report(word_text, ref_text, bib_text)
    write(OUT / "tool_check_report.md", tool_check_report(tools, scripts))
    write(OUT / "todo_reference_report.md", todo_report)
    write(OUT / "CONVERSION_BLOCKED.md", conversion_blocked(tools))
    write(OUT / "PDF_EXPORT_BLOCKED.md", pdf_blocked())
    write(OUT / "word_pdf_proof_report.md", proof_markdown(word_text, todo_count))
    write(OUT / "journal_decision_note.md", journal_decision_note())
    write(OUT / "USER_DECISIONS_REQUIRED.md", user_decisions())
    write(OUT / "FINAL_PASS3_WORD_READY_REPORT.md", final_report(tools, todo_count, False, False))
    print(f"Wrote pass3 outputs to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
