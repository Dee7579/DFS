from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from dfs.domain.tactical import TacticalGameState
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
    game = TacticalGameState.create(
        name="Scenario Controls",
        game_system_id="b5_acta",
        source_fleet_id="fleet",
        source_fleet_name="Fleet",
        units=(),
    ).set_scenario("ambush")
    widget.load_game_state(game)
    yield widget
    widget.close()


def test_scenario_summary_is_removed_from_visible_game_state(page) -> None:
    assert page.scenario_rules_label.isHidden() is True
    assert page.scenario_rules_label.parent() is not page.scenario_group


def test_scenario_header_uses_complete_rules_text(page) -> None:
    text = page.scenario_group.toolTip()
    assert "Pre-Battle Preparation:" in text
    assert "central deployment area marked on the map" in text
    assert "Victory and Defeat:" in text


def test_random_priority_button_updates_the_saved_game_state(page, qapp, monkeypatch) -> None:
    monkeypatch.setattr(tactical_page_module, "random_priority_level", lambda: "War")
    page.random_priority_button.click()
    qapp.processEvents()
    assert page.scenario_priority_combo.currentData() == "War"
    assert page.current_game.scenario_priority == "War"


def test_random_role_button_updates_the_saved_game_state(page, qapp, monkeypatch) -> None:
    monkeypatch.setattr(tactical_page_module, "random_player_role", lambda: "defender")
    page.random_role_button.click()
    qapp.processEvents()
    assert page.player_role_combo.currentData() == "defender"
    assert page.current_game.player_role == "defender"
