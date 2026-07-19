# 2026-07-19 Heat-Adjusted Pace Enrichment Work Retro

## Label

- This is a work-session retrospective, not a training retrospective.

## Summary

- Trigger: the open heat-index action item in `retros/weekly/week_2026-07-19_work_session.md`, with a request to plan work executable by a team of sub-agents.
- Work: ran the full brainstorm -> spec -> plan -> subagent-driven-execution loop. Designed a heat-adjusted *pace* estimate (Mark Hadley temperature + dew point chart) rather than a bare flag; added a pure `scripts/heat_adjust.py` module, wired dew-point/apparent-temp enrichment and an `Activity.heat_note`, backfilled all processed data back to the 2023 bulk import, and migrated 8 legacy-format historical weekly logs.
- Result: seven commits (`51f8bba` module, `b011b62` enrichment, `426c9da` backfill + decision + retro close, `23eb2dc` review fixes, `46b9831` historical migration, `d2b99ad` doc typo, plus the spec/plan commits). Feature verified end-to-end; the heat-index action item is closed with a matching record in `decisions/`.

## What Worked

- Grounded the formula before baking it into stored data. Web-searched and confirmed the exact Mark Hadley band numbers instead of trusting memory, since the chart was about to become a persisted computation on years of activities.
- Caught a false premise at design time. The action item assumed temp+humidity were "already captured," but the enrichment fetched only `temperature_2m`. Surfacing that before planning reshaped the whole approach (fetch dew point; drive the chart from it) rather than discovering it mid-implementation.
- Let the framework choice reshape scope. The EM's recollection of the "reddit heat chart" turned a binary heat flag into a heat-neutral equivalent pace — a far more decision-useful output that directly explains a slow hot run.
- Honored the repo's collaboration model over the tool's default. Ran a decision gate on branch and commit model up front, then adapted subagent-driven-development so sub-agents implemented and tested but never committed; the Tech Lead reviewed each working-tree diff and committed/pushed centrally per phase with explicit paths.
- Verified at every gate before committing. Inspected the dry-run backfill, checked every deleted prose fragment survived the log migration, and validated each changed weekly total equalled the sum of that week's processed activities.
- The final whole-branch review earned its keep. It found two real display-consistency bugs (a printed sum that could fail to add up near rounding boundaries; a percentage read from a stored field instead of the live fraction); both were fixed with a regression test.
- Deferred large churn to an explicit decision. Rather than silently commit a ~470-line historical-log migration, paused and let the EM choose — then executed it with the same verification discipline once approved.

## What Did Not Work

- The Task 3 sub-agent failed messily. It backgrounded the network-bound backfill and returned an incomplete "I'll wait for the backfill to finish" message, leaving 17 of 20 data files half-written, no re-render, no docs, and no report. Recovery cost a cycle. Long, network-bound, side-effecting operations fit poorly with the fire-and-report sub-agent contract; the controller should own them (which it then did inline, idempotently).
- `git diff` was silently truncated. The RTK hook collapsed `git diff` to a ~6-line summary when run inside a grouped/piped redirect, producing a near-empty review package twice before switching to a direct `git diff > file` redirect. Saved to memory to avoid a third occurrence.
- The plan named a command that could not do the job. Task 3 assumed `scripts/ingest_coros_fit.py --sync-only` would re-render all affected weekly logs, but it only touches the current week; historical weeks needed a per-week `sync_week` loop. A plan-vs-reality gap that only surfaced at execution.

## Changes Made

- `51f8bba` — pure `scripts/heat_adjust.py` (chart math) + unit tests.
- `b011b62` — fetch `dew_point_2m` + `apparent_temperature`; store six new fields; `Activity.heat_note`; managed-notes surfacing + tests.
- `426c9da` — backfill all `data/processed/*.jsonl`; re-render current-week log; decision record; close the heat-index action item.
- `23eb2dc` — final-review fixes (display self-consistency) + regression test.
- `46b9831` — migrate 8 legacy historical weekly logs; add 40 heat notes; correct three stale mid-week mileage totals to full-week sums that match the processed data.
- `d2b99ad` — spec example pace typo (`8:42` -> `8:43/mi`).

## Follow-Up

- The migration surfaced that historical weekly logs can silently drift from the processed activity data: three weeks were stale mid-week snapshots whose `Actual mileage so far` under-counted the real runs, undetected until a full re-render. There is currently no check that a rendered weekly log agrees with its source data.
- Long network-bound pipeline operations (backfill, archive re-fetch) should be run by the controller, not delegated to a report-back sub-agent whose contract assumes a bounded, self-contained task.

## Action Item

- Owner: Claude (Tech Lead)
- Action: add a reconciliation check (a `scripts/` script plus a test) that, for every existing `logs/weekly/week_*.md`, compares its `Actual mileage so far` against the sum of `distance_mi` for that week's activities in `data/processed/*.jsonl` and reports any mismatch, so stale or drifted logs are caught deliberately rather than by accident during an unrelated re-render.
- Success condition: running the check against the current repo reports zero mismatches, and a deliberately edited weekly total is flagged with its expected-vs-actual value in a single command.
- Status: Done — implemented 2026-07-19 in `scripts/reconcile_weekly_mileage.py` with `tests/test_reconcile_weekly_mileage.py` (6 tests) and a `scripts/README.md` entry (commit `31e9d9b`). Verified both halves: the current repo reports "OK: 9 weekly logs reconcile with processed data" (exit 0), and a deliberately edited total is flagged as `logged 99.99 != expected 30.03` (exit 1).
