from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication, QScrollArea, QTabWidget

from dfs.domain.tactical import (
    ATTACK_TABLE_HELP,
    DISPOSITION_DESCRIPTIONS,
    TURN_SEQUENCE_HELP,
    TacticalGameState,
    TacticalUnitState,
    TrackState,
    TraitState,
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
        traits=tuple(
            TraitState(f"trait-{index}", name)
            for index, name in enumerate(
                (
                    "Advanced Jump Engine",
                    "Anti-Fighter 2",
                    "Carrier 2",
                    "Command +1",
                    "Interceptors 4",
                    "Lumbering",
                    "Shields 6/1",
                ),
                start=1,
            )
        ),
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
    assert page.detail_tabs.count() == 2
    assert page.detail_tabs.tabText(0) == "Source Notes"
    assert page.detail_tabs.tabText(1) == "Unit Notes"
    assert page.turn_order_button.toolTip() == TURN_SEQUENCE_HELP
    assert page.weapons_group.toolTip() == ATTACK_TABLE_HELP
    assert "ⓘ" in page.weapons_group.title()
    assert page._tooltip_filter._SHOW_TIME_MS >= 3_600_000


@pytest.mark.parametrize("width,height", ((1100, 700), (1500, 900), (1920, 1080)))
def test_scrollable_workspace_keeps_combat_controls_visible(
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
    assert isinstance(page.detail_scroll, QScrollArea)
    assert page.detail_scroll.widget() is page.unit_detail_widget
    assert page.detail_scroll.horizontalScrollBar().maximum() == 0
    assert page._detail_groups_stacked is (
        page.detail_scroll.viewport().width() < 760
    )
    assert all(size > 0 for size in page.main_splitter.sizes())


def test_detail_forms_keep_natural_height_without_overlapping(page, qapp) -> None:
    page.resize(1500, 900)
    page.show()
    qapp.processEvents()

    def vertical_span(widget) -> tuple[int, int]:
        top = widget.mapTo(page, QPoint(0, 0)).y()
        return top, top + widget.height()

    def assert_separate(widgets) -> None:
        spans = [vertical_span(widget) for widget in widgets if widget.isVisible()]
        assert all(upper[1] <= lower[0] for upper, lower in zip(spans, spans[1:]))

    def assert_forms_do_not_overlap() -> None:
        assert_separate(
            (
                page.disposition_combo,
                page.disposition_description_label,
                page.crew_quality_edit,
                page.special_action_combo,
                page.special_action_rules_label,
                page.threshold_status_label,
                page.correct_crippled_button,
                page.damage_control_label,
            )
        )
        assert_separate(
            (
                page.critical_rule_combo,
                page.critical_damage_edit,
                page.critical_target_combo,
                page.critical_preview_label,
                page.critical_multiplier_combo,
                page.critical_tree,
                page.repair_critical_button,
            )
        )

    assert_forms_do_not_overlap()

    craft_item = page.unit_tree.topLevelItem(0).child(0).child(0)
    page.unit_tree.setCurrentItem(craft_item)
    qapp.processEvents()
    assert_forms_do_not_overlap()

    # The normal 900-pixel workspace may scroll, but the forms must never be
    # forced shorter than their layout minimum just to keep every section in view.
    assert page.detail_scroll.verticalScrollBar().maximum() > 0


def test_traits_are_full_width_auto_sized_and_responsive(page, qapp) -> None:
    page.resize(1500, 900)
    page.show()
    qapp.processEvents()

    assert page._traits_two_column is True
    assert page.trait_tree.columnCount() == 4
    assert page.trait_tree.topLevelItemCount() == 4
    assert page.trait_tree.verticalScrollBar().maximum() == 0
    assert page.trait_tree.viewport().height() >= (
        page.trait_tree.visualItemRect(page.trait_tree.topLevelItem(3)).bottom()
    )
    assert page.traits_group.mapTo(page, QPoint(0, 0)).y() < (
        page.status_and_critical_widget.mapTo(page, QPoint(0, 0)).y()
    )

    second_column_item = page.trait_tree.topLevelItem(0)
    page.trait_tree.setCurrentItem(second_column_item, 2)
    page.trait_disable_button.click()
    qapp.processEvents()
    selected_unit = page.current_game.get_unit("ship-1")
    second_trait = next(
        trait for trait in selected_unit.traits if trait.trait_key == "trait-2"
    )
    assert second_trait.disabled is True

    page.resize(1100, 700)
    qapp.processEvents()
    assert page._traits_two_column is False
    assert page.trait_tree.columnCount() == 2
    assert page.trait_tree.topLevelItemCount() == 7
    assert page.trait_tree.verticalScrollBar().maximum() == 0


def test_header_is_single_line_at_desktop_width_and_wraps_safely(page, qapp) -> None:
    page.resize(1500, 900)
    page.show()
    qapp.processEvents()

    assert page._header_wrapped is False
    title_center = page.page_title.mapTo(page, page.page_title.rect().center()).y()
    action_center = page.new_from_fleet_button.mapTo(
        page,
        page.new_from_fleet_button.rect().center(),
    ).y()
    assert abs(title_center - action_center) <= 4

    page.resize(1100, 700)
    qapp.processEvents()
    assert page._header_wrapped is True
    assert page.new_from_fleet_button.mapTo(page, QPoint(0, 0)).y() > (
        page.page_title.mapTo(page, QPoint(0, 0)).y()
    )


def test_carried_fighters_are_one_compact_group_with_linked_counts(page, qapp) -> None:
    carrier = page.unit_tree.topLevelItem(0)
    assert carrier.childCount() == 1
    group = carrier.child(0)
    assert group.text(0) == "Aurora Starfury Flight x3"
    assert group.text(1) == "Carried Craft"
    assert group.childCount() == 3
    assert group.isExpanded() is False

    ready = page.unit_tree.itemWidget(group, 3)
    launched = page.unit_tree.itemWidget(group, 4)
    lost = page.unit_tree.itemWidget(group, 5)
    assert isinstance(ready, page_module._CraftCountEditor)
    assert isinstance(launched, page_module._CraftCountEditor)
    assert isinstance(lost, page_module._CraftCountEditor)
    assert page.unit_tree.columnWidth(4) >= page.unit_tree.header().sectionSizeHint(4)
    assert ready.value() == 3
    assert launched.value() == 0
    assert lost.value() == 0
    assert ready.value_label.text() == "3"
    launched.increment_button.click()
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
