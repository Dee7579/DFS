from __future__ import annotations

import ast
import json
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR.parent.parent / "Database" / "Data" / "dfs.db"
DEFAULT_OUTPUT_DIR = BASE_DIR / "codex_inventory"
DEFAULT_CODEX_PATH = BASE_DIR / "dfs" / "codex" / "b5_acta_codex.py"

CODEX_DICTIONARY_NAMES = {
    "SHIP_TRAITS",
    "WEAPON_TRAITS",
    "NAMED_RULES",
    "FLEET_RULES",
}


# Canonical spelling used by the DFS codex.
ALIASES = {
    "anti fighter": "Anti-Fighter",
    "anti-fighter": "Anti-Fighter",
    "advanced anti fighter": "Advanced Anti-Fighter",
    "advanced anti-fighter": "Advanced Anti-Fighter",
    "double damage": "Double Damage",
    "double-damage": "Double Damage",
    "triple damage": "Triple Damage",
    "triple-damage": "Triple Damage",
    "quad damage": "Quad Damage",
    "quad-damage": "Quad Damage",
    "slow loading": "Slow-Loading",
    "slow-loading": "Slow-Loading",
    "super ap": "Super AP",
    "super-ap": "Super AP",
    "mini beam": "Mini-Beam",
    "mini-beam": "Mini-Beam",
    "twin linked": "Twin-Linked",
    "twin-linked": "Twin-Linked",
    "one shot": "One-Shot",
    "one-shot": "One-Shot",
    "self repairing": "Self-Repairing",
    "self-repairing": "Self-Repairing",
    "jump engine": "Jump Engine",
    "advanced jump engine": "Advanced Jump Engine",
    "flight computer": "Flight Computer",
    "adaptive armour": "Adaptive Armour",
    "gravitic energy grid": "Gravitic Energy Grid",
    "energy mine": "Energy Mine",
    "mass driver": "Mass Driver",
    "comm disruptor": "Comms Disruptor",
    "comms disruptor": "Comms Disruptor",
    "interceptor": "Interceptors",
    "interceptors": "Interceptors",
    "shield": "Shields",
    "shields": "Shields",
    "carrier": "Carrier",
    "fleet carrier": "Fleet Carrier",
    "command": "Command",
    "dodge": "Dodge",
    "stealth": "Stealth",
    "escort": "Escort",
    "scout": "Scout",
    "breaching pod": "Breaching Pod",
    "atmospheric": "Atmospheric",
    "agile": "Agile",
    "lumbering": "Lumbering",
    "precise": "Precise",
    "accurate": "Accurate",
    "beam": "Beam",
    "ap": "AP",
    "sap": "SAP",
    "super ap": "Super AP",
}


# Rules whose trailing value is part of the platform statistic, but not
# part of the codex lookup key.
PARAMETERIZED_RULES = {
    "Advanced Anti-Fighter",
    "Anti-Fighter",
    "Carrier",
    "Command",
    "Dodge",
    "Gravitic Energy Grid",
    "Interceptors",
    "Self-Repairing",
    "Shields",
    "Stealth",
}


SUSPICIOUS_PATTERNS = [
    r"\bCampaigns?\b",
    r"\bRefits?\b",
    r"\bOther Duties\b",
    r"\bpage\s+\d+\b",
    r"\brounding\b",
    r"\bhalve\b",
    r"\bweapon system\b",
    r"\brange\b",
    r"\bapplied once\b",
]


def connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def clean_spacing(value: str) -> str:
    value = str(value).strip()
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\s*,\s*", ", ", value)
    return value


def title_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def canonicalize_basic(value: str) -> str:
    value = clean_spacing(value)
    lookup = title_key(value)

    if lookup in ALIASES:
        return ALIASES[lookup]

    return value


def normalize_parameterized_trait(value: str) -> tuple[str, str | None]:
    """Return a normalized codex key and any trailing rule value.

    The final token is treated as a parameter only when it has a numeric
    game-value form such as ``4``, ``+2``, ``3+``, ``2D6``, ``20/5``, or
    ``28/2D6``. This lets future parameterized traits work without adding a
    new hard-coded regular expression for every rule name.
    """
    value = clean_spacing(value)

    parameter_match = re.match(
        r"^(.+?)\s+([+-]?\d+\+?|\d+[dD]\d+|\d+/(?:\d+|\d+[dD]\d+))$",
        value,
    )

    if parameter_match:
        base = canonicalize_basic(parameter_match.group(1))
        parameter = parameter_match.group(2).upper()
        return base, parameter

    return canonicalize_basic(value), None


def split_weapon_traits(value: str) -> list[str]:
    value = clean_spacing(value)

    if not value:
        return []

    return [
        token.strip()
        for token in value.split(",")
        if token.strip()
    ]


def is_suspicious(value: str) -> bool:
    text = clean_spacing(value)

    if len(text) > 80:
        return True

    return any(
        re.search(pattern, text, flags=re.IGNORECASE)
        for pattern in SUSPICIOUS_PATTERNS
    )


def get_ship_traits(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
            t.trait,
            s.ship_name,
            f.name AS faction,
            fl.name AS fleet
        FROM traits t
        JOIN acta_profiles ap
            ON t.profile_id = ap.profile_id
        JOIN ships s
            ON ap.ship_id = s.ship_id
        JOIN factions f
            ON s.faction_id = f.faction_id
        JOIN fleet_lists fl
            ON ap.fleet_list_id = fl.fleet_list_id
        ORDER BY t.trait, f.name, s.ship_name;
        """
    ).fetchall()


def get_weapon_traits(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
            w.traits,
            w.name AS weapon_name,
            s.ship_name,
            f.name AS faction,
            fl.name AS fleet
        FROM weapons w
        JOIN acta_profiles ap
            ON w.profile_id = ap.profile_id
        JOIN ships s
            ON ap.ship_id = s.ship_id
        JOIN factions f
            ON s.faction_id = f.faction_id
        JOIN fleet_lists fl
            ON ap.fleet_list_id = fl.fleet_list_id
        WHERE TRIM(COALESCE(w.traits, '')) <> ''
        ORDER BY w.traits, f.name, s.ship_name, w.name;
        """
    ).fetchall()


def get_platform_notes(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
            ap.notes,
            s.ship_name,
            f.name AS faction,
            fl.name AS fleet
        FROM acta_profiles ap
        JOIN ships s
            ON ap.ship_id = s.ship_id
        JOIN factions f
            ON s.faction_id = f.faction_id
        JOIN fleet_lists fl
            ON ap.fleet_list_id = fl.fleet_list_id
        WHERE TRIM(COALESCE(ap.notes, '')) <> ''
        ORDER BY f.name, s.ship_name;
        """
    ).fetchall()


def get_fleets(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
            f.name AS faction,
            fl.name AS fleet,
            fl.initiative
        FROM fleet_lists fl
        JOIN factions f
            ON fl.faction_id = f.faction_id
        ORDER BY f.name, fl.name;
        """
    ).fetchall()


def add_example(
    examples: dict[str, list[dict[str, str]]],
    key: str,
    example: dict[str, str],
    maximum: int = 5,
) -> None:
    existing = examples[key]

    if example in existing:
        return

    if len(existing) < maximum:
        existing.append(example)


def build_inventory(conn: sqlite3.Connection) -> dict:
    ship_rule_counts: Counter[str] = Counter()
    weapon_rule_counts: Counter[str] = Counter()

    ship_rule_parameters: dict[str, Counter[str]] = defaultdict(Counter)
    ship_examples: dict[str, list[dict[str, str]]] = defaultdict(list)
    weapon_examples: dict[str, list[dict[str, str]]] = defaultdict(list)

    suspicious_ship_traits: list[dict[str, str]] = []
    suspicious_weapon_traits: list[dict[str, str]] = []

    for row in get_ship_traits(conn):
        original = clean_spacing(row["trait"])

        if is_suspicious(original):
            suspicious_ship_traits.append(
                {
                    "trait": original,
                    "ship": row["ship_name"],
                    "faction": row["faction"],
                    "fleet": row["fleet"],
                }
            )
            continue

        key, parameter = normalize_parameterized_trait(original)
        ship_rule_counts[key] += 1

        if parameter:
            ship_rule_parameters[key][parameter] += 1

        add_example(
            ship_examples,
            key,
            {
                "original": original,
                "ship": row["ship_name"],
                "faction": row["faction"],
            },
        )

    for row in get_weapon_traits(conn):
        original_string = clean_spacing(row["traits"])

        if is_suspicious(original_string):
            suspicious_weapon_traits.append(
                {
                    "trait_string": original_string,
                    "weapon": row["weapon_name"],
                    "ship": row["ship_name"],
                    "faction": row["faction"],
                    "fleet": row["fleet"],
                }
            )
            continue

        for token in split_weapon_traits(original_string):
            key, parameter = normalize_parameterized_trait(token)
            weapon_rule_counts[key] += 1

            add_example(
                weapon_examples,
                key,
                {
                    "original": token,
                    "weapon": row["weapon_name"],
                    "ship": row["ship_name"],
                    "faction": row["faction"],
                },
            )

    fleet_rows = [
        {
            "faction": row["faction"],
            "fleet": row["fleet"],
            "initiative": row["initiative"],
        }
        for row in get_fleets(conn)
    ]

    notes = []

    for row in get_platform_notes(conn):
        for line in str(row["notes"]).splitlines():
            line = clean_spacing(line)

            if line:
                notes.append(
                    {
                        "note": line,
                        "ship": row["ship_name"],
                        "faction": row["faction"],
                        "fleet": row["fleet"],
                    }
                )

    ship_rules = []

    for key in sorted(ship_rule_counts, key=str.casefold):
        ship_rules.append(
            {
                "key": key,
                "occurrences": ship_rule_counts[key],
                "parameters": dict(
                    sorted(
                        ship_rule_parameters[key].items(),
                        key=lambda item: item[0].casefold(),
                    )
                ),
                "examples": ship_examples[key],
            }
        )

    weapon_rules = []

    for key in sorted(weapon_rule_counts, key=str.casefold):
        weapon_rules.append(
            {
                "key": key,
                "occurrences": weapon_rule_counts[key],
                "examples": weapon_examples[key],
            }
        )

    all_rule_keys = sorted(
        set(ship_rule_counts) | set(weapon_rule_counts),
        key=str.casefold,
    )

    return {
        "summary": {
            "ship_rule_keys": len(ship_rules),
            "weapon_rule_keys": len(weapon_rules),
            "all_unique_rule_keys": len(all_rule_keys),
            "fleet_lists": len(fleet_rows),
            "platform_notes": len(notes),
            "suspicious_ship_traits": len(suspicious_ship_traits),
            "suspicious_weapon_trait_strings": len(suspicious_weapon_traits),
        },
        "all_rule_keys": all_rule_keys,
        "ship_rules": ship_rules,
        "weapon_rules": weapon_rules,
        "fleets": fleet_rows,
        "platform_notes": notes,
        "suspicious_ship_traits": suspicious_ship_traits,
        "suspicious_weapon_traits": suspicious_weapon_traits,
    }


def write_json(inventory: dict, output_path: Path) -> None:
    output_path.write_text(
        json.dumps(
            inventory,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def write_markdown(inventory: dict, output_path: Path) -> None:
    summary = inventory["summary"]
    lines = [
        "# DFS B5 ACTA Codex Inventory",
        "",
        "Generated from the current DFS database.",
        "",
        "## Summary",
        "",
        f"- Unique ship-rule keys: {summary['ship_rule_keys']}",
        f"- Unique weapon-rule keys: {summary['weapon_rule_keys']}",
        f"- Combined unique rule keys: {summary['all_unique_rule_keys']}",
        f"- Fleet lists: {summary['fleet_lists']}",
        f"- Platform notes for review: {summary['platform_notes']}",
        f"- Suspicious ship traits: {summary['suspicious_ship_traits']}",
        (
            "- Suspicious weapon-trait strings: "
            f"{summary['suspicious_weapon_trait_strings']}"
        ),
        "",
        "## Combined Rule Keys",
        "",
    ]

    lines.extend(
        f"- {key}"
        for key in inventory["all_rule_keys"]
    )

    lines.extend(
        [
            "",
            "## Ship Rules",
            "",
        ]
    )

    for entry in inventory["ship_rules"]:
        lines.append(f"### {entry['key']}")
        lines.append("")
        lines.append(f"Occurrences: {entry['occurrences']}")

        if entry["parameters"]:
            values = ", ".join(entry["parameters"].keys())
            lines.append(f"Observed values: {values}")

        lines.append("")

    lines.extend(
        [
            "## Weapon Rules",
            "",
        ]
    )

    for entry in inventory["weapon_rules"]:
        lines.append(f"### {entry['key']}")
        lines.append("")
        lines.append(f"Occurrences: {entry['occurrences']}")
        lines.append("")

    lines.extend(
        [
            "## Fleet Lists",
            "",
            "| Faction | Fleet | Initiative |",
            "|---|---|---:|",
        ]
    )

    for row in inventory["fleets"]:
        lines.append(
            f"| {row['faction']} | {row['fleet']} | {row['initiative']} |"
        )

    lines.extend(
        [
            "",
            "## Platform Notes Requiring Review",
            "",
        ]
    )

    for row in inventory["platform_notes"]:
        lines.append(
            f"- **{row['ship']}** ({row['fleet']}): {row['note']}"
        )

    lines.extend(
        [
            "",
            "## Suspicious Ship Traits",
            "",
        ]
    )

    if inventory["suspicious_ship_traits"]:
        for row in inventory["suspicious_ship_traits"]:
            lines.append(
                f"- **{row['ship']}**: `{row['trait']}`"
            )
    else:
        lines.append("- None found.")

    lines.extend(
        [
            "",
            "## Suspicious Weapon-Trait Strings",
            "",
        ]
    )

    if inventory["suspicious_weapon_traits"]:
        for row in inventory["suspicious_weapon_traits"]:
            lines.append(
                (
                    f"- **{row['ship']} — {row['weapon']}**: "
                    f"`{row['trait_string']}`"
                )
            )
    else:
        lines.append("- None found.")

    output_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def write_codex_stub(inventory: dict, output_path: Path) -> None:
    ship_keys = [
        entry["key"]
        for entry in inventory["ship_rules"]
    ]
    weapon_keys = [
        entry["key"]
        for entry in inventory["weapon_rules"]
    ]

    lines = [
        '"""Babylon 5 ACTA rules codex.',
        "",
        "Populate each empty text field with verified official wording.",
        '"""',
        "",
        "",
        "SHIP_TRAITS = {",
    ]

    for key in ship_keys:
        lines.extend(
            [
                f"    {key!r}: {{",
                "        'category': 'Ship Trait',",
                "        'text': '',",
                "        'source': '',",
                "    },",
            ]
        )

    lines.extend(
        [
            "}",
            "",
            "",
            "WEAPON_TRAITS = {",
        ]
    )

    for key in weapon_keys:
        lines.extend(
            [
                f"    {key!r}: {{",
                "        'category': 'Weapon Trait',",
                "        'text': '',",
                "        'source': '',",
                "    },",
            ]
        )

    lines.extend(
        [
            "}",
            "",
            "",
            "NAMED_RULES = {",
            "}",
            "",
            "",
            "FLEET_RULES = {",
        ]
    )

    for row in inventory["fleets"]:
        lines.append(f"    {row['fleet']!r}: [],")

    lines.extend(
        [
            "}",
            "",
        ]
    )

    output_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )



def read_codex_keys(codex_path: Path) -> dict[str, set[str]]:
    results = {
        "SHIP_TRAITS": set(),
        "WEAPON_TRAITS": set(),
        "NAMED_RULES": set(),
        "FLEET_RULES": set(),
    }

    if not codex_path.exists():
        return results

    tree = ast.parse(
        codex_path.read_text(encoding="utf-8"),
        filename=str(codex_path),
    )

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue

        if len(node.targets) != 1:
            continue

        target = node.targets[0]

        if not isinstance(target, ast.Name):
            continue

        if target.id not in CODEX_DICTIONARY_NAMES:
            continue

        if not isinstance(node.value, ast.Dict):
            continue

        for key_node in node.value.keys:
            if (
                isinstance(key_node, ast.Constant)
                and isinstance(key_node.value, str)
            ):
                results[target.id].add(key_node.value)

    return results


def compare_inventory_to_codex(
    inventory: dict,
    codex_keys: dict[str, set[str]],
) -> dict:
    inventory_ship = {
        entry["key"]
        for entry in inventory["ship_rules"]
    }

    inventory_weapon = {
        entry["key"]
        for entry in inventory["weapon_rules"]
    }

    codex_rule_keys = (
        codex_keys["SHIP_TRAITS"]
        | codex_keys["WEAPON_TRAITS"]
        | codex_keys["NAMED_RULES"]
    )

    inventory_rule_keys = inventory_ship | inventory_weapon

    inventory_fleets = {
        row["fleet"]
        for row in inventory["fleets"]
    }

    codex_fleets = codex_keys["FLEET_RULES"]

    missing_rules = sorted(
        inventory_rule_keys - codex_rule_keys,
        key=str.casefold,
    )

    stale_rules = sorted(
        codex_rule_keys - inventory_rule_keys,
        key=str.casefold,
    )

    missing_fleets = sorted(
        inventory_fleets - codex_fleets,
        key=str.casefold,
    )

    stale_fleets = sorted(
        codex_fleets - inventory_fleets,
        key=str.casefold,
    )

    return {
        "codex_found": any(codex_keys.values()),
        "missing_rules": missing_rules,
        "stale_rules": stale_rules,
        "missing_fleets": missing_fleets,
        "stale_fleets": stale_fleets,
        "is_complete": not missing_rules and not missing_fleets,
    }


def write_validation_json(validation: dict, output_path: Path) -> None:
    output_path.write_text(
        json.dumps(
            validation,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def print_section(title: str, values: list[str]) -> None:
    print()
    print(title)

    if not values:
        print("  None")
        return

    for value in values:
        print(f"  - {value}")



def main(
    db_path: Path = DEFAULT_DB_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    codex_path: Path = DEFAULT_CODEX_PATH,
) -> None:
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    with connect(db_path) as conn:
        inventory = build_inventory(conn)

    codex_keys = read_codex_keys(codex_path)
    validation = compare_inventory_to_codex(
        inventory,
        codex_keys,
    )

    inventory["codex_validation"] = validation
    inventory["codex_path"] = str(codex_path)

    json_path = output_dir / "b5_acta_codex_inventory.json"
    markdown_path = output_dir / "b5_acta_codex_inventory.md"
    stub_path = output_dir / "b5_acta_codex_stub.py"
    validation_path = output_dir / "b5_acta_codex_validation.json"

    write_json(inventory, json_path)
    write_markdown(inventory, markdown_path)
    write_codex_stub(inventory, stub_path)
    write_validation_json(validation, validation_path)

    summary = inventory["summary"]

    print()
    print("DFS B5 ACTA Codex Extractor / Validator v3")
    print("---------------------------------------")
    print(f"Database: {db_path}")
    print(f"Codex:    {codex_path}")
    print()
    print(f"Ship-rule keys:          {summary['ship_rule_keys']}")
    print(f"Weapon-rule keys:        {summary['weapon_rule_keys']}")
    print(f"Combined unique keys:    {summary['all_unique_rule_keys']}")
    print(f"Fleet lists:             {summary['fleet_lists']}")
    print(f"Platform notes:          {summary['platform_notes']}")
    print(
        "Suspicious trait data:   "
        f"{summary['suspicious_ship_traits'] + summary['suspicious_weapon_trait_strings']}"
    )

    if not codex_path.exists():
        print()
        print("Codex status: NOT FOUND")
        print("The inventory and starter codex stub were generated.")
    else:
        print()
        print(
            "Codex status: "
            + ("COMPLETE" if validation["is_complete"] else "INCOMPLETE")
        )

        print_section(
            "NEW RULES DETECTED",
            validation["missing_rules"],
        )

        print_section(
            "NEW FLEET ENTRIES DETECTED",
            validation["missing_fleets"],
        )

        print_section(
            "CODEX RULES NOT USED BY CURRENT DATABASE",
            validation["stale_rules"],
        )

        print_section(
            "CODEX FLEET ENTRIES NOT USED BY CURRENT DATABASE",
            validation["stale_fleets"],
        )

    print()
    print("Created:")
    print(f"  {json_path}")
    print(f"  {markdown_path}")
    print(f"  {stub_path}")
    print(f"  {validation_path}")
    print()


if __name__ == "__main__":
    main()
