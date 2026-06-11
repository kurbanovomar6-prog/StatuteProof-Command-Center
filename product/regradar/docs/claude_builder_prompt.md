# Claude Builder Prompt Template — RegRadar

Use this as a base for future implementation tasks.
Fill in the [TASK] sections before sending.

---

```
Act as a strict Senior Product Engineer for RegRadar.

## Task

[DESCRIBE THE SPECIFIC TASK HERE — e.g.
"Add a mailto fallback to the Contact form if /api/contact returns a non-ok response."
"Build a [feature] section on the landing page."]

## Context

RegRadar is a B2B regulatory monitoring platform for fintech, crypto, payments,
banking, legal, compliance and consulting teams.

Latest commit: [PASTE LATEST HASH — e.g. 1c5a905]

Current relevant state: [SHORT DESCRIPTION — e.g.
"Contact form currently submits to /api/contact but no backend route confirmed.
Watchlist-to-contact flow is wired. build passing. No overclaims."]

## Rules

- Do NOT add new countries or sources.
- Do NOT modify sources.json unless this task explicitly requires it.
- Do NOT change backend monitoring logic unless this task explicitly requires it.
- Do NOT add auth or billing.
- Do NOT run long source audits.
- Do NOT send Telegram.
- Do NOT call AI.
- Do NOT write monitoring history.
- Do NOT add features beyond what is described above.
- Keep copy honest: no complete coverage claims, no legal advice claims.

## Expected scope

[LIST EXPECTED FILES — e.g.
- web/src/components/Contact.jsx
- web/src/App.jsx (if state changes needed)]

## Validation

Run after implementation:
.venv/bin/python -m compileall app run.py -q
cd web && npm run build

Run overclaim scan:
grep -rni "complete coverage\|global coverage\|all regulations\|never miss\|guaranteed compliance\|legal advice\|replaces lawyers\|fully automated compliance\|all jurisdictions" web/src/

## Output

Return:
- Files changed
- What was implemented
- Validation results (compileall, npm build)
- Overclaim scan result
- Commit hash
- Push status
- Remaining TODOs if any
- Update HANDOFF.md before finishing
```

---

## Notes on using this template

**Do not paste huge context.** Claude already knows the codebase if you're in the same session.
If starting a new session, attach HANDOFF.md or read it first.

**One task per prompt.** Bundling unrelated work leads to messy commits and harder Codex review.

**Validation is mandatory.** Always ask Claude to validate before committing.

**After Claude commits:** switch to Codex using `docs/codex_review_prompt.md`.
