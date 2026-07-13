# DFS Application Phase 3D

## Platform Explorer and Presentation Foundation

This phase corrects three usability issues found during live testing and formalizes the presentation architecture.

### Corrected

- Splash screen now remains visible for at least 1.5 seconds.
- Weapons display in canonical DFS arc order: B, F, P, S, A, B(a), T.
- Source/import order is preserved inside each firing arc.
- Platform Explorer panes resize more freely.
- PDF controls use two rows so they no longer impose an excessive workspace minimum width.
- Splitter handles are wider and gain a stronger hover state.
- Earlier restrictive splitter settings are automatically replaced once.

### Added

- View → Reset Platform Explorer Layout.
- Ctrl+Shift+0 layout reset shortcut.
- Recommended 18% / 22% / 60% pane defaults.
- DFS presentation-theme registry.
- DFS Design System document.
- DFS Presentation Engine document.

### Not included yet

- DFS Modern PDF renderer.
- Clickable Codex entries.
- Linked craft navigation.
- Dark mode.

The existing database, importer, validator, and DFS Standard PDF generator are unchanged.
