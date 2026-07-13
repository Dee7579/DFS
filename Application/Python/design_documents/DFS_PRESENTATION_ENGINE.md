# DFS Presentation Engine

**Status:** Architecture Foundation 1.0

## Objective

The DFS Presentation Engine separates platform truth from how that truth is displayed. The database and application services provide a normalized platform model. Renderers convert that model into interactive workspaces, PDFs, print previews, fleet packets, and future formats.

## Architectural flow

```text
SQLite / Platform Data
        ↓
Repositories
        ↓
Application Services
        ↓
Normalized Domain Models
        ↓
Presentation Engine
        ├── Platform Explorer
        ├── DFS Standard PDF
        ├── DFS Modern PDF
        ├── DFS Compact PDF
        ├── DFS Printer Friendly PDF
        ├── DFS Classic PDF
        ├── Fleet Reports
        └── Campaign Reports
```

## Rules

1. Renderers do not query SQLite.
2. Renderers do not import platform-data Python modules.
3. Renderers receive complete domain objects or dedicated presentation models.
4. Business rules remain in services.
5. Official display text is preserved even when services normalize it for behavior.
6. A theme is shown in the UI only after its renderer and document location are functional.

## Theme registry

Stable theme IDs:

- `dfs_standard`
- `dfs_modern`
- `dfs_compact`
- `dfs_printer_friendly`
- `dfs_classic`

The code registry lives in `dfs/presentation/themes.py`. At this phase only DFS Standard is implemented. Future themes are registered but intentionally hidden until functional.

## Renderer interface target

A future renderer should conceptually support:

```python
render_platform(platform, profile, theme, destination)
```

The exact interface will be introduced when DFS Modern is implemented. Existing generators remain operational until a renderer can reproduce their output without regression.

## Shared presentation models

Future work may introduce models such as:

- `PlatformPresentation`
- `ProfilePresentation`
- `WeaponPresentation`
- `CodexReference`
- `DocumentPackage`

These should be derived by services and remain independent of Qt and ReportLab.

## Screen renderer: Platform Explorer

Platform Explorer is the interactive reference renderer. Its Profile tab is the visual prototype for DFS Modern:

- stat cards
- grouped metadata
- strong title hierarchy
- readable traits and craft
- linked navigation

The screen layout is not forced into paper dimensions. The future PDF renderer adopts its design language while respecting pagination and print margins.

## PDF style selection

The document service resolves:

```text
profile + presentation theme + generated document
```

Platform Explorer must never construct output paths directly. Fleet Builder will reuse the same service for fleet packets and batch printing.

## Migration strategy

1. Preserve current DFS Standard generator unchanged.
2. Formalize theme registry and design system.
3. Implement DFS Modern as a separate renderer.
4. Compare generated output and validate all platform types.
5. Extract truly shared renderer components only after two working themes demonstrate reuse.

This avoids prematurely refactoring the proven PDF engine.
