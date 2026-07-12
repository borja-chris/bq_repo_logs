# Decision Gate - 2026-07-11

## Decision

Add a generated whole-block overview, `plans/2026-half-marathon/BLOCK_OVERVIEW.md`, built by a new `scripts/block_overview.py` from the per-week files. Fix the reorg regression that left `scripts/weekly_plan.py` pointing at the old plan-root path instead of `weeks/`.

## Facts

- After the 2026-07-11 plan-file reorg (see `2026-07-11_plan_file_reorg.md`), the day-by-day plan lives only in 18 separate `weeks/week_YYYY-MM-DD.md` files. The block arc — mileage ramp, down weeks, and workout rhythm — is not visible without opening every file.
- `scripts/weekly_plan.py:parse_week_file` still resolved `PLAN_DIR / week_*.md`, but the reorg moved the files into `weeks/`. It returned `None` for every in-block date, so `ingest_coros_fit.py:load_week_plan` would `SystemExit("No week plan found")` for any run on or after 2026-08-03. This regression was undetected because tests stub the parser.
- The reorg decision already anticipated a rollup view: "regenerating a concatenated full-plan view, if ever wanted, becomes a mechanical rollup of `weeks/` rather than a maintained copy."

## Preference

Single source of truth over managed duplication. Keep every plan edit in the week files; derive the overview instead of hand-maintaining a second copy that would drift.

## Risk

`BLOCK_OVERVIEW.md` is generated and carries a `do not edit by hand` banner, so it cannot silently diverge from the week files. The cell-compression tags (`LR`, `HMP`, `str`, `thr`, `spd`, `strd`, `ez`) are a lossy summary; the week file remains authoritative for exact reps and notes. `check_markdown_links.py` and the 38-test suite pass after the parser fix.

## Adaptation

- `scripts/block_overview.py` reads `weeks/*.md` via the shared `weekly_plan` parser and emits two tables: a weeks-x-days grid (leading mileage plus a short workout tag, SOS days bolded, race day as `RACE`) and a block-arc index (target, week-over-week delta from target midpoints, long run, SOS days, purpose).
- `scripts/weekly_plan.py` now resolves week files under `WEEKS_DIR = PLAN_DIR / "weeks"`, restoring the COROS import's plan lookup.
- `README.md` links the generated overview from the plan-file map.

Regenerate with `python scripts/block_overview.py` after any week-file edit.

## Final Call

Proceed. The overview restores the at-a-glance picture lost in the reorg without reintroducing a maintained duplicate, and the same change fixes a live regression in the import path.
