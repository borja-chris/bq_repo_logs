# COROS Export Manifest - 2026-11-14

## Import

- Source files: `9` files
- Repo folder: `data/coros_exports/COROS_export_2026-11-14/`
- Imported on: 2026-11-14
- FIT files: 9
- FIT payload bytes: 953,720
- Removed sidecars: 0 `*:Zone.Identifier` files

## Integrity

- Hash file: `SHA256SUMS.txt`
- Hash entries: 9

## Processing

- Processed JSONL: `data/processed/coros_export_2026-11-14_summary.jsonl`
- JSONL rows: 9
- Summary row count matches FIT count: yes
- Parser used for this batch: `fitdecode, fitparse`

## Archive

- Archive status: not archived yet
- Reason: current-month loose FIT files stay available for repair, reparse, or enrichment
- Folder bytes with loose FIT files: 954,908

## Notes

- Raw FIT files are binary training records and may contain GPS, timestamps, heart rate, and device metadata.
- Processed summaries should be written to `data/processed/`.
