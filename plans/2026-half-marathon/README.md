# 2026 Half-Marathon Plan Overview

## Race

- Goal A race: 2026-12-06 half marathon
- Block start: 2026-08-03
- Framework: Hanson-inspired half-marathon training

## Volume Frame

- Starting point: about 20 miles/week
- Extended-base target: build gradually through 2026-08-02
- Good block-entry target: about 30-35 miles/week
- Better block-entry target: about 35-40 miles/week if earned
- Expected peak: 50-55 miles/week
- Stretch peak: 58-60 miles/week only if earned

## Structure

- Preferred rhythm: phase 1 base at 5 days/week, then progress toward 6 days/week if earned
- Long runs: mostly 13-15 miles
- Main workout emphasis: threshold, stamina, and half-marathon-pace work

## Week 1 Adjustment

- Travel note: Thursday evening travel changes the normal opening-week shape
- Planning rule: move the long run to Wednesday and use Sunday as the off day
- Saturday note: replace the previously scheduled 5K fit check with a 3 mi easy shakeout
- Interpretation rule: keep the week useful and low-drama rather than trying to preserve the original race-week structure

## Plan Files

- `01_pre_block_ramp.md`: extended base into the block
- `03_framework.md`: block-level framework — purpose, weekly rhythm, pace guide, and adjustment rules that apply all cycle
- `weeks/week_YYYY-MM-DD.md`: the single source of truth for each week's day-by-day plan (operational layer)
- `BLOCK_OVERVIEW.md`: generated at-a-glance view of the whole block (weeks x days grid + arc index)

After editing any week file, run `bash scripts/ingest.sh --sync-only`. That is the complete
regeneration path: it rebuilds `BLOCK_OVERVIEW.md`, `STATUS.md`, and the root `README.md`'s
current-week block together. Running `scripts/block_overview.py` on its own leaves the other two stale.

Field mapping, which is not obvious from the rendered output: the root README's **Planned**
column is fed by the week file's **Run** cell — not its **Notes** cell, and not the weekly
log's own `- Planned:` line. The README's **Notes** column is populated only from the actual
log entry after the run, so plan-file Notes/Purpose text never reaches the README at all.
Pre-run detail (pace targets, rest-break structure) therefore belongs in the **Run** cell.

Use `03_framework.md` for block-level rules. Use the per-week files in `weeks/` as the operational layer once training is underway. Each week's file shares its date key with `logs/weekly/week_YYYY-MM-DD.md` and `retros/weekly/week_YYYY-MM-DD.md`.

## Week Index

| Week | Date | Target mileage | Primary purpose |
| --- | --- | --- | --- |
| 1 | 2026-08-03 | about 30 | enter the block smoothly while adjusting for Thursday evening travel |
| 2 | 2026-08-10 | about 31 | add light volume with one SOS day while the pace anchor is provisional |
| 3 | 2026-08-17 | about 13 | return-to-run test after shin splints; no SOS, no back-to-back running days |
| 4 | 2026-08-24 | about 18 | confirm shin durability while adding a 4th easy running day; still no SOS |
| 5 | 2026-08-31 | about 25 | extend to 5 easy running days if week 4 stayed pain-free; still no SOS |
| 6 | 2026-09-07 | about 30 | restore 6-day rhythm; reassess reintroducing SOS at the gate below |
| 7 | 2026-09-14 | about 42 | extend stamina without overreaching |
| 8 | 2026-09-21 | about 36 | hold gate two more weeks; no SOS, easy mileage only |
| 9 | 2026-09-28 | about 35 | reintroduce SOS work with a moderated mileage ramp off week 8 |
| 10 | 2026-10-05 | about 46 | build fatigue resistance |
| 11 | 2026-10-12 | about 48 | consolidate upper-40s mileage |
| 12 | 2026-10-19 | about 42 | down week before peak-specific work |
| 13 | 2026-10-26 | about 50 | start the peak phase |
| 14 | 2026-11-02 | about 52 | extend strength while holding recovery quality |
| 15 | 2026-11-09 | about 54 | peak week if decision gates are green |
| 16 | 2026-11-16 | about 48 | begin sharpening while reducing load |
| 17 | 2026-11-23 | about 40 | taper while keeping touch with pace |
| 18 | 2026-11-30 | about 28-32 before small rounding differences, including race | arrive fresh and sharp for race day |
