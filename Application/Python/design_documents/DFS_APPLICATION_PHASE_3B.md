# DFS Application Phase 3B

## Scope

Phase 3B completes the first document-aware Ship Viewer increment and corrects
all in-service formats present in the current Babylon 5 ACTA database.

## Changes

- Recognizes `Until 2261`, `From 2259`, and `2261 only` in addition to existing forms.
- Preserves official in-service wording in SQLite and normalizes behavior in one service.
- Adds an In Service results column.
- Adds a PDF tab with a sheet-style registry.
- Includes embedded PDF preview when Qt PDF support is available.
- Adds Fit Width, Fit Page, Open Externally, Refresh, and Print Sheet actions.
- Remembers the selected sheet style.
- Keeps the initial style registry to DFS Standard; future styles are added as new roots.

## Architectural boundary

The GUI requests a generated sheet from `DocumentService` using platform,
profile, and style information. It does not build output paths or filenames.
