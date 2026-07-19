from dfs.domain.fleet.priority import single_point_patterns, validate_priority_budget


def test_pnp_raid_breakdowns_are_exact():
    patterns = single_point_patterns("Raid")
    assert {"Skirmish": 2} in patterns
    assert {"Skirmish": 1, "Patrol": 2} in patterns
    assert {"Patrol": 3} in patterns
    assert {"Patrol": 4} not in patterns


def test_pnp_battle_mixed_breakdown():
    result = validate_priority_budget(
        "Battle", 1, {"Raid": 1, "Skirmish": 1, "Patrol": 2}
    )
    assert result.valid


def test_cannot_split_both_branches_for_extra_ships():
    # P&P permits five Patrol from one Battle point, not six.
    assert not validate_priority_budget("Battle", 1, {"Patrol": 6}).valid


def test_multiple_fap_can_use_different_legal_breakdowns():
    result = validate_priority_budget(
        "Raid", 2, {"Skirmish": 3, "Patrol": 2}
    )
    assert result.valid


def test_higher_priority_costs_follow_pnp_table():
    assert validate_priority_budget("Patrol", 16, {"War": 1}).valid
    assert not validate_priority_budget("Patrol", 15, {"War": 1}).valid
    assert validate_priority_budget("Patrol", 32, {"Armageddon": 1}).valid


def test_unused_split_choices_may_be_discarded():
    result = validate_priority_budget("Raid", 1, {"Patrol": 1})
    assert result.valid
    assert result.minimum_fap_required == 1
    assert result.remaining_fap == 0


def test_remaining_fap_is_reported():
    result = validate_priority_budget("Raid", 3, {"Raid": 1})
    assert result.valid
    assert result.minimum_fap_required == 1
    assert result.remaining_fap == 2


def test_exceeded_fap_is_reported():
    result = validate_priority_budget("Raid", 1, {"Battle": 1})
    assert not result.valid
    assert result.exceeded_by_fap == 1


def test_remaining_choices_after_one_war_from_armageddon():
    from dfs.domain.fleet.priority import affordable_priority_quantities, format_remaining_choices

    choices = affordable_priority_quantities("Armageddon", 1, {"War": 1})
    assert choices["War"] == 1
    assert choices["Battle"] == 2
    assert choices["Raid"] == 3
    assert "1 War choice" in format_remaining_choices("Armageddon", 1, {"War": 1})


def test_cannot_add_above_scenario_priority():
    from dfs.domain.fleet.priority import can_add_priority

    assert not can_add_priority("War", 1, {}, "Armageddon")
    assert can_add_priority("War", 1, {}, "War")
