# DFS Fleet Builder Sprint 002B.6.1

## Fleet-Specific Sheet Generation and Mixed-Size Printing

This corrective sprint replaces direct printing of stored master PDFs with a fleet-aware document workflow.

- Named vessel sheets are generated into a fleet-specific `sheets/` folder.
- Master PDFs under `output/` are never overwritten.
- Vessel names appear on the front and rules-reference back pages.
- Fighter and reusable-craft references continue to use the generic deduplicated sheet.
- Print jobs are grouped by actual PDF page dimensions so fighter sheets and variable-height ship sheets retain their designed size.
- One Windows print dialog appears for each distinct physical sheet size in the selected print set.

Current named generation supports DFS Standard. Future presentation renderers will implement the same fleet-sheet service contract.
