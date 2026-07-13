# DFS Platform Explorer Final Polish

**Version:** 2.1.0-alpha3  
**Milestone:** Platform Explorer Final Polish

## Comparison workflow

The comparison view now uses a row-oriented table rather than two independent text columns. The first column identifies the attribute and the next two columns display the selected platforms. Alternating row shading improves scanning, while cells with different values receive a subtle highlight.

Comparison content is separated into:

1. Core attributes
2. Platform traits
3. Weapons

This keeps long weapon lists from obscuring the immediately useful ship statistics.

## In-context Codex rules

Platform traits and weapon rules now follow the DFS principle of preserving user context.

- Clicking a trait opens a small rule popover near the Platform Explorer workspace.
- Single-clicking a weapon row opens the relevant weapon or weapon-trait rule.
- Hovering a weapon row provides a concise summary.
- Double-clicking a weapon opens the full Codex tab.
- Each popover includes an **Open in Codex** action for deeper browsing.
- Missing entries display a clear message rather than silently doing nothing.

## PDF behavior

The PDF tab remains read-only during normal browsing. It locates and displays an existing generated PDF from the configured output directories. Regeneration will remain an explicit future action rather than occurring automatically when a platform is viewed.
