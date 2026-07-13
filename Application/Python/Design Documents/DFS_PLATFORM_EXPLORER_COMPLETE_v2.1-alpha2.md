# DFS Platform Explorer Complete

**Version:** 2.1.0-alpha2

This milestone completes the first production-ready Platform Explorer feature set.

## Included

- Catalog filtering by name, faction, fleet/era, priority, year, trait, and weapon.
- Compact platform navigator.
- Multi-profile platform workspace.
- Correct DFS weapon ordering.
- Embedded PDF viewing, style selection, external opening, and printing.
- Clickable traits and weapon rules backed by the existing Codex.
- Related-craft navigation from the selected profile.
- Back/Forward navigation history.
- Persistent recent platforms and favorites.
- Side-by-side platform comparison.
- Dynamic game-system identity in the application splash.

## Architecture

The GUI remains a thin layer. Codex lookup is provided by `CodexService`; platform
queries remain in catalog/detail services; document lookup remains in
`DocumentService`. Favorites and recent navigation are user preferences stored
through `QSettings` and do not modify the canonical database.

## Deferred

- DFS logo and application icon.
- Additional PDF renderers such as DFS Modern and DFS Compact.
- Fleet Builder and Game Mode.
