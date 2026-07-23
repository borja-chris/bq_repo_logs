# COROS Export Manifest - 2026-07-23

## Import

- Source files: `3` files
- Repo folder: `data/coros_exports/COROS_export_2026-07-23/`
- Imported on: 2026-07-23
- FIT files: 3
- FIT payload bytes: 472,341
- Removed sidecars: 3 `*:Zone.Identifier` files

## Integrity

- Hash file: `SHA256SUMS.txt`
- Hash entries: 3

## Processing

- Processed JSONL: `data/processed/coros_export_2026-07-23_summary.jsonl`
- JSONL rows: 3
- Summary row count matches FIT count: yes
- Parser used for this batch: `fitdecode`

## Archive

- Archive status: not archived yet
- Reason: current-month loose FIT files stay available for repair, reparse, or enrichment
- Folder bytes with loose FIT files: 472,737

## Notes

- Raw FIT files are binary training records and may contain GPS, timestamps, heart rate, and device metadata.
- Processed summaries should be written to `data/processed/`.
