# COROS Export Manifest - 2026-06-21

## Import

- Source files: `5` files
- Repo folder: `data/coros_exports/COROS_export_2026-06-21/`
- Imported on: 2026-06-21
- FIT files: 5
- FIT payload bytes: 877,550
- Removed sidecars: 5 `*:Zone.Identifier` files

## Integrity

- Hash file: `SHA256SUMS.txt`
- Hash entries: 5

## Processing

- Processed CSV: `data/processed/coros_export_2026-06-21_summary.csv`
- Processed JSONL: `data/processed/coros_export_2026-06-21_summary.jsonl`
- CSV activity rows: 5
- JSONL rows: 5
- Summary row count matches FIT count: yes
- Parser used for this batch: `fitdecode`

## Archive

- Archive status: not archived yet
- Reason: current-month loose FIT files stay available for repair, reparse, or enrichment
- Folder bytes with loose FIT files: 878,210

## Notes

- Raw FIT files are binary training records and may contain GPS, timestamps, heart rate, and device metadata.
- Processed summaries should be written to `data/processed/`.
