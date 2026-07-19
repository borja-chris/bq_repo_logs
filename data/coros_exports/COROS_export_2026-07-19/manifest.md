# COROS Export Manifest - 2026-07-19

## Import

- Source files: `2` files
- Repo folder: `data/coros_exports/COROS_export_2026-07-19/`
- Imported on: 2026-07-19
- FIT files: 2
- FIT payload bytes: 304,301
- Removed sidecars: 2 `*:Zone.Identifier` files

## Integrity

- Hash file: `SHA256SUMS.txt`
- Hash entries: 2

## Processing

- Processed JSONL: `data/processed/coros_export_2026-07-19_summary.jsonl`
- JSONL rows: 2
- Summary row count matches FIT count: yes
- Parser used for this batch: `fitdecode`

## Archive

- Archive status: not archived yet
- Reason: current-month loose FIT files stay available for repair, reparse, or enrichment
- Folder bytes with loose FIT files: 304,565

## Notes

- Raw FIT files are binary training records and may contain GPS, timestamps, heart rate, and device metadata.
- Processed summaries should be written to `data/processed/`.
