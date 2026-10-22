# COROS Export Manifest - 2026-10-22

## Import

- Source file: `481227540841661018.fit`
- Repo folder: `data/coros_exports/COROS_export_2026-10-22/`
- Imported on: 2026-10-22
- FIT files: 1
- FIT payload bytes: 153,428
- Removed sidecars: 0 `*:Zone.Identifier` files

## Integrity

- Hash file: `SHA256SUMS.txt`
- Hash entries: 1

## Processing

- Processed JSONL: `data/processed/coros_export_2026-10-22_summary.jsonl`
- JSONL rows: 1
- Summary row count matches FIT count: yes
- Parser used for this batch: `fitdecode`

## Archive

- Archive status: not archived yet
- Reason: current-month loose FIT files stay available for repair, reparse, or enrichment
- Folder bytes with loose FIT files: 153,560

## Notes

- Raw FIT files are binary training records and may contain GPS, timestamps, heart rate, and device metadata.
- Processed summaries should be written to `data/processed/`.
