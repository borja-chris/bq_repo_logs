# COROS Export Manifest - 2026-08-22

## Import

- Source file: `479746788052468214.fit`
- Repo folder: `data/coros_exports/COROS_export_2026-08-22/`
- Imported on: 2026-08-22
- FIT files: 1
- FIT payload bytes: 102,201
- Removed sidecars: 0 `*:Zone.Identifier` files

## Integrity

- Hash file: `SHA256SUMS.txt`
- Hash entries: 1

## Processing

- Processed JSONL: `data/processed/coros_export_2026-08-22_summary.jsonl`
- JSONL rows: 1
- Summary row count matches FIT count: yes
- Parser used for this batch: `fitdecode`

## Archive

- Archive status: not archived yet
- Reason: current-month loose FIT files stay available for repair, reparse, or enrichment
- Folder bytes with loose FIT files: 102,333

## Notes

- Raw FIT files are binary training records and may contain GPS, timestamps, heart rate, and device metadata.
- Processed summaries should be written to `data/processed/`.
