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
    yield widget
    widget.close()


class _HeaderPosition:
    @staticmethod
    def y() -> int:
        return 10


class _HeaderClick:
    accepted = False

    @staticmethod
    def position() -> _HeaderPosition:
        return _HeaderPosition()

    def accept(self) -> None:
        self.accepted = True


def test_scenario_and_critical_titles_are_visibly_interactive(page, qapp) -> None:
    game = TacticalGameState.create(
        name="Header Test",
        game_system_id="b5_acta",
        source_fleet_id="fleet",
        source_fleet_name="Fleet",
        units=(),
    )
    page.load_game_state(game)
    assert "ⓘ" in page.scenario_group.title()
    assert "ⓘ" in page.critical_group.title()
    assert "palette(highlight)" in page.scenario_group.styleSheet()
    assert "palette(highlight)" in page.critical_group.styleSheet()


def test_scenario_header_hover_and_click_use_selected_scenario_rules(
    page, qapp, monkeypatch
) -> None:
    game = TacticalGameState.create(
        name="Scenario Header Test",
        game_system_id="b5_acta",
        source_fleet_id="fleet",
        source_fleet_name="Fleet",
        units=(),
    )
    page.load_game_state(game)
    page.scenario_combo.setCurrentIndex(page.scenario_combo.findData("call-to-arms"))
    qapp.processEvents()

    assert "Victory and Defeat:" in page.scenario_group.toolTip()
    assert "Call to Arms" in page.scenario_group._help_title

    shown: dict[str, str] = {}

    def _capture(dialog):
        shown["title"] = dialog.help_title
        shown["text"] = dialog.help_text
        return 0

    monkeypatch.setattr(tactical_page_module._RulesDialog, "exec", _capture)
    event = _HeaderClick()
    page.scenario_group.mousePressEvent(event)
    assert event.accepted is True
    assert "Call to Arms" in shown["title"]
    assert "Victory and Defeat:" in shown["text"]
