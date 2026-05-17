# Repo Workflow

This repo should stay useful during normal training, not become a second workout.

## Operating Loop

1. Sources define durable context.
2. Decisions record meaningful changes.
3. Plans describe future training.
4. Logs capture completed work.
5. Retros convert recent training into lessons.
6. Recurring lessons update sources.

## Weekly Usage

Before each week:

- Start from the matching file in `plans/2026-half-marathon/`.
- For plan adjustments, propose the exact wording first and only edit after approval.
- Adjust only that week unless the change affects the whole block.
- If the adjustment changes a major assumption, add or update a decision in `decisions/`.

During the week:

- Add daily logs only when there is useful signal.
- Record distance, effort, soreness, sleep/stress, and warning signs.
- Use daily-log manual notes for context that FIT data cannot capture, including run quality, travel fatigue, shortened runs, and skipped-run reasons.
- Do not backfill noise just to make the repo look complete.
- If repo Markdown changed, run `python scripts/check_markdown_links.py` before commit.
- If the live current week changed, check whether `README.md` needs a matching summary update before commit/push.
- Before updating live current-week status in `README.md`, verify completed work from `logs/daily/` first, then `logs/weekly/`, then `data/processed/` if a COROS import may have landed before the Markdown was updated.
- When a request could mean either a training retrospective or a work-session retrospective, label it explicitly before writing.

After each week:

- Add one weekly retro in `retros/weekly/`.
- Capture what changed, what was skipped, and what recovery signals said.
- Feed repeated patterns into `sources/04_planning_rules_and_retro.md`.
- Preserve the distinction between facts, inference, and coaching opinion when writing adjustments or retros.

## File Naming

- Daily log: `logs/daily/YYYY-MM-DD.md`
- Weekly log: `logs/weekly/week_YYYY-MM-DD.md`
- Weekly retro: `retros/weekly/week_YYYY-MM-DD.md`
- Decision: `decisions/YYYY-MM-DD_short_topic.md`
- Raw COROS export: `data/coros_exports/COROS_export_YYYY-MM-DD/`
- Processed data: `data/processed/YYYY-MM-DD_short_topic.*`

## Decision Triggers

Use a decision record before:

- Increasing peak mileage.
- Touching 58-60 mpw.
- Cutting back for more than a few days.
- Adding or removing SOS days.
- Changing race goals.
- Changing framework.
- Adjusting long-run structure.

## Data Import Loop

For a new COROS export:

1. Drop new raw `.fit` files in the repo root.
2. Run `python scripts/ingest_coros_fit.py`.
3. Let the script move those files into `data/coros_exports/COROS_export_YYYY-MM-DD/` for the import date.
4. Do not keep `*:Zone.Identifier` files.
5. Add or update `SHA256SUMS.txt` for the loose `.fit` files.
6. Add or update a manifest for the import.
7. Put derived summaries in `data/processed/`.
8. Write both a reviewable CSV summary and a machine-readable `.jsonl` summary when parser support is available.
9. Create or update matching `logs/daily/YYYY-MM-DD.md` entries from objective FIT data while preserving manual notes.
10. Seed daily log stubs for past skipped planned run days so manual notes can capture why the day changed.
11. Refresh the current week summary in `README.md` from the plan plus the daily logs.
12. Update `logs/weekly/week_YYYY-MM-DD.md` with the current factual week summary.
13. Verify that summary row count matches the batch FIT count before treating the import as complete.
14. Keep current-month loose `.fit` files available for repair, reparse, or enrichment.

## AI Interaction Model

Use AI as the default operator for factual repo maintenance.

- Auto-do: FIT import, hashing, processed summaries, daily log upserts, weekly log refresh, `README.md` sync, manifest maintenance, and archive housekeeping when the rules already exist.
- Draft, then ask: weekly retros, decision records, and plan-text changes.
- Ask first: changes to durable planning assumptions, framework changes, mileage-target changes, or destructive edits to historical records.

Use this rule of thumb:

- Facts: automate.
- Interpretation: draft.
- Decisions: ask.

## Data Archive Loop

For completed prior-month COROS export batches:

1. Archive only batches whose processed summaries already exist.
2. Create `fit_files.tar.gz` inside the batch folder.
3. Verify archive membership before removing loose `.fit` files.
4. Update processed JSONL rows with `source_archive_relpath` and `source_archive_member`.
5. Remove loose `.fit` files only after archive verification succeeds.
6. Keep `manifest.md`, `SHA256SUMS.txt`, processed summaries, and `fit_files.tar.gz`.
7. Update the manifest to record archive size, member count, and that loose FIT files were removed.

## Monthly Archive Rule

- On the first repo maintenance pass of a new month, archive all completed COROS export batches from the previous month.

Use `scripts/summarize_coros_fit.py` when the optional FIT parser dependency is available.
Use `scripts/archive_coros_export.py` for batch archiving after summaries exist.

Raw FIT files may include GPS, timestamps, heart rate, and device metadata. Treat them as private training data unless you intentionally publish them.
