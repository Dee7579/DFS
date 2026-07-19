"""Compose fleet documents onto standard Letter pages for reliable printing.

The composer preserves each source sheet at its intended scale whenever it fits
on Letter paper. Standard half-page ship sheets may share a page, while taller
or otherwise oversized sheets are placed alone rather than being shrunk to fit a
fixed slot. Fighter and reusable-craft references are imposed four-up at their
native quarter-page size. All output pages are US Letter portrait so the packet
uses one ordinary printer job.
"""
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterable, Sequence

from pypdf import PageObject, PdfReader, PdfWriter, Transformation
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas

LETTER_WIDTH = 612.0
LETTER_HEIGHT = 792.0
HALF_HEIGHT = LETTER_HEIGHT / 2.0
HALF_WIDTH = LETTER_WIDTH / 2.0
_EPSILON = 0.5


@dataclass(frozen=True, slots=True)
class PreparedFleetDocument:
    item: object
    copies: int
    path: Path


@dataclass(frozen=True, slots=True)
class FleetPrintPacket:
    path: Path
    item_keys: tuple[str, ...]
    page_count: int


def _blank_letter_page() -> PageObject:
    return PageObject.create_blank_page(width=LETTER_WIDTH, height=LETTER_HEIGHT)


def _guide_page(*, horizontal_y: float | None = None, fighter_grid: bool = False) -> PageObject:
    """Create a transparent Letter overlay containing subtle cut guides."""
    stream = BytesIO()
    c = canvas.Canvas(stream, pagesize=(LETTER_WIDTH, LETTER_HEIGHT))
    c.setStrokeColor(Color(0.70, 0.72, 0.75))
    c.setLineWidth(0.35)
    c.setDash(2, 2)
    if horizontal_y is not None:
        c.line(0, horizontal_y, LETTER_WIDTH, horizontal_y)
    if fighter_grid:
        c.line(0, HALF_HEIGHT, LETTER_WIDTH, HALF_HEIGHT)
        c.line(HALF_WIDTH, 0, HALF_WIDTH, LETTER_HEIGHT)
    c.showPage()
    c.save()
    stream.seek(0)
    return PdfReader(stream).pages[0]


def _merge_preserve(
    target: PageObject,
    source: PageObject,
    *,
    x: float,
    y: float,
    max_width: float,
    max_height: float,
    rotate_degrees: int = 0,
) -> tuple[float, float, float]:
    """Merge *source* without enlarging it and return drawn width/height/scale.

    A sheet is only reduced when it physically cannot fit on Letter paper. It is
    never reduced merely to make room for another sheet.
    """
    src_w = float(source.mediabox.width)
    src_h = float(source.mediabox.height)
    if src_w <= 0 or src_h <= 0:
        return 0.0, 0.0, 1.0

    if rotate_degrees not in (-90, 0, 90):
        raise ValueError("rotate_degrees must be -90, 0, or 90")
    oriented_w, oriented_h = (src_h, src_w) if rotate_degrees else (src_w, src_h)
    scale = min(1.0, max_width / oriented_w, max_height / oriented_h)
    drawn_w = oriented_w * scale
    drawn_h = oriented_h * scale

    left = x + (max_width - drawn_w) / 2.0
    bottom = y + (max_height - drawn_h) / 2.0

    if rotate_degrees == 90:
        transform = Transformation(ctm=(
            0.0, scale,
            -scale, 0.0,
            left + drawn_w, bottom,
        ))
    elif rotate_degrees == -90:
        transform = Transformation(ctm=(
            0.0, -scale,
            scale, 0.0,
            left, bottom + drawn_h,
        ))
    else:
        transform = Transformation().scale(scale).translate(left, bottom)

    target.merge_transformed_page(source, transform, over=True)
    return drawn_w, drawn_h, scale


def _effective_ship_size(path: Path) -> tuple[float, float]:
    reader = PdfReader(str(path))
    if not reader.pages:
        return 0.0, 0.0
    page = reader.pages[0]
    width = float(page.mediabox.width)
    height = float(page.mediabox.height)
    scale = min(1.0, LETTER_WIDTH / width, LETTER_HEIGHT / height)
    return width * scale, height * scale


def _group_ships(entries: Sequence[tuple[object, Path]]) -> list[list[tuple[object, Path]]]:
    """Pack adjacent ships without changing roster order or shrinking to pair."""
    groups: list[list[tuple[object, Path]]] = []
    index = 0
    while index < len(entries):
        first = entries[index]
        _w1, h1 = _effective_ship_size(first[1])
        if index + 1 < len(entries):
            second = entries[index + 1]
            _w2, h2 = _effective_ship_size(second[1])
            if h1 + h2 <= LETTER_HEIGHT + _EPSILON:
                groups.append([first, second])
                index += 2
                continue
        groups.append([first])
        index += 1
    return groups


class FleetPrintComposer:
    """Build one duplex-friendly Letter packet from selected fleet documents."""

    def compose(
        self,
        documents: Iterable[PreparedFleetDocument],
        output_path: Path,
    ) -> FleetPrintPacket:
        roster_docs: list[tuple[object, Path]] = []
        expanded_ships: list[tuple[object, Path]] = []
        craft: list[tuple[object, Path]] = []
        item_keys: list[str] = []

        for prepared in documents:
            item = prepared.item
            path = Path(prepared.path)
            kind = getattr(item, "kind", "ship")
            if kind == "roster":
                roster_docs.append((item, path))
            elif kind == "ship":
                for _ in range(max(1, int(prepared.copies))):
                    expanded_ships.append((item, path))
            else:
                craft.append((item, path))
            item_keys.append(str(item.item_key))

        writer = PdfWriter()

        # Roster pages are already Letter-sized and print first. A roster is
        # a single-sided report, so its section must end on an even page count
        # before any duplex front/back sheets begin. Otherwise the first ship
        # back would print on the reverse of the roster and every subsequent
        # pair would be shifted by one page.
        roster_page_count = 0
        for _item, path in roster_docs:
            reader = PdfReader(str(path))
            for page in reader.pages:
                target = _blank_letter_page()
                _merge_preserve(
                    target,
                    page,
                    x=0.0,
                    y=0.0,
                    max_width=LETTER_WIDTH,
                    max_height=LETTER_HEIGHT,
                )
                writer.add_page(target)
                roster_page_count += 1

        if roster_page_count % 2 == 1:
            # Intentionally blank reverse side for duplex safety.
            writer.add_page(_blank_letter_page())

        # Dimension-aware ship pagination. Pair only adjacent sheets whose native
        # fitted heights genuinely fit together. Tall sheets are placed alone.
        for group in _group_ships(expanded_ships):
            front = _blank_letter_page()
            back = _blank_letter_page()
            heights = [_effective_ship_size(path)[1] for _item, path in group]

            if len(group) == 2:
                # Keep the first sheet at the top and the second at the bottom.
                placements = [LETTER_HEIGHT - heights[0], 0.0]
                boundary = heights[1]
            else:
                # A single sheet is top-aligned at full intended size.
                placements = [LETTER_HEIGHT - heights[0]]
                boundary = None

            for index, (_item, path) in enumerate(group):
                reader = PdfReader(str(path))
                if not reader.pages:
                    continue
                y = placements[index]
                _merge_preserve(
                    front,
                    reader.pages[0],
                    x=0.0,
                    y=y,
                    max_width=LETTER_WIDTH,
                    max_height=heights[index],
                )
                if len(reader.pages) > 1:
                    _merge_preserve(
                        back,
                        reader.pages[1],
                        x=0.0,
                        y=y,
                        max_width=LETTER_WIDTH,
                        max_height=heights[index],
                    )

            if boundary is not None:
                guide = _guide_page(horizontal_y=boundary)
                front.merge_page(guide, over=True)
                back.merge_page(guide, over=True)
            writer.add_page(front)
            writer.add_page(back)

        # Four unique fighter/craft references per Letter page. Native fighter
        # sheets are 5.5 x 4.25 inches and therefore fit a rotated quarter-page
        # cell at exactly 100% scale. Back columns are mirrored for portrait
        # long-edge duplex alignment, and back artwork is rotated in the
        # opposite direction so it is upright behind the front after cutting.
        front_positions = (
            (0.0, HALF_HEIGHT),
            (HALF_WIDTH, HALF_HEIGHT),
            (0.0, 0.0),
            (HALF_WIDTH, 0.0),
        )
        back_positions = (
            (HALF_WIDTH, HALF_HEIGHT),
            (0.0, HALF_HEIGHT),
            (HALF_WIDTH, 0.0),
            (0.0, 0.0),
        )
        for start in range(0, len(craft), 4):
            group = craft[start:start + 4]
            front = _blank_letter_page()
            back = _blank_letter_page()
            for index, (_item, path) in enumerate(group):
                reader = PdfReader(str(path))
                if not reader.pages:
                    continue
                front_x, front_y = front_positions[index]
                _merge_preserve(
                    front,
                    reader.pages[0],
                    x=front_x,
                    y=front_y,
                    max_width=HALF_WIDTH,
                    max_height=HALF_HEIGHT,
                    rotate_degrees=90,
                )
                if len(reader.pages) > 1:
                    back_x, back_y = back_positions[index]
                    _merge_preserve(
                        back,
                        reader.pages[1],
                        x=back_x,
                        y=back_y,
                        max_width=HALF_WIDTH,
                        max_height=HALF_HEIGHT,
                        rotate_degrees=-90,
                    )
            guide = _guide_page(fighter_grid=True)
            front.merge_page(guide, over=True)
            back.merge_page(guide, over=True)
            writer.add_page(front)
            writer.add_page(back)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as handle:
            writer.write(handle)

        return FleetPrintPacket(
            path=output_path,
            item_keys=tuple(dict.fromkeys(item_keys)),
            page_count=len(writer.pages),
        )
