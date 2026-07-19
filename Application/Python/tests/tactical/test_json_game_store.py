from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from dfs.domain.tactical import (
    CriticalHitState,
    GamePhase,
    TacticalGameState,
    TacticalUnitState,
    TrackState,
    TraitState,
    UnitKind,
    WeaponState,
)
from dfs.infrastructure.tactical import JSONTacticalGameStore, TacticalGameFileError


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _game() -> TacticalGameState:
    critical = CriticalHitState.create("Weapons offline", "One weapon disabled")
    unit = TacticalUnitState(
        unit_id="unit-1",
        source_entry_id="entry-1",
        profile_id=100,
        parent_unit_id=None,
        kind=UnitKind.PLATFORM,
        platform_name="Test Destroyer",
        vessel_name="Valiant",
        faction_name="Test Faction",
        fleet_name="Test Fleet",
        priority_level="Battle",
        source_notes=("Source note",),
        damage=TrackState.create(50, threshold=12).lose(9),
        crew=TrackState.create(60, threshold=15).lose(4),
        shields=TrackState.create(8, recovery="2").lose(3),
        crew_quality="5",
        traits=(TraitState("trait-1", "Jump Engine", True),),
        weapons=(WeaponState("weapon-1", "Laser", "F", disabled=True, destroyed=False),),
        critical_hits=(critical,),
        special_action="Close Blast Doors!",
        notes="Player note",
    )
    return TacticalGameState.create(
        name="Test Battle",
        game_system_id="b5_acta",
        source_fleet_id="fleet-1",
        source_fleet_name="Test Fleet",
        units=(unit,),
        metadata={"selected_year": 2261},
    ).set_phase(GamePhase.MOVEMENT)


def test_game_file_round_trip_preserves_complete_live_state(tmp_path: Path) -> None:
    store = JSONTacticalGameStore()
    source = _game()
    path = tmp_path / "test.dfs-game.json"

    store.save(source, path)
    loaded = store.load(path)

    assert loaded == source
    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == 1


def test_game_save_and_load_do_not_touch_protected_sources(tmp_path: Path) -> None:
    protected_platform = tmp_path / "platform_data" / "ship.py"
    protected_database = tmp_path / "dfs.db"
    protected_platform.parent.mkdir()
    protected_platform.write_text("SHIP_NAME = 'Certified'\n", encoding="utf-8")
    protected_database.write_bytes(b"certified database bytes")
    before = (_hash(protected_platform), _hash(protected_database))

    game_path = tmp_path / "games" / "battle.dfs-game.json"
    store = JSONTacticalGameStore()
    store.save(_game(), game_path)
    store.load(game_path)

    assert (_hash(protected_platform), _hash(protected_database)) == before
    assert game_path.exists()


def test_unsupported_schema_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "future.dfs-game.json"
    path.write_text('{"schema_version": 999}', encoding="utf-8")

    with pytest.raises(TacticalGameFileError, match="Unsupported tactical game schema"):
        JSONTacticalGameStore().load(path)
