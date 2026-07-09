# COROS Export Manifest - 2026-07-08

## Import

- Source files: `2` files
- Repo folder: `data/coros_exports/COROS_export_2026-07-08/`
- Imported on: 2026-07-08
- FIT files: 2
- FIT payload bytes: 348,602
- Removed sidecars: 2 `*:Zone.Identifier` files

## Integrity

- Hash file: `SHA256SUMS.txt`
- Hash entries: 2

## Processing

- Processed JSONL: `data/processed/coros_export_2026-07-08_summary.jsonl`
- JSONL rows: 2
- Summary row count matches FIT count: yes
- Parser used for this batch: `fitdecode`

## Archive

- Archive status: not archived yet
- Reason: current-month loose FIT files stay available for repair, reparse, or enrichment
- Folder bytes with loose FIT files: 348,866

## Notes

- Raw FIT files are binary training records and may contain GPS, timestamps, heart rate, and device metadata.
- Processed summaries should be written to `data/processed/`.
