# Chat Handoff Summary

## Current State

The repository structure has been initialized for planning, logs, retros, decisions, templates, and data.

## How To Use This Repo

- Store durable planning assumptions in `sources/`.
- Store future training plans in `plans/`.
- Store completed weekly records and historical daily archives in `logs/`.
- Store reviews in `retros/`.
- Store meaningful plan changes in `decisions/`.
- Store raw and processed training data in `data/`.
- Use `docs/repo_workflow.md` for the weekly operating loop.
- Use weekly files in `plans/2026-half-marathon/` for normal week-by-week adjustments.
- Treat `logs/weekly/week_YYYY-MM-DD.md` as the only active log; any `logs/daily/` content is historical.

## Operational Learnings

- For COROS imports, the user should be able to drop raw `.fit` files in the repo root and let Codex handle sorting, hashing, summary generation, and archiving.
- The operator-facing default should be one command: `.venv/bin/python scripts/ingest_coros_fit.py`.
- FIT ingest should also sync the repo-facing Markdown layer: the active weekly log with appended daily entries, and the managed current-week block in `README.md`.
- On the first maintenance pass of a new month, historical daily logs from the completed prior month should move into `logs/daily/YYYY/YYYY-MM/` and get a generated `monthly_summary.md`.
- Human interaction model: factual repo maintenance is automatic by default; interpretation should be drafted; plan and framework decisions should still be surfaced explicitly.
- Processed summaries are the working layer, written as machine-readable JSONL under `data/processed/`.
- Raw FIT data should remain preserved as the canonical source, but prior-month completed batches can be compressed into `fit_files.tar.gz` to reduce clutter.
- Archive only after processed summaries exist, counts match, and archive membership verification passes.
- When loose FIT files are removed, processed JSONL should retain enough archive metadata to find the original source later.
