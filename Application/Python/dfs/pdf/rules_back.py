from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from reportlab.pdfbase.pdfmetrics import stringWidth

from dfs.codex import (
    get_fleet_rules,
    get_rule,
    normalize_rule_name,
    split_weapon_traits,
)
from dfs.pdf.layout import (
    RED,
    LIGHT_GREY,
    LINE_GREY,
    BLACK,
    WHITE,
)


FRAME_MARGIN = 18
CONTENT_MARGIN = 22
TOP_BAR_HEIGHT = 13
SECTION_GAP = 10
FOOTER_SPACE = 28
SECTION_HEADER_HEIGHT = 13

BODY_FONT = 6.7
BODY_LINE_GAP = 8.2
RULE_TITLE_FONT = 7.4
ENTRY_GAP = 4.0
COLUMN_GAP = 8
MIN_PAGE_HEIGHT = 306


@dataclass
class RuleEntry:
    title: str
    text: str
    category: str


class BackDrawing:
    def __init__(self, canvas_obj, page_width: float, page_height: float):
        self.c = canvas_obj
        self.page_width = page_width
        self.page_height = page_height

    def y(self, svg_y: float) -> float:
        return self.page_height - svg_y

    def rect(
        self,
        x,
        y,
        w,
        h,
        fill=None,
        stroke=BLACK,
        line_width=0.5,
    ):
        self.c.setLineWidth(line_width)
        self.c.setStrokeColor(stroke)

        if fill is not None:
            self.c.setFillColor(fill)
            self.c.rect(x, self.y(y + h), w, h, fill=True, stroke=True)
        else:
            self.c.rect(x, self.y(y + h), w, h, fill=False, stroke=True)

    def text(
        self,
        x,
        y,
        value,
        size=8,
        bold=False,
        anchor="start",
        color=BLACK,
    ):
        font_name = "Helvetica-Bold" if bold else "Helvetica"
        self.c.setFillColor(color)
        self.c.setFont(font_name, size)
        value = str(value)

        if anchor == "end":
            self.c.drawRightString(x, self.y(y), value)
        elif anchor == "middle":
            self.c.drawCentredString(x, self.y(y), value)
        else:
            self.c.drawString(x, self.y(y), value)

    def line(self, x1, y1, x2, y2, color=LINE_GREY, line_width=0.5):
        self.c.setStrokeColor(color)
        self.c.setLineWidth(line_width)
        self.c.line(x1, self.y(y1), x2, self.y(y2))


def _wrap_text(text: str, max_width: float, size: float) -> list[str]:
    text = str(text).strip()

    if not text:
        return []

    words = text.split()
    lines: list[str] = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()

        if stringWidth(candidate, "Helvetica", size) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def _rule_text(entry: dict[str, Any] | None) -> str:
    if not entry:
        return "Rule text has not yet been entered in the B5 ACTA Codex."

    text = str(entry.get("text", "")).strip()
    return text or "Rule text has not yet been entered in the B5 ACTA Codex."


def _display_title(key: str, entry: dict[str, Any] | None) -> str:
    if entry:
        title = str(entry.get("title", "")).strip()
        if title:
            return title

    return key


def collect_platform_rules(ship) -> list[RuleEntry]:
    keys: set[str] = set()

    for trait in ship.traits:
        key = normalize_rule_name(str(trait))
        if key:
            keys.add(key)

    for weapon in ship.weapons:
        for key in split_weapon_traits(str(weapon.traits)):
            if key:
                keys.add(key)

    entries: list[RuleEntry] = []

    for key in sorted(keys, key=str.casefold):
        codex_entry = get_rule(key)
        entries.append(
            RuleEntry(
                title=_display_title(key, codex_entry),
                text=_rule_text(codex_entry),
                category=(
                    str(codex_entry.get("category", "Rule"))
                    if codex_entry
                    else "Rule"
                ),
            )
        )

    return entries


def collect_fleet_rule_entries(ship) -> list[RuleEntry]:
    raw_rules = get_fleet_rules(ship.fleet)
    entries: list[RuleEntry] = []

    for item in raw_rules:
        if isinstance(item, dict):
            title = str(item.get("title", item.get("name", "Fleet Rule"))).strip()
            text = str(item.get("text", "")).strip()
            entries.append(
                RuleEntry(
                    title=title or "Fleet Rule",
                    text=text or "Fleet rule text has not yet been entered in the B5 ACTA Codex.",
                    category="Fleet Rule",
                )
            )
            continue

        key = str(item).strip()
        if not key:
            continue

        codex_entry = get_rule(key)
        entries.append(
            RuleEntry(
                title=_display_title(key, codex_entry),
                text=_rule_text(codex_entry),
                category="Fleet Rule",
            )
        )

    return sorted(entries, key=lambda entry: entry.title.casefold())


def _inline_layout(entry: RuleEntry, text_width: float) -> tuple[str, list[str]]:
    title_text = f"{entry.title} —"
    title_width = stringWidth(title_text + " ", "Helvetica-Bold", RULE_TITLE_FONT)
    available_first = max(30, text_width - title_width)

    words = entry.text.split()
    first_line_words: list[str] = []

    while words:
        candidate = " ".join(first_line_words + [words[0]])

        if stringWidth(candidate, "Helvetica", BODY_FONT) <= available_first:
            first_line_words.append(words.pop(0))
        else:
            break

    first_line = " ".join(first_line_words)
    remaining = " ".join(words)
    remaining_lines = _wrap_text(remaining, text_width, BODY_FONT)

    if not first_line and remaining_lines:
        first_line = remaining_lines.pop(0)

    return first_line, remaining_lines


def _entry_height(entry: RuleEntry, text_width: float) -> float:
    first_line, remaining_lines = _inline_layout(entry, text_width)
    line_count = 1 + len(remaining_lines)
    return line_count * BODY_LINE_GAP + ENTRY_GAP


def _entries_body_height(entries: list[RuleEntry], text_width: float) -> float:
    if not entries:
        return 30

    return 10 + sum(_entry_height(entry, text_width) for entry in entries)


def _split_balanced(
    entries: list[RuleEntry],
    text_width: float,
) -> tuple[list[RuleEntry], list[RuleEntry]]:
    if len(entries) <= 1:
        return entries, []

    heights = [_entry_height(entry, text_width) for entry in entries]
    best_index = 1
    best_difference = float("inf")

    for index in range(1, len(entries)):
        left_height = sum(heights[:index])
        right_height = sum(heights[index:])
        difference = abs(left_height - right_height)

        if difference < best_difference:
            best_difference = difference
            best_index = index

    return entries[:best_index], entries[best_index:]


def _single_section_height(
    entries: list[RuleEntry],
    text_width: float,
    empty_text: str,
) -> float:
    if not entries:
        lines = _wrap_text(empty_text, text_width, BODY_FONT)
        return SECTION_HEADER_HEIGHT + max(30, 10 + len(lines) * BODY_LINE_GAP)

    return SECTION_HEADER_HEIGHT + _entries_body_height(entries, text_width)


def _two_column_section_height(
    entries: list[RuleEntry],
    column_text_width: float,
) -> tuple[float, list[RuleEntry], list[RuleEntry]]:
    left, right = _split_balanced(entries, column_text_width)
    left_height = _entries_body_height(left, column_text_width)
    right_height = _entries_body_height(right, column_text_width)
    body_height = max(left_height, right_height, 30)
    return SECTION_HEADER_HEIGHT + body_height, left, right


def estimate_rules_back_height(
    ship,
    page_width: float,
    include_fleet_rules: bool,
) -> float:
    content_width = page_width - CONTENT_MARGIN * 2
    current_y = 45 + 58

    if include_fleet_rules:
        current_y += _single_section_height(
            collect_fleet_rule_entries(ship),
            content_width - 18,
            "No fleet rules are currently entered for this fleet.",
        ) + SECTION_GAP

    rule_entries = collect_platform_rules(ship)

    if page_width >= 500:
        column_width = (content_width - COLUMN_GAP) / 2
        section_height, _, _ = _two_column_section_height(
            rule_entries,
            column_width - 18,
        )
        current_y += section_height
    else:
        current_y += _single_section_height(
            rule_entries,
            content_width - 18,
            "No platform or weapon traits are listed on this sheet.",
        )

    return max(MIN_PAGE_HEIGHT, current_y + FOOTER_SPACE)


def _draw_header(
    d: BackDrawing,
    ship,
    y: float,
    sheet_type: str,
) -> float:
    era = str(ship.fleet).replace(str(ship.faction), "").replace("-", "").strip()
    header_text = (
        f"{ship.faction.upper()} - {era.upper()}"
        if era
        else str(ship.faction).upper()
    )

    d.text(24, y, header_text, 11.2, True)

    title = str(ship.name).upper()
    title_size = 18.0
    max_width = d.page_width - 210

    while title_size > 12.0:
        if stringWidth(title, "Helvetica-Bold", title_size) <= max_width:
            break
        title_size -= 0.5

    d.text(24, y + 22, title, title_size, True)

    right_x = d.page_width - 24
    d.text(right_x, y, str(ship.priority).upper(), 11.5, True, "end")
    d.text(right_x, y + 21, f"Initiative: {ship.initiative}", 8.7, True, "end")
    d.text(right_x, y + 36, f"{sheet_type} Rules Reference", 7.6, True, "end")

    d.line(FRAME_MARGIN, y + 48, d.page_width - FRAME_MARGIN, y + 48)
    return y + 58


def _draw_inline_entry(
    d: BackDrawing,
    x: float,
    y: float,
    text_width: float,
    entry: RuleEntry,
) -> float:
    first_line, remaining_lines = _inline_layout(entry, text_width)
    title_text = f"{entry.title} —"
    title_width = stringWidth(title_text + " ", "Helvetica-Bold", RULE_TITLE_FONT)

    d.text(x, y, title_text, RULE_TITLE_FONT, True)

    if first_line:
        d.text(
            x + title_width,
            y,
            first_line,
            BODY_FONT,
        )

    y += BODY_LINE_GAP

    for line in remaining_lines:
        d.text(x, y, line, BODY_FONT)
        y += BODY_LINE_GAP

    return y + ENTRY_GAP


def _draw_single_rule_section(
    d: BackDrawing,
    x: float,
    y: float,
    w: float,
    title: str,
    entries: list[RuleEntry],
    empty_text: str,
) -> float:
    text_width = w - 18
    height = _single_section_height(entries, text_width, empty_text)

    d.rect(x, y, w, height, line_width=0.5)
    d.rect(x, y, w, SECTION_HEADER_HEIGHT, fill=LIGHT_GREY, line_width=0.5)
    d.text(x + 5, y + 9, title, 7.4, True)

    cursor_y = y + SECTION_HEADER_HEIGHT + 13

    if not entries:
        for line in _wrap_text(empty_text, text_width, BODY_FONT):
            d.text(x + 9, cursor_y, line, BODY_FONT)
            cursor_y += BODY_LINE_GAP
        return y + height

    for entry in entries:
        cursor_y = _draw_inline_entry(
            d,
            x + 9,
            cursor_y,
            text_width,
            entry,
        )

    return y + height


def _draw_two_column_rule_section(
    d: BackDrawing,
    x: float,
    y: float,
    w: float,
    title: str,
    entries: list[RuleEntry],
) -> float:
    column_width = (w - COLUMN_GAP) / 2
    text_width = column_width - 18
    height, left_entries, right_entries = _two_column_section_height(
        entries,
        text_width,
    )

    d.rect(x, y, w, height, line_width=0.5)
    d.rect(x, y, w, SECTION_HEADER_HEIGHT, fill=LIGHT_GREY, line_width=0.5)
    d.text(x + 5, y + 9, title, 7.4, True)

    divider_x = x + column_width + COLUMN_GAP / 2
    d.line(
        divider_x,
        y + SECTION_HEADER_HEIGHT,
        divider_x,
        y + height,
        color=LINE_GREY,
        line_width=0.4,
    )

    left_y = y + SECTION_HEADER_HEIGHT + 13
    right_y = y + SECTION_HEADER_HEIGHT + 13

    for entry in left_entries:
        left_y = _draw_inline_entry(
            d,
            x + 9,
            left_y,
            text_width,
            entry,
        )

    right_x = x + column_width + COLUMN_GAP

    for entry in right_entries:
        right_y = _draw_inline_entry(
            d,
            right_x + 9,
            right_y,
            text_width,
            entry,
        )

    return y + height


def draw_rules_back(
    canvas_obj,
    ship,
    page_width: float,
    include_fleet_rules: bool = True,
    sheet_type: str = "Ship",
    page_height: float | None = None,
) -> None:
    required_height = estimate_rules_back_height(
        ship,
        page_width,
        include_fleet_rules,
    )

    if page_height is None:
        page_height = required_height
    else:
        page_height = max(page_height, required_height)

    canvas_obj.setPageSize((page_width, page_height))
    d = BackDrawing(canvas_obj, page_width, page_height)

    frame_width = page_width - FRAME_MARGIN * 2
    d.rect(
        FRAME_MARGIN,
        FRAME_MARGIN,
        frame_width,
        page_height - FRAME_MARGIN * 2,
        line_width=0.8,
    )
    d.rect(
        FRAME_MARGIN,
        FRAME_MARGIN,
        frame_width,
        TOP_BAR_HEIGHT,
        fill=RED,
        stroke=RED,
    )

    d.text(
        24,
        27.5,
        "Dee's Fighting Ships | Babylon 5 ACTA Tactical Reference System",
        7.2 if page_width >= 500 else 5.8,
        True,
        color=WHITE,
    )
    d.text(
        page_width - 24,
        27.5,
        "Rules Reference",
        7.2 if page_width >= 500 else 5.8,
        True,
        "end",
        WHITE,
    )

    current_y = _draw_header(d, ship, 45, sheet_type)
    content_width = page_width - CONTENT_MARGIN * 2

    if include_fleet_rules:
        current_y = _draw_single_rule_section(
            d,
            CONTENT_MARGIN,
            current_y,
            content_width,
            "FLEET RULES",
            collect_fleet_rule_entries(ship),
            "No fleet rules are currently entered for this fleet.",
        ) + SECTION_GAP

    rule_entries = collect_platform_rules(ship)

    if page_width >= 500:
        _draw_two_column_rule_section(
            d,
            CONTENT_MARGIN,
            current_y,
            content_width,
            "TRAITS AND WEAPON RULES",
            rule_entries,
        )
    else:
        _draw_single_rule_section(
            d,
            CONTENT_MARGIN,
            current_y,
            content_width,
            "TRAITS AND WEAPON RULES",
            rule_entries,
            "No platform or weapon traits are listed on this sheet.",
        )

    d.text(
        24,
        page_height - 8,
        "DFS B5 ACTA Rules Reference | Generated from DFS Codex",
        5.8 if page_width >= 500 else 5.0,
    )
