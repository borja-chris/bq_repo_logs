# Decision Gate - 2026-07-11

## Decision

Replace the qualitative Pace Guide in the 2026 half-marathon block framework
with concrete pace numbers anchored on the goal half-marathon pace, plus
target rep-time tables for speed and strength work.

## Facts

- The prior Pace Guide described efforts qualitatively ("about 7:05/mi",
  "roughly current 1-hour race effort", "faster than half-marathon pace").
- The goal anchor is already canonical: HMP ~7:05/mi, a sub-1:33 checkpoint
  (~1:32:53 finish), per `sources/00_project_context.md` and the framework
  Assumptions.
- The block's rep families (speed, strength, threshold, HMP, strides) and rep
  distances are already fixed in the Rep Recovery Guide.

## Preference

Runnable numbers for every run type so easy/SOS paces can be checked against a
watch, without decoupling the table from the goal. Everything is stated as a
range and tied explicitly to the ~7:05/mi anchor.

## Risk

The derived numbers below HMP (threshold, strength, speed) are inference from a
race-equivalency estimate (a 1:32-1:33 half ≈ VDOT ~49: ~5K 20:00, ~10K 41:40,
~1-hr/threshold ~6:52/mi), not measured performances. Treating them as hard
targets on a bad day risks forcing paces the Adjustment Rules would otherwise
soften. Mitigation: ranges, an explicit "equivalents, not separate goals" note,
and a stated instruction to re-derive the table if the goal pace changes.

## Adaptation

Hansons derivation rules from `archive/training_ideologies/hansons_method.md`:
strength = HMP - 10s blending to 10K effort; speed = 5K-10K effort; threshold =
sustained ~1-hr effort; easy/recovery = HMP + ~1:10-2:25. Speed and strength
rep-time tables key to the same rep distances as the Rep Recovery Guide.

## Final Call

Adopt the concrete Pace Guide in `plans/2026-half-marathon/03_framework.md` as
the single source of truth for training paces this block. Revisit if the goal
pace moves off 7:05/mi (re-derive the whole table from the new anchor) or if
logged SOS efforts consistently land outside the ranges, in which case update
the anchor's fitness estimate rather than forcing the paces.
