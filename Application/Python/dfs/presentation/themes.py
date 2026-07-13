"""Official DFS presentation-theme registry.

Only implemented themes are exposed to users. Future theme identities are
registered here so screen and print renderers share stable names and IDs.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PresentationTheme:
    theme_id: str
    label: str
    purpose: str
    implemented: bool = False


THEME_REGISTRY: tuple[PresentationTheme, ...] = (
    PresentationTheme(
        "dfs_standard",
        "DFS Standard",
        "Original tabletop reference sheet optimized for printing and lamination.",
        implemented=True,
    ),
    PresentationTheme(
        "dfs_modern",
        "DFS Modern",
        "Card-based contemporary presentation derived from Platform Explorer.",
    ),
    PresentationTheme(
        "dfs_compact",
        "DFS Compact",
        "High-density layout for printing and viewing larger fleets.",
    ),
    PresentationTheme(
        "dfs_printer_friendly",
        "DFS Printer Friendly",
        "Low-ink monochrome-oriented reference presentation.",
    ),
    PresentationTheme(
        "dfs_classic",
        "DFS Classic",
        "DFS interpretation of the traditional ACTA roster presentation.",
    ),
)


def installed_themes() -> tuple[PresentationTheme, ...]:
    return tuple(theme for theme in THEME_REGISTRY if theme.implemented)
