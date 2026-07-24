# DFS Tactical Assistant Sprint 004

## Purpose

Refine the live combat workflow after the first Sprint 003 playtest. This sprint fixes signed arithmetic input, fully resolves ordinary carried fighters, improves critical-result handling, adds carried-craft launch state, exposes Special Action rules, and introduces the first end-game battle report.

## Delivered

### Damage, Crew, and Shields

- Current-value editors now use a line-edit implementation that accepts signed expressions reliably on Windows/Qt.
- `-8` subtracts eight, `+4` restores four, and `24` sets the current value directly.
- Existing plus/minus step buttons remain available.

### Carried craft

- Printed included craft are conservatively resolved to their canonical DFS craft profiles using the same normalized-name approach used by Fleet Builder printing.
- Resolved carried fighters now display their canonical weapons, traits, notes, and statistics.
- Older Sprint 001-003 game files with blank carried-craft snapshots are enriched on load from the read-only catalog.
- Each carried craft row has a Ready/Launched selector directly in the Battle Roster. Destroyed craft display Lost.
- Craft launch state is stored in the independent `.dfs-game.json` file.

### Critical Results

- Hovering over the Critical Results group title displays the first Systems Table roll: 1-2 Engines, 3 Reactor, 4 Weapons, 5 Crew, 6 Vital Systems.
- Clicking the title opens the same chart in a message box.
- Damage and Crew dice expressions have Roll buttons while retaining manual entry.
- Random is available for critical target selection. Multi-target results select distinct eligible targets.
- A compact Undo button removes the most recently applied critical and restores the exact pre-application Damage, Crew, threshold state, destroyed state, and Special Action.

### Special Actions

- Selecting a Special Action displays its Crew Quality check and effect immediately below the selector.
- Unavailable actions continue to show their reason in red.

### End Game

- A compact End Game button appears beside Advance Turn.
- The Battle Report dialog records the player's Victory Points, opponent Victory Points, result, scenario/report notes, turn, force losses, crippled and Skeleton Crew ships, carried-craft status, and active critical effects.
- Because Tactical Assistant currently loads one fleet, scenario Victory Point totals remain manually entered rather than guessed from incomplete opponent/scenario information.
- Battle-report values persist in the `.dfs-game.json` file.

## Data boundary

This sprint does not modify `Database/Data/dfs.db` or any `platform_data` module. All live state remains in independent Tactical Assistant objects and `.dfs-game.json` files.
