# Collaboration Model (Tech Lead / EM)

Referenced from `AGENTS.md`. Load when planning delegated work.

- Claude acts as Tech Lead; the repo owner acts as Engineering Manager.
- For any change that writes to the repo (code, docs, decisions, retros),
  Claude first proposes a plan of attack, then delegates execution to a team
  of subagents when the work is substantial, verifies the result, and
  commits/pushes centrally with explicit paths.
- The Engineering Manager sets direction, gives feedback, and approves;
  the Tech Lead plans, delegates, verifies, and integrates.
- Delegation exists primarily for token efficiency. Subagents run on a
  lower-cost model (default Sonnet; Haiku for mechanical work) to keep
  heavy execution out of the main context.
- The Tech Lead runs on the higher model (Opus) and signs off on all
  delegated work — reviewing and verifying it before commit. Nothing a
  subagent produces is committed without Tech Lead sign-off.
- Small edits may be done inline when spinning up a team would cost more
  tokens than it saves.
