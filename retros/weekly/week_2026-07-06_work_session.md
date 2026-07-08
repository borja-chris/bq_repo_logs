# Week of 2026-07-06 Work-Session Retro

## Label

- This is a work-session retrospective, not a training retrospective.

## Summary

- Goal: reduce the token cost of the default agent-load surface and per-week artifacts without losing human-readable signal.
- Result: three commits (P1 `7f6bf8f`, P2 `87ed91a`, P3 `1fba209`) cut always-loaded context by roughly 39%, removed 100%-redundant CSV summaries from the ingest pipeline, and archived unreferenced framework files. Pipeline change verified end-to-end with `--sync-only`.
- Main issue: several always-loaded documents (AGENTS.md, README.md) restated content that already lived in `docs/repo_workflow.md` and `sources/`, and the COROS ingest emitted a CSV that carried the exact same 26 fields as the JSONL.

## What Worked

- Three parallel Explore agents produced enough concrete evidence (line counts, verbatim duplicated phrases, redundant fields) to write a specific plan rather than a vague direction.
- Phasing P1 → P2 → P3 kept each commit small and reviewable, and let low-risk edits (docs) land before the code refactor (CSV removal).
- Archiving the CSVs to `data/archive/processed_csv/` instead of `rm` preserved the historical data at zero ongoing cost.
- Skipping planned items (P3.8 table, P3.9 sources/README) after re-evaluation avoided churn that would not have paid back.
- `--sync-only` on the current week was the right verification path — it exercised the trimmed weekly-log body without needing a new FIT import.

## What Did Not Work

- First P1 commit accidentally included local tooling state (`.codex`, `.tokensave/`) because I used `git add -A`. Recovered with a soft reset and updated `.gitignore`, but the mistake would have been avoided by staging explicit paths from the start.
- The plan overestimated the win from converting the Decision Triggers prose to a table — the existing 7-bullet list was already tighter.
- The initial retro action item defaulted to "operator does it" when the verification step was actually mine to run — user correctly pushed back.

## Changes Made

- Trimmed `AGENTS.md` from 196 → 85 lines by dropping the directory tree and duplicated operational rules.
- Trimmed `README.md` from 64 → 43 lines by pointing to `docs/repo_workflow.md` for workflow.
- Removed CSV emission from `scripts/summarize_coros_fit.py`, `scripts/ingest_coros_fit_batch.py`, `scripts/ingest_coros_fit_weather.py`, `scripts/ingest_coros_fit.py`; updated `scripts/README.md` and `docs/repo_workflow.md`.
- Archived 16 existing CSV summaries to `data/archive/processed_csv/`.
- Added `.tokensave/` and `.codex` to `.gitignore`.
- Created `sources/00_project_context.md` as the canonical BQ/cycle baseline; deleted `sources/01_current_operating_plan_2026_half.md` and `sources/02_runner_background_and_bq_arc.md`.
- Removed the auto-summary day table from the weekly-log body in `scripts/weekly_entries.py` (README still renders the table).
- Replaced restated assumptions in `plans/2026-half-marathon/02_18_week_hanson_inspired_plan.md` with a link to `sources/00`.
- Moved `training_ideologies/` under `archive/`.
- Refreshed `sources/05_chat_handoff_summary.md` to drop the dual-CSV-and-JSONL line.
- Ran `--sync-only` against week_2026-07-06; auto-summary block correctly rendered metadata-only.

## Follow-Up

- Older `data/coros_exports/*/manifest.md` files still reference their CSV paths. Historical, no action needed.
- Any future doc edit that would have linked to `sources/01_*` or `sources/02_*` should point to `sources/00_project_context.md`.

## Action Item

- Owner: operator (Kelik)
- Action: on the next real COROS batch, confirm the resulting `manifest.md` shows a single JSONL processed-summary line and no CSV path, and that the weekly-log auto-summary block stays metadata-only.
- Success condition: batch imports cleanly with no CSV artifact under `data/processed/`, manifest lists only the JSONL, and no follow-up patch is needed.
