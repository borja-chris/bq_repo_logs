# Heat-Adjusted Pace Enrichment - 2026-07-19

## Decision

Enrich each imported activity with a heat-adjusted pace estimate derived from
Open-Meteo start-time temperature + dew point (Mark Hadley chart), and surface a
heat-neutral equivalent pace in managed notes so it flows to the weekly log and
README with no manual note.

## Facts

- Enrichment previously fetched only `temperature_2m`; dew point was not captured.
- Open-Meteo archive returns `dew_point_2m` and `apparent_temperature` in the same call.
- Chart: `temp_f + dew_point_f = sum` -> pace slowdown %, midpoint of band.
- Note rendered only when `sum >= 111`; fields stored regardless.
- Spec: `docs/superpowers/specs/2026-07-19-heat-adjusted-pace-enrichment-design.md`.

## Scope

- New pure module `scripts/heat_adjust.py`; fetch + storage in
  `ingest_coros_fit_weather.py`; note rendering via `Activity.heat_note` and
  `weekly_entries.build_managed_notes_lines`.
- Backfilled all existing `data/processed/*.jsonl` (heat fields now present on every
  activity with a start location, back to the 2023 bulk import).
- Re-rendered the current-week log (`logs/weekly/week_2026-07-13.md`), which now shows
  heat notes for the 7/14 and 7/17 runs.

## Historical logs (done in a follow-up pass)

- All 8 pre-existing historical weekly logs (2026-05-11 .. 2026-07-06) were re-rendered
  after the initial decision, migrating them from the legacy format (`## Auto Summary` /
  `## Manual Notes`) to the current format and adding heat notes (40 total). Manual and
  subjective prose was preserved (sourced from the untouched daily logs and the renamed
  weekly manual-notes section; verified no prose fragment was lost).
- Side effect, verified correct: three weeks' `Actual mileage so far` totals changed
  (05-18 9.02->20.77, 06-15 38.47->46.84, 06-22 22.95->30.03). The old logs were stale
  mid-week snapshots; each new total exactly equals the sum of that week's processed
  activities, so this is a correction to complete, accurate data, not a miscount.

## Risk / Adaptation

- Estimate, not measurement: midpoint of band, chart-based. Treated as context, not a target.
- Missing dew point is non-fatal: fields blank, import unaffected.

## Final Call

Adopted. Dew point drives the chart; apparent temperature stored as a bonus felt-like number.
