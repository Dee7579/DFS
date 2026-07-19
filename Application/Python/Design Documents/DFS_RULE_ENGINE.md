# DFS ACTA Rule Engine

**Milestone:** 002C.1 — Rule Engine Foundation
**Version:** 2.4.0-alpha1

## Purpose

The rule engine is the sole source of truth for fleet-construction legality. The Fleet Builder, future Rules Browser, diagnostics, and Tactical Assistant consume the same rule objects. UI code must not implement ACTA rules.

## Rule layers

1. Core ACTA construction rules
2. Fleet-specific rules
3. Platform and fighter-replacement rules
4. Alliance and contingent rules
5. Scenario overrides (future)

## Rule result contract

Each result includes a stable rule ID, severity, human title, explanation, source, optional platform/entry, and optional remedy.

## Stable rule ID convention

- `CORE_*` — universal construction rules
- `EA_*`, `ISA_*`, `NARN_*`, etc. — fleet rules
- `<FACTION>_<PLATFORM>_*` — platform rules
- `<FACTION>_*_REPLACEMENT` — fighter replacement rules

## Source precedence

1. Fleet Lists
2. Powers & Principalities updates and replacements
3. Official FAQ/errata

The P&P Fleet Allocation Point chart on page 12 is authoritative for priority breakdowns.

## Current foundation

The existing core checks now run through first-class rules:

- Fleet list required
- Database profile resolution
- Fleet-list eligibility
- In-service year availability
- Supported priority levels
- P&P priority budget

The next sprint adds declarative fighter-replacement rules and fleet-specific libraries.
