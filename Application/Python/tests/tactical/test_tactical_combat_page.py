from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from dfs.domain.tactical import (
    TacticalGameState,
    TacticalUnitState,
    TrackState,
    TraitState,
    UnitKind,
    WeaponState,
)
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
    def set(self, _message: str) -> None:
        pass


class _Notifications:
    def info(self, _title: str, _message: str) -> None:
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
        raise AssertionError("This UI test supplies game state directly.")


class _Codex:
    def get(self, name: str):
        base = name.rsplit(" ", 1)[0] if name.rsplit(" ", 1)[-1].replace("/", "").isdigit() else name
        if base.casefold() == "interceptors":
            return SimpleNamespace(
                title="Interceptors",
                text="Neutralises incoming attacks until overwhelmed.",
                source="B5 ACTA Second Edition Rulebook, p. 18",
            )
        return None

    def first_for_weapon(self, _weapon_name: str, traits: str):
        if "Beam" in traits:
            return SimpleNamespace(
                title="Beam",
                text="Beam weapons can score continuing hits.",
                source="B5 ACTA Second Edition Rulebook, p. 20",
            )
        return None


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


@pytest.fixture
def game() -> TacticalGameState:
    unit = TacticalUnitState(
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
        speed="12",
        turn="2/45o",
        hull="5",
        troops="3",
        damage=TrackState.create(32, threshold=8),
        crew=TrackState.create(40, threshold=10),
        shields=TrackState.create(6, recovery="2"),
        crew_quality="4",
        traits=(
            TraitState("trait-interceptors", "Interceptors 2"),
            TraitState("trait-jump", "Jump Engine"),
        ),
        weapons=(
            WeaponState("weapon-laser", "Heavy Laser Cannon", "B", "18", "4", "Beam, Double Damage"),
            WeaponState("weapon-pulse", "Pulse Cannon", "F", "10", "6", "Twin-Linked"),
        ),
    )
    return TacticalGameState.create(
        name="Combat UI Battle",
        game_system_id="b5_acta_2e",
        source_fleet_id="fleet-1",
        source_fleet_name="Combat UI Fleet",
        units=(unit,),
    )


@pytest.fixture
def page(qapp: QApplication, tmp_path: Path) -> TacticalAssistantPage:
    context = SimpleNamespace(
        tactical_games=_TacticalFiles(),
        settings=_Settings(),
        resources=SimpleNamespace(project_root=tmp_path),
        status=_Status(),
        notifications=_Notifications(),
        codex=_Codex(),
    )
    widget = TacticalAssistantPage(context)
    yield widget
    widget.close()


def test_game_state_and_battle_roster_share_left_column(
    page: TacticalAssistantPage,
    game: TacticalGameState,
) -> None:
    page.load_game_state(game)
    assert page.game_state_group.parentWidget() is page.roster_group.parentWidget()
    assert page.game_state_group.width() == page.roster_group.width()


def test_track_editor_accepts_relative_arithmetic(
    page: TacticalAssistantPage,
    game: TacticalGameState,
    qapp: QApplication,
) -> None:
    page.load_game_state(game)
    spin = page.damage_editor.current_spin
    spin.lineEdit().setText("-8")
    spin.interpretText()
    qapp.processEvents()
    assert page.current_game.get_unit("ship-1").damage.current == 24


def test_thresholds_recalculate_speed_turn_and_mark_modified_values_red(
    page: TacticalAssistantPage,
    game: TacticalGameState,
    qapp: QApplication,
) -> None:
    page.load_game_state(game)
    page.damage_editor.current_spin.setValue(8)
    qapp.processEvents()

    unit = page.current_game.get_unit("ship-1")
    assert unit.is_crippled is True
    assert unit.effective_speed == "6"
    assert unit.effective_turn == "1/45°"
    assert "#c62828" in page.unit_reference_label.text()
    assert "Original Speed: 12" in page.unit_reference_label.toolTip()
    assert page.shields_editor.current_spin.isEnabled() is False


def test_special_action_box_is_populated_and_explains_unavailable_actions(
    page: TacticalAssistantPage,
    game: TacticalGameState,
) -> None:
    page.load_game_state(game)
    assert page.special_action_combo.count() >= 16
    jump_index = page.special_action_combo.findData("Initiate Jump Point!")
    assert jump_index >= 0
    assert page.special_action_combo.model().item(jump_index).isEnabled() is True

    ramming_index = page.special_action_combo.findData("Give Me Ramming Speed!")
    assert ramming_index >= 0
    assert page.special_action_combo.model().item(ramming_index).isEnabled() is False
    assert "Only a Crippled ship" in str(
        page.special_action_combo.itemData(ramming_index, 3)
    )


def test_weapons_and_traits_have_rule_tooltips_and_state_controls(
    page: TacticalAssistantPage,
    game: TacticalGameState,
    qapp: QApplication,
) -> None:
    page.load_game_state(game)

    weapon_item = page.weapon_tree.topLevelItem(0)
    assert "Beam weapons" in weapon_item.toolTip(1)
    page.weapon_tree.setCurrentItem(weapon_item)
    page.weapon_destroy_button.click()
    qapp.processEvents()
    unit = page.current_game.get_unit("ship-1")
    assert unit.weapon_status("weapon-laser") == "Destroyed"
    assert page.weapon_tree.topLevelItem(0).font(1).strikeOut() is True

    trait_item = page.trait_tree.topLevelItem(0)
    assert "Neutralises incoming attacks" in trait_item.toolTip(0)
    page.trait_tree.setCurrentItem(trait_item)
    page.trait_disable_button.click()
    qapp.processEvents()
    unit = page.current_game.get_unit("ship-1")
    assert unit.trait_status("trait-interceptors") == "Disabled"
    assert page.trait_tree.topLevelItem(0).font(0).strikeOut() is True


def test_critical_dropdown_applies_losses_and_effective_stat_change(
    page: TacticalAssistantPage,
    game: TacticalGameState,
    qapp: QApplication,
) -> None:
    page.load_game_state(game)
    index = page.critical_rule_combo.findData("engines-thrusters")
    page.critical_rule_combo.setCurrentIndex(index)
    page.apply_critical_button.click()
    qapp.processEvents()

    unit = page.current_game.get_unit("ship-1")
    assert unit.damage.current == 31
    assert unit.crew.current == 40
    assert unit.effective_speed == "10"
    assert len(unit.active_critical_hits) == 1
    assert page.critical_tree.topLevelItemCount() == 1
    assert "#c62828" in page.unit_reference_label.text()
