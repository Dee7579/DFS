from reportlab.lib import colors


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


def estimate_page_height(ship):
    weapon_rows = len(ship.weapons)
    weapon_height = 12 + 13 + (weapon_rows * 13.3)

    header_stats_height = 120
    traits_notes_height = 72

    damage_total = int(str(ship.damage).split("/")[0])
    crew_total = int(str(ship.crew).split("/")[0])

    damage_rows = (damage_total + 29) // 30
    crew_rows = (crew_total + 29) // 30
    track_rows = max(damage_rows, crew_rows)

    track_height = 20 + (track_rows * 8)

    needed = 18 + 13 + header_stats_height + weapon_height + traits_notes_height + track_height + 40

    return max(BASE_PAGE_HEIGHT, needed)