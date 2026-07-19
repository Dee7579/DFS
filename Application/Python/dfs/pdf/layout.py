from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth


ARC_ORDER = {
    "B": 1,
    "F": 2,
    "P": 3,
    "S": 4,
    "A": 5,
    "B(a)": 6,
    "T": 7,
}


PAGE_WIDTH = 612
BASE_PAGE_HEIGHT = 396

MARGIN_X = 18
TOP_BANNER_Y = 18
CONTENT_X = 22
CONTENT_W = 568


RED = colors.HexColor("#8F1D1D")
LIGHT_GREY = colors.HexColor("#F4F4F4")
MID_GREY = colors.HexColor("#D9D9D9")
SHADE_GREY = colors.HexColor("#EFEFEF")
LINE_GREY = colors.HexColor("#777777")
BLACK = colors.black
WHITE = colors.white


def normalize_arc(arc: str) -> str:
    arc = str(arc).strip()

    if arc.upper() in ["B(A)", "B (A)", "B (a)"]:
        return "B(a)"

    return arc.upper()


def arc_sort_key(weapon):
    arc = normalize_arc(weapon.arc)
    return ARC_ORDER.get(arc, 99)


def sorted_weapons(weapons):
    return sorted(weapons, key=arc_sort_key)


def has_track(value):
    value = str(value).strip()
    return value not in ["", "-", "None", "none"]


def track_total(value):
    if not has_track(value):
        return 0

    return int(str(value).split("/")[0])


def track_rows(value):
    total = track_total(value)

    if total <= 0:
        return 1

    return (total + 24) // 25


def get_shields_from_traits(ship):
    for trait in ship.traits:
        trait = str(trait).strip()

        if trait.startswith("Shields"):
            return trait.replace("Shields", "").strip()

    return None


def wrapped_line_count(text, max_width, font_size):
    words = str(text).split()
    if not words:
        return 0

    lines = 0
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        if stringWidth(test_line, "Helvetica", font_size) <= max_width:
            line = test_line
        else:
            lines += 1
            line = word

    if line:
        lines += 1
    return lines


def traits_notes_box_height(ship):
    trait_lines = wrapped_line_count(", ".join(ship.traits), 180, 7.2)
    trait_needed = 24 + (trait_lines * 10) + 8

    note_needed = 24
    for note in ship.notes:
        note_needed += (wrapped_line_count(note, 344, 6.8) * 9) + 2
    note_needed += 8

    return max(62, trait_needed, note_needed)


def estimate_page_height(ship):
    weapon_rows = len(ship.weapons)
    weapon_height = 12 + 13 + (weapon_rows * 13.3)

    header_stats_height = 120
    traits_notes_height = traits_notes_box_height(ship) + 10

    damage_rows = track_rows(ship.damage)
    crew_rows = track_rows(ship.crew)

    track_row_count = max(damage_rows, crew_rows)
    track_height = 28 + (track_row_count * 10)

    shields = get_shields_from_traits(ship)

    if shields:
        shield_rows = track_rows(shields)
        track_height += 8 + 28 + (shield_rows * 10)

    needed = (
        18
        + 13
        + header_stats_height
        + weapon_height
        + traits_notes_height
        + track_height
        + 40
    )

    return max(BASE_PAGE_HEIGHT, needed)