# DFS Changelog

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
