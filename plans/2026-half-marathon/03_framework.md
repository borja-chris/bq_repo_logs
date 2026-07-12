# 18-Week Hanson-Inspired Half-Marathon Plan — Framework

## Purpose

Prepare for the 2026-12-06 half marathon with a sub-1:33 checkpoint target while preserving the larger 3-year BQ arc.

## Assumptions

Baseline dates, mileage targets, and framework are in [`sources/00_project_context.md`](../../sources/00_project_context.md).

Plan-specific:

- Goal pace: about 7:05/mi for sub-1:33
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

All paces are anchored on the goal half-marathon pace of ~7:05/mi (sub-1:33,
about a 1:32:53 finish). Race-effort references below are equivalents for that
fitness, not separate goals. If the goal pace changes, re-derive this table.

| Run Type | Pace | Basis |
| --- | --- | --- |
| Recovery | 8:45-9:30/mi | HMP + ~1:40-2:25; deliberately loose |
| Easy aerobic | 8:15-8:50/mi | HMP + ~1:10-1:45; conversational |
| Long run | 8:00-9:00/mi | Mostly easy; any steady finish no faster than ~7:50/mi |
| Half-marathon pace (HMP) | 7:00-7:10/mi | Goal race pace (7:05 target) |
| Threshold (~1-hr effort) | 6:50-7:00/mi | Sustained, controlled hard |
| Strength reps | 6:45-6:55/mi | HMP - 10s, toward 10K effort; controlled, not all-out |
| Speed reps | 6:15-6:35/mi | 5K-10K effort; faster for shorter reps, relaxed form |

### Speed reps — target rep times

Run the shorter reps nearer 5K effort, the longer reps nearer 10K effort.

| Rep | Target time | ~Pace |
| --- | --- | --- |
| 400m | 1:34-1:37 | 6:18-6:30/mi |
| 600m | 2:24-2:29 | 6:24-6:38/mi |
| 800m | 3:12-3:20 | 6:24-6:40/mi |
| 1000m | 4:02-4:12 | 6:30-6:45/mi |
| 1200m | 4:54-5:04 | 6:34-6:47/mi |
| 1 mile | 6:25-6:40 | 6:25-6:40/mi |

### Strength reps — target rep times (at ~6:45-6:55/mi)

| Rep | Target time |
| --- | --- |
| 1 mi | 6:45-6:55 |
| 1.5 mi | 10:07-10:22 |
| 2 mi | 13:30-13:50 |
| 3 mi | 20:15-20:45 |

## Rep Recovery Guide

Recoveries between SOS reps are not part of the workout — they are continued
movement to protect Hanson-style cumulative fatigue.

- Recovery jogs are **run, not walked or stood** (strides are the exception).
- Recovery pace is recovery/easy effort or a touch slower — roughly
  8:45-9:30/mi, conversational and deliberately loose.
- Recovery-jog mileage is **included** in each week's listed "X mi total"
  (warmup + reps + recoveries + cooldown = total).

| Rep type | Recovery jog | ~Time | Note |
| --- | --- | --- | --- |
| Speed 400m / 600m | 400m jog | 2:00-2:30 | Repeat form, not full rest |
| Speed 800m / 1000m | 400-600m jog | 2:30-3:00 | Slightly longer for the longer rep |
| Strength 1 mi | 400m jog | ~3:00 | Short on purpose |
| Strength 1.5 mi | 600m jog | ~4:00 | Short on purpose |
| Strength 2-3 mi | 800m jog | ~5:00 | Short on purpose |
| Threshold blocks (2x2, 2x3, 2x4) | 400-800m jog | 2:00-4:00 | Brief reset between efforts |
| HMP reps (3x1, 2x3, 2x4) | 400-800m jog | 2:00-4:00 | Race-rhythm simulation |
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
