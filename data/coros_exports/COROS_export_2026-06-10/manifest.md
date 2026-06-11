# COROS Export Manifest - 2026-06-10

## Import

- Source file: `478120817039802368.fit`
- Repo folder: `data/coros_exports/COROS_export_2026-06-10/`
- Imported on: 2026-06-10
- FIT files: 1
- FIT payload bytes: 154,692
- Removed sidecars: 1 `*:Zone.Identifier` file

## Integrity

- Hash file: `SHA256SUMS.txt`
- Hash entries: 1

## Processing

- Processed CSV: `data/processed/coros_export_2026-06-10_summary.csv`
- Processed JSONL: `data/processed/coros_export_2026-06-10_summary.jsonl`
- CSV activity rows: 1
- JSONL rows: 1
- Summary row count matches FIT count: yes
- Parser used for this batch: `fitdecode`

## Archive

- Archive status: not archived yet
- Reason: current-month loose FIT files stay available for repair, reparse, or enrichment
- Folder bytes with loose FIT files: 154,824

## Notes

- Raw FIT files are binary training records and may contain GPS, timestamps, heart rate, and device metadata.
- Processed summaries should be written to `data/processed/`.
