# DFS Tactical Assistant Sprint 005D

## Purpose

Refine scenario presentation and stricken-ship handling without changing certified
platform data or the canonical database.

## Scenario map workflow

The scenario selector is shortened and a `Map` button occupies the remaining row
space. The button opens a silent, scrollable deployment-map dialog for the selected
scenario. The map catalogue is declarative in `dfs.domain.tactical.scenarios` and
references runtime PNG assets under `resources/scenario_maps`.

Only printed deployment diagrams are included. Scenarios without a separate printed
map leave the button disabled rather than inventing a layout.

## Negative Damage

Damage may continue below zero. The current negative value is retained because each
point below zero modifies the Stricken Ship Damage Table roll. Crew and Shields remain
bounded at zero.

Damage at or below zero means the unit is Stricken and awaiting a Disposition result.
It does not automatically set the unit to Destroyed.

## Reversible Disposition

Destroyed is an explicit Disposition result. Selecting Operational after an accidental
Destroyed choice clears the Destroyed state without altering the entered Damage value.
This correction is available even when Damage remains zero or negative.

## Persistence

Schema version 1 remains compatible. The JSON reader now permits negative values only
for the Damage track. Existing game files remain valid.

## Protected-source boundary

This sprint contains no `platform_data` modules and no `dfs.db`. Scenario images are
read-only runtime resources derived from the supplied rule PDFs.
