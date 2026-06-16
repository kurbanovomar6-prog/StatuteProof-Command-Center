# What Clients Need for StatuteProof to Feel Ideal, Trustworthy, and Worth Paying For

> Date: 2026-06-16
> Basis: Full read-only inspection of product code, frontend, docs, pricing, competitor research, and source registry.
> Current truth: 66 enabled UAE sources / 62 readiness-supported / 4 remediation.
> Source usefulness score: 7.2/10. Product risk: 7/10 — material but manageable.
> This document is for internal strategic use only.
> Monitoring intelligence only. Not legal advice.

---

## Executive Verdict

StatuteProof has a real, defensible technical foundation: cryptographic evidence records, deterministic diff tracking, a gated human-review workflow, and genuine official-source coverage across 62 UAE regulatory endpoints. That is more than most early-stage compliance tools can honestly claim.

What it does not yet have is the product experience that makes a real compliance professional feel safe enough to depend on it, pay for it, and tell a colleague. The gap is not in the monitoring infrastructure — it is in proof of reliability, workflow completeness, delivery confidence, and honest scope communication.

**Overall product score: 6.9/10**

| Area | Score | Honest Reason |
|---|---:|---|
| Source usefulness | 7.2/10 | Best 30 sources are genuinely useful; long-tail sources are narrower |
| Workflow completeness | 4.8/10 | Monitoring exists; Acknowledge & Assess is spec-only |
| Trust presentation | 6.7/10 | Proof and hashes are strong; mock data in dashboard hurts |
| Pricing fairness | 6.5/10 | $199 pilot is fair; $399–749 needs more workflow before charging |
| Delivery reliability | 5.5/10 | Email not fully wired; Telegram not production-tested |

---

## Part 1: Buyer-by-Buyer Analysis (9 Buyer Types)

---

### Buyer 1: UAE VASP MLRO (Money Laundering Reporting Officer)

**Profile**: Employed at a VARA-licensed crypto or digital assets firm. Responsible for AML/CFT, regulatory reporting, and policy alignment with VARA, CBUAE, and UAE FIU. Team: 1–3 people. Budget authority: $500–$2,000/month, sometimes requires CFO sign-off above that.

**What they need from a regulatory monitoring tool**:
- Reliable detection of changes to VARA rulebook, VARA enforcement notices, CBUAE AML/CFT, UAE FIU typology reports, and EOCN sanctions guidance
- A defensible audit trail they can show an auditor: "We monitored this source on this date, the content was unchanged, here is the hash"
- A human-reviewed brief suitable for the compliance file — not raw machine output
- Alert delivery that reaches them reliably (email or Telegram), not just a dashboard
- Clear limitation disclosure: what sources are active, what is under remediation, what is outside scope

**Where StatuteProof stands today**:
- VARA coverage: 3 readiness-supported sources (4.8% of pack) — too thin for a VASP sales motion
- CBUAE AML/CFT: strong, 27 readiness-supported sources
- UAE FIU/EOCN: 7 readiness-supported sources — adequate
- Evidence trail: cryptographically sound
- Human-reviewed brief: code is complete but email delivery not fully wired
- Audit trail format: markdown/HTML available, no PDF export
- Dashboard: parts still show mock data — trust-damaging for a first meeting

**Gap severity**: HIGH. VARA coverage is the core product claim for this archetype and is currently the weakest segment. 3 VARA sources at 4.8% of the pack does not support "VASP compliance monitoring" as a headline.

**What must change before they pay**: VARA rulebook PDF extraction, at least 5 reliable VARA endpoints with stable hashes, end-to-end email delivery, zero mock data in the authenticated dashboard, PDF brief export.

---

### Buyer 2: DFSA-Regulated Firm CCO (Chief Compliance Officer)

**Profile**: Employed at a DIFC-licensed financial firm (fund manager, broker, payment institution). Responsible for DFSA compliance, MLRO reporting, and regulatory horizon scanning. Team: 2–5. Budget: $2,000–$10,000/month compliance spend.

**What they need**:
- Reliable DFSA rulebook, consultation paper, and enforcement notice monitoring
- DIFC laws and regulations tracking
- A brief that distinguishes "structural rulebook change" from "enforcement notice against a third party" — very different urgency
- Multi-user access: CCO + compliance associate, both reviewing alerts
- Evidence retention for at least 12 months (DFSA inspection windows)
- An acknowledgement workflow: "I reviewed this alert and took no action / actioned as follows" — not just viewing

**Where StatuteProof stands today**:
- DFSA coverage: 8 readiness-supported sources — adequate but not deep
- DIFC laws: under extraction remediation — a blocker for this buyer
- Evidence retention: 12-month retention in Professional spec, not confirmed as productized
- Multi-user: 2 users in Professional spec, multi-tenant auth not fully productized
- Acknowledgement workflow: specified, not implemented
- Alert differentiation: HIGH/MEDIUM/LOW risk scoring exists, but enforcement-vs-rulebook distinction not explicit in briefs

**Gap severity**: MEDIUM-HIGH. DFSA coverage is passable; DIFC remediation and missing acknowledgement workflow are blockers. Do not sell the "full DFSA compliance pack" while DIFC is in remediation.

**What must change**: DIFC out of remediation (or explicitly disclosed with expected timeline), acknowledgement/review record in the dashboard, PDF brief export.

---

### Buyer 3: ADGM/FSRA-Regulated Firm Compliance Manager

**Profile**: Employed at an Abu Dhabi Global Market-regulated firm (asset manager, fintech, fund administrator). Responsible for FSRA compliance and ADGM Authority regulations. Team: 1–3. Budget: similar to DFSA buyer.

**What they need**:
- ADGM FSRA rulebook changes, consultation papers, guidance notes, and enforcement notices
- ADGM Authority circulars (relevant for corporate structures)
- Coverage extending to CBUAE and UAE FIU (cross-jurisdictional in practice)
- Output their legal counsel can review alongside them

**Where StatuteProof stands today**:
- ADGM/FSRA: 10 readiness-supported sources — strongest non-CBUAE segment
- ADGM RA circulars: activated and readiness-supported
- Brief format: clean markdown + HTML with legal disclaimer
- Legal counsel sharing: no shared workspace or external view-only link — requires sending a file

**Gap severity**: MEDIUM. ADGM coverage is the best relative to source universe. The primary blocker is output format: markdown files are awkward to include in a compliance folder or forward to external counsel. PDF export solves this.

**What must change**: PDF brief export, or at minimum a clean HTML-to-PDF. A shareable brief link (read-only, no login required) would also help.

---

### Buyer 4: UAE Payments / E-Money Firm MLRO

**Profile**: Employed at a CBUAE-licensed payment service provider or electronic money institution. Heavy exposure to CBUAE Payment Systems Regulations, Consumer Protection Standards, Open Finance. Team: 1–4. Budget: $1,000–$5,000/month compliance.

**What they need**:
- Deep CBUAE coverage: regulations, circulars, consultation papers, consumer protection, open finance
- Immediate alert on CBUAE AML/CFT guidance changes — these trigger mandatory policy updates
- Brief distinguishing "new regulation" from "updated existing regulation" vs. "consultation paper"
- Evidence they can show during a CBUAE inspection: "We tracked this source, detected no change, hash matches"

**Where StatuteProof stands today**:
- CBUAE coverage: 27 readiness-supported sources — strongest segment (43.5% of pack)
- Change type classification: LICENSING, AML_CFT labels exist in alert schema but not surfaced prominently in briefs
- Inspection-ready evidence: hash + timestamp + URL exist, no formatted monitoring certificate

**Gap severity**: LOW-MEDIUM. This is StatuteProof's best-served archetype. The gap is in presentation (proof-of-monitoring record format) and delivery (email brief).

**What must change**: End-to-end email delivery, a simple "no-change monitoring record" format for inspection files, clearer change type labeling in briefs.

---

### Buyer 5: UAE Tax / Federal Compliance Officer (FTA/MoF)

**Profile**: Employed at or serving a UAE entity subject to corporate tax, VAT, or FATCA/CRS. Responsible for tracking FTA regulations, MoF consultations, and EOCN guidance.

**What they need**: FTA regulatory change monitoring, MoF consultation tracking, EOCN AML/CFT guidance, SCA (if publicly listed).

**Where StatuteProof stands today**: Federal/FTA/legislation: 3 readiness-supported sources — thin. SCA: 4 readiness-supported — adequate for AML/governance. MoF: enabled but limited relative to actual MoF regulatory output volume.

**Gap severity**: HIGH relative to this buyer's needs. This archetype is not the primary sales motion. Do not target this buyer until FTA and MoF coverage is meaningfully deeper.

---

### Buyer 6: UAE Compliance Consulting Firm

**Profile**: Small advisory firm (3–15 consultants) serving multiple UAE-regulated clients across VARA, DFSA, ADGM, and CBUAE. Wants to offer monitoring as a managed service add-on and charge it through to clients.

**What they need**:
- Multiple client workspaces — hard requirement
- White-label or client-branded brief output
- Bulk brief generation and delivery
- Clear data isolation between clients
- Pricing that allows a margin when they re-sell monitoring as a service

**Where StatuteProof stands today**: Multi-workspace not implemented. White-label not implemented. Single workspace per user. "Consultant — Talk to us" plan is explicitly roadmap-only in all internal docs.

**Gap severity**: CRITICAL. Do not pitch this buyer. Do not put them in the founding pilot cohort unless explicitly limited to one workspace with full disclosure that multi-workspace is unbuilt.

---

### Buyer 7: Law Firm with UAE Compliance Practice

**Profile**: Small-to-mid law firm with a regulatory practice advising UAE-regulated clients. Wants regulatory intelligence as background for advice. Not a compliance operations tool — they need monitoring to stay current before advising clients proactively.

**What they need**:
- Monitoring briefs as background regulatory intelligence
- Ability to share output with clients
- Strong evidence that StatuteProof does not provide legal advice (they are the legal adviser)
- Ideally multi-jurisdiction (not UAE-only)

**Where StatuteProof stands today**: UAE-only. Output sharing is awkward (markdown/HTML, no PDF). Legal advice boundary is correctly disclaimed but the disclaimer needs to be prominent in any client-shared output. Non-UAE coverage: zero.

**Gap severity**: HIGH. Geographic limitation is a structural constraint for law firms serving multi-jurisdiction clients. Only viable for firms whose entire client base is UAE-only. Do not actively target.

---

### Buyer 8: Internal RegTech Team at a UAE Bank

**Profile**: Internal team at a UAE bank (Emirates NBD, FAB, Mashreq, ADCB) responsible for regulatory change management. Enterprise procurement process. Requires SOC 2 or equivalent, SSO, API access, enterprise SLAs.

**What they need**:
- Enterprise security posture (SOC 2, UAE data residency)
- API/webhook integration with GRC systems (ServiceNow, Jira)
- SLA guarantees
- Legal agreements beyond standard terms (DPA, MSA, NDA)
- Reference customers from similar institutions
- Multi-user RBAC

**Where StatuteProof stands today**: SOC 2 not mentioned anywhere. No public API documentation. No enterprise SLA document. No reference customers. No RBAC. This buyer is not addressable.

**Gap severity**: CRITICAL. Do not spend sales effort here. Use enterprise inquiries for market research only.

---

### Buyer 9: Solo or Fractional Compliance Consultant

**Profile**: Individual consultant or MLRO-for-hire serving 1–3 small UAE firms as a fractional resource. Budget: $200–$500/month. Very price-sensitive. Wants a tool that makes their work faster and more defensible.

**What they need**:
- Simple, reliable monitoring of 5–8 critical UAE sources
- A professional brief they can hand to their client
- Evidence they can use in their own compliance file
- Under $400/month
- No IT procurement or enterprise setup

**Where StatuteProof stands today**:
- Pricing: $349 Monitor plan is accessible
- Source coverage: 5 sources at Monitor tier covers the core stack for a payments/AML profile
- Brief quality: good, disclaimer-complete, ready for sharing
- Onboarding: 3-step form exists but activation is still manual
- Dashboard: mock data visible in parts — this buyer will notice immediately

**Gap severity**: MEDIUM-LOW. This is the most accessible founding customer today. Remove mock data from the dashboard, wire email delivery, and offer fast activation (< 24h) — and this buyer can pay $349/month starting next week.

---

## Part 2: Product Gap Ranking (14 Categories)

Ranked by severity of impact on customer trust and payment readiness.

---

### Gap 1: VARA Source Coverage Depth — CRITICAL

**Current state**: 3 readiness-supported VARA sources (4.8% of pack). VARA enforcement notices and VARA main listing page. No VARA rulebook PDF extraction, no VARA administrative order archive, no VARA licensing register.

**Customer impact**: VASP MLROs (the most natural buyer) cannot trust a "UAE compliance monitor" that has thin coverage of their primary regulator. When asked "can you monitor VARA rulebook changes?" and the answer is "we have 3 VARA sources and the rulebook is in PDFs," the sale is at risk.

**What is needed**: VARA rulebook PDF endpoint (if accessible without login), VARA licensing register changes, VARA consultation papers. Minimum: stable hash on VARA rulebook with reliable detection of new content appended. Current VARA extraction covers navigation/listing pages, not the actual regulatory text.

**Effort**: High. VARA's website is JS-heavy and most documents are PDFs. Requires PDF adapter work and possibly a Playwright-based deep extraction pass with DevTools-discovered selectors.

---

### Gap 2: Mock Data Visible to Real Users — CRITICAL

**Current state**: Parts of the dashboard show sample/demo data in the frontend. Some app pages use mock flows or fallback to sample mode.

**Customer impact**: The single most trust-damaging thing a compliance professional sees is "SAMPLE" data in their workspace. For a tool claiming cryptographic evidence records, showing mock hashes is paradoxical. Any demo misunderstanding can destroy a relationship.

**What is needed**: Every authenticated user's dashboard must show either real data from their activated sources or an honest empty state ("No monitoring runs yet — your sources will appear here after your first cycle"). SAMPLE/FAKE labels belong in documentation and demo fixtures only — never in the live authenticated dashboard.

**Effort**: Medium. Audit every dashboard component for mock data injection and replace with real data or clear empty states.

---

### Gap 3: Email Brief Delivery Not Wired End-to-End — HIGH

**Current state**: Alert routing code exists (`alert_routing.py`). Email delivery logic exists. The pipeline from "approved alert → brief rendered → email sent to client" is not fully connected or production-tested.

**Customer impact**: An MLRO pays for a monitoring service. They expect a brief in their inbox at a predictable cadence without logging into a dashboard. If delivery requires them to check the dashboard, they will not check consistently, will miss updates, and will conclude the tool does not work. Email is the primary trust signal for recurring compliance tools.

**What is needed**: End-to-end tested email delivery: approved alert → brief rendered → sent to client's work email → delivery confirmation logged. Subject lines should be explicit ("StatuteProof Weekly Brief — UAE — Week ending 2026-06-14"). Full legal disclaimer must appear in the email body, not only linked.

**Effort**: Medium. The underlying code is close. The gap is integration, testing, and hardening the delivery guarantee.

---

### Gap 4: No Acknowledgement / Review Workflow — HIGH

**Current state**: "Acknowledge & Assess" is documented as a specification but not implemented. The alert review workflow exists in the backend (`alert_review.py`) but the MLRO-facing acknowledgement UI does not exist in the dashboard.

**Customer impact**: A compliance professional's workflow is: receive alert → review it → record what they did about it → file the record. StatuteProof handles steps 1–2 but not steps 3–4. Without step 3, the tool is a notification system. This is what separates a $199 tool from a $749 tool.

**What is needed**: In the dashboard Alerts view, each reviewed alert needs an "Acknowledge" button opening a brief modal: "I have reviewed this change. My assessment: No action required / Policy review initiated / Escalated to legal counsel / Other." The response is timestamped, stored, and visible in the evidence record. This creates the paper trail the MLRO needs for an inspection.

**Effort**: Medium. Backend `alert_review.py` already has the status model. This is primarily a frontend + API endpoint task.

---

### Gap 5: No PDF Export of Briefs — HIGH

**Current state**: Briefs render as markdown and HTML. No PDF export. Pricing docs mark "PDF/Markdown export — Requires activation."

**Customer impact**: An MLRO's compliance file is a PDF file, a printed document, or an email attachment they can forward. Markdown is not a format that ends up in a compliance file. If they cannot save the brief as a PDF, they will not use it for documentation. This is a basic professional output requirement, not a premium feature.

**What is needed**: HTML-to-PDF generation. The HTML rendering is already complete in `render_weekly_brief_html`. This is a one-module addition using wkhtmltopdf, Playwright print-to-PDF, or a cloud service. Output must include the disclaimer on every page footer and the SAMPLE/DEMO label on demo outputs only.

**Effort**: Low-medium. The hardest part (HTML rendering) is already done.

---

### Gap 6: Source Coverage Concentration Risk — HIGH

**Current state**: CBUAE = 43.5% of readiness-supported sources (27 of 62). VARA = 4.8% (3 of 62). DIFC in remediation.

**Customer impact**: This concentration makes StatuteProof excellent for CBUAE-heavy compliance profiles but thin for VASP, DFSA, and DIFC profiles. The positioning "UAE regulatory monitoring" implies balanced coverage. The actual coverage is CBUAE-first, UAE-federal-second, everything else materially thinner.

**What is needed**: Either (a) broaden VARA, DFSA, and DIFC coverage so no single regulator exceeds 35% of the pack, or (b) be completely honest in the sales pitch: "This pack is strongest for CBUAE and AML/payments compliance. VARA and DIFC coverage is being extended." Both are needed — the honesty immediately, the diversification as a product roadmap item.

**Effort**: High for (a). Low for (b). Start with (b) today.

---

### Gap 7: No Self-Serve Activation — MEDIUM-HIGH

**Current state**: Pricing is public. Activation is manual. A prospect who wants to start monitoring must wait for the founder to manually activate after a source readiness review call. No Stripe checkout exists.

**Customer impact**: Any compliance professional who lands on the pricing page and cannot immediately start a trial will leave. The gap between "I want this" and "I can start" is the largest drop-off in any SaaS funnel. Manual activation is appropriate during a very early pilot stage with 2–3 customers. It is not viable beyond that.

**What is needed**: Either a self-serve trial (7-day limited access with real data on a small source pack) or at minimum a fast-response lead capture that sends an activation link within 24 hours. Stripe integration should follow after the first manual pilots are validated.

**Effort**: Medium. Self-serve trial requires scope-limiting the product (3 sources, no email delivery) and wiring user creation to source activation.

---

### Gap 8: DIFC Source Pack Still in Remediation — MEDIUM-HIGH

**Current state**: DIFC laws and regulations are under extraction remediation. DIFC website is JS-heavy and selector-broken.

**Customer impact**: DFSA-regulated firms operating in DIFC need DIFC law tracking alongside DFSA rulebook monitoring. A "DFSA compliance monitor" that cannot track DIFC laws is incomplete for any DIFC-established firm.

**What is needed**: Either a working DIFC adapter (Playwright + DevTools-discovered CSS selectors) or a very clear disclosure on the Sources page: "DIFC laws and regulations: extraction under remediation — monitoring paused. Expected resolution: [timeline]."

**Effort**: High for adapter fix. Low for honest disclosure. Start with disclosure.

---

### Gap 9: No Proof-of-Monitoring Certificate — MEDIUM

**Current state**: Evidence records contain hash, timestamp, source URL, and proof block. But there is no formatted monitoring confirmation that an auditor can read without technical context.

**Customer impact**: An MLRO going into a CBUAE or VARA inspection needs to show what monitoring was done and when. The raw evidence record JSON requires explanation. The weekly brief covers the period summary. But a per-source "no change detected" record — formatted for a human auditor — is a different artifact.

**What is needed**: A "Source Monitoring Record" downloadable per source per period. Plain-language format: "StatuteProof monitored [source name] at [URL] on [date] at [time UTC]. Content fingerprint: [hash[:16]...]. Extraction quality: [GOOD/LIMITED]. No content change detected since prior check on [date]. This record is provided for compliance file documentation. It is not a legal opinion."

**Effort**: Low-medium. The data exists. This is a rendering and export task.

---

### Gap 10: No Security Posture Page — MEDIUM

**Current state**: No SOC 2, no data residency statement, no security page, no access-controls disclosure.

**Customer impact**: Any compliance professional evaluating a tool to handle regulatory intelligence data will ask: where is my data stored, who can access it, what happens in a breach. Without answers, procurement approval is blocked at many organizations regardless of how good the monitoring coverage is.

**What is needed**: A security page (even minimal): "Data is processed in [region]. We use AES-256 at rest, TLS in transit. We do not share client data with third parties. Access is restricted to [description]. We are working toward SOC 2 compliance." Honest about current certification status.

**Effort**: Low for the page content. SOC 2 is a medium-term track.

---

### Gap 11: Alert Risk Classification Not Surfaced Clearly — MEDIUM

**Current state**: Risk scoring exists (HIGH/MEDIUM/LOW). Alert schema has `change_type`. But the rendered brief does not explicitly group alerts by urgency.

**Customer impact**: An MLRO reading a brief with 8 alerts wants to know immediately which require action and which are background awareness. Without explicit grouping, every item reads at the same urgency level — inefficient and anxiety-inducing.

**What is needed**: A brief section header grouping: "Items requiring review this period" (HIGH risk) vs. "Items for awareness" (MEDIUM) vs. "Confirmed no-change sources" (LOW/none). This changes how the brief is consumed.

**Effort**: Low. This is a brief rendering change in `weekly_brief.py`.

---

### Gap 12: Telegram Delivery Not Verified at Production Scale — MEDIUM

**Current state**: Telegram pairing UI exists. Integration layer exists. Production reliability at multiple simultaneous clients is unverified.

**Customer impact**: Silent delivery failure in a compliance monitoring tool is worse than a visible error. If a brief is not delivered and the client does not know, they may assume nothing changed — which is a false negative they will blame on the tool.

**What is needed**: Delivery confirmation logging (brief sent → delivery status logged → visible in dashboard), retry on failure, and admin notification on delivery failure.

**Effort**: Medium. Standard webhook/bot reliability patterns.

---

### Gap 13: Source Health Timeline Not Visible to Customers — MEDIUM

**Current state**: Source health data exists internally (monitoring runs, quality, remediation status). Customers cannot see the history of a source's reliability over time.

**Customer impact**: A compliance professional relying on StatuteProof for 6 months wants to know: was this source monitored consistently? Were there any gaps? Without a timeline, they cannot assess the completeness of their monitoring record.

**What is needed**: Per-source timeline showing: monitoring run dates, quality scores, any remediation periods, current status. This turns "62 readiness-supported sources" into a verifiable, auditable monitoring record.

**Effort**: Medium. Data exists in `source_runs.jsonl`. Gap is a frontend visualization component.

---

### Gap 14: Onboarding Does Not Show Source Readiness Before Plan Selection — LOW-MEDIUM

**Current state**: The Source Readiness Review tool exists. But the onboarding 3-step form (company → markets/sources → industries) does not connect selected sources to their current readiness status before plan selection.

**Customer impact**: A prospect selects "VARA, DFSA, UAE FIU" in step 2, picks Professional, then learns VARA is only 3 sources and DIFC is in remediation. Post-purchase disappointment.

**What is needed**: In step 2 of onboarding, when a source layer is selected, show readiness status inline: "VARA: 3 readiness-supported sources (rulebook PDF extraction in progress). DFSA: 8 readiness-supported sources. DIFC: under extraction remediation."

**Effort**: Low. Source registry data is available. This is a frontend state-connection task.

---

## Part 3: The Ideal Product — Three Levels

---

### Level 1: Minimum Viable Trustworthy Product (MVP-T)

The minimum standard at which StatuteProof can be sold with confidence to a real founding pilot customer without risking trust damage.

**Requirements:**
1. Zero mock data in any authenticated dashboard view
2. Email delivery of weekly brief end-to-end tested for at least 2 founding pilots
3. VARA coverage expanded to at least 5 readiness-supported sources including one rulebook endpoint
4. PDF export of weekly brief available (even simple wkhtmltopdf)
5. Source readiness status shown in onboarding before plan selection
6. All dashboard pages showing real data or honest empty states with clear "monitoring not yet started" copy
7. DIFC remediation status explicitly disclosed with expected resolution timeline
8. Source last-checked timestamp visible on every source card
9. Proof-of-monitoring summary downloadable per source: "Last checked: [date]. No change detected. Hash: [hash[:16]...]"

**Current status**: Not at MVP-T on items 1, 2, 3, 4, and 6.

**Time to MVP-T**: 3–6 weeks of focused product work if prioritized correctly.

---

### Level 2: Product Worth Paying For at $399–$749/month

The standard at which an MLRO at a real UAE-regulated firm can justify the spend to their CFO.

**Requirements (in addition to MVP-T):**
1. Acknowledgement/review workflow in the dashboard
2. Alert risk classification grouped in brief header (HIGH / MEDIUM / awareness)
3. Source health timeline per source (30-day and 90-day stability)
4. Multi-user support confirmed (CCO + associate, 2 users)
5. Evidence retention confirmed at 12 months for Professional plan
6. Self-serve trial with limited source pack (no credit card, real monitoring data)
7. Security/data-handling page (honest, even if pre-SOC 2)
8. Brief delivery confirmation visible in dashboard
9. Certificate of monitoring downloadable per source per period
10. Onboarding limitation acknowledgement flow (explicit scope, unsupported sources, no legal advice)

**Current status**: Items 1, 3, 4, 5, 6, 7, 8, 9, 10 are not built or not confirmed as productized.

**Time to Level 2**: 6–12 weeks of focused product work.

---

### Level 3: Market-Defining UAE Compliance Intelligence Tool

The standard at which StatuteProof is recognizably superior to manual monitoring and simple webpage-change tools, and begins to compete for the UAE market against Regology-class tools.

**Requirements (in addition to Level 2):**
1. VARA rulebook extraction reliable and deep (PDF parsing, all major VARA regulatory documents)
2. DFSA expanded to 15+ sources including consultation papers and policy guidance
3. DIFC laws out of remediation and production-grade
4. Multi-workspace support for consulting firm buyers
5. White-label brief output (firm-branded header)
6. Webhook delivery to GRC tools (Jira, Notion, Slack)
7. Annual billing option with transparent annual discount
8. Source addition request workflow with published SLA ("assess readiness within 5 business days")
9. Source health history comparison (how does VARA coverage today compare to 6 months ago?)
10. Regulatory calendar integration (known publication dates for CBUAE quarterly circulars, VARA annual reports)
11. No-change monitoring confirmation (per source, per period, in printable format)
12. At least 2 paying reference customers (anonymized references acceptable)

**Time to Level 3**: 6–18 months depending on team size and prioritization.

---

## Part 4: Must-Have Lists

### Before First Founding Pilot Customer Signs

- [ ] Zero mock data in authenticated dashboard
- [ ] Email delivery of reviewed brief working end-to-end
- [ ] VARA coverage at 5+ readiness-supported sources
- [ ] Onboarding shows source readiness before plan selection
- [ ] PDF brief export
- [ ] Source last-checked timestamp on every source card
- [ ] Honest "no monitoring yet" empty state on all dashboard pages
- [ ] Brief HTML renders without markdown leakage (no `**bold**` visible)
- [ ] Full disclaimer on every brief (confirmed already in code)
- [ ] SAMPLE/DEMO label on every demo fixture output (confirmed already in code)

### Before Charging $349/month (Monitor Plan)

Everything above plus:
- [ ] Self-serve or fast-activation flow (< 24h from signup to first monitoring run)
- [ ] Brief delivery confirmation shown in dashboard
- [ ] Clear source limitations disclosed per source (readiness-supported vs. remediation)
- [ ] Legal/Privacy/Terms pages complete and accessible from footer
- [ ] Support email address visible and staffed with < 24h response
- [ ] Cancellation policy stated clearly (monthly, cancel any time)

### Before Charging $749/month (Professional Plan)

Everything above plus:
- [ ] Acknowledgement/review workflow functional
- [ ] Multi-user access (2 seats) confirmed as working
- [ ] 12-month evidence retention confirmed and visible in account settings
- [ ] Source health timeline visible per source
- [ ] Certificate of monitoring downloadable per source per period
- [ ] Alert risk classification grouped in briefs (HIGH / MEDIUM / awareness)
- [ ] Honest disclosure that DIFC is in remediation and Professional does not include DIFC until remediated
- [ ] Professional plan renamed "Professional Pilot" until audit export is built

### Before Pitching to Any Enterprise Buyer

Everything above plus:
- [ ] Security/data-handling page with data residency and access controls disclosed
- [ ] Privacy Policy covering regulatory intelligence data handling
- [ ] Enterprise MSA template
- [ ] Audit export (JSONL evidence records exportable as ZIP)
- [ ] Role-based access (admin / reviewer / read-only)
- [ ] Uptime/SLA statement
- [ ] At least 2 reference customers (even anonymized case studies)

---

## Part 5: Competitor Comparison

Assessed from the perspective of a UAE compliance professional with a $500–$2,000/month budget.

---

### ChangeDetection.io and Visualping ($13–$400/month)

**What they offer**: Simple webpage change detection for any URL. Cheap. Works for static pages.

**What they lack**: Regulatory source specialization, cryptographic evidence trail, normalization, diff quality, human review gate, legal disclaimers, brief format, PDF export, extraction quality scoring.

**StatuteProof advantage**: Everything a compliance professional needs that these tools cannot provide.

**StatuteProof weakness**: At $349/month vs $89/month, a cost-conscious buyer will ask why they need the expensive version. The answer must be specific and rehearsed: hashing, MLRO-ready brief, official-source extraction quality gates, human review before delivery.

**Positioning**: "StatuteProof is not a generic page change detector. It is official-source regulatory monitoring with a cryptographic evidence trail, human review gate, and compliance-grade brief output."

---

### CUBE RegPlatform

**What they offer**: Enterprise-grade automated regulatory intelligence, global source coverage, obligation management, workflow, horizon scanning. Likely $5,000–$20,000+/month for institutional clients.

**StatuteProof advantage**: UAE-specific depth, transparent source readiness, evidence-first proof trail, accessible pricing, no enterprise procurement required.

**StatuteProof weakness**: Global coverage, analyst-grade intelligence, obligation mapping, enterprise workflow maturity — CUBE wins on all of these.

**Positioning**: Do not compare directly. "If you need global coverage at enterprise scale, CUBE is worth evaluating. If you need UAE-specific official-source monitoring with an auditable evidence trail at a fraction of the cost, StatuteProof."

---

### Corlytics

**What they offer**: Regulatory risk intelligence, enforcement analytics, policy/control mapping for financial institutions.

**StatuteProof advantage**: Narrower, cheaper, more accessible, evidence-first.

**Positioning**: Not in the same buyer category for StatuteProof's target customers. Do not compare directly.

---

### Regology

**What they offer**: Regulatory AI, change management, compliance library. Public pricing page, targeting mid-market.

**StatuteProof advantage**: UAE-specific, evidence-first, transparent source readiness, lower entry price.

**StatuteProof weakness**: Regology has more workflow maturity and broader coverage.

**Lesson from Regology**: Packaging clarity. Regology presents tiers by workflow completeness, not just source count. StatuteProof should do the same: sell a workflow promise, not a number.

---

### Vixio / FiscalNote

**What they offer**: Regulatory intelligence and horizon scanning for payments and crypto. Sector expertise and analyst research.

**StatuteProof advantage**: Evidence trail, UAE-specific source depth, lower price, no analyst markup.

**StatuteProof weakness**: Analyst intelligence, global coverage, news and analysis layer.

**Positioning**: "StatuteProof monitors the official sources. Vixio analyzes the implications. They are complements for firms with the budget for both."

---

### Wolters Kluwer OneSumX, Thomson Reuters RIMS, LexisNexis

Enterprise regulatory change management platforms sold to banks and global financial institutions. Out of StatuteProof's addressable market entirely. Mention only to reassure prospects that StatuteProof is not trying to compete there: "We are not an enterprise RCM platform. We are UAE-specific official-source monitoring with an evidence trail for teams that cannot justify enterprise contracts."

---

### ComplyAdvantage

**What they offer**: AML screening, transaction monitoring, sanctions/adverse media data.

**Why they are not a direct competitor**: ComplyAdvantage screens counterparties. StatuteProof monitors regulatory sources. Adjacent categories, not the same.

**Positioning**: "A compliance professional using ComplyAdvantage for AML screening still needs to monitor VARA and CBUAE for regulatory changes. StatuteProof fills that gap alongside their screening tool."

---

## Part 6: Pricing Honesty

---

### Source Readiness Review — Free

**Honest assessment**: Correct entry point. Sets honest expectations. Generates leads without commitment. The risk: if source readiness review delivery is slow or manual, leads will go cold. This must be delivered within 24–48 hours of request. A week later is a lost lead.

---

### Monitor — $349/month (5 sources)

**Honest assessment**: $349 for 5 sources with 90-day retention and diff view is fair if those 5 sources match what the buyer actually needs. If a VASP pays $349 and the 5 sources are CBUAE-heavy with weak VARA, they will feel underserved.

**Required for this price to be honest**: Clearly state which 5 sources are included before payment. Confirm those are the sources the buyer selected. Disclose any limitations on those specific sources.

**Upsell trigger**: "You've been monitoring 5 sources for 60 days. Upgrading to Professional adds 57 more readiness-supported sources and the high-risk review queue." That is a real upgrade reason.

---

### Professional — $749/month (62 sources)

**Honest assessment**: $749 for 62 readiness-supported sources with 12-month retention, human-reviewed brief, and 2 users is genuinely good value IF the product delivers those features reliably. The problem: audit binder export, acknowledgement workflow, and some delivery features are not built yet. Charging $749 for an incomplete professional workflow is a reputational risk.

**Required for this price to be honest**: Audit export, acknowledgement workflow, and reliable email delivery must all be delivered — or the plan must be explicitly called "Professional Pilot" with disclosure that these features are in development.

**Honest price for current feature set**: $549–$599 for what is actually delivered today. $749 is the right price after audit export and acknowledgement workflow ship.

---

### Compliance Consultant — Talk to us

**Honest assessment**: Correct to gate this. No fixed price is right while multi-workspace is unbuilt. Do not put a price on this tier in any public communication until multi-workspace is productized.

---

### Annual Billing

Not yet implemented. Should not be advertised until Stripe is wired. Current approach is correct.

---

## Part 7: What Would Make This Perfect — 6 Stakeholder Perspectives

---

### Perspective 1: The MLRO Filing for a Regulatory Inspection

**What perfect looks like**: The regulator asks "what monitoring did you have in place for VARA rulebook changes?" The MLRO opens StatuteProof, navigates to Sources → VARA Rulebook → Monitoring History, downloads a per-source monitoring log as PDF. The log shows: 180 monitoring runs over 6 months, 3 changes detected (with timestamps, hashes, and human review records), 177 no-change confirmations. Each record shows source URL, monitoring timestamp, content fingerprint, reviewer name, and review date. The document is clean, professional, and self-explanatory to an auditor who has never seen StatuteProof before.

**What is missing today**: The monitoring history view, the per-source PDF export, reviewer name attribution, and the formatted "no-change confirmation" record.

---

### Perspective 2: The Compliance Consultant Serving 5 Clients

**What perfect looks like**: The consultant logs in and sees a workspace selector: "Client A / ADGM Firm," "Client B / VASP," "Client C / Payments." Each workspace has its own source pack, brief history, and evidence records. The consultant generates a brief for Client A, optionally white-labels it, and sends it directly. Billing is a single monthly fee for all workspaces.

**What is missing today**: Multi-workspace. White-label. Bulk brief generation. Client data isolation. All roadmap-only.

---

### Perspective 3: The CFO Approving the Compliance Tool Spend

**What perfect looks like**: The MLRO presents the tool to the CFO. The CFO asks three questions: "What does it cover? Can we trust it? What's the ROI?" The MLRO can answer: "62 official UAE regulatory sources. Cryptographic record of every monitoring run. $749/month, which is less than one day of compliance consulting fees." The CFO approves because the ROI story is concrete and the tool is obviously legitimate.

**What is missing today**: A one-page "what is StatuteProof" summary the MLRO can send to the CFO. A clear ROI comparison. The manual monitoring cost calculation ($3,200–$12,000/month equivalent) needs to be presented on the pricing page, not just in internal docs.

---

### Perspective 4: The Regulator Auditing a Firm's Compliance Program

**What perfect looks like**: The auditor sees in the firm's compliance file: "Regulatory source monitoring: StatuteProof. 62 UAE official sources. Evidence records retained 12 months. Human review required before alert delivery." The evidence records are self-explanatory: hash matches, timestamp matches, source URL matches. The brief format includes a clear disclaimer that this is monitoring information only, not legal advice.

**What is missing today**: The evidence format (JSON) requires context a non-technical auditor does not have. A formatted, plain-language monitoring record per source per period is needed. StatuteProof also needs to avoid any appearance of regulator endorsement — it correctly does — but it needs to proactively explain to regulators how the evidence chain works.

---

### Perspective 5: The Engineer Integrating with the Firm's GRC System

**What perfect looks like**: The engineer calls `GET /api/v1/alerts?client_id=X&status=approved&since=2026-06-01` and receives structured JSON with all approved alerts. They push these into Jira or Notion. The API is documented, versioned, and has a test environment.

**What is missing today**: `api.py` exists but no public API documentation, no versioned API contract, no test environment, and no webhook support. Developer integration is not possible today.

---

### Perspective 6: The Solo MLRO at a Startup VASP

**What perfect looks like**: Signs up, completes onboarding in 5 minutes, sees: "5 sources activated: VARA Enforcement Notices, CBUAE AML/CFT, UAE FIU Typology Reports, ADGM FSRA Regulations, UAE Legislation Portal." The first monitoring run happens automatically within 24 hours. The following Monday, a brief arrives in their email: "No regulatory changes detected this week. 5 sources monitored. Evidence records are stored. Next cycle: 2026-06-23." They forward it to their board as proof of monitoring.

**What is missing today**: Self-serve activation, email delivery, automated monitoring cadence visible to the user, and the confidence that the VARA source is meaningful and not just a navigation-level page.

---

## Part 8: The Three Questions Every Buyer Will Ask

---

### "What sources do you actually cover?"

**Honest answer**: "We monitor 62 readiness-supported UAE official regulatory sources across CBUAE (27), ADGM/FSRA (10), DFSA (8), UAE FIU/EOCN (7), SCA (4), VARA (3), and federal/legislation/tax (3). Four additional sources are enabled but under extraction remediation. Coverage is strongest for CBUAE and AML/payments compliance profiles. VARA coverage is currently 3 sources and we are extending it. DIFC laws are under remediation. We do not cover global or non-UAE regulatory bodies. Full source list is available on request."

**What not to say**: "We cover 66 UAE regulatory sources." "Complete UAE regulatory coverage." "We monitor VARA" without disclosing it is 3 sources.

---

### "How do I know I can trust the monitoring?"

**Honest answer**: "Every monitoring run produces a SHA-256 content hash of the extracted source text, a timestamp, a proof record, and an extraction quality score. Changes are detected by comparing hashes between runs, not keyword scanning. Alerts are human-reviewed before delivery — we do not send raw machine-detected changes. Every brief includes a full disclaimer: monitoring information only, not legal advice. Evidence records are retained for 12 months on the Professional plan."

**What not to say**: "We never miss an update." "Our AI guarantees accuracy." "You can rely on StatuteProof for compliance."

---

### "Why not use a lawyer or compliance consultant?"

**Honest answer**: "StatuteProof does not replace qualified legal or compliance professionals. It monitors official sources systematically so your MLRO or lawyer is working from a monitored, timestamped baseline rather than manually checking websites. The value is in the evidence trail, detection consistency, and time saved — not in replacing human professional judgment. You still need a lawyer or compliance professional to interpret changes and decide what action to take."

**What not to say**: "StatuteProof replaces expensive compliance consultants." "Our AI interprets regulatory changes." "You don't need to check regulators' websites anymore."

---

## Part 9: The Brutal Bottom Line

---

### What StatuteProof is today

A technically sound regulatory source monitoring engine with cryptographic evidence records, human-reviewed brief generation, and 62 readiness-supported UAE official sources. The infrastructure is real. The evidence records are real. The source coverage is real — with well-disclosed, material gaps.

**Honest score: 6.9/10**

---

### What it is not yet

A product that a compliance professional can depend on without the founder being involved in every delivery step. The delivery pipeline is incomplete, the dashboard shows mock data in parts, VARA coverage is too thin for the most natural buyer, the acknowledgement workflow does not exist, and there is no PDF export for the compliance file.

---

### The five things that would change everything

Fix these, in this order:

**1. Zero mock data in the authenticated dashboard.**
This is trust-destroying and fixable within days.

**2. End-to-end email brief delivery, production-tested.**
Without reliable delivery, the MLRO will not pay recurring fees. This is the single largest gap between "interesting prototype" and "paying customer."

**3. VARA source depth.**
The VASP sales motion — the most natural sales motion — requires at least 5–7 VARA endpoints including rulebook content. 3 navigation-level pages are not sufficient for a VARA-licensed firm's MLRO.

**4. Acknowledgement/review workflow in the dashboard.**
The moment an MLRO can record their review response in StatuteProof is the moment it becomes a compliance workflow tool instead of a monitoring notification. This is the gap between a $200 tool and a $750 tool.

**5. PDF brief export.**
The compliance file is a PDF. This is not a premium feature. It is a basic professional output requirement.

---

### What the product is worth at current state

A controlled founding pilot at $199–$349/month for CBUAE/payments-heavy compliance profiles with explicit disclosure of VARA, DFSA, and DIFC limitations. Not yet a $749 Professional plan for a VASP MLRO.

The gap between current state and Professional pricing is these five items.

---

### Honest competitive position

StatuteProof is not a CUBE or Corlytics replacement. It is the best UAE-specific official-source monitoring tool that a small compliance team can afford and operate without a procurement cycle. That is a real, defensible position. Hold it. The moment the positioning drifts toward "enterprise UAE compliance platform" or "complete UAE regulatory coverage" without the product to back it up, trust erodes permanently.

---

### The fastest path to "ideal, trustworthy, must-have"

1. Fix the five items above (3–6 weeks).
2. Sign 2–3 paying founding pilot customers at $199–$349/month and deliver reliably.
3. Build the acknowledgement workflow.
4. Deepen VARA coverage.
5. Add PDF export.
6. Charge $749/month.

That path exists and is not long. The infrastructure is already more solid than most competitors at this stage. The gap is execution on delivery and presentation, not on the monitoring foundation.

---

*Monitoring intelligence only. Not legal advice. Not a compliance certification. Not a guarantee of complete regulatory coverage.*

*StatuteProof reports are generated from monitored official-source records and are provided for information and compliance review support only. StatuteProof does not determine compliance outcomes, prevent fines, or confirm that all regulatory updates have been captured. Users should verify official source material directly and consult qualified legal or compliance professionals before making regulatory or operational decisions.*
