from __future__ import annotations

import os
from pathlib import Path
import tempfile


TARGET = (
    Path(__file__).resolve().parents[1]
    / "dfs"
    / "services"
    / "fleet"
    / "b5_composite_fleets.py"
)

GUARD_BLOCK = '''

class CanonicalDatabaseWriteError(RuntimeError):
    pass


def canonical_database_path() -> Path:
    return Path(__file__).resolve().parents[5] / "Database" / "Data" / "dfs.db"


def _targets_canonical_database(database_path: str | Path) -> bool:
    target = Path(database_path).resolve()
    canonical = canonical_database_path().resolve()
    try:
        return target.samefile(canonical)
    except FileNotFoundError:
        return target == canonical
'''

OLD_FUNCTION_START = '''def ensure_b5_composite_fleets(database_path: str | Path) -> None:
    connection = sqlite3.connect(str(database_path))
'''

NEW_FUNCTION_START = '''def ensure_b5_composite_fleets(database_path: str | Path) -> None:
    # Generated composite profiles belong only in a disposable runtime database.
    if _targets_canonical_database(database_path):
        raise CanonicalDatabaseWriteError(
            "Refusing to add generated composite-fleet profiles to the certified "
            "Database/Data/dfs.db. Use dfs.runtime_database.prepare_runtime_database()."
        )

    connection = sqlite3.connect(str(Path(database_path).resolve()))
'''


def main() -> int:
    if not TARGET.exists():
        raise SystemExit(f"Composite-fleet source file not found: {TARGET}")

    source = TARGET.read_text(encoding="utf-8")
    if "class CanonicalDatabaseWriteError" in source:
        print("Canonical database guard is already installed.")
        return 0

    insertion_marker = "\n\ndef _army_name_allowed"
    if insertion_marker not in source:
        raise SystemExit(
            "Expected insertion marker was not found. Source file was not changed."
        )
    if OLD_FUNCTION_START not in source:
        raise SystemExit(
            "Expected ensure_b5_composite_fleets implementation was not found. "
            "Source file was not changed."
        )

    updated = source.replace(insertion_marker, GUARD_BLOCK + insertion_marker, 1)
    updated = updated.replace(OLD_FUNCTION_START, NEW_FUNCTION_START, 1)

    handle, temporary_name = tempfile.mkstemp(
        prefix=TARGET.name + ".",
        suffix=".tmp",
        dir=TARGET.parent,
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(updated)
        os.replace(temporary_name, TARGET)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)

    print(f"Installed canonical database write guard: {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
