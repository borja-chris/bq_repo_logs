# COROS Export Manifest - 2026-05-14

## Import

- Source files: `2` files
- Repo folder: `data/coros_exports/COROS_export_2026-05-14/`
- Imported on: 2026-05-14
- FIT files: 2
- FIT payload bytes: 245,063
- Removed sidecars: 0 `*:Zone.Identifier` files

## Integrity

- Hash file: `SHA256SUMS.txt`
- Hash entries: 2

## Processing

- Processed CSV: `data/processed/coros_export_2026-05-14_summary.csv`
- Processed JSONL: `data/processed/coros_export_2026-05-14_summary.jsonl`
- CSV activity rows: 2
- JSONL rows: 2
- Summary row count matches FIT count: yes
- Parser used for this batch: `fitdecode`

## Archive

- Archive status: not archived yet
- Reason: current-month loose FIT files stay available for repair, reparse, or enrichment
- Folder bytes with loose FIT files: 246,284

## Notes

- Raw FIT files are binary training records and may contain GPS, timestamps, heart rate, and device metadata.
- Processed summaries should be written to `data/processed/`.
