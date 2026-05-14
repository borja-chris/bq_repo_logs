# Chat Handoff Summary

## Current State

The repository structure has been initialized for planning, logs, retros, decisions, templates, and data.

## How To Use This Repo

- Store durable planning assumptions in `sources/`.
- Store future training plans in `plans/`.
- Store completed daily and weekly records in `logs/`.
- Store reviews in `retros/`.
- Store meaningful plan changes in `decisions/`.
- Store raw and processed training data in `data/`.
- Use `docs/repo_workflow.md` for the weekly operating loop.
- Use weekly files in `plans/2026-half-marathon/` for normal week-by-week adjustments.

## Operational Learnings

- For COROS imports, the user should be able to drop raw `.fit` files in the repo root and let Codex handle sorting, hashing, summary generation, and archiving.
- The operator-facing default should be one command: `python scripts/ingest_coros_fit.py`.
- FIT ingest should also sync the repo-facing Markdown layer: matching daily logs, the live weekly log, and the managed current-week block in `README.md`.
- Human interaction model: factual repo maintenance is automatic by default; interpretation should be drafted; plan and framework decisions should still be surfaced explicitly.
- Processed summaries are the working layer. Prefer both reviewable CSV and machine-readable JSONL when parser support is available.
- Raw FIT data should remain preserved as the canonical source, but prior-month completed batches can be compressed into `fit_files.tar.gz` to reduce clutter.
- Archive only after processed summaries exist, counts match, and archive membership verification passes.
- When loose FIT files are removed, processed JSONL should retain enough archive metadata to find the original source later.
