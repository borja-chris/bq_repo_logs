# Decision Gate - 2026-09-29

## Decision

Reduce Week 10 target 46→40 mi and Week 11 target 48→45 mi, cutting only from
easy days (Monday, Friday, Saturday) and the Week 10 Sunday long run (13→12).
Tuesday strength and Thursday HMP workouts are unchanged in both weeks. Weeks
12-18 are left as originally planned.

## Facts

- Prior sequence jumped 35(wk9)→46(wk10, +11)→48(wk11, +2) before dropping to
  42(wk12, -6). The single +11 jump was the largest single-week increase in
  the block.
- Revised sequence: 35→40(+5)→45(+5)→42(-3, unchanged from original plan).
- Not a peak-mileage or 58-60 mpw gate decision (see `docs/decision_formats.md`
  → "58-60 mpw Gate") — both changes are reductions relative to the prior plan.

## Preference

Operator asked for a progressive mileage ramp rather than a large single-week
jump into week 10.

## Risk

Minimal — reducing rather than increasing load. Main risk considered was
degrading SOS quality (Tuesday strength, Thursday HMP) or long-run
progression to hit the lower numbers; both were protected by cutting easy
volume first (see Adaptation).

## Adaptation

- Week 10 (`plans/2026-half-marathon/weeks/week_2026-10-05.md`): Mon 4→3,
  Fri 7→5, Sat 5→3, Sun 13→12 LR (small trim only). Tue 8 and Thu 9 unchanged.
- Week 11 (`plans/2026-half-marathon/weeks/week_2026-10-12.md`): Mon 4→3,
  Fri 7→6, Sat 6→5. Sunday LR (13) and both SOS days (Tue 9, Thu 9) unchanged.
- Regenerated via `bash scripts/ingest.sh --sync-only`, which refreshed
  `plans/2026-half-marathon/BLOCK_OVERVIEW.md` (README/STATUS had no diff —
  current week is 9, not yet touched by this change).

## Final call

Applied as described above. Weeks 12-18 unchanged.
