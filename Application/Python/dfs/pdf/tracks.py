from reportlab.lib import colors


THRESHOLD_FILL = colors.HexColor("#F2D2D2")

BOX_SIZE = 6.0
BOX_SPACING = 3.0
GROUP_GAP = 5.0
PER_GROUP = 5
PER_ROW = 25


def parse_track(value):
    parts = str(value).split("/")
    total = int(parts[0])
    threshold = int(parts[1]) if len(parts) > 1 else 0
    return total, threshold


def draw_track(d, x, y, label, value):
    total, threshold = parse_track(value)
    normal_count = total - threshold

    d.text(x, y, f"{label} {value}", 8.8, True)

    start_y = y + 16
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
        py = start_y + row * spacing

        fill = THRESHOLD_FILL if i >= normal_count else None

        d.rect(px, py, BOX_SIZE, BOX_SIZE, fill=fill, line_width=0.33)

    visual_total = ((normal_count + PER_GROUP - 1) // PER_GROUP) * PER_GROUP + threshold
    rows = (visual_total + PER_ROW - 1) // PER_ROW

    return start_y + rows * spacing + 8


def draw_damage_and_crew(d, ship, x, y):
    damage_bottom = draw_track(d, x, y, "Damage", ship.damage)
    crew_bottom = draw_track(d, x + 288, y, "Crew", ship.crew)

    return max(damage_bottom, crew_bottom) + 12