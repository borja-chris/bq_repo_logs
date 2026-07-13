# 2026-07-13 Import Week-Mismatch Retro

## Label

- Tech (work-session) retro. Covers the 2026-07-13 ingest of the Sunday
  2026-07-12 long run and the import-date-vs-activity-date bug it exposed.
- Not a training retro — the run itself is logged on the 2026-07-06 week and
  reads normally (8.52 mi easy, Zone 2). This is about the tooling.

---

## Summary

- Trigger: single loose `.fit` dropped in root on 2026-07-13 with a "longer
  run, kept it in Zone 2" heads-up. The activity's real start was Sunday
  2026-07-12 09:59, i.e. the *previous* Mon–Sun week.
- What happened: `scripts/ingest.sh` (no `--date`) defaulted its batch/sync
  date to today (2026-07-13). The FIT parsed and enriched fine, the summary
  JSONL carried the correct 2026-07-12 start time — but the daily-entry sync
  only ever touches `monday_of(today)`'s week (2026-07-13 → 2026-07-19). The
  2026-07-12 activity fell outside that window and was silently dropped from
  daily-entry population. The run existed in `data/processed/` but appeared in
  no daily entry and no weekly total.
- The import still reported "Processed activities: 1 / Weather enriched: 1/1"
  and exited 0. Nothing signalled the miss.
- Fix applied this session: re-ran `scripts/ingest.sh --sync-only --date
  2026-07-12`, which retargeted the 2026-07-06 week, populated the 2026-07-12
  entry from the already-processed JSONL, refreshed that week's total
  (27.59 → 36.11 mi), and attached the manual note. A follow-up plain
  `--sync-only` restored README's "Current Week" to 2026-07-13 (the dated
  re-sync had reverted it to 2026-07-06).

## What Worked

- Verified placement before trusting the exit code. The tool said "success,"
  but a `grep` for the run's distance/HR across `logs/` returned nothing — that
  empty grep, not the tool output, is what caught the miss.
- Read the actual sync path (`sync_records` → `monday_of(today)`,
  `load_processed_activities_for_week` globs *all* JSONL and filters by activity
  `local_date`) before choosing a fix, so the `--sync-only --date` correction
  was known-good rather than a guess. Because the loader already filters by
  activity date across all processed files, no re-import or file surgery was
  needed — the data was right, only the sync window was wrong.
- Staging discipline held: explicit paths, no `git add -A` (left untracked
  `.claude/` alone), commit + push for the data phase before writing this retro.

## What Did Not Work / Watch

- **Silent wrong-week filing is a repeatable footgun.** Any run imported on a
  different day than it happened — the routine next-morning import, and every
  Sunday-run-imported-Monday case across the Mon→Sun week boundary — hits this.
  The tool reports success while the run lands in no daily entry. This is the
  same *class* of silent failure the FIT-parser preflight was built to kill:
  the operation "succeeds" while quietly doing nothing useful.
- **The dated re-sync has a side effect.** Passing `--date` to fix a past week
  also rewrites README's current-week block to that past week, because README
  refresh keys off the same `today`. The correction is a two-step dance
  (dated sync to fix the week, then bare sync to restore README) that is easy
  to forget the second half of and leave README pointing at a stale week.

## Changes Made

- `81b3b0c` / pushed as `0aae628` — imported 2026-07-12 long run (8.52 mi,
  10:55/mi, avg HR 143 / max 164, Zone 2), refiled to the 2026-07-06 week,
  refreshed that week's total to 36.11 mi, advanced README to the 2026-07-13
  week. Batch folder `COROS_export_2026-07-13/` keeps import-date naming per
  existing convention.
- This retro.

## Root Cause

`sync_records` derives its one target week from `today` (`args.date` or the
clock), not from the dates of the activities actually being imported. Import
date and activity date are treated as the same thing; they diverge whenever a
run is imported on a later day.

## Proposed Fix (direction, not yet built)

Recommended primary fix: after processing, drive the daily-entry sync from the
imported activities' own `local_date`s — sync every distinct Mon–Sun week that
contains a freshly imported activity, instead of only `monday_of(today)`. Keep
README's current-week refresh keyed to the real clock date so fixing a past
week never disturbs the current-week block (removes the two-step dance).

Guardrail to add alongside it: after enrichment, if any freshly processed
activity's `local_date` is not covered by any week the run synced, print a loud
warning naming the activity and its date (and make it exit non-zero under a
`--require-covered`-style flag, mirroring `--require-weather`). Success should
never be reported for an activity that landed in no daily entry.

This is a proposal for a later work session; no script code was changed here.

## Action Item (Tech)

- Owner: Claude (Tech Lead) — propose exact diff; EM approves before merge.
- Action: make `scripts/ingest_coros_fit.py` sync the week(s) derived from
  imported activities' dates (not `monday_of(today)`), decouple the README
  current-week refresh from `--date`, and warn (loudly, with a fail-flag
  option) when any processed activity is covered by no synced week. Add a test
  for the cross-week case (Sunday run imported the following day).
- Success condition: dropping a single FIT whose start date is in a prior week
  and running plain `scripts/ingest.sh` once populates the correct daily entry
  and weekly total with no manual `--date` re-sync, leaves README on the true
  current week, and prints a warning if any activity falls outside every synced
  week. Verified by the new test and one live cross-week import.
