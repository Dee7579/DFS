# DFS Application Phase 3E — Game System Framework and Dashboard

**Application version:** 2.1.0-alpha1

## Purpose

Phase 3E separates the DFS desktop shell from any single rules system and turns the Dashboard into a useful launch workspace.

## Included

- Application-level game-system registry.
- Babylon 5: A Call to Arms registered as the active system.
- Victory at Sea registered as a disabled future system.
- Persistent game-system selector in the left navigation.
- Dashboard cards for Continue Working, Recent Platforms, Database Status, and installed presentation themes.
- Recent-platform tracking in Platform Explorer.
- Dashboard links that reopen a recent platform.
- Three-second minimum branded splash screen with staged startup messages.
- Updated About dialog and application version.

## Architecture

The registry is deliberately small. A future system provider will supply its own repositories, services, Codex, fleet rules, and presentation resources. The desktop shell consumes the currently selected provider rather than containing game-specific rules.

Babylon 5 remains the only enabled provider in this phase. The selector exists now so future systems can be added without redesigning the application shell.
