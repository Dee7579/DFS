from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from dfs.domain.tactical import TacticalGameState, TacticalUnitState, TraitState, UnitKind
from dfs.infrastructure.tactical import JSONTacticalGameStore
from dfs.ui.tactical_assistant import TacticalAssistantPage


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


def test_fighter_header_displays_dogfight_and_dodge() -> None:
    app = QApplication.instance() or QApplication([])
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
    fighter = TacticalUnitState(
        unit_id="fighter-1",
        source_entry_id="entry-1",
        profile_id=1,
        parent_unit_id=None,
        kind=UnitKind.CRAFT,
        platform_name="White Star Fighter",
        priority_level="Patrol",
        initiative="+2",
        speed="16",
        turn="SM",
        hull="5",
        troops="-",
        source_notes=("Dogfight: +3", "Wing of Two Flights"),
        traits=(TraitState("dodge", "Dodge 2+"), TraitState("fighter", "Fighter")),
    )
    game = TacticalGameState.create(
        name="Fighter Header",
        game_system_id="b5_acta",
        source_fleet_id="fleet",
        source_fleet_name="Fleet",
        units=(fighter,),
    )
    page = TacticalAssistantPage(context)
    try:
        page.load_game_state(game)
        app.processEvents()
        header = page.unit_reference_label.text()
        assert "<b>Dogfight</b> +3" in header
        assert "<b>Dodge</b> 2+" in header
    finally:
        page.close()
