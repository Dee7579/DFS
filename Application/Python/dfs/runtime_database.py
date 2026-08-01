"""Isolated SQLite runtime database preparation for derived DFS data."""
from __future__ import annotations

import atexit
import shutil
import tempfile
from pathlib import Path

from dfs.services.fleet.b5_composite_fleets import ensure_b5_composite_fleets


def prepare_runtime_database(source_path: str | Path) -> Path:
    """Copy the certified database and add generated runtime-only profiles.

    Composite-fleet profiles must never be written into the committed canonical
    database. Each application process receives its own temporary SQLite copy.
    """

    source = Path(source_path).resolve()
    runtime_directory = Path(tempfile.mkdtemp(prefix="dfs_runtime_"))
    runtime_database = runtime_directory / source.name
    # Android app-private storage rejects the extended-attribute copy attempted
    # by shutil.copy2().  The runtime database needs the certified bytes, not
    # the source file's host metadata, so a content-only copy is intentional.
    shutil.copyfile(source, runtime_database)
    atexit.register(shutil.rmtree, runtime_directory, ignore_errors=True)
    ensure_b5_composite_fleets(runtime_database)
    return runtime_database
