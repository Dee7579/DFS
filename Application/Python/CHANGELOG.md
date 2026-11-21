# DFS Changelog

## 2.4.0-alpha28

- Made each aggregate fighter-type roster row open a dedicated fighter
  reference; removed the duplicate per-flight dropdown rows while preserving
  every individual flight in tactical save state.
- Tailored fighter references to show aggregate Ready/Launched/Lost status,
  fighter statistics, Weapons, Traits, and source notes without ship-only
  tracks, Disposition, criticals, or operational-status controls.
- Made Weapons auto-size to their full row count so short weapon lists no longer
  waste space and long lists use the outer platform scrollbar rather than an
  inner weapon scrollbar.
- Added a dark divider between the two desktop Traits columns.
- Corrected Apply Critical so its multiplier affects only the critical table's
  extra Damage and Crew; the normal hit is recorded separately on the tracks.
- Made Damage Control and numeric Special Action equations update immediately
  as Crew Quality is typed, including the required die result.
- Added fighter-reference, Weapons sizing, trait divider, multiplier, live Crew
  Quality, desktop, and 150%-scaling regression coverage.

## 2.4.0-alpha27

- Moved Traits into a full-width panel above Disposition and Critical Results.
- Show all traits without an inner scrollbar, using two columns on normal
  desktop widths and one column on narrow workspaces.
- Replaced the high-DPI-sensitive fighter spin boxes with separate Ready,
  Launched, and Lost columns using horizontal minus/value/plus controls.
- Moved New from Fleet, Open Game, and Quick Reference onto the Tactical
  Assistant title row and removed the redundant descriptive subtitle.
- Added responsive header, auto-sizing Traits, and counter regression coverage;
  visually verified the layouts at 100% and 150% display scaling.

## 2.4.0-alpha26

- Restored the Tactical Assistant's scrollable platform-detail pane so combat
  controls retain their natural height instead of overlapping.
- Kept the Sprint 002 compact tracks, tabbed notes, and condensed fighter roster
  while limiting Weapons, Criticals, and detail tabs to practical heights.
- Stack Disposition and Critical Results vertically on narrow workspaces to
  prevent horizontal crowding; wider displays continue to show them side by side.
- Added regression coverage for overlapping controls, responsive stacking,
  vertical scrolling, and both ship and fighter selections.

## 2.4.0-alpha25

- Condensed the Tactical Assistant combat workspace and grouped carried fighters
  into compact per-type status controls.
- Added searchable Quick Reference, Turn Order, Attack Table, Disposition, and
  Damage Control rules help from one shared reference catalogue.
- Added tactical ship naming, next-turn critical-repair eligibility, complete
  critical damage multipliers, and explicit Running Adrift movement.
- Added a persistent collapsible navigation rail with small-window auto-collapse.
- Preserved existing tactical save compatibility and the certified platform-data
  and canonical-database boundaries.

## 2.4.0-alpha23

- Refined grouped purchases to display one roster row per physical vessel.
- One grouped purchase now creates two independently nameable quantity-one rows.
- Linked rows consume a single priority choice and are removed together.
- Added grouped-purchase wording to the existing hover-card Notes section.
- Preserved support for legacy quantity-two grouped entries.
