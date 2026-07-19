# DFS Fleet Print Composer — Dimension-Aware Pagination

## Rule

DFS never reduces a platform reference sheet merely to force two sheets onto one Letter page.

## Ship pagination

- Generated ship PDFs retain their intended width and height when they fit on Letter paper.
- Adjacent roster entries share a page only when their fitted native heights total no more than 11 inches.
- Tall or dynamically expanded sheets print alone.
- Front and back pages use identical positions for long-edge duplex printing.
- Roster order is preserved.

## Fighter and reusable craft pagination

- Unique fighter/craft references remain deduplicated by stable profile ID.
- References are rotated into four quarter-page cells at no more than 100% scale.
- Back columns are mirrored for portrait Letter, flip-on-long-edge duplex alignment.

## Fleet roster

The optional roster prints first and includes fleet identity, construction profile, budget, remaining choices, vessel names, priorities, quantities, included craft, and validation results.
