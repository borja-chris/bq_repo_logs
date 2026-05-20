# BQ Repo Log

System of record for a multi-year Boston Marathon qualifying attempt.

Current working frame:

- BQ category: Male 35-39
- Posted BQ standard: 3:00:00
- Practical planning target: approximately 2:55:00 or faster
- Current Goal A race: half marathon on 2026-12-06
- Current preferred framework: Hanson-inspired half-marathon training

Use `sources/` for durable planning context, `plans/` for upcoming training, `logs/` for completed work, `retros/` for reviews, and `decisions/` for meaningful changes to the plan.

## Current Week

<!-- current-week:start -->
Source: [01_pre_block_ramp.md](plans/2026-half-marathon/01_pre_block_ramp.md)

Week of `2026-05-18`

- Target mileage: `about 24-26`
- Actual mileage so far: `9.02`
- Primary purpose: establish a normal 5-day rhythm after the travel-adjusted week
- Week status: `Tuesday run logged`

| Day | Planned | Actual | Notes |
| --- | --- | --- | --- |
| Monday | Off | 5.23 mi run | 58:12 at 11:08/mi. |
| Tuesday | 5 mi easy | 3.79 mi run | 38:21 at 10:07/mi. |
| Wednesday | 4 mi very easy | x | x |
| Thursday | 5 mi easy | x | x |
| Friday | Off | x | x |
| Saturday | 4 mi easy | x | x |
| Sunday | 7-8 mi easy | x | x |

The listed source plan is the live reference for this week.
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

COROS data workflow:

1. Drop new `.fit` files in the repo root.
2. Run `python scripts/ingest_coros_fit.py`.
3. Let the script move them into a dated batch folder under `data/coros_exports/`, update the processed summaries, and refresh the current logs.
4. Archive completed prior-month raw batches into `fit_files.tar.gz` after verification.

Aim to make this as Ai Tool Agnostic as possible.
