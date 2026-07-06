from reportlab.lib import colors

from dfs.pdf.layout import MID_GREY, SHADE_GREY, sorted_weapons, normalize_arc


def draw_weapon_table(d, ship, x, y, width):
    title_h = 12
    header_h = 13
    row_h = 13.3

    d.rect(x, y, width, title_h, fill=colors.HexColor("#F4F4F4"))
    d.text(x + 4, y + 8.3, "WEAPONS", 7.4, True)

    y += title_h

    d.rect(x, y, width, header_h, fill=MID_GREY)

    columns = [
        (x, 40, "ARC"),
        (x + 40, 205, "WEAPON"),
        (x + 245, 42, "AD"),
        (x + 287, 58, "RANGE"),
        (x + 345, width - 345, "TRAITS"),
    ]

    for cx, cw, label in columns:
        d.rect(cx, y, cw, header_h, line_width=0.35)
        d.text(cx + cw / 2, y + 9, label, 7.2, True, "middle")

    y += header_h

    weapons = sorted_weapons(ship.weapons)

    current_arc = None
    arc_group_index = -1

    for weapon in weapons:
        arc = normalize_arc(weapon.arc)

        if arc != current_arc:
            current_arc = arc
            arc_group_index += 1

        fill = None if arc_group_index % 2 == 0 else SHADE_GREY

        if fill:
            d.rect(x, y, width, row_h, fill=fill, line_width=0.25)
        else:
            d.rect(x, y, width, row_h, line_width=0.25)

        for cx, cw, _ in columns:
            d.rect(cx, y, cw, row_h, line_width=0.25)

        d.text(x + 20, y + 9, arc, 7.6, False, "middle")
        d.text(x + 44, y + 9, weapon.name, 7.6)
        d.text(x + 266, y + 9, weapon.attack_dice, 7.6, False, "middle")
        d.text(x + 316, y + 9, weapon.range, 7.6, False, "middle")
        d.text(x + 349, y + 9, weapon.traits, 6.8)

        y += row_h

    return y + 8