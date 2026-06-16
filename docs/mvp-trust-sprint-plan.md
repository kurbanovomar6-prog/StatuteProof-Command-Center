# MVP-T Trust Sprint Plan

Date: 2026-06-16

## 1. Current Product State

StatuteProof has crossed the source-readiness threshold for a controlled commercial pilot:

- 66 enabled UAE official-source endpoints.
- 62 readiness-supported sources.
- 4 sources under extraction remediation.
- Source infrastructure is strong enough for a controlled founder-led pilot.
- $199/month founding pilot is commercially justified when scope and limitations are explicit.
- $399/$749 positioning still needs stronger workflow, delivery, audit export, and source-health visibility.

The main trust risk is false confidence: a buyer must not confuse sample/mock data, no-save previews, or source-count breadth with complete legal/compliance coverage.

## 2. Top Customer Trust Gaps

1. Authenticated dashboard surfaces may still show mock/sample data or fallback sample data in ways that can confuse a real customer.
2. Reviewed brief to email delivery is not proven as a safe end-to-end test-mode pipeline.
3. Acknowledge & Assess exists as a specification, not as a saved-evidence workflow.
4. PDF/audit-pack export is not implemented as a real output.
5. Source-health and last-checked status need to be visibly present in customer-facing source views.
6. VARA source depth remains thin, but source coverage is lower priority than customer trust workflow in this sprint.

## 3. Files To Inspect

Backend:

- `product/regradar/app/api.py`
- `product/regradar/app/alert_review.py`
- `product/regradar/app/alert_routing.py`
- `product/regradar/app/weekly_brief.py`
- `product/regradar/app/source_runs.py`
- `product/regradar/app/proof.py`
- `product/regradar/app/source_certification.py`
- `product/regradar/app/source_quality.py`
- `product/regradar/app/mass_monitoring_runner.py`
- existing email/delivery modules if present

Frontend:

- `product/regradar/web/src/components/app/DashboardHome.jsx`
- `product/regradar/web/src/components/app/SourcesPage.jsx`
- `product/regradar/web/src/components/app/EvidencePage.jsx`
- `product/regradar/web/src/components/app/AlertsPage.jsx`
- `product/regradar/web/src/data/appMockData.js`
- route and API client helpers

Tests and validators:

- `product/regradar/tests/`
- `tools/validate_*`

Docs:

- `docs/what-clients-need-for-ideal-product.md`
- `docs/acknowledge-and-assess-workflow-spec.md`
- `docs/source-monitor-operational-risk-alerts.md`
- `docs/parser-quality-gates.md`

## 4. What Will Be Implemented

The target implementation is intentionally MVP-sized:

1. **Mock/sample data safety**
   - Authenticated customer-facing views should use real API data where available.
   - When sample/demo data is used, it must be clearly labeled.
   - Empty states must be honest, not filled with fake hashes or fake alerts.

2. **Safe email brief delivery test mode**
   - Create/render an email payload for approved/reviewed brief data.
   - Write to local outbox/log in test mode.
   - Include subject, disclaimer, delivery status, and failure visibility.
   - Never send real external customer email in tests.

3. **Audit-pack export MVP**
   - Implement Markdown/HTML audit-pack export first if PDF is too risky.
   - Include source, official URL, proof path/hash, normalized hash, source-health status, change summary, assessment if present, and disclaimer.
   - Clearly label sample/demo exports.

4. **Acknowledge & Assess MVP**
   - Saved evidence records only.
   - Persist assessment with impact level, note, reviewer/user id if available, timestamp, proof/hash linkage, and disclaimer.
   - Block assessments for no-save/preview/sample records.
   - Include assessment data in audit export.

5. **Source-health / last-checked visibility**
   - Source cards should show health/last checked where real data exists.
   - Remediation sources must show a reason or honest remediation state.
   - No source should look “ready” without proof/baseline support.

## 5. What Will Remain Spec-Only Or Deferred

- Real customer email sending.
- Production notification delivery.
- Full PDF styling if Markdown/HTML export is safer in this pass.
- Full multi-user workflow engine.
- Legal advice, obligation mapping, or automatic compliance determinations.
- Enterprise security features such as SSO, RBAC, retention policies, and audit-log hardening.
- Broad VARA source expansion unless the trust workflow work is already stable.

## 6. Validation Plan

Required validation before commit:

- `python3 -m compileall product/regradar`
- `python3 -m pytest product/regradar/tests -q`
- `python3 tools/validate_uae_source_pack.py`
- `python3 tools/validate_uae_50_working_sources.py`
- `python3 tools/validate_source_readiness_summary.py` if present
- `python3 tools/validate_parser_quality.py`
- `python3 tools/validate_workspace.py`
- `python3 tools/validate_codex_skills.py`
- `git diff --check`

If frontend is touched:

- `cd product/regradar/web && npm run build`
- `cd product/regradar/web && npm run lint`
- `cd product/regradar/web && node scripts/validate-routes.mjs`
- `cd product/regradar/web && node scripts/pre-demo-smoke.mjs` if present

New or updated tests should cover:

- No unlabeled sample data in authenticated surfaces.
- Test-mode email payload and status persistence.
- Audit export includes proof/hash/disclaimer.
- Assessment cannot be created without saved evidence/proof.
- Assessment links to evidence and export.
- Source card status/last-checked/remediation visibility.

## 7. Commit Policy

If validation passes:

- Stage only task files.
- Do not stage secrets, runtime junk, unrelated files, or generated evidence artifacts unless deliberately created as test fixtures.
- Commit with:
  - `feat: implement StatuteProof MVP trust workflow`
- Push to `origin/main`.

If validation fails:

- Do not commit broken code.
- Report exact failures and the next fix.

