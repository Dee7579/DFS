# DFS Release Sprint 002: Tactical Playtest Refinements

## Purpose

Apply the thirteen findings from the first tabletop playtest of the Tactical
Assistant while preserving certified platform data, the canonical database, and
existing `.dfs-game.json` saves.

## Compact combat workspace

- Keep the core statistics, Damage/Crew/Shields, Weapons, Disposition, and
  Critical Results close together in a compact, scrollable detail pane.
- Preserve each section's natural minimum height so controls never overlap;
  scrolling is preferred whenever the available height is insufficient.
- Show Disposition and Critical Results side by side on wide displays and stack
  them vertically on narrow workspaces to avoid horizontal crowding.
- Move Traits, Source Notes, and Unit Notes into compact tabs.
- Represent carried fighters with one row per fighter type and carrier, using
  linked Ready, Launched, and Destroyed counts while retaining individual flight
  records below the summary row.
- Let the application navigation collapse into a persistent icon rail, with
  automatic collapse at narrow window sizes.

## Rules help

- Add a Turn Order button to the Game State row.
- Make the Weapons heading open the official Attack Table:
  `1 = Bulkhead`, `2-5 = Solid`, and `6 = Critical`.
- Keep hover descriptions open until the pointer leaves or moves to another item.
- Explain Disposition choices both while choosing and after selection.
- Show the live Damage Control calculation, modifiers, required die result, and
  any condition that blocks a repair attempt.
- Provide a modeless, searchable Quick Reference window. Contextual help and the
  Quick Reference use the same catalogue so their wording cannot drift apart.

## Tactical-state corrections

- Rename or clear a tactical ship name from its roster context menu; the platform
  class remains visible and fleet-source files are not rewritten.
- Mark repairable criticals as New during the turn inflicted and Repairable from
  the following turn. Permanent and Repaired states remain explicit.
- Display current Speed and compulsory half-current-Speed movement while Running
  Adrift.
- Resolve Double, Triple, and Quad Damage criticals by multiplying both the normal
  Solid Hit and the critical table's extra Damage/Crew values. Reset the selector
  to x1 after application and retain exact undo behavior.

## Save compatibility

The JSON loader supplies defaults for fields introduced in this sprint. Older
saves continue to load, and new saves retain tactical names, critical infliction
turns, multipliers, and individual fighter states.

## Protected-data boundary

This release contains no platform-data module, database change, data migration,
or recertification. Certified sources and `Database/Data/dfs.db` remain unchanged.

## Verification

- Run the focused playtest-refinement domain and UI tests.
- Run the complete Tactical Assistant regression suite.
- Run the complete DFS regression suite.
- Verify certified-source hashes before and after testing.
- Validate the canonical database.
- Build and smoke-test the Windows portable archive and installer.
