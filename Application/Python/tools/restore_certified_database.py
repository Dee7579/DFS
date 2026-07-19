from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime
from typing import Iterable
import zipfile


DB_RELATIVE = Path("Database/Data/dfs.db")
MANIFEST_RELATIVE = Path(
    "Application/Python/data/certification/b5_acta_certified_sources.json"
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def locate_repo() -> Path:
    start = Path(__file__).resolve()
    for candidate in (start.parent, *start.parents):
        if (candidate / ".git").exists() and (candidate / DB_RELATIVE).exists():
            return candidate
    raise SystemExit("Could not locate the DFS Git repository root.")


def expected_certification(repo: Path) -> tuple[str, int, dict[str, int]]:
    manifest_path = repo / MANIFEST_RELATIVE
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    db_entry = next(
        (
            entry
            for entry in manifest.get("files", [])
            if entry.get("path") == DB_RELATIVE.as_posix()
        ),
        None,
    )
    if not db_entry:
        raise SystemExit(
            f"The certification manifest does not contain {DB_RELATIVE.as_posix()}."
        )
    return (
        str(db_entry["sha256"]).lower(),
        int(db_entry["size_bytes"]),
        {str(k): int(v) for k, v in manifest["database_counts"].items()},
    )


def validate_sqlite_bytes(data: bytes, expected_counts: dict[str, int]) -> None:
    handle, temp_name = tempfile.mkstemp(suffix=".db")
    os.close(handle)
    temp = Path(temp_name)
    try:
        temp.write_bytes(data)
        connection = sqlite3.connect(f"file:{temp.as_posix()}?mode=ro", uri=True)
        try:
            actual = {
                table: int(
                    connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                )
                for table in expected_counts
            }
        finally:
            connection.close()
    finally:
        temp.unlink(missing_ok=True)

    if actual != expected_counts:
        raise ValueError(
            f"Candidate hash matched but database counts did not: "
            f"expected {expected_counts}, found {actual}"
        )


def git_commit_candidates(repo: Path) -> Iterable[tuple[str, bytes]]:
    commits: list[str] = []

    for command in (
        ("log", "--all", "--format=%H", "--", DB_RELATIVE.as_posix()),
        ("reflog", "--all", "--format=%H"),
    ):
        result = run_git(repo, *command)
        if result.returncode == 0:
            commits.extend(result.stdout.decode("utf-8", errors="replace").splitlines())

    fsck = run_git(repo, "fsck", "--no-reflogs", "--unreachable")
    if fsck.returncode in (0, 1):
        for line in fsck.stdout.decode("utf-8", errors="replace").splitlines():
            parts = line.split()
            if len(parts) == 3 and parts[0] == "unreachable" and parts[1] == "commit":
                commits.append(parts[2])

    seen: set[str] = set()
    for commit in commits:
        commit = commit.strip()
        if not commit or commit in seen:
            continue
        seen.add(commit)
        result = run_git(repo, "show", f"{commit}:{DB_RELATIVE.as_posix()}")
        if result.returncode == 0 and result.stdout.startswith(b"SQLite format 3"):
            yield f"Git commit {commit}", result.stdout


def local_file_candidates(repo: Path) -> Iterable[tuple[str, bytes]]:
    candidate_paths: list[Path] = []

    data_dir = repo / DB_RELATIVE.parent
    candidate_paths.extend(sorted(data_dir.glob("dfs_before_*.db")))
    candidate_paths.extend(sorted(data_dir.glob("*backup*.db")))

    known = [
        Path("D:/Clone/DFS") / DB_RELATIVE,
        Path("D:/GitHub/DFS-Fresh-Test") / DB_RELATIVE,
        repo.parent / "DFS-Fresh-Test" / DB_RELATIVE,
    ]
    candidate_paths.extend(known)

    # Search likely checkout roots without crawling the whole drive.
    search_parents = {
        repo.parent,
        repo.parent.parent / "Clone",
        Path(repo.anchor) / "Clone" if repo.anchor else repo.parent,
    }
    for parent in search_parents:
        if not parent.is_dir():
            continue
        for child in parent.iterdir():
            candidate = child / DB_RELATIVE
            if candidate.is_file():
                candidate_paths.append(candidate)

    seen: set[Path] = set()
    canonical = (repo / DB_RELATIVE).resolve()
    for path in candidate_paths:
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if resolved == canonical or resolved in seen or not resolved.is_file():
            continue
        seen.add(resolved)
        try:
            data = resolved.read_bytes()
        except OSError:
            continue
        if data.startswith(b"SQLite format 3"):
            yield f"Local file {resolved}", data


def zip_candidates(repo: Path) -> Iterable[tuple[str, bytes]]:
    archives: list[Path] = []
    preferred = repo / "Application" / "DFS.zip"
    if preferred.is_file():
        archives.append(preferred)
    archives.extend(sorted(repo.glob("*.zip")))

    seen: set[Path] = set()
    for archive in archives:
        archive = archive.resolve()
        if archive in seen:
            continue
        seen.add(archive)
        try:
            with zipfile.ZipFile(archive) as zf:
                names = [
                    name
                    for name in zf.namelist()
                    if name.replace("\\", "/").lower().endswith(
                        DB_RELATIVE.as_posix().lower()
                    )
                    or name.replace("\\", "/").lower().endswith("/dfs.db")
                ]
                for name in names:
                    data = zf.read(name)
                    if data.startswith(b"SQLite format 3"):
                        yield f"ZIP {archive} :: {name}", data
        except (OSError, zipfile.BadZipFile, KeyError):
            continue


def restore_exact_database(repo: Path) -> str:
    expected_hash, expected_size, expected_counts = expected_certification(repo)
    current = repo / DB_RELATIVE

    print(f"Expected certified SHA-256: {expected_hash}")
    print(f"Expected certified size:    {expected_size} bytes")
    print(f"Current database SHA-256:   {sha256_file(current)}")
    print()

    candidate_groups = (
        ("Git history and reflogs", git_commit_candidates(repo)),
        ("local backups and clean clones", local_file_candidates(repo)),
        ("DFS ZIP archives", zip_candidates(repo)),
    )

    searched = 0
    for label, candidates in candidate_groups:
        print(f"Searching {label}...")
        for source, data in candidates:
            searched += 1
            if len(data) != expected_size:
                continue
            if sha256_bytes(data) != expected_hash:
                continue

            validate_sqlite_bytes(data, expected_counts)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup = current.with_name(f"dfs_before_certified_restore_{stamp}.db")
            shutil.copy2(current, backup)

            handle, temporary_name = tempfile.mkstemp(
                prefix="dfs_certified_",
                suffix=".db",
                dir=current.parent,
            )
            os.close(handle)
            temporary = Path(temporary_name)
            try:
                temporary.write_bytes(data)
                os.replace(temporary, current)
            finally:
                temporary.unlink(missing_ok=True)

            if sha256_file(current) != expected_hash:
                raise SystemExit("Atomic restore completed, but the final hash is wrong.")

            print()
            print(f"RESTORED from: {source}")
            print(f"Contaminated database backup: {backup}")
            print(f"Candidates inspected: {searched}")
            return source

    raise SystemExit(
        "\nCould not find the exact certified database bytes.\n"
        f"Expected SHA-256: {expected_hash}\n"
        "No file was replaced. Keep the report and do not force-recertify."
    )


def main() -> int:
    repo = locate_repo()
    print("DFS exact certified-database recovery")
    print(f"Repository: {repo}")
    print()
    restore_exact_database(repo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
