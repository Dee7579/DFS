from __future__ import annotations

from pathlib import Path

from dfs.integrity.certified_sources import locate_repository_root, verify_manifest


def test_committed_certified_sources_are_unchanged():
    repository_root = locate_repository_root(Path(__file__))
    result = verify_manifest(repository_root)

    details = "\n".join(
        f"{issue.kind}: {issue.path} (expected={issue.expected}, actual={issue.actual})"
        for issue in result.issues
    )
    assert result.ok, details
