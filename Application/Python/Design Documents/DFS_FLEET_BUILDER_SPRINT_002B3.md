# DFS Fleet Builder Sprint 002B.3

## Fleet Identity and Shared Comparison

This sprint introduces persistent individual vessel identity without changing canonical platform data.

### Default Fleet Folder

Fleet files open and save from `Python/fleets/` by default. The most recently used fleet folder is stored through `SettingsService` and reused by later dialogs.

### Vessel Names

`FleetEntry` now contains an optional `vessel_name`. Naming an entry with quantity greater than one splits one vessel into its own entry and leaves the remaining unnamed quantity grouped. This gives Tactical Assistant, campaigns, and future named-sheet generation a stable identity for each named vessel.

### Persistence

The version-1 fleet JSON format gains an optional `vessel_name` property. Older fleet files remain compatible because a missing property loads as an empty name.

### Shared Comparison

Fleet Builder and Platform Explorer both use `PlatformCompareDialog`. Difference highlighting is theme-aware and intentionally subdued.

### Named PDFs

This sprint stores the vessel name required by the generator. Fleet-specific named-sheet generation is the next document workflow and will not overwrite the master reference PDFs.
