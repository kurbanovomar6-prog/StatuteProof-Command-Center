#!/bin/bash
# ECC review gate (introduced 2026-07-10 after the VARA incident review).
#
# Blocks `git push` from Claude Code unless the commit being pushed has been
# ECC-reviewed and explicitly approved. Approval = the HEAD sha (of the repo
# root or any linked worktree) is listed in .claude/.review-approved.
#
# To approve after running ECC review agents (code-reviewer + security-reviewer
# + language reviewer) and addressing CRITICAL/HIGH findings:
#   git rev-parse HEAD >> .claude/.review-approved
#
# Exit codes: 0 = allow, 2 = block (stderr is shown to the model).

input=$(cat)
command=$(printf '%s' "$input" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

case "$command" in
  *"git push"*|*"git -C"*" push"*) ;;
  *) exit 0 ;;
esac

root="${CLAUDE_PROJECT_DIR:-$(pwd)}"
marker="$root/.claude/.review-approved"

# Candidate HEADs: main checkout + every linked worktree (pushes may run there)
heads=$(git -C "$root" worktree list --porcelain 2>/dev/null | awk '/^HEAD /{print $2}')
[ -z "$heads" ] && heads=$(git -C "$root" rev-parse HEAD 2>/dev/null)

if [ -f "$marker" ]; then
  for h in $heads; do
    if grep -q "$h" "$marker" 2>/dev/null; then
      exit 0
    fi
  done
fi

{
  echo "[review-gate] BLOCKED: git push requires ECC review approval."
  echo "[review-gate] Run the ECC review agents (code-reviewer, security-reviewer,"
  echo "[review-gate] language reviewer) on the commits being pushed, address"
  echo "[review-gate] CRITICAL/HIGH findings, then approve the reviewed HEAD:"
  echo "[review-gate]   git rev-parse HEAD >> .claude/.review-approved"
} >&2
exit 2
