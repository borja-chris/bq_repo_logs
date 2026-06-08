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

Week of `2026-06-01`

- Target mileage: `about 28-30`
- Actual mileage so far: `21.51`
- Primary purpose: make upper-20s mileage feel normal
- Week status: `Sunday run logged`

| Day | Planned | Actual | Notes |
| --- | --- | --- | --- |
| Monday | Off | x | x |
| Tuesday | 5-6 mi easy | 3.37 mi run | 39:50 at 11:49/mi. |
| Wednesday | 5 mi very easy | 3.15 mi run | 42:59 at 13:39/mi. |
| Thursday | 6 mi easy | 5.75 mi run | 1:17:24 at 13:28/mi. |
| Friday | Off | 1.77 mi run | 21:30 at 12:09/mi. |
| Saturday | 4-5 mi easy | 3.12 mi run | 25:32 at 8:11/mi. |
| Sunday | 8-9 mi easy | 4.35 mi run | 51:31 at 11:51/mi. |

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
