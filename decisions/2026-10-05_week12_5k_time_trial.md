# Decision Gate - 2026-10-05

## Decision

Replace week 12's Tuesday 5 x 1000m speed refresh (2026-10-20) with a 5K time
trial at even effort, inside the same 8 mi total. Use the result to re-measure
fitness and, if warranted, re-derive the pace guide in
`plans/2026-half-marathon/03_framework.md` before the peak weeks (13-15).

## Facts

- Current pace guide is anchored on a ~24:35 5K equivalent (2026-07-11 parkrun,
  split-repaired), HMP ~8:38/mi. The anchor is about 3 months old; the week 3-4
  time trial it called for did not happen (shin splint, since 2026-08-12).
- Tue 2026-09-29, 3 x 1 mi strength, target 8:28/mi: reps 8:03, 8:09, 7:03.
- Thu 2026-10-01, 4 mi HMP, target 8:33-8:43/mi: reps 8:11, 8:13, 7:57, 7:28,
  in heavy heat load (74°F + 67°F dew = 141).
- Last reps are excluded as evidence: they run fast by design
  (`decisions/2026-10-01_last_rep_fast_override.md`).
- Easy runs weeks 8-9: 10:08-11:03/mi at avg HR 138-147. Long runs 9:37/mi
  (8.24 mi) and 9:57/mi (9.05 mi, "felt amazing").
- `scripts/race_equivalency.py half 1:47:30` (an assumed ~8:12/mi half, not a
  measured result) gives 5K ~23:22, strength 8:23/mi, easy 10:03-11:03/mi.
- The framework says to re-derive paces when fitness is re-measured, not
  inferred from workouts.
- Week 12 is a planned down week (about 42 mi).

## Preference

Operator accepted the recommendation to measure rather than adjust paces from
two workouts.

## Risk

Moderate. A maximal 5K during the return-to-run ramp adds intensity load and
shin exposure; Thursday threshold follows two days later. Mitigation: down week,
even pacing with a controlled first mile (~7:45-7:50/mi, between the 24:35 and
~23:22 estimates), and a Thursday escape hatch (cut 4 mi threshold to 3 mi if
legs are heavy). Any logged shin warning sign converts Tuesday back to easy
running per the framework's adjustment rules.

## Adaptation

- `plans/2026-half-marathon/weeks/week_2026-10-19.md`: Tuesday becomes 2 mi
  warmup + strides, 5K time trial, 2.9 mi cooldown; Thursday Notes gain the
  cut-to-3-mi option.
- Weeks 10-11 keep the current table; the prescribed SOS paces are the slow end,
  not a target. Note effort on the early reps.

## Final Call

Approved 2026-10-05. After the trial: if 23:30 or faster, re-derive the pace
guide and rewrite weeks 13-18 Run cells in one pass (with a decision record);
if slower than 23:30, keep the current table.
