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

The plan's own Interfaces section was ruled to govern over its code block, and each Managed Notes block is now segmented per activity. Note explicitly that the plan's Task 12 manual-section snapshot would NOT have caught this, because manual sections survive intact — the loss was confined to managed content.

---

## Measured Success-Criteria Shortfall

### Auto-loaded instruction bytes

- **Criterion**: >= 40% reduction
- **Baseline** (commit 80056df):
  - AGENTS.md: 5576 bytes
  - sources/00_project_context.md: 1398 bytes
  - sources/04_planning_rules_and_retro.md: 1820 bytes
  - **Total**: 8794 bytes
- **Now**:
  - AGENTS.md: 4486 bytes
  - sources/00_canonical_context.md: 3136 bytes
  - STATUS.md: 966 bytes
  - **Total**: 8588 bytes
- **Result**: 2.3% reduction. **NOT MET.**

### Processed JSONL total bytes

- **Criterion**: >= 50% reduction
- **Baseline**: 57280 bytes
- **Now**: 35170 bytes
- **Result**: 38.6% reduction. **NOT MET.**

### Weekly logs (same 11 files, Phase 3 migration)

41732 → 32182 bytes => 22.9% reduction.

### Criteria that WERE met

- "Am I on track?" is answerable from `STATUS.md` alone and STATUS.md is under 60 lines: **28 lines**. ✓
- Weekly-log generated content per filled day dropped from 4 managed lines to 1 (>= 50%). ✓
- Pre-block history JSONL is out of `data/processed/`. ✓
- Reconcile and the full suite are green. ✓

### Summary

The two byte-reduction criteria (auto-loaded instruction bytes and processed JSONL total bytes) are **NOT met**. This is accepted for now with a named follow-up: Task 14 will trim the auto-loaded pre-read set, where `AGENTS.md` at 4486 bytes is the largest single item.
