from dataclasses import dataclass, field


@dataclass
class Weapon:
    name: str
    range: str
    arc: str
    attack_dice: int
    traits: str


@dataclass
class Ship:
    name: str
    ship_class: str
    faction: str
    fleet: str

    priority: str
    speed: int
    turn: str
    hull: int

    damage: str
    crew: str
    troops: int
    craft: str

    initiative: str
    in_service: str

    traits: list[str] = field(default_factory=list)
    weapons: list[Weapon] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)