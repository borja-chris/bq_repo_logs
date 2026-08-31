# COROS Export Manifest - 2026-08-30

## Import

- Source files: `3` files
- Repo folder: `data/coros_exports/COROS_export_2026-08-30/`
- Imported on: 2026-08-30
- FIT files: 3
- FIT payload bytes: 310,527
- Removed sidecars: 0 `*:Zone.Identifier` files

## Integrity

- Hash file: `SHA256SUMS.txt`
- Hash entries: 3

## Processing

- Processed JSONL: `data/processed/coros_export_2026-08-30_summary.jsonl`
- JSONL rows: 3
- Summary row count matches FIT count: yes
- Parser used for this batch: `fitdecode`

## Archive

- Archive status: not archived yet
- Reason: current-month loose FIT files stay available for repair, reparse, or enrichment
- Folder bytes with loose FIT files: 311,811

## Notes

- Raw FIT files are binary training records and may contain GPS, timestamps, heart rate, and device metadata.
- Processed summaries should be written to `data/processed/`.
