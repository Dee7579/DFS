from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QComboBox, QDialog

from dfs.domain.tactical import (
    GamePhase,
    TacticalGameState,
    TacticalUnitState,
    TrackState,
    TraitState,
    UnitKind,
    WeaponState,
)
from dfs.infrastructure.tactical import JSONTacticalGameStore
from dfs.ui.tactical_assistant import TacticalAssistantPage
import dfs.ui.tactical_assistant.page as page_module


class _Settings:
    def __init__(self) -> None:
        self.values: dict[str, object] = {}

    def get_str(self, key: str, default: str = "") -> str:
        return str(self.values.get(key, default))

    def set_value(self, key: str, value: object) -> None:
        self.values[key] = value

    def sync(self) -> None:
        pass


class _TacticalFiles:
    FILE_EXTENSION = ".dfs-game.json"

    def __init__(self) -> None:
        self.store = JSONTacticalGameStore()

    def save(self, game: TacticalGameState, path: str | Path) -> Path:
        return self.store.save(game, path)

    def load(self, path: str | Path) -> TacticalGameState:
        return self.store.load(path)

    def create_from_fleet_file(self, _path: str | Path) -> TacticalGameState:
        raise AssertionError


class _Status:
    def __init__(self) -> None:
        self.message = ""

    def set(self, message: str) -> None:
        self.message = message


class _Notifications:
    def info(self, _title: str, _message: str) -> None:
        pass


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


@pytest.fixture
def game() -> TacticalGameState:
    ship = TacticalUnitState(
        unit_id="ship-1",
        source_entry_id="entry-1",
        profile_id=101,
        parent_unit_id=None,
        kind=UnitKind.PLATFORM,
        platform_name="Test Carrier",
        damage=TrackState.create(32, threshold=8),
        crew=TrackState.create(40, threshold=10),
        speed="12",
        turn="2/45o",
        traits=(
            TraitState("trait-jump", "Advanced Jump Engine"),
            TraitState("trait-carrier", "Carrier 2"),
            TraitState("trait-dodge", "Dodge 5+"),
        ),
        weapons=(
            WeaponState("weapon-laser", "Heavy Laser Cannon", "F", "18", "4", "Beam"),
        ),
    )
    fighter = TacticalUnitState(
        unit_id="fighter-1",
        source_entry_id="entry-1",
        profile_id=202,
        parent_unit_id="ship-1",
        kind=UnitKind.CRAFT,
        platform_name="Test Fighter",
        traits=(TraitState("fighter-dodge", "Dodge 2+"),),
        weapons=(WeaponState("fighter-gun", "Light Cannon", "T", "2", "2", "Anti-Fighter"),),
    )
    return TacticalGameState.create(
        name="Sprint 004 Battle",
        game_system_id="b5_acta_2e",
        source_fleet_id="fleet-1",
        source_fleet_name="Test Fleet",
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
        codex=SimpleNamespace(get=lambda _name: None, first_for_weapon=lambda *_args: None),
    )
    widget = TacticalAssistantPage(context)
    yield widget
    widget.close()


def test_arithmetic_editor_accepts_typed_minus_and_plus(
    page: TacticalAssistantPage,
    game: TacticalGameState,
    qapp: QApplication,
) -> None:
    page.load_game_state(game)
    editor = page.damage_editor.current_spin
    editor.setText("-8")
    editor.interpretText()
    qapp.processEvents()
    assert page.current_game.get_unit("ship-1").damage.current == 24

    editor.setText("+4")
    editor.interpretText()
    qapp.processEvents()
    assert page.current_game.get_unit("ship-1").damage.current == 28


def test_carried_fighter_status_changes_in_battle_roster(
    page: TacticalAssistantPage,
    game: TacticalGameState,
    qapp: QApplication,
) -> None:
    page.load_game_state(game)
    fighter_item = page.unit_tree.topLevelItem(0).child(0)
    combo = page.unit_tree.itemWidget(fighter_item, 2)
    assert isinstance(combo, QComboBox)
    combo.setCurrentIndex(combo.findData("launched"))
    qapp.processEvents()
    assert page.current_game.get_unit("fighter-1").effective_craft_status == "launched"

    page.unit_tree.setCurrentItem(fighter_item)
    assert page.weapon_tree.topLevelItemCount() == 1
    assert page.trait_tree.topLevelItemCount() == 1


def test_special_action_rules_display_below_selector(
    page: TacticalAssistantPage,
    game: TacticalGameState,
    qapp: QApplication,
) -> None:
    page.load_game_state(game)
    index = page.special_action_combo.findData("All Power to Engines!")
    page.special_action_combo.setCurrentIndex(index)
    qapp.processEvents()
    assert "Crew Quality Check" in page.special_action_rules_label.text()
    assert "50% Speed" in page.special_action_rules_label.text()


def test_critical_panel_roll_random_and_undo(
    page: TacticalAssistantPage,
    game: TacticalGameState,
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    page.load_game_state(game)
    index = page.critical_rule_combo.findData("vital-catastrophic-explosion")
    page.critical_rule_combo.setCurrentIndex(index)
    assert page.critical_target_combo.currentData() == "__random__"
    assert page.critical_target_combo_2.currentData() == "__random__"

    rolls = iter([13, 7])
    monkeypatch.setattr(page_module, "roll_loss_expression", lambda _expression: next(rolls))
    page.critical_damage_roll_button.click()
    page.critical_crew_roll_button.click()
    assert page.critical_damage_edit.text() == "13"
    assert page.critical_crew_edit.text() == "7"

    page.apply_critical_button.click()
    qapp.processEvents()
    updated = page.current_game.get_unit("ship-1")
    assert len(updated.critical_hits[-1].target_keys) == 2
    assert updated.damage.current == 19
    assert page.undo_critical_button.isEnabled() is True

    page.undo_critical_button.click()
    qapp.processEvents()
    restored = page.current_game.get_unit("ship-1")
    assert restored.damage.current == 32
    assert restored.crew.current == 40
    assert restored.critical_hits == ()


def test_critical_header_exposes_first_roll_chart(
    page: TacticalAssistantPage,
    game: TacticalGameState,
) -> None:
    page.load_game_state(game)
    assert "1-2  Engines" in page.critical_group.toolTip()
    assert "6     Vital Systems" in page.critical_group.toolTip()


def test_end_game_button_records_battle_report(
    page: TacticalAssistantPage,
    game: TacticalGameState,
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    page.load_game_state(game)

    class _Value:
        def __init__(self, value: int) -> None:
            self._value = value

        def value(self) -> int:
            return self._value

    class _Notes:
        def toPlainText(self) -> str:
            return "Held the field"

    class _FakeReport:
        def __init__(self, _game, _parent) -> None:
            self.victory_points_spin = _Value(15)
            self.opponent_points_spin = _Value(9)
            self.notes_edit = _Notes()

        def exec(self) -> int:
            return int(QDialog.DialogCode.Accepted)

    monkeypatch.setattr(page_module, "_BattleReportDialog", _FakeReport)
    page.end_game_button.click()
    qapp.processEvents()

    assert page.current_game.phase is GamePhase.END
    assert page.current_game.victory_points == 15
    assert page.current_game.opponent_victory_points == 9
    assert page.current_game.battle_result == "Victory"
