from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QMessageBox

from dfs.domain.tactical import TacticalGameState
from dfs.infrastructure.tactical import JSONTacticalGameStore
from dfs.services.codex_service import CodexEntry
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


class _Codex:
    def get(self, _name):
        return None

    def first_for_weapon(self, _weapon, _traits):
        return None

    def all_for_weapon(self, _weapon, _traits):
        return (
            CodexEntry("Accurate", "Weapon Trait", "Accurate rule.", "Rulebook"),
            CodexEntry("Anti-Fighter", "Weapon Trait", "Anti-Fighter rule.", "Rulebook"),
            CodexEntry("Precise", "Weapon Trait", "Precise rule.", "Rulebook"),
        )


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
        codex=_Codex(),
    )
    widget = TacticalAssistantPage(context)
    widget.load_game_state(
        TacticalGameState.create(
            name="Sprint 005C",
            game_system_id="b5_acta",
            source_fleet_id="fleet",
            source_fleet_name="Fleet",
            units=(),
        )
    )
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


def test_weapon_tooltip_contains_every_printed_trait(page) -> None:
    tooltip = page._weapon_tooltip(
        "Uni-Pulse Cannon",
        "Accurate, Anti-Fighter, Precise",
    )
    assert "Accurate rule." in tooltip
    assert "Anti-Fighter rule." in tooltip
    assert "Precise rule." in tooltip


def test_disposition_is_an_active_rules_header(page) -> None:
    assert "Disposition" in page.disposition_group.title()
    assert "ⓘ" in page.disposition_group.title()
    assert "1-6 - Running Adrift" in page.disposition_group.toolTip()
    assert "18+ - Ship Explodes" in page.disposition_group.toolTip()
    assert "Rulebook, p. 9" in page.disposition_group.toolTip()


def test_active_headers_use_silent_rules_dialog(page, monkeypatch) -> None:
    shown = []

    def _unexpected_message_box(*_args, **_kwargs):
        raise AssertionError("Active rules headers must not use QMessageBox.information")

    def _capture(dialog):
        shown.append((dialog.help_title, dialog.help_text))
        return 0

    monkeypatch.setattr(QMessageBox, "information", _unexpected_message_box)
    monkeypatch.setattr(tactical_page_module._RulesDialog, "exec", _capture)

    for group in (page.scenario_group, page.critical_group, page.disposition_group):
        event = _HeaderClick()
        group.mousePressEvent(event)
        assert event.accepted is True

    assert len(shown) == 3
    assert any("Scenario" in title for title, _text in shown)
    assert any("Critical" in title for title, _text in shown)
    assert any("Damage Table" in title for title, _text in shown)
