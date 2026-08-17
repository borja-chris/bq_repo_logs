# Subagent Contract

Referenced from `.claude/agents/*.md`. Binding on every subagent this repo
spawns. Two failure modes motivate it: reports get garbled in transit by
output compression, and reports are occasionally fabricated at the source
(an implementer sincerely reported a test covered a behavior it did not —
only a mutation test caught it). The contract exists to make garbling
harmless and fabrication checkable.

## Rules

1. **Reports go to files.** Write the full report to a file on disk. The
   return channel (the value handed back to the dispatcher) carries ONLY a
   single status line plus the absolute path to the report file. The return
   channel is lossy — nothing load-bearing may travel through it.

2. **Evidence artifacts, not prose.** Every load-bearing claim must point at
   an artifact on disk. Generate artifacts by redirecting command output to
   a file and appending the exit code to that same file:

   ```
   cmd > artifact.txt 2>&1; echo "exit=$?" >> artifact.txt
   ```

   Asserting a result in prose ("tests pass") with no referenced artifact is
   not evidence.

3. **Falsifiable specifics.** Claims must be checkable: exact counts, exact
   filenames, line references, hashes, exact command strings. Vague success
   claims ("everything works", "fully tested", "all green") are an INVALID
   REPORT FORMAT — the dispatcher rejects the report rather than trusting
   it.

4. **Mutation evidence for data-safety tests.** Any test guarding data
   safety (dedup, idempotency, overwrite/destructive paths, ledger/state
   integrity) requires reported mutation evidence: break the implementation
   deliberately, capture the test FAILING, revert, capture it passing.
   Report both artifacts and the exact edit that was reverted. A
   data-safety test with no mutation evidence counts as unverified.

5. **PARTIAL and NOT_VERIFIED:\<what\> are legitimate outcomes.** Expected,
   not treated as failure. Reporting inability to verify is correct
   behavior; claiming verification you did not perform is a contract
   breach. Uncertainty is cheaper than a false claim.

## Artifact location

Artifacts and report files live under the session scratchpad directory the
dispatcher supplies in the prompt — the dispatcher passes an explicit
artifact directory for this purpose. Subagents must not scatter artifacts
into the repo tree, and must never leave untracked files in the repo.

Name the report for the task (`import-report.md`, `task-3-report.md`), not
bare `report.md` — the harness refuses that exact filename from a subagent,
which costs a retry mid-task. Dispatchers: name it in the brief.

## Report file format

```
STATUS: DONE | DONE_WITH_CONCERNS | BLOCKED | PARTIAL | NOT_VERIFIED:<what>
TASK: <one line, what was asked>

WHAT CHANGED
- <file>:<line> — <change>
- <file>:<line> — <change>

EVIDENCE
| artifact path                          | command              | exit |
|-----------------------------------------|----------------------|------|
| <scratch_dir>/artifact1.txt              | <exact command>      | 0    |
| <scratch_dir>/mutation_fail.txt          | <exact command>      | 1    |
| <scratch_dir>/mutation_pass.txt          | <exact command>      | 0    |

UNVERIFIED / PARTIAL
- <what wasn't checked and why>

CONCERNS
- <anything the dispatcher should scrutinize before trusting this>
```

Return channel: `STATUS: <status> — report at <absolute path>` and nothing
else.

## Dispatcher obligations

The dispatcher re-verifies load-bearing claims against the cited artifacts
before acting on them. A subagent report is never treated as evidence on
its own — it is a pointer to evidence the dispatcher checks.
