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

## Deferred

- Re-rendering the 8 pre-existing historical weekly logs (2026-05-11 .. 2026-07-06) is
  NOT done here. Those files are in the legacy log format (`## Auto Summary` /
  `## Manual Notes`); `sync_week` would migrate them to the current format in the same
  pass, producing large churn on system-of-record files unrelated to heat. Left as a
  separate, explicit decision. The underlying JSONL data is fully backfilled regardless,
  so any later re-render will surface the heat notes.

## Risk / Adaptation

- Estimate, not measurement: midpoint of band, chart-based. Treated as context, not a target.
- Missing dew point is non-fatal: fields blank, import unaffected.

## Final Call

Adopted. Dew point drives the chart; apparent temperature stored as a bonus felt-like number.
