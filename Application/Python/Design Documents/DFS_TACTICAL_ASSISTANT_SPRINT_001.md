# DFS Tactical Assistant Sprint 001

**Status:** Domain and persistence foundation

## Purpose

Sprint 001 establishes the protected live-game boundary before any Tactical
Assistant user interface is added.

The data flow is:

```text
Certified platform data and dfs.db
        ↓ read only
Saved .dfs-fleet.json fleet
        ↓ snapshot/expand
Independent .dfs-game.json tactical state
```

Tactical state never writes to `platform_data` or the canonical `dfs.db`.

## Delivered

- Game-neutral `TacticalGameState` and per-unit `TacticalUnitState` models.
- Separate records for every selected platform and every fighter/craft flight.
- Included craft expanded beneath the platform that carries them.
- Saved fighter replacements and Huge Hangars embarked ships carried into game state.
- Fleet-entry option data preserved for later missile-loadout and rules integration.
- Live tracking for:
  - damage and crippled threshold;
  - crew and skeleton-crew threshold;
  - shields and printed regeneration value;
  - Crew Quality;
  - traits and disabled state;
  - weapons and disabled/destroyed state;
  - critical hits and repair state;
  - special actions;
  - destroyed craft and fighter losses;
  - turn and phase.
- Catalog-backed profile resolver that snapshots canonical profile information.
- Atomic, versioned `.dfs-game.json` persistence.
- End-to-end service that loads `.dfs-fleet.json` and creates a separate game file.
- Tests proving game save/load does not alter protected source files.

## Important boundary

A game file stores a tactical snapshot. Reopening a game does not require and
must not rewrite the source fleet, platform modules, or canonical database.
The source fleet ID and profile IDs remain recorded for traceability.

## Schema

The initial game-file schema version is `1`. Future schema changes must add an
explicit migration rather than silently interpreting incompatible files.

## Not included yet

- Tactical Assistant GUI.
- Automatic ACTA damage/critical resolution.
- Special-action legality and phase enforcement.
- Scenario objectives, victory points, or opposing-fleet management.
- Campaign persistence.

Those belong to later Tactical Assistant sprints after this foundation is
verified and committed.
