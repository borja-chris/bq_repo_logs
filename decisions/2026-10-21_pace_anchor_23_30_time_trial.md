# Decision Gate - 2026-10-21

## Decision

Re-anchor the 2026 half-marathon pace guide on the week 12 5K time trial
(2026-10-20, track): **23:30**, replacing the ~24:35 split-repaired anchor from
`decisions/2026-08-07_pace_anchor_recalibration.md`. Re-derive the SOS paces in
`plans/2026-half-marathon/03_framework.md` and rewrite the SOS Run cells in weeks
14-18 in one pass, as pre-authorized by `decisions/2026-10-05_week12_5k_time_trial.md`
("if 23:30 or faster, re-derive the pace guide and rewrite weeks 13-18 Run cells").

## Facts

- Trial laps (FIT 481183741572579529): 1.02 mi 8:02 (7:52/mi, HR 156/180),
  1.03 mi 7:48 (7:33/mi, HR 174/181), 1.03 mi 7:21 (7:07/mi, HR 181/190).
  The three laps sum to 23:11; hard running continued ~20-25 s into the next
  lap. GPS reads long on a track, so the runner's 23:30 is taken as the result.
- Negative split, first mile on plan (target ~7:45-7:50/mi), last mile 7:07/mi.
  Run 48 h after Sunday's 10K; the 10-05 decision called the result a floor.
- `scripts/race_equivalency.py 5k 23:30`: HM 1:48:06 (8:15/mi); LT (10K-HM)
  7:53-8:15/mi; VO2max (3K-5K) 7:16-7:34/mi; marathon 8:36/mi.
- Old anchor 24:35: HM 1:53:05 (8:38/mi). Shift is 21-23 s/mi across SOS paces.
- Subjective: felt good; race-day shoes abraded the Achilles skin despite KT tape.

## Preference

Training paces describe the runner as measured now. The measurement is real
(even, track, negative split), so SOS paces move to it. Easy, recovery and long
run bands are effort-governed and already match logged easy runs at HR 138-147;
they stay as-is.

## Risk

- Faster SOS paces in peak weeks (14-16) raise load just as mileage peaks, ~10
  weeks after the 2026-08-12 shin splint onset. Mitigation: easy/long bands
  unchanged; prescribed SOS paces are the slow end, not a target; existing
  adjustment rules (cut reps before cutting the long run) still apply.
- Achilles skin abrasion from race shoes. Skin, not tendon, per the runner.
  Mitigation: race shoes off until healed; any tendon pain triggers the
  framework's Achilles adjustment rule.
- Not changed: goals (sub-1:50 primary, sub-1:45 stretch), race-day pacing
  (week 18 Sunday), the ~9:15/mi steady-finish cap. Race pacing gets its own
  decision closer to race week.

## Adaptation

| Run type | Old (24:35) | New (23:30) |
| --- | --- | --- |
| HMP | 8:33-8:43/mi | 8:10-8:20/mi |
| Threshold | 8:15-8:38/mi | 7:53-8:15/mi |
| Strength reps | 8:28-8:38/mi | 8:05-8:15/mi |
| Speed reps | 7:36-8:05/mi | 7:15-7:44/mi |
| Recovery / easy / long | unchanged | unchanged |

- `plans/2026-half-marathon/03_framework.md`: anchor line, Pace Guide prose,
  table and rep-time tables re-derived (rep times computed from pace × distance).
- `sources/00_canonical_context.md`: measured anchor line.
- Weeks 14-18 SOS Run cells updated. Week 12 Thursday threshold stays at
  8:15-8:38/mi (down week, legs 48 h post-trial). Week 13 is all easy; no change.

## Final Call

Approved 2026-10-21 by the runner ("Let's go with 23:30. Let it rip").
Follow-up (owner: Claude): after weeks 14-15 SOS sessions are imported, check
reps against the new ranges; if two consecutive SOS days land slower than the
slow end with HR at or above trial-race levels, revert SOS paces halfway toward
the old table and record it here. Success condition: weeks 14-15 SOS reps land
inside the new ranges.
