from __future__ import annotations

from pathlib import Path
import random

from dfs.domain.tactical import (
    SCENARIOS,
    SCENARIO_BY_KEY,
    TacticalGameState,
    TacticalUnitState,
    TrackState,
    TraitState,
    UnitDisposition,
    UnitKind,
    destroyed_victory_points,
    opponent_victory_points_from_local_fleet,
    random_scenario,
)
from dfs.infrastructure.tactical import JSONTacticalGameStore


def _ship(
    unit_id: str,
    *,
    priority: str = "Raid",
    damage: int = 30,
    crippled: int = 8,
    crew: int = 30,
    skeleton: int = 8,
) -> TacticalUnitState:
    return TacticalUnitState(
        unit_id=unit_id,
        source_entry_id=f"entry-{unit_id}",
        profile_id=1,
        parent_unit_id=None,
        kind=UnitKind.PLATFORM,
        platform_name=f"Platform {unit_id}",
        priority_level=priority,
        damage=TrackState.create(damage, threshold=crippled),
        crew=TrackState.create(crew, threshold=skeleton),
    )


def _game(*units: TacticalUnitState) -> TacticalGameState:
    return TacticalGameState.create(
        name="Scenario Test",
        game_system_id="b5_acta_2e",
        source_fleet_id="fleet-1",
        source_fleet_name="Test Fleet",
        units=tuple(units),
    ).set_scenario("call-to-arms", priority_level="Raid", player_role="attacker")


def test_scenario_catalog_contains_rulebook_pp_and_tournament_groups() -> None:
    names = {scenario.name for scenario in SCENARIOS}
    assert {
        "Ambush",
        "Call to Arms",
        "Supply Ships",
        "Gravity Well",
        "Towering Inferno",
        "Battle of the Line",
        "Between the Darkness and the Light",
        "Initial Contact",
        "Shadows of the Past",
    } <= names
    categories = {scenario.category for scenario in SCENARIOS}
    assert "Rulebook - Standard" in categories
    assert "Rulebook - Historical" in categories
    assert "P&P - Standard" in categories
    assert "P&P - Deep Space Tournament" in categories


def test_random_scenario_uses_only_normal_random_eligible_scenarios() -> None:
    for seed in range(30):
        selected = random_scenario(random.Random(seed))
        assert selected.random_eligible is True
        assert "Historical" not in selected.category
        assert "Tournament" not in selected.category


def test_destroyed_victory_point_table_matches_priority_differences() -> None:
    assert destroyed_victory_points("Raid", "Raid") == 10
    assert destroyed_victory_points("Battle", "Raid") == 20
    assert destroyed_victory_points("War", "Raid") == 30
    assert destroyed_victory_points("Skirmish", "Raid") == 5
    assert destroyed_victory_points("Patrol", "Raid") == 3


def test_opponent_scoring_uses_highest_applicable_platform_status() -> None:
    destroyed = _ship("destroyed").set_disposition(UnitDisposition.DESTROYED)
    surrendered = _ship("surrendered").set_disposition(UnitDisposition.SURRENDERED)
    withdrawn = _ship("withdrawn").set_disposition(UnitDisposition.WITHDRAWN)
    crippled = _ship("crippled").set_damage_current(8)
    summary = opponent_victory_points_from_local_fleet(
        _game(destroyed, surrendered, withdrawn, crippled)
    )
    assert summary.automatic_points == 10 + 20 + 3 + 3
    reasons = {entry.unit_id: entry.reason for entry in summary.entries}
    assert reasons["destroyed"] == "Destroyed"
    assert reasons["surrendered"] == "Surrendered"
    assert reasons["withdrawn"] == "Tactical Withdrawal"
    assert reasons["crippled"] == "Crippled"


def test_running_adrift_counts_as_destroyed_for_victory_points() -> None:
    adrift = _ship("adrift").set_disposition(UnitDisposition.ADRIFT)
    summary = opponent_victory_points_from_local_fleet(_game(adrift))
    assert summary.automatic_points == 10
    assert summary.entries[0].reason.startswith("Running Adrift")


def test_only_independently_purchased_destroyed_fighters_score() -> None:
    purchased = TacticalUnitState(
        unit_id="fighter-purchased",
        source_entry_id="entry-fighters",
        profile_id=2,
        parent_unit_id=None,
        kind=UnitKind.CRAFT,
        platform_name="Aurora Starfury Flight",
    ).set_disposition(UnitDisposition.DESTROYED)
    carried = TacticalUnitState(
        unit_id="fighter-carried",
        source_entry_id="entry-carrier",
        profile_id=2,
        parent_unit_id="carrier",
        kind=UnitKind.CRAFT,
        platform_name="Aurora Starfury Flight",
    ).set_disposition(UnitDisposition.DESTROYED)
    carrier = _ship("carrier")
    summary = opponent_victory_points_from_local_fleet(_game(carrier, purchased, carried))
    assert summary.automatic_points == 1
    assert summary.entries[0].unit_id == "fighter-purchased"


def test_threshold_status_can_be_corrected_without_changing_track_value() -> None:
    unit = _ship("correction").set_damage_current(8).set_crew_current(8)
    assert unit.is_crippled is True
    assert unit.is_skeleton_crew is True
    corrected = unit.correct_crippled_status().correct_skeleton_crew_status()
    assert corrected.damage.current == 8
    assert corrected.crew.current == 8
    assert corrected.is_crippled is False
    assert corrected.is_skeleton_crew is False


def test_threshold_correction_resets_after_recovery_and_new_crossing() -> None:
    unit = _ship("crossing").set_damage_current(8).correct_crippled_status()
    unit = unit.set_damage_current(12)
    assert unit.is_crippled is False
    unit = unit.set_damage_current(8)
    assert unit.is_crippled is True


def test_ambush_defender_does_not_score_attacker_withdrawals() -> None:
    withdrawn = _ship("withdrawn").set_disposition(UnitDisposition.WITHDRAWN)
    game = TacticalGameState.create(
        name="Ambush",
        game_system_id="b5_acta_2e",
        source_fleet_id="fleet",
        source_fleet_name="Ambusher",
        units=(withdrawn,),
    ).set_scenario("ambush", priority_level="Raid", player_role="attacker")
    assert opponent_victory_points_from_local_fleet(game).automatic_points == 0


def test_sprint_005_fields_round_trip_in_game_json(tmp_path: Path) -> None:
    unit = (
        _ship("roundtrip")
        .set_damage_current(8)
        .correct_crippled_status()
        .set_disposition(UnitDisposition.ADRIFT)
    )
    game = _game(unit).set_scenario_objectives({"opponent_bonus": 5})
    target = tmp_path / "scenario.dfs-game.json"
    store = JSONTacticalGameStore()
    store.save(game, target)
    loaded = store.load(target)
    restored = loaded.get_unit("roundtrip")
    assert loaded.scenario_key == "call-to-arms"
    assert loaded.scenario_priority == "Raid"
    assert loaded.player_role == "attacker"
    assert loaded.scenario_objectives == {"opponent_bonus": 5}
    assert restored.disposition is UnitDisposition.ADRIFT
    assert restored.crippled_correction is True
    assert restored.is_crippled is False
