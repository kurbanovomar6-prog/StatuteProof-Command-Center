# StatuteProof MVP Plan

## MVP Goal
Build evidence-backed monitoring for a small UAE source pack and use it to start customer discovery.
The MVP proves that official-source monitoring can produce audit-ready evidence and short compliance review briefs.
It does not need a full dashboard, multi-tenant system, or automated legal analysis.

## First ICP
Primary ICP: UAE VASPs and UAE fintechs with small or medium compliance capacity.
They are likely to care because regulatory updates can be operationally important, compliance teams may be small, and official-source monitoring is tedious.
Buyer titles include MLRO, Head of Compliance, Chief Compliance Officer, Legal Counsel, Operations lead, and founder in regulated startup.

## First Source Pack
1. VARA official source page — VERIFY BEFORE PRODUCTION.
2. CBUAE official circular/regulation page — VERIFY BEFORE PRODUCTION.
3. DFSA or ADGM FSRA official page — VERIFY BEFORE PRODUCTION.
The first pack should be small enough to monitor manually before automation.
The first pack should produce evidence records that can be explained to prospects.

## What MVP Must Do
- Write source specs.
- Fetch official source content.
- Normalize source text.
- Hash normalized content.
- Compare old and new text.
- Create evidence record.
- Store raw content and snapshot.
- Store normalized current and previous text.
- Create diff.
- Classify risk using `docs/risk-scoring-guide.md`.
- Produce a short brief.
- Trigger human review.
- Run legal language review.
- Run QA / Critic review.
- Support sample outreach.

## What NOT To Build Yet
1. Multi-tenant customer portal.
2. Enterprise SSO.
3. Payment system.
4. Fully automated sending.
5. Broad regulator coverage across all UAE sources.
6. AI legal answer chatbot.
7. Vector database.
8. Redis queue.
9. PostgreSQL migration.
10. Mobile app.
11. Browser extension.
12. Complex n8n orchestration.

## 30-Day Plan
### Week 1 — Source Specs + First Evidence Records
- Confirm first ICP and source pack.
- Write source specs for VARA and CBUAE.
- Create SAMPLE / FAKE evidence record and real-data checklist.
- Run Source Monitor Agent and Evidence Trail Agent manually.
- Produce one source readiness review outline.

### Week 2 — Manual Workflow + Risk Scoring
- Run manual monitoring workflow on selected sources.
- Capture raw and normalized content.
- Test hash and diff process.
- Score one SAMPLE / FAKE change using the risk guide.
- Write one human-reviewed SAMPLE / FAKE brief.

### Week 3 — ICP Research + 20 Leads + 10 Outreach Messages
- Define lead scoring.
- Research 20 public-source leads.
- Mark unknowns honestly.
- Draft 10 outreach messages.
- Review messages with Legal Language and QA / Critic.

### Week 4 — Pilot Offer + Landing Page Copy
- Define 2-source 30-day pilot.
- Write landing page copy.
- Create source readiness review checklist.
- Send first reviewed outreach batch.
- Record prospect responses and objections.

## Pilot Offer Definition
Scope: two official sources for 30 days.
Output: weekly source health summary, evidence records for detected changes, and human-reviewed briefs for meaningful changes.
Boundary: monitoring information only, not legal advice.
Review: human review included before any client-facing brief.
Delivery: email or shared document during pilot.

## Success Metrics
- 3 source specs completed.
- 2 evidence records created and verified.
- 1 SAMPLE / FAKE brief passes Legal Language and QA.
- 20 qualified leads researched.
- 10 reviewed messages drafted.
- 5 outreach messages sent.
- 2 discovery calls booked.
- 1 pilot conversation opened.
- 0 unsafe claims shipped.
- 0 evidence-less briefs created.

## Risks And Mitigations
- Risk: source pages are hard to monitor. Mitigation: manual MVP and source classification.
- Risk: no clear buyer pain. Mitigation: discovery calls before dashboard build.
- Risk: legal language overreach. Mitigation: Legal Language and QA gates.
- Risk: evidence process too manual. Mitigation: automate only after manual proof.
- Risk: too many regulators. Mitigation: first source pack only.
- Risk: false positives. Mitigation: normalization and QUALITY_DROP rules.
- Risk: founder overbuilds. Mitigation: Chief of Staff do-not-do list.
- Risk: outreach too generic. Mitigation: ICP + Lead Research source-backed hooks.

## Task-to-Agent Map
| Task | Owner Agent |
|---|---|
| Weekly plan | Chief of Staff Agent |
| MVP scope | Product Manager Agent |
| Implementation plan | Code Architect / Dev Agent |
| Final review | QA / Critic Agent |
| Safe wording | Legal Language Agent |
| Source specs | Source Monitor Agent |
| Evidence records | Evidence Trail Agent |
| Risk briefs | Risk + Brief Pipeline Agent |
| Lead research | ICP + Lead Research Agent |
| Outreach | Outreach Writer Agent |
