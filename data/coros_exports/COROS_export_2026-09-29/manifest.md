# COROS Export Manifest - 2026-09-29

## Import

- Source files: `6` files
- Repo folder: `data/coros_exports/COROS_export_2026-09-29/`
- Imported on: 2026-09-29
- FIT files: 6
- FIT payload bytes: 731,851
- Removed sidecars: 0 `*:Zone.Identifier` files

## Integrity

- Hash file: `SHA256SUMS.txt`
- Hash entries: 6

## Processing

- Processed JSONL: `data/processed/coros_export_2026-09-29_summary.jsonl`
- JSONL rows: 6
- Summary row count matches FIT count: yes
- Parser used for this batch: `fitdecode`

## Archive

- Archive status: not archived yet
- Reason: current-month loose FIT files stay available for repair, reparse, or enrichment
- Folder bytes with loose FIT files: 732,643

## Notes

- Raw FIT files are binary training records and may contain GPS, timestamps, heart rate, and device metadata.
- Processed summaries should be written to `data/processed/`.
