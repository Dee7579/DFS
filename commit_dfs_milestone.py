from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parent
PYTHON_DIR = REPO / "Application" / "Python"
OUTPUT_DIR = PYTHON_DIR / "output"
GITATTRIBUTES = REPO / ".gitattributes"
GITIGNORE = REPO / ".gitignore"

COMMIT_SUBJECT = "Complete fleet builder milestone and certify 304 profiles"
COMMIT_BODY = """\
- complete the B5 ACTA fleet builder and construction-rule framework
- apply and document the platform gameplay audit corrections
- certify 280 ships, 304 profiles, and 304 generated PDFs
- add database validation and full platform reimport tooling
- remove tracked Python caches and runtime artifacts
"""


def run(*args: str, cwd: Path = REPO, check: bool = True) -> subprocess.CompletedProcess[str]:
    print(f"> {' '.join(args)}")
    result = subprocess.run(list(args), cwd=cwd, text=True)
    if check and result.returncode != 0:
        raise SystemExit(result.returncode)
    return result


def ensure_line(path: Path, line: str, heading: str | None = None) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if line in existing.splitlines():
        return

    with path.open("a", encoding="utf-8", newline="\n") as handle:
        if existing and not existing.endswith("\n"):
            handle.write("\n")
        if heading and heading not in existing:
            handle.write(f"\n{heading}\n")
        handle.write(f"{line}\n")


def main() -> None:
    if not (REPO / ".git").is_dir():
        raise SystemExit(f"Not a Git repository: {REPO}")

    print("============================================================")
    print("DFS MILESTONE COMMIT")
    print("============================================================")
    print("This script will run checks and create a local Git commit.")
    print("It will NOT push to GitHub.")
    input("Press Enter to continue, or close this window to cancel...")

    # Mark generated/binary artifacts correctly so Git does not inspect
    # their internal byte streams as text.
    for line in ("*.pdf binary", "*.db binary", "*.zip binary"):
        ensure_line(GITATTRIBUTES, line)

    ensure_line(
        GITIGNORE,
        "commit_dfs_milestone.py",
        "# DFS local commit-preparation artifacts",
    )

    run("git", "add", ".gitattributes", ".gitignore")

    print("\nRunning Python test suite...")
    run(sys.executable, "-m", "pytest", "-q", cwd=PYTHON_DIR)

    print("\nRunning database validator...")
    run(sys.executable, "validate_database.py", cwd=PYTHON_DIR)

    pdf_count = sum(1 for _ in OUTPUT_DIR.rglob("*.pdf"))
    print(f"\nGenerated PDF count: {pdf_count}")
    if pdf_count != 304:
        raise SystemExit(f"Expected 304 generated PDFs, found {pdf_count}. Commit cancelled.")

    print("\nChecking staged diff...")
    run("git", "diff", "--cached", "--check")

    staged = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=REPO,
    )
    if staged.returncode == 0:
        raise SystemExit("Nothing is staged. Commit cancelled.")

    print("\nCreating local commit...")
    run(
        "git",
        "commit",
        "-m",
        COMMIT_SUBJECT,
        "-m",
        COMMIT_BODY,
    )

    print("\n============================================================")
    print("COMMIT COMPLETE")
    print("============================================================")
    run("git", "log", "-1", "--oneline", check=False)
    print("\nNothing has been pushed.")
    print("After reviewing the commit, push with:")
    print("    git push origin main")


if __name__ == "__main__":
    main()
