# DFS Fleet Builder Sprint 002B.5

## Purpose

Complete the core Fleet Builder roster workflow before beginning the ACTA-specific rule extensions.

## Roster ordering

Purchased entries can be reordered by dragging a roster row. Included craft are derived child rows and move with their parent platform. The context menu also exposes Move Up, Move Down, Move to Top, and Move to Bottom commands. Fleet JSON persistence already preserves entry tuple order, so custom order survives save and reload.

## Sorting

The Platform and Priority headers are clickable. Platform sorting uses the official displayed platform name. Priority sorting uses ACTA order: Patrol, Skirmish, Raid, Battle, War, and Armageddon. Clicking the same header reverses the direction. A manual move clears the active sort and restores Custom Order.

## Tactical Assistant terminology

All user-facing and documentation references to Game Mode are renamed Tactical Assistant. Existing internal identifiers may remain stable where changing them would create migration risk.

## Boundary

This sprint closes the Fleet Builder usability phase. Subsequent work should prioritize official ACTA construction rules, fighter replacements, purchase groups, allied allowances, and faction-specific restrictions.
