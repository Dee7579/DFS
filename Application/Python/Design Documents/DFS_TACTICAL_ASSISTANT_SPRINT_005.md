# DFS Tactical Assistant Sprint 005

## Purpose

Sprint 005 adds scenario-aware battle administration while preserving the
certified database and platform modules as read-only source material.

## Scenario selection

Game State contains a scenario selector with:

- None
- Random Standard Scenario
- Rulebook standard scenarios
- Powers & Principalities standard scenarios
- Rulebook historical scenarios
- Powers & Principalities Deep Space Tournament scenarios

Random selection excludes historical and tournament scenarios. Scenario
selection also records the scenario Priority Level and the local player's role
when applicable. The panel displays a concise game-length and victory reminder;
the complete stored reminder is available as a tooltip.

## Battle roster

The Battle Roster uses official platform names. A vessel name remains visible
in the selected-unit display and the roster tooltip.

Independently purchased fighter flights are grouped beneath an expandable
purchased-craft row. Each flight remains a separate tactical unit with its own
Ready, Launched, and Lost state.

## Platform disposition

Platforms support these explicit dispositions:

- Operational
- Running Adrift
- Destroyed
- Surrendered
- Tactical Withdrawal

Crew loss and active critical effects may also derive Running Adrift without
rewriting certified source data.

## Threshold correction

Crippled and Skeleton Crew remain persistent battle-state consequences. Two
confirmed correction actions suppress a status that was applied only because
of mistaken data entry. Recovering above the threshold clears the correction
suppression; crossing the threshold again reapplies the normal status.

## Victory Point support

The End Game report automatically totals unit-derived points yielded to the
opponent when the selected scenario uses standard Victory Points. It handles:

- destroyed or Running Adrift platforms
- surrendered platforms
- tactical withdrawals when the scenario awards them
- Crippled and Skeleton Crew platforms
- independently purchased fighter flights that are lost

Scenario objectives requiring table knowledge remain a manual scenario/objective
bonus. The report shows the stored scenario victory reminder so the player can
enter those points without the application guessing.

## Persistence

The version-1 `*.dfs-game.json` format gains optional fields for scenario,
priority, player role, scenario objectives, unit disposition, and threshold
corrections. Missing fields receive backward-compatible defaults.

## Integrity boundary

This sprint writes only tactical game-state JSON and application settings. It
contains no database and no `platform_data` modules. Verification checks the
certified sources before and after the complete test suite.

## Deferred

A two-fleet authoritative game model and local-network Host/Join synchronization
are reserved for Sprint 006. Sprint 005 deliberately does not simulate an
opponent device or infer table-position objectives.
