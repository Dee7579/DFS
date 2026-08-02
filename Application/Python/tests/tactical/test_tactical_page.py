from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from dfs.domain.tactical import GamePhase, TacticalGameState, TacticalUnitState, TrackState, UnitKind
from dfs.infrastructure.tactical import JSONTacticalGameStore
from dfs.ui.tactical_assistant import TacticalAssistantPage


class _Settings:
    def __init__(self) -> None:
        self.values: dict[str, object] = {}

    def get_str(self, key: str, default: str = "") -> str:
        return str(self.values.get(key, default))

    def set_value(self, key: str, value: object) -> None:
        self.values[key] = value

    def sync(self) -> None:
        pass


class _Status:
    def __init__(self) -> None:
        self.message = ""

    def set(self, message: str) -> None:
        self.message = message


class _Notifications:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    def info(self, title: str, message: str) -> None:
        self.messages.append((title, message))


class _TacticalFiles:
    FILE_EXTENSION = ".dfs-game.json"

    def __init__(self) -> None:
        self.store = JSONTacticalGameStore()

    def save(self, game: TacticalGameState, path: str | Path) -> Path:
        return self.store.save(game, path)

    def load(self, path: str | Path) -> TacticalGameState:
        return self.store.load(path)

    def create_from_fleet_file(self, _path: str | Path) -> TacticalGameState:
        raise AssertionError("This UI test supplies game state directly.")


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance() or QApplication([])
    return app


@pytest.fixture
def game() -> TacticalGameState:
    ship = TacticalUnitState(
        unit_id="ship-1",
        source_entry_id="entry-1",
        profile_id=101,
        parent_unit_id=None,
        kind=UnitKind.PLATFORM,
        platform_name="Test Cruiser",
        vessel_name="Resolute",
        faction_name="Earth Alliance",
        fleet_name="Crusade Era",
        priority_level="Raid",
        damage=TrackState.create(30, threshold=8),
        crew=TrackState.create(40, threshold=10),
        shields=TrackState.create(6, recovery="2"),
        crew_quality="4",
    )
    fighter = TacticalUnitState(
        unit_id="fighter-1",
        source_entry_id="entry-1",
        profile_id=102,
        parent_unit_id="ship-1",
        kind=UnitKind.CRAFT,
        platform_name="Aurora Starfury flight",
    )
    return TacticalGameState.create(
        name="UI Battle",
        game_system_id="b5_acta_2e",
        source_fleet_id="fleet-1",
        source_fleet_name="UI Fleet",
        units=(ship, fighter),
    )


@pytest.fixture
def page(qapp: QApplication, tmp_path: Path) -> TacticalAssistantPage:
    context = SimpleNamespace(
        tactical_games=_TacticalFiles(),
        settings=_Settings(),
        resources=SimpleNamespace(project_root=tmp_path),
        status=_Status(),
        notifications=_Notifications(),
    )
    widget = TacticalAssistantPage(context)
    yield widget
    widget.close()


def test_page_loads_every_individual_unit_and_edits_tracks(
    page: TacticalAssistantPage,
    game: TacticalGameState,
    qapp: QApplication,
) -> None:
    page.load_game_state(game)

    assert page.unit_tree.topLevelItemCount() == 1
    ship_item = page.unit_tree.topLevelItem(0)
    assert ship_item.childCount() == 1
    assert ship_item.text(0) == "Resolute — Test Cruiser"
    assert "Resolute" in ship_item.toolTip(0)
    fighter_group = ship_item.child(0)
    assert fighter_group.text(0) == "Aurora Starfury flight x1"
    assert fighter_group.childCount() == 1
    assert fighter_group.child(0).text(0) == "Aurora Starfury flight"

    page.unit_tree.setCurrentItem(ship_item)
    page.damage_editor.current_spin.setValue(24)
    page.crew_editor.current_spin.setValue(35)
    page.shields_editor.current_spin.setValue(3)
    qapp.processEvents()

    updated = page.current_game.get_unit("ship-1")
    assert updated.damage.current == 24
    assert updated.crew.current == 35
    assert updated.shields.current == 3
    assert page.is_dirty is True


def test_page_updates_turn_phase_and_advance_turn(
    page: TacticalAssistantPage,
    game: TacticalGameState,
    qapp: QApplication,
) -> None:
    page.load_game_state(game)
    page.turn_spin.setValue(3)
    page.phase_combo.setCurrentIndex(page.phase_combo.findData(GamePhase.ATTACK.value))
    qapp.processEvents()

    assert page.current_game.turn_number == 3
    assert page.current_game.phase is GamePhase.ATTACK

    page.advance_turn_button.click()
    qapp.processEvents()
    assert page.current_game.turn_number == 4
    assert page.current_game.phase is GamePhase.INITIATIVE


def test_page_saves_independent_game_file(
    page: TacticalAssistantPage,
    game: TacticalGameState,
    tmp_path: Path,
) -> None:
    page.load_game_state(game)
    page.turn_spin.setValue(2)
    target = page.save_game_to_path(tmp_path / "battle")

    assert target.name == "battle.dfs-game.json"
    assert target.exists()
    assert page.current_path == target.resolve()
    assert page.is_dirty is False


def test_page_can_reopen_independent_game_file(
    page: TacticalAssistantPage,
    game: TacticalGameState,
    tmp_path: Path,
) -> None:
    target = tmp_path / "reopen.dfs-game.json"
    JSONTacticalGameStore().save(game.set_turn_number(5), target)

    loaded = page.load_game_from_path(target)

    assert loaded.turn_number == 5
    assert page.current_game.turn_number == 5
    assert page.current_path == target.resolve()
    assert page.is_dirty is False
