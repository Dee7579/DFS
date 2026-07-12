# DFS Application Phase 2 — Desktop Shell and Ship Viewer

## Included

- PySide6 desktop application launcher (`dfs_desktop.py`)
- Dashboard and permanent module navigation
- Read-only Ship Viewer using the Phase 1 services
- Name/class search with debounce
- Faction, fleet/era, priority, trait, and weapon filtering
- Canonical platform result table
- Multi-profile selector for era/fleet variants
- Profile statistics, traits, weapons, and platform-specific notes
- Database path discovery without hard-coded machine paths
- Centralized visual theme

## Installation

From the project `Python` folder:

```powershell
py -m pip install -r requirements-desktop.txt
py dfs_desktop.py
```

DFS searches for the database in common project locations, including:

```text
Database/Data/dfs.db
```

A custom location may be supplied with the `DFS_DATABASE_PATH` environment variable.

## Deliberately deferred

- Embedded PDF preview
- Codex tabs
- linked fighter navigation
- multi-select trait/weapon controls
- saved layout and preferences
- Fleet Builder and other modules

These remain separate services/modules rather than being embedded prematurely in the first viewer window.
