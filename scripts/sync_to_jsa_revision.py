"""Sync ASMAG_Project_Code -> JSA Revision workspace (single source of record).

Run from the project root after each revision phase:
    python scripts/sync_to_jsa_revision.py

Copies (one-way, project -> JSA Revision):
  - clean code snapshot        -> 04_Code/asmag-trc/
  - outputs/revision_jsa/**    -> 05_Results/
Never deletes anything in the destination; overwrites changed files only.
"""
import filecmp
import shutil
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
JSA = Path(r"D:\PhD Program\03.Final Submission\01 JSA - ASMAG-TRC\JSA Revision")

CODE_INCLUDE = [
    "src", "configs", "docs", "tools", "evaluation", "datasets", "scripts", "tests",
    "jetson",  # Jetson-side scripts pulled back from the device (Phase 0)
    "requirements.txt", "README.md", "README_QUICKSTART.md", "RUNBOOK.md",
    "PROJECT_STATE.md", "TASK_BOARD.md", "LICENSE",
    "run_cross_dataset.py", "jetson_gpu_profiler.py", "jetson_profiler.py",
]
EXCLUDE_DIRS = {"__pycache__", ".git", "outputs", "logs", "models", "manuscript"}


def copy_tree(src: Path, dst: Path) -> int:
    n = 0
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists() or not filecmp.cmp(src, dst, shallow=True):
            shutil.copy2(src, dst)
            n += 1
        return n
    for p in src.rglob("*"):
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        rel = p.relative_to(src)
        out = dst / rel
        if p.is_dir():
            out.mkdir(parents=True, exist_ok=True)
        else:
            out.parent.mkdir(parents=True, exist_ok=True)
            if not out.exists() or not filecmp.cmp(p, out, shallow=True):
                shutil.copy2(p, out)
                n += 1
    return n


def main() -> None:
    assert JSA.exists(), f"JSA Revision workspace not found: {JSA}"
    total = 0
    for item in CODE_INCLUDE:
        src = PROJECT / item
        if src.exists():
            total += copy_tree(src, JSA / "04_Code" / "asmag-trc" / item)
    rev = PROJECT / "outputs" / "revision_jsa"
    if rev.exists():
        total += copy_tree(rev, JSA / "05_Results")
    print(f"Synced {total} changed file(s) -> {JSA}")


if __name__ == "__main__":
    main()
