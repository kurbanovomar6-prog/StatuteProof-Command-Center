# StatuteProof Master Plan to Ideal Product

> Date: 2026-06-16
> Author: Claude — product strategist, MLRO buyer psychologist, frontend critic, pricing analyst, compliance workflow architect
> Basis: Full read-only inspection of all product code, frontend components, backend modules, tests, docs, pricing, and competitor data.
> Current truth: 66 enabled UAE sources / 62 readiness-supported / 4 remediation / 217 tests passing.
> Hard rule: No fake confidence. No legal advice. No guaranteed compliance. No "never miss updates."
> This document is for internal strategic use only.

---

## Summary (Read This First)

**Current honest product score: 7.1/10**

**Top 5 things that are still missing:**
1. AlertsPage.jsx still uses MOCK_ALERTS — the most customer-visible trust risk
2. Dashboard source counts (66/62/4) are hardcoded in JSX, not API-driven
3. Price/capability mismatch: plan.py encodes $199/$399 but pricing strategy docs target $349/$749 — no reconciliation has happened
4. Professional plan source_limit is 13 in plan.py, not 62 — a major discrepancy from how the pack is described externally
5. Global review queue with risk/source-health filters does not exist — the MLRO has no single place to manage all unreviewed items

**What to build first:** The global unreviewed alert queue (the single MLRO workflow page that makes $399 feel underpriced).

**Whether customers will pay now:** Yes, at $199 for a controlled founder-led pilot targeting CBUAE/AML/payments-heavy compliance teams. Not yet at $399 without the review queue, corrected plan capabilities, and AlertsPage live data.

**What exact offer to sell:** "Founder-led UAE official-source monitoring pilot. Scope agreed upfront. Evidence-backed source status, diffs, and A&A review records. 3 UAE official sources (CBUAE/AML focus). $199/month. Monitoring intelligence only. Not legal advice."

**What makes it feel underpriced:** A compliance professional seeing evidence-backed source records, hashes, diffs, and a locked A&A review trail for $199 — compared to a $3,200–12,000/month equivalent manual monitoring labor cost — will think "this is not priced for what it does." That feeling only comes when the product works end-to-end with zero mock data.

**Next exact product task:** Replace MOCK_ALERTS in AlertsPage with the live `/api/alerts` or honest empty state, and API-drive the DashboardHome source counts (66/62/4) from the sources API, not hardcoded JSX.

**Next exact sales task:** Run one real MLRO demo using a verified CBUAE source with a live evidence record, a real diff, and a completed A&A assessment — then ask "what review field is still missing from your compliance file?"

---

## 1. Brutally Honest Executive Verdict

StatuteProof has crossed the hardest threshold: it has a genuine, proof-backed, evidence-first monitoring infrastructure with 62 readiness-supported UAE official sources, a locked A&A assessment workflow, and legal-safe output. That is not common at this stage and it is genuinely defensible.

But the product is not yet ideal. It has four structural flaws that are each individually fixable but together limit what can be charged and who can buy:

**Flaw 1 — The dashboard is partly lying.** The source counts (66/62/4) on DashboardHome are hardcoded JSX constants, not API responses. AlertsPage still serves MOCK_ALERTS. AIBriefPage silently falls back to mock if the API call fails. A compliance professional who inspects what they are looking at will lose confidence.

**Flaw 2 — The plan configuration contradicts the external pricing narrative.** The pricing strategy documents say $349/$749. The website shows $199/$399. The plan.py backend encodes $199/$399. The Professional plan in plan.py has source_limit: 13 (not 62), retention_days: 180 (not 365). There is no reconciliation. The product is internally inconsistent about what it sells.

**Flaw 3 — The MLRO has no command center.** There is an EvidencePage for reviewing individual records and a Sources page for seeing source status. But there is no single review queue where the MLRO can see all unassessed changes, filter by risk level, mark as reviewed, and move on. Without this, the A&A workflow is isolated to one-off evidence records. It is not a workflow.

**Flaw 4 — VARA coverage is 3 readiness-supported sources (4.8%) but VASP MLROs are described as the primary buyer.** These two things are incompatible. Either VARA coverage must be extended before targeting VASPs seriously, or the primary ICP must be explicitly shifted to CBUAE/payments compliance teams.

Fix these four things and the product moves from 7.1/10 to 8.5/10. That is where "feels underpriced" starts.

---

## 2. Current Product Scorecard

Scores from 1–10 with strict grading. No inflation.

| # | Area | Score | Why | +1 Point | 10/10 Requires |
|---|------|------:|-----|----------|---------------|
| 1 | Overall product | 7.1 | Real foundation, real sources, A&A MVP exists, but 4 structural flaws | Fix AlertsPage mock data + API-drive dashboard counts | All 4 flaws fixed + PDF + VARA coverage |
| 2 | Website clarity | 7.0 | Positioning clear, source readiness matrix good, pricing visible | Fix plan capability description (13 sources vs "62 sources" confusion) | Buyer-matched landing with dynamic source coverage per ICP |
| 3 | Website visual trust | 7.5 | Dark professional design, cyan accent, no fake screenshots | Remove any hardcoded placeholder values in components | Add real proof-of-monitoring screenshot to landing |
| 4 | Dashboard usefulness | 6.5 | Profile summary, info cards work; source counts hardcoded; no risk trend; no review queue | API-drive all source/alert counts | Live monitoring timeline, risk trend chart, global review queue |
| 5 | Sources page usefulness | 8.0 | Live API data, multiple filters, health states clear, honest remediation | Add last-checked timestamp column | Per-source monitoring history timeline (30/90-day stability) |
| 6 | Evidence page usefulness | 8.5 | Rich: hash, URL, quality, proof path, assessment section, review history | Add review history count badge on page header | PDF export of evidence record + assessment |
| 7 | Acknowledge & Assess usefulness | 7.0 | MVP correct — blocks assessment without proof; impact level + note + next action | Add assessment status filter and sort across all records | Full review queue with A&A inline; email notification to reviewer |
| 8 | Source health timeline usefulness | 6.0 | Latest status visible on source cards; no historical chart | Add 7-day sparkline per source on Sources page | Full 30/90-day timeline chart with MONITOR_OK vs QUALITY_DROP history |
| 9 | Source coverage usefulness | 7.5 | 62 real readiness-supported sources, honest limitations, 4 remediation documented | Improve VARA from 3 to 6+ sources | Balanced pack: no regulator above 30%; VARA, DIFC, DFSA all at 8+ |
| 10 | Source diversity | 5.5 | CBUAE is 43.5%; VARA is 4.8%; DIFC is 0 active; lopsided for broad sales | Add 2–3 VARA PDF/rulebook sources | Regulator distribution: CBUAE ≤30%, DFSA ≥12%, VARA ≥10%, DIFC ≥6% |
| 11 | Parser/adapter trust | 8.0 | 13 adapter families, quality gates, FAILED ≠ UNCHANGED enforced, nav-shell detection | Surface adapter name on evidence card in UI | Adapter health monitoring with per-adapter success rate dashboard |
| 12 | Evidence/audit trail trust | 8.5 | SHA-256 hash, timestamp, proof path, diff path, A&A locked record, disclaimer | Add reviewer name in audit export | PDF audit pack with court-admissible metadata format |
| 13 | Alert fatigue protection | 5.5 | Risk scoring (HIGH/MEDIUM/LOW) exists but no review queue, no materiality filter | Add unreviewed badge/counter to sidebar nav | Materiality triage, source-health-driven suppression, noise threshold per source |
| 14 | Customer onboarding | 6.5 | 3-step form clear; source layers shown; no source readiness visibility before plan selection | Add readiness status per source layer in step 2 | Guided source selection based on buyer's regulated activities + real readiness preview |
| 15 | Pricing fairness | 7.0 | $199 is fair for pilot; $399 partially fair; but plan.py vs website mismatches undermine trust | Reconcile plan.py source_limit (13 vs 62) and retention (180 vs 365) with external copy | Honest plan cards with live source count per plan from API |
| 16 | Demo readiness | 7.5 | Demo script exists, proof-backed demo script exists, concentration caveat included | Remove all hardcoded mock from any demo-adjacent surface | Full live demo with real evidence record, real diff, real A&A — zero mock |
| 17 | $199 pilot readiness | 7.5 | Ready for narrow founder-led CBUAE/AML pilot; cannot do broad self-serve | API-drive dashboard counts, fix AlertsPage mock | Full source readiness review delivery within 24h |
| 18 | $399 UAE Monitor readiness | 5.5 | Premature for broad self-serve; fair only for CBUAE/AML-heavy with high-touch | Build global review queue + fix all 4 structural flaws | VARA coverage ≥8 sources, DIFC active, email delivery production-grade |
| 19 | $749 Professional readiness | 4.0 | Plan.py still says $399 is "professional"; no reconciliation; no PDF; no annual billing | Reconcile plan naming, pricing, and capabilities with real feature state | A&A export PDF, multi-user RBAC, annual billing, 12-month retention |
| 20 | Enterprise readiness | 2.0 | No SOC 2, no RBAC, no SLA, no API docs, no multi-workspace, no reference customers | Create security/data page (even minimal) | SOC 2 Type II, RBAC, SSO, SLA document, enterprise MSA |

---

## 3. What Is Already Strong

These are real strengths. Not inflated. Not false.

- **Proof architecture is correct.** FAILED ≠ UNCHANGED is enforced. Content hashes are SHA-256 of normalized text, not raw HTML. Hash collisions are detected and block activation. This is meaningful.
- **62 real readiness-supported sources.** All have documented activation paths. No fake "covered" sources. The 4 remediation sources are explicitly held with documented reasons. This honesty is unusual and valuable.
- **A&A MVP is implemented and gated correctly.** Assessment is blocked without a saved evidence record. Impact levels (monitor, policy_review, escalate) are meaningful. Review history is stored and retrievable. Disclaimer is included in every export.
- **Forbidden phrases enforcement is strong.** The weekly brief generator blocks "guarantee compliance," "prevent fines," "ensure compliant," "certified," "official partner." The legal scan gate exists and is tested.
- **Sources page is live API-driven.** Status, extraction quality, last checked, and health are fetched from `/api/sources/status`, not mock. This is the most trust-sensitive page and it works correctly.
- **EvidencePage is the strongest page in the product.** Hash, URL, proof path, diff path, quality label, assessment section, review history — all present, all meaningful, all correctly gated.
- **206 tests covering core pipeline.** No meaningful feature in the evidence trail or brief generation pathway goes untested.
- **Legal copy discipline.** "Monitoring intelligence only. Not legal advice." appears consistently across EvidencePage, email test-mode, audit export, and brief output.
- **Honest remediation display.** The 4 remediation sources are not hidden. They appear on the Sources page with status "Needs remediation." This builds more trust than pretending they work.
- **Source Lab is a useful lead tool.** A prospect can test any public URL before committing. This reduces buyer risk and differentiates from vendors who hide source readiness.

---

## 4. What Is Still Weak

Ranked by customer impact.

1. **AlertsPage.jsx uses MOCK_ALERTS from appMockData.** This is the only remaining authenticated page that serves raw mock data without a SAMPLE/DEMO label on the records themselves. A prospect who clicks into Alerts and sees "Reviewed sample" in the status column has lost trust.

2. **Dashboard source counts (66/62/4) are hardcoded JSX constants.** If the source registry changes, the dashboard will show wrong numbers until someone manually edits DashboardHome.jsx. This is not a live truth signal.

3. **Plan price mismatch between strategy docs and code.** Plan.py says professional is $399 with 13 sources and 180-day retention. Pricing strategy says Professional = $749 with 62 sources and 12-month retention. The website shows $399. None of this is reconciled. When a prospect asks "what do I actually get for $399?" the answer depends on which document they read.

4. **No global review queue.** The MLRO's primary workflow — see all changed sources, triage by risk, acknowledge/assess each, mark complete — has no single page in the dashboard. EvidencePage shows individual records. AlertsPage shows mock data. Neither is the command center an MLRO needs.

5. **VARA coverage at 3 readiness-supported sources.** VARA-licensed entities are described as the primary ICP in STATUTEPROOF_CONTEXT.md. 3 VARA sources is inadequate for this positioning. VARA rulebook PDFs are not extracted.

6. **Email delivery is test-mode only.** The local outbox works. No external SMTP is wired. No production email is ever sent. An MLRO who signs up expecting to receive a brief in their inbox will be disappointed.

7. **PDF export does not exist.** The compliance file is a PDF. Markdown audit exports are technically correct but professionally inadequate for a document that will be placed in an inspection folder.

8. **Source health historical timeline is not built.** Latest status is visible. No 7/30/90-day sparkline, no trend, no stability report. An MLRO cannot answer "was this source reliably monitored for the past 3 months?" from the current UI.

9. **Onboarding does not show source readiness before plan selection.** A VASP selects VARA in step 2 of onboarding, chooses a plan, and only discovers after activation that VARA has 3 readiness-supported sources. This creates post-purchase disappointment.

10. **AIBriefPage silently falls back to mock data.** If `/api/briefs?market=AE` fails, the page silently shows MOCK_ALERTS labeled "SAMPLE / DEMO." The fallback label is correct but the silent failure is not. A production product would show "No briefs generated yet for this period" rather than serving a mock.

---

## 5. Customer Value Gaps — 9 Buyer Types

---

### Buyer 1: UAE Fintech / Payment Compliance Team

**Current product fit: 8/10**

What they love: 27 CBUAE sources covering payments, consumer protection, AML/CFT, open finance — their entire regulatory stack. Proof-backed diffs, evidence records, A&A workflow.

What worries them: Will the tool generate noise alerts on minor page reformatting? Is the source-health timeline stable? Can they export evidence for a CBUAE inspection?

What stops them paying: No PDF export for the inspection file. No review queue to manage 20+ CBUAE sources. Email delivery is test-mode only.

Missing workflow: Global review queue filtered by CBUAE sources. PDF download of A&A assessment record.

Missing coverage: Minimal — CBUAE is strong. Could add more FTA for firms with cross-tax obligations.

Proof that would convince them: Show a live CBUAE AML/CFT monitoring record from the last 30 days: hash, diff, no-change confirmation, and the A&A record the reviewer filed.

Fair price: $399/month. Would feel cheap at $199.

**Buy today: Yes / Maybe.** Yes at $199 (immediate), Maybe at $399 (needs review queue).

Best offer: "$199 founder-led CBUAE/AML pilot. 5 sources agreed upfront. Weekly source status summary. Evidence records included. Disclaimer: monitoring intelligence only, not legal advice."

Must build before targeting seriously at $399: Review queue, PDF export, production email delivery.

---

### Buyer 2: CBUAE-Heavy Compliance Team (Banking / E-Money)

**Current product fit: 7.5/10**

What they love: Deepest CBUAE coverage available. CBUAE AML/CFT, open finance, consumer protection, payment token, cross-border rulebooks — all readiness-supported.

What worries them: The 43.5% CBUAE concentration makes "UAE Monitor" look like "CBUAE Monitor." If they need DFSA or DIFC alongside CBUAE, the pack feels thin.

What stops them paying: "Is this just a CBUAE tool?" needs to be addressed. If they have any DFSA or DIFC exposure, the gaps are apparent.

Missing: Cleaner proof-of-monitoring certificate per source (per-period no-change confirmation in a format suitable for a CBUAE inspection file).

Fair price: $399/month. At $199 they would buy immediately.

**Buy today: Yes at $199, Maybe at $399.**

Best offer: "$199 pilot focused on CBUAE official sources. Honest scope: coverage is deepest for CBUAE. DFSA, VARA, and DIFC coverage exists but is narrower and should be validated before relying on it."

---

### Buyer 3: VARA-Regulated VASP MLRO

**Current product fit: 5.5/10**

What they love: AML/CFT chain (UAE FIU + EOCN + CBUAE AML), A&A workflow concept, evidence-first approach.

What worries them: VARA is 3 readiness-supported sources. VARA rulebook is not extracted (PDFs). VARA administrative orders archive is not in the pack. The product cannot monitor VARA's primary regulatory outputs reliably.

What stops them paying: "Do you monitor the VARA Rulebook?" Answer: "Not yet — we have 3 VARA sources (enforcement notices listing, main page, and one other). VARA PDF rulebook extraction is planned." This is a dealbreaker for a VARA-primary buyer.

Missing coverage: VARA Virtual Assets and Related Activities Regulations (VARAR), VARA Transfer of Virtual Assets Regulation (TVAR), VARA Compliance & Risk Management Rulebook PDFs, VARA Administrative Orders archive, VARA licensing register changes.

Missing workflow: VARA-specific review view.

Proof that would convince them: A live VARA enforcement notice detection with hash, diff, evidence record, and A&A assessment filed by the MLRO.

Fair price: $199/month for what exists. Cannot justify $399 without VARA rulebook.

**Buy today: Maybe at $199 only, with explicit VARA limitation disclosure.**

Must build before targeting seriously: VARA PDF adapter, 5+ additional VARA sources with stable hashes, rulebook extraction pipeline.

---

### Buyer 4: DFSA / DIFC Compliance Officer

**Current product fit: 6.0/10**

What they love: 8 DFSA readiness-supported sources (AML, rulebook, consultation, enforcement, notices, MLRO letters). Honest disclosure that DIFC laws are under remediation.

What worries them: DIFC laws are not active (0 readiness-supported). DFSA main rulebook source had hash drift (held, not activated). "8 DFSA sources" sounds good, but what exactly are they?

What stops them paying: DIFC laws under remediation means they cannot monitor DIFC court decisions, DIFC Authority authority regulations, or DIFC company law changes. For a DIFC-incorporated entity, this is the most important coverage gap.

Missing: DIFC laws active. DFSA main rulebook re-tested and hash drift resolved. Per-source clarity on what each DFSA source monitors (rulebook section? all DFSA publications?).

Fair price: $199 (pilot, DFSA sources only, DIFC disclosed as remediation). $399 only after DIFC is active and DFSA main rulebook is resolved.

**Buy today: Maybe at $199 with explicit DIFC remediation disclosure.**

Must build before targeting seriously: DIFC laws adapter (Playwright + DevTools selectors), DFSA main rulebook hash drift resolution.

---

### Buyer 5: ADGM / FSRA Regulated Firm

**Current product fit: 7.0/10**

What they love: 10 ADGM/FSRA readiness-supported sources — ADGM FSRA rulebooks, guidance, waivers, enforcement, circulars, ADGM RA circulars. Strong relative coverage.

What worries them: Are the ADGM pages stable? (The ADGM website uses custom web components — some ADGM URLs failed with NAV_SHELL in the past.) The compliance manager cannot tell from the dashboard whether ADGM sources have been stable for the past 30 days.

What stops them paying: No 30-day source stability report. If they experienced a quality drop last week and the monitoring was silently degraded, they would not know from the current UI.

Missing: Source health timeline showing ADGM source stability over time. Per-source monitoring confirmation record.

Fair price: $399/month. Strong ADGM coverage supports the price.

**Buy today: Yes / Maybe at $199–399.**

Best offer: "$199 ADGM/FSRA pilot — 5 ADGM sources agreed upfront. Honest: ADGM website uses custom web components; some pages may show quality drops. Source health is visible and reported."

---

### Buyer 6: Compliance Consulting Firm

**Current product fit: 4.0/10**

What they love: Proof-backed monitoring concept reduces their manual source checking burden. Evidence records they could show clients.

What worries them: They serve multiple clients. StatuteProof is single-workspace. They cannot run Client A's monitoring alongside Client B's monitoring without separate accounts.

What stops them paying: No multi-workspace. No client-branded reports. No role-based access. The product is structurally incompatible with the consulting firm use case.

Missing: Multi-workspace support. White-label brief output. Team roles. Client data isolation.

**Buy today: No. Only viable if they use one workspace for one client and are explicit about that limitation.**

Must build before targeting: Multi-workspace architecture. White-label report output. Minimum 3 months of product work.

---

### Buyer 7: Small Crypto Startup (Sub-$5M Revenue)

**Current product fit: 5.5/10**

What they love: Low price point ($199). Covers the core UAE regulatory sources for a startup VASP (CBUAE AML/CFT, UAE FIU, VARA basics).

What worries them: Budget is the primary concern. $199/month requires board approval at many early-stage startups. They may not have a dedicated MLRO — the CEO or CTO is handling compliance.

What stops them paying: A non-compliance professional opening the dashboard and seeing evidence records, normalized hashes, and diff paths will be confused. The product is not designed for a non-technical compliance manager who has never seen a hash.

Missing: A simplified view for non-MLRO users: "These 3 sources changed this week / These 5 sources were stable this week." Plain English, no technical fields.

Fair price: $99–$199/month. $399 is out of reach.

**Buy today: Maybe at $199 if VARA limitations are explicit.**

Must build before targeting seriously: A "compliance digest" simplified view that hides technical fields and shows only: source name, change status (Changed / Stable), risk level, and "Review required" badge.

---

### Buyer 8: Larger Bank / Enterprise Buyer

**Current product fit: 2.0/10**

What they love: Evidence architecture is technically correct. The principle of monitoring official sources with cryptographic records aligns with what enterprise GRC teams want.

What worries them: Everything else. No SOC 2. No RBAC. No SLA. No API documentation. No reference customers. No enterprise procurement support. No data residency statement. No SSO.

What stops them paying: Their security team will not approve a tool with no SOC 2, no RBAC, and no DPA before it is used for regulatory intelligence. The product is not enterprise-ready and should not be pitched as such.

**Buy today: No.**

Must build before targeting: SOC 2 Type II (12-18 months of process), RBAC, audit logs, API documentation, enterprise MSA template, at least 2 reference customers. This is a Level 4 product goal.

---

### Buyer 9: Law Firm with UAE Compliance Practice

**Current product fit: 4.5/10**

What they love: Evidence-backed monitoring with strong legal disclaimers (they are the legal adviser and do not want the tool to blur that boundary). Could use StatuteProof as a background intelligence layer for staying current before advising clients.

What worries them: UAE-only coverage. Multi-jurisdiction clients need global or at least GCC coverage. The brief format says "monitoring intelligence only, not legal advice" prominently — good for their compliance but possibly confusing when they share a brief with a client who expects legal analysis.

What stops them paying: Geographic limitation. A law firm advising on Saudi Arabia + UAE + Qatar cannot use a UAE-only tool. Multi-jurisdiction is a structural gap, not a feature gap.

Missing: At minimum GCC coverage (Saudi Arabia SAMA, Qatar QCB, Bahrain CBB) to serve a multi-jurisdiction law firm client base.

Fair price: $199–$399 if UAE-only is sufficient for their practice.

**Buy today: Maybe, only if all clients are UAE-only.**

---

## 6. Website / UI / UX Review

### What Feels Premium
- Dark theme (#07111F background, #16D9F5 cyan accent) is clean and professional
- RadarMark branding component is distinctive
- SourceTransparencyMatrix and SourceCoverageTable are genuinely informative and trust-building
- EvidencePage is the best page in the product — professional, dense, correct
- Source Lab (test any URL) is a confident, transparent feature
- PlanBanner showing plan limitations is honest — does not oversell locked features

### What Feels Confusing
- The word "Acknowledge & Assess" will confuse non-technical compliance managers the first time they see it. Should be preceded by context: "Human Review Required" → "Review this change" → "Record your assessment."
- AlertsPage looks like a real data page but serves MOCK_ALERTS. The "Reviewed sample" status label in the status column will confuse a prospect who does not know what "sample" means here.
- The OnboardingPage (step 2) shows "Capital Market Authority (Limited)" — "Limited" is unexplained. Is it limited extraction? Limited sources? No tooltip or explanation.
- The dashboard shows "Plan enabled" even before source readiness review is complete. "Plan enabled" sounds like monitoring is running. It is not.
- ChoosePlanPage and BillingPage both exist but plan selection is manual-only. The flow between "choose a plan" and "actual monitoring begins" is not explained in the UI.

### What Feels Like a Prototype
- AlertsPage with MOCK_ALERTS — "Reviewed sample" text is visible in the status column
- AIBriefPage silently falling back to mock with a tiny "SAMPLE / DEMO" label
- Dashboard source counts (66/62/4) being hardcoded — a developer reading the JSX knows this immediately
- ReportsPage using MOCK_REPORTS — "No briefs for your selected profile yet" message is reasonable, but it appears alongside mock report cards

### What Creates Trust
- EvidencePage with real hashes, real proof paths, real diff paths
- Sources page fetching live data from the API
- "Monitoring intelligence only. Not legal advice." appearing consistently
- Remediation sources shown honestly (not hidden)
- Source Lab showing quality scores and failure reasons before any commitment
- The A&A assessment blocked without a saved evidence record — this gate builds confidence

### What Destroys Trust
- AlertsPage mock data without a prominent banner ("These are sample alerts — your real alerts will appear here after monitoring begins")
- Dashboard source counts hardcoded in JSX — if anyone checks the source code, they see it
- AIBriefPage silent API failure fallback to mock
- Pricing page showing $199/$399 while pricing strategy docs say $349/$749 — no reconciliation means whoever reads both documents sees a company that does not know its own prices
- Plan professional: "source_limit: 13" in plan.py while the product externally describes "62 readiness-supported sources"

### What Should Be Removed
- Any hardcoded MOCK_ data in authenticated app pages — no exceptions
- The word "Limited" next to Capital Market Authority in onboarding step 2 without an explanation
- "AI Brief" page name — sounds like an AI feature that generates legal interpretations, which is exactly what StatuteProof must not imply. Rename to "Monitoring Brief" or "Weekly Brief"

### What Should Be Added
- Global review queue page (see Part 11 — Add)
- Source readiness preview in onboarding step 2 (tooltip or inline text per source layer)
- Per-source monitoring confirmation record (no-change certificate)
- A "What does this mean?" tooltip on technical fields (normalized_hash, proof_block_path, extraction_quality)
- A data freshness indicator on the dashboard: "Sources last checked: 6 hours ago"

### What Should Be Shown More Clearly
- The distinction between "Readiness-supported" and "Monitoring active" — are sources being monitored automatically on a schedule, or only when manually triggered?
- The monitoring cadence: how often does StatuteProof check each source? This is not visible anywhere in the dashboard.
- The remediation timeline: "DIFC laws: under remediation. Expected resolution: not yet confirmed." The current UI shows "Needs remediation" without any context.

---

## 7. Source Pack Review

### Coverage Distribution (62 readiness-supported)

| Regulator | Count | % | Assessment |
|-----------|------:|--:|-----------|
| CBUAE | 27 | 43.5% | Genuinely strong. Payments, open finance, AML/CFT, consumer protection all covered. Risk: overrepresentation. |
| ADGM/FSRA | 10 | 16.1% | Strongest non-CBUAE segment. Rulebooks, guidance, waivers, enforcement, circulars. |
| DFSA | 8 | 12.9% | Adequate. AML, rulebook, consultation, enforcement, notices, MLRO letters. DFSA main rulebook held (hash drift). |
| UAE FIU / EOCN | 7 | 11.3% | Strong for AML/CFT buyers. AML/CFT laws, typology reports, guidance, sanctions. |
| SCA | 4 | 6.5% | AML/CFT, circulars, FATCA/CRS, corporate governance. Adequate for SCA-regulated firms. |
| VARA | 3 | 4.8% | **Too thin.** Enforcement notices listing, main page. No rulebook PDFs, no administrative orders. |
| Federal/Legislation/Tax | 3 | 4.8% | Thin. UAE Legislation Portal, EOCN (counted in FIU/EOCN above), FTA/MoF minimal. |
| DIFC | 0 | 0% | Under remediation. No active DIFC source. Critical gap for DIFC-established firms. |

### Strongest Sources (Commercial Value)
- AE-dfsa-aml-ctf-rulebook (DFSA AML module — every DFSA firm needs this)
- AE-cbuae-aml-cft-regulations (CBUAE AML/CFT — every UAE regulated firm needs this)
- AE-uaefiu-aml-typology-reports (UAE FIU typology — MLRO gold for understanding enforcement priorities)
- AE-cbuae-open-finance-regulation (CBUAE — critical for any UAE fintech with open banking exposure)
- AE-cbuae-payment-token-svs-regulation (CBUAE — crypto/payment token firms in UAE)
- AE-adgm-fsra-regulations-guidance (ADGM FSRA — essential for ADGM-regulated firms)

### Weakest Sources (Padding Risk)
- Ministry of Economy generic pages (broad economic policy, low regulatory signal value)
- Ministry of Finance generic pages (budget policy, not compliance-specific)
- CBUAE generic announcement pages (duplicate coverage of what AML/CFT specific sources cover)
- ADGM generic media/press pages (PR content, not regulatory text)

### What Is Missing
- **VARA**: Virtual Assets and Related Activities Regulations (VARAR), Transfer of Virtual Assets Regulation (TVAR), Compliance & Risk Management Rulebook, Administrative Orders archive
- **DIFC**: Laws and Regulations portal (currently in remediation), DIFC Court decisions, DIFC Authority circulars
- **DFSA**: Main rulebook (held due to hash drift — needs re-testing and re-activation)
- **FTA**: More specific Federal Tax Authority guidance notes (VAT, corporate tax, excise)
- **GCC (future)**: Saudi Arabia SAMA, Qatar QCB, Bahrain CBB — needed before law firms become a viable buyer

---

## 8. Evidence / Audit Workflow Review

### What Is Strong
- **Proof chain is complete and correct.** SHA-256 hash of normalized text, timestamp, proof block path, diff path — all stored and retrievable.
- **A&A MVP is gated correctly.** Assessment blocked without `proof_block_path` and `evidence_record_id`. This is the most important gate in the workflow.
- **Review history is stored and retrievable.** Multiple assessments per evidence record are accumulated. The `reviewHistory()` API returns the full chain.
- **Export is legally safe.** Markdown/HTML audit pack includes disclaimer on every export. Demo label is added to sample/demo exports only (not real exports).
- **Audit log in JSONL.** Evidence assessments stored in `data/evidence_assessments/assessments.jsonl`. Simple, append-only, reviewable by a human.

### What Is Incomplete
- **PDF export does not exist.** The compliance file is a PDF file. An MLRO who downloads a Markdown audit pack cannot give it to an auditor without converting it. This is a workflow gap, not a nice-to-have.
- **No per-source no-change confirmation record.** The evidence chain shows what changed. It does not have a clean "certificate of monitoring" for sources where nothing changed. Auditors often want to see proof of monitoring for stable periods, not just for change events.
- **No reviewer name captured in the UI.** The A&A assessment stores `reviewer_user_id` in the data model, but the current frontend does not show the reviewer's name on the assessment card. Auditors expect to see "Reviewed by: [Name], [Date]."
- **Source health historical timeline is not built.** `source_health_timeline.py` exists in the backend. The frontend shows latest health status only. No 7/30/90-day chart.
- **No bulk assessment or bulk acknowledgement.** If 20 sources show UNCHANGED for 4 weeks, the MLRO has to open each evidence record individually to acknowledge it. Bulk "Acknowledge all UNCHANGED this week" would save time.

### What Is Missing
- **MLRO Review Queue:** A page that shows all evidence records in a table with columns: Source, Date, Status (CHANGED/UNCHANGED/FAILED), Risk Level, A&A Status (Pending/Acknowledged/Assessed), with filters by source, period, risk level, and A&A status. This is the core workflow page.
- **Email notification on new evidence record.** When a CHANGED event is detected for a source, the MLRO should receive an email notification (in production). Currently test-mode only.
- **Evidence integrity verification.** A "Verify evidence record" button that re-hashes the stored content and confirms it matches the recorded hash. This is what an auditor would want to see.

---

## 9. Pricing / Will They Pay?

### Critical Discrepancy: Prices Are Not Reconciled

This is the first thing to fix in pricing:

| Plan (PLAN_DISPLAY name) | plan.py backend price | Website PricingPage price | Pricing strategy target | Mismatch? |
|--------------------------|----------------------|--------------------------|------------------------|-----------|
| Source Readiness Review | $0 | Free | Free | No |
| Founding Pilot (starter_pilot) | $199 | $199 | $349 | Yes — strategy says $349 |
| UAE Monitor (professional) | $399 | $399 | $749 | Yes — strategy says $749 |
| Compliance Consultant | $0 / custom | Talk to us | Custom | No |

Additionally, `plan.py` says professional has `source_limit: 13` and `retention_days: 180`. But every external document describes the professional plan as covering 62 readiness-supported sources with 12-month retention. These are different products.

**Verdict:** The pricing strategy document is aspirational and has not been implemented. The actual code, website, and live product are at $199/$399. This is fine for now — the strategy document is a roadmap — but the mismatch creates internal confusion and will create customer confusion if they ever see both.

**Recommendation:** Freeze the pricing strategy document and govern by plan.py as the source of truth for now. Do not raise prices until the feature set matches the higher tier.

---

### Will They Pay at Each Price Point?

**$199/month (Founding Pilot, 3 sources, manual activation)**

Will they pay: **Yes**, for the right narrow ICP (CBUAE/AML/payments-heavy, founder-led, explicit scope agreement).

What makes them pay: The source readiness review shows their sources are active. The founder explains the evidence trail. The prospect gets a sample A&A record and sees it is real work.

What makes them not pay: Dashboard shows mock data. AlertsPage says "Reviewed sample." They feel they are paying for a prototype.

**Fix before charging $199:** AlertsPage live data or honest empty state. Dashboard counts from API.

---

**$399/month (UAE Monitor, 13 sources, manual activation)**

Will they pay: **Maybe**, only for CBUAE/AML-heavy buyers with high-touch founder support.

What makes them pay: Source coverage matches their profile. A&A workflow works. Source health visible. Weekly brief delivered via email (not just dashboard).

What makes them not pay: AlertsPage mock data. No review queue. Email is test-mode. DIFC or VARA buyer discovers gaps after signing.

**Fix before broadly charging $399:** Review queue, email delivery production-grade, AlertsPage live, DIFC out of remediation.

---

**$749/month (a future Professional tier)**

Will they pay: **Not yet.** No reconciled plan.py. No PDF export. No multi-user confirmed. No 12-month retention confirmed in plan.py (currently 180 days). No annual billing option.

**Fix before charging $749:** Complete all Level 2 items in the 10/10 roadmap (see Part 14).

---

## 10. Competitor Comparison

### Where Big Companies Destroy StatuteProof

- **Global coverage.** Thomson Reuters Regulatory Intelligence, CUBE, Wolters Kluwer OneSumX, and LexisNexis cover hundreds of jurisdictions with thousands of sources. StatuteProof is UAE-only and not comparable on breadth.
- **Analyst-grade legal intelligence.** These platforms have regulatory experts who write summaries, horizon scanning reports, and obligation mappings. StatuteProof produces monitoring records with source text — not expert analysis.
- **Enterprise workflow maturity.** Obligation management, policy control mapping, multi-user governance, audit trails, SSO, SLA — enterprise GRC platforms have years of workflow investment that StatuteProof does not.
- **Brand trust.** An MLRO at a bank will trust Thomson Reuters before StatuteProof. This is a reality, not a criticism. It takes time and reference customers to build institutional trust.
- **Security posture.** SOC 2, data residency, enterprise DPA, MSA — none of these exist at StatuteProof yet.

### Where StatuteProof Can Win

- **UAE-specific depth.** No large competitor has 62 UAE official regulatory sources with documented activation paths, extraction quality scores, and publicly visible remediation status. StatuteProof knows the UAE regulatory source landscape more granularly than any enterprise platform's UAE coverage layer.
- **Evidence-first transparency.** Enterprise platforms sell regulatory intelligence. StatuteProof sells proof of monitoring. These are different. An MLRO who needs to show an auditor "we monitored this source on this date, here is the hash" will not find that capability in most regulatory intelligence platforms.
- **Accessible price.** $199–$399/month is 10–50× cheaper than enterprise platforms and dramatically below manual monitoring labor cost equivalent. For a 10-person VASP, there is no budget for CUBE — StatuteProof fits.
- **Honest limitation disclosure.** StatuteProof shows extraction quality, failure reasons, and remediation status openly. Enterprise platforms do not surface source health this explicitly. This transparency builds trust with technically sophisticated compliance professionals.
- **Founder-led customization.** Early-stage means a prospect talks directly to the person who built the product. That shortens trust cycles.

### Where StatuteProof Is Not Comparable Yet

- Enterprise regulatory change management workflows
- Legal interpretation or obligation mapping
- Global or multi-jurisdiction coverage
- AML/KYC screening (ComplyAdvantage / LSEG World-Check territory — completely adjacent)
- Bank-grade vendor procurement

### What to Copy Conceptually

- **Regology's packaging clarity:** Tiers based on workflow completeness, not just source count. StatuteProof should sell workflow tiers: "Monitor" (evidence only), "Review" (evidence + A&A), "Audit" (evidence + A&A + PDF + review queue + email delivery).
- **Clausematch's acknowledgement trail:** Policy acknowledgement and version history as the primary audit artifact. StatuteProof's A&A is the equivalent and should be positioned more prominently.
- **ChangeDetection.io's simplicity for the simplified view:** A non-technical compliance manager at a small VASP needs ChangeDetection-level simplicity with StatuteProof-level evidence depth. A simplified "digest mode" would serve this buyer.

### What Never to Copy

- Global coverage claims — StatuteProof cannot deliver this
- Obligation mapping — out of scope and legally dangerous
- Analyst-grade interpretation — these are legal advice adjacent

### Honest Competitive Positioning Statement

"StatuteProof monitors UAE official regulatory sources with cryptographic evidence records and human-reviewed briefs. We are not a regulatory intelligence platform, not a legal advice service, and not a global compliance solution. We are UAE-specific official-source monitoring with a transparent evidence trail, for compliance teams that need more than manual website checks and less than an enterprise regulatory intelligence contract."

---

## 11. What to Add

Prioritized by customer impact.

### A1. Global MLRO Review Queue — CRITICAL, Build First

**What:** A dedicated page in the dashboard showing all evidence records with unread/unassessed status. Columns: Source, Last Checked, Status (CHANGED/UNCHANGED/FAILED), Risk Level, A&A Status (Pending / Acknowledged / Assessed / No Action). Filter by: source, date range, risk level, A&A status. Sort by: most recent, highest risk, pending assessment.

**Why:** This is the MLRO's command center. Without it, the A&A workflow is buried in individual evidence record pages. The MLRO has no way to see "what needs my attention today" in one place.

**Customer impact:** HIGH — this is what separates a $399 product from a $199 product.

**Priority:** P0 — build before any sales push at $399.

**Files involved:** New `ReviewQueuePage.jsx` in `components/app/`, new API route `GET /api/reviews/queue?status=pending&risk=HIGH` in `api.py`, uses existing `evidence_assessment.py` data.

**Effort:** Medium — 5–8 days.

---

### A2. Production Email Delivery — CRITICAL

**What:** Wire the email delivery pipeline to a real SMTP provider (SendGrid, Postmark, or SES). Add recipient verification. Send weekly brief to client's registered email. Include full disclaimer in email body.

**Why:** An MLRO who signs up expects to receive a brief in their inbox. Test-mode local outbox is not a product. Without email delivery, the product requires the MLRO to log in to the dashboard to discover if anything changed — compliance professionals do not have that habit.

**Customer impact:** HIGH — directly determines whether recurring payment feels justified.

**Priority:** P0 — required before $399 can be charged broadly.

**Files involved:** `email_delivery.py` (already has the structure), `.env` SMTP configuration, Integrations page email test-mode → production mode toggle.

**Effort:** Medium — 3–5 days including SMTP provider setup and deliverability testing.

---

### A3. API-Driven Dashboard Source Counts — HIGH

**What:** Replace hardcoded `enabled: 66, supported: 62, remediation: 4` constants in `DashboardHome.jsx` with a live API call to `/api/sources/status/summary`.

**Why:** Hardcoded JSX constants mean the dashboard will show wrong numbers if the source registry changes. A developer who reads the JSX sees `const PACK_STATS = { enabled: 66, supported: 62, remediation: 4 }` and knows the dashboard is not live. This is a trust signal to technical buyers.

**Customer impact:** MEDIUM-HIGH — mostly a trust issue, not a workflow issue.

**Priority:** P1 — 1 day effort, high trust return.

**Files involved:** `DashboardHome.jsx`, new API route `GET /api/sources/summary` returning `{enabled, supported, remediation}`.

**Effort:** Low — 1 day.

---

### A4. AlertsPage Live Data or Honest Empty State — CRITICAL

**What:** Replace `MOCK_ALERTS` in `AlertsPage.jsx` with either (a) live data from `/api/alerts` or (b) an honest empty state: "Your reviewed alerts will appear here. No alerts have been approved for your profile yet." Remove the `MOCK_ALERTS` import entirely.

**Why:** "Reviewed sample" in the status column is the single most trust-damaging visible element in the authenticated dashboard. Any prospect who reads it will lose confidence.

**Customer impact:** HIGH — direct trust damage visible immediately after login.

**Priority:** P0 — 1–2 days effort, maximum trust return.

**Files involved:** `components/app/AlertsPage.jsx`, `data/appMockData.js`.

**Effort:** Low-medium — 1–2 days.

---

### A5. PDF Export of A&A Audit Pack — HIGH

**What:** Add PDF generation to the audit export pipeline. The HTML rendering already exists in `render_audit_pack_html`. Add wkhtmltopdf or Playwright print-to-PDF as a PDF provider. Output a clean PDF with the disclaimer on every page footer.

**Why:** The compliance file is a PDF. A Markdown audit pack is technically correct but professionally inadequate for an MLRO who needs to place it in an inspection folder.

**Customer impact:** HIGH — directly affects whether the A&A workflow is used in practice.

**Priority:** P1 — required before the product is called "Professional."

**Files involved:** `audit_export.py`, new API route `GET /api/evidence/export?format=pdf`, new dependency in `requirements.txt`.

**Effort:** Medium — 3–5 days including edge case handling and testing.

---

### A6. Source Health 7-Day Sparkline — MEDIUM

**What:** Add a small sparkline chart (7 data points) to each source card on the Sources page showing MONITOR_OK / QUALITY_DROP / FAILED status over the past 7 monitoring runs.

**Why:** "Latest status" is not enough for an MLRO doing compliance due diligence. They want to see that the source has been stable for the past week, not just that the last run passed.

**Customer impact:** MEDIUM — meaningful for trust, not yet a dealbreaker.

**Priority:** P2 — after P0 and P1 items.

**Files involved:** `SourcesPage.jsx`, `source_health_timeline.py`, new API route returning last 7 run statuses per source.

**Effort:** Medium — 3–4 days.

---

### A7. Source Readiness Preview in Onboarding Step 2 — HIGH

**What:** In OnboardingPage step 2 (source layers selection), add inline status per source layer: "VARA: 3 readiness-supported sources (VARA PDF extraction in progress)" or "DFSA: 8 readiness-supported sources" or "DIFC: under extraction remediation."

**Why:** A VASP selects VARA in step 2, picks Professional plan, and only after activation discovers VARA has 3 sources. Post-purchase disappointment. Pre-purchase disclosure prevents churn and builds trust.

**Customer impact:** HIGH — prevents post-purchase churn and builds trust.

**Priority:** P1.

**Files involved:** `OnboardingPage.jsx`, static source coverage data (can be hardcoded per layer initially).

**Effort:** Low — 1–2 days.

---

### A8. Monitoring Cadence Visible in Dashboard — MEDIUM

**What:** Add a visible "Last monitored: [X hours ago]" indicator to the dashboard. Show which sources were checked in the last monitoring cycle. Show the next scheduled monitoring run time.

**Why:** An MLRO cannot answer "is my monitoring current?" from the current dashboard. They need to know when StatuteProof last ran. Without this, "monitoring" feels like a black box.

**Customer impact:** MEDIUM — trust and confidence signal.

**Priority:** P2.

**Files involved:** `DashboardHome.jsx`, `scheduler.py`, new API route returning last/next run timestamp.

**Effort:** Low-medium — 2 days.

---

### A9. Per-Source No-Change Confirmation Record — MEDIUM

**What:** A downloadable "Source Monitoring Record" per source per period: "StatuteProof monitored [source] at [URL] on [date] at [time UTC]. Content fingerprint: [hash[:16]...]. Extraction quality: [GOOD/LIMITED]. No content change detected since prior check on [date]. Monitoring intelligence only. Not legal advice."

**Why:** An MLRO going into an inspection needs to show what monitoring was done during periods of no change. The current evidence records show change events. A no-change confirmation is a different artifact.

**Customer impact:** MEDIUM-HIGH — directly useful for inspections.

**Priority:** P2.

**Files involved:** `audit_export.py`, `EvidencePage.jsx`, new export format.

**Effort:** Medium — 3 days.

---

### A10. Security and Data-Handling Page — MEDIUM

**What:** A static page (can be in LegalPage or separate) stating: "Data is processed in [region]. We use AES-256 at rest, TLS 1.3 in transit. We do not share client data with third parties. Access is restricted to your account and the StatuteProof team for monitoring operations only. We are working toward SOC 2 Type II compliance. Evidence records are retained for [retention_days] days per your plan. To request data deletion, contact [email]."

**Why:** Any compliance professional evaluating a tool for regulatory intelligence data will ask about data handling. Without a security page, enterprise buyers cannot complete their vendor assessment.

**Customer impact:** MEDIUM — blocks enterprise. Not needed for $199 pilots.

**Priority:** P2.

**Files involved:** New route in `App.jsx`, new `SecurityPage.jsx` component.

**Effort:** Low (content writing + simple component) — 1 day.

---

## 12. What to Remove

### R1. MOCK_ALERTS Import from AlertsPage.jsx — CRITICAL

**Why:** Trust-destroying. "Reviewed sample" is visible in the status column.

**Customer impact:** High negative.

**Priority:** P0. Remove today.

**File:** `components/app/AlertsPage.jsx`, `data/appMockData.js`

---

### R2. Hardcoded `PACK_STATS` Constants in DashboardHome.jsx — HIGH

**Why:** Makes the dashboard a static display, not a live product.

**Customer impact:** Medium trust damage (only visible to technical users who check source).

**Priority:** P1.

**File:** `components/app/DashboardHome.jsx`

---

### R3. "AI Brief" Page Name and Label — MEDIUM

**Why:** "AI Brief" implies the product uses AI to generate legal interpretations. StatuteProof's positioning is explicitly "not legal advice." The name creates confusion and positioning risk.

**What to replace with:** "Monitoring Brief" or "Weekly Brief" — accurate and unambiguous.

**Customer impact:** Medium — positioning and legal safety.

**Priority:** P2.

**Files:** `App.jsx` (route), `AIBriefPage.jsx` (rename to `MonitoringBriefPage.jsx`), `AppSidebar.jsx` (nav link).

---

### R4. Silent API Failure Fallback to Mock in AIBriefPage — MEDIUM

**Why:** If the briefs API fails, the page silently shows MOCK_ALERTS labeled "SAMPLE / DEMO." A production product would show a clear error state: "Brief generation is not available right now. Your monitored briefs will appear here."

**Priority:** P1 after removing AIBriefPage mock dependency.

**File:** `components/app/AIBriefPage.jsx`

---

### R5. "Limited" Label in Onboarding Without Explanation — LOW

**Why:** "Capital Market Authority (Limited)" in step 2 of onboarding is unexplained. "Limited" could mean limited sources, limited extraction, limited availability. Add a tooltip or rename.

**Priority:** P3.

**File:** `components/app/OnboardingPage.jsx`

---

### R6. MOCK_REPORTS from ReportsPage — MEDIUM

**Why:** Same reasoning as AlertsPage. Authentic empty state is more trust-building than mock report cards.

**Priority:** P1 (after AlertsPage).

**File:** `components/app/ReportsPage.jsx`

---

## 13. What to Simplify

### S1. Acknowledge & Assess Entry Point — HIGH

**Current state:** An MLRO navigates to EvidencePage, finds a specific evidence record, and sees a button labeled "Acknowledge & Assess." If they have never used the product before, they do not know what this means.

**What to simplify:** Add a workflow guide: When an evidence record shows CHANGED or FIRST_SEEN, show a prominent banner: "This source has changed. Human review is required before delivery. → Review and Acknowledge." The "Acknowledge & Assess" button should have a sub-label: "Record your review and next action."

**Customer impact:** HIGH — reduces friction in the most important workflow.

**Effort:** Low — UI copy and layout change.

---

### S2. Evidence Record Technical Fields — MEDIUM

**Current state:** EvidencePage shows normalized_hash, raw_hash, proof_block_path, diff_json_path, extraction_quality in a dense card. A non-technical compliance manager is overwhelmed.

**What to simplify:** Add two views: "Summary" (change status, source, date, risk level, and one-sentence extraction quality note) and "Technical" (current full display with hashes and paths). Default to Summary. Technical view available on expand/toggle.

**Customer impact:** MEDIUM — makes the product accessible to non-technical MLROs.

**Effort:** Medium — UI reorganization.

---

### S3. Onboarding Source Layers → "What do you need to monitor?" — MEDIUM

**Current state:** Step 2 asks the user to select "source layers" — a technical term that means nothing to a non-technical compliance manager.

**What to simplify:** Rename to "What regulatory bodies matter to your firm?" and add sub-labels: "CBUAE — Central Bank, payments, AML/CFT" | "VARA — Virtual assets, Dubai crypto licensing" | "DFSA — Dubai International Financial Centre" | "ADGM/FSRA — Abu Dhabi Global Market" | etc.

**Customer impact:** HIGH — onboarding drop-off reduction.

**Effort:** Low — UI copy change.

---

### S4. Plan Capability Table in BillingPage — MEDIUM

**Current state:** The plan capabilities table shows "pdf_export: false, audit_export: false, multiple_workspaces: false" across all plans. This is an honest display but it lists absence of features, which reads as a weakness list.

**What to simplify:** Show what each plan includes (not what it lacks). Replace missing features with "Roadmap" badges or simply do not list them. Show the value each plan delivers: "Sources monitored: 3 | Evidence records: Yes | A&A review: Yes | Export: Markdown/HTML."

**Customer impact:** MEDIUM — reduces the feeling that the product is incomplete.

**Effort:** Low — UI copy and layout.

---

### S5. Source Health Status Labels — LOW

**Current state:** Status labels include "MONITOR_OK," "QUALITY_DROP," "NAV_SHELL_ONLY," "SELECTOR_BROKEN" — technical codes from the monitoring engine, not customer-facing language.

**What to simplify:** Map to customer-friendly labels: "MONITOR_OK → Readiness supported" | "QUALITY_DROP → Source extraction degraded — under review" | "NAV_SHELL_ONLY → Page content not accessible for monitoring" | "SELECTOR_BROKEN → Source format changed — remediation queued."

**Customer impact:** LOW-MEDIUM — trust signal for non-technical users.

**Effort:** Low — label mapping in source status rendering.

---

## 14. 10/10 Roadmap by Level

---

### Level 1: Sellable Controlled Pilot — Goal: Customer Pays $199 and Feels It Is Fair

**Readiness today: 75%**

**Required product features:**
- [ ] AlertsPage.jsx: remove MOCK_ALERTS, replace with live API or honest empty state (**P0**)
- [ ] DashboardHome.jsx: API-drive source counts (66/62/4) (**P1**)
- [ ] Monitoring cadence visible: "Sources last checked: X hours ago" (**P2**)
- [ ] Source readiness preview in onboarding step 2 (**P1**)
- [ ] AIBriefPage: remove silent mock fallback, honest empty state (**P1**)
- [ ] ReportsPage: remove MOCK_REPORTS (**P1**)

**Required source coverage:**
- 62 readiness-supported sources (already done)
- Honest limitation disclosure for VARA (3 sources) and DIFC (0 active)

**Required UI/UX:**
- Zero hardcoded mock data visible to authenticated users
- SAMPLE/DEMO labels on all demo/sample surfaces only
- Source layer descriptions in onboarding step 2
- "What does this mean?" tooltips on hash/proof_path fields

**Required trust signals:**
- "Monitoring intelligence only. Not legal advice." on dashboard home (currently only on EvidencePage and exports)
- Founder contact information visible (for manual activation questions)
- Legal/Privacy/Terms footer links working

**Required delivery workflow:**
- Email test-mode working (already done)
- Manual activation process documented and reliable (< 24h)

**Required evidence/audit workflow:**
- A&A MVP working (already done)
- Audit export (Markdown/HTML) working (already done)
- Disclaimer on all exports (already done)

**Required support/ops:**
- Support email staffed (< 24h response)
- Source readiness review delivered within 24h of request

**Required legal/security:**
- Legal, Privacy, Terms pages complete
- No SAMPLE/DEMO label missing from any demo output

**Required validators/tests:**
- `validate_mvp_trust_workflow.py` passing (already exists)
- No MOCK_ constants in authenticated pages (validator check)

**Exact tasks to reach Level 1:**
1. Remove MOCK_ALERTS from AlertsPage (P0, 1 day)
2. API-drive DashboardHome source counts (P1, 1 day)
3. Remove MOCK_REPORTS from ReportsPage (P1, 1 day)
4. Remove silent mock fallback from AIBriefPage (P1, 1 day)
5. Add source readiness preview to OnboardingPage step 2 (P1, 2 days)
6. Add "Monitoring intelligence only. Not legal advice." to DashboardHome (P2, 0.5 days)
7. Add "Sources last checked: X hours ago" to dashboard (P2, 1 day)

**Total effort: ~7–8 days**

---

### Level 2: Strong UAE Monitor — Goal: Customer Pays $399 and Feels It Is Cheap

**Readiness today: 45%**

**Required product features (beyond Level 1):**
- [ ] Global MLRO Review Queue page (**P0, 5–8 days**)
- [ ] Production email delivery via SMTP (**P0, 3–5 days**)
- [ ] PDF export of A&A audit pack (**P1, 3–5 days**)
- [ ] Source health 7-day sparkline on Sources page (**P2, 3 days**)
- [ ] Per-source no-change monitoring confirmation record (**P2, 3 days**)
- [ ] Reviewer name visible on A&A assessment card (**P1, 1 day**)
- [ ] Plan.py reconciliation: fix source_limit and retention_days for professional plan (**P0, 0.5 days**)
- [ ] Bulk acknowledgement: "Acknowledge all UNCHANGED sources this week" (**P2, 3 days**)

**Required source coverage:**
- DFSA main rulebook hash drift resolved and re-activated (currently held)
- DIFC laws active (out of remediation) or explicitly disclosed with expected timeline
- VARA expanded to at least 5 readiness-supported sources

**Required UI/UX:**
- Review Queue page as the default landing page after login (or prominent in sidebar)
- Onboarding shows per-source readiness state before plan selection
- Source health timeline accessible from each source card
- A&A assessment shows reviewer name and review date prominently

**Required trust signals:**
- Security/data-handling page (minimal)
- Email delivery confirmation visible in dashboard (delivery log)
- Delivery failure notification to admin if brief send fails
- "Evidence retained for [X] months" visible in Settings

**Required delivery workflow:**
- Weekly brief delivered via email to client's work email (production, not test-mode)
- Telegram delivery production-tested
- Delivery status (sent/failed) visible in Integrations page

**Required evidence/audit workflow:**
- PDF audit pack export
- Review history count badge on Evidence page header
- Per-source monitoring confirmation records downloadable

**Required support/ops:**
- < 4h response time for production email/Telegram delivery failures
- Source health operational alerting for founder (QUALITY_DROP alerts to admin)
- At least 2 completed source readiness reviews with prospects

**Required legal/security:**
- Security/data-handling page live
- Evidence retention period confirmed and visible per plan

**Exact tasks:**
1. Review Queue page (5–8 days)
2. Production SMTP email delivery (3–5 days)
3. PDF audit pack export (3–5 days)
4. Plan.py fix: source_limit 62, retention_days 365 for professional (0.5 days)
5. Rename AIBriefPage to MonitoringBriefPage, remove AI framing (1 day)
6. DFSA main rulebook re-test and re-activation (2–3 days)
7. VARA: expand to 5 sources including at least 1 rulebook endpoint (5–10 days)
8. Reviewer name on A&A card (1 day)
9. Source health sparkline (3 days)
10. Security page (1 day)
11. Per-source no-change confirmation (3 days)

**Total effort: ~30–45 days**

---

### Level 3: Professional Compliance Workflow — Goal: Customer Pays $749+ and Feels Justified

**Readiness today: 20%**

**Required product features (beyond Level 2):**
- [ ] DIFC laws out of remediation and active
- [ ] Multi-user support confirmed (2 users, role-based: admin / reviewer)
- [ ] 12-month evidence retention confirmed and enforced in plan.py
- [ ] Annual billing option (Stripe integration)
- [ ] Source addition request with SLA ("we assess within 5 business days")
- [ ] Evidence integrity verification ("re-verify hash" button on evidence record)
- [ ] Compliance digest mode (simplified view for non-technical users)
- [ ] Webhook delivery to external tools (Jira, Notion, Slack)
- [ ] Regulatory calendar integration (known CBUAE quarterly circular dates)
- [ ] White-label brief header option (custom company name in brief header)

**Required source coverage:**
- VARA: 8+ readiness-supported sources including rulebook PDFs
- DFSA: 12+ sources including all consultation papers and policy guidance
- DIFC: 4+ sources active
- Regulator concentration: CBUAE ≤35%

**Required UI/UX:**
- RBAC: admin (full access), reviewer (evidence and A&A only), read-only (sources and briefs)
- User invitation and management page
- Plan upgrade / downgrade self-service
- Billing history page (for invoice requests)

**Required trust signals:**
- At least 2 paying reference customers (anonymized acceptable)
- SOC 2 Type II in progress (can show readiness plan)
- Enterprise MSA template available

**Required delivery workflow:**
- Webhook delivery to external tools
- Scheduled brief delivery (weekly on day/time of customer's choice)
- Brief acknowledgement by recipient (read-receipt)

**Required evidence/audit workflow:**
- Hash integrity verification UI
- Exportable JSONL evidence archive (full evidence history as ZIP)
- 12-month retention enforced and verifiable

**Total effort: ~3–6 months of focused product work**

---

### Level 4: Enterprise-Ready — Goal: Larger Firms Take It Seriously

**Readiness today: 5%**

**Required:**
- SOC 2 Type II certification
- SSO (SAML 2.0)
- Multi-workspace (client isolation for consulting firms)
- API documentation (OpenAPI spec, versioned)
- Enterprise SLA (99.9% uptime, < 4h incident response)
- Enterprise MSA, DPA, NDA templates
- Data residency options (UAE/EU/US)
- Custom source onboarding with SLA
- Team roles: admin / compliance officer / reviewer / read-only
- Audit log of all platform actions (not just evidence assessments)
- Enterprise billing (annual, purchase order, Net-30)
- At least 5 reference customers
- UAE data residency option

**Total effort: 12–24 months of focused work. Not the current priority.**

---

## 15. Perfect Demo Script (10-Minute MLRO Demo)

**Setup before the demo:**
- Have a real CBUAE AML/CFT monitoring run with at least 2 runs (one UNCHANGED, one showing a baseline hash)
- Have a real A&A assessment completed with impact level "policy_review" and an internal note
- Have the audit pack Markdown export ready
- Run the demo from the live product (no demo environment — live product only)
- Make sure AlertsPage shows live data or an honest empty state (not MOCK_ALERTS)
- Have the Sources page open showing CBUAE sources with green status badges

---

**Minute 0–1: Setup the frame**

"Before I show you the product, let me be clear about what StatuteProof is and is not. We monitor public official UAE regulatory sources, detect content changes, store cryptographic evidence records, and produce human-reviewed monitoring briefs. We are not a legal advice service. We do not interpret regulatory changes. We do not guarantee that all updates are captured. What we do is give your MLRO a systematic, evidence-backed monitoring record that you can show an auditor."

---

**Minute 1–2: Source coverage — be honest immediately**

"We have 62 readiness-supported UAE official regulatory sources. Here is what that actually means."

[Open Sources page — live API data]

"You can see each source, its extraction quality, its last monitoring run, and its health status. These four here — DFSA rulebook, DFSA notices, DIFC laws, UAE FIU homepage — are under extraction remediation. We do not pretend they work. They do not. We are working on them."

"Our strongest coverage is CBUAE — 27 sources across payments, AML/CFT, open finance, and consumer protection. DFSA is 8 sources. ADGM/FSRA is 10 sources. VARA is 3 sources — I'll be honest about that in a moment."

---

**Minute 2–4: One real source timeline**

[Navigate to the CBUAE AML/CFT regulations source — show the source card]

"This source has been monitored continuously. Last checked: [timestamp]. Extraction quality: GOOD. Here is the monitoring hash for the last run: [hash[:16]...]. The run before that had the same hash, confirming no content change."

"This is your audit trail for stable periods. You can tell an auditor: 'We checked CBUAE AML/CFT regulations on [date]. Content fingerprint confirmed unchanged. Here is the record.'"

---

**Minute 4–6: One evidence record and A&A flow**

[Navigate to an evidence record where something changed — ideally FIRST_SEEN or CHANGED]

"This is a real evidence record. Source: [name]. Status: CHANGED. Detected: [date]. Here is the change — a new document section was added."

[Show the diff panel]

"And here is where human review comes in. An MLRO reviews this and clicks 'Acknowledge & Assess.'"

[Show A&A section with completed assessment]

"This assessment says: Impact level — Policy Review Required. Internal note: 'Reviewed with compliance team, no immediate policy update required but flagging for Q3 review.' Next action: 'Monitor for related circulars.' Reviewed by: [name]. Reviewed at: [timestamp]."

"This record is locked. The assessment cannot be changed after it is filed. The MLRO has a defensible paper trail."

---

**Minute 6–7: Audit export**

[Click Export — show Markdown audit pack]

"Here is the audit pack. It includes the source, the URL, the hash, the diff, the assessment, and this disclaimer: 'Monitoring intelligence only. Not legal advice.'"

"An MLRO can put this in their inspection file. We are working on PDF export — it is not available yet, and I will not pretend it is."

---

**Minute 7–8: Remediation honest moment**

[Navigate to DIFC laws source — shows "Needs remediation"]

"DIFC laws are under extraction remediation. Our adapter cannot reliably extract content from the DIFC laws portal — it uses a JavaScript-heavy framework that blocks our current extraction method. We are working on it. We do not charge you for monitoring a source we cannot extract. We show you the limitation clearly and explain what we are doing about it."

"This is what I mean when I say we are transparent about source health. We would rather tell you a source is broken than pretend it works."

---

**Minute 8–9: Time savings and value**

"An MLRO manually checking CBUAE, VARA, DFSA, and ADGM sources — roughly 5–8 sources per week, at 30–45 minutes per check — spends 4–6 hours per week on source monitoring. At an internal compliance rate of $80–$100/hour, that is $1,600–$2,400 per month in monitoring labor. StatuteProof at $199–$399/month replaces that systematically with evidence records you can actually use in an inspection. The time savings alone justifies the cost. The audit trail is the additional value."

---

**Minute 9–10: Close and next step**

"What I would suggest as a next step: a source readiness review. We map your specific UAE regulatory obligations to our source pack, show you which sources are active, which are limited, and which are in remediation. You get a clear picture of what you are actually monitoring before you commit any budget. This takes less than a week and costs nothing."

"Questions?"

---

**What not to show in the demo:**
- AlertsPage if MOCK_ALERTS is still present — explain "the alerts view is being updated to show live data" and skip it
- AIBriefPage if it shows mock content without a prominent banner
- Any hardcoded dashboard stats until they are API-driven
- Telegram pairing if it has not been tested in this environment

**What to say if asked about VARA/DIFC gaps:**

"VARA: we have 3 readiness-supported VARA sources today — enforcement notices, main page, and one listing. VARA's primary regulatory documents are PDFs, and reliable PDF extraction at the level of quality we require is in progress. If VARA rulebook monitoring is your primary requirement, I would rather tell you now that we are not there yet. We are working on it and I can give you an honest timeline when you choose to begin a pilot."

"DIFC: DIFC laws are under extraction remediation. The DIFC laws portal uses a JavaScript framework that our current adapters cannot reliably parse. We are testing a Playwright-based adapter that may resolve this. We do not offer DIFC source monitoring today and will not claim to until it is production-grade."

**What to say if asked about enterprise competitors:**

"If you need global regulatory coverage, analyst-grade summaries, and obligation management, CUBE or Wolters Kluwer are the right tools. They are excellent at what they do and they cost accordingly. We are not competing with them. We are UAE-specific official-source monitoring with an evidence trail, at a price that makes sense for a 5-person compliance team."

**What to say if asked "can you guarantee we won't miss changes?":**

"No. We can guarantee that we run monitoring checks on our registered sources at the stated cadence, store cryptographic evidence of each run, and alert you on detected changes. We cannot guarantee that all regulatory publications from all UAE bodies are captured. Some sources are not accessible to automated monitoring. Some sources publish via channels we do not monitor. We are transparent about what we cover and what we do not. The monitoring is a systematic layer on top of — not a replacement for — your own regulatory horizon scanning."

**What to say if asked "why shouldn't we just use a lawyer?":**

"You should use a lawyer. StatuteProof does not replace legal counsel. What StatuteProof does is give your MLRO — or your lawyer — a systematic monitoring baseline with evidence records. Without StatuteProof, the question 'did you monitor CBUAE on June 3?' is answered by 'we think so, our notes say we checked.' With StatuteProof, the answer is 'yes, here is the hash, here is the timestamp, here is the A&A record.' That difference matters in an inspection."

---

## 16. Next 10 Product Tasks (In Exact Priority Order)

1. **Remove MOCK_ALERTS from AlertsPage.jsx** — replace with live `/api/alerts` or honest empty state. (P0, 1 day)
2. **API-drive DashboardHome source counts** — `GET /api/sources/summary` returns enabled/supported/remediation from live sources.json. (P0, 1 day)
3. **Remove MOCK_REPORTS from ReportsPage.jsx** — replace with honest empty state. (P0, 1 day)
4. **Remove silent mock fallback from AIBriefPage.jsx** — honest empty state on API failure. Rename to MonitoringBriefPage. (P1, 1 day)
5. **Fix plan.py Professional plan capabilities** — source_limit: 62, retention_days: 365 for the plan that charges $399+ (P1, 0.5 days)
6. **Add source readiness preview to OnboardingPage step 2** — per-source layer status inline. (P1, 2 days)
7. **Build Global Review Queue page** — evidence records table with status, risk, A&A filters. (P0, 5–8 days)
8. **Wire production SMTP email delivery** — SendGrid or Postmark, rate-limited, delivery status logged. (P0, 3–5 days)
9. **Add PDF export to audit_export.py** — wkhtmltopdf or Playwright print-to-PDF. (P1, 3–5 days)
10. **Add reviewer name to A&A assessment card UI** — fetched from user record, displayed prominently. (P1, 1 day)

---

## 17. Next 10 Sales Tasks (In Exact Priority Order)

1. **Complete one real source readiness review with a prospect** — any UAE MLRO or compliance manager. Deliver within 48h. Document the output format. (This week)
2. **Run one MLRO demo using the corrected demo script** — real CBUAE evidence record, real diff, real A&A assessment. Ask at the end: "What review field is still missing from your compliance file?" (This week)
3. **Identify 5 prospects in the UAE fintech/payments compliance space** — CBUAE-heavy, 5–50 person company, 1-person compliance team. Use LinkedIn, CBUAE public licensee list, VARA licensee registry. (This week)
4. **Fix the AlertsPage mock data issue before showing the product to anyone** — the demo is not ready until AlertsPage is clean. (Before any demo)
5. **Write a one-page "What StatuteProof Is and Is Not" summary** — 2 paragraphs, no forbidden claims, for the CFO or board member who will approve the spend. (1 day)
6. **Document the source readiness review process** — what the prospect receives, what format, how quickly. This is the primary lead-gen offer. (1 day)
7. **Contact 2–3 UAE compliance consultants about a pilot collaboration** — offer a single-workspace $199 pilot, acknowledge multi-workspace is not built. (This week)
8. **Create a comparison one-pager: StatuteProof vs. manual monitoring** — time saved, cost comparison, evidence trail as the differentiator. (1 day)
9. **Record a 3-minute screen recording demo using the corrected demo script** — not a polished production video, just a real walkthrough. Post to LinkedIn. (After AlertsPage fix)
10. **Ask the first prospect: "What would make you put this in front of your board?"** — use the answer to prioritize features. (First call)

---

## 18. What I Would Do This Week

**Monday:**
- Remove MOCK_ALERTS from AlertsPage.jsx (2 hours)
- API-drive DashboardHome source counts (2 hours)
- Remove MOCK_REPORTS from ReportsPage.jsx (1 hour)

**Tuesday:**
- Fix plan.py Professional plan capabilities (source_limit: 62, retention_days: 365) (0.5 day)
- Add source readiness preview to OnboardingPage step 2 (1 day)

**Wednesday:**
- Rename AIBriefPage to MonitoringBriefPage, remove silent mock fallback (1 day)
- Start building the Global Review Queue page — data model and API route first (1 day)

**Thursday:**
- Continue Review Queue page — frontend table component (1 day)

**Friday:**
- Run the first MLRO demo using the corrected demo script on a real prospect
- If no prospect is identified yet, record the 3-minute screen recording

**Do not do this week:**
- Stripe integration (not yet needed)
- PDF export (important but not P0 — review queue comes first)
- Multi-workspace (far future)
- Anything to do with the enterprise buyer
- VARA PDF adapter (important but not P0 this week)
- Any new sources activation (source count is not the bottleneck — workflow is)

---

## 19. What I Would Not Do

- **Do not raise prices to $349/$749 before the product matches it.** Specifically: plan.py currently encodes $199/$399 with source_limit: 13 and retention_days: 180. These do not match the aspirational prices. Fix the product first, then raise prices.
- **Do not pitch VASPs as the primary buyer** until VARA coverage reaches at least 6–8 readiness-supported sources including at least one rulebook endpoint. The gap between "3 VARA navigation pages" and "VARA compliance monitoring" is too wide to bridge with words.
- **Do not demo AlertsPage until MOCK_ALERTS is removed.** One "Reviewed sample" text in the status column is worse than not having an Alerts page at all.
- **Do not build more sources before fixing the workflow.** 62 readiness-supported sources is sufficient. The bottleneck is not sources — it is the review queue, email delivery, and PDF export.
- **Do not add Stripe yet.** Stripe complexity introduces bugs and edge cases. Manual activation at $199 for 2–3 pilots is faster to learn from than a self-serve checkout that sends the wrong plan capabilities.
- **Do not target enterprise buyers.** No SOC 2. No RBAC. No SLA. No reference customers. Enterprise sales will drain time and produce nothing.
- **Do not build multi-workspace.** The consulting firm buyer is valuable but structurally unserved. Building multi-workspace before product-market fit with single-workspace customers is premature.
- **Do not claim VARA monitoring is strong** in any external communication until VARA coverage is materially expanded. Current 3 sources at 4.8% of the pack is not "VARA monitoring."
- **Do not let any demo run while AlertsPage shows mock data.** This is the single most important trust rule for the next 30 days.

---

## 20. Final Founder Advice

"If I were advising Omar, I would say:

You have done the hardest thing — you built something real. 62 readiness-supported UAE regulatory sources with cryptographic evidence records and a human-reviewed brief system is not a demo. It is a product. The frustrating news is that you are 3–4 targeted weeks of work away from having something that a paying MLRO would call genuinely useful, but you are not there yet.

Here is exactly what is standing between you and your first $399 monthly payment:

The MLRO opens the Alerts page and sees 'Reviewed sample' in the status column. The sale is over. Fix this today.

The MLRO asks what they actually get for $399. Your plan.py says 13 sources and 180-day retention. Your pricing page says $399. Your pricing strategy doc says $749. These three things say three different things. Fix this before any call.

The MLRO wants a single place to see all unreviewed items, filter by risk, acknowledge them, and mark them done. This page does not exist. Build it next.

The MLRO expects a brief in their inbox. Email is test-mode only. No one is receiving a brief. Wire SMTP or you are selling a dashboard-only tool.

The MLRO wants to download the A&A record as a PDF for their compliance file. PDF does not exist. Add it.

Fix these five things and you have a $399/month product. Skip them and you have a $199/month controlled pilot with a very patient customer.

The product's strongest asset is not its source count. It is the evidence chain — hash, timestamp, diff, A&A record, disclaimer, locked and downloadable. No generic change detector does this. No cheap tool does this. This is what is worth $399/month. Make sure the customer can see it end-to-end without touching any mock data. Once they can, the product sells itself.

Do not add more sources. Do not build multi-workspace. Do not integrate Stripe. Fix the five things above, run one real MLRO demo, ask what is still missing from their compliance file, and let that answer drive the next sprint. Revenue before roadmap."

---

*Monitoring intelligence only. Not legal advice. Not a compliance certification. Not a guarantee of complete regulatory coverage.*
