from reportlab.pdfgen import canvas

from dfs.pdf.layout import (
    PAGE_WIDTH,
    estimate_page_height,
    RED,
    LIGHT_GREY,
    LINE_GREY,
    BLACK,
    WHITE,
    CONTENT_X,
    CONTENT_W,
)
from dfs.pdf.weapons import draw_weapon_table
from dfs.pdf.tracks import draw_damage_and_crew


class Drawing:
    def __init__(self, c, page_height):
        self.c = c
        self.page_height = page_height

    def y(self, svg_y):
        return self.page_height - svg_y

    def rect(self, x, y, w, h, fill=None, stroke=BLACK, line_width=0.5):
        self.c.setLineWidth(line_width)
        self.c.setStrokeColor(stroke)

        if fill:
            self.c.setFillColor(fill)
            self.c.rect(x, self.y(y + h), w, h, fill=True, stroke=True)
        else:
            self.c.rect(x, self.y(y + h), w, h, fill=False, stroke=True)

    def text(self, x, y, txt, size=8, bold=False, anchor="start", color=BLACK):
        self.c.setFillColor(color)
        self.c.setFont("Helvetica-Bold" if bold else "Helvetica", size)

        txt = str(txt)

        if anchor == "end":
            self.c.drawRightString(x, self.y(y), txt)
        elif anchor == "middle":
            self.c.drawCentredString(x, self.y(y), txt)
        else:
            self.c.drawString(x, self.y(y), txt)

    def line(self, x1, y1, x2, y2, color=LINE_GREY, line_width=0.5):
        self.c.setStrokeColor(color)
        self.c.setLineWidth(line_width)
        self.c.line(x1, self.y(y1), x2, self.y(y2))


class ACTAClassicGenerator:
    def __init__(self, filename):
        self.filename = filename

    def generate_ship_sheet(self, ship):
        page_height = estimate_page_height(ship)
        c = canvas.Canvas(str(self.filename), pagesize=(PAGE_WIDTH, page_height))
        d = Drawing(c, page_height)

        self.draw_frame(d, page_height)

        current_y = 45
        current_y = self.draw_header(d, ship, current_y)
        current_y = self.draw_stat_boxes(d, ship, current_y)
        current_y = draw_weapon_table(d, ship, CONTENT_X, current_y, CONTENT_W)
        current_y = self.draw_traits_notes(d, ship, current_y)
        current_y = draw_damage_and_crew(d, ship, CONTENT_X, current_y)

        self.draw_footer(d, page_height)

        c.save()

    def draw_frame(self, d, page_height):
        d.rect(18, 18, 576, page_height - 36, line_width=0.8)

        d.rect(
            18,
            18,
            576,
            13,
            fill=RED,
            stroke=RED,
        )

        d.text(
            24,
            27.5,
            "Dee's Fighting Ships | Babylon 5 ACTA Tactical Reference System",
            7.2,
            True,
            color=WHITE,
        )

        d.text(
            588,
            27.5,
            "Generated Ship Sheet",
            7.2,
            True,
            "end",
            WHITE,
        )

    def draw_header(self, d, ship, y):
        era = ship.fleet.replace(ship.faction, "").replace("-", "").strip()

        if era:
            header_text = f"{ship.faction.upper()} — {era.upper()}"
        else:
            header_text = ship.faction.upper()

        d.text(24, y, header_text, 11.2, True)
        d.text(24, y + 21, ship.name.upper(), 18, True)

        d.text(588, y, ship.priority.upper(), 11.5, True, "end")
        d.text(588, y + 21, f"Initiative: {ship.initiative}", 8.7, True, "end")

        d.text(24, y + 41, "SHIP NAME", 6.8, True)
        d.text(458, y + 41, "CREW QUALITY", 6.8, True)

        d.line(80, y + 42, 414, y + 42)
        d.line(535, y + 42, 575, y + 42)
        d.line(18, y + 55, 594, y + 55)

        return y + 65

    def draw_stat_boxes(self, d, ship, y):
        self.stat_box(d, 22, y, 52, "Speed", ship.speed)
        self.stat_box(d, 74, y, 64, "Turns", ship.turn)
        self.stat_box(d, 138, y, 48, "Hull", ship.hull)
        self.stat_box(d, 186, y, 56, "Troops", ship.troops)
        self.stat_box(d, 242, y, 260, "Craft", ship.craft)
        self.stat_box(d, 502, y, 88, "In Service", ship.in_service)

        return y + 37

    def stat_box(self, d, x, y, w, label, value):
        d.rect(x, y, w, 27, line_width=0.35)
        d.text(x + w / 2, y + 9, label, 6.8, True, "middle")
        d.text(x + w / 2, y + 22, value, 8.2, False, "middle")

    def draw_traits_notes(self, d, ship, y):
        box_h = 62

        d.rect(22, y, 196, box_h, line_width=0.5)
        d.rect(22, y, 196, 12, fill=LIGHT_GREY)
        d.text(26, y + 8.3, "SHIP TRAITS", 7.3, True)

        self.wrapped_text(
            d,
            30,
            y + 24,
            ", ".join(ship.traits),
            180,
            7.2,
            10,
        )

        d.rect(226, y, 364, box_h, line_width=0.5)
        d.rect(226, y, 364, 12, fill=LIGHT_GREY)
        d.text(230, y + 8.3, "NOTES", 7.3, True)

        for line_y in [y + 27, y + 40, y + 53]:
            d.line(234, line_y, 582, line_y)

        return y + box_h + 10

    def wrapped_text(self, d, x, y, text, max_width, size, line_gap):
        c = d.c
        c.setFont("Helvetica", size)

        words = str(text).split()
        line = ""

        for word in words:
            test_line = f"{line} {word}".strip()

            if c.stringWidth(test_line, "Helvetica", size) <= max_width:
                line = test_line
            else:
                d.text(x, y, line, size)
                y += line_gap
                line = word

        if line:
            d.text(x, y, line, size)

    def draw_footer(self, d, page_height):
        d.text(
            24,
            page_height - 8,
            "DFS ACTA Classic Sheet v0.1 | Generated from DFS Database",
            5.8,
            False,
        )