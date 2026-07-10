from reportlab.lib import colors


THRESHOLD_FILL = colors.HexColor("#F2D2D2")
LIGHT_GREY = colors.HexColor("#F4F4F4")

BOX_SIZE = 6.0
BOX_SPACING = 3.0
GROUP_GAP = 5.0
PER_GROUP = 5
PER_ROW = 25


def has_track(value):
    value = str(value).strip()
    return value not in ["", "-", "None", "none"]


def parse_track(value):
    if not has_track(value):
        return 0, 0

    parts = str(value).split("/")
    total = int(parts[0])
    threshold = int(parts[1]) if len(parts) > 1 else 0

    return total, threshold


def track_rows(total, threshold):
    if total <= 0:
        return 1

    normal_count = total - threshold
    visual_total = ((normal_count + PER_GROUP - 1) // PER_GROUP) * PER_GROUP + threshold
    return (visual_total + PER_ROW - 1) // PER_ROW


def draw_track_boxes(d, x, y, value, shade_threshold=True):
    total, threshold = parse_track(value)

    if total <= 0:
        return

    if not shade_threshold:
        threshold = 0

    normal_count = total - threshold
    spacing = BOX_SIZE + BOX_SPACING

    for i in range(total):
        if i < normal_count:
            visual_index = i
        else:
            threshold_index = i - normal_count
            threshold_start = ((normal_count + PER_GROUP - 1) // PER_GROUP) * PER_GROUP
            visual_index = threshold_start + threshold_index

        row = visual_index // PER_ROW
        col = visual_index % PER_ROW
        group = col // PER_GROUP

        px = x + col * spacing + group * GROUP_GAP
        py = y + row * spacing

        fill = THRESHOLD_FILL if shade_threshold and i >= normal_count else None
        d.rect(px, py, BOX_SIZE, BOX_SIZE, fill=fill, line_width=0.33)


def draw_track_panel(
    d,
    x,
    y,
    w,
    label,
    value,
    forced_rows=None,
    shade_threshold=True,
):
    total, threshold = parse_track(value)
    rows = track_rows(total, threshold)

    if forced_rows is not None:
        rows = max(rows, forced_rows)

    header_h = 13
    body_h = 12 + rows * (BOX_SIZE + BOX_SPACING)

    d.rect(x, y, w, header_h + body_h, line_width=0.5)
    d.rect(x, y, w, header_h, fill=LIGHT_GREY, line_width=0.5)
    d.text(x + 5, y + 9, f"{label.upper()} {value}", 7.4, True)

    draw_track_boxes(
        d,
        x + 7,
        y + header_h + 8,
        value,
        shade_threshold=shade_threshold,
    )

    return y + header_h + body_h


def get_shields_from_traits(ship):
    for trait in ship.traits:
        trait = str(trait).strip()

        if trait.startswith("Shields"):
            return trait.replace("Shields", "").strip()

    return None


def draw_damage_and_crew(d, ship, x, y):
    gap = 8
    full_w = 568
    half_w = (full_w - gap) / 2

    damage_total, damage_threshold = parse_track(ship.damage)
    crew_total, crew_threshold = parse_track(ship.crew)

    shared_rows = max(
        track_rows(damage_total, damage_threshold),
        track_rows(crew_total, crew_threshold),
    )

    damage_bottom = draw_track_panel(
        d,
        x,
        y,
        half_w,
        "Damage",
        ship.damage,
        forced_rows=shared_rows,
        shade_threshold=True,
    )

    crew_bottom = draw_track_panel(
        d,
        x + half_w + gap,
        y,
        half_w,
        "Crew",
        ship.crew,
        forced_rows=shared_rows,
        shade_threshold=True,
    )

    current_bottom = max(damage_bottom, crew_bottom)

    shields = get_shields_from_traits(ship)

    if shields:
        current_bottom += 8

        current_bottom = draw_track_panel(
            d,
            x,
            current_bottom,
            full_w,
            "Shields",
            shields,
            shade_threshold=False,
        )

    return current_bottom + 12