# DFS UI Guidelines

## Principles

- Preserve the user's current context whenever possible.
- Keep business rules outside widgets.
- Use progressive disclosure instead of presenting every field everywhere.
- Use one authoritative workspace for detailed platform information.
- Keep DFS application branding separate from active game-system identity.

## Theme Usage

- Accent color is semantic and supplied by `ThemeService`.
- Selection, links, primary actions, and active states use the current accent.
- Warning and destructive actions must not be represented only by accent color.
- Light, dark, and system modes must preserve readable contrast.

## Layout

- Primary page margins: 24–28 px.
- Related controls should be grouped in cards or group boxes.
- Splitters must remain freely resizable and remember user choices when enabled.
- Tables use alternating rows when that improves scanning.

## Interaction

- Hover may provide a concise summary.
- Click may pin or open a contextual popover.
- Full-page navigation should be reserved for deeper workflows.
- Status messages belong in the shared status service.
- Success notifications should be unobtrusive; warnings and errors may require dialogs.
