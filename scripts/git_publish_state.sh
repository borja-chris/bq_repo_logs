#!/usr/bin/env bash
#
# One line naming what is NOT yet on GitHub: tracked files with uncommitted
# changes, and local commits not yet pushed. Silent when everything is pushed.
#
# Shared by ingest.sh (footer) and the UserPromptSubmit hook, so "synced" is
# never mistaken for "published" (2026-10-17: README "missing" on GitHub was
# simply unpushed). Reads the local upstream ref only -- no fetch; git push
# updates it, so it is current for pushes made from this machine.
set -uo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 0
dirty=$(git diff --name-only HEAD 2>/dev/null)
ahead=$(git rev-list --count "@{u}..HEAD" 2>/dev/null || echo 0)
[[ -z "${dirty}" && "${ahead}" == 0 ]] && exit 0

n=$(printf '%s\n' "${dirty}" | grep -c . || true)
files=$(printf '%s\n' "${dirty}" | head -4 | paste -sd, -)
(( n > 4 )) && files+=", +$((n - 4)) more"
echo "NOT ON GITHUB: ${n} uncommitted tracked file(s)${files:+ (${files})}; ${ahead} unpushed commit(s)."
