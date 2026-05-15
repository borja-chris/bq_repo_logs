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

Week of `2026-05-11`

- Target mileage: `about 22-25`
- Actual mileage so far: `15.38`
- Primary purpose: settle into rhythm while accommodating travel logistics
- Week status: `Thursday run logged`

| Day | Planned | Actual | Notes |
| --- | --- | --- | --- |
| Monday | Rest | Rest day | Took a rest day because the Sunday recovery bike ride was not especially recovery-like. |
| Tuesday | 5 mi easy | 5.80 mi run | 1:09:53 at 12:03/mi. Right glute is still sore from the 5K race over the weekend and was noticeable during strides. |
| Wednesday | 4 mi very easy | 5.58 mi run | 1:05:07 at 11:40/mi. |
| Thursday | 5 mi easy | 4.00 mi run | 47:09 at 11:47/mi. |
| Friday | Off | x | x |
| Saturday | 3-4 mi easy | x | x |
| Sunday | 6-7 mi easy | x | x |

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
