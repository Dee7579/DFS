# B5 ACTA Fleet Construction Rule Catalog

This inventory separates **cataloguing** from **activation**. Existing ISA and Raiders allied-contingent rules remain implemented; other records are source-audited targets for later activation sprints.

| Rule ID | Fleet | Rule | Family | Source | Status |
|---|---|---|---|---|---|
| `B5-LEAGUE-ALL-001` | Allied League of Non-Aligned Worlds | Permitted component fleet lists | `allowed_fleet_lists` | A Call to Arms: Second Edition Fleet Lists, Combined Fleets of the Non-Aligned Worlds, p. 6 | catalogued |
| `B5-LEAGUE-FTR-002` | Allied League of Non-Aligned Worlds | No cross-fleet carrier loading | `carrier_craft_affinity` | A Call to Arms: Second Edition Fleet Lists, Combined Fleets of the Non-Aligned Worlds, p. 6 | catalogued |
| `B5-LEAGUE-FTR-003` | Allied League of Non-Aligned Worlds | Ship prerequisite for purchased fighters | `required_platform` | A Call to Arms: Second Edition Fleet Lists, Combined Fleets of the Non-Aligned Worlds, p. 6 | catalogued |
| `B5-LEAGUE-DATE-004` | Allied League of Non-Aligned Worlds | Combined League date limit | `fleet_year_limit` | Powers & Principalities, Combined League Fleets and Army of Light, p. 11 | catalogued |
| `B5-AOL-LIST-001` | Army of Light | Permitted fleet lists | `allowed_fleet_lists` | Powers & Principalities, Army of Light, p. 11 | catalogued |
| `B5-AOL-PLAT-002` | Army of Light | Permitted platforms | `allowed_platforms` | Powers & Principalities, Army of Light, p. 11 | catalogued |
| `B5-AOL-MIX-003` | Army of Light | Minimum two component fleets | `minimum_distinct_fleets` | Powers & Principalities, Army of Light, p. 11 | catalogued |
| `B5-ISA-ALL-001` | Interstellar Alliance | Allied contingent | `allied_contingent` | A Call to Arms: Second Edition Fleet Lists, ISA Fleet Special Rules - Allied Fleets, p. 82 | implemented |
| `B5-ISA-DATE-002` | Interstellar Alliance | Fleet unavailable before 2262 | `fleet_year_minimum` | A Call to Arms: Second Edition Fleet Lists, ISA Fleet Special Rules - In Service Dates, p. 82 | catalogued |
| `B5-RAID-ALL-001` | Raiders | Allied contingent | `allied_contingent` | A Call to Arms: Second Edition Fleet Lists, Raiders Fleet Special Rules - Allied Fleets, p. 127 | implemented |
| `B5-PSI-ALL-001` | Psi Corps | EarthForce requisition | `allied_contingent` | A Call to Arms: Second Edition Fleet Lists, Psi Corps Fleet Special Rules - EarthForce Requisition, p. 149 | catalogued |
| `B5-GAIM-QUEEN-001` | Gaim Intelligence | At least one Queen | `minimum_fleet_requirement` | Powers & Principalities, Revised Gaim Intelligence Fleet Special Rules - The Queens, p. 19 | catalogued |
| `B5-GAIM-QUEEN-002` | Gaim Intelligence | One highest-priority Ruling Queen | `maximum_quantity_dynamic` | Powers & Principalities, Revised Gaim Intelligence Fleet Special Rules - The Queens, p. 19 | catalogued |
| `B5-ANCIENT-UNQ-001` | The Ancients | Each Ancient is unique | `unique_platform` | A Call to Arms: Second Edition Fleet Lists, Using the Ancients, p. 139 | implemented |
| `B5-ANCIENT-DATE-002` | The Ancients | Ancients depart in 2261 | `fleet_year_maximum` | A Call to Arms: Second Edition Fleet Lists, Using the Ancients, p. 139 | review |
| `B5-DRAKH-HGR-001` | The Drakh | Huge Hangar carried-ship capacity | `hangar_capacity` | A Call to Arms: Second Edition Fleet Lists, Drakh Fleet Special Rules - Huge Hangars, p. 143 | catalogued |

## Status meanings

- **implemented** - already enforced by the current rules engine.
- **catalogued** - source confirmed; platform selectors and activation still pending.
- **review** - source confirmed but needs a product decision or finer scenario metadata before enforcement.
