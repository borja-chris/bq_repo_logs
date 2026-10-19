# Decision Gate - 2026-10-19

## Decision

Week 12 (`plans/2026-half-marathon/weeks/week_2026-10-19.md`): keep the
Tuesday 5K time trial as planned; replace Thursday's 7 mi with 4 mi
threshold by 7 mi easy. Weekly target stays about 42.

## Facts

- Sunday 2026-10-18 10K at HMP effort: 6.13 mi in 51:40 (8:26/mi), HR 166/188
  — faster than the 8:33-8:43/mi HMP reference.
- Tuesday's trial falls 48h after that session; as written, Week 12 had three
  quality days in five (Sun 10K, Tue trial, Thu threshold) in a down week.
- The trial result re-derives the pace table for Weeks 13-18.
- Week 13 (about 50) is ~27% above the prior three-week average; Week 14
  (about 52) ~26%.

## Preference

Operator prefers to run the trial on accumulated fatigue (Hansons cumulative
fatigue). Advisor recommended moving the trial to Thursday so it measures
fitness rather than residual fatigue; operator chose the compromise.

## Risk

Low. A trial on tired legs likely underestimates fitness, so derived paces
err slow — the conservative direction going into the 50/52 mi weeks after
the August shin splints. Cost: one threshold session, mostly covered by
Sunday's 10K.

## Adaptation

- Tuesday: 5K time trial unchanged. Treat the result as a floor.
- Thursday: 7 mi easy @ 10:30-11:30/mi (was 4 mi threshold).
- After the trial: re-derive paces with `scripts/race_equivalency.py`, then
  check them against Week 13-14 strength reps; if reps feel easy, adjust
  faster.
- Week 13 gate: start the 50 mi week only if Week 12 has no shin pain during
  or 48h after any run, the Achilles shoe rub stays skin-level (no tendon
  soreness), and Sunday's 11 mi long run feels normal. Otherwise repeat a
  week at about 45.

## Final Call

Option 2 applied. Regenerated via `bash scripts/ingest.sh --sync-only`.

## Follow-up

- Owner: Claude. After the Tuesday trial is imported, re-derive the pace
  table and propose Week 13-18 pace updates. Success: proposed paces
  presented to operator before Week 13 Tuesday (2026-10-27).
