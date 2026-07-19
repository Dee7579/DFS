# DFS Fleet Builder Sprint 002B.4

## Fleet Interaction and Included Craft

This sprint improves Fleet Builder interaction without adding faction-specific
replacement legality yet.

### Delivered

- Theme-aware muted selection and comparison highlights.
- Shared comparison actions that can add either compared platform to the fleet.
- Automatic single-list Fleet / Era selection.
- Rich Fleet Roster hover summaries.
- Derived included-craft rows beneath parent platforms.
- Included craft do not spend Fleet Allocation Points and are removed with the
  parent because they are derived from the selected platform profile.

### Included craft model

Included craft are currently a derived presentation of the profile's official
Craft field. They are not ordinary purchased fleet entries. This prevents them
from consuming construction budget while establishing the visual and service
boundary required by Tactical Assistant.

### Deferred to Sprint 002C

- Fighter replacement controls and legality.
- Purchase groups and two-for-one selections.
- Faction-specific construction restrictions.
- Explicit persistence of replacement craft selections.
