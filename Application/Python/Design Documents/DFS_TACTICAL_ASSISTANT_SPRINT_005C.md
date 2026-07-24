# DFS Tactical Assistant Sprint 005C

## Purpose

Refine Tactical Assistant rule help and weapon-trait reference behavior without
changing certified platform modules or the canonical database.

## Weapon trait tooltips

A weapon row now resolves the weapon rule and every recognized printed weapon
trait. The tooltip joins all resolved Codex entries rather than stopping after
the first match. `CodexService.first_for_weapon` remains compatible and now
uses the complete resolver internally.

## Disposition rules header

The Unit Status panel is renamed **Disposition** and uses the same active-header
treatment as Scenario and Critical Results. Hovering shows the Stricken Ship
Damage Table. Clicking opens the same table in a readable rules dialog.

## Silent active rules dialogs

Active headers no longer use `QMessageBox.information`, which produced the
operating-system alert sound. They now open a plain read-only `QDialog` with no
alert icon or notification sound.

## Test correction

The Sprint 005A scenario-header regression test now checks the complete scenario
rules text delivered by Sprint 005B and the new silent rules dialog rather than
the superseded abbreviated wording and message-box implementation.
