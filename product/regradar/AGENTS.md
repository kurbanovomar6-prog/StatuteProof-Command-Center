# RegRadar — Agent Instructions

Read this before writing a single line of code.

---

## Project

RegRadar is an English-first B2B regulatory monitoring platform for fintech, crypto, payments, banking, legal, compliance and consulting teams.

It monitors official regulatory sources across emerging and developing markets and delivers risk-ranked AI compliance briefs, source proof, and pilot watchlists.

---

## Product principles

- Actionable regulatory intelligence — not "we parse X websites"
- Source proof on every alert
- Coverage transparency — limitations are documented honestly
- Custom pilot watchlists per client profile
- No claims of complete, global, or legal coverage
- No legal advice claims
- No "never miss anything" or "guaranteed compliance" language
- Limitations must appear near coverage claims

---

## Agent roles

| Agent | Role |
|-------|------|
| Claude Code | Builder — features, frontend, source packs, product engineering |
| Codex | Reviewer — QA, regression audit, safe refactor, bug fixes after Claude commits |

**Work must be sequential. Do not edit the same files from two agents simultaneously.**

---

## Before starting any task

```bash
git status          # must be clean
git pull            # must be up to date
git log --oneline -5
```

If the tree is dirty: commit or revert first, or get explicit human approval to proceed dirty.

---

## Safety rules

- Never modify `sources.json` unless activating a real validated source
- `source_candidates.json` is planning only — not production coverage
- Do not claim a source is monitored unless it is in `sources.json` and passes health check
- Do not add sources without testing with `run.py health` or `run.py adapter-queue`
- Do not commit generated report artifacts (see Generated Artifacts below)
- Do not call AI or send Telegram during validation runs
- Do not write monitoring history during tests
- Do not fake command output
- Do not expose secrets or `.env` values
- Do not push to main without validation passing

---

## Validation commands

Run after every task, before commit:

```bash
# Backend
.venv/bin/python -m compileall app run.py -q
.venv/bin/python run.py health      # only if explicitly required — takes minutes

# Frontend
cd web && npm run build
```

Optional (only if task touches coverage):
```bash
.venv/bin/python run.py coverage --json
.venv/bin/python run.py adapter-queue
```

---

## Generated artifacts — do NOT commit

```
reports/discover_source_*.json
reports/source_audit_*.json
reports/coverage_*.json
reports/coverage_*.html
reports/coverage_plan_*.json
reports/coverage_plan_*.html
```

These are already in `.gitignore`. If they appear as tracked/modified after a run, restore with `git restore`.

---

## Git hygiene

```bash
git diff --stat     # review before staging
git add <specific files only>
git commit -m "type(regradar): short description"
git push origin main
```

- Commit only files relevant to the task
- Keep commits small and meaningful
- Do not use `git add -A` or `git add .` without reviewing what's staged
- Validate before commit, not after

---

## Handoff

After finishing: update `HANDOFF.md`, commit, push, tell the human to switch agents.
