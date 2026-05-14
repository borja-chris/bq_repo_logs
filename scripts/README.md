# Scripts

This directory is reserved for repeatable repo operations.

Near-term candidates:

- Weekly rollover helper: create daily log stubs, weekly log, and weekly retro from templates.
- Decision gate helper: collect recent weekly retros before mileage or workout changes.

## FIT Summaries

The expected operator flow is:

1. Drop new `.fit` files in the repo root.
2. Run `ingest_coros_fit.py` to move them into a dated batch folder under `data/coros_exports/`, produce processed summaries, and sync the repo records.
3. Archive completed prior-month batches later with `archive_coros_export.py`.

Primary command:

```bash
python scripts/ingest_coros_fit.py
```

Optional flags:

```bash
python scripts/ingest_coros_fit.py --sync-only
python scripts/ingest_coros_fit.py --date 2026-05-14
python scripts/ingest_coros_fit.py --no-readme
python scripts/ingest_coros_fit.py --no-logs
```

`ingest_coros_fit.py` is the operator-facing entry point. It handles:

- moving loose root-level `.fit` files into the dated batch folder
- removing `:Zone.Identifier` sidecars
- writing `SHA256SUMS.txt`
- generating CSV and JSONL processed summaries
- upserting matching daily logs from objective FIT fields
- refreshing `logs/weekly/`
- refreshing the managed current-week block in `README.md`
- writing the batch manifest

`summarize_coros_fit.py` reads FIT files from an import directory and writes a CSV summary to `data/processed/`. It can also write newline-delimited JSON (`.jsonl`) with stable machine-oriented fields such as the import batch, repo-relative source path, FIT activity ID, and SHA-256 hash.

Example:

```bash
python scripts/summarize_coros_fit.py data/coros_exports/COROS_export_2026-05-09 data/processed/coros_export_2026-05-09_summary.csv
```

```bash
python scripts/summarize_coros_fit.py \
  data/coros_exports/COROS_export_2026-05-09 \
  data/processed/coros_export_2026-05-09_summary.csv \
  --jsonl data/processed/coros_export_2026-05-09_summary.jsonl
```

It requires the optional `fitparse` package. Installing `fitdecode` as a fallback improves support for COROS files with vendor-specific FIT records.

The ingest script only automates objective recordkeeping. Subjective recovery signals, coaching interpretation, retros, and plan changes remain manual.

## FIT Archiving

`archive_coros_export.py` packs the loose FIT files in one export batch into `fit_files.tar.gz`, updates the matching processed JSONL sidecar with archive metadata, verifies archive membership, and then removes the loose `.fit` files.

Archive policy:

- Keep current-month FIT files loose after import.
- On the first maintenance pass of a new month, archive completed batches from the previous month.
- Do not archive a batch until its processed summaries already exist.

Example:

```bash
python scripts/archive_coros_export.py data/coros_exports/COROS_export_2026-05-09
```

Keep scripts small and reviewable. The Markdown files remain the system of record.

## Markdown Link Check

`check_markdown_links.py` scans Markdown files for GitHub-unsafe link targets such as:

- absolute local filesystem paths like `/home/...`
- `file://...` links
- root-relative paths like `/docs/...` that GitHub resolves outside the repo

Example:

```bash
python scripts/check_markdown_links.py
```
