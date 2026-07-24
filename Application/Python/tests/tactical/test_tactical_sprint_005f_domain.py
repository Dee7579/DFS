from __future__ import annotations

from dfs.domain.tactical.models import TacticalUnitState, TraitState, UnitKind
from dfs.domain.tactical.reference_stats import fighter_reference_stats


def _unit(*, kind: UnitKind, notes=(), traits=()) -> TacticalUnitState:
    return TacticalUnitState(
        unit_id="unit-1",
        source_entry_id="entry-1",
        profile_id=1,
        parent_unit_id=None,
        kind=kind,
        platform_name="Test Unit",
        source_notes=tuple(notes),
        traits=tuple(traits),
    )


def test_fighter_reference_stats_extracts_colon_dogfight_and_dodge() -> None:
    unit = _unit(
        kind=UnitKind.CRAFT,
        notes=("Dogfight: +3", "Wing of Four Flights"),
        traits=(TraitState("dodge", "Dodge 2+"), TraitState("fighter", "Fighter")),
    )

    assert fighter_reference_stats(unit) == (("Dogfight", "+3"), ("Dodge", "2+"))


def test_fighter_reference_stats_accepts_legacy_dogfight_format() -> None:
    unit = _unit(
        kind=UnitKind.CRAFT,
        notes=("Dogfight +1",),
        traits=(TraitState("dodge", "Dodge 3+"),),
    )

    assert fighter_reference_stats(unit) == (("Dogfight", "+1"), ("Dodge", "3+"))


def test_ship_reference_stats_do_not_gain_fighter_fields() -> None:
    unit = _unit(
        kind=UnitKind.PLATFORM,
        notes=("Dogfight: +2",),
        traits=(TraitState("dodge", "Dodge 2+"),),
    )

    assert fighter_reference_stats(unit) == ()
