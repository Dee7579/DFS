# DFS Tactical Assistant Sprint 005A

## Fighter Wing Expansion and Active Rules Headers

### Purpose

Correct the final roster interpretation issue discovered during Sprint 005 review
and make rules-bearing interface headers visibly interactive before beginning the
shared two-fleet/networking work planned for Sprint 006.

### Purchased fighter wings

A Fleet Builder fighter entry represents one purchased **wing**, not one flight.
The canonical craft profile note identifies its size, for example:

- `Wing of Two Flights`
- `Wing of Four Flights`
- `Wing of Six Flights`

Tactical Assistant now expands every purchased wing into that number of
independently tracked flights. A quantity of three Aurora Starfury purchases,
whose profile says `Wing of Four Flights`, therefore creates twelve tactical
flight records.

Carried craft are unchanged: their printed carrier quantity already represents
individual flights and continues to expand through the included-craft workflow.

### Existing saved games

Games created through Sprint 005 may contain one representative tactical row per
purchased wing. Reopening those files upgrades them once:

- the existing row becomes the first flight and retains its current state;
- the remaining flights are added Ready and Operational;
- a metadata marker prevents a second expansion on later loads.

The upgrade changes only the independent `.dfs-game.json` state. It does not
modify the source fleet, platform modules, or canonical database.

### Active rules headers

Scenario and Critical Results now share the same interaction language:

- an information symbol appears in each title;
- the title is outlined and uses the current theme highlight color;
- hovering displays the applicable rules;
- clicking the title opens the rules in a message box.

Scenario help updates immediately whenever the selected scenario changes and
includes its source, fleet setup, special rules, game length, and victory
conditions.

### Boundary

This refinement contains no network synchronization. Sprint 006 remains the
planned two-fleet shared-game and local-network synchronization milestone.
