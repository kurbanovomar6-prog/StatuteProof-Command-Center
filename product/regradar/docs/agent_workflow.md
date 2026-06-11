# Claude + Codex Workflow for RegRadar

## Purpose

Claude builds. Codex reviews.

This document explains how to use both agents safely on the same Git repository without conflicts or token waste.

---

## The correct sequence

```
1. Human plans task (with ChatGPT or alone)
        ↓
2. Human opens Claude → gives implementation task
        ↓
3. Claude implements → validates → commits → pushes
        ↓
4. Claude updates HANDOFF.md → tells human "ready for Codex"
        ↓
5. Human opens Codex → pastes codex_review_prompt.md → Codex audits
        ↓
6. Codex fixes only real issues → commits if needed → pushes
        ↓
7. Codex returns short summary (verdict + files + hash + risks)
        ↓
8. Human pastes short summary to Claude (not full log)
        ↓
9. Repeat
```

---

## What Claude does

- Implement new features
- Add frontend sections
- Build source packs (after validation)
- Update product copy
- Wire state flows
- Keep build passing
- Keep copy honest (no overclaims)
- Update HANDOFF.md after each task

## What Codex does

- Audit the latest commit
- Run build and backend checks
- Check for broken links, dead state, missing error handling
- Identify overclaims or copy drift
- Fix small real issues
- Do NOT add features
- Do NOT add sources
- Do NOT rewrite architecture

---

## Forbidden patterns

| What | Why |
|------|-----|
| Claude and Codex editing same files simultaneously | Git conflicts, logic mismatch |
| Starting from a dirty git tree | Risk of committing unrelated changes |
| Pasting full Codex log into Claude | Token waste, context pollution |
| Treating `source_candidates.json` as active coverage | It is planning only |
| Committing generated report artifacts | Noise, not signal |
| Adding sources without health validation | Source count ≠ coverage |

---

## Token and cost guidance

Codex runs do NOT spend Claude tokens unless you paste Codex output into Claude.

When switching from Codex back to Claude, paste only:

```
Verdict: PASS / PARTIAL / FAIL
Files changed: [list]
Tests: compileall OK, npm build OK
Commit: abc1234
Remaining risks: [short list]
```

Do not paste full Codex terminal output. Do not paste full diffs.

---

## Before switching agents

Always run:

```bash
cd /Users/kurbnovomar/документы/obsidian/ruflo/regrada/regradar
git status          # must be clean
git pull            # must be up to date
git log --oneline -5
```

If dirty: resolve before switching.

---

## After each completed task

```bash
# Backend check
.venv/bin/python -m compileall app run.py -q

# Frontend check
cd web && npm run build

# Overclaim scan
grep -rni "complete coverage\|global coverage\|all regulations\|never miss\|guaranteed compliance\|legal advice\|replaces lawyers\|fully automated compliance\|all jurisdictions" web/src/

# Git state
git status
git diff --stat
```

---

## Recommended prompt patterns

See:
- `docs/claude_builder_prompt.md` — template for Claude implementation tasks
- `docs/codex_review_prompt.md` — ready-to-copy Codex audit prompt

---

## When the same file needs changes from both agents

1. Claude finishes and commits first
2. Codex pulls, then audits
3. If Codex needs to change the same file: small targeted fix only, then commit
4. Claude pulls before next session

Never merge manually — let Git handle it via sequential commits.
