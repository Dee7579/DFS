# DFS Tactical Assistant Sprint 003

## Combat Status and Critical Effects

Sprint 003 turns the initial Tactical Assistant workspace into a practical live
combat tracker while preserving the certified-source boundary established in
Sprint 001.

## Layout

The left column contains **Game State** above **Battle Roster**. Both sections
therefore have exactly the same width. The selected unit's information begins
at the top of the wider right column.

The right column now separates:

- printed and effective ship statistics
- Damage, Crew, and Shields
- Weapons
- Unit Status
- Critical Results
- Traits
- printed source notes
- player notes

## Arithmetic tracks

Damage, Crew, and Shields accept three entry forms:

- `24` sets the current value to 24
- `-8` subtracts 8
- `+4` restores 4

All results are clamped between zero and the printed maximum.

## Threshold effects

Crossing the printed Damage threshold latches the ship as Crippled. Crossing
the printed Crew threshold latches Skeleton Crew. Repairs above a threshold do
not erase the state once it has been reached.

Crippled automatically changes the effective display to:

- half Speed
- one fewer turn, minimum one, at 45 degrees
- Super-Manoeuvrable becomes two 45-degree turns
- Shields offline
- one weapon per fire arc reminder

The interface also reminds the player to resolve the published 4+ trait-loss
rolls and use the trait controls to record the results.

Skeleton Crew automatically applies:

- no Special Actions
- one weapon system per turn
- a -2 Damage Control modifier
- half Troops

Flight Computer ignores the appropriate Skeleton Crew penalties while active.
Modified Speed, Turn, Troops, and weapon AD values are displayed in bold red;
the original printed value is retained in the tooltip.

## Critical results

The Critical Results selector contains every result from the core ACTA critical
hit tables. Fixed Damage and Crew losses are populated automatically. Results
that use dice ask the player to enter the rolled totals. Random weapon, arc, or
trait results ask the player to select the rolled target before applying the
critical.

Applying a critical records an independent history item and automatically
applies its persistent effect, including:

- Damage and Crew losses
- highest applicable Speed penalty
- stacking weapon AD penalties
- Running Adrift
- Special Action restrictions
- Damage Control restrictions
- temporary Hull Breach Damage Control restriction for the inflicted turn
- weapon, arc, or trait outages
- Troop losses

Repairable critical effects can be marked repaired. Vital Systems results remain
permanent, matching the published rules. Raw Damage, Crew, and Troop losses are
not restored when a critical effect is repaired.

## Weapons and traits

Weapons have their own table with Arc, Weapon, Range, AD, Traits, and Status.
Each weapon can be disabled or destroyed without changing its source profile.
Inactive rows are muted and struck through.

Traits have the same independent Disabled and Destroyed controls. Hovering a
trait displays the active DFS Codex rule and source when available. Disabled,
destroyed, critically lost, and Crippled-offline traits are muted and struck
through.

## Special Actions

The Special Action field is populated with the core ACTA actions plus the
currently catalogued faction-specific actions. Actions that the selected unit
cannot currently attempt remain visible but disabled, with a tooltip explaining
the restriction.

This sprint records the selected Special Action and applies availability
restrictions. Full automation of each action's turn-by-turn mechanical effects
is deliberately deferred to a later combat-automation sprint.

## Persistence and source integrity

All new state remains optional within schema-version 1 `*.dfs-game.json` files,
so Sprint 001 and Sprint 002 saves remain compatible. Tactical data never writes
to `platform_data` or the canonical `dfs.db`.
