# Heat-Adjusted Pace Enrichment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Derive a heat-adjusted pace estimate per activity from Open-Meteo temperature + dew point, and surface a heat-neutral equivalent pace in the managed notes that flows to the weekly log and README automatically.

**Architecture:** One new pure module (`scripts/heat_adjust.py`) holds all chart math with no I/O. The weather enrichment step fetches dew point + apparent temperature alongside temperature and stores raw + derived heat fields in the processed JSONL. The `Activity` dataclass renders a heat note from those fields plus the run's own pace, and `build_managed_notes_lines` appends it after the weather note. Existing processed batches are backfilled through the existing re-enrichment path.

**Tech Stack:** Python 3 stdlib only (`unittest`, `urllib`, `dataclasses`). No new dependencies. Open-Meteo archive API. Tests are stdlib `unittest`, run with `python tests/test_<name>.py`.

## Global Constraints

- Python stdlib only — no new third-party dependencies.
- Processed JSONL is written by `summarize.write_jsonl` with `json.dumps(row, sort_keys=True)`; new row keys slot in alphabetically automatically — do NOT maintain a fieldname list.
- All row field values are stored as **strings** (existing convention, e.g. `weather_temp_f` is `"87.4"`).
- Weather/heat enrichment is **optional and non-fatal**: missing data leaves new fields blank and never aborts an import.
- Spec: `docs/superpowers/specs/2026-07-19-heat-adjusted-pace-enrichment-design.md`.
- Repo rules (AGENTS.md): never `git add -A` — stage explicit paths only; commit + push per phase.
- The chart: `temp_f + dew_point_f = sum` → pace slowdown %, **midpoint of band**. Render note only when `sum >= 111`.
- Heat-neutral equivalent: `neutral_sec = round(actual_sec_per_mi / (1 + fraction))`.

### Chart bands (sum → midpoint fraction, label)

| Sum range | Midpoint % | fraction | Label                 |
| --------- | ---------- | -------- | --------------------- |
| ≤100      | 0%         | 0.0      | none                  |
| 101–110   | 0.25%      | 0.0025   | light                 |
| 111–120   | 0.75%      | 0.0075   | light                 |
| 121–130   | 1.5%       | 0.015    | moderate              |
| 131–140   | 2.5%       | 0.025    | moderate              |
| 141–150   | 3.75%      | 0.0375   | heavy                 |
| 151–160   | 5.25%      | 0.0525   | heavy                 |
| 161–170   | 7.0%       | 0.07     | heavy                 |
| 171–180   | 9.0%       | 0.09     | severe                |
| >180      | —          | —        | hard-not-recommended  |

---

## File Structure

- **Create** `scripts/heat_adjust.py` — pure chart math (Task 1).
- **Create** `tests/test_heat_adjust.py` — unit tests for the pure module (Task 1).
- **Modify** `scripts/ingest_coros_fit_weather.py` — fetch dew point + apparent temp; store raw + derived heat fields; add `Activity.heat_note` (Task 2).
- **Modify** `scripts/weekly_entries.py` — append heat note in `build_managed_notes_lines` (Task 2).
- **Modify** `tests/test_ingest_coros_fit.py` — cover new fields, `heat_note`, and note rendering (Task 2).
- **Backfill** `data/processed/*.jsonl` + re-render `logs/weekly/*.md`, `logs/daily/**`, `README.md` (Task 3).
- **Create** `decisions/2026-07-19_heat_adjusted_pace_enrichment.md` (Task 3).
- **Modify** `retros/weekly/week_2026-07-19_work_session.md` — close the action item (Task 3).

---

## Task 1: Pure heat-adjust module

**Files:**
- Create: `scripts/heat_adjust.py`
- Test: `tests/test_heat_adjust.py`

**Interfaces:**
- Consumes: nothing (pure stdlib).
- Produces, for Task 2:
  - `heat_load_sum(temp_f: float, dew_point_f: float) -> int`
  - `pace_adjust_fraction(load_sum: int) -> float`
  - `heat_band_label(load_sum: int) -> str`
  - `heat_neutral_pace_seconds(actual_sec_per_mi: int, fraction: float) -> int`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_heat_adjust.py`:

```python
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


def load_module():
    repo_root = Path(__file__).resolve().parents[1]
    scripts_dir = repo_root / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    module_path = scripts_dir / "heat_adjust.py"
    spec = importlib.util.spec_from_file_location("heat_adjust_under_test", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load heat_adjust.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


h = load_module()


class HeatAdjustTest(unittest.TestCase):
    def test_heat_load_sum_rounds_to_int(self) -> None:
        self.assertEqual(h.heat_load_sum(92.0, 71.0), 163)
        self.assertEqual(h.heat_load_sum(87.4, 60.6), 148)

    def test_pace_adjust_fraction_band_boundaries(self) -> None:
        self.assertEqual(h.pace_adjust_fraction(100), 0.0)
        self.assertEqual(h.pace_adjust_fraction(101), 0.0025)
        self.assertEqual(h.pace_adjust_fraction(110), 0.0025)
        self.assertEqual(h.pace_adjust_fraction(111), 0.0075)
        self.assertEqual(h.pace_adjust_fraction(163), 0.07)
        self.assertEqual(h.pace_adjust_fraction(180), 0.09)
        self.assertEqual(h.pace_adjust_fraction(181), 0.09)

    def test_heat_band_label(self) -> None:
        self.assertEqual(h.heat_band_label(100), "none")
        self.assertEqual(h.heat_band_label(115), "light")
        self.assertEqual(h.heat_band_label(135), "moderate")
        self.assertEqual(h.heat_band_label(163), "heavy")
        self.assertEqual(h.heat_band_label(175), "severe")
        self.assertEqual(h.heat_band_label(181), "hard-not-recommended")

    def test_heat_neutral_pace_worked_example(self) -> None:
        # ran 9:20/mi = 560 s/mi, sum 163 -> 7% -> 560 / 1.07 = 523 s = 8:43/mi
        fraction = h.pace_adjust_fraction(163)
        self.assertEqual(h.heat_neutral_pace_seconds(560, fraction), 523)

    def test_heat_neutral_pace_zero_fraction_is_identity(self) -> None:
        self.assertEqual(h.heat_neutral_pace_seconds(560, 0.0), 560)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python tests/test_heat_adjust.py`
Expected: FAIL — `Unable to load heat_adjust.py` / `ModuleNotFoundError` (file does not exist yet).

- [ ] **Step 3: Write the module**

Create `scripts/heat_adjust.py`:

```python
from __future__ import annotations

# Mark Hadley temperature + dew point pace-adjustment chart.
# sum = temp_f + dew_point_f -> pace slowdown fraction (midpoint of band).
# Each entry: (inclusive upper bound of sum, fraction, label).
_BANDS: list[tuple[int, float, str]] = [
    (100, 0.0, "none"),
    (110, 0.0025, "light"),
    (120, 0.0075, "light"),
    (130, 0.015, "moderate"),
    (140, 0.025, "moderate"),
    (150, 0.0375, "heavy"),
    (160, 0.0525, "heavy"),
    (170, 0.07, "heavy"),
    (180, 0.09, "severe"),
]
_ABOVE_MAX = (0.09, "hard-not-recommended")


def heat_load_sum(temp_f: float, dew_point_f: float) -> int:
    return round(temp_f + dew_point_f)


def _band(load_sum: int) -> tuple[float, str]:
    for upper, fraction, label in _BANDS:
        if load_sum <= upper:
            return fraction, label
    return _ABOVE_MAX


def pace_adjust_fraction(load_sum: int) -> float:
    return _band(load_sum)[0]


def heat_band_label(load_sum: int) -> str:
    return _band(load_sum)[1]


def heat_neutral_pace_seconds(actual_sec_per_mi: int, fraction: float) -> int:
    return round(actual_sec_per_mi / (1 + fraction))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python tests/test_heat_adjust.py`
Expected: PASS (`Ran 5 tests ... OK`).

- [ ] **Step 5: Commit**

```bash
git add scripts/heat_adjust.py tests/test_heat_adjust.py
git commit -m "Add pure heat-adjust chart module (temp+dew-point -> pace)"
```

---

## Task 2: Wire enrichment, Activity.heat_note, and managed notes

**Files:**
- Modify: `scripts/ingest_coros_fit_weather.py` (fetch params `:116-123`; `weather_update_from_hourly` `:132-154`; `Activity` dataclass `:32-90`)
- Modify: `scripts/weekly_entries.py` (`build_managed_notes_lines` `:163-167`)
- Test: `tests/test_ingest_coros_fit.py`

**Interfaces:**
- Consumes from Task 1: `heat_adjust.heat_load_sum`, `pace_adjust_fraction`, `heat_band_label`, `heat_neutral_pace_seconds`.
- Produces:
  - New JSONL row keys (string values): `weather_dew_point_c`, `weather_dew_point_f`, `weather_apparent_temp_c`, `weather_apparent_temp_f`, `heat_load_sum`, `heat_pace_adjust_pct`.
  - `Activity.heat_note` property → managed-note line or `""`.
  - `build_managed_notes_lines` appends the heat note after the weather note.

- [ ] **Step 1: Write the failing tests**

Add these methods inside the existing test class in `tests/test_ingest_coros_fit.py` (the class that already holds `test_weather_update_from_hourly_matches_hour_and_reports_missing`). They use the same `m.weather` access pattern already in that file:

```python
    def test_weather_update_from_hourly_populates_heat_fields(self) -> None:
        activity = m.weather.Activity(
            row={
                "start_lat": "40.81",
                "start_lon": "-73.95",
                "distance_mi": "5.76",
                "duration_s": "3226",
            },
            local_start=datetime(2026, 7, 14, 8, 0),
            local_date=date(2026, 7, 14),
            timezone_name="America/New_York",
        )
        hourly = {
            "time": ["2026-07-14T08:00"],
            "temperature_2m": [33.3],
            "dew_point_2m": [21.7],
            "apparent_temperature": [39.0],
        }
        update = m.weather.weather_update_from_hourly(activity, hourly)
        self.assertEqual(update["weather_temp_f"], "91.9")
        self.assertEqual(update["weather_dew_point_f"], "71.1")
        self.assertEqual(update["weather_apparent_temp_f"], "102.2")
        # 92 + 71 = 163 -> heavy -> 7%
        self.assertEqual(update["heat_load_sum"], "163")
        self.assertEqual(update["heat_pace_adjust_pct"], "7.0")

    def test_heat_note_renders_above_threshold(self) -> None:
        activity = m.weather.Activity(
            row={
                "distance_mi": "5.76",
                "duration_s": "3226",  # 560 s/mi = 9:20/mi
                "weather_temp_f": "91.9",
                "weather_dew_point_f": "71.1",
                "heat_load_sum": "163",
                "heat_pace_adjust_pct": "7.0",
            },
            local_start=datetime(2026, 7, 14, 8, 0),
            local_date=date(2026, 7, 14),
            timezone_name="America/New_York",
        )
        note = activity.heat_note
        self.assertIn("163", note)
        self.assertIn("heavy", note)
        self.assertIn("8:43/mi", note)
        self.assertIn("9:20/mi", note)

    def test_heat_note_empty_below_threshold_or_missing(self) -> None:
        low = m.weather.Activity(
            row={"distance_mi": "5.0", "duration_s": "3000", "heat_load_sum": "90"},
            local_start=datetime(2026, 5, 1, 8, 0),
            local_date=date(2026, 5, 1),
            timezone_name="America/New_York",
        )
        self.assertEqual(low.heat_note, "")
        absent = m.weather.Activity(
            row={"distance_mi": "5.0", "duration_s": "3000"},
            local_start=datetime(2026, 5, 1, 8, 0),
            local_date=date(2026, 5, 1),
            timezone_name="America/New_York",
        )
        self.assertEqual(absent.heat_note, "")

    def test_build_managed_notes_includes_heat_note_after_weather(self) -> None:
        activity = m.weather.Activity(
            row={
                "source_relpath": "data/x.fit",
                "distance_mi": "5.76",
                "duration_s": "3226",
                "sport": "running",
                "start_time": "2026-07-14T08:00:00-04:00",
                "avg_hr": "150",
                "max_hr": "165",
                "ascent_m": "40",
                "weather_temp_f": "91.9",
                "weather_dew_point_f": "71.1",
                "weather_observation_time": "2026-07-14T08:00",
                "weather_source": "open-meteo",
                "heat_load_sum": "163",
                "heat_pace_adjust_pct": "7.0",
            },
            local_start=datetime(2026, 7, 14, 8, 0),
            local_date=date(2026, 7, 14),
            timezone_name="America/New_York",
        )
        lines = m.build_managed_notes_lines(activity)
        weather_idx = next(i for i, ln in enumerate(lines) if "Weather at start" in ln)
        heat_idx = next(i for i, ln in enumerate(lines) if "Heat:" in ln)
        self.assertGreater(heat_idx, weather_idx)
```

Note: `ingest_coros_fit.py` does `from weekly_entries import (build_managed_notes_lines, ...)`, so the harness exposes it as bare `m.build_managed_notes_lines` (weather is `import ... as weather`, hence `m.weather.Activity`). Both access paths are confirmed against the existing test file.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python tests/test_ingest_coros_fit.py`
Expected: FAIL — `KeyError`/`AttributeError` on `weather_dew_point_f`, `heat_note`, or `heat_load_sum` (fields/property not implemented yet).

- [ ] **Step 3: Add the fetch params and heat imports**

In `scripts/ingest_coros_fit_weather.py`, add the import near the top (after `import ingest_coros_fit_batch as batch`):

```python
import heat_adjust
```

Change the `hourly` param in `fetch_open_meteo_archive` (currently `"hourly": "temperature_2m"`) to:

```python
        "hourly": "temperature_2m,dew_point_2m,apparent_temperature",
```

- [ ] **Step 4: Populate heat fields in `weather_update_from_hourly`**

Replace the success `return` block at the end of `weather_update_from_hourly` (the dict starting `"weather_temp_c": ...`) with logic that also reads dew point + apparent temp at the same `index` and derives heat fields. Full replacement of the function body from `temperature_c = temperatures_c[index]` onward:

```python
    temperature_c = temperatures_c[index]
    if temperature_c in (None, ""):
        return {"weather_fetch_error": f"Open-Meteo blank temperature for {target_time}"}
    temperature_c_float = float(temperature_c)
    temperature_f = (temperature_c_float * 9 / 5) + 32

    update = {
        "weather_temp_c": f"{temperature_c_float:.1f}",
        "weather_temp_f": f"{temperature_f:.1f}",
        "weather_source": "open-meteo",
        "weather_observation_time": target_time,
        "weather_fetch_error": "",
        "weather_dew_point_c": "",
        "weather_dew_point_f": "",
        "weather_apparent_temp_c": "",
        "weather_apparent_temp_f": "",
        "heat_load_sum": "",
        "heat_pace_adjust_pct": "",
    }

    dew_points_c = hourly.get("dew_point_2m", [])
    if isinstance(dew_points_c, list) and index < len(dew_points_c):
        dew_c = dew_points_c[index]
        if dew_c not in (None, ""):
            dew_c_float = float(dew_c)
            dew_f = (dew_c_float * 9 / 5) + 32
            update["weather_dew_point_c"] = f"{dew_c_float:.1f}"
            update["weather_dew_point_f"] = f"{dew_f:.1f}"
            load_sum = heat_adjust.heat_load_sum(temperature_f, dew_f)
            update["heat_load_sum"] = str(load_sum)
            update["heat_pace_adjust_pct"] = f"{heat_adjust.pace_adjust_fraction(load_sum) * 100:.1f}"

    apparent_c = hourly.get("apparent_temperature", [])
    if isinstance(apparent_c, list) and index < len(apparent_c):
        app_c = apparent_c[index]
        if app_c not in (None, ""):
            app_c_float = float(app_c)
            update["weather_apparent_temp_c"] = f"{app_c_float:.1f}"
            update["weather_apparent_temp_f"] = f"{(app_c_float * 9 / 5) + 32:.1f}"

    return update
```

- [ ] **Step 5: Add the `heat_note` property to `Activity`**

In `scripts/ingest_coros_fit_weather.py`, add this property to the `Activity` dataclass, right after the existing `weather_note` property:

```python
    @property
    def heat_note(self) -> str:
        load_sum_raw = self.row.get("heat_load_sum", "").strip()
        temp_f = self.row.get("weather_temp_f", "").strip()
        dew_f = self.row.get("weather_dew_point_f", "").strip()
        if not load_sum_raw or not temp_f or not dew_f:
            return ""
        load_sum = int(load_sum_raw)
        if load_sum < 111:
            return ""
        if self.distance_mi <= 0 or self.duration_s <= 0:
            return ""
        actual_sec = round(self.duration_s / self.distance_mi)
        fraction = heat_adjust.pace_adjust_fraction(load_sum)
        neutral_sec = heat_adjust.heat_neutral_pace_seconds(actual_sec, fraction)
        label = heat_adjust.heat_band_label(load_sum)
        pct = self.row.get("heat_pace_adjust_pct", "").strip() or f"{fraction * 100:.1f}"

        def fmt(seconds: int) -> str:
            minutes, secs = divmod(seconds, 60)
            return f"{minutes}:{secs:02d}/mi"

        return (
            f"- Heat: {round(float(temp_f))}°F + {round(float(dew_f))}°F dew = {load_sum} "
            f"({label}). Heat-neutral equivalent ~{fmt(neutral_sec)} "
            f"(ran {fmt(actual_sec)}, ~+{pct}%)."
        )
```

- [ ] **Step 6: Append the heat note in `build_managed_notes_lines`**

In `scripts/weekly_entries.py`, update `build_managed_notes_lines`:

```python
def build_managed_notes_lines(activity: Any) -> list[str]:
    managed = [activity.import_note, activity.fit_note]
    if activity.weather_note:
        managed.append(activity.weather_note)
    if activity.heat_note:
        managed.append(activity.heat_note)
    return [f"  {line}" for line in managed]
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `python tests/test_ingest_coros_fit.py && python tests/test_heat_adjust.py`
Expected: both PASS (`OK`).

- [ ] **Step 8: Commit**

```bash
git add scripts/ingest_coros_fit_weather.py scripts/weekly_entries.py tests/test_ingest_coros_fit.py
git commit -m "Fetch dew point + apparent temp; render heat-neutral pace note"
```

---

## Task 3: Backfill, decision record, close retro

**Files:**
- Modify: `data/processed/*.jsonl` (backfill new fields)
- Modify: `logs/weekly/*.md`, `logs/daily/**`, `README.md` (re-render)
- Create: `decisions/2026-07-19_heat_adjusted_pace_enrichment.md`
- Modify: `retros/weekly/week_2026-07-19_work_session.md`

**Interfaces:**
- Consumes: Task 2's enrichment (`re_enrich_processed_batch_weather`) and note rendering.
- Produces: no code; data + docs only.

- [ ] **Step 1: Dry-run backfill on one recent batch and inspect**

Re-enrich the 2026-07-19 batch (contains the 87°F run) in-process and inspect the new fields before touching everything:

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from datetime import date
import ingest_coros_fit_weather as w
path, rows, acts = w.re_enrich_processed_batch_weather(date(2026,7,19), timeout_s=30)
for r in rows:
    print(r['start_time'], r.get('weather_temp_f'), r.get('weather_dew_point_f'), r.get('heat_load_sum'), r.get('heat_pace_adjust_pct'))
"
```
Expected: each row prints a temp, a dew point, a heat_load_sum, and a pct (non-blank for hot runs). If blank, stop and diagnose (network, missing dew point) before proceeding — do NOT commit partial data.

- [ ] **Step 2: Backfill all processed batches**

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from datetime import date
from pathlib import Path
import ingest_coros_fit_weather as w
for p in sorted(Path('data/processed').glob('coros_export_*_summary.jsonl')):
    d = date.fromisoformat(p.stem.removeprefix('coros_export_').removesuffix('_summary'))
    w.re_enrich_processed_batch_weather(d, timeout_s=30)
    print('backfilled', p.name)
"
```
Expected: one `backfilled ...` line per batch, no traceback.

- [ ] **Step 3: Re-render logs and README via the sync path**

Run the canonical sync (updates weekly logs + README from processed data without importing new FIT files):

```bash
.venv/bin/python scripts/ingest_coros_fit.py --sync-only
```
Expected: exits 0. `git diff --stat` shows changes under `logs/` and `README.md` (heat notes now present on hot days). Spot-check the 7/14 entry:

```bash
git diff -- logs/weekly | grep -A1 -B1 "Heat:" | head -20
```
Expected: a `- Heat: ... Heat-neutral equivalent ...` line on the 7/14 daily entry.

- [ ] **Step 4: Verify markdown links / tests still pass**

```bash
python tests/test_heat_adjust.py && python tests/test_ingest_coros_fit.py && python scripts/check_markdown_links.py
```
Expected: tests `OK`; link check passes.

- [ ] **Step 5: Write the decision record**

Create `decisions/2026-07-19_heat_adjusted_pace_enrichment.md`:

```markdown
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
- Backfilled all existing `data/processed/*.jsonl` and re-rendered logs + README.

## Risk / Adaptation

- Estimate, not measurement: midpoint of band, chart-based. Treated as context, not a target.
- Missing dew point is non-fatal: fields blank, import unaffected.

## Final Call

Adopted. Dew point drives the chart; apparent temperature stored as a bonus felt-like number.
```

- [ ] **Step 6: Close the retro action item**

In `retros/weekly/week_2026-07-19_work_session.md`, update the `## Action Item` block: change `- Status: Open — not started. Threshold value deferred to a future session.` to:

```markdown
- Status: Done — implemented 2026-07-19. Uses the Mark Hadley temp+dew-point chart (render threshold sum >= 111). See `decisions/2026-07-19_heat_adjusted_pace_enrichment.md` and `docs/superpowers/specs/2026-07-19-heat-adjusted-pace-enrichment-design.md`.
```

- [ ] **Step 7: Commit (data + docs)**

```bash
git add data/processed decisions/2026-07-19_heat_adjusted_pace_enrichment.md retros/weekly/week_2026-07-19_work_session.md README.md logs
git commit -m "Backfill heat-adjusted pace; add decision record; close retro item"
```

---

## Self-Review

- **Spec coverage:** pure module (Task 1) ✓; fetch dew point + apparent temp (Task 2 Step 3–4) ✓; stored fields `weather_dew_point_c/f`, `weather_apparent_temp_c/f`, `heat_load_sum`, `heat_pace_adjust_pct` (Task 2 Step 4) ✓; `Activity.heat_note` with ≥111 threshold + heat-neutral pace (Task 2 Step 5) ✓; managed-notes surfacing (Task 2 Step 6) ✓; backfill (Task 3 Step 1–3) ✓; decision record + retro close (Task 3 Step 5–6) ✓; tests for boundaries, worked example, note rendering ✓.
- **Placeholder scan:** no TBD/TODO; all code shown in full.
- **Type consistency:** `heat_load_sum`/`pace_adjust_fraction`/`heat_band_label`/`heat_neutral_pace_seconds` signatures match between Task 1 (produced) and Task 2 (consumed); row field names identical between Task 2 storage and `heat_note`/tests.
- **Harness access paths confirmed:** `m.weather.Activity` (imported `as weather`) and bare `m.build_managed_notes_lines` (imported `from weekly_entries import ...`), both verified against the existing test file.
