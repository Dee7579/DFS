# DFS Application Phase 3C

## Platform Explorer Identity and Navigator

This phase completes the transition from **Ship Viewer** to **Platform Explorer** in the active desktop UI.

### Added

- Compact two-line platform navigator replacing the five-column results table.
- Freely resizable navigator/workspace splitter with improved default proportions.
- Full platform metadata available through result tooltips.
- Platform Explorer naming in navigation, dashboard, title, and active modules.
- Tactical Reference System application subtitle.
- Help > About Dee's Fighting Ships dialog.
- Runtime database statistics in Dashboard and About dialog.
- Lightweight startup splash screen.
- `Ctrl+1` shortcut to open Platform Explorer.

### Compatibility

The previous `dfs/ui/ship_viewer` package is left untouched so this update can be safely merged into an existing project. The active application now imports `dfs/ui/platform_explorer`.

### Version

`2.0.0-alpha2`
