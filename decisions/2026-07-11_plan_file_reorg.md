# Decision Gate - 2026-07-11

## Decision

Reorganize `plans/2026-half-marathon/` so the per-week files are the single source of truth. Move them into a `weeks/` subdirectory keyed only by date (`week_YYYY-MM-DD.md`), extract the block-level framework from the former full-plan file into `03_framework.md`, and delete the duplicated `02_18_week_hanson_inspired_plan.md`.

## Facts

- Every week's day-by-day table lived in two places: the per-week `week_NN_YYYY-MM-DD.md` files and the full `02_18_week_hanson_inspired_plan.md`. The two copies were verified content-identical at reorg time.
- The plan files used a `week_NN_` ordinal prefix, while `logs/weekly/` and `retros/weekly/` use a bare `week_YYYY-MM-DD.md` key, so plans could not be glob-joined to their logs and retros by a shared filename.
- The block-level framework (purpose, weekly rhythm, pace guide, adjustment rules) was only the preamble of the full-plan file; it is genuinely cycle-wide, not per-week.

## Preference

Single source of truth over managed duplication. Keep block-level framework in one durable file and each week's operational detail in one per-week file that shares its date key with the matching log and retro.

## Risk

The reorg is content-preserving, so training content is unchanged. The main risk is stale path references elsewhere in the repo. Live references in `README.md`, `docs/repo_workflow.md`, and `sources/05_chat_handoff_summary.md` are updated in the same change. Historical records in `logs/` and `retros/` are left as point-in-time records and intentionally not rewritten.

## Adaptation

New layout:
- `README.md` — race, volume frame, structure, plan-file map, and a week index table. Renamed from `00_overview.md` so GitHub renders it inline when browsing the folder.
- `01_pre_block_ramp.md` — unchanged.
- `03_framework.md` — block-level framework extracted from the former full plan.
- `weeks/week_YYYY-MM-DD.md` — one file per week, the single source of truth for that week's day-by-day plan.

The former `02_18_week_hanson_inspired_plan.md` is removed; regenerating a concatenated full-plan view, if ever wanted, becomes a mechanical rollup of `weeks/` rather than a maintained copy.

## Final Call

Proceed. The reorg removes the duplicate-edit hazard and aligns the plan layer's date key with logs and retros, at the cost of losing filename ordinal-sort in `ls` (mitigated by the week index in `README.md` and the `# Week N` heading inside each file).
