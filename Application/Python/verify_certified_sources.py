"""Verify DFS platform modules and canonical database against certification."""
from __future__ import annotations

from pathlib import Path

from dfs.integrity.certified_sources import (
    format_verification,
    locate_repository_root,
    verify_manifest,
)


def main() -> int:
    try:
        repository_root = locate_repository_root(Path(__file__))
        result = verify_manifest(repository_root)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Certified-source verification failed: {exc}")
        return 1

    print(format_verification(result))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
