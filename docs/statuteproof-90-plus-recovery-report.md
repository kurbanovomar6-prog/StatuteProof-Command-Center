# StatuteProof 90+ Recovery Report

Date: 2026-06-21

## 1. Starting Audit Score

External CTO audit starting score: 52/100.

## 2. Ending Internal Score

Honest internal score after this sprint: 64/100.

Confidence: medium-high.

This sprint materially improved the evidence and brief gates, but the product is not 80+ or 90+ yet. The remaining blockers are real: no production canonical evidence-record corpus, no completed real customer brief, no human review UI, no Stripe/payment conversion, no real paying customer evidence, and no production uptime/deployment automation.

## 3. Agents Launched

- `multi_agent_v1` Evidence Trail spawn attempted: blocked by `agent thread limit reached`.
- `claude-flow` Evidence Trail registered: not counted as usable execution because it only registered a worker.
- Fresh `claude -p --no-session-persistence` Evidence Trail audit: completed and produced one usable handoff packet.

Usable handoff packets exchanged: 1.

## 4. P0 Blockers Fixed

1. Canonical evidence writer missing:
   - Added `create_canonical_evidence_record()` in `product/regradar/app/evidence_records.py`.
   - The writer copies saved source-run artifacts from `data/source_snapshots` into append-only `evidence/{regulator}/{source_id}/{run_id}/`.
   - It rejects missing proof, missing normalized artifacts, hash mismatch, `FAILED`, `QUALITY_DROP`, and non-`FIRST_SEEN` records without previous normalized evidence.

2. Weekly brief path bypassed canonical evidence:
   - `collect_approved_alerts()` now excludes approved alerts without an eligible canonical `evidence_record_id`.
   - Added `build_evidence_backed_brief_draft()` for non-delivery drafts from approved canonical evidence only.
   - Source snapshot `proof.json` remains blocked from customer brief eligibility.

3. FTA customer-facing inconsistency:
   - Updated customer-facing copy to distinguish 25 active direct official FTA tax PDF endpoints from broader FTA portal/listing extraction that remains adapter/roadmap work.

## 5. P0 Blockers Remaining

1. No production canonical evidence records were backfilled or committed.
2. No real customer brief has completed the full production delivery path.
3. No founder-facing human review UI was implemented in this sprint.
4. Delivery approval remains explicit and blocked by default.
5. 90+ GTM score is impossible without a real paying or design-partner pilot.

## 6. P1 Improvements Completed

1. Operator-only source health report:
   - Added `build_operator_source_health_report()`.
   - Flags sources with 3+ consecutive failed/quality-drop/access-blocked runs.
   - Does not send email, Telegram, or customer-facing alerts.

2. Preflight orchestration:
   - Added `tools/run_statuteproof_preflight.py`.
   - Runs backend tests, compileall, source validators, parser validators, frontend build/lint/routes.
   - No deployment, SSH, production sync, or secrets.
   - GitHub Actions workflow creation was attempted but could not be pushed because the current OAuth token lacks `workflow` scope.

## 7. Evidence Writer Status

Implemented and fixture-tested.

Canonical evidence records created in committed production data: 0.

Fixture tests create and validate canonical `evidence-record.json` packages under temporary test directories.

## 8. End-to-End Brief Path Status

Partially implemented and tested.

The path now proves:

- no canonical evidence record = no weekly brief inclusion
- pending canonical evidence = no brief draft
- approved canonical evidence = draft can be built
- forbidden legal phrases block draft creation
- draft is not customer delivery
- `delivery_approved` remains false by default

Not yet done:

- no real customer brief delivered
- no production review UI
- no production evidence corpus

## 9. FTA Consistency Status

Fixed across:

- `product/regradar/web/src/components/Coverage.jsx`
- `product/regradar/web/src/components/BuyerSourcePacks.jsx`
- `product/regradar/web/src/data/sourceQualityAudit.ts`
- `product/regradar/reports/source_signal_quality_audit.json`
- `product/regradar/reports/source_signal_quality_audit.md`

Current safe distinction: 25 direct official FTA tax PDF endpoints are fresh-alert eligible; broader FTA portal/listing extraction remains candidate/adapter work.

## 10. Failed-Run Alerting Status

Implemented as operator-only report logic.

Not implemented:

- no external notifications
- no uptime monitor
- no PagerDuty/Telegram/email send

## 11. CI / Validator Orchestration Status

Added local preflight orchestration.

It validates tests and source-truth gates but does not deploy.

GitHub Actions remains a blocked next task until a credential with `workflow` scope can add `.github/workflows/*`.

## 12. Source-Family Changes

Sources activated: 0.

MONITOR_OK added: 0.

Source truth unchanged:

- 241 enabled UAE sources
- 172 fresh-alert eligible
- 61 evidence-library
- 5 candidate
- 3 remediation

## 13. Customer Claims Changed

Yes.

Changed only to make FTA wording more precise. No complete coverage, perfect parsing, legal advice, certification, guaranteed compliance, or never-miss claim was added.

## 14. Tests Added

Added/updated tests for:

- canonical evidence writer creation
- canonical writer hash mismatch rejection
- failed/quality-drop canonical writer rejection
- missing proof rejection
- evidence-backed brief draft blocking pending records
- evidence-backed draft non-delivery status
- forbidden legal phrase blocking
- weekly brief exclusion without canonical evidence
- operator-only failed-run health report

## 15. Validation Results

Passed:

- `python3 -m compileall -q product/regradar tools`
- `python3 -m pytest product/regradar/tests -q` -> 350 passed, 5 warnings
- `python3 tools/validate_fresh_signal_sources.py`
- `python3 tools/validate_source_monitoring_modes.py`
- `python3 tools/validate_daily_checkable_sources.py`
- `python3 tools/validate_uae_coverage_claims.py`
- `python3 tools/validate_plan_pricing_consistency.py`
- `python3 product/regradar/reports/validate_audit.py`
- `python3 tools/validate_parser_quality.py`
- `python3 tools/validate_no_static_sources_as_alerts.py`
- `python3 tools/validate_no_unvalidated_active_sources.py`
- `python3 tools/validate_uae_source_pack.py`
- `python3 tools/validate_fresh_signal_25_per_family.py`
- `python3 tools/agent_council.py list`
- `git diff --check`
- `python3 tools/run_statuteproof_preflight.py` -> added as local orchestrator; equivalent commands were run individually in this sprint

Frontend:

- `npm run build` -> passed
- `npm run lint` -> passed with one existing TanStack Table React Compiler warning in `DashboardPreview.jsx`
- `node scripts/validate-routes.mjs` -> passed

## 16. Exact Path To 80+

1. Generate 10 real canonical evidence records from current saved source runs without broad backfill.
2. Add a minimal founder review UI for pending alerts and canonical evidence.
3. Run one full non-customer delivery cycle: source run -> canonical evidence -> alert -> review -> draft -> legal scan -> delivery blocked/approved state.
4. Add operator UI or scheduled report for failed-run health.
5. Add GitHub Actions with a token that has workflow scope, then keep CI green on every push.

## 17. Exact Path To 90+

1. Complete the 80+ path.
2. Deliver one real pilot brief under explicit pilot terms.
3. Add Stripe or a clean manual-to-paid conversion path.
4. Add uptime monitoring and deployment automation.
5. Add adapter health visibility by source/family.
6. Complete at least one real design-partner feedback loop.

90+ still requires real customer evidence, not only engineering.

## 18. Next Exact Engineering Task

Create a controlled command to generate canonical evidence records for 5-10 selected saved source runs, with dry-run mode, no overwrite, and a review report.

## 19. Next Exact Evidence Task

Evidence Trail review of the first real canonical evidence records created from production source snapshots.

## 20. Next Exact Product Task

Build a minimal founder review page for canonical evidence-backed alerts: list, inspect evidence, approve/reject, annotate, and keep delivery blocked unless explicitly approved.

## 21. Next Exact Source Task

Run operator source-health report on current `source_runs.jsonl` and document any source with 3+ consecutive failures.

## 22. Next Exact Sales Task

Do not sell as production. Prepare a pilot-only offer that says: selected-source UAE monitoring, evidence-backed draft briefs, human review required, no legal advice, no complete coverage claim.
