"""Create and verify the DFS certified-source checksum manifest.

The canonical platform modules and SQLite database are immutable inputs to
runtime features such as Fleet Builder and Tactical Assistant.  This module
records their SHA-256 hashes and reports any missing, changed, or unexpected
protected source file.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterable


MANIFEST_FORMAT_VERSION = 1
DEFAULT_CERTIFICATION_ID = "b5-acta-certified-304"
DEFAULT_MANIFEST_RELATIVE_PATH = Path(
    "Application/Python/data/certification/b5_acta_certified_sources.json"
)
DEFAULT_MANIFEST_PATH = DEFAULT_MANIFEST_RELATIVE_PATH
PLATFORM_DATA_RELATIVE_PATH = Path("Application/Python/platform_data")
DATABASE_RELATIVE_PATH = Path("Database/Data/dfs.db")
DATABASE_TABLES = (
    "ships",
    "acta_profiles",
    "weapons",
    "traits",
    "profile_fleet_lists",
)


@dataclass(frozen=True, slots=True)
class IntegrityIssue:
    """One difference between the certified manifest and the checkout."""

    kind: str
    path: str
    expected: str | int | None = None
    actual: str | int | None = None


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """Complete verification outcome."""

    certification_id: str
    manifest_path: Path
    checked_file_count: int
    issues: tuple[IntegrityIssue, ...]

    @property
    def ok(self) -> bool:
        return not self.issues


def locate_repository_root(start: str | Path | None = None) -> Path:
    """Find the DFS repository root from a path inside the checkout."""

    candidate = Path(start or __file__).resolve()
    if candidate.is_file():
        candidate = candidate.parent

    for directory in (candidate, *candidate.parents):
        if (
            (directory / PLATFORM_DATA_RELATIVE_PATH).is_dir()
            and (directory / DATABASE_RELATIVE_PATH).is_file()
        ):
            return directory

    raise FileNotFoundError(
        "Could not locate the DFS repository root. Expected both "
        f"{PLATFORM_DATA_RELATIVE_PATH.as_posix()} and "
        f"{DATABASE_RELATIVE_PATH.as_posix()}."
    )


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Return a lowercase SHA-256 digest for *path*."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_path(repository_root: Path, manifest_path: str | Path | None) -> Path:
    if manifest_path is None:
        return repository_root / DEFAULT_MANIFEST_RELATIVE_PATH
    supplied = Path(manifest_path)
    return supplied if supplied.is_absolute() else repository_root / supplied


def protected_relative_paths(repository_root: Path) -> tuple[Path, ...]:
    """Return every file protected by the certification manifest."""

    platform_root = repository_root / PLATFORM_DATA_RELATIVE_PATH
    platform_files = sorted(
        path.relative_to(repository_root)
        for path in platform_root.rglob("*.py")
        if "__pycache__" not in path.parts
    )
    return tuple(platform_files + [DATABASE_RELATIVE_PATH])


def database_counts(database_path: Path) -> dict[str, int]:
    """Read the canonical certification counts from the SQLite database."""

    connection = sqlite3.connect(f"file:{database_path.as_posix()}?mode=ro", uri=True)
    try:
        cursor = connection.cursor()
        counts: dict[str, int] = {}
        for table in DATABASE_TABLES:
            cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
            counts[table] = int(cursor.fetchone()[0])
        return counts
    finally:
        connection.close()


def build_manifest(
    repository_root: str | Path,
    *,
    certification_id: str = DEFAULT_CERTIFICATION_ID,
    expected_database_counts: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Build a deterministic manifest dictionary for the current checkout."""

    root = Path(repository_root).resolve()
    paths = protected_relative_paths(root)
    if not paths:
        raise ValueError("No protected DFS source files were found.")

    counts = database_counts(root / DATABASE_RELATIVE_PATH)
    if expected_database_counts:
        mismatches = {
            table: (expected, counts.get(table))
            for table, expected in expected_database_counts.items()
            if counts.get(table) != expected
        }
        if mismatches:
            details = ", ".join(
                f"{table}: expected {expected}, found {actual}"
                for table, (expected, actual) in mismatches.items()
            )
            raise ValueError(f"Database counts do not match the certified baseline: {details}")

    files = [
        {
            "path": relative.as_posix(),
            "sha256": sha256_file(root / relative),
            "size_bytes": (root / relative).stat().st_size,
        }
        for relative in paths
    ]

    return {
        "format_version": MANIFEST_FORMAT_VERSION,
        "certification_id": certification_id,
        "algorithm": "sha256",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "protected_roots": [PLATFORM_DATA_RELATIVE_PATH.as_posix()],
        "protected_single_files": [DATABASE_RELATIVE_PATH.as_posix()],
        "database_counts": counts,
        "files": files,
    }


def write_manifest(
    repository_root: str | Path,
    *,
    manifest_path: str | Path | None = None,
    certification_id: str = DEFAULT_CERTIFICATION_ID,
    expected_database_counts: dict[str, int] | None = None,
    overwrite: bool = False,
) -> Path:
    """Write a new certification manifest, refusing replacement by default."""

    root = Path(repository_root).resolve()
    destination = _manifest_path(root, manifest_path)
    if destination.exists() and not overwrite:
        raise FileExistsError(
            f"Certification manifest already exists: {destination}. "
            "Use the explicit force option only after a deliberate recertification."
        )

    manifest = build_manifest(
        root,
        certification_id=certification_id,
        expected_database_counts=expected_database_counts,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Certified-source manifest is missing: {path}. "
            "Run certify_sources.py to create the baseline."
        ) from None

    if manifest.get("format_version") != MANIFEST_FORMAT_VERSION:
        raise ValueError(
            "Unsupported certified-source manifest format: "
            f"{manifest.get('format_version')!r}"
        )
    if manifest.get("algorithm") != "sha256":
        raise ValueError("The certified-source manifest must use SHA-256.")
    return manifest


def _current_protected_paths_from_manifest(
    repository_root: Path,
    manifest: dict[str, Any],
) -> set[str]:
    current: set[str] = set()
    for relative_root in manifest.get("protected_roots", []):
        source_root = repository_root / Path(relative_root)
        if source_root.is_dir():
            current.update(
                path.relative_to(repository_root).as_posix()
                for path in source_root.rglob("*.py")
                if "__pycache__" not in path.parts
            )
    for relative_file in manifest.get("protected_single_files", []):
        path = repository_root / Path(relative_file)
        if path.exists():
            current.add(Path(relative_file).as_posix())
    return current


def verify_manifest(
    repository_root: str | Path,
    *,
    manifest_path: str | Path | None = None,
) -> VerificationResult:
    """Verify the checkout against its committed certification manifest."""

    root = Path(repository_root).resolve()
    source = _manifest_path(root, manifest_path)
    manifest = _load_manifest(source)
    issues: list[IntegrityIssue] = []

    expected_files = {
        str(entry["path"]): entry
        for entry in manifest.get("files", [])
    }
    current_files = _current_protected_paths_from_manifest(root, manifest)

    for relative_path, entry in sorted(expected_files.items()):
        path = root / Path(relative_path)
        if not path.is_file():
            issues.append(IntegrityIssue("missing", relative_path, entry.get("sha256"), None))
            continue
        actual_hash = sha256_file(path)
        expected_hash = str(entry.get("sha256", ""))
        if actual_hash != expected_hash:
            issues.append(IntegrityIssue("changed", relative_path, expected_hash, actual_hash))

    for relative_path in sorted(current_files - set(expected_files)):
        issues.append(IntegrityIssue("unexpected", relative_path, None, sha256_file(root / relative_path)))

    database_path = root / DATABASE_RELATIVE_PATH
    if database_path.is_file():
        actual_counts = database_counts(database_path)
        for table, expected in sorted(manifest.get("database_counts", {}).items()):
            actual = actual_counts.get(table)
            if actual != expected:
                issues.append(
                    IntegrityIssue(
                        "database_count",
                        f"{DATABASE_RELATIVE_PATH.as_posix()}::{table}",
                        int(expected),
                        actual,
                    )
                )

    return VerificationResult(
        certification_id=str(manifest.get("certification_id", "unknown")),
        manifest_path=source,
        checked_file_count=len(expected_files),
        issues=tuple(issues),
    )


def format_verification(result: VerificationResult) -> str:
    """Return a concise human-readable verification report."""

    lines = [
        "=====================================",
        "DFS CERTIFIED-SOURCE VERIFICATION",
        "=====================================",
        f"Certification: {result.certification_id}",
        f"Manifest:      {result.manifest_path}",
        f"Files checked: {result.checked_file_count}",
        "",
    ]
    if result.ok:
        lines.extend(
            [
                "PASS  All certified platform modules are unchanged",
                "PASS  The canonical DFS database is unchanged",
                "",
                "Certified-source verification PASSED",
            ]
        )
        return "\n".join(lines)

    for issue in result.issues:
        if issue.kind == "missing":
            lines.append(f"FAIL  Missing protected file: {issue.path}")
        elif issue.kind == "unexpected":
            lines.append(f"FAIL  Unexpected platform-data file: {issue.path}")
        elif issue.kind == "database_count":
            lines.append(
                f"FAIL  Database count changed: {issue.path} "
                f"(expected {issue.expected}, found {issue.actual})"
            )
        else:
            lines.append(f"FAIL  Protected file changed: {issue.path}")
    lines.extend(["", "Certified-source verification FAILED"])
    return "\n".join(lines)
