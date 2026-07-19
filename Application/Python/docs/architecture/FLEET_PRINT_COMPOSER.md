# DFS Fleet Print Composer

## Purpose

Fleet printing no longer sends each custom-size reference PDF to Windows as a separate job. DFS first composes selected fleet sheets into one standard US Letter PDF, then submits that packet through one print dialog.

## Imposition

- Ship sheets: two-up on Letter portrait pages.
- Ship backs: placed in the same top/bottom positions as their fronts for long-edge duplex printing.
- Fighter and reusable-craft sheets: four-up on Letter portrait pages, rotated into exact quarter-sheet cells.
- Every packet page is 612 × 792 points.
- Subtle cut guides are included.

## Vessel Names

Named ship sheets are rendered as fleet-specific PDFs before imposition. The vessel-name field is native to both the front and rules-reference back page. Unnamed sheets still include a blank labeled line for later handwritten use.

## Output

Generated packets are retained under the fleet's `print_packets` directory. Master PDFs in `output/` are never modified.

## Printing

The composed packet uses one paper size and one orientation, eliminating repeated printer dialogs and custom-paper-size prompts. Duplex printing should use long-edge binding so front and back halves remain aligned.
