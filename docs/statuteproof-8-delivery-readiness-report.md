# StatuteProof 8/10 Delivery Readiness Report

Date: 2026-06-21

## Verdict

This sprint moved StatuteProof closer to an 8/10 internal delivery-readiness process, but it did not honestly reach 8/10.

The product now has a reproducible operator-only monitoring digest that classifies the current 39 queued alerts against canonical evidence, parser-noise indicators, and source-health blockers. That is real progress because it makes the monitoring output harder to overclaim.

It is still not 8/10 because:

- 39 of 39 queued alerts are still pending review.
- 38 of 39 queued alerts still lack `evidence_record_id`.
- 0 currently enabled sources require operator review due to repeated failed/quality-drop runs; 5 disabled or historical source IDs retain repeated-failure history and remain disclosed.
- No real founder-approved internal non-customer brief/digest has been generated through the full source -> evidence -> review -> alert -> brief path.
- No real customer or pilot proof exists.

## Scores

- Starting autonomous customer-delivery trust: 3/10.
- Ending autonomous customer-delivery trust: 4.5/10.
- Starting overall external CTO score reference: 67/100.
- Ending honest overall readiness estimate: 69/100.
- 8/10 reached: no.

Why only 4.5/10 on customer-delivery trust: the digest improves truth control, but customer delivery still requires human review, evidence linking, legal scan, and a real gated draft cycle.

## Agent Runtime

Fresh agent launch was attempted.

- Agents launched: 0
- Agent launch failures: 1
- Failure: agent thread limit reached
- Fallback used: yes, Codex local fallback

No agent packet is claimed as real. This report uses Codex local role checks only.

## What Was Added

1. `product/regradar/app/verified_monitoring_digest.py`
   - Builds an operator-only digest from saved alert queue entries.
   - Reads source runs, source registry, canonical evidence gates, and source-health report.
   - Classifies alerts as `HOLD`, `REVIEW_READY`, `NEEDS_PARSER_REVIEW`, or `LIKELY_NOISE`.
   - Keeps `customer_delivery=false` and `external_send=false`.

2. `tools/generate_verified_monitoring_digest.py`
   - Generates `product/regradar/reports/verified_monitoring_digest_latest.md`.
   - Does not mutate alerts, evidence records, database, or source snapshots.

3. `tools/validate_verified_monitoring_digest.py`
   - Fails if the digest implies customer delivery.
   - Fails if source-health blockers are hidden.
   - Fails if item counts are inconsistent.
   - Fails if an item is marked review-ready without brief-input eligibility.

4. `product/regradar/tests/test_verified_monitoring_digest.py`
   - 5 tests added.
   - Covers unlinked alert hold, limited/non-meaningful diff noise, approved canonical record review readiness, source-health blocker inclusion, and operator-only markdown boundary.

5. `docs/statuteproof-8-delivery-readiness-sprint-prompt.md`
   - Full governed prompt for the 8/10 sprint.
   - Includes agent runtime truth rule and no-fake-delivery gates.

6. `tools/run_statuteproof_preflight.py`
   - Added `tools/validate_verified_monitoring_digest.py` to the local preflight suite.

## Current Monitoring Digest Result

Generated report:

- `product/regradar/reports/verified_monitoring_digest_latest.md`

Digest facts from current saved data:

- Alerts queued: 39
- Pending review: 39
- Linked to canonical evidence: 2
- Brief-input eligible after evidence gate: 1
- Missing evidence links: 37
- Alerts with parser/noise indicators: 30
- Active source-health blockers: 0
- Historical disabled-source failures: 5
- Customer delivery allowed: 0

Status distribution:

- `HOLD`: 38
- `NEEDS_PARSER_REVIEW`: 1
- `REVIEW_READY`: 0
- `LIKELY_NOISE`: 0

Important nuance: several `HOLD` alerts still have parser/noise indicators. They are not counted as clean `LIKELY_NOISE` because they are already blocked by missing canonical evidence.

## Source-Health Classification

The digest now separates active blockers from disabled or historical repeated-failure rows.

Active/current enabled source-health blockers:

- None detected at the configured threshold.

Historical disabled or replaced source IDs still visible in audit history:

- `AE-adgm-fsra-rules`: 3 consecutive failed/quality-drop runs
- `AE-difc-legislation`: 3 consecutive failed/quality-drop runs
- `AE-uae-e-laws-portal-ministry-of-justice`: 14 consecutive failed/quality-drop runs
- `AE-uae-federal-tax-authority-fta`: 14 consecutive failed/quality-drop runs
- `AE-uae-securities-and-commodities-authority-sca`: 3 consecutive failed/quality-drop runs

These must stay disclosed as disabled/replaced/remediation history. They are not counted as active fresh-alert blockers unless a currently enabled source ID starts failing.

## What the Product Can Honestly Say Now

Safe:

- StatuteProof has saved monitoring artifacts and canonical evidence gates.
- StatuteProof can classify saved alert queue entries for operator review.
- StatuteProof separates alert triage from customer delivery.
- StatuteProof shows repeated source-health failures instead of hiding them.
- Current digest is operator-only and not a customer brief.

Unsafe:

- Evidence-backed customer briefs are ready for delivery.
- UAE coverage is complete.
- All source families are complete.
- Parsing is perfect.
- Monitoring will never miss updates.
- The current alert queue is ready for customers.

## What Blocks 8/10

1. Founder review must approve at least one real canonical evidence record for operational use, not only test/audit approval.
2. The approved record must be linked to a real alert queue entry.
3. One internal non-customer draft must be generated through the full gated path.
4. The draft must pass forbidden-phrase/legal scan.
5. The draft must remain `customer_delivery=false`.
6. Historical repeated-failure sources must stay formally documented as disabled, replaced, or remediation history.
7. Evidence backup policy must be written or implemented.
8. CI/preflight gating must exist outside developer discipline.

## Exact Next Engineering Task

Build the first internal non-customer gated brief cycle:

1. Use the existing linked SCA canonical record.
2. Replace the audit/test approval with a real founder/operator review entry if appropriate.
3. Verify `build_risk_brief_inputs()` returns eligible.
4. Build one internal draft via `build_evidence_backed_brief_draft()`.
5. Run legal scan.
6. Save the output as internal sample only.
7. Keep `delivery_approved=false` and `customer_delivery=false`.
8. Add a validator that proves the cycle exists without enabling customer delivery.

## Exact Next Evidence Task

Generate/link canonical evidence records for the highest-signal alert queue items:

- CBUAE retail payment services rulebook
- UAE FIU typology reports
- VARA compliance/risk PDFs
- DFSA AML/guidance items
- SCA AML/CFT only after parser noise review

Do not link evidence if run IDs, hashes, or diff paths do not match.

## Exact Next Source Task

Maintain the classification for the 5 historical repeated-failure source IDs:

- disabled/replaced by proof-backed active alternative;
- official access blocked;
- dynamic/public adapter needed;
- remediation;
- evidence-library only.

No fake `MONITOR_OK`.

## Exact Next Sales Task

Do not send Apollo outreach yet.

Prepare only a draft selected-source pilot offer that says:

- selected official-source monitoring;
- evidence gates and human review;
- source limitations disclosed;
- not legal advice;
- not complete UAE coverage;
- first brief is internal/demo until gated cycle is complete.

## Validation Run So Far

- `python3 -m pytest product/regradar/tests/test_verified_monitoring_digest.py -q`: passed, 5 tests.
- `python3 tools/validate_verified_monitoring_digest.py`: passed.
- `python3 -m pytest product/regradar/tests -q`: passed, 391 tests, 5 warnings.
- `python3 tools/run_statuteproof_preflight.py`: passed.
- Frontend validation inside preflight:
  - `npm run build`: passed.
  - `npm run lint`: passed with 1 existing TanStack Table React Compiler warning.
  - `node scripts/validate-routes.mjs`: passed.
- `git diff --check`: passed.
