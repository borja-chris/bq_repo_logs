# Decision Gate - 2026-08-07

## Decision

Re-anchor the 2026 half-marathon block's Pace Guide on measured 5K fitness
rather than on goal pace, and restate the 2026-12-06 target as sub-1:50 primary
with a sub-1:45 stretch, holding sub-1:33 as a later arc checkpoint.

## Facts

- Two measured 5K efforts exist. 2026-06-06: 3.12 mi, 25:32, 8:11/mi, avg HR
  178 / max 196, logged as "5K race effort". 2026-07-11 parkrun: 3.06 mi, 24:53,
  8:08/mi, avg HR 168 / max 188.
- Mile splits, from the source FIT files. 07-11: 8:43 (HR 154) / 8:03 (172) /
  7:39 (179), final 0.06 at 7:21. 06-06: 8:19 (165) / 8:26 (179) / 7:58 (190),
  final 0.12 at 6:40.
- The 07-11 closing mile was 19 s/mi faster than 06-06's at 11 bpm lower HR, in
  a 69.6°F dew point versus 59.0°F.
- The runner confirms 07-11 was not all-out and that the first mile was held back.
- The prior table was anchored on a goal HMP of 7:05/mi, implying a ~20:13 5K.
  No logged effort is consistent with that; all are consistent with ~25:00.
- Logged easy runs sit at 10:24-11:17/mi, inside the recalibrated easy band and
  well outside the prior 8:15-8:50/mi band.
- Block weeks have run under target: 23.18 vs 33-36, 25.51 vs 34-37, 27.74 vs
  30-34.
- `decisions/2026-07-11_concrete_pace_guide.md` pre-authorizes this: "if logged
  SOS efforts consistently land outside the ranges, update the anchor's fitness
  estimate rather than forcing the paces."

## Preference

Training paces that describe the runner who exists now, so easy days are
genuinely easy and SOS days are attemptable. Goal remains ambitious; the table
stops being the place where ambition is expressed.

## Risk

The 24:35 anchor is inference, not a race: it repairs 07-11's held-back first
mile to that run's own second-mile pace and normalizes GPS distance to a true
5K. It may understate fitness, since the runner finished 11 bpm below June's
max. Mitigation: the table is marked provisional, and an evenly-paced 5K or 10K
time trial in weeks 3-4 replaces the inference with a measurement.

Second risk: restating 1:33 as 1:50 could read as lowering the ceiling.
Mitigation: 1:33 is retained explicitly as an arc checkpoint, and mileage
targets are not identity markers.

## Adaptation

Bands derived via `scripts/race_equivalency.py` (Hansons offsets, Riegel
k=1.06). Rep-time tables key to the same rep distances as the Rep Recovery
Guide; recovery-jog times re-derived from the new recovery pace. Method change:
the table is now anchored on measured fitness and re-derived when fitness is
re-measured, rather than anchored on goal pace and re-derived when the goal
moves.

## Final Call

Adopt the recalibrated Pace Guide. Hold week 2 at ~31 miles with one SOS day.
Cut week 1 Wednesday to 4-5 easy. Re-derive the table after the weeks 3-4 time
trial, and record that result here as a follow-up.
