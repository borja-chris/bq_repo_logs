# COROS Export Manifest - 2026-10-06

## Import

- Source file: `480832519546110153.fit`
- Repo folder: `data/coros_exports/COROS_export_2026-10-06/`
- Imported on: 2026-10-06
- FIT files: 1
- FIT payload bytes: 87,654
- Removed sidecars: 0 `*:Zone.Identifier` files

## Integrity

- Hash file: `SHA256SUMS.txt`
- Hash entries: 1

## Processing

- Processed JSONL: `data/processed/coros_export_2026-10-06_summary.jsonl`
- JSONL rows: 1
- Summary row count matches FIT count: yes
- Parser used for this batch: `fitdecode`

## Archive

- Archive status: not archived yet
- Reason: current-month loose FIT files stay available for repair, reparse, or enrichment
- Folder bytes with loose FIT files: 87,786

## Notes

- Raw FIT files are binary training records and may contain GPS, timestamps, heart rate, and device metadata.
- Processed summaries should be written to `data/processed/`.
