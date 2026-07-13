# DFS Architecture Decisions

## ADR-001 — Platform Explorer replaces Ship Viewer

**Decision:** Use Platform Explorer as the module name.

**Reason:** DFS includes ships, fighters, drones, breaching pods, stations, Ancients, and future game systems.

## ADR-002 — Services own business logic

**Decision:** The GUI remains a thin presentation layer.

**Reason:** Fleet Builder, Game Mode, Campaign Manager, and future systems must reuse identical rules.

## ADR-003 — Game-system identity is dynamic

**Decision:** DFS branding is permanent; game-system branding comes from the active system registry.

**Reason:** The desktop shell must support Babylon 5 ACTA, Victory at Sea, and future systems without hard-wired branding.

## ADR-004 — Presentation themes share one data model

**Decision:** DFS Standard, DFS Modern, DFS Compact, DFS Printer Friendly, and DFS Classic render the same domain data.

**Reason:** Presentation must vary without duplicating platform data or business logic.

## ADR-005 — One ApplicationContext per desktop session

**Decision:** Modules receive a shared `ApplicationContext`.

**Reason:** Centralized dependency construction improves testability, consistency, and future plugin support.

## ADR-006 — Settings migrate incrementally

**Decision:** `SettingsService` initially uses QSettings as its storage backend.

**Reason:** Existing user layout, favorites, recent platforms, and preferences remain intact while direct settings access is phased out safely.
