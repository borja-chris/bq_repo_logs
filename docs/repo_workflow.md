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
- Treat `logs/weekly/week_YYYY-MM-DD.md` as the only active log for the week.
- Keep the weekly summary at the top of that file and append daily entries below it.

During the week:

- Append daily entries to the active weekly log only when there is useful signal.
- Record distance, effort, soreness, sleep/stress, and warning signs.
- Use daily-entry manual notes for context that FIT data cannot capture, including run quality, travel fatigue, shortened runs, and skipped-run reasons.
- When a new `.fit` import is being requested and the user supplies subjective notes in the same turn, persist them into the matching daily entry during that import workflow instead of expecting a separate later edit.
- Do not create standalone daily log files or backfill noise just to make the repo look complete.
- If repo Markdown changed, run `.venv/bin/python scripts/check_markdown_links.py` before commit.
- If the live current week changed, check whether `README.md` needs a matching summary update before commit/push.
- Before updating live current-week status in `README.md`, verify the active weekly log first, then `data/processed/` if a COROS import may have landed before the Markdown was updated.
- When a request could mean either a training retrospective or a work-session retrospective, label it explicitly before writing.

After each week:

- Add one weekly retro in `retros/weekly/`.
- Capture what changed, what was skipped, and what recovery signals said.
- Feed repeated patterns into `sources/04_planning_rules_and_retro.md`.
- Preserve the distinction between facts, inference, and coaching opinion when writing adjustments or retros.

## File Naming

- Active weekly log: `logs/weekly/week_YYYY-MM-DD.md`
- Historical daily log month folder: `logs/daily/YYYY/YYYY-MM/`
- Historical daily log: `logs/daily/YYYY/YYYY-MM/YYYY-MM-DD.md`
- Historical monthly daily summary: `logs/daily/YYYY/YYYY-MM/monthly_summary.md`
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
2. Run `.venv/bin/python scripts/ingest_coros_fit.py`.
3. If the user supplied same-turn subjective notes for the run, pass them into the ingest command with `--manual-note`, `--sleep`, `--soreness`, `--stress`, and `--warning-signs` so they are written into the active weekly log immediately.
4. Let the script move those files into `data/coros_exports/COROS_export_YYYY-MM-DD/` for the import date.
5. Do not keep `*:Zone.Identifier` files.
6. Add or update `SHA256SUMS.txt` for the loose `.fit` files.
7. Add or update a manifest for the import.
8. Put derived summaries in `data/processed/`.
9. Write a `.jsonl` summary when parser support is available.
10. Create or update matching daily-entry blocks inside `logs/weekly/week_YYYY-MM-DD.md` from objective FIT data while preserving manual notes.
11. Seed daily-entry stubs for past skipped planned run days so manual notes can capture why the day changed.
12. Refresh the current week summary in `README.md` from the plan plus the weekly log.
13. Update `logs/weekly/week_YYYY-MM-DD.md` with the current factual week summary.
14. Verify that summary row count matches the batch FIT count before treating the import as complete.
15. Keep current-month loose `.fit` files available for repair, reparse, or enrichment.

## AI Interaction Model

Use AI as the default operator for factual repo maintenance.

- Auto-do: FIT import, hashing, processed summaries, weekly log upserts, `README.md` sync, manifest maintenance, and archive housekeeping when the rules already exist.
- Auto-do: when the user supplies subjective notes in the same turn as a FIT import request, persist those notes into the matching daily entry during the import command instead of leaving them in chat only.
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

- On the first repo maintenance pass of a new month, archive all completed COROS export batches from the previous month. This remains a separate manual step for now.
- Prior-month daily-log archiving is automatic: every `scripts/ingest_coros_fit.py` run calls `scripts/monthly_archive.py`, which moves any loose prior-month `logs/daily/YYYY-MM-DD.md` files into `logs/daily/YYYY/YYYY-MM/` and regenerates that month's `monthly_summary.md`. It is idempotent — if no loose prior-month files exist (the normal case, since daily entries live inside weekly logs from mid-June 2026 onward), it is a no-op. Pass `--no-archive` to `ingest_coros_fit.py` to skip it for a single run.
- Current-week sync must still read and update archived historical daily logs when a week spans a month boundary.

Use `.venv/bin/python scripts/summarize_coros_fit.py` when the optional FIT parser dependency is available.
Use `.venv/bin/python scripts/archive_coros_export.py` for batch archiving after summaries exist.

Raw FIT files may include GPS, timestamps, heart rate, and device metadata. Treat them as private training data unless you intentionally publish them.
