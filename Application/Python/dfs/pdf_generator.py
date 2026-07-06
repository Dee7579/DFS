from reportlab.lib import colors
from reportlab.pdfgen import canvas


PAGE_SIZE = (612, 396)


class PDFGenerator:
    def __init__(self, filename):
        self.filename = filename
        self.width, self.height = PAGE_SIZE

    def y(self, svg_y):
        return self.height - svg_y

    def rect(self, c, x, y, w, h, fill=None, stroke=colors.black, line_width=0.5):
        c.setLineWidth(line_width)
        c.setStrokeColor(stroke)

        if fill:
            c.setFillColor(fill)
            c.rect(x, self.y(y + h), w, h, fill=True, stroke=True)
        else:
            c.rect(x, self.y(y + h), w, h, fill=False, stroke=True)

    def text(self, c, x, y, txt, size=8, bold=False, anchor="start", color=colors.black):
        c.setFillColor(color)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)

        txt = str(txt)

        if anchor == "end":
            c.drawRightString(x, self.y(y), txt)
        elif anchor == "middle":
            c.drawCentredString(x, self.y(y), txt)
        else:
            c.drawString(x, self.y(y), txt)

    def generate_ship_sheet(self, ship):
        c = canvas.Canvas(str(self.filename), pagesize=PAGE_SIZE)

        self.draw_frame(c)

        current_y = 45
        current_y = self.draw_header(c, ship, current_y)
        current_y = self.draw_stat_boxes(c, ship, current_y)
        current_y = self.draw_weapons(c, ship, current_y)
        current_y = self.draw_traits_notes(c, ship, current_y)
        current_y = self.draw_tracks(c, ship, current_y)

        c.save()

    def draw_frame(self, c):
        self.rect(c, 18, 18, 576, 360, line_width=0.8)
        self.rect(
            c,
            18,
            18,
            576,
            13,
            fill=colors.HexColor("#8F1D1D"),
            stroke=colors.HexColor("#8F1D1D"),
        )

        self.text(
            c,
            24,
            27.5,
            "Dee's Fighting Ships | Babylon 5 ACTA Tactical Reference System",
            7.2,
            True,
            color=colors.white,
        )

        self.text(
            c,
            588,
            27.5,
            "Generated Ship Sheet",
            7.2,
            True,
            "end",
            colors.white,
        )

    def draw_header(self, c, ship, y):
        self.text(c, 24, y, f"{ship.faction.upper()} | {ship.in_service}", 11.2, True)
        self.text(c, 24, y + 21, ship.name.upper(), 18, True)

        self.text(c, 588, y, ship.priority.upper(), 11.5, True, "end")
        self.text(c, 588, y + 21, f"Initiative: {ship.initiative}", 8.7, True, "end")

        self.text(c, 24, y + 41, "SHIP NAME", 6.8, True)
        self.text(c, 458, y + 41, "CREW QUALITY", 6.8, True)

        c.setStrokeColor(colors.HexColor("#777777"))
        c.line(80, self.y(y + 42), 414, self.y(y + 42))
        c.line(535, self.y(y + 42), 575, self.y(y + 42))

        c.setStrokeColor(colors.HexColor("#999999"))
        c.line(18, self.y(y + 55), 594, self.y(y + 55))

        return y + 65

    def draw_stat_boxes(self, c, ship, y):
        self.stat_box(c, 22, y, 52, "Speed", ship.speed)
        self.stat_box(c, 74, y, 64, "Turns", ship.turn)
        self.stat_box(c, 138, y, 48, "Hull", ship.hull)
        self.stat_box(c, 186, y, 56, "Troops", ship.troops)
        self.stat_box(c, 242, y, 260, "Craft", ship.craft)
        self.stat_box(c, 502, y, 88, "In Service", ship.in_service)

        return y + 37

    def stat_box(self, c, x, y, w, label, value):
        self.rect(c, x, y, w, 27, line_width=0.35)
        self.text(c, x + w / 2, y + 9, label, 6.8, True, "middle")
        self.text(c, x + w / 2, y + 22, value, 8.2, False, "middle")

    def draw_weapons(self, c, ship, y):
        x = 22
        w = 568
        title_h = 12
        header_h = 13
        row_h = 13.3

        self.rect(c, x, y, w, title_h, fill=colors.HexColor("#F4F4F4"))
        self.text(c, x + 4, y + 8.3, "WEAPONS", 7.4, True)

        y += title_h

        self.rect(c, x, y, w, header_h, fill=colors.HexColor("#D9D9D9"))

        columns = [
            (22, 40, "ARC"),
            (62, 205, "WEAPON"),
            (267, 42, "AD"),
            (309, 58, "RANGE"),
            (367, 223, "TRAITS"),
        ]

        for cx, cw, label in columns:
            self.rect(c, cx, y, cw, header_h, line_width=0.35)
            self.text(c, cx + cw / 2, y + 9, label, 7.2, True, "middle")

        y += header_h

        for weapon in ship.weapons:
            for cx, cw, _ in columns:
                self.rect(c, cx, y, cw, row_h, line_width=0.25)

            self.text(c, 42, y + 9, weapon.arc, 7.6, False, "middle")
            self.text(c, 66, y + 9, weapon.name, 7.6)
            self.text(c, 288, y + 9, weapon.attack_dice, 7.6, False, "middle")
            self.text(c, 338, y + 9, weapon.range, 7.6, False, "middle")
            self.text(c, 371, y + 9, weapon.traits, 6.8)

            y += row_h

        return y + 8

    def draw_traits_notes(self, c, ship, y):
        box_h = 62

        self.rect(c, 22, y, 196, box_h, line_width=0.5)
        self.rect(c, 22, y, 196, 12, fill=colors.HexColor("#F4F4F4"))
        self.text(c, 26, y + 8.3, "SHIP TRAITS", 7.3, True)

        trait_text = ", ".join(ship.traits)
        self.wrapped_text(c, 30, y + 24, trait_text, 180, 7.2, line_gap=10)

        self.rect(c, 226, y, 364, box_h, line_width=0.5)
        self.rect(c, 226, y, 364, 12, fill=colors.HexColor("#F4F4F4"))
        self.text(c, 230, y + 8.3, "NOTES", 7.3, True)

        c.setStrokeColor(colors.HexColor("#777777"))
        for line_y in [y + 27, y + 40, y + 53]:
            c.line(234, self.y(line_y), 582, self.y(line_y))

        return y + box_h + 10

    def wrapped_text(self, c, x, y, text, max_width, size, line_gap=10):
        c.setFont("Helvetica", size)
        words = str(text).split()
        line = ""

        for word in words:
            test_line = f"{line} {word}".strip()

            if c.stringWidth(test_line, "Helvetica", size) <= max_width:
                line = test_line
            else:
                self.text(c, x, y, line, size)
                y += line_gap
                line = word

        if line:
            self.text(c, x, y, line, size)

    def draw_tracks(self, c, ship, y):
        self.draw_track(c, 22, y, "Damage", ship.damage, box=5.8)
        self.draw_track(c, 310, y, "Crew", ship.crew, box=5.2)

        return y + 70

    def draw_track(self, c, x, y, label, value, box):
        total, critical = self.parse_track(value)

        self.text(c, x, y, f"{label} {value}", 8.8, True)

        start_y = y + 9
        spacing = box + 1.25
        per_group = 5
        group_gap = 4.6
        per_row = 30

        for i in range(total):
            row = i // per_row
            col = i % per_row
            group = col // per_group

            px = x + col * spacing + group * group_gap
            py = start_y + row * spacing

            fill = colors.HexColor("#F2D2D2") if i >= total - critical else colors.white
            self.rect(c, px, py, box, box, fill=fill, line_width=0.33)

    def parse_track(self, value):
        parts = str(value).split("/")
        total = int(parts[0])
        critical = int(parts[1]) if len(parts) > 1 else 0
        return total, critical