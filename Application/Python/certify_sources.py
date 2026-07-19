"""Create the committed checksum manifest for certified DFS source data."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

from dfs.integrity.certified_sources import (
    DEFAULT_CERTIFICATION_ID,
    DATABASE_RELATIVE_PATH,
    format_verification,
    locate_repository_root,
    verify_manifest,
    write_manifest,
)


CERTIFIED_COUNTS = {
    "ships": 280,
    "acta_profiles": 304,
    "weapons": 1099,
    "traits": 1069,
    "profile_fleet_lists": 304,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create the DFS certified-source SHA-256 manifest."
    )
    parser.add_argument(
        "--certification-id",
        default=DEFAULT_CERTIFICATION_ID,
        help="Permanent identifier written into the manifest.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing manifest after a deliberate recertification.",
    )
    parser.add_argument(
        "--skip-validator",
        action="store_true",
        help="Skip validate_database.py (intended only for isolated unit testing).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repository_root = locate_repository_root(Path(__file__))
    python_root = repository_root / "Application" / "Python"

    if not args.skip_validator:
        print("Running database validator before certification...")
        completed = subprocess.run(
            [sys.executable, "validate_database.py"],
            cwd=python_root,
        )
        if completed.returncode != 0:
            print("Certification cancelled because database validation failed.")
            return completed.returncode or 1

    try:
        manifest_path = write_manifest(
            repository_root,
            certification_id=args.certification_id,
            expected_database_counts=CERTIFIED_COUNTS,
            overwrite=args.force,
        )
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        print(f"Certification failed: {exc}")
        return 1

    result = verify_manifest(repository_root, manifest_path=manifest_path)
    print()
    print(format_verification(result))
    if not result.ok:
        return 1

    print()
    print(f"Manifest created: {manifest_path}")
    print(f"Canonical database: {repository_root / DATABASE_RELATIVE_PATH}")
    print("Commit this manifest with the integrity-guard code.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
