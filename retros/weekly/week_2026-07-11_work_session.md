# Week of 2026-07-11 Work-Session Retro

## Label

- This is a work-session retrospective, not a training retrospective.

## Summary

- Goal: make `plans/2026-half-marathon/` easier for both agents and humans to reference.
- Result: reorganized the folder to a single source of truth — moved the 18 per-week files into `weeks/` keyed only by date (`week_YYYY-MM-DD.md`), extracted the block-level framework into `03_framework.md`, and deleted the duplicated `02_18_week_hanson_inspired_plan.md` (commit `0ec14d9`). Then renamed `00_overview.md` to `README.md` so GitHub renders the overview and week index inline when browsing the folder (commit `5f0236f`).
- Diagnosis that drove it: the day-by-day tables lived in two places (per-week files + master plan), and the plan layer used a `week_NN_` ordinal prefix that could not be glob-joined to the bare `week_YYYY-MM-DD.md` key used by `logs/weekly/` and `retros/weekly/`.

## What Worked

- Proved the deletion was lossless before doing it: diffed every per-week file against the corresponding week section of the master plan and confirmed they were byte-identical (only trailing-newline noise), so removing the master could not drop content.
- Closed the prior session's action item. The mechanical reorg was delegated to a subagent pinned to Sonnet (~46K subagent tokens), Tech Lead verified before commit, and the token-heavy execution stayed off Opus — the first delegation where the model-selection rule was actually honored end to end.
- Post-execution verification was specific, not trusting the report: confirmed all 18 renames were 100% similarity (pure moves), that `03_framework.md` differed from the original preamble only by the retitled H1 and appended pointer, and ran a stale-reference sweep that correctly separated live refs (updated) from historical `logs/`/`retros/` records (left intact).
- Every commit was staged by explicit path, keeping pre-existing untracked items (`.claude/`, `retros/block/…`) out of both commits.

## What Did Not Work

- The initial reorg proposal optimized file structure but missed the GitHub-rendering affordance — the EM surfaced the `README.md` rename, not me. A "how does a human actually browse this on GitHub" pass would have folded it into the first proposal instead of a second commit.
- Left two cosmetic issues open by choice (numbering gap `01/03`, verbose week-18 index cell) rather than resolving or explicitly deferring them in a tracked place.

## Changes Made

- Reorg (`0ec14d9`): `weeks/` subdirectory with 18 date-keyed files, new `03_framework.md`, deleted master plan, added a Week Index to the overview, repointed live refs in `docs/repo_workflow.md` and `sources/05_chat_handoff_summary.md`, recorded `decisions/2026-07-11_plan_file_reorg.md`.
- README rename (`5f0236f`): `00_overview.md` → `README.md`, repointed the one live link in `03_framework.md`, updated the decision record.
- File Naming addition (`b0b4197`): recorded the plan overview, framework, and per-week naming convention in `docs/repo_workflow.md` (see Action Item).

## Follow-Up

- Cosmetic, non-blocking: decide whether to renumber `03_framework.md` → `02_framework.md` (closing the gap) or keep the gap as a deliberate marker of the deletion; optionally trim the verbose week-18 Week Index cell.

## Action Item

- Owner: Claude (Tech Lead)
- Action: add plan-file naming to the `## File Naming` section of `docs/repo_workflow.md` — the per-week key `plans/2026-half-marathon/weeks/week_YYYY-MM-DD.md`, plus `README.md` (folder overview) and `03_framework.md` (block-level framework) — noting the week key intentionally matches the log/retro key.
- Success condition: the File Naming section lists the plan week-file path and it is character-for-character the same date key as `logs/weekly/week_YYYY-MM-DD.md` and `retros/weekly/week_YYYY-MM-DD.md`.
- Status: Resolved same session in `b0b4197` — File Naming now lists the plan overview, framework, and per-week key, with the per-week key matching the active weekly log and weekly retro date key.
