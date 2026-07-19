from pathlib import Path

from pypdf import PdfReader

from dfs.pdf.generator import ACTAClassicGenerator
from dfs.ship import Ship


def make_ship() -> Ship:
    return Ship(
        name="Test Cruiser",
        ship_class="Test Cruiser",
        faction="Test Faction",
        fleet="Test Faction",
        priority="Raid",
        speed=8,
        turn="2/45°",
        hull=5,
        damage="20/5",
        crew="24/6",
        troops=2,
        craft="None",
        initiative="+0",
        in_service="2250+",
        traits=[],
        weapons=[],
        notes=[],
    )


def test_ship_name_field_is_native_on_front_and_back(tmp_path: Path):
    output = tmp_path / "named.pdf"
    ACTAClassicGenerator(output).generate_ship_sheet(make_ship(), vessel_name="Valiant")
    reader = PdfReader(str(output))
    assert len(reader.pages) == 2
    for page in reader.pages:
        text = page.extract_text()
        assert "SHIP NAME" in text
        assert "VALIANT" in text


def test_blank_ship_name_field_still_exists_on_both_pages(tmp_path: Path):
    output = tmp_path / "blank.pdf"
    ACTAClassicGenerator(output).generate_ship_sheet(make_ship())
    reader = PdfReader(str(output))
    for page in reader.pages:
        assert "SHIP NAME" in page.extract_text()
