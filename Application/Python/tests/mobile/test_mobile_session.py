from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from dfs.mobile.application import build_mobile_context
from dfs.mobile.session import MobileSession


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CANONICAL_DATABASE = REPOSITORY_ROOT / "Database" / "Data" / "dfs.db"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture()
def mobile_session(tmp_path: Path) -> MobileSession:
    return MobileSession(build_mobile_context(CANONICAL_DATABASE), tmp_path / "mobile-data")


def test_native_catalog_and_rules_use_certified_data(mobile_session: MobileSession) -> None:
    factions = mobile_session.factions()
    platforms = mobile_session.search_platforms()

    assert factions
    assert platforms
    detail = mobile_session.platform_detail(platforms[0]["shipId"])
    assert detail["name"] == platforms[0]["name"]
    assert detail["profiles"]
    assert "damage" in detail["profiles"][0]
    assert "weapons" in detail["profiles"][0]

    matches = mobile_session.search_rules("Interceptors")
    assert any(match["title"] == "Interceptors" for match in matches)
    assert all(match["text"] for match in matches)


def test_fleet_to_tactical_vertical_slice_preserves_canonical_database(
    mobile_session: MobileSession,
) -> None:
    original_hash = _sha256(CANONICAL_DATABASE)
    faction = mobile_session.factions()[0]
    fleet_list = mobile_session.fleet_lists(faction["id"])[0]

    created = mobile_session.create_fleet(
        "Android Feasibility Fleet",
        faction["id"],
        fleet_list["id"],
        "Raid",
        1,
    )
    assert created["active"] is True
    assert mobile_session.context.runtime_database_path != CANONICAL_DATABASE

    choice = next(
        profile for profile in mobile_session.available_profiles() if profile["allowed"]
    )
    fleet_state = mobile_session.add_profile(choice["profileId"])
    assert fleet_state["roster"]
    assert list(mobile_session.fleet_root.glob("*.dfs-fleet.json"))

    game_state = mobile_session.start_battle("Android Table Test")
    assert game_state["active"] is True
    assert game_state["units"]
    unit = game_state["units"][0]
    available_track = next(
        name for name in ("damage", "crew", "shields") if unit[name]["available"]
    )
    previous = unit[available_track]["current"]
    updated = mobile_session.adjust_track(unit["unitId"], available_track, -1)
    assert updated[available_track]["current"] == max(0, previous - 1)

    advanced = mobile_session.advance_turn()
    assert advanced["turn"] == game_state["turn"] + 1
    assert list(mobile_session.game_root.glob("*.dfs-game.json"))
    assert _sha256(CANONICAL_DATABASE) == original_hash
