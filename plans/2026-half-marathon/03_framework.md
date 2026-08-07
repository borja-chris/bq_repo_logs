# 18-Week Hanson-Inspired Half-Marathon Plan — Framework

## Purpose

Prepare for the 2026-12-06 half marathon with a sub-1:50 primary target and a sub-1:45 stretch, preserving sub-1:33 as a checkpoint in the larger 3-year BQ arc.

## Assumptions

Baseline dates, mileage targets, and framework are in [`sources/00_canonical_context.md`](../../sources/00_canonical_context.md).

Plan-specific:

- Anchor pace: about 8:38/mi HMP, derived from measured 5K fitness (provisional — see `decisions/2026-08-07_pace_anchor_recalibration.md`)
- Weekly rhythm: 6 running days/week
- Normal off day: Wednesday
- Monday, Wednesday, and Friday are flexible recovery/easy slots when scheduling requires a swap
- Stretch peak of 58-60 miles/week is not included by default

## Weekly Rhythm

| Day | Default Purpose |
| --- | --- |
| Monday | Short recovery run after the long run |
| Tuesday | SOS 1: speed early, strength later |
| Wednesday | Off or non-running recovery |
| Thursday | SOS 2: threshold / half-marathon-pace work |
| Friday | Recovery / easy aerobic mileage |
| Saturday | Easy aerobic mileage |
| Sunday | Moderate Hanson-style long run |

## Pace Guide

All paces are anchored on **current measured fitness**, not on goal pace: a
~24:35 5K equivalency (HMP ~8:38/mi, ~1:53 half). Race-effort references below
are equivalents for that fitness, not separate goals. This anchor is provisional
pending an evenly-paced 5K/10K time trial in weeks 3-4. Re-derive this table
whenever the fitness estimate is re-measured — not when the goal changes.

| Run Type | Pace | Basis |
| --- | --- | --- |
| Recovery | 11:00-11:45/mi | Slow end of easy and slower; deliberately loose |
| Easy aerobic | 10:30-11:30/mi | Hansons easy band; matches logged easy runs (10:24-11:17/mi) |
| Long run | 9:30-11:00/mi | Mostly easy; any steady finish no faster than ~9:15/mi |
| Half-marathon pace (HMP) | 8:33-8:43/mi | Current-fitness race pace (8:38 anchor) |
| Threshold (~1-hr effort) | 8:15-8:38/mi | Sustained, controlled hard |
| Strength reps | 8:28-8:38/mi | HMP - 10s, toward 10K effort; controlled, not all-out |
| Speed reps | 7:36-8:05/mi | 5K-10K effort; faster for shorter reps, relaxed form |

### Speed reps — target rep times

Run the shorter reps nearer 5K effort, the longer reps nearer 10K effort.

| Rep | Target time | ~Pace |
| --- | --- | --- |
| 400m | 1:53-1:57 | 7:36-7:50/mi |
| 600m | 2:52-2:57 | 7:40-7:55/mi |
| 800m | 3:51-3:59 | 7:45-8:00/mi |
| 1000m | 4:52-5:01 | 7:50-8:05/mi |
| 1200m | 5:52-6:03 | 7:52-8:07/mi |
| 1 mile | 7:55-8:15 | 7:55-8:15/mi |

### Strength reps — target rep times (at ~8:28-8:38/mi)

| Rep | Target time |
| --- | --- |
| 1 mi | 8:28-8:38 |
| 1.5 mi | 12:42-12:57 |
| 2 mi | 16:56-17:16 |
| 3 mi | 25:24-25:54 |

## Rep Recovery Guide

Recoveries between SOS reps are not part of the workout — they are continued
movement to protect Hanson-style cumulative fatigue.

- Recovery jogs are **run, not walked or stood** (strides are the exception).
- Recovery pace is recovery/easy effort or a touch slower — roughly
  11:00-11:45/mi, conversational and deliberately loose.
- Recovery-jog mileage is **included** in each week's listed "X mi total"
  (warmup + reps + recoveries + cooldown = total).

| Rep type | Recovery jog | ~Time | Note |
| --- | --- | --- | --- |
| Speed 400m / 600m | 400m jog | 2:45-3:00 | Repeat form, not full rest |
| Speed 800m / 1000m | 400-600m jog | 2:45-4:25 | Slightly longer for the longer rep |
| Strength 1 mi | 400m jog | ~2:50 | Short on purpose |
| Strength 1.5 mi | 600m jog | ~4:15 | Short on purpose |
| Strength 2-3 mi | 800m jog | ~5:40 | Short on purpose |
| Threshold blocks (2x2, 2x3, 2x4) | 400-800m jog | 2:45-5:50 | Brief reset between efforts |
| HMP reps (3x1, 2x3, 2x4) | 400-800m jog | 2:45-5:50 | Race-rhythm simulation |
| Strides (6x20s) | Walk/stand to easy breathing | 45-60s | Only standing-rest case |
| Continuous / progression runs | none | — | No interval recovery by design |

Short strength/threshold/HMP recoveries are intentional: the reps are meant to
accumulate fatigue, not fully clear between efforts. If paces collapse rather
than drift, apply the Adjustment Rules below before lengthening recoveries.

## Adjustment Rules

- If easy days stop feeling easy, reduce the next SOS workout before cutting the long run.
- If SOS days degrade for more than one week, hold mileage steady or step back.
- If long runs require multi-day recovery, shorten the next long run by 2-3 miles.
- If a run must be skipped, do not repay the mileage later in the week.
- If calves, Achilles, plantar fascia, knees, hips, or hamstrings show warning signs, replace the next SOS day with easy running or rest.
- Monday, Wednesday, and Friday may be flipped when needed, but preserve the Tuesday/Thursday/Sunday workout structure unless there is a clear reason to change it.

## Weekly Files

The day-by-day plan for each week lives in one file per week under `weeks/` (`weeks/week_YYYY-MM-DD.md`). Each week's file is the single source of truth for that week and shares its date key with `logs/weekly/week_YYYY-MM-DD.md` and `retros/weekly/week_YYYY-MM-DD.md`. See `README.md` for the week index.
