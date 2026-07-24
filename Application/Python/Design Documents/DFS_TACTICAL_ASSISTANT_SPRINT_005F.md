# DFS Tactical Assistant Sprint 005F

## Purpose

Complete the fighter reference header by displaying the two fighter-specific
statistics that were already present in certified source data but not visible in
the Tactical Assistant: Dogfight and Dodge.

## Behavior

For craft units, the selected-unit reference line now derives:

- `Dogfight` from the immutable source-note entry (`Dogfight: +3`, with legacy
  `Dogfight +3` formatting also supported).
- `Dodge` from the immutable platform trait (`Dodge 3+`).

The fields appear after Hull and before Troops. Non-craft platforms do not gain
these fighter-only fields. Missing values are omitted rather than invented.

## Data boundary

This sprint changes presentation and derived display logic only. It contains no
`platform_data` module, no database, and no migration. Existing `.dfs-game.json`
files already retain source notes and traits, so they display the fields when
reopened without a schema change.
