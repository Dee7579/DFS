from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QTabWidget

from dfs.domain.tactical import (
    ATTACK_TABLE_HELP,
    DISPOSITION_DESCRIPTIONS,
    TURN_SEQUENCE_HELP,
    TacticalGameState,
    TacticalUnitState,
    TrackState,
    UnitDisposition,
    UnitKind,
    WeaponState,
)
from dfs.infrastructure.tactical import JSONTacticalGameStore
from dfs.services.codex_service import CodexService
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
def game() -> TacticalGameState:
    carrier = TacticalUnitState(
        unit_id="ship-1",
        source_entry_id="carrier-entry",
        profile_id=1,
        parent_unit_id=None,
        kind=UnitKind.PLATFORM,
        platform_name="Omega-class Destroyer",
        speed="12",
        turn="2/45o",
        hull="6",
        damage=TrackState.create(30, threshold=8),
        crew=TrackState.create(40, threshold=10),
        crew_quality="4",
        weapons=(WeaponState("laser", "Heavy Laser Cannon", "B", "30", "6", "Beam"),),
    )
    fighters = tuple(
        TacticalUnitState(
            unit_id=f"fighter-{index}",
            source_entry_id="carrier-entry",
            profile_id=2,
            parent_unit_id="ship-1",
            kind=UnitKind.CRAFT,
            platform_name="Aurora Starfury Flight",
            instance_number=index,
        )
        for index in range(1, 4)
    )
    return TacticalGameState.create(
        name="Playtest Refinements",
        game_system_id="b5_acta_2e",
        source_fleet_id="fleet-1",
        source_fleet_name="Earth Alliance",
        units=(carrier, *fighters),
    )


@pytest.fixture
def page(qapp: QApplication, tmp_path: Path, game: TacticalGameState):
    context = SimpleNamespace(
        tactical_games=_Files(),
        settings=_Settings(),
        resources=SimpleNamespace(project_root=tmp_path),
        status=SimpleNamespace(set=lambda _message: None),
        notifications=SimpleNamespace(info=lambda *_args: None),
        codex=CodexService(),
    )
    widget = TacticalAssistantPage(context)
    widget.load_game_state(game)
    yield widget
    widget.close()


def test_compact_detail_and_context_buttons_share_reference_text(page) -> None:
    assert isinstance(page.detail_tabs, QTabWidget)
    assert page.detail_tabs.count() == 3
    assert page.turn_order_button.toolTip() == TURN_SEQUENCE_HELP
    assert page.weapons_group.toolTip() == ATTACK_TABLE_HELP
    assert "ⓘ" in page.weapons_group.title()
    assert page._tooltip_filter._SHOW_TIME_MS >= 3_600_000


@pytest.mark.parametrize("width,height", ((1100, 700), (1500, 900), (1920, 1080)))
def test_compact_workspace_keeps_combat_controls_visible(
    page,
    qapp,
    width: int,
    height: int,
) -> None:
    page.resize(width, height)
    page.show()
    qapp.processEvents()

    assert page.damage_editor.isVisible()
    assert page.weapons_group.isVisible()
    assert page.status_group.isVisible()
    assert page.critical_group.isVisible()
    assert page.detail_tabs.isVisible()
    assert all(size > 0 for size in page.main_splitter.sizes())


def test_carried_fighters_are_one_compact_group_with_linked_counts(page, qapp) -> None:
    carrier = page.unit_tree.topLevelItem(0)
    assert carrier.childCount() == 1
    group = carrier.child(0)
    assert group.text(0) == "Aurora Starfury Flight x3"
    assert group.text(1) == "Carried Craft"
    assert group.childCount() == 3
    assert group.isExpanded() is False

    editor = page.unit_tree.itemWidget(group, 2)
    assert isinstance(editor, page_module._CraftGroupEditor)
    assert editor.ready_spin.value() == 3
    editor.launched_spin.setValue(1)
    qapp.processEvents()
    statuses = [
        page.current_game.get_unit(f"fighter-{index}").effective_craft_status
        for index in range(1, 4)
    ]
    assert statuses.count("ready") == 2
    assert statuses.count("launched") == 1
    assert statuses.count("lost") == 0


def test_disposition_selection_keeps_the_active_rule_visible(page, qapp) -> None:
    index = page.disposition_combo.findData(UnitDisposition.ADRIFT.value)
    assert page.disposition_combo.itemData(index, 3) == DISPOSITION_DESCRIPTIONS["adrift"]
    page.disposition_combo.setCurrentIndex(index)
    qapp.processEvents()
    assert page.disposition_description_label.text() == DISPOSITION_DESCRIPTIONS["adrift"]
    assert "current Speed" in page.disposition_description_label.text()


def test_tactical_ship_rename_updates_only_the_game_copy(page) -> None:
    page._set_unit_vessel_name("ship-1", "Agamemnon")
    unit = page.current_game.get_unit("ship-1")
    assert unit.vessel_name == "Agamemnon"
    assert unit.platform_name == "Omega-class Destroyer"
    assert page.unit_tree.topLevelItem(0).text(0) == "Agamemnon — Omega-class Destroyer"


def test_critical_multiplier_preview_and_next_turn_repair_status(page, qapp) -> None:
    page.critical_rule_combo.setCurrentIndex(
        page.critical_rule_combo.findData("engines-thrusters")
    )
    page.critical_multiplier_combo.setCurrentIndex(
        page.critical_multiplier_combo.findData(2)
    )
    qapp.processEvents()
    assert "4 Damage and 2 Crew" in page.critical_preview_label.text()

    page.apply_critical_button.click()
    qapp.processEvents()
    unit = page.current_game.get_unit("ship-1")
    assert unit.damage.current == 26
    assert unit.crew.current == 38
    assert unit.critical_hits[-1].damage_multiplier == 2
    assert page.critical_tree.topLevelItem(0).text(2) == "New"
    assert page.repair_critical_button.isEnabled() is False
    assert page.critical_multiplier_combo.currentData() == 1

    page.advance_turn_button.click()
    qapp.processEvents()
    assert page.critical_tree.topLevelItem(0).text(2) == "Repairable"
    page.critical_tree.setCurrentItem(page.critical_tree.topLevelItem(0))
    qapp.processEvents()
    assert page.repair_critical_button.isEnabled() is True


def test_quick_reference_is_modeless_and_searchable(page, qapp) -> None:
    page._show_quick_reference()
    dialog = page._quick_reference_dialog
    assert dialog is not None
    assert dialog.isModal() is False
    dialog.search_edit.setText("bulkhead")
    qapp.processEvents()
    assert dialog.entry_list.count() >= 1
    assert "Bulkhead" in dialog.detail_box.toPlainText()
    dialog.close()
