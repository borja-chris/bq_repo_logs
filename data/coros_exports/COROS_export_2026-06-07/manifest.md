# COROS Export Manifest - 2026-06-07

## Import

- Source files: `10` files
- Repo folder: `data/coros_exports/COROS_export_2026-06-07/`
- Imported on: 2026-06-07
- FIT files: 10
- FIT payload bytes: 848,120
- Removed sidecars: 10 `*:Zone.Identifier` files

## Integrity

- Hash file: `SHA256SUMS.txt`
- Hash entries: 10

## Processing

- Processed CSV: `data/processed/coros_export_2026-06-07_summary.csv`
- Processed JSONL: `data/processed/coros_export_2026-06-07_summary.jsonl`
- CSV activity rows: 10
- JSONL rows: 10
- Summary row count matches FIT count: yes
- Parser used for this batch: `fitdecode, fitparse`

## Archive

- Archive status: not archived yet
- Reason: current-month loose FIT files stay available for repair, reparse, or enrichment
- Folder bytes with loose FIT files: 849,440

## Notes

- Raw FIT files are binary training records and may contain GPS, timestamps, heart rate, and device metadata.
- Processed summaries should be written to `data/processed/`.
