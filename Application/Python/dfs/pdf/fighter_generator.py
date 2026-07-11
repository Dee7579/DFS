from reportlab.pdfgen import canvas

from dfs.pdf.rules_back import draw_rules_back, estimate_rules_back_height

from dfs.pdf.layout import (
    RED,
    LIGHT_GREY,
    LINE_GREY,
    BLACK,
    WHITE,
)


FIGHTER_PAGE_WIDTH = 396
BASE_PAGE_HEIGHT = 270

FRAME_MARGIN = 10
CONTENT_X = 16
CONTENT_W = FIGHTER_PAGE_WIDTH - 32

HEADER_TOP = 37
STATS_TOP = 82
SECTION_GAP = 8
FOOTER_SPACE = 26

HEADER_FONT = 6.5
BODY_FONT = 6.0
BODY_LINE_GAP = 8.0


class Drawing:
    def __init__(self, c, page_height):
        self.c = c
        self.page_height = page_height

    def y(self, svg_y):
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

        if fill:
            self.c.setFillColor(fill)
            self.c.rect(
                x,
                self.y(y + h),
                w,
                h,
                fill=True,
                stroke=True,
            )
        else:
            self.c.rect(
                x,
                self.y(y + h),
                w,
                h,
                fill=False,
                stroke=True,
            )

    def text(
        self,
        x,
        y,
        txt,
        size=8,
        bold=False,
        anchor="start",
        color=BLACK,
    ):
        self.c.setFillColor(color)
        self.c.setFont(
            "Helvetica-Bold" if bold else "Helvetica",
            size,
        )

        txt = str(txt)

        if anchor == "end":
            self.c.drawRightString(x, self.y(y), txt)
        elif anchor == "middle":
            self.c.drawCentredString(x, self.y(y), txt)
        else:
            self.c.drawString(x, self.y(y), txt)

    def line(
        self,
        x1,
        y1,
        x2,
        y2,
        color=LINE_GREY,
        line_width=0.5,
    ):
        self.c.setStrokeColor(color)
        self.c.setLineWidth(line_width)
        self.c.line(
            x1,
            self.y(y1),
            x2,
            self.y(y2),
        )


class ACTAFighterGenerator:
    def __init__(self, filename):
        self.filename = filename

    def generate_ship_sheet(self, ship):
        front_height = self.estimate_page_height(ship)
        back_height = estimate_rules_back_height(
            ship,
            FIGHTER_PAGE_WIDTH,
            include_fleet_rules=False,
        )
        page_height = max(front_height, back_height)

        c = canvas.Canvas(
            str(self.filename),
            pagesize=(FIGHTER_PAGE_WIDTH, page_height),
        )

        d = Drawing(c, page_height)

        self.draw_frame(d, page_height)

        current_y = self.draw_header(d, ship)
        current_y = self.draw_stats(d, ship, current_y)
        current_y = self.draw_traits(d, ship, current_y)
        current_y = self.draw_weapons(d, ship, current_y)
        current_y = self.draw_notes(d, ship, current_y)

        self.draw_footer(d, page_height)

        c.showPage()
        draw_rules_back(
            c,
            ship,
            page_width=FIGHTER_PAGE_WIDTH,
            include_fleet_rules=False,
            sheet_type="Fighter",
            page_height=page_height,
        )

        c.save()

    def estimate_page_height(self, ship):
        current_y = STATS_TOP

        current_y += 28 + SECTION_GAP

        trait_lines = self.count_wrapped_lines(
            ", ".join(ship.traits),
            CONTENT_W - 12,
            BODY_FONT,
        )

        trait_body_height = max(
            17,
            8 + trait_lines * BODY_LINE_GAP,
        )

        current_y += 11 + trait_body_height + SECTION_GAP

        weapon_rows = max(len(ship.weapons), 1)
        current_y += 13 + 12 + weapon_rows * 12 + SECTION_GAP

        notes = self.filtered_notes(ship)
        note_lines = 0

        for note in notes:
            note_lines += self.count_wrapped_lines(
                note,
                CONTENT_W - 16,
                BODY_FONT,
            )
            note_lines += 1

        if notes:
            notes_body_height = max(
                28,
                8 + note_lines * BODY_LINE_GAP,
            )
        else:
            notes_body_height = 34

        current_y += 11 + notes_body_height

        needed_height = current_y + FOOTER_SPACE

        return max(BASE_PAGE_HEIGHT, needed_height)

    def draw_frame(self, d, page_height):
        d.rect(
            FRAME_MARGIN,
            FRAME_MARGIN,
            FIGHTER_PAGE_WIDTH - 20,
            page_height - 20,
            line_width=0.8,
        )

        d.rect(
            FRAME_MARGIN,
            FRAME_MARGIN,
            FIGHTER_PAGE_WIDTH - 20,
            12,
            fill=RED,
            stroke=RED,
        )

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
        era = (
            ship.fleet
            .replace(ship.faction, "")
            .replace("-", "")
            .strip()
        )

        if era:
            header_text = (
                f"{ship.faction.upper()} — {era.upper()}"
            )
        else:
            header_text = ship.faction.upper()

        dogfight = self.get_note_value(
            ship,
            "Dogfight",
        )

        d.text(
            16,
            HEADER_TOP,
            header_text,
            8.6,
            True,
        )

        self.draw_smart_title(
            d,
            16,
            HEADER_TOP + 19,
            ship.name,
        )

        d.text(
            FIGHTER_PAGE_WIDTH - 16,
            HEADER_TOP,
            ship.priority.upper(),
            9.5,
            True,
            "end",
        )

        d.text(
            FIGHTER_PAGE_WIDTH - 16,
            HEADER_TOP + 15,
            f"Dogfight: {dogfight}",
            7.5,
            True,
            "end",
        )

        d.text(
            FIGHTER_PAGE_WIDTH - 16,
            HEADER_TOP + 29,
            f"In Service: {ship.in_service}",
            7.2,
            True,
            "end",
        )

        d.line(
            FRAME_MARGIN,
            74,
            FIGHTER_PAGE_WIDTH - FRAME_MARGIN,
            74,
        )

        return STATS_TOP

    def draw_smart_title(self, d, x, y, title):
        title = str(title).upper()

        max_width = 245
        size = 13.5

        while size > 9:
            width = d.c.stringWidth(
                title,
                "Helvetica-Bold",
                size,
            )

            if width <= max_width:
                break

            size -= 0.5

        d.text(
            x,
            y,
            title,
            size,
            True,
        )

    def draw_stats(self, d, ship, y):
        h = 28
        wing = self.get_wing_note(ship)

        stats = [
            ("Speed", ship.speed, 48),
            ("Turns", ship.turn, 48),
            ("Hull", ship.hull, 48),
            ("Troops", ship.troops, 52),
            ("Wing", wing, 164),
        ]

        current_x = CONTENT_X

        for label, value, width in stats:
            d.rect(
                current_x,
                y,
                width,
                h,
                line_width=0.4,
            )

            d.text(
                current_x + width / 2,
                y + 9,
                label,
                6,
                True,
                "middle",
            )

            self.draw_fitted_center_text(
                d,
                current_x,
                y + 22,
                width,
                value,
                6.5,
                5.0,
            )

            current_x += width

        return y + h + SECTION_GAP

    def draw_traits(self, d, ship, y):
        x = CONTENT_X
        w = CONTENT_W

        traits_text = ", ".join(ship.traits)

        trait_lines = self.wrap_text(
            d,
            traits_text,
            w - 12,
            BODY_FONT,
        )

        body_h = max(
            17,
            8 + len(trait_lines) * BODY_LINE_GAP,
        )

        total_h = 11 + body_h

        d.rect(
            x,
            y,
            w,
            total_h,
            line_width=0.5,
        )

        d.rect(
            x,
            y,
            w,
            11,
            fill=LIGHT_GREY,
        )

        d.text(
            x + 4,
            y + 8,
            "TRAITS",
            HEADER_FONT,
            True,
        )

        text_y = y + 22

        for line in trait_lines:
            d.text(
                x + 6,
                text_y,
                line,
                BODY_FONT,
            )
            text_y += BODY_LINE_GAP

        return y + total_h + SECTION_GAP

    def draw_weapons(self, d, ship, y):
        x = CONTENT_X
        w = CONTENT_W

        d.rect(
            x,
            y,
            w,
            13,
            fill=LIGHT_GREY,
        )

        d.text(
            x + 4,
            y + 9,
            "WEAPONS",
            HEADER_FONT,
            True,
        )

        table_y = y + 13
        row_h = 12

        columns = [
            ("ARC", 30),
            ("WEAPON", 140),
            ("RANGE", 45),
            ("AD", 32),
            (
                "TRAITS",
                w - 30 - 140 - 45 - 32,
            ),
        ]

        current_x = x

        for label, col_w in columns:
            d.rect(
                current_x,
                table_y,
                col_w,
                row_h,
                fill=LIGHT_GREY,
                line_width=0.35,
            )

            d.text(
                current_x + col_w / 2,
                table_y + 8.2,
                label,
                5.6,
                True,
                "middle",
            )

            current_x += col_w

        row_y = table_y + row_h

        if ship.weapons:
            for weapon in ship.weapons:
                current_x = x

                values = [
                    weapon.arc,
                    weapon.name,
                    weapon.range,
                    weapon.attack_dice,
                    weapon.traits,
                ]

                for value, (_, col_w) in zip(
                    values,
                    columns,
                ):
                    d.rect(
                        current_x,
                        row_y,
                        col_w,
                        row_h,
                        line_width=0.35,
                    )

                    if col_w <= 45:
                        self.draw_fitted_center_text(
                            d,
                            current_x,
                            row_y + 8.2,
                            col_w,
                            value,
                            5.6,
                            4.5,
                        )
                    else:
                        self.draw_fitted_left_text(
                            d,
                            current_x + 3,
                            row_y + 8.2,
                            col_w - 6,
                            value,
                            5.6,
                            4.3,
                        )

                    current_x += col_w

                row_y += row_h
        else:
            d.rect(
                x,
                row_y,
                w,
                row_h,
                line_width=0.35,
            )

            d.text(
                x + 4,
                row_y + 8.2,
                "No conventional weapons",
                5.6,
            )

            row_y += row_h

        return row_y + SECTION_GAP

    def draw_notes(self, d, ship, y):
        x = CONTENT_X
        w = CONTENT_W

        notes = self.filtered_notes(ship)

        wrapped_notes = []

        for note in notes:
            lines = self.wrap_text(
                d,
                note,
                w - 16,
                BODY_FONT,
            )

            if lines:
                wrapped_notes.append(lines)

        if wrapped_notes:
            line_count = sum(
                len(lines)
                for lines in wrapped_notes
            )

            body_h = max(
                28,
                8
                + line_count * BODY_LINE_GAP
                + (len(wrapped_notes) - 1) * 3,
            )
        else:
            body_h = 34

        total_h = 11 + body_h

        d.rect(
            x,
            y,
            w,
            total_h,
            line_width=0.5,
        )

        d.rect(
            x,
            y,
            w,
            11,
            fill=LIGHT_GREY,
        )

        d.text(
            x + 4,
            y + 8,
            "NOTES",
            HEADER_FONT,
            True,
        )

        if wrapped_notes:
            text_y = y + 22

            for note_index, lines in enumerate(
                wrapped_notes,
            ):
                for line in lines:
                    d.text(
                        x + 8,
                        text_y,
                        line,
                        BODY_FONT,
                    )

                    text_y += BODY_LINE_GAP

                if note_index < len(wrapped_notes) - 1:
                    text_y += 3
        else:
            line_y = y + 23

            while line_y < y + total_h - 6:
                d.line(
                    x + 8,
                    line_y,
                    x + w - 8,
                    line_y,
                )

                line_y += 11

        return y + total_h

    def draw_footer(self, d, page_height):
        d.text(
            16,
            page_height - 6,
            "DFS ACTA Fighter Sheet v0.4 | Generated from DFS Database",
            5.2,
            False,
        )

    def filtered_notes(self, ship):
        notes = []

        for note in ship.notes:
            note = str(note).strip()

            if not note:
                continue

            if note.startswith("Dogfight:"):
                continue

            if note.startswith("Wing of"):
                continue

            notes.append(note)

        return notes

    def get_note_value(self, ship, label):
        prefix = f"{label}:"

        for note in ship.notes:
            note = str(note)

            if note.startswith(prefix):
                return note.replace(
                    prefix,
                    "",
                    1,
                ).strip()

        return "-"

    def get_wing_note(self, ship):
        for note in ship.notes:
            note = str(note).strip()

            if note.startswith("Wing of "):
                return note.replace(
                    "Wing of ",
                    "",
                    1,
                )

        return "-"

    def wrap_text(
        self,
        d,
        text,
        max_width,
        size,
        bold=False,
    ):
        text = str(text).strip()

        if not text:
            return []

        font_name = (
            "Helvetica-Bold"
            if bold
            else "Helvetica"
        )

        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            candidate = (
                f"{current_line} {word}".strip()
            )

            width = d.c.stringWidth(
                candidate,
                font_name,
                size,
            )

            if width <= max_width:
                current_line = candidate
            else:
                if current_line:
                    lines.append(current_line)

                current_line = word

        if current_line:
            lines.append(current_line)

        return lines

    def count_wrapped_lines(
        self,
        text,
        max_width,
        size,
        bold=False,
    ):
        text = str(text).strip()

        if not text:
            return 0

        font_name = (
            "Helvetica-Bold"
            if bold
            else "Helvetica"
        )

        words = text.split()
        lines = 0
        current_line = ""

        for word in words:
            candidate = (
                f"{current_line} {word}".strip()
            )

            width = canvas.Canvas(
                None
            ).stringWidth(
                candidate,
                font_name,
                size,
            )

            if width <= max_width:
                current_line = candidate
            else:
                if current_line:
                    lines += 1

                current_line = word

        if current_line:
            lines += 1

        return lines

    def draw_fitted_center_text(
        self,
        d,
        x,
        y,
        width,
        value,
        start_size,
        minimum_size,
    ):
        text = str(value)
        size = start_size

        while size > minimum_size:
            text_width = d.c.stringWidth(
                text,
                "Helvetica",
                size,
            )

            if text_width <= width - 6:
                break

            size -= 0.2

        d.text(
            x + width / 2,
            y,
            text,
            size,
            False,
            "middle",
        )

    def draw_fitted_left_text(
        self,
        d,
        x,
        y,
        width,
        value,
        start_size,
        minimum_size,
    ):
        text = str(value)
        size = start_size

        while size > minimum_size:
            text_width = d.c.stringWidth(
                text,
                "Helvetica",
                size,
            )

            if text_width <= width:
                break

            size -= 0.2

        d.text(
            x,
            y,
            text,
            size,
        )