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
    UnitDisposition,
    UnitKind,
)
from dfs.infrastructure.tactical import JSONTacticalGameStore
from dfs.ui.tactical_assistant import TacticalAssistantPage
import dfs.ui.tactical_assistant.page as tactical_page_module


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


def _ship() -> TacticalUnitState:
    return TacticalUnitState(
        unit_id="ship-1",
        source_entry_id="entry-1",
        profile_id=1,
        parent_unit_id=None,
        kind=UnitKind.PLATFORM,
        platform_name="Test Cruiser",
        damage=TrackState.create(10, threshold=3),
        crew=TrackState.create(8, threshold=2),
    )


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


@pytest.fixture
def page(qapp: QApplication) -> TacticalAssistantPage:
    project_root = Path(__file__).resolve().parents[2]
    context = SimpleNamespace(
        tactical_games=_Files(),
        settings=_Settings(),
        resources=SimpleNamespace(project_root=project_root),
        status=SimpleNamespace(set=lambda _message: None),
        notifications=SimpleNamespace(info=lambda *_args: None),
        codex=SimpleNamespace(
            get=lambda _name: None,
            first_for_weapon=lambda *_args: None,
            all_for_weapon=lambda *_args: (),
        ),
    )
    widget = TacticalAssistantPage(context)
    widget.load_game_state(
        TacticalGameState.create(
            name="Sprint 005D",
            game_system_id="b5_acta",
            source_fleet_id="fleet",
            source_fleet_name="Fleet",
            units=(_ship(),),
        ).set_scenario("ambush")
    )
    yield widget
    widget.close()


def test_map_button_tracks_whether_the_selected_scenario_has_a_printed_map(page, qapp) -> None:
    assert page.scenario_map_button.isEnabled() is True
    assert page._scenario_map_path("ambush").is_file() is True

    page.scenario_combo.setCurrentIndex(page.scenario_combo.findData("invasion"))
    qapp.processEvents()
    assert page.scenario_map_button.isEnabled() is False


def test_map_button_opens_the_silent_deployment_map_dialog(page, qapp, monkeypatch) -> None:
    page.scenario_combo.setCurrentIndex(page.scenario_combo.findData("ambush"))
    qapp.processEvents()
    shown = []

    def _capture(dialog):
        shown.append((dialog.windowTitle(), dialog))
        return 0

    monkeypatch.setattr(tactical_page_module._ScenarioMapDialog, "exec", _capture)
    page.scenario_map_button.click()

    assert shown
    assert shown[0][0] == "Ambush - Deployment Map"


def test_damage_editor_accepts_negative_values(page, qapp) -> None:
    editor = page.damage_editor.current_spin
    editor.setText("-12")
    editor.interpretText()
    qapp.processEvents()

    assert editor.value() == -2
    assert page.current_game.get_unit("ship-1").damage.current == -2
    assert page.current_game.get_unit("ship-1").is_destroyed is False


def test_destroyed_disposition_can_be_changed_back_to_operational(page, qapp) -> None:
    destroyed_index = page.disposition_combo.findData(UnitDisposition.DESTROYED.value)
    operational_index = page.disposition_combo.findData(UnitDisposition.OPERATIONAL.value)

    page.disposition_combo.setCurrentIndex(destroyed_index)
    qapp.processEvents()
    assert page.current_game.get_unit("ship-1").is_destroyed is True

    page.disposition_combo.setCurrentIndex(operational_index)
    qapp.processEvents()
    assert page.current_game.get_unit("ship-1").is_destroyed is False
    assert page.current_game.get_unit("ship-1").disposition is UnitDisposition.OPERATIONAL
