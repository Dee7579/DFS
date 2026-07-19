from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader
from reportlab.pdfgen import canvas

from dfs.services.fleet.print_composer import (
    FleetPrintComposer,
    PreparedFleetDocument,
)


@dataclass
class Item:
    item_key: str
    kind: str


def make_pdf(path: Path, size: tuple[float, float], label: str) -> None:
    c = canvas.Canvas(str(path), pagesize=size)
    for side in ("FRONT", "BACK"):
        c.setFont("Helvetica-Bold", 24)
        c.drawString(20, size[1] - 40, f"{label} {side}")
        c.showPage()
    c.save()


def test_letter_packet_two_up_ships_and_four_up_fighters(tmp_path: Path):
    ship = tmp_path / "ship.pdf"
    fighter = tmp_path / "fighter.pdf"
    make_pdf(ship, (612, 396), "SHIP")
    make_pdf(fighter, (396, 306), "FIGHTER")

    docs = [
        PreparedFleetDocument(Item("ship:1", "ship"), 1, ship),
        PreparedFleetDocument(Item("ship:2", "ship"), 1, ship),
        PreparedFleetDocument(Item("ship:3", "ship"), 1, ship),
        PreparedFleetDocument(Item("craft:1", "craft"), 1, fighter),
        PreparedFleetDocument(Item("craft:2", "craft"), 1, fighter),
    ]
    output = tmp_path / "packet.pdf"
    packet = FleetPrintComposer().compose(docs, output)

    reader = PdfReader(str(output))
    # Two pairs of ship pages (front/back) plus one fighter front/back pair.
    assert len(reader.pages) == 6
    assert packet.page_count == 6
    assert packet.item_keys == ("ship:1", "ship:2", "ship:3", "craft:1", "craft:2")
    for page in reader.pages:
        assert float(page.mediabox.width) == 612
        assert float(page.mediabox.height) == 792


def test_tall_ship_is_not_paired_or_shrunk_to_half_page(tmp_path: Path):
    tall = tmp_path / "tall.pdf"
    standard = tmp_path / "standard.pdf"
    make_pdf(tall, (612, 540), "TALL")
    make_pdf(standard, (612, 360), "STANDARD")

    docs = [
        PreparedFleetDocument(Item("ship:tall", "ship"), 1, tall),
        PreparedFleetDocument(Item("ship:standard", "ship"), 1, standard),
    ]
    output = tmp_path / "dimension_aware.pdf"
    packet = FleetPrintComposer().compose(docs, output)

    # They cannot fit together at their intended scale, so each receives its
    # own front/back Letter pair instead of being forced into half-page slots.
    assert packet.page_count == 4
    reader = PdfReader(str(output))
    assert len(reader.pages) == 4


def test_roster_pages_print_before_ship_pages(tmp_path: Path):
    roster = tmp_path / "roster.pdf"
    ship = tmp_path / "ship.pdf"
    make_pdf(roster, (612, 792), "ROSTER")
    make_pdf(ship, (612, 396), "SHIP")
    docs = [
        PreparedFleetDocument(Item("roster", "roster"), 1, roster),
        PreparedFleetDocument(Item("ship:1", "ship"), 1, ship),
    ]
    output = tmp_path / "with_roster.pdf"
    FleetPrintComposer().compose(docs, output)
    reader = PdfReader(str(output))
    # The helper makes a two-page roster, followed by the ship front/back pair.
    assert len(reader.pages) == 4
    assert "ROSTER FRONT" in reader.pages[0].extract_text()


def test_single_page_roster_gets_blank_duplex_reverse(tmp_path: Path):
    roster = tmp_path / "single_roster.pdf"
    ship = tmp_path / "ship.pdf"

    c = canvas.Canvas(str(roster), pagesize=(612, 792))
    c.drawString(20, 760, "ROSTER")
    c.showPage()
    c.save()
    make_pdf(ship, (612, 396), "SHIP")

    docs = [
        PreparedFleetDocument(Item("roster", "roster"), 1, roster),
        PreparedFleetDocument(Item("ship:1", "ship"), 1, ship),
    ]
    output = tmp_path / "duplex_safe_roster.pdf"
    packet = FleetPrintComposer().compose(docs, output)
    reader = PdfReader(str(output))

    assert packet.page_count == 4
    assert "ROSTER" in (reader.pages[0].extract_text() or "")
    assert not (reader.pages[1].extract_text() or "").strip()
    assert "SHIP FRONT" in (reader.pages[2].extract_text() or "")
    assert "SHIP BACK" in (reader.pages[3].extract_text() or "")
