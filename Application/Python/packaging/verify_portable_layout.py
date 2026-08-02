"""Validate the contents of a built DFS portable release."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


FORBIDDEN_PARTS = {
    ".git",
    "certification",
    "design documents",
    "design_documents",
    "docs",
    "platform_data",
    "project_sources",
    "tests",
}
FORBIDDEN_SUFFIXES = {
    ".doc",
    ".docx",
    ".md",
    ".py",
    ".pyc",
    ".spec",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _payload_root(bundle_root: Path) -> Path:
    internal = bundle_root / "_internal"
    return internal if internal.is_dir() else bundle_root


def validate_bundle(bundle_root: Path, source_database: Path) -> list[str]:
    """Return release-layout errors without modifying the bundle."""

    errors: list[str] = []
    bundle_root = bundle_root.resolve()
    payload_root = _payload_root(bundle_root)

    executable = bundle_root / "DFS.exe"
    database = payload_root / "Database" / "Data" / "dfs.db"
    resources = payload_root / "resources" / "scenario_maps"
    output = payload_root / "output"

    if not executable.is_file():
        errors.append(f"Missing executable: {executable}")
    if not database.is_file():
        errors.append(f"Missing packaged database: {database}")
    elif sha256(database) != sha256(source_database):
        errors.append("Packaged database does not match the canonical source database.")
    if not resources.is_dir() or not any(resources.glob("*.png")):
        errors.append("Packaged scenario-map resources are missing.")
    if not output.is_dir() or not any(output.rglob("*.pdf")):
        errors.append("Packaged master reference sheets are missing.")

    for path in bundle_root.rglob("*"):
        relative = path.relative_to(bundle_root)
        lowered_parts = {part.casefold() for part in relative.parts}
        if lowered_parts & FORBIDDEN_PARTS:
            errors.append(f"Forbidden development path in release: {relative}")
            continue
        if path.is_file() and path.suffix.casefold() in FORBIDDEN_SUFFIXES:
            errors.append(f"Forbidden source/document file in release: {relative}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle_root", type=Path)
    parser.add_argument("source_database", type=Path)
    args = parser.parse_args()

    errors = validate_bundle(args.bundle_root, args.source_database)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("DFS portable release layout verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
