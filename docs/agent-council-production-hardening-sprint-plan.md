# Agent Council Production Hardening Sprint Plan

Date: 2026-06-20

## Current Source Truth

- Latest pushed commit before sprint: `95e172f`
- UAE enabled sources: 238
- Fresh-alert eligible daily monitors: 168
- Evidence-library sources: 61
- Candidate/pending sources: 6
- Remediation sources: 3
- Fresh-alert validator state before sprint: recently passing with `fresh_alert_count=168`
- Full test suite before sprint: recently passing with 305 tests and 5 warnings

These are monitoring-truth numbers, not complete UAE coverage claims.

## Current Task Board State

Task board: `product/regradar/config/agent_council_tasks.json`

- `evidence-validator-hardening`: `review_evidence`, owner Code Architect, next handoff Evidence Trail.
- `customer-claim-truth-cleanup`: `accepted`, owner Product Manager.
- `source-summary-fresh-alert-counting`: `proposed`, owner Code Architect.
- `vara-final-source-to-25`: `accepted`, owner Source Monitor.
- `dfsa-publication-listing-adapter`: `accepted`, owner Code Architect.
- `sca-table-download-adapter`: `accepted`, owner Code Architect.
- `fiu-circulars-public-source-investigation`: `accepted`, owner Source Monitor.
- `difc-consultation-listing-adapter`: `accepted`, owner Code Architect.
- `mof-document-publication-adapter`: `accepted`, owner Code Architect.
- `moj-gazette-official-alternative-research`: `accepted`, owner Source Monitor.
- `ruflo-safe-tooling-intake`: `accepted`, owner Security/Tooling Auditor.

## Agent Wave Schedule

Runtime constraint: Codex subagents are limited, so this sprint uses waves of one to three agents. Agents coordinate through task-board notes and handoff statuses, not hidden automation.

### Wave 1: Evidence + QA Gate

Agents:

- Evidence Trail
- QA / Critic

Task: review `evidence-validator-hardening` after the validator hardening patch.

Expected outputs:

- PASS/HOLD on the current fresh-alert validators.
- Missing evidence checks, especially canonical `evidence-record.json` gaps.
- Whether the 169 fresh-alert claim is validator-safe after VARA enforcement activation.
- What still blocks customer risk briefs.
- Exact next validator improvements.

Coordinator action:

- Add task-board notes.
- Move `evidence-validator-hardening` to `done` only if both gates pass.
- If a blocker remains, keep the task at `review_evidence`, `review_qa`, or `blocked`.

### Wave 2: Customer Claim Truth Cleanup

Agents:

- Product Manager
- Legal Language
- QA / Critic

Task: find stale or unsafe customer-facing monitoring claims and propose exact corrections.

Expected files:

- `product/regradar/web/src/components/`
- `product/regradar/web/src/data/`
- `product/regradar/app/plan.py`
- `docs/uae-source-family-scorecard.md`
- `product/regradar/web/src/data/sourceQualityAudit.ts`

Coordinator action:

- Implement only agreed Product + Legal + QA claim cleanup.
- Do not edit source activation.
- Run frontend validation if frontend files change.

### Wave 3: Source Monitor Triage

Agents:

- Source Monitor
- Code Architect

Task: prioritize adapter/source tasks and pick exactly one first implementation task.

Candidate task order:

1. `vara-final-source-to-25`
2. `dfsa-publication-listing-adapter`
3. `sca-table-download-adapter`
4. `difc-consultation-listing-adapter`
5. `mof-document-publication-adapter`
6. `fiu-circulars-public-source-investigation`
7. `moj-gazette-official-alternative-research`

Coordinator action:

- Update task board.
- Select one adapter task only for implementation.

### Wave 4: One Adapter Implementation

Default first choice: `vara-final-source-to-25`.

Rules:

- Add fixture/regression test before production implementation.
- Run failing test before implementation when feasible.
- Implement minimal adapter/fetch/selector change.
- No source becomes `fresh_alert` without proof path, normalized text path, normalized hash, baseline runs >= 2, mass-monitor dry-run, and real `MONITOR_OK`.
- If no source passes, document blocker instead of inflating counts.

### Wave 5: Evidence Record System Design

Agents:

- Evidence Trail
- Risk + Brief Pipeline

Task: design canonical evidence-record generator and no-evidence-no-brief gate.

Coordinator action:

- Add task-board entries if missing:
  - `canonical-evidence-record-generator`
  - `evidence-record-validator`
  - `risk-brief-eligibility-gate`

## Exact Task Ownership

- Chief of Staff / Coordinator: sequencing, task-board status, final validation, commit scope.
- Evidence Trail: evidence completeness and no-evidence-no-brief gate.
- QA / Critic: false claims, stale counts, validator adequacy, ship/no-ship.
- Product Manager: sellability and UI/product wording.
- Legal Language: forbidden claims and disclaimer safety.
- Source Monitor: official/public status, source-health, noise risk, adapter blocker.
- Code Architect: implementation design, adapter/validator changes, tests.
- Risk + Brief Pipeline: brief eligibility and risk scoring prerequisites.

## Expected Files Per Task

- Governance docs: `docs/agent-council-production-hardening-sprint-report.md`, this plan.
- Task board: `product/regradar/config/agent_council_tasks.json`.
- Validators: `tools/validate_fresh_signal_sources.py`, `tools/validate_source_monitoring_modes.py`, `tools/validate_daily_checkable_sources.py`, plus any new narrowly scoped validator.
- Tests: `product/regradar/tests/`.
- Claim cleanup, if approved: frontend/source audit files and docs only.
- Adapter task, if selected: one adapter family plus its tests/fixtures/docs.

## Validation Commands

Minimum:

```bash
python3 -m compileall -q product/regradar tools
python3 -m pytest product/regradar/tests -q
python3 tools/validate_fresh_signal_sources.py
python3 tools/validate_source_monitoring_modes.py
python3 tools/validate_daily_checkable_sources.py
python3 tools/validate_uae_coverage_claims.py
python3 tools/validate_plan_pricing_consistency.py
python3 tools/agent_council.py list
git diff --check
```

If frontend files change:

```bash
cd product/regradar/web
npm run build
npm run lint
node scripts/validate-routes.mjs
```

If source/adapters change:

```bash
python3 tools/validate_parser_quality.py
python3 tools/validate_no_static_sources_as_alerts.py
python3 tools/validate_no_unvalidated_active_sources.py
python3 tools/validate_uae_source_pack.py
```

## What Will Not Be Claimed

- Complete UAE coverage.
- Complete family coverage unless validators and evidence prove it.
- Legal advice.
- Guaranteed compliance.
- Perfect parsing.
- Never-miss update promises.
- Regulator certification.
- All-source coverage.
- Broad SCA/FIU/MoJ/MoF readiness beyond the documented fresh-alert counts.

## Rollback Policy

- Do not revert user changes blindly.
- If an agent produces unsafe or unrelated edits, preserve the diff for review and revert only the agent-owned files after confirming they are this sprint's runtime work.
- Do not stage runtime junk, source snapshots, secrets, `.env`, or unrelated files.
- If validation fails, keep task status honest (`blocked`, `review_qa`, or `review_evidence`) and document the exact failure before any commit.
