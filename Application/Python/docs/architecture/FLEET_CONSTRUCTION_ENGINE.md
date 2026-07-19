# DFS Fleet Construction Engine

**Milestone:** Sprint 002A
**Status:** Foundation

## Purpose

The Fleet Manager is a thin presentation layer. It edits a game-neutral `Fleet`
and asks a registered construction profile to calculate cost and legality.

## Core rule

A fleet entry references a **profile ID**, not merely a canonical platform ID.
This preserves faction, era, priority, service date, and variant-specific data.

## Built-in construction profiles

- `b5_acta_priority_standard` — official Babylon 5 ACTA priority system.
- `generic_points` — numeric points supplied through entry options or a future cost provider.
- `no_validation` — scenario and sandbox use.

## ACTA authority

The standard priority profile uses the final Fleet Allocation Point and mixed
breakdown tables printed on page 12 of *Powers & Principalities*. The exact
legal single-point breakdowns are encoded explicitly. The implementation does
not approximate the table with simple binary fractions.

The first foundation validates standard priority arithmetic, fleet-list
membership, and year availability. Faction-specific allies, replacement craft,
purchase groups, unique limits, and special-priority platforms are extension
rules to be registered before the Fleet Manager is declared complete.

## Persistence

Fleet files use versioned UTF-8 JSON with the extension `.dfs-fleet.json`.
The format stores profile IDs and player choices, never copied platform stats.
This keeps the database as the source of truth and allows schema migration.

## Dependency direction

```text
Fleet Manager UI
    -> FleetConstructionService
        -> FleetConstructionProfile
        -> PlatformRepository
        -> JSONFleetStore
```
