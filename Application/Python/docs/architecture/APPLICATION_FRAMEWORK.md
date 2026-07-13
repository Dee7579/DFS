# DFS Application Framework 1.0

## Purpose

The DFS Application Framework supplies shared desktop services to every module. UI modules receive one `ApplicationContext` and do not construct infrastructure directly.

## ApplicationContext

`dfs.bootstrap.ApplicationContext` exposes:

- platform catalog and detail services
- document and Codex services
- game-system registry
- settings service
- theme service
- status service
- notification service
- logging service
- command registry
- resource resolver

Existing code that imports `ApplicationServices` remains compatible while modules migrate gradually.

## Rules

1. New UI modules receive `ApplicationContext` through their constructor.
2. New code must not create `QSettings` directly.
3. Widgets must use the theme service rather than owning permanent accent colors.
4. Modules publish status and notifications through services rather than directly controlling the main window.
5. Commands intended for menus, shortcuts, toolbars, or the future command palette belong in `CommandService`.

## Migration Strategy

The framework is introduced alongside working code. Existing Platform Explorer settings remain valid because `SettingsService` uses Qt's existing settings store as its compatibility backend. Direct `QSettings` use in older modules will be removed incrementally rather than through a risky all-at-once rewrite.
