# ADR-005: Rule Engine as the Single Source of Truth

## Status
Accepted

## Decision
All fleet-construction logic is implemented as source-backed rule objects evaluated by `FleetRuleEngine`. User-interface modules may display, filter, and explain results but may not independently decide legality.

## Consequences

- Rules Browser and validator cannot drift apart.
- Rule errors can be reported with stable IDs and sources.
- New game systems can register different rule libraries.
- Additional up-front structure is required, but faction expansion becomes safer and easier to audit.
