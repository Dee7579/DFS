"""B5 ACTA profiles purchased as multiple ships for one priority choice."""
from __future__ import annotations

from math import ceil
from typing import Mapping

# Fleet Lists printed entries marked "Patrol (Two Ships)".
GROUPED_PURCHASE_SIZES: dict[int, int] = {
    6318: 2,  # Haven-class Patrol Boat
    6456: 2,  # Sho’Kos-class Patrol Cutter
    6457: 2,  # Sho’Kov-class Torpedo Cutter
    6481: 2,  # Tethys-class Cutter
    6482: 2,  # Tethys-class Laser Boat
    6483: 2,  # Tethys-class Missile Boat
}


def grouped_purchase_size(profile_id: int) -> int:
    return GROUPED_PURCHASE_SIZES.get(int(profile_id), 1)


def purchased_choice_count(
    profile_id: int, quantity: int, options: Mapping[str, object] | None = None
) -> int:
    """Return priority choices consumed by one roster entry.

    New grouped purchases are stored as separate quantity-one vessel rows.  One
    row in each linked purchase group carries the choice cost and the other row
    carries zero cost.  Legacy quantity-two entries remain supported.
    """
    options = options or {}
    if "grouped_purchase_charge" in options:
        return max(0, int(options.get("grouped_purchase_charge", 0)))
    size = grouped_purchase_size(profile_id)
    return ceil(max(0, int(quantity)) / size)


def grouped_purchase_label(profile_id: int) -> str:
    size = grouped_purchase_size(profile_id)
    return "" if size == 1 else f"Purchased in groups of {size}; one group costs one priority choice."
