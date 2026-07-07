from pathlib import Path

from dfs.database import Database
from dfs.pdf import ACTAClassicGenerator


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR.parent.parent / "Database" / "Data" / "dfs.db"
OUTPUT_DIR = BASE_DIR / "output"


def safe_filename(name):
    return (
        str(name)
        .replace("/", "-")
        .replace("\\", "-")
        .replace(":", "-")
        .replace("*", "")
        .replace("?", "")
        .replace('"', "")
        .replace("<", "")
        .replace(">", "")
        .replace("|", "")
        .replace(" ", "_")
    )


def clean_era_name(faction, fleet):
    era = str(fleet).replace(str(faction), "").replace("-", "").strip()

    if era.lower().startswith("the "):
        era = era[4:]

    return era or "General"


def faction_code(faction):
    codes = {
        "Earth Alliance": "EA",
        "Centauri Republic": "CR",
        "Narn Regime": "NR",
        "Minbari Federation": "MF",
        "Vorlons": "VO",
        "Shadows": "SH",
        "League of Non-Aligned Worlds": "LN",
        "Drakh": "DR",
        "Raiders": "RA",
    }

    return codes.get(faction, "XX")


def era_code(era):
    codes = {
        "Early Years": "EY",
        "Third Age": "3A",
        "Crusade Era": "CE",
        "General": "GN",
    }

    return codes.get(era, "XX")


def main():
    db = Database(DB_PATH)

    ships = db.get_all_ships()

    print(f"Generating {len(ships)} ship sheet(s)...")

    for ship in ships:

        era = clean_era_name(ship.faction, ship.fleet)

        faction_folder = safe_filename(ship.faction)
        era_folder = safe_filename(era)

        output_folder = OUTPUT_DIR / faction_folder / era_folder
        output_folder.mkdir(parents=True, exist_ok=True)

        prefix = f"{faction_code(ship.faction)}-{era_code(era)}"

        filename = (
            output_folder
            / f"{prefix}_{safe_filename(ship.name)}.pdf"
        )

        generator = ACTAClassicGenerator(filename)
        generator.generate_ship_sheet(ship)

        print(f"Generated: {filename}")

    print("Done.")


if __name__ == "__main__":
    main()