# DFS Fleet Builder Sprint 002B.6

## Selective Fleet Printing

Fleet printing is planned before ACTA-specific rule expansion so the document workflow has a stable service boundary.

### Ship sheets

Each selected purchased vessel remains a separate printable item. Named ships retain their vessel identity in the print-selection screen. Grouped unnamed entries default to one copy per vessel represented by the quantity.

### Fighter and reusable-craft sheets

Fighters, breaching pods, drones, crewed missiles, and similar reusable craft are deduplicated by stable profile ID across the complete fleet. Purchased fighter entries and included carrier craft contribute to the same fleet-wide quantity, while the print plan creates only one reference sheet for each unique profile.

### Print history

After a print job is submitted, the fleet metadata records the printed item keys and timestamp. `Select Unprinted` uses this history to avoid reprinting already laminated sheets. PDF generation alone does not mark a sheet as printed.

### Existing PDF source

This sprint prints existing generated DFS PDFs. It does not regenerate or overwrite master reference sheets. Fleet-specific named-sheet generation remains a separate document workflow.
