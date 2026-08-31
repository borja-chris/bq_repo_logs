# COROS Export Manifest - 2026-08-30

## Import

- Source file: `479914696034517092.fit`
- Repo folder: `data/coros_exports/COROS_export_2026-08-30/`
- Imported on: 2026-08-30
- FIT files: 1
- FIT payload bytes: 104,033
- Removed sidecars: 0 `*:Zone.Identifier` files

## Integrity

- Hash file: `SHA256SUMS.txt`
- Hash entries: 1

## Processing

- Processed JSONL: `data/processed/coros_export_2026-08-30_summary.jsonl`
- JSONL rows: 1
- Summary row count matches FIT count: yes
- Parser used for this batch: `fitdecode`

## Archive

- Archive status: not archived yet
- Reason: current-month loose FIT files stay available for repair, reparse, or enrichment
- Folder bytes with loose FIT files: 104,165

## Notes

- Raw FIT files are binary training records and may contain GPS, timestamps, heart rate, and device metadata.
- Processed summaries should be written to `data/processed/`.
