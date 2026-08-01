"""Qt/QML adapter for :class:`dfs.mobile.session.MobileSession`."""

from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import QObject, Property, Signal, Slot

from dfs.mobile.session import MobileSession


class MobileController(QObject):
    factionsChanged = Signal()
    fleetListsChanged = Signal()
    platformsChanged = Signal()
    selectedPlatformChanged = Signal()
    availableProfilesChanged = Signal()
    fleetStateChanged = Signal()
    gameStateChanged = Signal()
    selectedUnitChanged = Signal()
    rulesChanged = Signal()
    messageChanged = Signal()
    errorChanged = Signal()

    def __init__(self, session: MobileSession) -> None:
        super().__init__()
        self._session = session
        self._factions: list[dict[str, Any]] = []
        self._fleet_lists: list[dict[str, Any]] = []
        self._platforms: list[dict[str, Any]] = []
        self._selected_platform: dict[str, Any] = {}
        self._available_profiles: list[dict[str, Any]] = []
        self._fleet_state: dict[str, Any] = session.fleet_state()
        self._game_state: dict[str, Any] = session.game_state()
        self._selected_unit: dict[str, Any] = {}
        self._rules: list[dict[str, Any]] = []
        self._message = ""
        self._error = ""
        self._fleet_query = ""
        self._load_initial_state()

    def _load_initial_state(self) -> None:
        self._perform(
            lambda: self._assign_list(
                "_factions",
                self._session.factions(),
                self.factionsChanged,
            ),
            success="Certified DFS data loaded",
        )
        self.searchPlatforms("", 0)

    @Property("QVariantList", notify=factionsChanged)
    def factions(self):
        return self._factions

    @Property("QVariantList", notify=fleetListsChanged)
    def fleetLists(self):
        return self._fleet_lists

    @Property("QVariantList", notify=platformsChanged)
    def platforms(self):
        return self._platforms

    @Property("QVariantMap", notify=selectedPlatformChanged)
    def selectedPlatform(self):
        return self._selected_platform

    @Property("QVariantList", notify=availableProfilesChanged)
    def availableProfiles(self):
        return self._available_profiles

    @Property("QVariantMap", notify=fleetStateChanged)
    def fleetState(self):
        return self._fleet_state

    @Property("QVariantMap", notify=gameStateChanged)
    def gameState(self):
        return self._game_state

    @Property("QVariantMap", notify=selectedUnitChanged)
    def selectedUnit(self):
        return self._selected_unit

    @Property("QVariantList", notify=rulesChanged)
    def rules(self):
        return self._rules

    @Property(str, notify=messageChanged)
    def message(self) -> str:
        return self._message

    @Property(str, notify=errorChanged)
    def error(self) -> str:
        return self._error

    def _set_message(self, value: str) -> None:
        if self._message == value:
            return
        self._message = value
        self.messageChanged.emit()

    def _set_error(self, value: str) -> None:
        if self._error == value:
            return
        self._error = value
        self.errorChanged.emit()

    def _assign_list(self, attribute: str, value: list, signal: Signal) -> None:
        setattr(self, attribute, value)
        signal.emit()

    def _assign_map(self, attribute: str, value: dict, signal: Signal) -> None:
        setattr(self, attribute, value)
        signal.emit()

    def _perform(self, action: Callable[[], Any], *, success: str = "") -> Any:
        try:
            result = action()
        except Exception as exc:  # UI boundary: surface domain errors to the user.
            self._set_error(str(exc))
            return None
        self._set_error("")
        if success:
            self._set_message(success)
        return result

    @Slot()
    def clearError(self) -> None:
        self._set_error("")

    @Slot(int)
    def loadFleetLists(self, faction_id: int) -> None:
        def action() -> None:
            values = self._session.fleet_lists(int(faction_id)) if faction_id else []
            self._assign_list("_fleet_lists", values, self.fleetListsChanged)

        self._perform(action)

    @Slot(str, int)
    def searchPlatforms(self, query: str, faction_id: int = 0) -> None:
        def action() -> None:
            values = self._session.search_platforms(query, faction_id or None)
            self._assign_list("_platforms", values, self.platformsChanged)

        self._perform(action)

    @Slot(int)
    def selectPlatform(self, ship_id: int) -> None:
        def action() -> None:
            value = self._session.platform_detail(int(ship_id))
            self._assign_map("_selected_platform", value, self.selectedPlatformChanged)

        self._perform(action)

    @Slot(str, int, int, str, int, int)
    def createFleet(
        self,
        name: str,
        faction_id: int,
        fleet_list_id: int,
        scenario_priority: str,
        fleet_allocation_points: int,
        selected_year: int,
    ) -> None:
        def action() -> None:
            value = self._session.create_fleet(
                name,
                faction_id,
                fleet_list_id,
                scenario_priority,
                fleet_allocation_points,
                selected_year or None,
            )
            self._assign_map("_fleet_state", value, self.fleetStateChanged)
            self._refresh_available()
            self._assign_map("_game_state", self._session.game_state(), self.gameStateChanged)
            self._assign_map("_selected_unit", {}, self.selectedUnitChanged)

        self._perform(action, success="New fleet created and saved")

    def _refresh_available(self) -> None:
        values = self._session.available_profiles(self._fleet_query)
        self._assign_list("_available_profiles", values, self.availableProfilesChanged)

    @Slot(str)
    def searchFleetProfiles(self, query: str) -> None:
        self._fleet_query = query
        self._perform(self._refresh_available)

    @Slot(int)
    def addProfile(self, profile_id: int) -> None:
        def action() -> None:
            value = self._session.add_profile(int(profile_id))
            self._assign_map("_fleet_state", value, self.fleetStateChanged)
            self._refresh_available()

        self._perform(action, success="Platform added to fleet")

    @Slot(str)
    def removeEntry(self, entry_id: str) -> None:
        def action() -> None:
            value = self._session.remove_entry(entry_id)
            self._assign_map("_fleet_state", value, self.fleetStateChanged)
            self._refresh_available()

        self._perform(action, success="Platform removed from fleet")

    @Slot(str)
    def startBattle(self, name: str = "") -> None:
        def action() -> None:
            value = self._session.start_battle(name)
            self._assign_map("_game_state", value, self.gameStateChanged)
            units = value.get("units", [])
            selected = units[0] if units else {}
            self._assign_map("_selected_unit", selected, self.selectedUnitChanged)

        self._perform(action, success="Tactical game started and saved")

    @Slot(str)
    def selectUnit(self, unit_id: str) -> None:
        def action() -> None:
            value = self._session.unit_detail(unit_id)
            self._assign_map("_selected_unit", value, self.selectedUnitChanged)

        self._perform(action)

    @Slot(str, str, int)
    def adjustTrack(self, unit_id: str, track_name: str, delta: int) -> None:
        def action() -> None:
            value = self._session.adjust_track(unit_id, track_name, delta)
            self._assign_map("_selected_unit", value, self.selectedUnitChanged)
            self._assign_map("_game_state", self._session.game_state(), self.gameStateChanged)

        self._perform(action, success=f"{track_name.title()} updated")

    @Slot(str, bool)
    def setDestroyed(self, unit_id: str, destroyed: bool) -> None:
        def action() -> None:
            value = self._session.set_destroyed(unit_id, destroyed)
            self._assign_map("_selected_unit", value, self.selectedUnitChanged)
            self._assign_map("_game_state", self._session.game_state(), self.gameStateChanged)

        self._perform(action, success="Unit status updated")

    @Slot()
    def advanceTurn(self) -> None:
        def action() -> None:
            value = self._session.advance_turn()
            self._assign_map("_game_state", value, self.gameStateChanged)
            selected_id = str(self._selected_unit.get("unitId", ""))
            if selected_id:
                self._assign_map(
                    "_selected_unit",
                    self._session.unit_detail(selected_id),
                    self.selectedUnitChanged,
                )

        self._perform(action, success="Advanced to the next turn")

    @Slot(str)
    def searchRules(self, query: str) -> None:
        def action() -> None:
            self._assign_list(
                "_rules",
                self._session.search_rules(query),
                self.rulesChanged,
            )

        self._perform(action)
