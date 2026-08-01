"""Materialize the certified database embedded in an Android staging build."""

from __future__ import annotations

import base64
import hashlib
from pathlib import Path
import zlib


class BundledDatabaseError(RuntimeError):
    pass


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def materialize_bundled_database(destination: str | Path) -> Path:
    """Write the verified build-time database payload into app-private storage."""

    try:
        from dfs.mobile._bundled_database_payload import (  # type: ignore[import-not-found]
            DATABASE_B85,
            DATABASE_SHA256,
        )
    except ImportError as exc:
        raise BundledDatabaseError("This build does not contain a certified DFS database.") from exc

    target = Path(destination).expanduser().resolve()
    if target.is_file() and _sha256(target.read_bytes()) == DATABASE_SHA256:
        return target

    try:
        compressed = base64.b85decode("".join(DATABASE_B85).encode("ascii"))
        payload = zlib.decompress(compressed)
    except (ValueError, zlib.error) as exc:
        raise BundledDatabaseError("The bundled DFS database payload is damaged.") from exc
    if _sha256(payload) != DATABASE_SHA256:
        raise BundledDatabaseError("The bundled DFS database failed its integrity check.")

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(target)
    return target
