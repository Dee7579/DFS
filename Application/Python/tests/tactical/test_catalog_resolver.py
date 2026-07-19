from __future__ import annotations

from dfs.domain.catalog import PlatformDetail, PlatformProfile, PlatformSummary, WeaponDetail
from dfs.domain.tactical import UnitKind
from dfs.services.tactical import CatalogTacticalProfileResolver


class FakeCatalog:
    def search(self, filters):
        assert filters.fleet_list_ids == (22,)
        return [
            PlatformSummary(
                ship_id=5,
                name="Test Carrier",
                ship_class="Test Carrier",
                faction_id=3,
                faction_name="Test Faction",
                profile_count=1,
            )
        ]


class FakeDetails:
    def __init__(self) -> None:
        self.profile = PlatformProfile(
            profile_id=101,
            fleet_list_id=22,
            fleet_name="Test Fleet",
            initiative="+1",
            priority_level="War",
            speed="8",
            turn="1/45",
            hull="5",
            damage="40/10",
            crew="50/12",
            troops="2",
            craft="2 Test Fighter flights",
            in_service="2250+",
            source_book="Test Book",
            crew_quality="5",
            notes=("Source note",),
            traits=("Jump Engine", "Shields 10/2D6"),
            weapons=(WeaponDetail("Laser", "18", "F", "4", "Beam", 1),),
        )
        self.detail = PlatformDetail(
            ship_id=5,
            name="Test Carrier",
            ship_class="Test Carrier",
            file_name="test_carrier",
            faction_id=3,
            faction_name="Test Faction",
            profiles=(self.profile,),
        )

    def get_profile(self, profile_id: int):
        return self.profile if profile_id == 101 else None

    def get(self, ship_id: int):
        assert ship_id == 5
        return self.detail


def test_catalog_resolver_snapshots_printed_profile_tracks_and_equipment() -> None:
    template = CatalogTacticalProfileResolver(FakeCatalog(), FakeDetails()).resolve(101)

    assert template.platform_name == "Test Carrier"
    assert template.damage_maximum == 40
    assert template.crippled_threshold == 10
    assert template.crew_maximum == 50
    assert template.skeleton_threshold == 12
    assert template.shield_maximum == 10
    assert template.shield_recovery == "2D6"
    assert template.crew_quality == "5"
    assert template.kind is UnitKind.PLATFORM
    assert template.included_craft[0].quantity == 2
    assert template.weapons[0].name == "Laser"
