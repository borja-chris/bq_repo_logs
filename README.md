# BQ Repo Log

System of record for a multi-year Boston Marathon qualifying attempt.

Current working frame:

- BQ category: Male 35-39
- Posted BQ standard: 3:00:00
- Practical planning target: approximately 2:55:00 or faster
- Current Goal A race: half marathon on 2026-10-04
- Current preferred framework: Hanson-inspired half-marathon training

Use `sources/` for durable planning context, `plans/` for upcoming training, `logs/` for completed work, `retros/` for reviews, and `decisions/` for meaningful changes to the plan.

## Current Week

Source: [plans/2026-half-marathon/01_pre_block_ramp.md](plans/2026-half-marathon/01_pre_block_ramp.md)

Week of `2026-05-11`

- Target mileage: about `22-25`
- Actual mileage so far: `5.80`
- Primary purpose: settle into rhythm while accommodating travel logistics
- Week status: `Tuesday run logged`

| Day | Planned | Actual | Notes |
| --- | --- | --- | --- |
| Monday | Rest | Rest | Took rest after the Sunday bike ride ended up less recovery-like than intended. |
| Tuesday | 5 mi easy | 5.80 mi easy | 1:09:53 at 12:03/mi. Right glute still sore from the weekend 5K and noticeable during strides. |
| Wednesday | 4 mi very easy | x | Replaces Monday's easy run. No strides. Keep it controlled. |
| Thursday | 5 mi easy | x | No steady finish; keep it conversational. |
| Friday | Off | x | Packing and last-minute errands. No makeup mileage. |
| Saturday | 3-4 mi easy | x | Use this to loosen up after the flight. Stay relaxed. |
| Sunday | 6-7 mi easy | x | Finish fresh. |

The 18-week half-marathon block starts on `2026-06-01`. Until then, this pre-block ramp week is the live reference.

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
2. Move them into a dated batch folder under `data/coros_exports/`.
3. Generate processed summaries in `data/processed/`.
4. Archive completed prior-month raw batches into `fit_files.tar.gz` after verification.

Aim to make this as Ai Tool Agnostic as possible.
