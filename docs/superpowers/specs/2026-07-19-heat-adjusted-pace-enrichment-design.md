# Heat-Adjusted Pace Enrichment — Design

- Date: 2026-07-19
- Owner: Claude (Tech Lead)
- Status: Approved (brainstorming), pending implementation plan
- Closes: heat-index action item in `retros/weekly/week_2026-07-19_work_session.md`

## Problem

The 7/14 run (5.76 mi @ 92°F) was notably slower than surrounding runs. The repo
captures Open-Meteo start-time **temperature** per activity, but has no derived
heat signal, so interpreting a hot run is manual and easy to miss during import.

A key finding corrected the original retro premise: the enrichment fetch currently
requests **only `temperature_2m`** (`scripts/ingest_coros_fit_weather.py:122`).
Humidity/dew point is **not** captured today, so a felt-like adjustment cannot be
derived from stored data as-is.

## Decision

Compute a **heat-adjusted pace estimate** per activity using the Mark Hadley
**temperature + dew point** chart, and surface a **heat-neutral equivalent pace**
in the managed notes so it flows to the weekly log and README with no manual note.

This is a pace-adjustment estimate, not a binary heat flag. It directly answers
"how much did the heat cost this run?"

### The chart (temp °F + dew point °F → pace slowdown %)

| Temp + Dew Point | Pace adjustment | Band label            |
| ---------------- | --------------- | --------------------- |
| ≤100             | none            | none                  |
| 101–110          | 0–0.5%          | light                 |
| 111–120          | 0.5–1%          | light                 |
| 121–130          | 1–2%            | moderate              |
| 131–140          | 2–3%            | moderate              |
| 141–150          | 3–4.5%          | heavy                 |
| 151–160          | 4.5–6%          | heavy                 |
| 161–170          | 6–8%            | heavy                 |
| 171–180          | 8–10%           | severe                |
| >180             | not recommended | hard-not-recommended  |

**Confirmed rules:**
- **Percentage = midpoint of the band** (e.g. 161–170 → 7%).
- **Render threshold: sum ≥ 111.** Fields are always stored; the heat note is only
  rendered when sum ≥ 111 (first band with a real adjustment). Below that it is noise.

**Heat-neutral equivalent pace:** `neutral = actual_sec_per_mi / (1 + fraction)`
(a run in heat is slower than its neutral effort by `fraction`).

Source: [RunnersConnect — dew point effect](https://runnersconnect.net/dew-point-effect-running/),
[RunFit MKE — hot weather pace adjustment](https://www.runfitmke.com/blog/how-to-calculate-pace-adjustment-for-hot-weather-running).

## Data source

Open-Meteo archive API returns `dew_point_2m` and `apparent_temperature` in the
same hourly call. Add both to the fetch. **Dew point drives the chart**; apparent
temperature is stored as a bonus felt-like number for future use.

## Architecture

One new pure module plus three wiring points. Boundaries chosen so the formula is
unit-testable with zero repo/network state.

### 1. `scripts/heat_adjust.py` (new — pure, no I/O)

All chart math lives here. Pure functions, trivially testable:

- `heat_load_sum(temp_f: float, dew_point_f: float) -> int` — the sum.
- `pace_adjust_fraction(sum: int) -> float` — chart lookup, midpoint of band.
- `heat_band_label(sum: int) -> str` — `none | light | moderate | heavy | severe | hard-not-recommended`.
- `heat_neutral_pace_seconds(actual_sec_per_mi: int, fraction: float) -> int` — `round(actual / (1 + fraction))`.

Boundary rule: the module knows nothing about activities, files, or the network.
It takes numbers and returns numbers/labels.

### 2. `scripts/ingest_coros_fit_weather.py` — fetch + store

- Extend the hourly param at `:122` to `temperature_2m,dew_point_2m,apparent_temperature`.
- Extend `weather_update_from_hourly` to read `dew_point_2m` and `apparent_temperature`
  at the same hour index and return new fields:
  - `weather_dew_point_c`, `weather_dew_point_f`
  - `weather_apparent_temp_c`, `weather_apparent_temp_f`
  - `heat_load_sum` (int as string), `heat_pace_adjust_pct` (e.g. `7.0`)
- Missing/blank dew point or apparent temp is non-fatal: leave the new fields blank,
  keep temperature enrichment working (mirrors current optional-enrichment behavior).
- Derived heat fields are computed here from `weather_temp_f` + `weather_dew_point_f`
  via `heat_adjust`.

### 3. `Activity` dataclass — `heat_note` property

New `heat_note` property combines the stored heat fields with the run's own pace
(`duration_s` / `distance_mi`, already available) to render the headline line.
Returns `""` when heat fields are absent or `heat_load_sum < 111`.

Format:
```
- Heat: 92°F + 71°F dew = 163 (heavy). Heat-neutral equivalent ~8:43/mi (ran 9:20/mi, ~+7%).
```

### 4. `scripts/weekly_entries.py` — surface in notes

`build_managed_notes_lines` appends `heat_note` after `weather_note` (only when
non-empty), so it flows to weekly log daily entries and the README current-week
block automatically. This satisfies the "no manual note required" success condition.

## Data flow

```
FIT import → summarize → enrich_rows_with_weather
  → fetch temp + dew_point + apparent_temp (one Open-Meteo call per lat/lon/tz group)
  → weather_update_from_hourly stores raw + derived heat fields in JSONL row
  → sync: load_processed_activities_for_week → Activity.heat_note
  → build_managed_notes_lines → weekly log + README
```

## Backfill

Existing `data/processed/*.jsonl` predate the new fields. Backfill them through the
existing `re_enrich_processed_batch_weather` path (re-fetches from Open-Meteo archive,
which is historical and stable), then re-render affected weekly logs and README.
Backfill is a one-time operation, run and verified by the Tech Lead before commit.

## Error handling

- No dew point / apparent temp in payload → new fields blank, temperature unaffected,
  no heat note rendered. Import still succeeds.
- Network failure → existing `weather_fetch_error` path unchanged.
- `heat_load_sum < 111` → fields stored, note suppressed.
- Zero/blank distance or duration → no heat-neutral pace, note suppressed.

## Testing

- `tests/` — new unit tests for `heat_adjust.py`: band boundaries (100, 101, 110, 111,
  180, 181), midpoint values, neutral-pace back-calc, the worked example (92 + 71 = 163,
  9:20/mi → ~8:43/mi @ 7%).
- Extend `tests/test_ingest_coros_fit.py`:
  - `weather_update_from_hourly` populates the new fields from a mocked hourly payload.
  - `Activity.heat_note` renders above threshold and is empty below it / when fields absent.
  - `build_managed_notes_lines` includes the heat note after the weather note.

## Out of scope (YAGNI)

- Two-tier heat_level enum beyond the band label.
- NWS heat-index formula (superseded by the temp+dew-point chart).
- Backfilling device-recorded FIT temperature.
- Any UI beyond the existing markdown notes.

## Execution (sub-agent team)

Tech Lead (Opus) plans, reviews, integrates, commits. Sub-agents run on Sonnet
(one tier below), per the repo collaboration model.

- **Agent 1 (Sonnet):** TDD `scripts/heat_adjust.py` + unit tests. Fully isolated.
- **Agent 2 (Sonnet):** wire fetch + `Activity.heat_note` + `build_managed_notes_lines`;
  extend `test_ingest_coros_fit.py`. Depends on Agent 1's module.
- **Agent 3 (Sonnet):** backfill processed JSONL, re-render logs/README, write the
  `decisions/` record, close the retro action item.

Order: Agent 1 → Agent 2 → Agent 3. Tech Lead signs off and commits each phase before
the next (commit + push per phase, explicit paths — no `git add -A`).

## Follow-ups / records

- Add `decisions/2026-07-19_heat_adjusted_pace_enrichment.md` recording this pipeline change.
- Close the action item in `retros/weekly/week_2026-07-19_work_session.md` (Status → Done,
  reference this spec and the decision record).
