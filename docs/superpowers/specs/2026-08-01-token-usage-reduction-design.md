# Token-Usage Reduction — Design Spec

Date: 2026-08-01
Status: approved design, pending implementation plan

## Problem

The repo serves three jobs — .fit run collector, training-block record keeper,
BQ-tracking checker — and all three burn more agent tokens than they need to:

1. **Session startup**: `AGENTS.md` (~8K) auto-loads every session, and the
   Default Context Loading rule mandates reading `sources/00` + `sources/04`
   before any training question.
2. **Coaching sessions**: answering "am I on track?" means reading several
   ~150-line weekly logs whose bulk is empty scaffold and verbose generated
   Managed Notes.
3. **Import sessions**: `data/processed/*.jsonl` rows carry redundant fields
   (three timestamp variants, dual temperature units, tmp paths), and one
   345KB / 333-row pre-block history file sits in the greppable path.

Operator decisions: optimize all three areas by expected savings; weekly-log
section layout stays (compress generated content only); JSONL schema and
history may be reshaped freely; `AGENTS.md` may be reorganized freely provided
no rule is lost, only relocated to a clearly referenced on-demand file.

## Architecture: "read the view, not the record"

Every artifact is classified as **record** (system of record — optimized for
correctness/audit; scripts and humans write it, agents rarely read it) or
**view** (generated, compact — what gets read into context). The existing
`scripts/block_overview.py` → `BLOCK_OVERVIEW.md` pipeline is the model;
this design generalizes it. Data flows one way: record → view. No script
reads a view to write a record, so view staleness cannot corrupt records.

Four lanes, ordered by expected savings:

## Lane 1 — Views & status digest

- New `scripts/status_digest.py` reads weekly-log auto-summary blocks,
  `plans/2026-half-marathon/weeks/*.md` targets, and canonical source facts;
  writes `STATUS.md` at repo root (target: under 60 lines) containing the
  current week digest (target vs. actual mileage, runs completed, warning
  signs, next SOS day), block position, and BQ-tracking snapshot.
- Regenerated at the end of every import session (hooked into
  `scripts/ingest.sh`) and runnable standalone.
- `weekly_entries.py`'s auto-summary block gains per-day one-liners
  (e.g. `Mon 5.6mi @10:44 ez, HR141 | Tue rest | Wed 5.6mi @11:00 ⚠ calf`),
  a warning-signs rollup, and week status, so a weekly log's first ~15 lines
  answer most week-level questions.
- Default Context Loading (Lane 4) points agents at `STATUS.md` first.

## Lane 2 — Weekly-log compression

- `build_managed_notes_lines()` in `scripts/weekly_entries.py` emits one
  compact line instead of four verbose ones, e.g.
  `Imported 479051765975646409.fit | start 17:25 | HR 141/161 | 84°F/49°dew heat 133 (mod) → neutral ~10:28/mi (+2.5%)`.
  Full provenance (paths, weather source, timestamps) stays in the JSONL
  record, referenced not repeated.
- One-time migration pass converts existing logs' Managed Notes to the
  compact form. **Invariant: manual sections (Manual Notes, Sleep, Soreness,
  Stress, Warning signs) are byte-identical before/after.** Section layout
  is unchanged.

## Lane 3 — Record layer (JSONL) slim + quarantine

- New schema in `scripts/summarize_coros_fit.py`. Keep: `activity_id`,
  `start_time` (with offset), `start_timezone`, `distance_mi`, `duration_s`,
  `avg_hr`, `max_hr`, `ascent_m`, `sport`, `source_file`, `source_sha256`,
  `weather_temp_f`, `weather_dew_point_f`, `weather_apparent_temp_f`,
  `weather_observation_time`, `weather_source`, `heat_load_sum`,
  `heat_pace_adjust_pct`, `parser`, `start_lat`, `start_lon`.
  Drop: `start_time_raw`, `start_time_utc`, `start_time_resolution`,
  all `*_c` temperature duplicates, `source_relpath`, `import_batch`,
  `sub_sport`. Emit `parse_error` / `weather_fetch_error` only when
  non-empty. Roughly 60% smaller per row.
- One-shot migration script converts existing `data/processed/*.jsonl`.
- The 333-row pre-block history file
  (`coros_export_2026-05-09_summary.jsonl`) moves to
  `data/archive/pre_block_history/` with a short README explaining what it
  is and why it is out of the default search path.

## Lane 4 — Instruction & context load

- `AGENTS.md` keeps auto-loaded: role, coaching rules, decision gates,
  operating discipline, the record/view reading contract, and one-line
  pointers to on-demand docs.
- Moves to on-demand docs: six-hat format detail (already duplicated in
  `templates/`), collaboration-model narrative (→
  `docs/collaboration_model.md`), major-decision format detail.
- `sources/00_project_context.md` + `sources/04_planning_rules_and_retro.md`
  merge into `sources/00_canonical_context.md`; the old filenames become
  one-line redirect stubs so existing links don't break.
- Default Context Loading rule becomes: read `STATUS.md` +
  `sources/00_canonical_context.md`.

## Testing

- Lane 1: new `tests/test_status_digest.py` — digest built from fixture
  logs; stale/missing-week handling; fails loud on unparseable auto-summary
  (verbatim-data rule: never emit a guessed number).
- Lane 2: update `tests/test_ingest_coros_fit.py` for compact Managed
  Notes; migrator tests assert the manual-section byte-identity invariant.
- Lane 3: schema round-trip tests; migration test asserts no activity lost
  (row counts and `source_sha256` sets match old vs. new).
- Lane 4: `scripts/check_markdown_links.py` passes; grep-based check that
  every removed AGENTS.md rule string exists in its relocation target.
- Full pytest suite green before each phase commit;
  `scripts/reconcile_weekly_mileage.py` runs as end-to-end check after
  Lanes 2 and 3 land.

## Error handling

- Migrations write to a temp path, diff-verify, then move into place —
  never in-place edits of records.
- `status_digest.py` fails loud rather than emitting wrong numbers.

## Delegation structure (HARD RULES)

- **Delegation cannot be skipped.** All lane execution goes through the
  subagent hierarchy. The Opus Tech Lead plans, reviews, signs off,
  commits/pushes with explicit paths, and reports shas — it does not absorb
  lane implementation work inline. The only inline exception is a trivial
  edit where spawning an agent costs more tokens than it saves, and the
  lead must state that justification explicitly before doing it.
- **Model tiers are mandatory and cascade one tier down per level**:
  Opus lead → Sonnet lane owners → Haiku mechanical sub-tasks. Every
  `Agent` call passes an explicit `model` override; never rely on
  inheritance.
- Sonnet lane owners: Lane 1 (most design judgment), Lane 2, Lane 3,
  Lane 4. Haiku sub-tasks: running migrations over existing files,
  redirect stubs, fixture updates.
- Nothing a subagent produces is committed without Tech Lead review.
- **Mechanically enforced across all projects** (2026-08-01): a global
  PreToolUse hook (`~/.claude/hooks/enforce-subagent-model.sh`, registered
  in `~/.claude/settings.json` on matcher `Agent|Task`) denies any
  sub-agent launch without an explicit `model` override and requires
  operator confirmation for Opus-tier-or-above spawns. The
  "delegation cannot be skipped" rule itself is instruction-level
  (`~/.claude/CLAUDE.md` + this spec); hooks cannot force a tool call
  to happen, only block wrong ones.

## Sequencing

- **Phase 0 — cheap wins**: quarantine the pre-block JSONL; trim/relocate
  AGENTS.md prose. (Subset of Lanes 3/4; lowest risk, immediate savings.)
- **Phase 1 — Lanes 3 + 4 in parallel**: JSONL schema + migration; docs
  restructure. Fully independent of each other.
- **Phase 2 — Lane 1**: auto-summary enrichment + `status_digest.py`.
- **Phase 3 — Lane 2**: Managed Notes compression + log migration, then
  end-to-end reconcile check.
- Commit and push after each phase verifies, before starting the next
  (Operating Discipline). Explicit file paths only; never `git add -A`.
- A `decisions/` record accompanies the change (it alters log/plan
  conventions and the instruction-file layout).

## Success criteria

- "Am I on track?" answerable from `STATUS.md` alone in typical sessions.
- Auto-loaded instruction bytes (AGENTS.md + mandated pre-reads) reduced
  by ≥40% with zero rules lost.
- Weekly-log generated content reduced by ≥50% per filled day; manual
  sections untouched.
- JSONL rows ≥50% smaller; pre-block history out of the default search
  path; reconcile and full test suite green.
