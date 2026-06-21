# StatuteProof 10 / 10 Readiness Report

Report date: 2026-06-21

Starting reference:
- External CTO v1: 52/100.
- External CTO v2: 60/100.
- External CTO v3: 63/100.
- Previous internal 100-readiness score after `9c6083d`: 68/100.

Ending honest score after this sprint: 72/100, or 7.2/10.

StatuteProof did not reach 8/10, 9/10, or 10/10. The evidence-review and draft-brief gates are materially stronger, but real production evidence records remain unapproved, no customer or demo brief has been generated from a real approved canonical record, source-health blockers remain, CI/CD is still absent, and no real pilot/customer proof exists.

## Score Status

- Reached 8/10: no.
- Reached 9/10: no.
- Reached 10/10: no.

Exact blockers to 10/10:
1. Zero real canonical evidence records have been approved by a human reviewer.
2. Zero customer-delivered canonical evidence-backed briefs exist.
3. The first real end-to-end brief cycle has not been run against an approved production canonical record.
4. Five sources still require operator review after repeated FAILED or QUALITY_DROP runs.
5. No CI/CD workflow enforces preflight on push.
6. No production uptime history or external operational proof exists.
7. No paying or signed design-partner pilot exists.
8. No Stripe or equivalent clean payment path exists.
9. `api.py` and adapter architecture maintainability debt remains.
10. Agent runtime is not reliable enough to claim fully autonomous agent operation.

## Agent Attempts

Fresh agent attempts:
1. QA / Critic via `multi_agent_v1.spawn_agent` -> failed: agent thread limit reached.
2. Evidence Trail via `multi_agent_v1.spawn_agent` -> failed: agent thread limit reached.
3. Risk + Brief Pipeline via `multi_agent_v1.spawn_agent` -> failed: agent thread limit reached.
4. Product Manager via `multi_agent_v1.spawn_agent` -> failed: agent thread limit reached.
5. Evidence Trail canary via `multi_agent_v1.spawn_agent` -> failed: agent thread limit reached.
6. Evidence Trail via one-shot Claude CLI -> usable packet received.
7. QA / Critic via one-shot Claude CLI -> timed out after 120 seconds.
8. Risk + Brief Pipeline via one-shot Claude CLI -> timed out after 120 seconds.

Usable packets exchanged: 1.

Methods retried:
- Full 4-agent wave through `multi_agent_v1`.
- One-agent canary through `multi_agent_v1`.
- One-shot Claude CLI agents.
- Local verified audit and TDD implementation when agent runtime was blocked.

Agent-system conclusion:
- Agent handoff quality improved in docs/config, but real autonomous execution remains unreliable.
- The council cannot honestly claim self-driving operation until fresh agents can be spawned and return packets reliably.

## P0 Fixed

1. Canonical evidence review workflow backend.
   - Added `build_canonical_evidence_review_queue()` in `product/regradar/app/review_queue.py`.
   - Added `record_canonical_review_action()` in `product/regradar/app/review_queue.py`.
   - Decisions remain append-only through `record_canonical_evidence_review()`.
   - Completed records are not mutated.

2. Canonical evidence review API.
   - Added `GET /api/canonical-evidence`.
   - Added `POST /api/canonical-evidence/review`.
   - Reviewer identity comes from the authenticated user.
   - `approved`, `rejected`, and `blocked` decisions are supported.
   - `customer_delivery_approved` remains false.

3. Founder/operator review UI surface.
   - Updated `ReviewQueuePage.jsx` to list canonical evidence records.
   - Shows pending/approved/rejected/blocked counts.
   - Shows record ID, path, source, regulator, run status, embedded review status, and latest external decision.
   - Adds approve/reject/block buttons with required reviewer note.

4. First non-customer draft-brief path coverage.
   - Added tests proving append-only approval makes draft brief inputs eligible.
   - Added tests proving rejection keeps records blocked.
   - Added weekly brief collector tests proving external approval includes an approved alert and rejection blocks it.
   - `build_evidence_backed_brief_draft()` still returns `customer_delivery=false` and `delivery_approved=false`.

5. Source health blocker dossier refreshed.
   - Operator source health report currently flags 5 sources requiring review:
     - `AE-adgm-fsra-rules` — 3 consecutive failed/quality-drop runs.
     - `AE-difc-legislation` — 3 consecutive failed/quality-drop runs.
     - `AE-uae-e-laws-portal-ministry-of-justice` — 14 consecutive failed/quality-drop runs.
     - `AE-uae-federal-tax-authority-fta` — 14 consecutive failed/quality-drop runs.
     - `AE-uae-securities-and-commodities-authority-sca` — 3 consecutive failed/quality-drop runs.

## P0 Remaining

1. Human/Evidence Trail review of the 11 real local canonical evidence records.
2. Approval or rejection of real records through the new UI/API/CLI workflow.
3. Link one approved real canonical record to an alert.
4. Run one complete non-customer brief cycle from a real approved record.
5. Remediate or formally downgrade the 5 repeated-failure sources.
6. Add CI/CD preflight enforcement.
7. Add evidence backup/reproducibility policy for gitignored evidence records.
8. Complete real pilot/customer proof before any 9/10 or 10/10 claim.

## Evidence Records

- Canonical evidence records created locally before this sprint: 11.
- Canonical evidence records committed: 0.
- Evidence records approved in this sprint: 0.
- Customer deliveries: 0.
- Raw evidence/source snapshots staged: no.
- Alert queue runtime files staged: no.

Current validator state:
- `tools/validate_canonical_evidence_records.py` passes.
- All 11 local records are complete and hash-verifiable.
- All 11 still show latest review decision `none` in preflight.

## Brief Path

What improved:
- Append-only external approval now has an API/UI path.
- Approved fixture records can become draft-brief eligible.
- Rejected fixture records remain blocked.
- Weekly brief collector can include an approved alert only when canonical evidence is eligible.
- Delivery remains disabled by default.

What remains:
- No real local record was approved.
- No real non-customer brief output was generated from the 11 local records.
- No customer delivery was performed.

## Source Health

Source health reporting was used, not substantially changed.

Current blocker count: 5 operator-review sources.

Next source task:
- For each of the 5 sources, inspect source config and latest run records, try one controlled no-save retest only where public/official access is safe, then either fix adapter/selectors or mark exact remediation/downgrade reason.

## Customer Claims

Customer-facing claims changed: no broad marketing claims changed.

Claims explicitly not made:
- Complete UAE coverage.
- Complete family coverage.
- Legal advice.
- Guaranteed compliance.
- Regulator certification.
- Perfect parsing.
- Never-miss updates.
- All-source coverage.
- Production-ready 10/10.
- Customer-delivered evidence-backed briefs.

## Tests Added

New tests:
1. Canonical review action approval unlocks non-delivery brief draft.
2. Canonical review action rejection keeps record blocked.
3. Append-only canonical approval allows a weekly-approved alert into `collect_approved_alerts()`.
4. Append-only canonical rejection blocks that alert from `collect_approved_alerts()`.

Focused validation completed before full preflight:
- `python3 -m pytest product/regradar/tests/test_canonical_review_workflow.py -q` -> 2 passed.
- `python3 -m pytest product/regradar/tests/test_weekly_brief.py -q` -> 19 passed.
- `python3 -m pytest product/regradar/tests/test_canonical_review_workflow.py product/regradar/tests/test_canonical_evidence_records.py product/regradar/tests/test_review_canonical_evidence_cli.py -q` -> 27 passed.
- Frontend build -> passed.
- Frontend lint -> 0 errors, 1 existing TanStack Table warning in `DashboardPreview.jsx`.
- Route validation -> passed.

Full validation:
- `python3 -m compileall -q product/regradar tools` -> PASS.
- `python3 -m pytest product/regradar/tests -q` -> 377 passed, 5 warnings.
- `python3 tools/validate_agent_council_protocol.py` -> PASS.
- `python3 tools/run_statuteproof_preflight.py` -> PASS.
- `python3 tools/agent_council.py list` -> PASS.
- `git diff --check` -> PASS.
- Preflight source truth: 241 enabled UAE sources, 172 fresh-alert, 61 evidence-library, 5 candidate, 3 remediation.
- Preflight canonical evidence list: 11 records, all still pending, latest review `none`.
- Frontend build -> PASS.
- Frontend lint -> 0 errors, 1 existing TanStack Table warning in `DashboardPreview.jsx`.
- Route validation -> PASS.

## Next Exact Tasks

Next engineering task:
- Add a backend/UI flow to link an approved canonical evidence record to a specific alert draft without editing alert queue JSON by hand.

Next evidence task:
- Review `evr_AE-sca-aml-cft_intake-20260619T143025Z` first because it is a CHANGED canonical record and is the most valuable candidate for the first non-customer brief cycle.

Next product task:
- Add a guided founder review checklist before the approve button can be used: source URL checked, hashes recomputed, diff inspected, limitation recorded, no customer delivery.

Next source task:
- Remediate or document `AE-uae-federal-tax-authority-fta` and `AE-uae-e-laws-portal-ministry-of-justice`, both at 14 consecutive failed/quality-drop runs.

Next sales task:
- Do not sell as production. Prepare a pilot-only offer after one real approved canonical evidence-backed draft brief exists.
