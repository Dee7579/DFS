from __future__ import annotations

import random

from dfs.domain.tactical import (
    SCENARIOS,
    SCENARIO_BY_KEY,
    random_player_role,
    random_priority_level,
)


def test_every_scenario_has_complete_player_facing_rules_text() -> None:
    for scenario in SCENARIOS:
        text = scenario.display_text
        assert text.startswith("Source:"), scenario.key
        assert "Pre-Battle Preparation:" in text, scenario.key
        assert "Scenario Rules:" in text, scenario.key
        assert "Game Length:" in text, scenario.key
        assert ("Victory and Defeat:" in text or "Battle Grades:" in text), scenario.key
        assert len(text) > 350, scenario.key


def test_ambush_help_contains_the_full_published_setup_not_the_old_summary() -> None:
    text = SCENARIO_BY_KEY["ambush"].display_text
    assert "central deployment area marked on the map" in text
    assert "place stellar debris how he wishes" in text
    assert "Crew Quality check (target number 10)" in text
    assert "does not gain Victory Points for enemy ships that tactically withdraw" in text


def test_catalog_includes_the_two_remaining_rulebook_scenarios() -> None:
    assert SCENARIO_BY_KEY["border-dispute"].name == "Border Dispute"
    assert SCENARIO_BY_KEY["hunting-the-hunters"].name == "Hunting the Hunters"


def test_random_priority_uses_the_published_2d6_table() -> None:
    class _Rolls:
        def __init__(self, *values: int) -> None:
            self.values = iter(values)

        def randint(self, _minimum: int, _maximum: int) -> int:
            return next(self.values)

    assert random_priority_level(_Rolls(1, 1)) == "Patrol"
    assert random_priority_level(_Rolls(2, 3)) == "Skirmish"
    assert random_priority_level(_Rolls(3, 4)) == "Raid"
    assert random_priority_level(_Rolls(5, 5)) == "Battle"
    assert random_priority_level(_Rolls(6, 6)) == "War"


def test_random_player_role_only_returns_valid_roles() -> None:
    roles = {random_player_role(random.Random(seed)) for seed in range(20)}
    assert roles == {"attacker", "defender"}
