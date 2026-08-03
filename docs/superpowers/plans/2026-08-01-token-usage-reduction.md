# Token-Usage Reduction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.
> Spec: `docs/superpowers/specs/2026-08-01-token-usage-reduction-design.md`

**Goal:** Cut agent token usage across session startup, coaching sessions, and import
sessions by splitting the repo into a record layer (correct, rarely read) and a view
layer (compact, generated, read into context).

**Architecture:** Generalize the existing `block_overview.py` generated-view pattern:
a root `STATUS.md` digest, enriched weekly auto-summaries, one-line Managed Notes,
a slimmed JSONL record schema, and a restructured instruction load. Data flows one
way: record → view.

**Tech Stack:** Python 3.12 (stdlib only, run via `.venv/bin/python`), pytest, bash,
markdown.

## Global Constraints

- **Delegation is a HARD RULE.** The Opus Tech Lead does not implement tasks inline.
  Every task below is dispatched to a subagent at the tier marked in the Delegation
  Map. Every `Agent` call passes an explicit `model` override (enforced by the global
  PreToolUse hook `~/.claude/hooks/enforce-subagent-model.sh`, which denies
  model-less launches and gates Opus-tier spawns behind operator confirmation).
- Tier cascade: Opus lead → `model: sonnet` lane owners → `model: haiku` mechanical
  tasks. Haiku is the floor.
- Never `git add -A` or `git add .` — stage explicit file paths only; `git mv` for moves.
- Commit and push after each phase completes and verifies; report the sha before the
  next phase starts. The Tech Lead commits centrally after reviewing subagent output.
- Verbatim data reporting: numeric values copied from tool output, never retyped.
- Build any review diffs with a direct `git diff ... > file` redirect (RTK hook
  truncates diffs inside compound commands).
- Migrations write to a temp path, verify, then replace — never in-place edits.
- Manual sections of weekly logs (Manual Notes, Sleep, Soreness, Stress, Warning
  signs, Manual Weekly Notes) are NEVER modified by any script or migration.
- Full pytest suite (`.venv/bin/python -m pytest tests/ -v`) green before every commit.

## Delegation Map

| Phase | Task | Executor | Notes |
| --- | --- | --- | --- |
| 0 | 1. Quarantine pre-block JSONL | Haiku | mechanical move + README |
| 0 | 2. Restructure AGENTS.md | Sonnet | judgment: no rule lost |
| 1 | 3. Slim JSONL output schema | Sonnet (Lane 3 owner) | |
| 1 | 4. Processed-file migration script | Sonnet (Lane 3 owner) | |
| 1 | 5. Run migration + verify | Haiku (under Lane 3) | |
| 1 | 6. Merge sources 00+04, stubs | Sonnet (Lane 4 owner) | |
| 2 | 7. Enriched auto-summary | Sonnet (Lane 1 owner) | |
| 2 | 8. `status_digest.py` + STATUS.md | Sonnet (Lane 1 owner) | |
| 2 | 9. Wire digest into ingest.sh + AGENTS.md pointer | Haiku (under Lane 1) | |
| 3 | 10. Compact Managed Notes builder | Sonnet (Lane 2 owner) | |
| 3 | 11. Weekly-log Managed Notes migrator | Sonnet (Lane 2 owner) | |
| 3 | 12. Run log migration + end-to-end reconcile | Haiku (under Lane 2) | |
| 3 | 13. Decision record + workflow doc refresh | Haiku | |

Lanes 3 and 6 (Phase 1) are independent and may run in parallel. Phase 2 must
precede Phase 3 only because both touch `scripts/weekly_entries.py`.

---

## Phase 0 — Cheap wins

### Task 1: Quarantine the pre-block history JSONL

**Files:**
- Move: `data/processed/coros_export_2026-05-09_summary.jsonl`
  → `data/archive/pre_block_history/coros_export_2026-05-09_summary.jsonl`
- Create: `data/archive/pre_block_history/README.md`

This file holds 333 historical activities (2023–2026, pre-block bulk import; 345KB)
and dominates any grep over `data/processed/`. Nothing in `scripts/` reads it by
name; `reconcile_weekly_mileage.py` and weather re-enrichment operate on the
current-block week window only.

- [x] **Step 1: Verify nothing depends on the file by name or by pre-block dates**
  Run: `grep -rn "2026-05-09_summary" scripts/ tests/`
  Expected: no matches (the ingest derives processed paths from the export dir name
  of the batch being imported, not from a fixed list).
- [x] **Step 2: Move with git mv**
  ```bash
  mkdir -p data/archive/pre_block_history
  git mv data/processed/coros_export_2026-05-09_summary.jsonl data/archive/pre_block_history/
  ```
- [x] **Step 3: Write the README**
  Create `data/archive/pre_block_history/README.md`:
  ```markdown
  # Pre-block history (quarantined)

  `coros_export_2026-05-09_summary.jsonl` holds 333 activities from the
  2026-05-09 COROS bulk export (2023 through early 2026 — before the current
  block). It is out of `data/processed/` so searches over current-block records
  never sweep it in. Schema is the pre-2026-08 verbose schema; it was
  intentionally NOT migrated (audit copy).
  ```
- [x] **Step 4: Run full test suite**
  Run: `.venv/bin/python -m pytest tests/ -v`
  Expected: all pass.
- [x] **Step 5: Commit (Tech Lead, after review)**
  ```bash
  git add data/archive/pre_block_history/README.md
  git commit -m "Quarantine pre-block history JSONL out of data/processed"
  ```
  (`git mv` already staged the move.)

### Task 2: Restructure AGENTS.md — relocate prose, keep rules

**Files:**
- Modify: `AGENTS.md`
- Create: `docs/collaboration_model.md`
- Create: `docs/decision_formats.md`

Rule: content is *relocated*, never dropped. The auto-loaded file keeps: role
statement, Default Context Loading, Core Coaching Rules, Decision Gates,
Operating Discipline, Editing and Retros, plus one-line pointers.

- [x] **Step 1: Create `docs/collaboration_model.md`**
  Move the entire `## Collaboration Model` section body from `AGENTS.md` verbatim
  under a `# Collaboration Model (Tech Lead / EM)` heading, prefixed with:
  ```markdown
  # Collaboration Model (Tech Lead / EM)

  Referenced from `AGENTS.md`. Load when planning delegated work.
  ```
- [x] **Step 2: Create `docs/decision_formats.md`**
  Move the `## Major Decision Format` section body (both the 6-step format and the
  six-hat list, and the "Major decisions include" list) verbatim under:
  ```markdown
  # Major Decision Formats

  Referenced from `AGENTS.md`. Load when making or recording a major training
  decision. Templates live in `templates/six_hat_decision_template.md` and
  `templates/decision_gate_template.md`.
  ```
- [x] **Step 3: Replace the moved sections in `AGENTS.md` with pointers**
  ```markdown
  ## Major Decision Format

  For major training decisions (peak mileage, SOS changes, race-goal or framework
  changes, long-run structure, half→full switch), follow
  `docs/decision_formats.md`: Decision / Facts / Preference / Risk / Adaptation /
  Final call; six-hat review for complex calls.

  ## Collaboration Model

  Tech Lead (Claude, Opus) plans, delegates to lower-tier subagents, verifies,
  and commits centrally; the repo owner is Engineering Manager. Delegation and
  the model-tier cascade are hard rules. Full model: `docs/collaboration_model.md`.
  ```
- [x] **Step 4: Verify no rule text was lost**
  For each line removed from `AGENTS.md`, confirm it exists in one of the two new
  docs: `grep -F "<distinctive phrase>" docs/collaboration_model.md docs/decision_formats.md`
  for at least: "Nothing a", "six-hat", "Sub-agents run on a lower-cost model"
  (adjust phrases to actual text). Zero misses allowed.
- [x] **Step 5: Link check + tests**
  Run: `.venv/bin/python scripts/check_markdown_links.py && .venv/bin/python -m pytest tests/ -v`
  Expected: both pass.
- [x] **Step 6: Commit + push Phase 0 (Tech Lead)**
  ```bash
  git add AGENTS.md docs/collaboration_model.md docs/decision_formats.md
  git commit -m "Slim AGENTS.md: relocate collaboration model and decision formats to docs/"
  git push
  ```
  Report sha.

---

## Phase 1 — Record layer + instruction merge (Lanes 3 and 4, parallel)

### Task 3: Slim JSONL output schema

**Files:**
- Modify: `scripts/summarize_coros_fit.py` (add `OUTPUT_FIELDS`, `ERROR_FIELDS`,
  `slim_row()`; apply in its JSONL write path)
- Modify: `scripts/ingest_coros_fit_batch.py` (`write_processed_outputs` applies
  `slim_row` to each row before serializing)
- Modify: `scripts/ingest_coros_fit_weather.py:71-73` (`Activity.import_note`)
- Test: `tests/test_ingest_coros_fit.py` (extend)

**Interfaces:**
- Produces: `summarize_coros_fit.OUTPUT_FIELDS: list[str]`,
  `summarize_coros_fit.slim_row(row: dict[str, str]) -> dict[str, str]` —
  Task 4's migration script imports both.
- Internal `FIELDS` (parse-time row skeleton) is unchanged; slimming happens at
  write time only, so parsing/weather/heat code keeps working untouched.

- [x] **Step 1: Write failing test** — append to `tests/test_ingest_coros_fit.py`:
  ```python
  def test_slim_row_drops_redundant_fields_and_empty_errors():
      import summarize_coros_fit as s
      full = {f: "" for f in s.FIELDS}
      full.update({
          "activity_id": "123", "source_file": "123.fit", "source_sha256": "abc",
          "start_time": "2026-07-20T17:25:54-04:00", "start_time_raw": "x",
          "start_time_utc": "x", "start_time_resolution": "x",
          "start_timezone": "America/New_York", "import_batch": "tmpdir",
          "source_relpath": "/tmp/tmpdir/123.fit", "sub_sport": "",
          "weather_temp_c": "19.9", "weather_temp_f": "67.8",
          "weather_dew_point_c": "-4.4", "weather_dew_point_f": "24.1",
          "weather_apparent_temp_c": "16.4", "weather_apparent_temp_f": "61.5",
          "heat_load_sum": "92", "heat_pace_adjust_pct": "0.0",
          "parse_error": "", "weather_fetch_error": "boom",
      })
      slim = s.slim_row(full)
      for dropped in ("start_time_raw", "start_time_utc", "start_time_resolution",
                      "import_batch", "source_relpath", "sub_sport",
                      "weather_temp_c", "weather_dew_point_c",
                      "weather_apparent_temp_c"):
          assert dropped not in slim
      assert "parse_error" not in slim          # empty error omitted
      assert slim["weather_fetch_error"] == "boom"  # non-empty error kept
      assert slim["start_time"] == "2026-07-20T17:25:54-04:00"
      assert slim["weather_temp_f"] == "67.8"
      assert slim["heat_load_sum"] == "92"
  ```
- [x] **Step 2: Run it, verify it fails**
  Run: `.venv/bin/python -m pytest tests/test_ingest_coros_fit.py::test_slim_row_drops_redundant_fields_and_empty_errors -v`
  Expected: FAIL — `AttributeError: ... no attribute 'slim_row'`.
- [x] **Step 3: Implement in `scripts/summarize_coros_fit.py`** (below `FIELDS`):
  ```python
  # Written to data/processed/*.jsonl. FIELDS stays the parse-time skeleton;
  # slimming happens only at write time so parse/weather code is untouched.
  OUTPUT_FIELDS = [
      "activity_id", "source_file", "source_sha256",
      "start_time", "start_timezone", "start_lat", "start_lon",
      "sport", "distance_mi", "duration_s", "avg_hr", "max_hr", "ascent_m",
      "weather_temp_f", "weather_dew_point_f", "weather_apparent_temp_f",
      "weather_source", "weather_observation_time",
      "heat_load_sum", "heat_pace_adjust_pct",
      "parser",
  ]
  ERROR_FIELDS = ["parse_error", "weather_fetch_error"]


  def slim_row(row: dict[str, str]) -> dict[str, str]:
      out = {key: row.get(key, "") for key in OUTPUT_FIELDS}
      for key in ERROR_FIELDS:
          value = row.get(key, "").strip()
          if value:
              out[key] = value
      return out
  ```
- [x] **Step 4: Apply at every JSONL write site**
  Run: `grep -n "jsonl\|json.dumps" scripts/summarize_coros_fit.py scripts/ingest_coros_fit_batch.py scripts/ingest_coros_fit_weather.py`
  In each function that serializes rows to a processed `*_summary.jsonl`
  (`write_processed_outputs` in `ingest_coros_fit_batch.py`, the CLI writer in
  `summarize_coros_fit.py`, and the re-enrich writer in
  `ingest_coros_fit_weather.py` if it writes directly), wrap the row:
  `handle.write(json.dumps(slim_row(row), sort_keys=True) + "\n")`.
- [x] **Step 5: Fix `Activity.import_note` for slim rows** — in
  `scripts/ingest_coros_fit_weather.py` replace lines 71-73 with:
  ```python
  @property
  def import_note(self) -> str:
      # Slim schema keeps only the file name; full provenance stays in the
      # JSONL record (source_sha256) and data/coros_exports/ on disk.
      source = self.row.get("source_relpath", "").strip() or self.row.get("source_file", "")
      return f"- Imported from `{source}`."
  ```
- [x] **Step 6: Run the new test, then the full suite**
  Run: `.venv/bin/python -m pytest tests/ -v`
  Expected: new test passes; if any existing test asserts dropped keys in written
  output, update that assertion to the slim schema (it is a schema change, not a
  regression — note it in the task report).
- [x] **Step 7: Commit (Tech Lead, after review)**
  ```bash
  git add scripts/summarize_coros_fit.py scripts/ingest_coros_fit_batch.py scripts/ingest_coros_fit_weather.py tests/test_ingest_coros_fit.py
  git commit -m "Slim processed JSONL output schema (write-time filter)"
  ```

### Task 4: One-shot migration script for existing processed files

**Files:**
- Create: `scripts/migrate_processed_slim.py`
- Test: `tests/test_migrate_processed_slim.py`

**Interfaces:**
- Consumes: `summarize_coros_fit.slim_row` (Task 3).
- Produces: CLI `scripts/migrate_processed_slim.py [--processed-dir PATH]`.

- [x] **Step 1: Write failing test** — create `tests/test_migrate_processed_slim.py`:
  ```python
  import json
  import subprocess
  import sys
  from pathlib import Path

  SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "migrate_processed_slim.py"

  def test_migration_slims_rows_and_preserves_identity(tmp_path):
      row = {
          "activity_id": "1", "source_file": "1.fit", "source_sha256": "sha1",
          "source_relpath": "/tmp/x/1.fit", "import_batch": "x",
          "start_time": "2026-07-20T17:25:54-04:00", "start_time_raw": "r",
          "start_time_utc": "u", "start_time_resolution": "res",
          "start_timezone": "America/New_York", "start_lat": "40.8",
          "start_lon": "-73.9", "sport": "running", "sub_sport": "",
          "distance_mi": "5.57", "duration_s": "3586", "avg_hr": "141",
          "max_hr": "161", "ascent_m": "66", "weather_temp_c": "28.7",
          "weather_temp_f": "83.7", "weather_dew_point_f": "49.0",
          "parser": "fitdecode", "parse_error": "", "weather_fetch_error": "",
      }
      src = tmp_path / "coros_export_2026-07-23_summary.jsonl"
      src.write_text(json.dumps(row) + "\n")
      result = subprocess.run(
          [sys.executable, str(SCRIPT), "--processed-dir", str(tmp_path)],
          capture_output=True, text=True,
      )
      assert result.returncode == 0, result.stderr
      migrated = [json.loads(l) for l in src.read_text().splitlines()]
      assert len(migrated) == 1
      assert migrated[0]["source_sha256"] == "sha1"
      assert migrated[0]["distance_mi"] == "5.57"
      assert "source_relpath" not in migrated[0]
      assert "weather_temp_c" not in migrated[0]
      assert "parse_error" not in migrated[0]
  ```
- [x] **Step 2: Run it, verify it fails**
  Run: `.venv/bin/python -m pytest tests/test_migrate_processed_slim.py -v`
  Expected: FAIL (script does not exist).
- [x] **Step 3: Implement `scripts/migrate_processed_slim.py`**
  ```python
  #!/usr/bin/env python3
  """One-shot: rewrite data/processed/*_summary.jsonl to the slim output schema.

  Writes each file to a .tmp sibling, verifies row count and the source_sha256
  set match the original, then atomically replaces. Idempotent.
  """
  from __future__ import annotations

  import argparse
  import json
  import sys
  from pathlib import Path

  sys.path.insert(0, str(Path(__file__).resolve().parent))
  from summarize_coros_fit import slim_row

  REPO_ROOT = Path(__file__).resolve().parent.parent


  def migrate_file(path: Path) -> int:
      rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
      slim = [slim_row(row) for row in rows]
      if len(slim) != len(rows):
          raise SystemExit(f"{path.name}: row count changed ({len(rows)} -> {len(slim)})")
      before = {row.get("source_sha256", "") for row in rows}
      after = {row.get("source_sha256", "") for row in slim}
      if before != after:
          raise SystemExit(f"{path.name}: source_sha256 set changed")
      tmp = path.with_name(path.name + ".tmp")
      tmp.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in slim))
      tmp.replace(path)
      return len(slim)


  def main() -> None:
      parser = argparse.ArgumentParser(description=__doc__)
      parser.add_argument("--processed-dir", type=Path,
                          default=REPO_ROOT / "data" / "processed")
      args = parser.parse_args()
      files = sorted(args.processed_dir.glob("*_summary.jsonl"))
      if not files:
          raise SystemExit(f"no *_summary.jsonl files in {args.processed_dir}")
      for path in files:
          count = migrate_file(path)
          print(f"migrated {path.name}: {count} rows")


  if __name__ == "__main__":
      main()
  ```
- [x] **Step 4: Run test, verify pass; run full suite**
  Run: `.venv/bin/python -m pytest tests/test_migrate_processed_slim.py tests/ -v`
  Expected: PASS.
- [x] **Step 5: Commit (Tech Lead, after review)**
  ```bash
  git add scripts/migrate_processed_slim.py tests/test_migrate_processed_slim.py
  git commit -m "Add one-shot slim migration for processed JSONL"
  ```

### Task 5: Run the migration over real data (Haiku)

- [x] **Step 1: Record pre-migration facts**
  Run: `wc -l data/processed/*_summary.jsonl && du -sh data/processed`
  Save the output verbatim in the task report.
- [x] **Step 2: Run the migration**
  Run: `.venv/bin/python scripts/migrate_processed_slim.py`
  Expected: one `migrated <file>: N rows` line per file; N values must equal the
  pre-migration `wc -l` counts exactly.
- [x] **Step 3: Post-checks**
  Run: `wc -l data/processed/*_summary.jsonl && du -sh data/processed && .venv/bin/python scripts/reconcile_weekly_mileage.py && bash scripts/ingest.sh --sync-only && .venv/bin/python -m pytest tests/ -v`
  Expected: identical line counts, smaller size (~40-60%), reconcile clean,
  sync-only re-render succeeds (proves slim rows still drive weekly logs), tests
  pass. If sync-only rewrites weekly logs, inspect `git diff logs/` — expected:
  no changes (Managed Notes format unchanged until Phase 3).
- [x] **Step 4: Commit + push Phase 1 Lane 3 (Tech Lead)**
  ```bash
  git add data/processed
  git commit -m "Migrate processed JSONL files to slim schema"
  git push
  ```
  Report sha. (`data/processed` contains only the migrated JSONL + `.gitkeep`;
  explicit-path rule satisfied since nothing untracked lives there.)

### Task 6: Merge sources 00+04 into one canonical context file

**Files:**
- Create: `sources/00_canonical_context.md`
- Modify: `sources/00_project_context.md` (→ redirect stub)
- Modify: `sources/04_planning_rules_and_retro.md` (→ redirect stub)
- Modify: `AGENTS.md` (Default Context Loading)

- [x] **Step 1: Create `sources/00_canonical_context.md`**
  Concatenate the two source files with zero content loss: full text of
  `00_project_context.md` (sections: Long-Term Frame, Current Goal, Current
  Training Assumptions, Planning Principle), then full text of
  `04_planning_rules_and_retro.md` (sections: Core Rules, Decision Gate for
  58-60 mpw, Retro Notes), under the top heading:
  ```markdown
  # Canonical Context (project facts + planning rules)

  Single mandated pre-read for training questions. Merged 2026-08-01 from
  `00_project_context.md` + `04_planning_rules_and_retro.md`. Update here first;
  other files link, not restate.
  ```
  Deduplicate only exact-duplicate bullets that appear in both files (e.g.
  "Distinguish \"not now\" from \"not possible\"" / consistency-as-top-constraint
  appear in both Planning Principle and Core Rules — keep one, in Core Rules).
- [x] **Step 2: Reduce old files to redirect stubs** — each becomes exactly:
  ```markdown
  # Moved

  Merged into [`00_canonical_context.md`](00_canonical_context.md) on 2026-08-01.
  ```
- [x] **Step 3: Update every reference**
  Run: `grep -rln "00_project_context\|04_planning_rules" --include="*.md" .`
  Update `AGENTS.md` Default Context Loading to:
  ```markdown
  Before answering training-plan questions, read:

  1. `STATUS.md` — generated current-status digest (if present)
  2. `sources/00_canonical_context.md` — canonical facts and planning rules
  ```
  Update all other referencing markdown files to point at the canonical file
  (plans/decisions/retros may keep historical mentions in past-tense narrative;
  update only live instructions and link targets).
- [x] **Step 4: Verify**
  Run: `.venv/bin/python scripts/check_markdown_links.py && .venv/bin/python -m pytest tests/ -v`
  Expected: pass. Also `wc -l sources/00_canonical_context.md` ≈ 60-65 (sum of
  originals minus merged headers/dupes).
- [x] **Step 5: Commit + push Phase 1 complete (Tech Lead)**
  ```bash
  git add sources/00_canonical_context.md sources/00_project_context.md sources/04_planning_rules_and_retro.md AGENTS.md
  git add <other updated referencing files, explicit paths>
  git commit -m "Merge canonical context sources; point AGENTS.md at single pre-read"
  git push
  ```
  Report sha.

---

## Phase 2 — Views and status digest (Lane 1)

### Task 7: Enrich the weekly auto-summary block

**Files:**
- Modify: `scripts/weekly_entries.py:523-531` (`build_weekly_log_body`) and its
  caller `upsert_weekly_log` (:534-551)
- Test: `tests/test_weekly_summary.py` (create)

**Interfaces:**
- Consumes: `WeeklyDayEntry` (fields: `day_date, completed, distance, pace,
  effort, warning_signs, has_content`), `WeekPlan` (fields: `source_relpath,
  target_mileage, primary_purpose, week_start`).
- Produces: `build_weekly_log_body(week_plan, rows, total_miles, status,
  day_entries: dict[date, WeeklyDayEntry]) -> str` — new 5th parameter; body now
  contains `- Days:` and `- Warnings:` lines that Task 8's parser reads.

- [x] **Step 1: Write failing test** — create `tests/test_weekly_summary.py`:
  ```python
  from datetime import date
  import sys
  from pathlib import Path

  sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
  from weekly_entries import WeeklyDayEntry, build_weekly_log_body
  from weekly_plan import WeekPlan


  def make_plan():
      return WeekPlan(
          week_start=date(2026, 7, 20),
          target_mileage="about 34-37",
          primary_purpose="build a stable platform",
          source_relpath="plans/2026-half-marathon/01_pre_block_ramp.md",
          day_plans=[],
      )


  def test_body_has_day_digest_and_warning_rollup():
      entries = {
          date(2026, 7, 20): WeeklyDayEntry(
              day_date=date(2026, 7, 20), completed="5.57 mi run",
              distance="5.57 mi", pace="10:44/mi", effort="imported"),
          date(2026, 7, 22): WeeklyDayEntry(
              day_date=date(2026, 7, 22), completed="5.62 mi run",
              distance="5.62 mi", pace="11:00/mi", effort="imported",
              warning_signs="Right calf: slight sharp pain, watch closely"),
      }
      body = build_weekly_log_body(make_plan(), [], 11.19, "Wednesday run logged", entries)
      assert "- Days: Mon 5.57mi @10:44/mi | Wed 5.62mi @11:00/mi ⚠" in body
      assert "- Warnings: Wed: Right calf: slight sharp pain, watch closely" in body


  def test_body_without_warnings_says_none():
      body = build_weekly_log_body(make_plan(), [], 0.0, "No days logged yet", {})
      assert "- Warnings: none logged" in body
      assert "- Days: none yet" in body
  ```
  (If `WeekPlan`'s constructor differs, mirror its real signature from
  `scripts/weekly_plan.py` — check first with `grep -n "class WeekPlan" -A 12 scripts/weekly_plan.py`.)
- [x] **Step 2: Run, verify failure**
  Run: `.venv/bin/python -m pytest tests/test_weekly_summary.py -v`
  Expected: FAIL — `build_weekly_log_body() takes 4 positional arguments but 5 were given`.
- [x] **Step 3: Implement** — replace `build_weekly_log_body` in
  `scripts/weekly_entries.py`:
  ```python
  def day_digest(entry: WeeklyDayEntry) -> str:
      label = entry.day_date.strftime("%a")
      miles = entry.distance.removesuffix(" mi").strip()
      part = f"{label} {miles}mi" if miles else f"{label} {entry.completed or 'logged'}"
      if entry.pace:
          part += f" @{entry.pace}"
      if entry.warning_signs:
          part += " ⚠"
      return part


  def build_weekly_log_body(
      week_plan: WeekPlan,
      rows: list[str],
      total_miles: float,
      status: str,
      day_entries: dict[date, WeeklyDayEntry],
  ) -> str:
      logged = [e for _, e in sorted(day_entries.items()) if e.has_content]
      days = " | ".join(day_digest(e) for e in logged) or "none yet"
      warnings = "; ".join(
          f"{e.day_date.strftime('%a')}: {e.warning_signs}"
          for e in logged if e.warning_signs
      ) or "none logged"
      lines = [
          f"- Source plan: `{week_plan.source_relpath}`",
          f"- Target mileage: `{week_plan.target_mileage}`",
          f"- Actual mileage so far: `{total_miles:.2f}`",
          f"- Primary purpose: {week_plan.primary_purpose}",
          f"- Status: `{status}`",
          f"- Days: {days}",
          f"- Warnings: {warnings}",
      ]
      return "\n".join(lines)
  ```
  In `upsert_weekly_log` change the call to
  `build_weekly_log_body(week_plan, rows, total_miles, status, day_entries)`.
- [x] **Step 4: Run tests, re-render current week, eyeball**
  Run: `.venv/bin/python -m pytest tests/ -v && bash scripts/ingest.sh --sync-only && head -20 logs/weekly/week_2026-07-20.md`
  Expected: tests pass; the auto-summary block of the current week shows the two
  new lines with real data matching the daily entries verbatim.
- [x] **Step 5: Commit (Tech Lead, after review)**
  ```bash
  git add scripts/weekly_entries.py tests/test_weekly_summary.py logs/weekly README.md
  git commit -m "Enrich weekly auto-summary with day digest and warning rollup"
  ```

### Task 8: `status_digest.py` → root `STATUS.md`

**Files:**
- Create: `scripts/status_digest.py`
- Create: `STATUS.md` (generated)
- Test: `tests/test_status_digest.py`

**Interfaces:**
- Consumes: the auto-summary block format written by Task 7 (lines
  `- Target mileage:`, `- Actual mileage so far:`, `- Status:`, `- Days:`,
  `- Warnings:` between `<!-- auto-summary:start -->` / `end` markers).
- Produces: CLI `scripts/status_digest.py [--today YYYY-MM-DD] [--repo-root PATH]`
  writing `STATUS.md`. Fails loud (`SystemExit`, nonzero) on unparseable blocks —
  never emits a guessed number.

- [x] **Step 1: Write failing test** — create `tests/test_status_digest.py`:
  ```python
  import subprocess
  import sys
  from pathlib import Path

  SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "status_digest.py"

  WEEK = """# Week of 2026-07-20 Weekly Log

  ## Weekly Summary

  <!-- auto-summary:start -->
  - Source plan: `plans/2026-half-marathon/01_pre_block_ramp.md`
  - Target mileage: `about 34-37`
  - Actual mileage so far: `11.19`
  - Primary purpose: build a stable platform
  - Status: `Wednesday run logged`
  - Days: Mon 5.57mi @10:44/mi | Wed 5.62mi @11:00/mi ⚠
  - Warnings: Wed: Right calf: slight sharp pain, watch closely
  <!-- auto-summary:end -->
  """

  def run(tmp_path, today):
      (tmp_path / "logs" / "weekly").mkdir(parents=True)
      (tmp_path / "logs" / "weekly" / "week_2026-07-20.md").write_text(WEEK)
      return subprocess.run(
          [sys.executable, str(SCRIPT), "--repo-root", str(tmp_path), "--today", today],
          capture_output=True, text=True,
      )

  def test_writes_status_md_for_current_week(tmp_path):
      result = run(tmp_path, "2026-07-23")
      assert result.returncode == 0, result.stderr
      status = (tmp_path / "STATUS.md").read_text()
      assert "week of 2026-07-20" in status
      assert "`about 34-37`" in status and "`11.19`" in status
      assert "Right calf" in status

  def test_fails_loud_on_unparseable_block(tmp_path):
      (tmp_path / "logs" / "weekly").mkdir(parents=True)
      (tmp_path / "logs" / "weekly" / "week_2026-07-20.md").write_text("# broken\n")
      result = subprocess.run(
          [sys.executable, str(SCRIPT), "--repo-root", str(tmp_path), "--today", "2026-07-23"],
          capture_output=True, text=True,
      )
      assert result.returncode != 0
  ```
- [x] **Step 2: Run, verify failure** (script missing).
- [x] **Step 3: Implement `scripts/status_digest.py`**
  ```python
  #!/usr/bin/env python3
  """Generate STATUS.md — the one-file 'am I on track?' digest.

  Reads weekly-log auto-summary blocks only (never raw daily entries): the
  record/view contract says views are built from what weekly_entries.py already
  distilled. Fails loud on unparseable blocks rather than guessing numbers.
  """
  from __future__ import annotations

  import argparse
  import re
  from datetime import date, timedelta
  from pathlib import Path

  BLOCK_START = date(2026, 8, 3)
  RACE_DAY = date(2026, 12, 6)
  BLOCK_WEEKS = 18
  MARKER = re.compile(r"<!-- auto-summary:start -->\n(?P<body>.*?)<!-- auto-summary:end -->", re.DOTALL)
  FIELD = re.compile(r"^- (?P<key>[^:]+): ?(?P<value>.*)$")


  def parse_summary(path: Path) -> dict[str, str]:
      match = MARKER.search(path.read_text())
      if match is None:
          raise SystemExit(f"{path.name}: no auto-summary block")
      fields: dict[str, str] = {}
      for line in match.group("body").splitlines():
          field = FIELD.match(line.strip())
          if field:
              fields[field.group("key")] = field.group("value")
      required = {"Target mileage", "Actual mileage so far", "Status"}
      missing = required - fields.keys()
      if missing:
          raise SystemExit(f"{path.name}: auto-summary missing {sorted(missing)}")
      return fields


  def week_start_of(path: Path) -> date:
      return date.fromisoformat(path.stem.removeprefix("week_"))


  def build(repo_root: Path, today: date) -> str:
      weekly_dir = repo_root / "logs" / "weekly"
      files = sorted(weekly_dir.glob("week_*.md"))
      if not files:
          raise SystemExit(f"no weekly logs under {weekly_dir}")
      summaries = {week_start_of(p): parse_summary(p) for p in files}
      current_start = today - timedelta(days=today.weekday())
      current = summaries.get(current_start)

      lines = [
          "<!-- generated by scripts/status_digest.py; do not edit by hand -->",
          "",
          "# Training Status",
          "",
          f"Updated {today.isoformat()}. Regenerate: `.venv/bin/python scripts/status_digest.py`.",
          "",
          f"## Current Week (week of {current_start.isoformat()})",
          "",
      ]
      if current is None:
          lines.append("- No weekly log yet for this week.")
      else:
          for key in ("Target mileage", "Actual mileage so far", "Status",
                      "Primary purpose", "Days", "Warnings"):
              if key in current:
                  lines.append(f"- {key}: {current[key]}")
      block_week = (current_start - BLOCK_START).days // 7 + 1
      position = (
          f"week {block_week} of {BLOCK_WEEKS}" if 1 <= block_week <= BLOCK_WEEKS
          else "pre-block ramp" if block_week < 1 else "post-block"
      )
      lines += [
          "",
          "## Block Position",
          "",
          f"- 2026 half-marathon block: {position} (starts {BLOCK_START.isoformat()}, race {RACE_DAY.isoformat()})",
          "- Grid: `plans/2026-half-marathon/BLOCK_OVERVIEW.md`; facts/rules: `sources/00_canonical_context.md`",
          "",
          "## Recent Weeks",
          "",
          "| Week of | Target | Actual | Status |",
          "| --- | --- | --- | --- |",
      ]
      for start in sorted(summaries)[-4:]:
          fields = summaries[start]
          lines.append(
              f"| {start.isoformat()} | {fields['Target mileage']} | "
              f"{fields['Actual mileage so far']} | {fields['Status']} |"
          )
      return "\n".join(lines) + "\n"


  def main() -> None:
      parser = argparse.ArgumentParser(description=__doc__)
      parser.add_argument("--repo-root", type=Path,
                          default=Path(__file__).resolve().parent.parent)
      parser.add_argument("--today", type=date.fromisoformat, default=date.today())
      args = parser.parse_args()
      output = build(args.repo_root, args.today)
      (args.repo_root / "STATUS.md").write_text(output)
      print(f"wrote {args.repo_root / 'STATUS.md'}")


  if __name__ == "__main__":
      main()
  ```
- [x] **Step 4: Run tests, then generate the real file**
  Run: `.venv/bin/python -m pytest tests/test_status_digest.py -v && .venv/bin/python scripts/status_digest.py && cat STATUS.md`
  Expected: tests pass; STATUS.md under 60 lines; every number matches the source
  auto-summary blocks verbatim (spot-check against `logs/weekly/week_2026-07-20.md`).
- [x] **Step 5: Commit (Tech Lead, after review)**
  ```bash
  git add scripts/status_digest.py tests/test_status_digest.py STATUS.md
  git commit -m "Add status digest generator and root STATUS.md view"
  ```

### Task 9: Wire the digest into ingest + instructions (Haiku)

**Files:**
- Modify: `scripts/ingest.sh` (final lines)
- Modify: `AGENTS.md` (Default Context Loading — drop the "(if present)" hedge)
- Modify: `README.md` (one pointer line near the top)

- [x] **Step 1: ingest.sh runs the digest after every ingest** — replace the final
  `exec "${venv_python}" "${ingest_script}" "$@"` with:
  ```bash
  "${venv_python}" "${ingest_script}" "$@"
  "${venv_python}" "${repo_root}/scripts/status_digest.py"
  ```
  (No `exec`: the digest must run after the ingest finishes; `set -e` still
  aborts on ingest failure so a failed import never regenerates the view.)
- [x] **Step 2: AGENTS.md** — Default Context Loading item 1 becomes:
  `1. \`STATUS.md\` — generated current-status digest`
- [x] **Step 3: README.md** — add under the title:
  `Current status at a glance: [STATUS.md](STATUS.md) (generated; regenerate via \`scripts/status_digest.py\`).`
- [x] **Step 4: Verify end-to-end**
  Run: `bash scripts/ingest.sh --sync-only && git diff --stat && .venv/bin/python scripts/check_markdown_links.py && .venv/bin/python -m pytest tests/ -v`
  Expected: ingest completes and rewrites STATUS.md; links and tests pass.
- [x] **Step 5: Commit + push Phase 2 (Tech Lead)**
  ```bash
  git add scripts/ingest.sh AGENTS.md README.md STATUS.md
  git commit -m "Regenerate STATUS.md on every ingest; point default context at it"
  git push
  ```
  Report sha.

---

## Phase 3 — Weekly-log compression (Lane 2)

### Task 10: Compact Managed Notes builder

**Files:**
- Modify: `scripts/weekly_entries.py:163-169` (`build_managed_notes_lines`)
- Test: `tests/test_weekly_summary.py` (extend)

**Interfaces:**
- Consumes: `Activity` from `ingest_coros_fit_weather.py` — `row: dict[str, str]`,
  `heat_note: str` (either `""` or
  `"- Heat: 84°F + 49°F dew = 133 (moderate). Heat-neutral equivalent ~10:28/mi (ran 10:44/mi, ~+2.5%)."`).
- Produces: one managed-note line per activity:
  `  - Imported 479051765975646409.fit | start 17:25 | HR 141/161 | asc 66m | 84°F + 49°F dew = 133 (moderate). Heat-neutral equivalent ~10:28/mi (ran 10:44/mi, ~+2.5%)`

- [x] **Step 1: Write failing test** — append to `tests/test_weekly_summary.py`:
  ```python
  from datetime import datetime
  from zoneinfo import ZoneInfo
  from ingest_coros_fit_weather import Activity
  from weekly_entries import build_managed_notes_lines


  def make_activity(**overrides):
      row = {
          "source_file": "479051765975646409.fit",
          "start_time": "2026-07-20T17:25:54-04:00",
          "distance_mi": "5.57", "duration_s": "3586",
          "avg_hr": "141", "max_hr": "161", "ascent_m": "66",
          "weather_temp_f": "83.7", "weather_dew_point_f": "49.4",
          "heat_load_sum": "133",
          "weather_observation_time": "2026-07-20T17:00",
          "weather_source": "open-meteo",
      }
      row.update(overrides)
      start = datetime(2026, 7, 20, 17, 25, 54, tzinfo=ZoneInfo("America/New_York"))
      return Activity(row=row, local_start=start, local_date=start.date(),
                      timezone_name="America/New_York")


  def test_managed_notes_is_one_compact_line():
      lines = build_managed_notes_lines(make_activity())
      assert len(lines) == 1
      line = lines[0]
      assert line.startswith("  - Imported 479051765975646409.fit | start 17:25 | HR 141/161 | asc 66m | ")
      assert "84°F + 49°F dew = 133" in line
      assert "Heat-neutral equivalent" in line


  def test_managed_notes_without_heat_falls_back_to_temp():
      lines = build_managed_notes_lines(make_activity(heat_load_sum="", weather_dew_point_f=""))
      assert lines == [
          "  - Imported 479051765975646409.fit | start 17:25 | HR 141/161 | asc 66m | 83.7°F"
      ]
  ```
- [x] **Step 2: Run, verify failure** (current builder returns 3-4 lines).
- [x] **Step 3: Implement** — replace `build_managed_notes_lines` in
  `scripts/weekly_entries.py`:
  ```python
  def build_managed_notes_lines(activity: Any) -> list[str]:
      # One compact line; full provenance stays in data/processed JSONL.
      row = activity.row
      parts = [f"Imported {row.get('source_file', '') or row.get('source_relpath', '')}"]
      start = row.get("start_time", "")
      if len(start) >= 16:
          parts.append(f"start {start[11:16]}")
      if row.get("avg_hr", "").strip():
          parts.append(f"HR {row['avg_hr']}/{row.get('max_hr', '').strip() or '?'}")
      if row.get("ascent_m", "").strip():
          parts.append(f"asc {row['ascent_m']}m")
      heat = activity.heat_note
      if heat:
          parts.append(heat.removeprefix("- Heat: ").rstrip("."))
      elif row.get("weather_temp_f", "").strip():
          parts.append(f"{row['weather_temp_f']}°F")
      return [f"  - {' | '.join(parts)}"]
  ```
- [x] **Step 4: Run full suite; update any existing assertions on the old 4-line
  format** (they are format expectations, not behavior — note each in the report).
  Run: `.venv/bin/python -m pytest tests/ -v`
- [x] **Step 5: Commit (Tech Lead, after review)**
  ```bash
  git add scripts/weekly_entries.py tests/test_weekly_summary.py
  git commit -m "Compress Managed Notes to one line per import"
  ```

### Task 11: Migrator for existing weekly-log Managed Notes

**Files:**
- Create: `scripts/migrate_managed_notes.py`
- Test: `tests/test_migrate_managed_notes.py`

**Interfaces:**
- Consumes: verbose managed-note blocks in `logs/weekly/week_*.md` (lines starting
  `  - Imported from`, `  - FIT summary:`, `  - Weather at start:`, `  - Heat:`).
- Produces: those lines replaced by one compact line (Task 10's format). ALL other
  lines byte-identical.

- [x] **Step 1: Write failing test** — create `tests/test_migrate_managed_notes.py`:
  ```python
  import subprocess
  import sys
  from pathlib import Path

  SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "migrate_managed_notes.py"

  VERBOSE = """### 2026-07-20

  - Planned: Off or 3 mi very easy
  - Completed: 5.57 mi run
  - Time: 59:46
  - Distance: 5.57 mi
  - Pace: 10:44/mi
  - Effort: imported
  - Managed Notes:
    - Imported from `data/coros_exports/COROS_export_2026-07-23/479051765975646409.fit`.
    - FIT summary: start `2026-07-20T17:25:54-04:00`, avg HR `141`, max HR `161`, ascent `66 m`.
    - Weather at start: `83.7 F` at `2026-07-20T17:00` from `open-meteo`.
    - Heat: 84°F + 49°F dew = 133 (moderate). Heat-neutral equivalent ~10:28/mi (ran 10:44/mi, ~+2.5%).
  - Manual Notes:
    - Felt heavy but fine.
  - Sleep: 7h
  - Soreness: calves tight
  - Stress: low
  - Warning signs: 
  """

  def test_compacts_managed_notes_and_touches_nothing_else(tmp_path):
      log = tmp_path / "week_2026-07-20.md"
      log.write_text(VERBOSE)
      result = subprocess.run(
          [sys.executable, str(SCRIPT), "--weekly-dir", str(tmp_path)],
          capture_output=True, text=True,
      )
      assert result.returncode == 0, result.stderr
      text = log.read_text()
      assert text.count("  - Imported 479051765975646409.fit | start 17:25 | HR 141/161 | asc 66m | 84°F + 49°F dew = 133 (moderate). Heat-neutral equivalent ~10:28/mi (ran 10:44/mi, ~+2.5%)") == 1
      assert "FIT summary" not in text
      # every non-managed line byte-identical
      managed_prefixes = ("  - Imported", "  - FIT summary", "  - Weather at start", "  - Heat:")
      def strip_managed(source):
          keep, in_managed = [], False
          for line in source.splitlines():
              if line == "- Managed Notes:":
                  in_managed = True
                  keep.append(line)
              elif in_managed and line.startswith("  - "):
                  continue
              else:
                  in_managed = False
                  keep.append(line)
          return keep
      assert strip_managed(VERBOSE) == strip_managed(text)

  def test_idempotent(tmp_path):
      log = tmp_path / "week_2026-07-20.md"
      log.write_text(VERBOSE)
      subprocess.run([sys.executable, str(SCRIPT), "--weekly-dir", str(tmp_path)], check=True)
      once = log.read_text()
      subprocess.run([sys.executable, str(SCRIPT), "--weekly-dir", str(tmp_path)], check=True)
      assert log.read_text() == once
  ```
- [x] **Step 2: Run, verify failure** (script missing).
- [x] **Step 3: Implement `scripts/migrate_managed_notes.py`**
  ```python
  #!/usr/bin/env python3
  """One-shot: compress verbose Managed Notes blocks in logs/weekly/*.md.

  Only rewrites nested lines under '- Managed Notes:' that match the four known
  verbose prefixes; every other byte passes through untouched. Idempotent:
  already-compact lines (no 'Imported from' backtick form) are left alone.
  """
  from __future__ import annotations

  import argparse
  import re
  from pathlib import Path

  REPO_ROOT = Path(__file__).resolve().parent.parent
  IMPORTED = re.compile(r"- Imported from `(?P<path>[^`]+)`")
  FIT = re.compile(
      r"- FIT summary: start `(?P<start>[^`]*)`, avg HR `(?P<avg>[^`]*)`, "
      r"max HR `(?P<max>[^`]*)`, ascent `(?P<ascent>[^`]*) m`"
  )
  WEATHER = re.compile(r"- Weather at start: `(?P<temp>[^ `]+) F`")
  HEAT = re.compile(r"- Heat: (?P<body>.+?)\.?$")


  def compact(block: list[str]) -> list[str]:
      joined = "\n".join(block)
      imported = IMPORTED.search(joined)
      fit = FIT.search(joined)
      if not imported or not fit:
          return block  # not the verbose import format; leave untouched
      parts = [f"Imported {Path(imported.group('path')).name}"]
      start = fit.group("start")
      if len(start) >= 16:
          parts.append(f"start {start[11:16]}")
      if fit.group("avg"):
          parts.append(f"HR {fit.group('avg')}/{fit.group('max') or '?'}")
      if fit.group("ascent"):
          parts.append(f"asc {fit.group('ascent')}m")
      heat = HEAT.search(joined)
      weather = WEATHER.search(joined)
      if heat:
          parts.append(heat.group("body").rstrip("."))
      elif weather:
          parts.append(f"{weather.group('temp')}°F")
      extras = [line for line in block
                if not any(p.search(line) for p in (IMPORTED, FIT, WEATHER, HEAT))]
      return [f"  - {' | '.join(parts)}", *extras]


  def migrate_text(text: str) -> str:
      out: list[str] = []
      block: list[str] = []
      in_managed = False
      for line in text.splitlines():
          if line == "- Managed Notes:":
              in_managed = True
              out.append(line)
          elif in_managed and line.startswith("  - "):
              block.append(line)
          else:
              if block:
                  out.extend(compact(block))
                  block = []
              in_managed = False
              out.append(line)
      if block:
          out.extend(compact(block))
      trailing = "\n" if text.endswith("\n") else ""
      return "\n".join(out) + trailing


  def main() -> None:
      parser = argparse.ArgumentParser(description=__doc__)
      parser.add_argument("--weekly-dir", type=Path,
                          default=REPO_ROOT / "logs" / "weekly")
      args = parser.parse_args()
      for path in sorted(args.weekly_dir.glob("week_*.md")):
          original = path.read_text()
          migrated = migrate_text(original)
          if migrated != original:
              tmp = path.with_name(path.name + ".tmp")
              tmp.write_text(migrated)
              tmp.replace(path)
              print(f"compacted {path.name}")


  if __name__ == "__main__":
      main()
  ```
- [x] **Step 4: Run tests**
  Run: `.venv/bin/python -m pytest tests/test_migrate_managed_notes.py tests/ -v`
  Expected: PASS.
- [x] **Step 5: Commit (Tech Lead, after review)**
  ```bash
  git add scripts/migrate_managed_notes.py tests/test_migrate_managed_notes.py
  git commit -m "Add one-shot Managed Notes compaction migrator"
  ```

### Task 12: Run log migration + end-to-end reconcile (Haiku)

- [x] **Step 1: Snapshot manual sections before migration**
  Run: `grep -c "Warning signs:" logs/weekly/*.md && wc -l logs/weekly/*.md`
  Record the output verbatim in the task report (compared again in Step 3).
- [x] **Step 2: Run the migrator**
  Run: `.venv/bin/python scripts/migrate_managed_notes.py`
  Expected: one `compacted week_*.md` line per file that had verbose notes.
- [x] **Step 3: Verify manual sections untouched**
  Run: `git diff logs/weekly/ | grep '^[-+]' | grep -v '^[-+][-+]' | grep -v 'Imported\|FIT summary\|Weather at start\|Heat:'`
  Expected: empty output — every changed line is a managed-note line.
- [x] **Step 4: End-to-end**
  Run: `bash scripts/ingest.sh --sync-only && .venv/bin/python scripts/reconcile_weekly_mileage.py && .venv/bin/python -m pytest tests/ -v`
  Expected: sync-only leaves logs stable (`git diff --stat logs/` shows no *new*
  churn beyond the migration), reconcile clean, tests pass.
- [x] **Step 5: Commit + push (Tech Lead)**
  ```bash
  git add logs/weekly STATUS.md README.md
  git commit -m "Compact Managed Notes across existing weekly logs"
  git push
  ```
  Report sha.

### Task 13: Decision record + workflow doc refresh (Haiku)

**Files:**
- Create: `decisions/2026-08-01_token_usage_record_view_split.md`
- Modify: `docs/repo_workflow.md` (only sections describing the verbose Managed
  Notes format, the two-file mandated pre-read, or `data/processed` layout)

- [x] **Step 1: Write the decision record**
  ```markdown
  # 2026-08-01 — Record/view split for token-usage reduction

  1. **Decision**: Adopt the record/view architecture from
     `docs/superpowers/specs/2026-08-01-token-usage-reduction-design.md`:
     STATUS.md digest, enriched auto-summaries, one-line Managed Notes, slim
     JSONL schema, quarantined pre-block history, merged canonical context.
  2. **Facts**: Weekly logs were ~150 lines with 4-line generated notes per run;
     JSONL rows carried 3 timestamp variants and dual temperature units; a
     345KB pre-block file sat in the greppable path; AGENTS.md auto-loaded ~8K.
  3. **Preference**: Keep hand-edited section layout; agents read views, not
     records.
  4. **Risk**: Migrations could corrupt manual notes — mitigated by byte-identity
     tests and temp-file writes; view staleness cannot corrupt records (one-way
     data flow).
  5. **Adaptation**: STATUS.md regenerates on every ingest; migrators are
     idempotent and re-runnable.
  6. **Final call**: Adopted; executed by Opus-led subagent team under the
     mandatory tier cascade (globally hook-enforced).
  ```
- [x] **Step 2: Refresh `docs/repo_workflow.md`** — update only stale statements
  found via: `grep -n "FIT summary\|00_project_context\|04_planning_rules\|Managed Notes" docs/repo_workflow.md`
- [x] **Step 3: Final full verification**
  Run: `.venv/bin/python -m pytest tests/ -v && .venv/bin/python scripts/check_markdown_links.py && .venv/bin/python scripts/status_digest.py`
  Expected: all green.
- [x] **Step 4: Commit + push Phase 3 complete (Tech Lead)**
  ```bash
  git add decisions/2026-08-01_token_usage_record_view_split.md docs/repo_workflow.md
  git commit -m "Record the record/view split decision; refresh workflow doc"
  git push
  ```
  Report sha.

---

## Success criteria (from spec — verify at the end)

- [ ] "Am I on track?" answerable from `STATUS.md` alone (< 60 lines).
- [ ] Auto-loaded instruction bytes (AGENTS.md + mandated pre-reads) down ≥ 40%:
      compare `wc -c AGENTS.md sources/00_canonical_context.md STATUS.md` against
      the pre-change `wc -c AGENTS.md sources/00_project_context.md sources/04_planning_rules_and_retro.md` baseline.
- [ ] Weekly-log generated content per filled day down ≥ 50% (4 managed lines → 1).
- [ ] JSONL rows ≥ 50% smaller (Task 5 du/wc evidence); pre-block history out of
      `data/processed/`; reconcile and full suite green.
