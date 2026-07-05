from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


class PDFGenerator:
    def __init__(self, filename):
        self.filename = filename

    def generate_ship_sheet(self, ship):
        c = canvas.Canvas(str(self.filename), pagesize=letter)

        width, height = letter

        # Title
        c.setFont("Helvetica-Bold", 20)
        c.drawString(40, height - 50, ship.name.upper())

        # Priority
        c.setFont("Helvetica", 12)
        c.drawString(40, height - 80, f"Priority: {ship.priority}")

        # Basic Stats
        y = height - 120

        stats = [
            f"Speed: {ship.speed}",
            f"Turn: {ship.turn}",
            f"Hull: {ship.hull}",
            f"Damage: {ship.damage}",
            f"Crew: {ship.crew}",
            f"Troops: {ship.troops}",
            f"Craft: {ship.craft}",
            f"Initiative: {ship.initiative}",
            f"In Service: {ship.in_service}"
        ]

        for stat in stats:
            c.drawString(40, y, stat)
            y -= 18

        # Traits
        y -= 15
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, y, "Traits")

        c.setFont("Helvetica", 12)
        y -= 20

        for trait in ship.traits:
            c.drawString(60, y, "• " + trait)
            y -= 18

        # Weapons
        y -= 20
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, y, "Weapons")

        y -= 25
        c.setFont("Helvetica-Bold", 12)

        c.drawString(40, y, "Weapon")
        c.drawString(250, y, "Range")
        c.drawString(320, y, "Arc")
        c.drawString(380, y, "AD")
        c.drawString(430, y, "Special")

        c.setFont("Helvetica", 12)

        y -= 20

        for weapon in ship.weapons:
            c.drawString(40, y, weapon.name)
            c.drawString(250, y, str(weapon.range))
            c.drawString(320, y, weapon.arc)
            c.drawString(380, y, str(weapon.attack_dice))
            c.drawString(430, y, weapon.traits)
            y -= 18

        c.save()