from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from dfs.domain.tactical import (
    TacticalGameState,
    TacticalUnitState,
    TrackState,
    UnitDisposition,
    UnitKind,
)
from dfs.infrastructure.tactical import JSONTacticalGameStore
from dfs.ui.tactical_assistant import TacticalAssistantPage
import dfs.ui.tactical_assistant.page as page_module


class _Settings:
    def get_str(self, _key: str, default: str = "") -> str:
        return default

    def set_value(self, _key: str, _value: object) -> None:
        pass

    def sync(self) -> None:
        pass


class _Files:
    FILE_EXTENSION = ".dfs-game.json"

    def __init__(self) -> None:
        self.store = JSONTacticalGameStore()

    def save(self, game, path):
        return self.store.save(game, path)

    def load(self, path):
        return self.store.load(path)


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


@pytest.fixture
def page(qapp: QApplication, tmp_path: Path) -> TacticalAssistantPage:
    context = SimpleNamespace(
        tactical_games=_Files(),
        settings=_Settings(),
        resources=SimpleNamespace(project_root=tmp_path),
        status=SimpleNamespace(set=lambda _message: None),
        notifications=SimpleNamespace(info=lambda *_args: None),
        codex=SimpleNamespace(get=lambda _name: None, first_for_weapon=lambda *_args: None),
    )
    widget = TacticalAssistantPage(context)
    yield widget
    widget.close()


@pytest.fixture
def game() -> TacticalGameState:
    ship = TacticalUnitState(
        unit_id="ship-1",
        source_entry_id="entry-ship",
        profile_id=1,
        parent_unit_id=None,
        kind=UnitKind.PLATFORM,
        platform_name="White Star",
        vessel_name="White Star One",
        priority_level="Raid",
        damage=TrackState.create(10, threshold=3),
        crew=TrackState.create(12, threshold=3),
    )
    purchased_1 = TacticalUnitState(
        unit_id="fighter-1",
        source_entry_id="entry-fighters",
        profile_id=2,
        parent_unit_id=None,
        kind=UnitKind.CRAFT,
        platform_name="Nial Heavy Fighter Flight",
        instance_number=1,
    )
    purchased_2 = TacticalUnitState(
        unit_id="fighter-2",
        source_entry_id="entry-fighters",
        profile_id=2,
        parent_unit_id=None,
        kind=UnitKind.CRAFT,
        platform_name="Nial Heavy Fighter Flight",
        instance_number=2,
    )
    return TacticalGameState.create(
        name="Sprint 005",
        game_system_id="b5_acta_2e",
        source_fleet_id="fleet",
        source_fleet_name="ISA Fleet",
        units=(ship, purchased_1, purchased_2),
    )


def test_scenario_selector_has_none_random_and_all_groups(page, game, qapp) -> None:
    page.load_game_state(game)
    assert page.scenario_combo.findData("") >= 0
    assert page.scenario_combo.findData("__random__") >= 0
    assert page.scenario_combo.findData("call-to-arms") >= 0
    assert page.scenario_combo.findData("gravity-well") >= 0
    assert page.scenario_combo.findData("battle-of-the-line") >= 0
    assert page.scenario_combo.findData("initial-contact") >= 0

    page.scenario_combo.setCurrentIndex(page.scenario_combo.findData("call-to-arms"))
    page.scenario_priority_combo.setCurrentIndex(page.scenario_priority_combo.findData("Raid"))
    qapp.processEvents()
    assert page.current_game.scenario_key == "call-to-arms"
    assert page.current_game.scenario_priority == "Raid"
    assert "Standard Victory Points" in page.scenario_rules_label.text()


def test_roster_uses_platform_name_and_groups_purchased_flights(page, game) -> None:
    page.load_game_state(game)
    assert page.unit_tree.topLevelItem(0).text(0) == "White Star"
    assert "White Star One" in page.unit_tree.topLevelItem(0).toolTip(0)
    group = page.unit_tree.topLevelItem(1)
    assert group.text(0) == "Nial Heavy Fighter Flight x2"
    assert group.childCount() == 2
    assert group.child(0).text(0) == "Nial Heavy Fighter Flight"
    assert group.child(1).text(0) == "Nial Heavy Fighter Flight #2"


def test_disposition_selector_adds_running_adrift(page, game, qapp) -> None:
    page.load_game_state(game)
    page.disposition_combo.setCurrentIndex(
        page.disposition_combo.findData(UnitDisposition.ADRIFT.value)
    )
    qapp.processEvents()
    assert page.current_game.get_unit("ship-1").is_adrift is True
    assert "Adrift" in page.unit_tree.topLevelItem(0).text(2)


def test_threshold_correction_buttons_remove_mistaken_status(
    page, game, qapp, monkeypatch
) -> None:
    crippled = game.replace_unit(game.get_unit("ship-1").set_damage_current(3))
    page.load_game_state(crippled)
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes,
    )
    page.correct_crippled_button.click()
    qapp.processEvents()
    assert page.current_game.get_unit("ship-1").is_crippled is False
    assert page.current_game.get_unit("ship-1").damage.current == 3


def test_battle_report_prefills_opponent_unit_points(page, game) -> None:
    destroyed = game.replace_unit(
        game.get_unit("ship-1").set_disposition(UnitDisposition.DESTROYED)
    ).set_scenario("call-to-arms", priority_level="Raid")
    dialog = page_module._BattleReportDialog(destroyed, page)
    try:
        assert dialog.opponent_points_spin.value() == 10
        assert "Platform ship-1" not in dialog.scoring_breakdown.toPlainText()
        assert "White Star" in dialog.scoring_breakdown.toPlainText()
    finally:
        dialog.close()
