from pathlib import Path

from dfs.database import Database
from dfs.pdf_generator import PDFGenerator


DB_PATH = Path(__file__).resolve().parents[2] / "Database" / "Data" / "dfs.db"
OUTPUT_PATH = Path(__file__).resolve().parent / "output" / "Omega_Destroyer.pdf"

OUTPUT_PATH.parent.mkdir(exist_ok=True)

def main():
    db = Database(DB_PATH)
    ship = db.get_ship("Omega Destroyer")

    if ship is None:
        print("Ship not found.")
        return

    generator = PDFGenerator(OUTPUT_PATH)
    generator.generate_ship_sheet(ship)

    print(f"Generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()