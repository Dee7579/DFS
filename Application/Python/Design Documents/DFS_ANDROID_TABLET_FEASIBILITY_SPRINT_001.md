# DFS Android Tablet Feasibility Sprint 001

## Goal

Prove that DFS can run as a focused, offline, landscape tablet companion without
porting the desktop document and printing system. The proof must exercise one
real path from certified catalog data through fleet construction into live
tactical state on an ARM64 Android device.

## Product boundary

The tablet companion includes four touch-first surfaces:

| Surface | Sprint 001 capability |
|---|---|
| Ships | Search certified platforms and inspect native stats, weapons, traits, and notes |
| Fleet | Select a faction/list, apply Priority Level budget and platform rules, add/remove entries, and save |
| Battle | Create units from the active fleet, track damage/crew/shields/status, inspect combat data, advance turns, and save |
| Rules | Search and read the existing B5 ACTA Codex |

PDFs, printing, master reference sheets, source rulebooks, platform importing,
certification utilities, developer tools, and desktop widgets are outside this
sprint. The first APK is landscape-first, ARM64, side-loaded, and intended for
hardware feasibility testing rather than store distribution.

## Architecture

The new `dfs.mobile` boundary composes the existing read-only platform
repository, Fleet Construction service, Tactical Game service, JSON stores, and
Codex. `MobileSession` exposes pure Python view models and owns app-private fleet
and game folders. `MobileController` is the only Qt/QML adapter. The QML interface
contains no game rules.

The canonical database is never opened for writes. At build time its bytes and
SHA-256 digest are converted to a generated Python payload in an ignored staging
tree. On first launch the payload is verified and materialized to Android's
private application storage; DFS then creates its existing isolated runtime copy
for generated composite profiles.

Desktop print exports remain source-compatible but are lazy-loaded so importing
the shared fleet rule engine does not import ReportLab, pypdf, or Qt Print
Support.

## Acceptance criteria

- The mobile composition root imports without desktop/PDF modules.
- Certified factions, platform profiles, weapons, traits, and Codex rules load.
- A legal platform can be added to a fleet and persisted in the existing JSON
  format.
- A tactical game can be created from that fleet, modified, advanced, and saved.
- The source database and certified platform-data hashes remain unchanged.
- Android staging contains no raw database, desktop UI, PDF modules, source
  platform data, or development/reference material.
- GitHub Actions produces an ARM64 APK and SHA-256 checksum using Qt's official
  Android deployment tool.

## Follow-up after device proof

Hardware testing will set the order for the next sprint. Expected work includes
larger-screen responsive polish, fleet load/select UI, vessel naming, fighter
substitutions, missile loadouts, allied contingents, Huge Hangars, critical-hit
controls, special actions, and tactical rule automation already present in the
desktop assistant.
