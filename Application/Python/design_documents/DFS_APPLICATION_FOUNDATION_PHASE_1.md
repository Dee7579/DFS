# DFS Application Foundation — Phase 1

This phase introduces the read-only application boundary that the Ship Viewer and future modules will use.

## Added packages

- `dfs.domain`: immutable catalog and platform-detail models
- `dfs.repositories`: repository protocols
- `dfs.infrastructure.sqlite`: SQLite connection and repository implementations
- `dfs.services`: catalog and detail application services
- `dfs.bootstrap`: application composition root

## Compatibility

The existing importer, validator, generators, `dfs.database.Database`, and platform files are unchanged. The new foundation runs beside the Version 1.0 engine until each proven workflow is deliberately migrated.

## Query behavior

- Platform search returns canonical platforms.
- Fleet, priority, trait, and weapon filters match profiles associated with each canonical platform.
- Multiple selected traits and weapons use AND semantics.
- Full platform detail loads all profiles, traits, and weapons in three database queries, avoiding the existing N+1 pattern.
- SQLite connections enable foreign-key enforcement and are read-only at the repository boundary.

## Test command

From the `Python` directory:

```powershell
$env:DFS_TEST_DB = "C:\path\to\Database\Data\dfs.db"
python -m unittest discover -s tests -v
```

## Next phase

Build the PySide6 desktop shell and Ship Viewer ViewModel against these services. The first GUI milestone will browse, search, filter, and display complete platform profiles without direct SQL in the UI.
