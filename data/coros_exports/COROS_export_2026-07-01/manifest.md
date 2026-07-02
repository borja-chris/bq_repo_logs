# COROS Export Manifest - 2026-07-01

## Import

- Source files: `6` files
- Repo folder: `data/coros_exports/COROS_export_2026-07-01/`
- Imported on: 2026-07-01
- FIT files: 6
- FIT payload bytes: 628,363
- Removed sidecars: 6 `*:Zone.Identifier` files

## Integrity

- Hash file: `SHA256SUMS.txt`
- Hash entries: 6

## Processing

- Processed CSV: `data/processed/coros_export_2026-07-01_summary.csv`
- Processed JSONL: `data/processed/coros_export_2026-07-01_summary.jsonl`
- CSV activity rows: 6
- JSONL rows: 6
- Summary row count matches FIT count: yes
- Parser used for this batch: `fitdecode`

## Archive

- Archive status: not archived yet
- Reason: current-month loose FIT files stay available for repair, reparse, or enrichment
- Folder bytes with loose FIT files: 629,155

## Notes

- Raw FIT files are binary training records and may contain GPS, timestamps, heart rate, and device metadata.
- Processed summaries should be written to `data/processed/`.
