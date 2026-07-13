# DFS Design System

**Status:** Foundation 1.0  
**Applies to:** DFS Desktop, Platform Explorer, printable renderers, fleet and campaign reports

## Purpose

The DFS Design System gives every interactive screen and printable output a shared visual identity. It is deliberately restrained: readable, professional, and suitable for long tabletop sessions.

## Core principles

1. **One data model, many presentations.** Presentation changes never alter platform data.
2. **Progressive disclosure.** Show the most useful information first; reveal deeper rules and metadata through tabs and navigation.
3. **Navigation over dialog chains.** Users should move Platform → Craft → Weapon → Codex and back without losing context.
4. **Readable at a glance.** Important game values use strong hierarchy and generous spacing.
5. **Screen and print are related, not identical.** They share typography, cards, spacing, and naming while adapting to their medium.

## Product identity

- Product name: **Dee's Fighting Ships**
- Subtitle: **Tactical Reference System**
- Primary browser module: **Platform Explorer**
- Printable presentation family: **DFS Standard, DFS Modern, DFS Compact, DFS Printer Friendly, DFS Classic**

## Typography

- Desktop default: Segoe UI or the operating-system UI sans serif.
- Body text: 10 pt desktop baseline.
- Page title: 22–30 pt depending on context.
- Platform title: 18 pt, semibold.
- Stat value: 14 pt, bold.
- Stat caption and secondary metadata: 8–9 pt.
- Avoid compressed text as a substitute for layout decisions.

## Spacing scale

Use a small shared spacing scale:

- 2 px: caption/value relationship
- 4 px: tightly related controls
- 8 px: card padding and small section gaps
- 12 px: normal control grouping
- 16 px: major section separation
- 24 px: page-level separation

## Shared components

### Stat Card

A compact card containing an uppercase caption and a prominent value. Used by Platform Explorer and the future DFS Modern renderer.

### Navigator Item

Two-line platform selection item:

- line 1: official platform name
- line 2: faction and profile count or platform type

The navigator identifies what to open; it does not duplicate the workspace record.

### Profile Details Panel

Contains Fleet/Era, Craft, In Service, Source, and Traits. Text must wrap and remain selectable.

### Workspace Splitter

Recommended initial proportions:

- Filters: 18%
- Platform Navigator: 22%
- Platform Workspace: 60%

Splitters must be easy to grab, freely resizable within sensible minimums, persistent, and resettable.

### Buttons and controls

- Minimum desktop height: 28 px.
- Use verbs for actions: Print Sheet, Open Externally, Reset Layout.
- Avoid decorative buttons without a clear action.

## Color direction

Current light theme:

- Sidebar: deep slate
- Primary text: near-black slate
- Secondary text: medium slate
- Card backgrounds: very light slate
- Borders: light neutral gray
- Selection: operating-system highlight color

A future dark theme should map semantic roles rather than duplicate hard-coded colors.

## Presentation themes

### DFS Standard

Existing tabletop sheet. Dense, structured, optimized for print, lamination, and dry-erase use.

### DFS Modern

Card-based contemporary design derived from Platform Explorer. Intended for screen reading and modern printable sheets.

### DFS Compact

High-density layout for large fleets and reduced page counts.

### DFS Printer Friendly

Minimal shading and low-ink output, suitable for monochrome printers.

### DFS Classic

A DFS interpretation of traditional ACTA roster presentation.

## Accessibility and usability

- Do not communicate state by color alone.
- Preserve keyboard navigation.
- Provide hover tooltips where names are elided.
- Keep splitter handles visible and practical on high-resolution displays.
- Ensure all critical text can be selected or copied where appropriate.
