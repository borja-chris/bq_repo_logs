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

Source: [plans/2026-half-marathon/01_pre_block_ramp.md](/home/kelik/projects/bq_repo_logs/plans/2026-half-marathon/01_pre_block_ramp.md)

Week of `2026-05-11`

- Target mileage: about `24-26`
- Primary purpose: settle into rhythm

| Day | Run | Purpose | Notes |
| --- | --- | --- | --- |
| Monday | Rest | Recovery | Took rest after the Sunday bike ride ended up less recovery-like than intended. |
| Tuesday | 5 mi easy | Easy aerobic | Optional 4-6 x 20 sec strides if legs feel good. |
| Wednesday | 3 mi very easy | Recovery / easy | Replaces Monday's easy run. No strides. Keep it controlled if the right glute is still sore. |
| Thursday | 5 mi easy | Easy aerobic | No steady finish; keep it conversational. |
| Friday | 3 mi easy | Recovery / easy | Can flip with Monday or Wednesday if needed. |
| Saturday | 3-4 mi easy | Easy aerobic | Stay relaxed. |
| Sunday | 6-7 mi easy | Long run | Finish fresh. |

The 18-week half-marathon block starts on `2026-06-01`. Until then, this pre-block ramp week is the live reference.

## Workflow

Use [docs/repo_workflow.md](/home/kelik/projects/bq_repo_logs/docs/repo_workflow.md) as the operating loop for normal usage.

The short version:

1. Read current assumptions from `sources/`.
2. Use weekly files in `plans/2026-half-marathon/` for upcoming training.
3. Log completed work in `logs/`.
4. Review the week in `retros/weekly/`.
5. Record meaningful changes in `decisions/`.

Raw COROS exports belong under `data/coros_exports/`. Processed summaries belong under `data/processed/`.

Aim to make this as Ai Tool Agnostic as possible.
