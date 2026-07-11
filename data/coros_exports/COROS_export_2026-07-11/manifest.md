# COROS Export Manifest - 2026-07-11

## Import

- Source files: `4` files
- Repo folder: `data/coros_exports/COROS_export_2026-07-11/`
- Imported on: 2026-07-11
- FIT files: 4
- FIT payload bytes: 197,066
- Removed sidecars: 0 `*:Zone.Identifier` files

## Integrity

- Hash file: `SHA256SUMS.txt`
- Hash entries: 4

## Processing

- Processed JSONL: `data/processed/coros_export_2026-07-11_summary.jsonl`
- JSONL rows: 4
- Summary row count matches FIT count: yes
- Parser used for this batch: `fitdecode, fitparse`

## Archive

- Archive status: not archived yet
- Reason: current-month loose FIT files stay available for repair, reparse, or enrichment
- Folder bytes with loose FIT files: 197,594

## Notes

- Raw FIT files are binary training records and may contain GPS, timestamps, heart rate, and device metadata.
- Processed summaries should be written to `data/processed/`.
