# COROS Export Manifest - 2026-08-26

## Import

- Source files: `4` files
- Repo folder: `data/coros_exports/COROS_export_2026-08-26/`
- Imported on: 2026-08-26
- FIT files: 4
- FIT payload bytes: 463,911
- Removed sidecars: 0 `*:Zone.Identifier` files

## Integrity

- Hash file: `SHA256SUMS.txt`
- Hash entries: 4

## Processing

- Processed JSONL: `data/processed/coros_export_2026-08-26_summary.jsonl`
- JSONL rows: 4
- Summary row count matches FIT count: yes
- Parser used for this batch: `fitdecode`

## Archive

- Archive status: not archived yet
- Reason: current-month loose FIT files stay available for repair, reparse, or enrichment
- Folder bytes with loose FIT files: 465,313

## Notes

- Raw FIT files are binary training records and may contain GPS, timestamps, heart rate, and device metadata.
- Processed summaries should be written to `data/processed/`.
