"""Generate a readable Letter-size fleet roster for print packets."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from dfs.domain.fleet.included_craft import parse_included_craft
from dfs.domain.fleet.huge_hangars import embarked_profile_ids


@dataclass(frozen=True, slots=True)
class GeneratedFleetRoster:
    path: Path


class FleetRosterGenerator:
    def __init__(self, catalog, platform_details, fleet_service) -> None:
        self._catalog = catalog
        self._details = platform_details
        self._fleet_service = fleet_service
        self._detail_cache: dict[int, object | None] = {}

    def _detail_for_profile(self, profile) -> object | None:
        cached = self._detail_cache.get(profile.profile_id, ...)
        if cached is not ...:
            return cached
        from dfs.domain.catalog import PlatformFilter
        result = None
        for summary in self._catalog.search(PlatformFilter(fleet_list_ids=(profile.fleet_list_id,), limit=1000)):
            detail = self._details.get(summary.ship_id)
            if detail and any(candidate.profile_id == profile.profile_id for candidate in detail.profiles):
                result = detail
                break
        self._detail_cache[profile.profile_id] = result
        return result

    def generate(self, fleet, output_path: Path) -> GeneratedFleetRoster:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        summary = self._fleet_service.summarize(fleet)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DFS Fleet Title", parent=styles["Title"], fontName="Helvetica-Bold",
            fontSize=18, leading=21, spaceAfter=6,
        )
        subtitle_style = ParagraphStyle(
            "DFS Fleet Subtitle", parent=styles["Normal"], fontSize=9,
            textColor=colors.HexColor("#506176"), leading=12,
        )
        section_style = ParagraphStyle(
            "DFS Section", parent=styles["Heading2"], fontName="Helvetica-Bold",
            fontSize=11, leading=14, spaceBefore=8, spaceAfter=5,
        )
        cell_style = ParagraphStyle(
            "DFS Cell", parent=styles["Normal"], fontSize=8, leading=10,
        )
        small_right = ParagraphStyle(
            "DFS Small Right", parent=cell_style, alignment=TA_RIGHT,
        )

        doc = SimpleDocTemplate(
            str(output_path), pagesize=letter,
            rightMargin=0.4 * inch, leftMargin=0.4 * inch,
            topMargin=0.4 * inch, bottomMargin=0.4 * inch,
            title=f"DFS Fleet Roster - {fleet.name}",
        )

        story = [Paragraph(fleet.name or "Untitled Fleet", title_style)]

        faction_name = "—"
        fleet_name = "—"
        for entry in fleet.entries:
            profile = self._details.get_profile(entry.profile_id)
            if profile is None:
                continue
            detail = self._detail_for_profile(profile)
            fleet_name = profile.fleet_name
            if detail is not None:
                faction_name = detail.faction_name
            break

        meta_lines = [
            f"Game system: {fleet.game_system_id}",
            f"Construction profile: {fleet.construction_profile_id}",
            f"Faction: {faction_name}",
            f"Fleet / Era: {fleet_name}",
            f"Year: {fleet.selected_year if fleet.selected_year is not None else 'Any year'}",
            f"Budget: {summary.budget_label or '—'}",
            f"Remaining: {summary.remaining_label or '—'}",
        ]
        story.append(Paragraph(" &nbsp; | &nbsp; ".join(meta_lines), subtitle_style))
        story.append(Spacer(1, 0.12 * inch))
        story.append(Paragraph("Fleet Roster", section_style))

        rows = [[
            Paragraph("Platform", cell_style),
            Paragraph("Ship Name", cell_style),
            Paragraph("Priority", cell_style),
            Paragraph("Qty", small_right),
            Paragraph("Included Craft", cell_style),
        ]]

        for entry in fleet.entries:
            profile = self._details.get_profile(entry.profile_id)
            if profile is None:
                rows.append([
                    Paragraph(f"Unknown profile {entry.profile_id}", cell_style),
                    Paragraph(entry.vessel_name or "", cell_style),
                    Paragraph("—", cell_style),
                    Paragraph(str(entry.quantity), small_right),
                    Paragraph("—", cell_style),
                ])
                continue

            detail = self._detail_for_profile(profile)
            platform_name = detail.name if detail is not None else f"Profile {entry.profile_id}"
            craft = []
            for included in parse_included_craft(profile.craft):
                qty = included.quantity * entry.quantity
                craft.append(f"{qty} {included.printed_name}")
            for embarked_profile_id in embarked_profile_ids(entry.options):
                embarked_profile = self._details.get_profile(embarked_profile_id)
                embarked_detail = self._detail_for_profile(embarked_profile) if embarked_profile is not None else None
                embarked_name = embarked_detail.name if embarked_detail is not None else f"Profile {embarked_profile_id}"
                craft.append(f"Embarked ship: {embarked_name}")

            rows.append([
                Paragraph(platform_name, cell_style),
                Paragraph(entry.vessel_name or "—", cell_style),
                Paragraph(profile.priority_level, cell_style),
                Paragraph(str(entry.quantity), small_right),
                Paragraph("<br/>".join(craft) if craft else "—", cell_style),
            ])

        roster = Table(rows, colWidths=[2.25*inch, 1.35*inch, 0.8*inch, 0.45*inch, 2.25*inch], repeatRows=1)
        roster.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCE3EC")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#172033")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#AEB8C5")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F5F8")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(roster)

        story.append(Paragraph("Validation", section_style))
        if summary.validation.messages:
            for message in summary.validation.messages:
                label = message.severity.value.upper()
                story.append(Paragraph(f"<b>{label}:</b> {message.message}", cell_style))
        else:
            story.append(Paragraph("Fleet legal under the selected construction profile.", cell_style))

        if fleet.notes.strip():
            story.append(Paragraph("Fleet Notes", section_style))
            story.append(Paragraph(fleet.notes.replace("\n", "<br/>") , cell_style))

        doc.build(story)
        return GeneratedFleetRoster(output_path)
