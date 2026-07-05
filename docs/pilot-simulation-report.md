# StatuteProof Simulated Pilot Report

Report date: 2026-06-21

This report is a synthetic pilot simulation, not customer research proof. No real customer used the product, no customer email was sent, no production deployment was touched, and no simulated persona should be counted as a paying customer, design partner, or readiness-score evidence.

## Decision This Simulation Informs

Can StatuteProof invite a tightly scoped real design-partner pilot, and what must be fixed before the first paid or externally delivered evidence-backed brief?

Short answer: StatuteProof can be shown to a carefully qualified design partner as a pilot candidate, but it should not be sold as paid production delivery yet. The simulated users found strong trust signals in source transparency, validators, and canonical evidence records, but they also found a blocking workflow gap: no real canonical evidence record has been approved by a founder/operator for production use, no real customer-delivered evidence-backed brief cycle has completed, and disabled/historical source-health failures still need clear disclosure.

Source-truth snapshot verified during this simulation:
- 241 enabled UAE sources.
- 172 fresh-alert eligible.
- 61 evidence-library.
- 5 candidate.
- 3 remediation.
- 11 canonical evidence records exist locally and pass hash verification.
- 0 currently enabled sources require operator review after repeated FAILED or QUALITY_DROP runs.
- 5 disabled or historical source IDs retain repeated-failure history and remain disclosed.

Subsequent local proof-recovery update: a later UAE FIU-focused sprint created
a 12th local canonical evidence record for `AE-uaefiu-typology-reports` and
linked the matching alert queue item. That later record remains pending review
and does not change the simulated-customer proof boundary in this report.

## Method

The pilot was simulated through code and product-surface review, not live customer interviews. Synthetic personas inspected the current product as if evaluating a 30-day pilot. The simulation used:

- `docs/statuteproof-10-out-of-10-readiness-report.md`
- `product/regradar/web/src/components/Coverage.jsx`
- `product/regradar/web/src/components/app/ReviewQueuePage.jsx`
- `product/regradar/web/src/components/app/EvidencePage.jsx`
- `product/regradar/web/src/components/app/AIBriefPage.jsx`
- `product/regradar/web/src/components/app/ReportsPage.jsx`
- `product/regradar/web/src/components/PricingPage.jsx`
- `product/regradar/web/src/data/sourceQualityAudit.ts`
- `product/regradar/app/evidence_records.py`
- `product/regradar/app/review_queue.py`
- `product/regradar/app/source_health_timeline.py`

Validation commands run during the simulation:

```bash
python3 tools/validate_canonical_evidence_records.py
python3 product/regradar/reports/validate_audit.py
python3 - <<'PY'
from app.source_health_timeline import build_operator_source_health_report
r = build_operator_source_health_report()
print(r.get("sources_requiring_operator_review"))
PY
```

Agent-runtime note:
- Attempted fresh `product-manager`, `evidence-trail`, and `qa-critic` subagents for persona packets.
- All three `multi_agent_v1.spawn_agent` attempts failed with `agent thread limit reached`.
- A Claude CLI one-shot fallback was attempted as a synthetic external auditor and timed out after 90 seconds.
- The final report is therefore based on locally verified product/code inspection, validation commands, and the synthetic persona method described above.
- This reinforces the existing agent-system blocker: the council cannot honestly claim reliable autonomous multi-agent operation yet.

## Tasks Attempted By Personas

Each persona attempted to answer:

1. What is actually monitored?
2. Which source families are strong, partial, weak, or blocked?
3. What evidence exists, and what is only source-run proof?
4. Can canonical evidence be approved or rejected?
5. Can an evidence-backed brief be inspected or generated?
6. Are disclaimers and legal boundaries clear?
7. Is there any overclaim?
8. Is this safe for a 30-day pilot?

## Persona 1 - UAE VASP MLRO

Verdict: Interested, but would only enter a limited pilot with explicit scope and manual review. The VARA and AML/TFS source transparency is strong, but the MLRO cannot yet see a completed evidence-approved brief cycle.

Score: 6.8 / 10

Confusing screens:
- `Evidence Records` appears to mean live source-run records, while `Canonical evidence review` appears inside `Review Queue`. A buyer may not understand which evidence object supports a customer brief.
- `Monitoring Briefs` says evidence-backed, but the empty state does not show the exact missing prerequisite: approved canonical evidence plus linked alert plus delivery approval.
- Pricing mentions weekly MLRO brief for `UAE Monitor`, but the product readiness report says no real canonical evidence-backed brief has completed.

Missing features:
- A guided MLRO review checklist before approving canonical evidence.
- A visible "why this brief is blocked" path from evidence record to alert to brief.
- A source-health warning panel for sources with repeated failures.
- A pilot scope selector that says "selected-source VARA/CBUAE/FIU/EOCN only" rather than implying broad AML coverage.
- A sample internal brief generated from a real approved canonical evidence record, marked non-customer.

Trust blockers:
- 11 canonical records exist, but all remain unapproved in operational truth.
- UAE FIU has partial coverage and FIU circulars remain held/candidate.
- SCA and MoJ/Gazette gaps matter for capital markets and legal horizon scanning.
- 5 sources require operator review, including SCA and FTA portal records.

Purchase blockers:
- No real approved evidence-backed brief has been produced.
- No customer delivery proof exists.
- No uptime or CI/CD proof.
- No payment/self-serve path beyond manual activation.

Legal/claim risks:
- "Evidence-backed" can be safe only when paired with "draft-only until canonical evidence is approved." Otherwise it risks sounding like delivered evidence-backed reporting exists today.
- VASP buyer needs "selected-source monitoring" repeated wherever VARA/EOCN/TFS appears.

Evidence concerns:
- Source-run evidence and canonical customer evidence are too easy to confuse.
- There is no buyer-friendly chain view: source run -> canonical evidence -> review -> alert -> draft brief.

Top 5 fixes:
1. Approve one real canonical evidence record through the new review path.
2. Generate one internal non-customer draft brief from that approved record.
3. Add a chain-of-custody panel that shows source run, canonical record, review decision, alert link, and brief state.
4. Add operator source-health warnings to the pilot dashboard.
5. Tighten pricing copy so weekly MLRO brief is clearly "available after review and delivery setup."

Would pilot: yes, if positioned as a 30-day selected-source design partner pilot.

Would pay: not yet. Payment becomes plausible after one real evidence-backed draft brief and source-health remediation.

Next prompt for Product Manager:
Review the VASP pilot package and rewrite the offer around selected-source VARA, CBUAE, FIU public-source, and EOCN/TFS monitoring, with a hard gate that no brief is customer-delivered until canonical evidence is approved.

## Persona 2 - DFSA Compliance Manager

Verdict: Would respect the honesty of the coverage page, but would not buy until DFSA-specific workflows show evidence, review, and brief output for a real source.

Score: 6.5 / 10

Confusing screens:
- DFSA appears in source quality as `good` with 16 fresh-alert sources, but the buyer has no DFSA-specific readiness page or pack showing which 16 matter for their firm.
- Evidence and Reports pages are built around source-run evidence, while the brief gate depends on canonical evidence.
- Review Queue has canonical records but does not visually connect them to the relevant source family or customer risk.

Missing features:
- DFSA source-family drilldown with fresh-alert, evidence-library, and caveat rows.
- Review checklist tailored to DFSA consultation/enforcement/rulebook workflows.
- A reviewed DFSA example brief generated through canonical evidence.
- Operator note explaining that static individual pages are not inflated as fresh alerts.
- A "not complete DFSA coverage" disclosure in the pilot configuration.

Trust blockers:
- DFSA has 16 fresh-alert sources, below the 25 target.
- Static evidence-library sources are correctly excluded, but the buyer must work to understand why that is good.
- No approved canonical evidence-backed DFSA brief exists.

Purchase blockers:
- The manager cannot evaluate the actual reviewed brief artifact.
- No human review SLA.
- No CI/CD or operational assurance.

Legal/claim risks:
- DFSA buyer may read "selected fresh-alert eligible official UAE sources across DFSA" as broad coverage unless the plan screen links to the caveat detail.

Evidence concerns:
- Reports can export from saved source-run records; customer brief eligibility requires canonical evidence. This boundary needs clearer labeling.

Top 5 fixes:
1. Add source-family detail pages for DFSA, ADGM/FSRA, VARA, CBUAE, FIU, SCA, MoF, and MoJ/Gazette.
2. Generate one DFSA canonical evidence record and route it through review.
3. Add a "Brief eligibility" column to Evidence/Reports views.
4. Add a source-family caveat panel to pricing and onboarding.
5. Add a reviewed DFSA pilot sample once evidence is approved.

Would pilot: yes, if the pilot is scoped to a narrow DFSA source set and includes manual review.

Would pay: not before a real reviewed brief artifact exists.

Next prompt for Product Manager:
Define the minimum DFSA pilot configuration: exact sources, exclusions, brief cadence, review SLA, evidence workflow, and safe wording for "selected-source DFSA monitoring."

## Persona 3 - ADGM/FSRA Compliance Officer

Verdict: Cautiously interested, but ADGM/FSRA trust is held back by candidate/source-depth ambiguity and unclear adapter depth.

Score: 6.1 / 10

Confusing screens:
- Coverage says ADGM FSRA sources are active in several categories, while the old `AE-adgm-fsra-rules` failure is now classified as disabled/replaced history and the UI still does not make that replacement story obvious.
- ADGM/FSRA has 10 fresh-alert sources and 3 candidates, but the UI does not show the candidate/remediation breakdown at the moment of buyer evaluation.
- The buyer cannot tell which ADGM records are generic extraction vs purpose-built adapter output.

Missing features:
- ADGM/FSRA source-family status page with failed/candidate details.
- Extraction method visibility by source.
- Operator note explaining that `AE-adgm-fsra-rules` is disabled/replaced by active proof-backed ADGM/FSRA sources.
- One reviewed ADGM/FSRA canonical evidence example.
- Clear "this is not complete ADGM coverage" pilot language.

Trust blockers:
- ADGM/FSRA source family is below 25 fresh-alert sources.
- 3 ADGM/FSRA candidate rows remain unresolved.
- Disabled/replaced source-health history still exists and must be explained clearly.

Purchase blockers:
- No family-specific assurance.
- No evidence-backed brief cycle for ADGM/FSRA.
- No uptime/source failure SLA.

Legal/claim risks:
- "ADGM FSRA - Rules, Guidance, Waivers" in Coverage could feel stronger than current health supports unless paired with a live source-health caveat.

Evidence concerns:
- The user cannot see whether an ADGM source's current evidence can become brief-eligible or is only source-run evidence.

Top 5 fixes:
1. Show `AE-adgm-fsra-rules` as disabled/replaced history, not an active blocker.
2. Add extraction method and adapter confidence to source rows.
3. Add ADGM/FSRA family drilldown with candidates and blockers.
4. Create and review one canonical ADGM/FSRA evidence record.
5. Add buyer-safe copy: selected ADGM/FSRA official-source monitoring, not complete coverage.

Would pilot: maybe, only after ADGM source-health blocker is resolved or disclosed.

Would pay: no, not yet.

Next prompt for Product Manager:
Create an ADGM/FSRA pilot-readiness checklist that requires source-health remediation, candidate disclosure, and one reviewed canonical evidence artifact before sales outreach.

## Persona 4 - Founder Operator

Verdict: The internal operator workflow is close enough to run a concierge pilot, but too much relies on founder discipline and manual interpretation.

Score: 7.4 / 10

Confusing screens:
- Review Queue combines old review queue rows and canonical evidence review rows in one page.
- Evidence, Reports, and Monitoring Briefs use overlapping language for "evidence-backed" at different maturity levels.
- There is no single operator runbook view saying "do these five steps to produce a safe pilot brief."

Missing features:
- Operator checklist for the first full cycle.
- Button or CLI flow to link approved canonical evidence to an alert without editing runtime JSON.
- Source-health remediation queue.
- Evidence backup/reproducibility policy.
- Preflight/CI status badge in the operator dashboard.

Trust blockers:
- Agent runtime still cannot reliably spawn fresh agents due to thread-limit failures.
- 5 disabled/historical source-health failures need disclosure as replacement/remediation history.
- Evidence records are local/gitignored; backup policy remains a blocker.

Purchase blockers:
- Founder cannot yet demonstrate a complete evidence-approved brief output.
- Manual billing and activation create friction.
- No operational runbook for repeated source failures.

Legal/claim risks:
- Founder could over-explain the evidence system and accidentally imply customer delivery readiness before the first approved brief cycle.

Evidence concerns:
- All 11 local records passing validation is strong, but without approval and brief output it is still pre-delivery evidence.

Top 5 fixes:
1. Run first internal non-customer evidence-backed brief cycle.
2. Add "link approved canonical evidence to alert" flow.
3. Add source-health remediation queue and owner/status per failing source.
4. Write evidence backup policy.
5. Add CI or document the credentials blocker for CI.

Would pilot: yes, as founder-operated concierge pilot.

Would pay: not applicable as internal operator.

Next prompt for Product Manager:
Turn the first-pilot operator workflow into a single checklist: source scope approved, canonical record approved, alert linked, brief draft generated, legal scan passed, delivery explicitly blocked or approved.

## Persona 5 - External CTO / Auditor

Verdict: The architecture is unusually honest for an early RegTech product, but the product is still not beyond pilot readiness because its strongest promise has not been exercised end-to-end on real data.

Score: 6.6 / 10

Confusing screens:
- "Evidence Records" in the authenticated app is not the same as canonical `evidence-record.json` readiness.
- "Evidence-backed report exports" can be read as stronger than canonical customer evidence unless copy distinguishes source-run audit packs from customer brief evidence.
- Pricing says weekly MLRO brief on the `UAE Monitor` tier, but operationally delivery still requires setup and real evidence approval.

Missing features:
- End-to-end evidence-backed brief demo.
- CI/CD workflow.
- Uptime/source-health operational monitoring.
- API/module maintainability improvements.
- Real design-partner feedback.

Trust blockers:
- No real approved canonical evidence record.
- No real evidence-backed brief cycle.
- Source-health blocker count remains 5.
- No reliable agent-runtime autonomy.
- No external customer proof.

Purchase blockers:
- No paid pilot evidence.
- No payment path.
- No runbook/SLA.
- No CI gate.

Legal/claim risks:
- The public-facing site is mostly safe, but words like "evidence-backed" and "weekly MLRO brief" need conditional language until the full cycle is demonstrated.

Evidence concerns:
- Evidence tree is local and gitignored. That is good for data hygiene but requires backup/reproducibility policy before customer reliance.
- The current validator proves record integrity, not customer delivery readiness.

Top 5 fixes:
1. Complete first real internal evidence-backed brief cycle.
2. Add CI/preflight enforcement.
3. Resolve or downgrade the 5 failing sources.
4. Add evidence backup policy.
5. Split `api.py` only after the brief workflow is stable.

Would pilot: yes, as a controlled design-partner pilot after one internal full-cycle brief.

Would pay: no, not before the full cycle and source-health remediation.

Next prompt for Product Manager:
Define the pilot-readiness gate as a binary checklist. The product can be shown now, but paid pilot activation requires one approved canonical evidence-backed draft brief, source-health remediation notes, and a written evidence backup policy.

## Cross-Persona Findings

Overall simulated pilot score: 6.7 / 10.

This should not raise the official product-readiness score. The simulation produced useful product feedback, but it is not real customer proof. The current 7.2/10 internal readiness score remains bounded by the same hard blockers: approved real evidence, end-to-end brief cycle, source-health remediation, CI/CD, customer proof, and payment path.

### P0 Failures Found

1. No real approved canonical evidence-backed brief cycle exists.
   - 11 canonical records exist and validate.
   - They remain operationally unapproved in current truth.
   - No real brief has been generated from an approved production canonical record.

2. Evidence vocabulary is too ambiguous.
   - Evidence page: live source-run records.
   - Reports page: source-run audit packs.
   - Review Queue: canonical evidence review.
   - Brief gate: canonical evidence only.
   - A buyer can easily assume these are the same artifact.

3. Source-health history still needs clearer product disclosure.
   - `AE-adgm-fsra-rules` - 3 consecutive failed/quality-drop runs.
   - `AE-difc-legislation` - 3 consecutive failed/quality-drop runs.
   - `AE-uae-e-laws-portal-ministry-of-justice` - 14 consecutive failed/quality-drop runs.
   - `AE-uae-federal-tax-authority-fta` - 14 consecutive failed/quality-drop runs.
   - `AE-uae-securities-and-commodities-authority-sca` - 3 consecutive failed/quality-drop runs.

4. The buyer cannot see a single chain-of-custody view.
   - There is no unified screen for source run -> canonical evidence -> review decision -> alert link -> brief draft -> delivery state.

5. Weekly MLRO brief claim is still commercially fragile.
   - Pricing qualifies delivery, but buyer personas want the exact gate visible: no approved canonical evidence means no customer-deliverable brief.

### P1 Failures Found

1. No family drilldown from buyer viewpoint.
   - SCA, FIU, MoF, MoJ/Gazette, ADGM/FSRA, DFSA all need family-level explanation in the app.

2. No guided founder review checklist.
   - Approval requires note, but not a checklist confirming source URL, hash, diff, limitations, and delivery boundary.

3. No extraction method visibility in buyer/operator views.
   - Buyers cannot tell purpose-built adapter vs generic fallback.

4. No evidence backup/reproducibility policy visible.
   - Canonical records are local and gitignored. Correct, but operationally incomplete without backup policy.

5. Agent system is still not reliable enough for an "automatic council" claim.
   - Fresh subagent launches failed with thread-limit errors during this simulation.

## Product Fixes Required

1. Build the first-pilot chain view:
   - source run
   - canonical evidence record
   - validation status
   - review decision
   - linked alert
   - brief draft state
   - delivery approval state

2. Add source-family detail pages or panels:
   - current count
   - fresh-alert count
   - evidence-library count
   - candidate/remediation count
   - caveats
   - last source-health status
   - pilot suitability

3. Add a "why no brief yet" empty state on Monitoring Briefs.
   - It should list the missing gates in order.

4. Clarify plan wording:
   - `Weekly MLRO brief` should say "available after canonical evidence approval and delivery setup" where relevant.

5. Add an operator runbook page:
   - approve evidence
   - link alert
   - generate draft
   - legal scan
   - delivery approval
   - record limitation

## Evidence Fixes Required

1. Review the first real record:
   - Start with `evr_AE-sca-aml-cft_intake-20260619T143025Z` because it is a CHANGED record and is most useful for an internal brief cycle.

2. Add a link-approved-evidence-to-alert workflow.
   - Do not require manual runtime JSON editing.

3. Run one non-customer draft brief from an approved real canonical record.
   - Mark it internal/demo only.
   - Keep customer delivery false by default.

4. Add evidence backup policy.
   - State where canonical records live, how they are backed up, how hashes are reverified, and how customer exports are controlled.

5. Add evidence eligibility labels:
   - source-run evidence
   - canonical evidence pending review
   - canonical evidence approved for draft brief
   - customer delivery approved

## UX Fixes Required

1. Rename or subtitle the Evidence page:
   - "Source-run evidence records" rather than ambiguous "Evidence Records."

2. Rename canonical review section:
   - "Canonical customer-brief evidence review."

3. Add a visible chain-of-custody drawer for every evidence item.

4. Add guarded confirmation before approval:
   - I inspected official source URL.
   - I verified hash.
   - I inspected diff.
   - I recorded limitation.
   - I understand approval does not approve customer delivery.

5. Add source-health warnings to source and family views.

## Claims Fixes Required

1. Avoid "evidence-backed briefs are available" until one real approved canonical evidence-backed brief cycle exists.

2. Use safer wording:
   - "Canonical evidence-backed brief workflow is implemented and pending first internal approved cycle."
   - "Selected-source UAE monitoring, not complete coverage."
   - "Brief delivery requires human review and configured delivery setup."

3. Keep these claims explicitly blocked:
   - complete UAE coverage
   - complete family coverage
   - legal advice
   - compliance guarantee
   - regulator certification
   - perfect parsing
   - never-miss updates
   - all-source coverage
   - production-ready customer delivery

## Exact Path To A Real Pilot

1. Approve or reject all 11 current canonical evidence records through the new review workflow.
2. Link one approved CHANGED canonical record to an alert without manual JSON editing.
3. Generate one internal non-customer draft brief from that record.
4. Verify the brief includes canonical evidence metadata, legal disclaimer, source URL, hash, and limitation notes.
5. Run legal/QA review on the generated brief.
6. Keep the 5 disabled/historical repeated-failure sources documented as replaced/remediation history.
7. Add family-level pilot scope pages for VASP, DFSA, ADGM/FSRA, and FIU users.
8. Write evidence backup/reproducibility policy.
9. Add or document CI/preflight enforcement.
10. Only then invite 3 real design-partner interviews or pilots.

## What Cannot Be Claimed Because This Was Simulated

The team cannot claim:
- real customer validation
- real willingness to pay
- paid pilot readiness proven by users
- buyer acceptance
- usability validated by customers
- customer-delivered evidence-backed brief
- product-market fit
- production readiness
- 8/10, 9/10, or 10/10 readiness from this simulation alone

The team can claim:
- a synthetic pilot simulation was performed.
- the simulation found specific UX, evidence, source-health, and claim-safety blockers.
- the product remains suitable for an internal demo and a carefully scoped design-partner conversation after the first real approved evidence-backed brief cycle.

## Next Exact Tasks

Next engineering task:
- Build the link from approved canonical evidence record to alert draft without manual alert queue JSON edits.

Next evidence task:
- Review `evr_AE-sca-aml-cft_intake-20260619T143025Z` first and document approve/reject/block reasoning.

Next product task:
- Design the chain-of-custody view and the first-pilot operator checklist.

Next source task:
- Build family drilldowns that show active proof-backed replacements separately from disabled/historical repeated-failure source IDs.

Next sales task:
- Prepare only a design-partner discovery script. Do not pitch paid delivery until the first internal evidence-backed brief cycle is complete.
