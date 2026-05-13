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

1. Put raw FIT files under `data/coros_exports/COROS_export_YYYY-MM-DD/`.
2. Do not keep `*:Zone.Identifier` files.
3. Add or update a manifest for the import.
4. Add hashes for dedupe.
5. Put derived summaries in `data/processed/`.

Use `scripts/summarize_coros_fit.py` when the optional FIT parser dependency is available.

Raw FIT files may include GPS, timestamps, heart rate, and device metadata. Treat them as private training data unless you intentionally publish them.
