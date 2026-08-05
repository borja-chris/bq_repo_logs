# COROS Export Manifest - 2026-08-05

## Import

- Source files: `12` files
- Repo folder: `data/coros_exports/COROS_export_2026-08-05/`
- Imported on: 2026-08-05
- FIT files: 12
- FIT payload bytes: 1,352,325
- Removed sidecars: 0 `*:Zone.Identifier` files

## Integrity

- Hash file: `SHA256SUMS.txt`
- Hash entries: 12

## Processing

- Processed JSONL: `data/processed/coros_export_2026-08-05_summary.jsonl`
- JSONL rows: 12
- Summary row count matches FIT count: yes
- Parser used for this batch: `fitdecode, fitparse`

## Archive

- Archive status: not archived yet
- Reason: current-month loose FIT files stay available for repair, reparse, or enrichment
- Folder bytes with loose FIT files: 1,353,909

## Notes

- Raw FIT files are binary training records and may contain GPS, timestamps, heart rate, and device metadata.
- Processed summaries should be written to `data/processed/`.
