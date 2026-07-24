# DFS Tactical Assistant Sprint 002

**Version:** 2.4.0-alpha24  
**Milestone:** Initial Tactical Assistant user interface

## Purpose

Sprint 002 exposes the independent game-state foundation from Sprint 001 through
the DFS desktop application. The Tactical Assistant remains strictly separated
from certified source data:

```text
Certified platform data / dfs.db
        ↓ read-only snapshot
Saved Fleet Builder file
        ↓ expanded per unit
TacticalGameState
        ↓
*.dfs-game.json
```

No Tactical Assistant control writes to `platform_data` or `Database/Data/dfs.db`.

## Delivered

- Enabled **Tactical Assistant** in the main DFS navigation.
- Added `Ctrl+3` as the Tactical Assistant shortcut.
- Added `TacticalGameService` to `ApplicationContext` through the composition root.
- Added **New from Fleet**, **Open Game**, **Save**, and **Save As** workflows.
- Expanded a saved fleet into a hierarchical battle roster showing every
  individual platform, embarked platform, fighter flight, drone, pod, or other
  included craft.
- Added editable game name, turn, and phase controls plus **Advance Turn**.
- Added live Damage, Crew, and Shields controls with printed maximum,
  threshold, and recovery information.
- Added destroyed/lost state, Crew Quality, current Special Action, and
  game-only unit notes.
- Added a read-only source snapshot for traits, weapons, and printed notes.
- Added unsaved-change protection when replacing or closing a game.
- Added a dedicated ignored `games/` folder for `*.dfs-game.json` saves.

## Persistence

Tactical games use the Sprint 001 schema and are saved atomically through
`JSONTacticalGameStore`. Fleet files are never modified when a game is created.
The page stores only its last-used fleet and tactical-game folders in
`SettingsService`.

## Verification

Sprint 002 adds six tests:

- two game-state editing and validation tests;
- four offscreen PySide6 page tests covering roster expansion, track editing,
  turn/phase changes, save, and reopen.

`verify_tactical_sprint_002.cmd` verifies certified source hashes both before
and after the full test suite.

## Next Sprint

Sprint 003 will add live weapon/trait disablement, critical-hit management,
special-action selection support, and faster game-table interaction controls.
