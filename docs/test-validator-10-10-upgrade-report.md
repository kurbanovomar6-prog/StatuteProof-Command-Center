# Test and Validator 10/10 Upgrade Report

## 1. Current Validator Coverage

Existing validators cover:

- workspace structure
- Codex skill format/safety
- parser quality files and unsafe customer-facing parser claims
- frontend route registry
- Python compile checks
- frontend build/lint

The P0 sprint reported 86 Python tests passing, parser quality passing, frontend build passing, lint passing with one existing warning, and route/workspace/skills/diff checks passing.

## 2. Remaining Validator Gaps

| Gap | Severity | Recommended action |
|---|---:|---|
| Sample brief label/proof guard | P1 | Add parser-quality validator check for the proof-backed sample brief |
| Runtime alert queue tracked history | P1 | Existing tracked alert queue JSON should be reviewed in a separate cleanup, not silently deleted in this task |
| Browser smoke automation | P1 | Add a dedicated browser smoke script after local server behavior is stable |
| Source readiness constants duplicated | P1 | Add a canonical readiness summary generator or shared fixture |
| Billing manual activation copy guard | P2 | Add copy checks if plan pages change frequently |

## 3. Changes In This Run

Planned and implemented in this continuation:

- Harden `tools/validate_parser_quality.py` to verify the proof-backed sample brief remains unmistakably labeled as sample/demo and includes proof/hash/not-legal-advice references.

Not implemented in this pass:

- A failing check for tracked historical runtime alert queue JSON. Those files already exist in the repository and should be handled in a separate cleanup with owner approval.
- Full browser smoke script committed to the repo. Browser smoke was attempted and documented separately.

## 4. Validation Commands

Required commands for this continuation:

```bash
python3 -m compileall product/regradar
python3 tools/validate_parser_quality.py
python3 tools/validate_workspace.py
python3 tools/validate_codex_skills.py
git diff --check
```

If frontend files are touched:

```bash
cd product/regradar/web
npm run build
npm run lint
node scripts/validate-routes.mjs
```

## 5. Next Exact Task

Create a committed browser smoke test that exercises login, register, protected-route redirect, onboarding, billing/manual activation copy, Source Lab, and evidence sample labels.
