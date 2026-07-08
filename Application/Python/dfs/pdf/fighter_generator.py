from reportlab.pdfgen import canvas

from dfs.pdf.layout import RED, LIGHT_GREY, LINE_GREY, BLACK, WHITE


FIGHTER_PAGE_WIDTH = 396
FIGHTER_PAGE_HEIGHT = 306
MARGIN = 14
CONTENT_X = 18
CONTENT_W = FIGHTER_PAGE_WIDTH - 36


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


class ACTAFighterGenerator:
    def __init__(self, filename):
        self.filename = filename

    def generate_ship_sheet(self, ship):
        c = canvas.Canvas(
            str(self.filename),
            pagesize=(FIGHTER_PAGE_WIDTH, FIGHTER_PAGE_HEIGHT),
        )
        d = Drawing(c, FIGHTER_PAGE_HEIGHT)

        self.draw_frame(d)
        self.draw_header(d, ship)
        self.draw_stats(d, ship)
        self.draw_traits(d, ship)
        self.draw_weapons(d, ship)
        self.draw_notes(d, ship)
        self.draw_footer(d)

        c.save()

    def draw_frame(self, d):
        d.rect(10, 10, FIGHTER_PAGE_WIDTH - 20, FIGHTER_PAGE_HEIGHT - 20, line_width=0.8)
        d.rect(10, 10, FIGHTER_PAGE_WIDTH - 20, 12, fill=RED, stroke=RED)

        d.text(
            16,
            18.5,
            "Dee's Fighting Ships | Babylon 5 ACTA",
            6.2,
            True,
            color=WHITE,
        )

        d.text(
            FIGHTER_PAGE_WIDTH - 16,
            18.5,
            "Fighter Sheet",
            6.2,
            True,
            "end",
            WHITE,
        )

    def draw_header(self, d, ship):
        era = ship.fleet.replace(ship.faction, "").replace("-", "").strip()
        header_text = f"{ship.faction.upper()} — {era.upper()}" if era else ship.faction.upper()

        dogfight = self.get_note_value(ship, "Dogfight")

        d.text(16, 37, header_text, 8.6, True)
        d.text(16, 56, ship.name.upper(), 13.5, True)

        d.text(FIGHTER_PAGE_WIDTH - 16, 37, ship.priority.upper(), 9.5, True, "end")
        d.text(FIGHTER_PAGE_WIDTH - 16, 52, f"Dogfight: {dogfight}", 7.5, True, "end")
        d.text(FIGHTER_PAGE_WIDTH - 16, 66, f"In Service: {ship.in_service}", 7.2, True, "end")

        d.text(16, 83, "NAME", 5.8, True)
        d.text(244, 83, "CREW QUALITY", 5.8, True)

        d.line(50, 84, 220, 84)
        d.line(318, 84, 376, 84)
        d.line(10, 96, FIGHTER_PAGE_WIDTH - 10, 96)

    def draw_stats(self, d, ship):
        y = 106
        x = 16
        h = 28

        wing = self.get_wing_note(ship)

        stats = [
            ("Speed", ship.speed, 48),
            ("Turns", ship.turn, 48),
            ("Hull", ship.hull, 48),
            ("Troops", ship.troops, 52),
            ("Wing", wing, 164),
        ]

        current_x = x

        for label, value, width in stats:
            d.rect(current_x, y, width, h, line_width=0.4)
            d.text(current_x + width / 2, y + 9, label, 6, True, "middle")
            d.text(current_x + width / 2, y + 22, value, 6.5, False, "middle")
            current_x += width

    def draw_traits(self, d, ship):
        x = 16
        y = 141
        w = FIGHTER_PAGE_WIDTH - 32
        h = 28

        d.rect(x, y, w, h, line_width=0.5)
        d.rect(x, y, w, 11, fill=LIGHT_GREY)
        d.text(x + 4, y + 8, "TRAITS", 6.5, True)
        d.text(x + 6, y + 21, ", ".join(ship.traits), 6.4)

    def draw_weapons(self, d, ship):
        x = 16
        y = 177
        w = FIGHTER_PAGE_WIDTH - 32

        d.rect(x, y, w, 13, fill=LIGHT_GREY)
        d.text(x + 4, y + 9, "WEAPONS", 6.5, True)

        table_y = y + 13
        row_h = 12

        columns = [
            ("ARC", 30),
            ("WEAPON", 140),
            ("RANGE", 45),
            ("AD", 32),
            ("TRAITS", w - 30 - 140 - 45 - 32),
        ]

        current_x = x

        for label, col_w in columns:
            d.rect(current_x, table_y, col_w, row_h, fill=LIGHT_GREY, line_width=0.35)
            d.text(current_x + col_w / 2, table_y + 8.2, label, 5.6, True, "middle")
            current_x += col_w

        row_y = table_y + row_h

        for weapon in ship.weapons:
            current_x = x
            values = [
                weapon.arc,
                weapon.name,
                weapon.range,
                weapon.attack_dice,
                weapon.traits,
            ]

            for value, (_, col_w) in zip(values, columns):
                d.rect(current_x, row_y, col_w, row_h, line_width=0.35)

                if col_w <= 45:
                    d.text(current_x + col_w / 2, row_y + 8.2, value, 5.6, False, "middle")
                else:
                    d.text(current_x + 3, row_y + 8.2, value, 5.6)

                current_x += col_w

            row_y += row_h

    def draw_notes(self, d, ship):
        y = 238
        h = 42
        x = 16
        w = FIGHTER_PAGE_WIDTH - 32

        d.rect(x, y, w, h, line_width=0.5)
        d.rect(x, y, w, 11, fill=LIGHT_GREY)
        d.text(x + 4, y + 8, "NOTES", 6.5, True)

        notes = [
            str(note)
            for note in ship.notes
            if not str(note).startswith("Dogfight:")
            and not str(note).startswith("Wing of")
        ]

        if notes:
            d.text(x + 6, y + 22, " | ".join(notes), 6)
        else:
            d.line(x + 8, y + 23, x + w - 8, y + 23)
            d.line(x + 8, y + 34, x + w - 8, y + 34)

    def draw_footer(self, d):
        d.text(
            16,
            FIGHTER_PAGE_HEIGHT - 6,
            "DFS ACTA Fighter Sheet v0.3 | Generated from DFS Database",
            5.2,
            False,
        )

    def get_note_value(self, ship, label):
        prefix = f"{label}:"

        for note in ship.notes:
            note = str(note)
            if note.startswith(prefix):
                return note.replace(prefix, "").strip()

        return "-"

    def get_wing_note(self, ship):
        for note in ship.notes:
            note = str(note)
            if note.startswith("Wing of"):
                return note.replace("Wing of ", "")

        return "-"