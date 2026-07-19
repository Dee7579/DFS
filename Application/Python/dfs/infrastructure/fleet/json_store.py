"""Versioned, portable JSON persistence for DFS fleet files."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dfs.domain.fleet import Fleet, FleetEntry


class FleetFileError(ValueError):
    pass


class JSONFleetStore:
    FILE_EXTENSION = ".dfs-fleet.json"

    def save(self, fleet: Fleet, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": fleet.schema_version,
            "fleet_id": fleet.fleet_id,
            "name": fleet.name,
            "game_system_id": fleet.game_system_id,
            "construction_profile_id": fleet.construction_profile_id,
            "faction_id": fleet.faction_id,
            "fleet_list_id": fleet.fleet_list_id,
            "selected_year": fleet.selected_year,
            "entries": [
                {
                    "entry_id": entry.entry_id,
                    "profile_id": entry.profile_id,
                    "quantity": entry.quantity,
                    "options": dict(entry.options),
                    "vessel_name": entry.vessel_name,
                    "notes": entry.notes,
                }
                for entry in fleet.entries
            ],
            "notes": fleet.notes,
            "metadata": dict(fleet.metadata),
            "created_at": fleet.created_at,
            "updated_at": fleet.updated_at,
        }
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(target)
        return target

    def load(self, path: str | Path) -> Fleet:
        source = Path(path)
        try:
            payload: dict[str, Any] = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise FleetFileError(f"Unable to read fleet file: {source}") from exc
        version = int(payload.get("schema_version", 0))
        if version != Fleet.CURRENT_SCHEMA_VERSION:
            raise FleetFileError(
                f"Unsupported fleet schema version {version}; expected {Fleet.CURRENT_SCHEMA_VERSION}."
            )
        entries = tuple(
            FleetEntry(
                entry_id=str(item["entry_id"]),
                profile_id=int(item["profile_id"]),
                quantity=int(item.get("quantity", 1)),
                options=dict(item.get("options", {})),
                vessel_name=str(item.get("vessel_name", "")),
                notes=str(item.get("notes", "")),
            )
            for item in payload.get("entries", [])
        )
        return Fleet(
            schema_version=version,
            fleet_id=str(payload["fleet_id"]),
            name=str(payload.get("name", "Untitled Fleet")),
            game_system_id=str(payload["game_system_id"]),
            construction_profile_id=str(payload["construction_profile_id"]),
            faction_id=payload.get("faction_id"),
            fleet_list_id=payload.get("fleet_list_id"),
            selected_year=payload.get("selected_year"),
            entries=entries,
            notes=str(payload.get("notes", "")),
            metadata=dict(payload.get("metadata", {})),
            created_at=str(payload.get("created_at", "")),
            updated_at=str(payload.get("updated_at", "")),
        )
