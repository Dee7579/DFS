# DFS Software Architecture v2.0 — Working Draft

**Project:** Dee's Fighting Ships (DFS)  
**Status:** Architecture review in progress  
**Scope:** Desktop application foundation, beginning with Ship Viewer

## 1. Current System Snapshot

The current DFS codebase is a working Babylon 5 ACTA toolchain built around:

- Python platform-data modules
- SQLite database
- Platform importer
- Database validation workflow
- Ship, fighter, and Ancient PDF generators
- ACTA Codex and inventory/validation tooling
- Generated output organized by faction and era

The database currently contains:

- 23 factions
- 25 fleet lists
- 274 canonical ship/platform records
- 295 fleet-specific profiles
- 1,047 trait rows
- 1,108 weapon rows

SQLite reports `integrity_check = ok`. No orphaned ship, profile, trait, or weapon records were found.

## 2. Current Database Model

```text
factions
   │
   ├──< fleet_lists
   │       │
   │       ├──< acta_profiles >── ships
   │       │          │
   │       │          ├──< traits
   │       │          └──< weapons
   │       │
   │       └──< profile_fleet_lists >── acta_profiles
   │
   └──< ships
```

### Important observations

1. `ships` represents canonical platform identity.
2. `acta_profiles` represents a platform in a specific fleet list or era.
3. `traits` and `weapons` are correctly attached to profiles rather than canonical ships.
4. `profile_fleet_lists` currently duplicates the direct `fleet_list_id` relationship already stored on `acta_profiles`.
5. The schema declares foreign keys, but the current Python connection does not enable SQLite foreign-key enforcement.
6. Only one explicit application index exists: the unique profile/fleet bridge index.
7. The current data has no duplicate canonical ship/faction pairs and no duplicate ship/fleet profiles.

## 3. Architectural Direction

The desktop GUI must remain a thin presentation layer.

```text
PySide6 GUI
    │
    ▼
Application Services
    │
    ▼
Repository Interfaces
    │
    ▼
SQLite / Filesystem / Existing Generators / Codex
```

The GUI must not:

- contain SQL
- import platform-data modules directly
- derive PDF paths
- parse Codex structures
- interpret ACTA fleet rules
- implement fleet eligibility

## 4. Recommended Package Layout

```text
Python/
├── dfs_app.py
├── dfs/
│   ├── domain/
│   │   ├── models/
│   │   ├── queries/
│   │   └── repositories/
│   ├── services/
│   ├── infrastructure/
│   │   ├── sqlite/
│   │   ├── documents/
│   │   └── codex/
│   ├── pdf/                 # existing generators retained
│   └── ui/
│       ├── main_window.py
│       ├── ship_viewer/
│       └── shared/
├── platform_data/           # authoritative import source retained
├── codex_inventory/
├── output/
└── tests/
```

This should be introduced incrementally. Existing working generators and importers should not be moved until service-level compatibility tests exist.

## 5. First Application Services

### PlatformCatalogService

Provides:

- faction choices
- fleet/era choices
- priority choices
- trait choices
- weapon choices
- name search
- combined filtering
- sorting and result paging

### PlatformDetailService

Provides:

- canonical platform identity
- all available fleet profiles
- selected profile statistics
- traits
- weapons
- notes
- linked craft references

### DocumentService

Provides:

- generated PDF lookup by profile
- front/back or combined document references
- external opening
- future regeneration and printing

The GUI must request a document by profile identity rather than construct a filename.

### CodexService

Wraps the existing Codex rather than replacing it. It will expose:

- entries related to a platform profile
- entries related to traits and weapon rules
- free-text Codex search

### PlatformLinkService

Initially resolves carried craft such as fighters. Later it can support variants, replacements, auxiliary craft, Huge Hangars, and fleet-builder relationships.

## 6. Immediate Technical Findings

### Database class

`dfs/database.py` currently combines:

- connection creation
- SQL query execution
- domain-object construction
- note parsing
- multi-query loading

It is a useful working foundation but should become a SQLite repository implementation behind a stable interface.

### N+1 loading

`get_all_ships()` loads a list of profiles and then separately loads each profile, its traits, and its weapons. For 295 profiles, this creates hundreds of SQLite connections and queries.

The Ship Viewer should use dedicated catalog queries for summaries and one detail query for the selected record.

### Domain typing

The current `Ship` and `Weapon` dataclasses type several fields as integers even though valid ACTA data includes textual values such as `-`, dice notation, and other non-integer forms. Domain types should reflect stored reality rather than only standard warships.

### Foreign-key enforcement

Every SQLite connection should execute:

```sql
PRAGMA foreign_keys = ON;
```

This is low-risk for read-only application code. Importer behavior must be tested before enabling it there because deletion order currently compensates manually for the absence of cascade rules.

### Indexing

Before GUI search is finalized, likely indexes include:

```sql
CREATE INDEX idx_ships_name ON ships(ship_name);
CREATE INDEX idx_ships_faction ON ships(faction_id);
CREATE INDEX idx_profiles_ship ON acta_profiles(ship_id);
CREATE INDEX idx_profiles_fleet ON acta_profiles(fleet_list_id);
CREATE INDEX idx_profiles_priority ON acta_profiles(priority_level);
CREATE INDEX idx_traits_profile ON traits(profile_id);
CREATE INDEX idx_traits_value ON traits(trait);
CREATE INDEX idx_weapons_profile ON weapons(profile_id);
CREATE INDEX idx_weapons_name ON weapons(name);
```

These will be tested against representative viewer queries before any migration is proposed.

## 7. Ship Viewer First Vertical Slice

The first executable milestone will:

1. Open the real DFS database read-only.
2. Display profile results with platform name, faction, fleet/era, priority, and type.
3. Filter by faction, fleet/era, priority, trait, weapon, and name.
4. Select a profile and display statistics, traits, weapons, and notes.
5. Preserve the canonical-platform/profile distinction.
6. Use services and repository interfaces rather than direct GUI SQL.

PDF, Codex, and linked-craft tabs follow after the catalog/detail path is proven.

## 8. Proposed Development Order

### Phase A — Foundation

- introduce application path/configuration service
- introduce SQLite connection factory
- define domain DTOs and repository protocols
- implement read-only platform repository
- add unit and integration tests

### Phase B — Catalog and detail services

- catalog filters
- stable platform summary query
- stable profile detail query
- error handling and result models

### Phase C — PySide6 application shell

- main window
- module navigation
- Ship Viewer page
- filter panel
- result model
- detail tabs

### Phase D — Existing-system integration

- PDF lookup and preview
- Codex service
- linked fighters
- external PDF opening

### Phase E — Hardening

- saved settings
- window layout persistence
- query performance checks
- packaging for Windows
- regression tests for existing generator/import workflows

## 9. Decisions Not Yet Finalized

The following require further code and data review before implementation:

- whether `profile_fleet_lists` remains as a future many-to-many bridge or is redundant
- exact platform classification strategy for ships, fighters, breaching pods, and Ancients
- whether PDF paths should be stored in the database or resolved through a document manifest
- how Codex metadata currently links to traits, weapons, factions, and platform notes
- migration/versioning strategy for future database changes

## 10. Current Recommendation

Do not modify the working importer or generators yet.

First, build a read-only repository and service layer alongside the current system. Once integration tests prove identical data loading, the existing `Database` class can be gradually reduced or retained as a compatibility adapter.
