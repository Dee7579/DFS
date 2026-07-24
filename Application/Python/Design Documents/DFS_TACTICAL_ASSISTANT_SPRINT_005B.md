# DFS Tactical Assistant Sprint 005B

## Complete Scenario Help and Compact Random Controls

### Purpose

Complete the table-use scenario workflow identified during Sprint 005A review.
The active Scenario header now carries the complete operational text needed to
set up and play the selected scenario, while the redundant summary row has been
removed from the visible Game State panel.

### Complete scenario help

Every scenario record now provides its full player-facing rules sections:

- source;
- fleets and any fixed-force restrictions;
- pre-battle preparation;
- scenario rules;
- game length; and
- victory conditions or Deep Space Tournament Battle Grades.

The catalogue includes the two remaining Rulebook historical scenarios,
`Border Dispute` and `Hunting the Hunters`, bringing the Tactical Assistant
scenario catalogue to 36 entries.

Hovering over the active Scenario title displays the complete text. Clicking the
title opens the same text in the rules box. The help changes immediately when a
new scenario is selected.

### Random Priority and role

Small Random buttons now sit beside Priority and Role.

- Priority uses the published 2d6 table: Patrol on 4 or less, Skirmish on 5-6,
  Raid on 7-8, Battle on 9-10, and War on 11 or more.
- Role randomly selects Attacker or Defender.

Both results are written to the independent tactical game state and persist in
the `.dfs-game.json` file.

### Layout refinement

The former two-line scenario summary remains available internally for backwards
compatibility but is no longer placed in the visible layout. Scenario guidance
is now obtained through the active title, giving the Battle Roster more vertical
space.

### Boundary

This sprint changes only Tactical Assistant domain data, UI code, tests, and
documentation. It contains no canonical database or `platform_data` files.
