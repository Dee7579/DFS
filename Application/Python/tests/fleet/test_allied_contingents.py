from dfs.domain.catalog import PlatformProfile
from dfs.domain.fleet.models import Fleet, FleetEntry
from dfs.services.fleet.b5_acta_rules import build_b5_acta_core_rule_engine


def profile(pid, list_id, name, priority="Raid"):
    return PlatformProfile(pid, list_id, name, "0", priority, "", "", "", "", "", "", "", "All", "Fleet Lists")


def fleet(list_id=10, scenario="Raid"):
    f=Fleet.create("Test","b5_acta","b5_acta_priority_standard",7,list_id,None)
    from dataclasses import replace
    return replace(f, metadata={"scenario_priority":scenario,"fleet_allocation_points":5})


def test_isa_allows_one_allied_fleet_list():
    f=fleet()
    e=FleetEntry.create(1)
    f=f.add_entry(e)
    result=build_b5_acta_core_rule_engine().validate(f,{e.entry_id:profile(1,3,"Earth Alliance - Third Age")})
    assert not result.errors


def test_isa_rejects_multiple_allied_sources():
    f=fleet()
    a=FleetEntry.create(1); b=FleetEntry.create(2)
    f=f.add_entry(a).add_entry(b)
    result=build_b5_acta_core_rule_engine().validate(f,{a.entry_id:profile(1,3,"EA"),b.entry_id:profile(2,8,"Narn")})
    assert any(m.code=="CORE_ALLIED_CONTINGENT" for m in result.errors)
