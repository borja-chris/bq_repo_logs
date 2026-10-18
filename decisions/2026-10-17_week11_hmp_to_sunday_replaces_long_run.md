# Decision Gate - 2026-10-17

## Decision

Rearrange Week 11 (`plans/2026-half-marathon/weeks/week_2026-10-12.md`): the
Thursday 6 mi HMP workout moves to Sunday 2026-10-18 as a 10K at HMP effort
(about 3 mi warmup, easy cooldown) and replaces the 13 mi long run this week.
Friday is a travel-day rest; Wednesday and Thursday are easy treadmill days.

## Facts

- Mon-Wed actual: 3.02 + 7.55 + 3.15 = 13.72 mi, all indoor treadmill runs.
- Tuesday strength logged 7.55 mi against 9 planned; operator: fine, the point
  was the interval work.
- Thursday and Saturday distances are placeholders (4 mi, 7 mi) until the
  next COROS import.
- Sunday is a solo workout in Central Park (rolling hills, crowds), not a race.
- Projected week lands below the about 45 target (upper 30s to low 40s).
- Reference: Luke Humphrey, "Modifying Your Marathon Plan for a Race" - a
  short race replaces a shorter tempo, warmup and cooldown bring the day near
  its planned mileage, effort is capped, resume the plan after an easy day.
  Applies loosely: the source is a marathon plan and Sunday is not a race.

## Preference

Operator wants to keep the HMP workout this week and run it by effort.

## Risk

Moderate-low. Load moves down, so the 58-60 mpw gate is not triggered. Hills
and crowds will distort pace; the risk is overrunning the effort, so the
warmup stays truly easy and pace is informational only. Dropping the long run
costs one week of long-run stimulus.

## Adaptation

- Wednesday: 4 mi easy (completed 3.15 mi, treadmill).
- Thursday: 4 mi easy, treadmill (placeholder).
- Friday: Off, travel.
- Saturday: 7 mi easy (placeholder).
- Sunday: 10K at HMP effort, about 10-11 mi total, replaces the long run.
- Monday 2026-10-19: easy or short recovery; Tuesday resumes the plan.
- Regenerated via `bash scripts/ingest.sh --sync-only`.

## Final Call

Applied as described above. Update Thursday and Saturday after the import.

## Correction (2026-10-17)

Thursday's 4 mi and Saturday's 7 mi were placeholder distances inserted during the plan edit; the operator never set them. Both Run cells are now marked `(provisional)`, so the Plan check reports a provisional distance instead of a FLAG (Saturday ran 4.42 mi against the placeholder 7 mi).
