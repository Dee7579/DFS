from pathlib import Path

from pypdf import PdfReader

from dfs.domain.catalog import PlatformDetail, PlatformProfile, WeaponDetail
from dfs.services.fleet.print_planner import FleetPrintItem
from dfs.services.fleet.sheet_generator import FleetSheetGenerator


class Details:
    def __init__(self):
        self.profile = PlatformProfile(
            profile_id=11, fleet_list_id=2, fleet_name="Earth Alliance - Third Age",
            initiative="+2", priority_level="Raid", speed="8", turn="2/45°",
            hull="5", damage="28/6", crew="32/6", troops="3",
            craft="1 Aurora Starfury Flight", in_service="2240+", source_book="",
            traits=("Anti-Fighter 2", "Jump Engine"),
            weapons=(WeaponDetail("Heavy Laser Cannon", "18", "B", "4", "Beam", 0),),
        )
        self.detail = PlatformDetail(
            ship_id=7, name="Hyperion-class Cruiser", ship_class="Hyperion-class Cruiser",
            file_name="Hyperion_Cruiser", faction_id=1, faction_name="Earth Alliance",
            profiles=(self.profile,),
        )

    def get(self, ship_id):
        return self.detail if ship_id == 7 else None

    def get_profile(self, profile_id):
        return self.profile if profile_id == 11 else None


class Documents:
    def find_sheet(self, **kwargs):
        return None


def test_named_ship_is_written_to_front_and_back(tmp_path: Path):
    generator = FleetSheetGenerator(Details(), Documents())
    item = FleetPrintItem(
        item_key="ship:abc", kind="ship", profile_id=11, ship_id=7,
        platform_name="Hyperion-class Cruiser", vessel_name="Agamemnon",
        fleet_name="Earth Alliance - Third Age", faction_name="Earth Alliance",
        file_name="Hyperion_Cruiser", quantity_represented=1, copies=1,
    )
    result = generator.generate(item, style_id="dfs_standard", output_folder=tmp_path)
    reader = PdfReader(str(result.path))
    assert len(reader.pages) == 2
    assert "AGAMEMNON" in (reader.pages[0].extract_text() or "")
    assert "SHIP NAME: AGAMEMNON" in (reader.pages[1].extract_text() or "")
    first = reader.pages[0].mediabox
    second = reader.pages[1].mediabox
    assert float(first.width) == float(second.width)
    assert float(first.height) == float(second.height)
