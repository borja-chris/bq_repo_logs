# COROS Export Manifest - 2026-06-26

## Import

- Source files: `4` files
- Repo folder: `data/coros_exports/COROS_export_2026-06-26/`
- Imported on: 2026-06-26
- FIT files: 4
- FIT payload bytes: 576,677
- Removed sidecars: 4 `*:Zone.Identifier` files

## Integrity

- Hash file: `SHA256SUMS.txt`
- Hash entries: 4

## Processing

- Processed CSV: `data/processed/coros_export_2026-06-26_summary.csv`
- Processed JSONL: `data/processed/coros_export_2026-06-26_summary.jsonl`
- CSV activity rows: 4
- JSONL rows: 4
- Summary row count matches FIT count: yes
- Parser used for this batch: `fitdecode`

## Archive

- Archive status: not archived yet
- Reason: current-month loose FIT files stay available for repair, reparse, or enrichment
- Folder bytes with loose FIT files: 577,205

## Notes

- Raw FIT files are binary training records and may contain GPS, timestamps, heart rate, and device metadata.
- Processed summaries should be written to `data/processed/`.
