# Week of 2026-07-19 Work-Session Retro

## Label

- This is a work-session retrospective, not a training retrospective.

## Summary

- Ingested the 7/14 and 7/17 runs. The 7/14 run (5.76 mi, 92°F) was notably slower than surrounding runs, which surfaced a gap: the repo captures raw temperature/humidity via Open-Meteo enrichment (see `retros/block/2026-06-07_coros_weather_work_retro.md`) but has no derived heat-index or heat-risk signal, and no flag on activities imported under high heat.

## What Did Not Work

- No process exists to translate temp+humidity into a felt-like heat index or to flag a run as heat-affected. Interpretation of hot runs is currently manual and easy to miss during import.

## Follow-Up

- Design question to resolve before implementation: should the heat index be computed and stored per-activity in the processed JSONL (a data change), surfaced only as a README/weekly-log flag (a presentation change), or both? Decide scope before starting.

## Action Item

- Owner: Claude (Tech Lead)
- Action: Add a heat-index computation to the ingest pipeline — derive a felt-like heat index from the existing Open-Meteo temp/humidity fields already captured per activity, and flag activities above a defined threshold (e.g., in `data/processed/*.jsonl` and/or the daily-entry note in the weekly log).
- Success condition: A new COROS import of an activity recorded above the heat threshold automatically carries a visible heat-index value/flag through to the weekly log, with no manual note required to surface it.
- Status: Open — not started. Threshold value deferred to a future session.
