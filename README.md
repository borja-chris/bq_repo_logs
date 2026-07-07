# BQ Repo Log

System of record for a multi-year Boston Marathon qualifying attempt.

Current working frame:

- BQ category: Male 35-39
- Posted BQ standard: 3:00:00
- Practical planning target: approximately 2:55:00 or faster
- Current Goal A race: half marathon on 2026-12-06
- Current preferred framework: Hanson-inspired half-marathon training

Use `sources/` for durable planning context, `plans/` for upcoming training, `logs/` for completed work, `retros/` for reviews, and `decisions/` for meaningful changes to the plan.
The active weekly log lives in `logs/weekly/week_YYYY-MM-DD.md`; daily entries are appended under the weekly summary there. Any `logs/daily/` content is historical only.

## Current Week

<!-- current-week:start -->
Source: [01_pre_block_ramp.md](plans/2026-half-marathon/01_pre_block_ramp.md)

Week of `2026-06-29`

- Target mileage: `about 32-35`
- Actual mileage so far: `17.18`
- Primary purpose: let low-30s become normal while keeping recovery intact
- Week status: `Wednesday run logged`

| Day | Planned | Actual | Notes |
| --- | --- | --- | --- |
| Monday | Off | 4.20 mi total (2 runs) | 44:16 at 10:32/mi. |
| Tuesday | 6 mi easy | 8.37 mi run | 1:36:58 at 11:35/mi. |
| Wednesday | 5 mi very easy | 4.61 mi run | 56:43 at 12:18/mi. |
| Thursday | 6-7 mi easy | x | x |
| Friday | Off or 3 mi very easy | x | x |
| Saturday | 5 mi easy | x | x |
| Sunday | 10 mi easy | x | x |

This block mirrors the active weekly log summary for the current week. Daily entries for the week live in `logs/weekly/week_YYYY-MM-DD.md`.
<!-- current-week:end -->

## Workflow

Use [docs/repo_workflow.md](docs/repo_workflow.md) as the operating loop for normal usage.

The short version:

1. Read current assumptions from `sources/`.
2. Use weekly files in `plans/2026-half-marathon/` for upcoming training.
3. Log completed work in `logs/`.
4. Review the week in `retros/weekly/`.
5. Record meaningful changes in `decisions/`.

Raw COROS exports belong under `data/coros_exports/`. Processed summaries belong under `data/processed/`.
Historical daily-log months should be archived under `logs/daily/YYYY/YYYY-MM/` with a generated `monthly_summary.md`.

COROS data workflow:

1. Drop new `.fit` files in the repo root.
2. Run `.venv/bin/python scripts/ingest_coros_fit.py`.
3. Let the script move them into a dated batch folder under `data/coros_exports/`, update the processed summaries, and refresh the current logs.
4. Archive completed prior-month raw batches into `fit_files.tar.gz` after verification.
5. On the first maintenance pass of a new month, let the repo archive prior-month daily logs into their month folder and refresh that month's historical summary.

Aim to make this as Ai Tool Agnostic as possible.
