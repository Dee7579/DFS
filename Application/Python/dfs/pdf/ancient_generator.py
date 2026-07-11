from reportlab.lib import colors
from reportlab.pdfgen import canvas

from dfs.pdf.rules_back import draw_rules_back, estimate_rules_back_height

from dfs.pdf.layout import (
    PAGE_WIDTH,
    RED,
    LIGHT_GREY,
    LINE_GREY,
    BLACK,
    WHITE,
)


BASE_PAGE_HEIGHT = 420
FRAME_X = 18
FRAME_Y = 18
FRAME_W = PAGE_WIDTH - 36
CONTENT_X = 22
CONTENT_W = PAGE_WIDTH - 44
SECTION_GAP = 10
FOOTER_SPACE = 28
BODY_FONT = 7.0
BODY_LINE_GAP = 9.0
BOX_SIZE = 6.0
BOX_SPACING = 3.0
GROUP_GAP = 5.0
PER_GROUP = 5
PER_ROW = 50
THRESHOLD_FILL = colors.HexColor("#F2D2D2")


class Drawing:
    def __init__(self, c, page_height):
        self.c = c
        self.page_height = page_height

    def y(self, svg_y):
        return self.page_height - svg_y

    def rect(self, x, y, w, h, fill=None, stroke=BLACK, line_width=0.5):
        self.c.setLineWidth(line_width)
        self.c.setStrokeColor(stroke)
        if fill is not None:
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


class ACTAAncientGenerator:
    def __init__(self, filename):
        self.filename = filename

    def generate_ship_sheet(self, ship):
        front_height = self.estimate_page_height(ship)
        back_height = estimate_rules_back_height(
            ship,
            PAGE_WIDTH,
            include_fleet_rules=True,
        )
        page_height = max(front_height, back_height)

        c = canvas.Canvas(str(self.filename), pagesize=(PAGE_WIDTH, page_height))
        d = Drawing(c, page_height)

        self.draw_frame(d, page_height)
        current_y = 45
        current_y = self.draw_header(d, ship, current_y)
        current_y = self.draw_stat_boxes(d, ship, current_y)
        current_y = self.draw_weapons(d, ship, current_y)
        current_y = self.draw_traits_and_notes(d, ship, current_y)
        current_y = self.draw_damage(d, ship, current_y)

        shields = self.get_shields_from_traits(ship)
        if shields:
            self.draw_shields(d, shields, current_y)

        self.draw_footer(d, page_height)

        c.showPage()
        draw_rules_back(
            c,
            ship,
            page_width=PAGE_WIDTH,
            include_fleet_rules=True,
            sheet_type="Ancient",
            page_height=page_height,
        )

        c.save()

    def estimate_page_height(self, ship):
        current_y = 45 + 48 + 37
        weapon_rows = max(len(ship.weapons), 1)
        current_y += 13 + 12 + weapon_rows * 12 + SECTION_GAP

        trait_lines = self.count_wrapped_lines(
            ", ".join(ship.traits), 180, BODY_FONT
        )
        note_lines = 0
        for note in ship.notes:
            note_lines += self.count_wrapped_lines(note, 344, BODY_FONT) + 1

        panel_body_h = max(
            34,
            10 + trait_lines * BODY_LINE_GAP,
            10 + note_lines * BODY_LINE_GAP,
        )
        current_y += 12 + panel_body_h + SECTION_GAP

        damage_total, damage_threshold = self.parse_track(ship.damage)
        current_y += self.track_panel_height(damage_total, damage_threshold) + SECTION_GAP

        shields = self.get_shields_from_traits(ship)
        if shields:
            shield_total, _ = self.parse_track(shields)
            current_y += self.track_panel_height(shield_total, 0) + SECTION_GAP

        return max(BASE_PAGE_HEIGHT, current_y + FOOTER_SPACE)

    def draw_frame(self, d, page_height):
        d.rect(FRAME_X, FRAME_Y, FRAME_W, page_height - 36, line_width=0.8)
        d.rect(FRAME_X, FRAME_Y, FRAME_W, 13, fill=RED, stroke=RED)
        d.text(
            24,
            27.5,
            "Dee's Fighting Ships | Babylon 5 ACTA Tactical Reference System",
            7.2,
            True,
            color=WHITE,
        )
        d.text(PAGE_WIDTH - 24, 27.5, "Ancient Sheet", 7.2, True, "end", WHITE)

    def draw_header(self, d, ship, y):
        d.text(24, y, ship.faction.upper(), 11.2, True)
        self.draw_smart_title(d, 24, y + 22, ship.name)
        d.text(PAGE_WIDTH - 24, y, ship.priority.upper(), 11.5, True, "end")
        d.text(
            PAGE_WIDTH - 24,
            y + 21,
            f"Initiative: {ship.initiative}",
            8.7,
            True,
            "end",
        )
        d.text(PAGE_WIDTH - 24, y + 36, "Crew Quality: 7", 8.2, True, "end")
        d.line(FRAME_X, y + 48, PAGE_WIDTH - FRAME_X, y + 48)
        return y + 58

    def draw_smart_title(self, d, x, y, title):
        title = str(title).upper()
        max_width = 430
        size = 18
        while size > 13:
            if d.c.stringWidth(title, "Helvetica-Bold", size) <= max_width:
                break
            size -= 0.5
        d.text(x, y, title, size, True)

    def draw_stat_boxes(self, d, ship, y):
        boxes = [
            ("Speed", ship.speed, 54),
            ("Turns", ship.turn, 66),
            ("Hull", ship.hull, 50),
            ("Troops", ship.troops, 58),
            ("Craft", ship.craft, 252),
            ("In Service", ship.in_service, 86),
        ]
        current_x = CONTENT_X
        for label, value, width in boxes:
            self.stat_box(d, current_x, y, width, label, value)
            current_x += width
        return y + 37

    def stat_box(self, d, x, y, w, label, value):
        d.rect(x, y, w, 27, line_width=0.35)
        d.text(x + w / 2, y + 9, label, 6.8, True, "middle")
        self.draw_fitted_center_text(d, x, y + 22, w, value, 8.2, 5.6)

    def draw_weapons(self, d, ship, y):
        x = CONTENT_X
        w = CONTENT_W
        d.rect(x, y, w, 13, fill=LIGHT_GREY)
        d.text(x + 4, y + 9, "WEAPONS", 7.0, True)
        table_y = y + 13
        row_h = 12
        columns = [
            ("ARC", 40),
            ("WEAPON", 205),
            ("RANGE", 58),
            ("AD", 42),
            ("TRAITS", w - 40 - 205 - 58 - 42),
        ]
        current_x = x
        for label, col_w in columns:
            d.rect(current_x, table_y, col_w, row_h, fill=LIGHT_GREY, line_width=0.35)
            d.text(current_x + col_w / 2, table_y + 8.2, label, 6.0, True, "middle")
            current_x += col_w

        row_y = table_y + row_h
        if ship.weapons:
            for weapon in ship.weapons:
                values = [
                    weapon.arc,
                    weapon.name,
                    weapon.range,
                    weapon.attack_dice,
                    weapon.traits,
                ]
                current_x = x
                for value, (_, col_w) in zip(values, columns):
                    d.rect(current_x, row_y, col_w, row_h, line_width=0.35)
                    if col_w <= 58:
                        self.draw_fitted_center_text(
                            d, current_x, row_y + 8.2, col_w, value, 6.0, 4.6
                        )
                    else:
                        self.draw_fitted_left_text(
                            d, current_x + 4, row_y + 8.2, col_w - 8, value, 6.0, 4.5
                        )
                    current_x += col_w
                row_y += row_h
        else:
            d.rect(x, row_y, w, row_h, line_width=0.35)
            d.text(x + 4, row_y + 8.2, "No conventional weapons", 6.0)
            row_y += row_h
        return row_y + SECTION_GAP

    def draw_traits_and_notes(self, d, ship, y):
        gap = 8
        traits_w = 196
        notes_w = CONTENT_W - traits_w - gap
        trait_lines = self.wrap_text(d, ", ".join(ship.traits), traits_w - 16, BODY_FONT)

        note_groups = []
        for note in ship.notes:
            lines = self.wrap_text(d, note, notes_w - 18, BODY_FONT)
            if lines:
                note_groups.append(lines)

        trait_body_h = max(34, 10 + len(trait_lines) * BODY_LINE_GAP)
        note_line_count = sum(len(lines) for lines in note_groups)
        note_body_h = max(
            34,
            10 + note_line_count * BODY_LINE_GAP + max(0, len(note_groups) - 1) * 3,
        )
        body_h = max(trait_body_h, note_body_h)
        total_h = 12 + body_h

        self.draw_text_panel(d, CONTENT_X, y, traits_w, total_h, "SHIP TRAITS", trait_lines)
        self.draw_text_panel(
            d,
            CONTENT_X + traits_w + gap,
            y,
            notes_w,
            total_h,
            "NOTES",
            note_groups,
            grouped=True,
        )
        return y + total_h + SECTION_GAP

    def draw_text_panel(self, d, x, y, w, h, label, content, grouped=False):
        d.rect(x, y, w, h, line_width=0.5)
        d.rect(x, y, w, 12, fill=LIGHT_GREY)
        d.text(x + 4, y + 8.5, label, 7.0, True)
        text_y = y + 24

        if grouped:
            if content:
                for group_index, lines in enumerate(content):
                    for line in lines:
                        d.text(x + 8, text_y, line, BODY_FONT)
                        text_y += BODY_LINE_GAP
                    if group_index < len(content) - 1:
                        text_y += 3
            else:
                self.draw_blank_lines(d, x, y, w, h)
        else:
            if content:
                for line in content:
                    d.text(x + 8, text_y, line, BODY_FONT)
                    text_y += BODY_LINE_GAP
            else:
                self.draw_blank_lines(d, x, y, w, h)

    def draw_blank_lines(self, d, x, y, w, h):
        line_y = y + 25
        while line_y < y + h - 7:
            d.line(x + 8, line_y, x + w - 8, line_y)
            line_y += 13

    def draw_damage(self, d, ship, y):
        return self.draw_track_panel(
            d, CONTENT_X, y, CONTENT_W, "Damage", ship.damage, shade_threshold=True
        ) + SECTION_GAP

    def draw_shields(self, d, shields, y):
        return self.draw_track_panel(
            d, CONTENT_X, y, CONTENT_W, "Shields", shields, shade_threshold=False
        ) + SECTION_GAP

    def draw_track_panel(self, d, x, y, w, label, value, shade_threshold=True):
        total, threshold = self.parse_track(value)
        if not shade_threshold:
            threshold = 0
        rows = self.track_rows(total, threshold)
        header_h = 13
        body_h = 12 + rows * (BOX_SIZE + BOX_SPACING)
        total_h = header_h + body_h
        d.rect(x, y, w, total_h, line_width=0.5)
        d.rect(x, y, w, header_h, fill=LIGHT_GREY, line_width=0.5)
        d.text(x + 5, y + 9, f"{label.upper()} {value}", 7.4, True)
        self.draw_track_boxes(d, x + 8, y + header_h + 8, total, threshold, shade_threshold)
        return y + total_h

    def draw_track_boxes(self, d, x, y, total, threshold, shade_threshold):
        if total <= 0:
            return
        normal_count = total - threshold
        spacing = BOX_SIZE + BOX_SPACING
        for index in range(total):
            if index < normal_count:
                visual_index = index
            else:
                threshold_index = index - normal_count
                threshold_start = ((normal_count + PER_GROUP - 1) // PER_GROUP) * PER_GROUP
                visual_index = threshold_start + threshold_index
            row = visual_index // PER_ROW
            col = visual_index % PER_ROW
            group = col // PER_GROUP
            px = x + col * spacing + group * GROUP_GAP
            py = y + row * spacing
            fill = THRESHOLD_FILL if shade_threshold and index >= normal_count else None
            d.rect(px, py, BOX_SIZE, BOX_SIZE, fill=fill, line_width=0.33)

    def get_shields_from_traits(self, ship):
        for trait in ship.traits:
            trait = str(trait).strip()
            if trait.startswith("Shields"):
                return trait.replace("Shields", "", 1).strip()
        return None

    def parse_track(self, value):
        value = str(value).strip()
        if value in ("", "-", "None", "none"):
            return 0, 0
        parts = value.split("/")
        total = int(parts[0])
        threshold = 0
        if len(parts) > 1:
            try:
                threshold = int(parts[1])
            except ValueError:
                threshold = 0
        return total, threshold

    def track_rows(self, total, threshold):
        if total <= 0:
            return 1
        normal_count = total - threshold
        visual_total = (((normal_count + PER_GROUP - 1) // PER_GROUP) * PER_GROUP) + threshold
        return max(1, (visual_total + PER_ROW - 1) // PER_ROW)

    def track_panel_height(self, total, threshold):
        rows = self.track_rows(total, threshold)
        return 13 + 12 + rows * (BOX_SIZE + BOX_SPACING)

    def wrap_text(self, d, text, max_width, size):
        text = str(text).strip()
        if not text:
            return []
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            candidate = f"{current_line} {word}".strip()
            if d.c.stringWidth(candidate, "Helvetica", size) <= max_width:
                current_line = candidate
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines

    def count_wrapped_lines(self, text, max_width, size):
        text = str(text).strip()
        if not text:
            return 0
        helper = canvas.Canvas(None)
        words = text.split()
        lines = 0
        current_line = ""
        for word in words:
            candidate = f"{current_line} {word}".strip()
            if helper.stringWidth(candidate, "Helvetica", size) <= max_width:
                current_line = candidate
            else:
                if current_line:
                    lines += 1
                current_line = word
        if current_line:
            lines += 1
        return lines

    def draw_fitted_center_text(self, d, x, y, width, value, start_size, minimum_size):
        text = str(value)
        size = start_size
        while size > minimum_size:
            if d.c.stringWidth(text, "Helvetica", size) <= width - 6:
                break
            size -= 0.2
        d.text(x + width / 2, y, text, size, False, "middle")

    def draw_fitted_left_text(self, d, x, y, width, value, start_size, minimum_size):
        text = str(value)
        size = start_size
        while size > minimum_size:
            if d.c.stringWidth(text, "Helvetica", size) <= width:
                break
            size -= 0.2
        d.text(x, y, text, size)

    def draw_footer(self, d, page_height):
        d.text(
            24,
            page_height - 8,
            "DFS ACTA Ancient Sheet v0.1 | Generated from DFS Database",
            5.8,
            False,
        )
