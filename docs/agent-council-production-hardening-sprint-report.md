# Agent Council Production Hardening Sprint Report

Date: 2026-06-20 Asia/Baku; evidence runs saved on 2026-06-19 UTC.

## 1. Worktree Clean Before Start
No. The only initial dirty item was the allowed carryover sprint plan: `docs/agent-council-production-hardening-sprint-plan.md`.

## 2. Agents Launched By Wave
- Wave 1: Evidence Trail, QA / Critic.
- Wave 2: Product Manager, Legal Language, QA / Critic.
- Wave 3: Source Monitor, Code Architect.
- VARA activation review: Evidence Trail, QA / Critic.
- VARA wording review: Product Manager, Legal Language.
- Phase 5 evidence design: Evidence Trail, Risk + Brief Pipeline.

Total fresh agents launched: 13. No old stuck agents were resumed or closed.

## 3. Task Board Changes
- `evidence-validator-hardening`: done.
- `customer-claim-truth-cleanup`: done.
- `source-summary-fresh-alert-counting`: done.
- `vara-final-source-to-25`: done.
- Added accepted tasks: `canonical-evidence-record-generator`, `evidence-record-validator`, `risk-brief-eligibility-gate`.

## 4. Bugs Found
- Fresh-alert validators did not fully enforce proof artifact presence, `source_id`, normalized hash recomputation, and safe baseline parsing.
- Source summary counted legacy active rows as readiness-supported instead of fresh-alert eligibility.
- Customer-facing UI/docs contained stale 168/24 VARA claims after activation.
- VARA enforcement page was table-shaped; the existing VARA listing adapter only handled card/link layouts.
- `source_intake` did not recognize `vara_enforcement_listing` as structured adapter content.
- Source snapshots are not canonical risk-brief evidence records.

## 5. Validators Improved
- Added shared fresh-alert validator helper.
- Fresh-alert validators now require source ID, proof path, normalized text path, SHA-256 normalized hash format, recomputed hash match, proof JSON alignment, baseline completeness, daily metadata, alert eligibility, and MONITOR_OK.

## 6. Adapters Improved
- Added `vara_enforcement_listing` adapter with VARA enforcement table extraction and card fallback.
- Added fixture coverage for enforcement cards, enforcement tables, homepage shell rejection, and source-intake structured adapter recognition.

## 7. Sources Activated
1 source: `AE-vara-enforcement`.

Current source truth: 238 enabled / 169 fresh-alert eligible / 61 evidence-library / 5 candidate / 3 remediation.

## 8. Evidence Saved
Three source-lab snapshot/proof runs were saved for `AE-vara-enforcement`; latest activation anchor is `intake-20260619T213128Z`.

Canonical evidence records added: 0. Risk briefs remain blocked until canonical `evidence-record.json` packages exist.

## 9. MONITOR_OK Added
1 source-level MONITOR_OK was added for `AE-vara-enforcement` after dry-run mass-monitor returned MONITOR_OK.

## 10. Customer Claims Changed
Yes. Product copy and docs now use 169 fresh-alert eligible sources and selected-source VARA wording. No complete UAE coverage, complete VARA coverage, legal advice, guaranteed compliance, regulator certification, perfect parsing, or never-miss claim was added.

## 11. Tests Passed
- `python3 -m compileall -q product/regradar tools`
- `python3 -m pytest product/regradar/tests -q`: 314 passed, 5 warnings.
- Fresh-alert/source-mode/daily validators passed at 169.
- UAE coverage, plan/pricing, parser quality, static-source, unvalidated-active, and UAE source-pack validators passed.
- `git diff --check` passed.

## 12. Frontend Validation
- `npm run build`: passed.
- `npm run lint`: passed with one existing TanStack Table warning, 0 errors.
- `node scripts/validate-routes.mjs`: passed.

## 13. Tasks Done
- Validator hardening.
- Customer claim truth cleanup.
- Fresh-alert source summary counting.
- VARA enforcement adapter and activation to 25 selected-source fresh-alert monitors.

## 14. Tasks Blocked
- Customer risk briefs are blocked until canonical evidence records and brief eligibility gates exist.
- DFSA, SCA, DIFC, MoF, FIU circulars, and MoJ/Gazette adapter/research tasks remain accepted but not implemented.

## 15. Next Exact Agent Task
Evidence Trail + Code Architect: create `schemas/evidence-record.schema.json` from `docs/evidence-record-spec.md` and add validator tests proving current source snapshot `proof.json` is not brief-eligible evidence.

## 16. Next Exact Adapter Task
`dfsa-publication-listing-adapter`: build a DFSA publication/guidance listing adapter with homepage-shell rejection fixtures before any live source activation.

## 17. Next Exact Evidence Task
Implement `build_risk_brief_inputs(evidence_record_id, base_dir)` to return BLOCK unless canonical `evidence-record.json` has `record_status=complete` and verified hashes/paths.

## 18. Next Exact Sales Task
Use only the 169 selected-source fresh-alert claim. Lead with CBUAE, VARA, FTA, MoE/DNFBP, and EOCN/TFS selected-source strengths; disclose DFSA/DIFC/ADGM/FIU/SCA/MoJ/MoF limits and keep the “monitoring intelligence only, not legal advice” boundary.
