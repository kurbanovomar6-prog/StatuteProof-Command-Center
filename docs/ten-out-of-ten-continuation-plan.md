# StatuteProof 10/10 Continuation Plan

Date: 2026-06-14

## 1. Files Already Created

Recovered untracked files from the interrupted 10/10 task:

1. `docs/ten-out-of-ten-execution-plan.md`
2. `docs/ten-out-of-ten-agent-tool-use-plan.md`
3. `docs/ten-out-of-ten-context-review.md`
4. `docs/ten-out-of-ten-scorecard.md`
5. `docs/website-app-ux-10-10-review.md`
6. `docs/parser-source-lab-10-10-review.md`
7. `docs/dfsa-10-10-remediation-plan.md`
8. `docs/dfsa-10-10-remediation-report.md`

`git diff --stat` is empty because these files are new/untracked.

## 2. What The Previous Thread Completed

- Passed the clean-state gate from commit `64eea4f`.
- Read the P0 sprint reports and current code surfaces.
- Confirmed current source-readiness truth remains 13 enabled UAE sources / 9 readiness-supported / 4 remediation.
- Created the initial 10/10 execution plan and agent/tool-use plan.
- Created grounded review docs for context, scorecard, website/app UX, parser/Source Lab, and DFSA remediation.
- Identified safe fix candidates:
  - stale `EvidencePage.jsx` header comment;
  - missing workflows for pre-demo, first paid pilot, evidence baseline, and GitHub safe adoption;
  - missing final review artifacts;
  - possible validator/report hardening.

## 3. What Remains

- Read and complete all existing 10/10 artifacts.
- Create missing review reports:
  - GitHub/open-source research notes;
  - proof-backed sample brief QA;
  - browser auth/session smoke report;
  - billing/manual activation review;
  - security/data hygiene review;
  - tests/validators review;
  - agents/workflows review;
  - final gate review;
  - final execution report.
- Implement only safe scoped fixes after the reviews exist.
- Run focused validation and commit/push if passing.

## 4. What This Continuation Will Do

1. Inspect the recovered docs and avoid duplicates.
2. Complete missing docs with actual code/report evidence.
3. Add small workflow/docs improvements where clearly useful.
4. Apply small code/comment/validator fixes only if safe.
5. Attempt focused browser smoke if local servers can run; otherwise document limitation.
6. Run validation:
   - `python3 -m compileall product/regradar`
   - targeted parser/auth/brief tests if relevant
   - `python3 tools/validate_parser_quality.py`
   - `python3 tools/validate_workspace.py`
   - `python3 tools/validate_codex_skills.py`
   - frontend build/lint/routes if frontend touched
   - `git diff --check`
7. Stage only files from this continuation task and push if validation passes.

## 5. Files Likely To Change

Docs/reports:

- `docs/ten-out-of-ten-github-research.md`
- `docs/proof-backed-sample-brief-10-10-qa.md`
- `docs/browser-auth-plan-smoke-report.md`
- `docs/billing-manual-activation-10-10-review.md`
- `docs/security-data-hygiene-10-10-review.md`
- `docs/test-validator-10-10-upgrade-report.md`
- `docs/agents-workflows-10-10-review.md`
- `docs/ten-out-of-ten-final-gate-review.md`
- `docs/ten-out-of-ten-execution-final-report.md`

Workflows:

- `workflows/09-pre-demo-readiness-gate.md`
- `workflows/10-first-paid-pilot-readiness.md`
- `workflows/11-source-baseline-and-evidence-save.md`
- `workflows/12-github-research-and-safe-adoption.md`

Possible safe code/tool fixes:

- `product/regradar/web/src/components/app/EvidencePage.jsx`
- `tools/validate_parser_quality.py`

## 6. Validation Plan

Run from root:

```bash
git status --short
python3 -m compileall product/regradar
python3 -m pytest product/regradar/tests/test_source_intake.py product/regradar/tests/test_auth_plan_contracts.py product/regradar/tests/test_weekly_brief.py -q
python3 tools/validate_parser_quality.py
python3 tools/validate_workspace.py
python3 tools/validate_codex_skills.py
git diff --check
```

Run from frontend if a frontend file changes:

```bash
cd product/regradar/web
npm run build
npm run lint
node scripts/validate-routes.mjs
```

## 7. Commit Plan

If only docs/workflows change:

```bash
git commit -m "docs: complete StatuteProof 10-10 readiness review"
```

If safe code/tool fixes are made and validation passes:

```bash
git commit -m "fix: continue StatuteProof 10-10 readiness improvements"
```

Stage only files created or modified by this continuation. Do not stage runtime data, reference repos, `.env`, secrets, or unrelated files.
