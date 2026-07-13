# DFS Coding Standards

## Architecture

- GUI is a thin presentation layer.
- Business logic belongs in services.
- Persistence belongs in repositories or framework services.
- Composition occurs in `dfs.bootstrap`.

## Naming

Use explicit responsibility-based names such as `PlatformCatalogService`, `ThemeService`, and `FleetRepository`. Avoid generic names such as `manager`, `helper2`, or `thing`.

## Dependencies

- UI may depend on domain models and services.
- Services may depend on repository interfaces.
- Infrastructure implements repository interfaces.
- Domain code must not depend on PySide6.

## Compatibility

Prefer incremental migration over broad rewrites. Preserve public compatibility aliases when replacing a stable interface.

## Testing

- Service behavior should have unit tests.
- SQLite behavior should have integration tests.
- GUI behavior should be tested where practical and always visually verified before release.
