# Decision Gate - 2026-08-01

## Decision

Adopt the record/view architecture from `docs/superpowers/specs/2026-08-01-token-usage-reduction-design.md`: STATUS.md digest, enriched auto-summaries, one-line Managed Notes, slim JSONL schema, quarantined pre-block history, merged canonical context.

## Facts

Weekly logs were ~150 lines with 4-line generated notes per run; JSONL rows carried 3 timestamp variants and dual temperature units; a 345KB pre-block file sat in the greppable path; AGENTS.md auto-loaded ~8K.

## Preference

Keep hand-edited section layout; agents read views, not records.

## Risk

Migrations could corrupt manual notes — mitigated by byte-identity tests and temp-file writes; view staleness cannot corrupt records (one-way data flow).

## Adaptation

STATUS.md regenerates on every ingest; migrators are idempotent and re-runnable.

## Final Call

Adopted; executed by Opus-led subagent team under the mandatory tier cascade (globally hook-enforced).

---

## Deviations from Execution Plan

### Deviation 1: Task 4 — Safety checks replaced with ordered tuple identity comparison

The plan mandated two specific safety checks in `scripts/migrate_processed_slim.py`. Both were replaced with a single ordered per-row identity comparison over the tuple `(activity_id, source_sha256, distance_mi, duration_s)`, plus a monkeypatched-corruption test asserting `SystemExit` and a byte-unchanged source file.

**Rationale**: The plan's two checks were found to be a dead row-count check and a tautological sha-set check — neither could fail. The ordered tuple comparison catches drops, reorders and duplication that the originals could not.

### Deviation 2: Task 11 — Managed Notes block segmentation per activity

The plan's Step 3 supplied verbatim code for `compact()`/`migrate_text()` that collapsed an ENTIRE Managed Notes block to ONE line regardless of how many activities the block contained. Measured on real repo data before any file was written, `logs/weekly/week_2026-07-06.md` would have gone from 8 activities to 6 — silent destruction of two runs' provenance. Three logs were affected: `week_2026-06-15.md` (2 activities in one block), `week_2026-06-29.md` (2), `week_2026-07-06.md` (3).

The plan's own Interfaces section was ruled to govern over its code block, and each Managed Notes block is now segmented per activity. The plan's Task 12 manual-section snapshot would NOT have caught this: manual sections survive intact, so the loss was confined to managed content.

---

## Measured Success Criteria

### Auto-loaded instruction bytes

- **Criterion**: >= 40% reduction
- **Baseline** (commit 80056df):
  - AGENTS.md: 5576 bytes
  - sources/00_project_context.md: 1398 bytes
  - sources/04_planning_rules_and_retro.md: 1820 bytes
  - **Total**: 8794 bytes
- **Now** (commit 9973b2f):
  - AGENTS.md: 3181 bytes
  - sources/00_canonical_context.md: 1125 bytes
  - STATUS.md: 966 bytes
  - **Total**: 5272 bytes
- **Result**: 40.1% reduction. **MET**, with a 4-byte margin against the
  5276-byte ceiling.

Closed by de-duplication, not deletion: Decision Gates moved to
`docs/decision_formats.md` and Retro Notes to `docs/repo_workflow.md`, each
with a resolving pointer from the auto-loaded set. Treat 5276 as a soft
target — the thin margin is what caused the direction-neutral decision-gate
trigger to be squeezed out on the first pass (caught in review, restored).
Prefer relocating a rule over compressing it away.

### Processed JSONL row size

- **Criterion**: rows >= 50% smaller
- **Baseline** (80056df, same 20 files): 57280 bytes / 53 rows = 1080.8 bytes per row
- **Now**: 35170 bytes / 53 rows = 663.6 bytes per row
- **Result**: 38.6% reduction. **NOT MET** — accepted gap.

The remaining row weight is load-bearing. `source_sha256` is the largest
single field (13.7% of row bytes) and is the file-integrity key used by
`scripts/ingest_coros_fit_batch.py` and by the identity check in
`scripts/migrate_processed_slim.py`. The only genuinely redundant fields are
the near-constant `parser` and `weather_source`; dropping both reaches 47.1%,
still short. Reaching 50% requires dropping `source_sha256` (54.8%), which
trades away content-hash verification on the system of record for 7.7
percentage points. Not worth it. The criterion is recorded as missed rather
than met by weakening data integrity.

### Weekly logs (same 11 files, Phase 3 migration)

41732 → 32182 bytes => 22.9% reduction.

### Criteria that WERE met

- "Am I on track?" is answerable from `STATUS.md` alone and STATUS.md is under 60 lines: **28 lines**. ✓
- Weekly-log generated content per filled day dropped from 4 managed lines to 1 (>= 50%). ✓
- Pre-block history JSONL is out of `data/processed/`. ✓
- Reconcile and the full suite are green. ✓

### Summary

Five of six criteria met. The auto-loaded instruction-byte criterion was
initially missed at 2.3% and closed by Task 14 (de-duplication) at 40.1%. The
JSONL row-size criterion stands at 38.6% against a >= 50% target and is
accepted as a recorded gap, because closing it means removing the content
hash from the system of record.
