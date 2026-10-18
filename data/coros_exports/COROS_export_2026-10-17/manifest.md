# COROS Export Manifest - 2026-10-17

## Import

- Source files: `5` files
- Repo folder: `data/coros_exports/COROS_export_2026-10-17/`
- Imported on: 2026-10-17
- FIT files: 5
- FIT payload bytes: 319,932
- Removed sidecars: 0 `*:Zone.Identifier` files

## Integrity

- Hash file: `SHA256SUMS.txt`
- Hash entries: 5

## Processing

- Processed JSONL: `data/processed/coros_export_2026-10-17_summary.jsonl`
- JSONL rows: 5
- Summary row count matches FIT count: yes
- Parser used for this batch: `fitdecode, fitparse`

## Archive

- Archive status: not archived yet
- Reason: current-month loose FIT files stay available for repair, reparse, or enrichment
- Folder bytes with loose FIT files: 321,476

## Notes

- Raw FIT files are binary training records and may contain GPS, timestamps, heart rate, and device metadata.
- Processed summaries should be written to `data/processed/`.
