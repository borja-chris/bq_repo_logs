# Scripts

This directory is reserved for repeatable repo operations.

Near-term candidates:

- Weekly rollover helper: create daily log stubs, weekly log, and weekly retro from templates.
- Decision gate helper: collect recent weekly retros before mileage or workout changes.

## FIT Summaries

`summarize_coros_fit.py` reads FIT files from an import directory and writes a CSV summary to `data/processed/`.

Example:

```bash
python scripts/summarize_coros_fit.py data/coros_exports/COROS_export_2026-05-09 data/processed/coros_export_2026-05-09_summary.csv
```

It requires the optional `fitparse` package.

Keep scripts small and reviewable. The Markdown files remain the system of record.
