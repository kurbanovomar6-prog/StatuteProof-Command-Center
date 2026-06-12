# StatuteProof — Website and App Master Specification

**Version:** 1.0  
**Date:** 2026-06-12  
**Status:** Implementation-ready  
**Scope:** Public website, authenticated app, backend API, data model, MVP phases

> This document is documentation only. No claims herein constitute legal advice or regulatory compliance guidance. All sample data is labeled [SAMPLE — NOT REAL REGULATORY DATA].

---

## SECTION 1 — EXECUTIVE PRODUCT VISION

**One-sentence product promise:** StatuteProof monitors selected UAE official regulatory sources, detects text changes, stores SHA-256 snapshot evidence, and delivers human-reviewed compliance briefs that MLRO teams can act on with an audit trail they can show.

**One-sentence "what it is not":** StatuteProof is not a legal adviser, not a guarantee of compliance, not a replacement for qualified legal counsel or internal compliance professionals, and does not certify that all regulatory updates have been captured.

**One-sentence MLRO value proposition:** Stop manually checking nine UAE regulator websites every week — get structured, evidence-backed alerts with diff records, risk context, and a human-reviewed brief that slots into your existing compliance review workflow.

**One-sentence technical proof proposition:** Every alert includes a SHA-256 hash of the monitored source text at the time of detection, a normalized diff of what changed, the official source URL, and a timestamped evidence record — so you can verify the change yourself.

**Design tone:** Serious, precise, evidence-first, premium B2B compliance tool. Not hype AI. Not crypto SaaS. Closer to Bloomberg Terminal than Notion. Typography-driven, data-dense where needed, never playful. Every design choice should reinforce the message: "this is auditable, this is trustworthy, this is built for professionals who have to answer for their decisions."

---

## SECTION 2 — TARGET USER PERSONAS

### Persona 1: MLRO at a VARA-licensed VASP

**Job title:** Money Laundering Reporting Officer  
**Company type:** Dubai-licensed virtual asset service provider — exchange, custody, or broker  
**Team size:** 2-5 compliance staff; MLRO often doubles as Head of Compliance  
**Daily pain:** VARA publishes rulebook updates, enforcement notices, and guidance on a website that has no email subscription for text changes. MLRO manually checks the site, scans PDFs, and tries to keep a shared changelog. This takes 2-4 hours per week that they do not have.  
**What they manually check today:** vara.ae/en/regulatory-framework/, vara.ae/en/enforcement/, centralbank.ae/en/regulations/, uaefiu.gov.ae  
**What they fear:** Missing a VARA rulebook change that triggers an audit finding, missing an AML/CFT circular that creates an STR reporting gap, failing a VARA supervisory review because their internal compliance log does not match the published rulebook version  
**What builds trust:** Seeing the actual official URL, the hash, the diff, and the timestamp. Not a summary that could be AI-hallucinated. Proof they can put in a board paper or an external audit response.  
**What they need on homepage:** Credible demonstration of what an alert looks like. Evidence that the product monitors the right sources (VARA, CBUAE, UAE FIU). No overclaims. Clear "not legal advice" framing — they will not forward anything that sounds like legal advice.  
**What they need in dashboard:** Source status by regulator, diff viewer, risk rating, evidence record with hash/URL, ability to export for internal audit trail.  
**What they would pay:** $299-499/month for a UAE VASP-specific pack if it saves 4+ hours/week and produces audit-ready records.

### Persona 2: CCO at a UAE fintech or payment company

**Job title:** Chief Compliance Officer  
**Company type:** UAE-licensed payment institution, fintech, money transfer operator, or licensed digital lender  
**Team size:** 3-10 compliance staff; reports to CEO or General Counsel  
**Daily pain:** CBUAE publishes regulatory circulars and frameworks with limited advance notice. The CCO needs to track CBUAE, Ministry of Finance, and UAE FIU simultaneously while also managing internal compliance programs. Monitoring is manual, fragmented, and often delegated to a compliance analyst whose work is inconsistent.  
**What they manually check today:** centralbank.ae/en/regulations/, mof.gov.ae, uaefiu.gov.ae, sometimes difc.com  
**What they fear:** A CBUAE circular that introduces a new reporting requirement going unnoticed for 60 days. An internal audit finding that the compliance team did not have a monitoring process for regulatory changes.  
**What builds trust:** An evidence record they can attach to their compliance program documentation. Clear sourcing. Disclosed limitations (they know some sources are hard to monitor and will appreciate honesty about it).  
**What they need on homepage:** Source coverage (which regulators, which URLs), evidence trail explanation, pricing that fits a sub-$2K/month SaaS budget.  
**What they need in dashboard:** Filterable alert feed by regulator and risk level, brief export to PDF/email, team review workflow.  
**What they would pay:** $499-999/month for a UAE pack if the brief quality is good enough to forward to their General Counsel.

### Persona 3: Compliance consultant serving multiple UAE regulated clients

**Job title:** Independent compliance consultant, compliance advisory partner, or small compliance firm principal  
**Company type:** Boutique compliance consultancy, often 1-10 people, serving 5-20 UAE-regulated clients simultaneously  
**Team size:** Solo to small team  
**Daily pain:** Manually tracks regulatory updates across multiple regulators for multiple clients. Produces bespoke monitoring reports. Each report takes 2-4 hours to compile. The volume does not scale as the practice grows.  
**What they manually check today:** Everything their clients are regulated by — typically VARA, CBUAE, DFSA, ADGM FSRA, UAE FIU, SCA (when accessible), Ministry of Finance  
**What they fear:** Advising a client incorrectly because they missed a source change. Losing a client because a competitor caught a regulatory update faster. Reputational damage if a monitoring gap leads to a client compliance failure.  
**What builds trust:** The ability to white-label or reformat briefs for client delivery. Evidence records they can share. Clear "not legal advice" disclaimers they can attach without adding their own.  
**What they need on homepage:** Multi-client positioning, consultant pack pricing, evidence quality demonstration.  
**What they need in dashboard:** Multi-client/org workspace (later), brief export, ability to set custom regulators per client.  
**What they would pay:** $999-2000/month for a consultant pack if it covers 5+ clients and replaces 10+ hours of manual monitoring per week.

### Persona 4: Legal/compliance analyst at a DFSA or ADGM-regulated firm

**Job title:** Compliance Analyst, Regulatory Affairs Manager, Associate General Counsel  
**Company type:** Bank, asset manager, broker, or professional services firm regulated by DFSA (DIFC) or ADGM FSRA  
**Team size:** 10-50 compliance staff; analyst reports to Head of Compliance or General Counsel  
**Daily pain:** Tracks DFSA rulebook changes, ADGM FSRA updates, and DIFC laws simultaneously. Changes to the DFSA rules can require immediate policy updates. The analyst feeds a compliance register that their Head of Compliance reviews weekly.  
**What they manually check today:** dfsa.ae/rules-and-standards, dfsa.ae/regulation/notices-public-registers, adgm.com/fsra, difc.com/business/laws-and-regulations/  
**What they fear:** Missing a DFSA rule update that requires a policy or procedure change before their next supervisory review. Creating an internal compliance calendar gap.  
**What builds trust:** Professional presentation. Audit-ready evidence. Compatibility with their internal compliance management system (they may want webhook integration or export). Clear delineation between "detected change" and "legal interpretation" — they will add the legal interpretation themselves.  
**What they need on homepage:** DFSA/ADGM-specific source coverage, evidence quality, API/integration capability (future), pricing that fits a larger firm budget.  
**What they need in dashboard:** Rulebook diff viewer, source-specific alerts, evidence record detail page.  
**What they would pay:** $499-1000/month or as part of a broader compliance software budget; integration API would unlock higher pricing.

---

## SECTION 3 — PUBLIC WEBSITE INFORMATION ARCHITECTURE

### Page 1: Home (/)

**Purpose:** Convert MLRO/CCO visitors into Source Readiness Review requests or sample brief downloads. Establish that StatuteProof is a credible, evidence-first tool — not another AI compliance chatbot.  
**Target user:** All four personas, cold or warm traffic  
**Primary CTA:** "Request a free UAE source readiness review"  
**Secondary CTA:** "View sample evidence-backed brief"  
**Page sections:** Hero, Sample Evidence Alert Card, Problem section, How StatuteProof Works, UAE Source Coverage, Evidence Trail section, Weekly Brief section, Human Review section, Source Readiness Review CTA, Use Cases, Pricing/Pilot preview, FAQ, Footer  
**Copy direction:** Evidence-first, professional, never hype. Use "detects", "stores", "monitors", "supports review" — never "guarantees", "prevents", "replaces"  
**Trust elements:** Official source URLs in the alert card, SHA-256 hash display, "human review required" language, clear disclaimer  
**Legal-safety requirements:** Standard short disclaimer in footer. No claims of completeness. No legal advice language. Sample data clearly labeled.  
**What not to say:** AI lawyer, guarantee compliance, prevent fines, replace lawyers, 100% accurate, never miss an update, official partner of any regulator

### Page 2: How It Works (/how-it-works)

**Purpose:** Explain the monitoring-to-brief pipeline for skeptical buyers who want to understand the mechanics before requesting a review  
**Target user:** Persona 1 and 2 who are evaluating vs. alternatives (manual checking, Thomson Reuters, other tools)  
**Primary CTA:** "Request a source readiness review"  
**Secondary CTA:** "View sample evidence alert"  
**Page sections:** Pipeline overview (5 steps), source check mechanics, evidence record explanation, diff viewer explanation, brief workflow, human review gate, limitations disclosure  
**Copy direction:** Technical credibility. Show the pipeline honestly. Acknowledge limitations.  
**Trust elements:** Specific source names and URLs, SHA-256 explanation, "not automated legal advice" language  
**Legal-safety requirements:** Explain what human review means. Note that monitoring may be affected by website changes, access limits, PDF formatting.  
**What not to say:** Fully automated compliance, real-time monitoring (unless true), 100% source coverage

### Page 3: Source Coverage (/sources)

**Purpose:** Show exactly which UAE sources are monitored, their status, and disclosed limitations  
**Target user:** All personas evaluating whether their relevant regulators are covered  
**Primary CTA:** "Request a readiness review for your specific sources"  
**Secondary CTA:** None  
**Page sections:** UAE sources table (13 READY sources with URLs and status), limitations disclosure section, custom source inquiry form link, non-UAE markets teaser  
**Copy direction:** Transparent and precise. Show Active/Limited/Not Active status honestly. Do not claim complete coverage.  
**Trust elements:** Official URLs for each source, status explanation, geo-restriction disclosures  
**Legal-safety requirements:** State that source monitoring may be affected by website changes, JavaScript rendering limitations, PDF access issues, and geo-restrictions. Never claim complete UAE regulatory coverage.  
**What not to say:** Complete UAE coverage, all regulators monitored, nothing missed

### Page 4: Sample Evidence Brief (/sample-brief)

**Purpose:** Let prospects download or view a realistic sample brief to evaluate quality before committing  
**Target user:** Personas 1 and 2 who need to evaluate brief quality before internal approval  
**Primary CTA:** "Request your free UAE source readiness review"  
**Secondary CTA:** "Download sample PDF"  
**Page sections:** SAMPLE / FAKE label at top, evidence alert card, diff section, risk score, brief text, evidence record details, disclaimer  
**Copy direction:** Realistic but clearly labeled. Shows what a real brief looks like. Does not imply the sample represents a real regulatory change.  
**Trust elements:** SAMPLE / FAKE label, not-legal-advice disclaimer, evidence record format  
**Legal-safety requirements:** Prominent "SAMPLE / FAKE — NOT REAL REGULATORY DATA" label. Full disclaimer. No real regulatory content.  
**What not to say:** This is a real regulatory update, this represents actual VARA guidance

### Page 5: Source Readiness Review (/readiness-review)

**Purpose:** Dedicated landing page for the free Source Readiness Review CTA that appears throughout the site  
**Target user:** All personas responding to the primary CTA  
**Primary CTA:** Form submission  
**Secondary CTA:** None  
**Page sections:** What a readiness review is, what you receive, form (company/name/email/regulators/use case), what happens next, timeline, disclaimer  
**Copy direction:** Service description, not sales. Honest about what the review covers and does not cover.  
**Trust elements:** Specific deliverable list, timeline, no-commitment framing  
**Legal-safety requirements:** State clearly that the readiness review is not legal advice and not a compliance assessment.  
**What not to say:** Free compliance audit, legal review, certified assessment

### Page 6: Pricing / Pilot (/pricing)

**Purpose:** Convert research-stage visitors to pilot requests; filter for right-fit customers  
**Target user:** Personas 1-3 who have evaluated the product and want to understand costs  
**Primary CTA:** "Request a pilot" or "Book intro call"  
**Secondary CTA:** "Start with a free source readiness review"  
**Page sections:** 4 tiers (Free Source Check, Founding Pilot, UAE VASP Pack, Consultant Pack), FAQ, disclaimer  
**Copy direction:** Transparent pricing, clear inclusions and exclusions, no fake logos or customer counts  
**Trust elements:** No fake social proof, honest pilot framing, clear refund/cancellation terms (manual invoicing)  
**Legal-safety requirements:** No guarantee language. No "prevent fines" framing in pricing benefits.  
**What not to say:** Guarantee compliance, prevent fines, replace your compliance team, unlimited sources

### Page 7: Security and Evidence (/security)

**Purpose:** Address trust questions from technical buyers and compliance teams who need to explain the product to their IT/security function  
**Target user:** Persona 2 and 4 who face internal security reviews  
**Primary CTA:** "Request a readiness review"  
**Secondary CTA:** None  
**Page sections:** How evidence is stored (SHA-256, timestamps, snapshots), what data is retained, what data is not retained, server infrastructure (honest — do not claim SOC 2 if not certified), snapshot security, API security overview  
**Copy direction:** Honest, precise, technical. Do not overclaim security certifications.  
**Trust elements:** Technical specifics, honest limitations, data retention explanation  
**Legal-safety requirements:** Do not claim SOC 2, ISO 27001, or any certification not actually achieved.  
**What not to say:** Enterprise-grade security (without specifics), bank-grade encryption (without specifics), SOC 2 certified (unless true)

### Page 8: About / Methodology (/about)

**Purpose:** Establish founder credibility and product methodology for buyers who want to understand who is behind this  
**Target user:** All personas doing due diligence  
**Primary CTA:** "Request a source readiness review"  
**Secondary CTA:** "Contact us"  
**Page sections:** What StatuteProof is, methodology (official-source-only, not news aggregation), limitations of the approach, founder note, contact  
**Copy direction:** Transparent, human, professionally grounded. Not startup hype.  
**Trust elements:** Honest methodology, limitations disclosure, direct contact  
**Legal-safety requirements:** Full not-legal-advice disclaimer. No implied legal expertise.  
**What not to say:** AI lawyer, regulatory expert team, certified compliance professionals on staff

### Page 9: Login (/login) and Register (/register)

**Purpose:** Entry points for authenticated users. Register is invite/pilot only at MVP.  
**Target user:** Pilot customers  
**Primary CTA:** Email/password form  
**Secondary CTA:** "Don't have an account? Request access"  
**Page sections:** Form, legal acknowledgement checkbox, link to Privacy Policy and Terms  
**Trust elements:** HTTPS, password requirements visible, no ambiguous "agree to marketing" checkboxes  
**Legal-safety requirements:** Terms of Service and Privacy Policy links visible. Login/register does not imply compliance certification.  
**What not to say:** Free trial (unless one exists), guaranteed access

### Page 10: Terms of Service (/terms)

Standard B2B SaaS terms. Key clauses: not legal advice, monitoring information only, no guarantee of completeness, user responsibility for compliance decisions, data usage, payment terms (manual invoicing at MVP).

### Page 11: Privacy Policy (/privacy)

Standard. Key: what data is collected (email, company, source configuration), where it is stored, how long retained, user rights.

### Page 12: Disclaimer (/disclaimer)

Full standard disclaimer page. Links from every brief, every alert page, every email.

---

## SECTION 4 — HOMEPAGE SPEC IN EXTREME DETAIL

### Hero Section

**5 Headline Options:**

1. "Monitor UAE regulatory sources. Know what changed. Have the evidence to show it." *(evidence/proof-first, process-first, not AI-first)*
2. "Official-source regulatory monitoring with an audit trail for UAE compliance teams." *(direct, B2B, evidence-first)*
3. "Your UAE compliance team doesn't need another tool. They need proof of what changed." *(problem-first, contrast)*
4. "SHA-256. Diff. Timestamp. That's what a regulatory change looks like at StatuteProof." *(technical credibility, bold)*
5. "When VARA publishes a rule change, StatuteProof detects it, stores the evidence, and drafts the brief. You review it." *(pipeline, human-review honest)*

**Chosen winner:** Headline 1 — "Monitor UAE regulatory sources. Know what changed. Have the evidence to show it."

**Rationale for choice:** Evidence-first without being cryptic. "Know what changed" addresses the core MLRO fear. "Have the evidence to show it" speaks to audit readiness — the real business driver. Not AI-first (AI is over-indexed on competitor landing pages). Not "prevent fines" (forbidden). Not "replace your team" (forbidden). Directly addresses what Persona 1 (MLRO) and Persona 2 (CCO) care about most.

**Subheadline:** StatuteProof monitors selected UAE official regulatory sources (VARA, CBUAE, DFSA, ADGM FSRA, UAE FIU, and more), detects text changes, stores SHA-256 evidence records, and delivers human-reviewed compliance briefs. For UAE-regulated VASPs, fintechs, and financial firms.

**Primary CTA button:** "Request a free UAE source readiness review"  
**Why NOT "Start free trial":** There is no self-serve product yet. A free trial CTA without a working product creates a trust gap when users click and reach a contact form. "Request a free source readiness review" is honest about what happens next, sets the right expectation (you receive a tailored report, not instant product access), and qualifies the lead.

**Secondary CTA button:** "View sample evidence-backed brief"

**Trust line (below CTAs):** Monitoring information only. Not legal advice. Source coverage and limitations disclosed.

**Disclaimer line (small text):** StatuteProof reports are for information and compliance review support only. Not legal advice, not compliance certification. See full disclaimer.

**Visual design:** Dark navy background (#0B1426). White headline text. Slate/muted subheadline (#8B9AB5). Primary CTA: white button with dark navy text (inverted, draws the eye). Secondary CTA: outlined/ghost button in white. No hero image. Instead: the Sample Evidence Alert Card sits directly below/beside the hero copy as evidence of the product.

**Why no hero image:** Generic office photos are trust-destroying for a B2B compliance product. The sample alert card is the product — showing it in the hero is more honest and more convincing than photography.

---

### Sample Evidence Alert Card (appears in hero or immediately below)

**SAMPLE / FAKE — NOT REAL REGULATORY DATA**

```
┌─────────────────────────────────────────────────────────────────┐
│  REGULATORY CHANGE DETECTED                     [SAMPLE / FAKE] │
│                                                                  │
│  Source:         VARA — Enforcement Notices                      │
│  Regulator:      Dubai Virtual Assets Regulatory Authority       │
│  URL:            https://www.vara.ae/en/enforcement/             │
│  Status:         ● CHANGED                                       │
│  Detected:       2026-06-10 09:14:22 UTC                        │
│  Risk Level:     MEDIUM                                          │
│                                                                  │
│  Affected Entities:  VASP licence holders, custody providers     │
│                                                                  │
│  Evidence Record                                                 │
│  Previous hash:  a3f8d2c1...b9e4f7a0  (2026-06-03)             │
│  Current hash:   7c1a9b3e...d2f6e8c4  (2026-06-10)             │
│  Diff available: YES — 3 sections changed                        │
│  Snapshot saved: data/source_snapshots/2026-06-10/AE/           │
│  Normalization:  text/whitespace-normalized before hashing       │
│                                                                  │
│  ⚠  Human review required before delivery                       │
│                                                                  │
│  Disclaimer: Not legal advice. For monitoring information only.  │
│  Review evidence record and official source before acting.       │
└─────────────────────────────────────────────────────────────────┘
```

**Visual design notes:**
- Dark navy card background (#0F1E35), slightly lighter than page background
- Left border: 3px solid green (#22C55E) for CHANGED status
- "CHANGED" badge: green background (#22C55E), dark text
- "SAMPLE / FAKE" badge: amber/orange (#F59E0B), visible in top-right corner
- Hash strings: monospace font (JetBrains Mono or similar), slate color
- "Human review required" row: highlighted row with amber/caution styling
- Evidence section: slightly lighter background within the card
- Typography: Inter or similar precision sans-serif for all card content

---

### Problem Section

**Headline:** The problem with manual regulatory monitoring is the gap you don't see.

**Body copy:**

Most compliance teams at UAE VASPs and fintechs check regulatory websites manually — a few times a week if they're disciplined, less often if they're busy. VARA publishes rulebook updates on a website. CBUAE posts circulars as PDFs. The UAE FIU publishes AML/CFT guidance with no alert emails. DFSA updates its rules without notifying every regulated firm by name.

The real risk isn't the update you catch. It's the one that sat on an official website for three weeks before anyone on your team noticed.

Manual monitoring also creates an audit problem. When your VARA supervisory reviewer asks when you became aware of a rule change, "we checked the website regularly" is not the same as "here is the timestamped evidence record with the diff."

**Supporting bullets:**
- 9 UAE official regulatory sources require active monitoring for most licensed firms
- No official consolidated UAE regulatory change notification service exists
- Website changes, PDF reformats, and JavaScript rendering can cause missed updates even when teams are diligent
- Monitoring without evidence records creates an audit gap — you know you checked, but you cannot prove it

---

### How StatuteProof Works (3-4 steps)

**Headline:** From official source to evidence-backed brief — the complete workflow.

**Step 1 — Monitor official sources**
StatuteProof fetches selected UAE official regulatory sources (VARA, CBUAE, DFSA, ADGM FSRA, UAE FIU, DIFC Laws, Ministry of Finance, Ministry of Economy, UAE Legislation Portal) on a scheduled basis using configured extractors. Sources are fetched from their official URLs. Limitations (JavaScript-only pages, geo-restricted sources, PDF-only sources) are disclosed per source.

**Step 2 — Detect changes with evidence**
Fetched content is normalized (whitespace, encoding, formatting removed) and hashed using SHA-256. When the current hash differs from the stored baseline hash, the source is marked CHANGED. A diff of the normalized text is generated, showing exactly what was added, removed, or modified. The raw snapshot, normalized text, hash, and diff are all stored together as an evidence record.

**Step 3 — Score risk and draft alert**
The detected change is assessed against a rule-based risk classifier. Risk levels: LOW, MEDIUM, HIGH. High-risk signals include: obligation language, deadline references, penalty/fine language, licensing changes, AML/CFT framework changes. The alert draft includes the change type, risk level, rationale, changed excerpts, affected entity categories, and the proof block. All drafts are HOLD_FOR_REVIEW.

**Step 4 — Human review, then brief delivery**
No alert or brief reaches a customer without explicit human review and approval. A compliance review step is required before any HIGH-risk alert is delivered. The human reviewer can approve for urgent delivery, approve for weekly brief, reject, or escalate. After approval, the brief includes the evidence record, diff excerpt, risk score, affected entities, and the full not-legal-advice disclaimer.

---

### UAE Source Coverage Preview Section

**Headline:** 13 READY UAE regulatory sources. Limitations disclosed.

**Subheadline:** StatuteProof monitors these official UAE sources. Source status, extraction quality, and access limitations are shown honestly.

**Source table (13 READY sources at time of writing):**

| Source | Regulator | Category | Status | Notes |
|--------|-----------|----------|--------|-------|
| VARA — Enforcement Notices | VARA | Financial Regulator | READY | vara.ae/en/enforcement/ |
| CBUAE Regulations | Central Bank UAE | Central Bank | READY | centralbank.ae/en/regulations/ |
| Dubai Financial Services Authority (DFSA) | DFSA | Financial Regulator | READY | dfsa.ae/rules-and-standards |
| DFSA Regulatory Notices | DFSA | Financial Regulator | READY | dfsa.ae/regulation/notices-public-registers |
| Abu Dhabi Global Market (ADGM FSRA) | ADGM | Financial Regulator | READY | adgm.com/fsra |
| DIFC Laws and Regulations | DIFC | Legal Database | READY | difc.com/business/laws-and-regulations/ |
| UAE FIU Circulars and Notices | UAE FIU | AML/CFT | READY | uaefiu.gov.ae/en/Publications/ |
| UAE Ministry of Finance | Ministry of Finance | Finance Ministry | READY | mof.gov.ae |
| UAE Legislation Portal | UAE Government | Legal Acts | READY | uaelegislation.gov.ae |
| UAE Ministry of Economy | Ministry of Economy | Company Registry | READY | moet.gov.ae/en/ |
| VARA Homepage | VARA | Financial Regulator | READY | vara.ae |
| Central Bank UAE Homepage | CBUAE | Central Bank | READY | centralbank.ae |
| UAE FIU Homepage | UAE FIU | AML/CFT | READY | uaefiu.gov.ae |

**Limitation disclosure (always visible):**
Source monitoring may be affected by website changes, JavaScript rendering limitations, PDF access restrictions, and UAE geo-restrictions. UAE Federal Tax Authority (FTA), UAE Official Gazette, and certain SCA pages are not currently monitorable from outside UAE. StatuteProof does not claim complete UAE regulatory coverage. See the Source Coverage page for full status.

---

### Evidence Trail Section

**Headline:** Every change comes with a proof record you can audit yourself.

**Body copy:**
When StatuteProof detects a change on an official source, it does not just send you a summary. It stores an evidence record that contains everything you need to verify the detection independently:

- The official source URL
- The full normalized text snapshot before and after the change
- SHA-256 hash of both the before and after snapshots
- The precise diff — what text was added, what was removed
- The extraction method used (HTML, PDF, or Playwright-rendered)
- The timestamp of detection in UTC
- Extraction quality rating and any known limitations

This is not a summarization tool. The evidence record is the foundation. The brief is built on top of it, and the brief cannot be delivered if the evidence record is incomplete.

---

### Weekly Brief Section

**Headline:** One brief per week, per client profile — reviewed before it reaches you.

**Body copy:**
StatuteProof generates weekly monitoring briefs from approved change events. Each brief includes: a header showing the monitoring period, a list of reviewed regulatory updates with source, risk level, and brief description, a source coverage and limitations section, and the full not-legal-advice disclaimer.

Briefs are generated only from alerts that have been explicitly approved for delivery by a human reviewer. An empty monitoring period does not generate a false "nothing changed" brief — it generates an honest "no reviewed updates were approved for this brief period" brief with the source coverage status included.

Brief format: Markdown (for copy-paste into your compliance system) and PDF export. Later: direct email delivery, Slack integration.

---

### Human Review / Not Legal Advice Section

**Headline:** StatuteProof detects and documents. Your team reviews and decides.

**Body copy:**
Every StatuteProof alert and brief is produced by an automated monitoring pipeline and reviewed by a human before delivery. We do not send automated legal interpretations. We do not claim to tell you whether you are compliant. We do not replace your legal team or your MLRO.

What StatuteProof does: detects text changes on monitored official sources, stores evidence of the change, classifies risk using a rule-based classifier, drafts a brief for human review, and delivers the brief with the evidence record attached.

What you do with the brief: review it with your compliance team, verify the change against the official source, consult your legal counsel if the risk level requires it, update your compliance program accordingly.

StatuteProof reports are for information and compliance review support only. They do not constitute legal advice, regulatory advice, compliance certification, or a legal opinion.

---

### Source Readiness Review CTA Section

**Headline:** See exactly which UAE sources are monitorable for your firm — before you commit.

**Body copy:**
A free UAE Source Readiness Review gives you a detailed report of which UAE regulatory sources are currently active, which have access limitations, and which are not currently monitorable. We test the specific sources relevant to your licence type and tell you honestly what we can and cannot cover.

The review takes 2-3 business days. No commitment required. You receive a readiness report, not a sales pitch.

**CTA button:** "Request a free UAE source readiness review"  
**Supporting text:** Responds within 1 business day. Takes 2-3 business days to complete. No automatic subscription.

---

### Pricing Preview Section

**Headline:** Start with a free source readiness review. Pilot when you're ready.

**4 tiers preview:**
1. **Free Source Readiness Review** — see what's monitorable before you commit
2. **Founding Pilot** — $99-299/month — small UAE source pack, weekly brief, evidence records
3. **UAE VASP/Fintech Pack** — $499-999/month — full UAE P0 sources, custom profile, brief delivery
4. **Compliance Consultant Pack** — $999-2000/month — multi-client, configurable source packs

Full pricing details on the Pricing page.

---

### FAQ Section (8 Questions)

**Q1: Is StatuteProof a legal adviser or compliance consultant?**
No. StatuteProof is an official-source monitoring tool that detects text changes, stores evidence records, and delivers human-reviewed compliance briefs. It does not provide legal advice, regulatory interpretations, or compliance opinions. Always consult qualified legal counsel before making regulatory, filing, or operational decisions.

**Q2: Which UAE regulatory sources does StatuteProof monitor?**
Currently: VARA, CBUAE, DFSA, ADGM FSRA, UAE FIU, DIFC Laws, UAE Ministry of Finance, UAE Ministry of Economy, and UAE Legislation Portal (13 ready sources). Source availability is disclosed per source. Some UAE sources (FTA, Official Gazette, certain SCA pages) are not currently accessible from outside UAE. See the Source Coverage page for full status.

**Q3: What happens if a source website changes its structure?**
StatuteProof monitors known limitations actively. If a source undergoes a structural change that breaks extraction, the source status is updated to reflect the issue and disclosed to you. Extraction quality is rated per source run. We do not silently continue to report UNCHANGED when extraction has failed — failure is surfaced as a distinct status.

**Q4: Does StatuteProof cover all UAE regulators?**
No. StatuteProof covers selected official UAE sources and discloses which sources are monitored, which have limitations, and which are not accessible. We do not claim complete UAE regulatory coverage. Adding new sources requires source testing, quality validation, and manual configuration.

**Q5: Can I add my own custom sources?**
Yes (on applicable plans). Custom source monitoring allows you to add official source URLs not in the default UAE pack. Custom sources are subject to the same extraction quality testing and status disclosure. Not all URLs are suitable for automated monitoring — sources requiring login, CAPTCHA, or complete geo-restriction are not supported.

**Q6: What does "human review required" mean?**
Every alert generated by the monitoring pipeline is reviewed by a human before delivery. No automated alert or brief is sent directly to customers without an explicit review and approval step. HIGH-risk alerts require additional review before delivery.

**Q7: How does the evidence record work?**
Each change event produces an evidence record containing: the official source URL, SHA-256 hash of the normalized text before and after the change, the diff of what changed, the extraction method and quality, and a timestamp. You can verify any record independently by re-fetching the official source and comparing hashes.

**Q8: What if I need monitoring for a regulator not in the current UAE pack?**
Request a source readiness review and specify the regulator or URL. We will test the source, disclose its extractability, and if it passes quality standards, add it to your monitoring profile. Custom source additions may require additional setup time.

---

### Footer

**Footer content:**
- StatuteProof logo (top-left)
- Nav links: Home, How It Works, Source Coverage, Sample Brief, Pricing, Security, About, Login
- Legal links: Terms of Service, Privacy Policy, Disclaimer
- Disclaimer text (abbreviated): StatuteProof monitors selected official UAE regulatory sources. Reports are for information and compliance review support only. Not legal advice, not compliance certification, not a guarantee of completeness. Source monitoring may be affected by website changes, access restrictions, and PDF formatting. Consult qualified legal counsel before acting on any report. StatuteProof is not affiliated with, endorsed by, or an official partner of VARA, CBUAE, DFSA, ADGM, UAE FIU, or any UAE regulatory authority.
- Copyright line

---

## SECTION 5 — REGISTRATION / LOGIN / ACCOUNT SYSTEM

### Registration Form (Full Fields)

**Required fields:**
- Email address (validated format, not disposable domain check recommended)
- Password (min 12 chars, at least one uppercase, one number, one special character)
- First name
- Last name
- Company name
- Job title (free text or dropdown: MLRO, CCO, Compliance Manager, Legal Counsel, Compliance Analyst, Consultant, Other)
- Country of operation (dropdown, UAE pre-selected)
- I have read and agree to the Terms of Service [checkbox — required]
- I understand that StatuteProof reports are for information only and do not constitute legal advice [checkbox — required]

**Optional onboarding fields (shown post-registration on onboarding step 1):**
- Company type (dropdown: VASP, Fintech/Payment, Bank, Asset Manager, Broker, DIFC/ADGM Firm, Consultancy, Other)
- Licence type (free text: VARA, DFSA, ADGM FSRA, CBUAE-licensed, Other)
- Primary regulator(s) to monitor (multi-select: VARA, CBUAE, DFSA, ADGM FSRA, UAE FIU, DIFC, Ministry of Finance, Ministry of Economy, UAE Legislation Portal, Other)
- Approximate team size for compliance function
- How did you hear about us (dropdown: LinkedIn, referral, Google, other)
- Pilot interest: "I am interested in a paid pilot" checkbox

### Login

- Email + password form
- "Forgot password?" link → password reset flow
- "Don't have an account? Request access" link (not open self-registration at MVP)
- Error states: "Incorrect email or password" (do not specify which one — security)
- After 5 failed attempts: "Too many failed attempts. Please try again in 15 minutes or reset your password."
- Magic link login: future feature (noted in spec but not required for MVP)
- Session: JWT access token (15 min) + HttpOnly refresh cookie (7 days)

### Password Reset Flow

1. User clicks "Forgot password?" → enters email
2. If email exists: "If this email is registered, you will receive a reset link within 5 minutes." (same message for registered and unregistered — prevent email enumeration)
3. User clicks link in email → lands on /reset-password?token=...
4. Form: new password + confirm password
5. On success: "Password updated. You can now log in."
6. Reset link expires in 1 hour. Single use.

### Roles Table

| Role | Description | Permissions |
|------|-------------|-------------|
| Owner | Organization owner (first registered user) | All permissions including billing, user management, org settings, all data |
| Admin | Organization administrator | All permissions except billing/payment; can invite users, configure sources, approve briefs |
| Compliance User | Standard compliance team member | View all alerts/briefs/sources, create reviews, export reports, cannot configure sources or manage users |
| Reviewer | Human review workflow participant | Same as Compliance User plus: approve/reject alerts, approve briefs for delivery |
| Read-only Auditor | External auditor or guest | View alerts, evidence records, briefs — no edit, no export, view-only |

### User Journey: Register → Onboarding → Dashboard

1. Register form → email verification sent
2. Email verification → click link → "Email verified. Set up your account."
3. Onboarding step 1: Company profile (company type, licence type, primary regulators)
4. Onboarding step 2: Choose source pack (UAE Standard, UAE VASP Pack, UAE DFSA Pack, Custom)
5. Onboarding step 3: Select specific regulators to monitor (pre-populated from source pack)
6. Onboarding step 4: Add custom source (optional, skip available)
7. Onboarding step 5: Book source readiness review (optional, skip available)
8. Onboarding step 6: Dashboard with checklist (3 items: sources configured, first run complete, first brief delivered)

**Empty state (new user, no data):** "Your monitoring is being set up. Your first source run will complete within 24 hours. In the meantime, view the sample brief to understand what you'll receive." [View sample brief] [Track setup status]

**Confirmation email copy:**
Subject: "Verify your StatuteProof account"
Body: "You're almost set up. Click below to verify your email and complete registration. This link expires in 24 hours. If you did not sign up for StatuteProof, ignore this email."

**Invite flow:**
Owner or Admin sends invite from Settings > Team. Invitee receives email with invite link (expires 72 hours). Invitee clicks link → registration form pre-filled with email, role shown. Invitee sets password and accepts Terms of Service. Invitee joins organization immediately on completion.

---

## SECTION 6 — ONBOARDING FLOW

### Step 1 — Company Profile

**Screen title:** "Tell us about your compliance context"  
**Microcopy:** "This helps us suggest the right source pack and configure alerts relevant to your licence type."  
**Fields:** Company name (pre-filled from registration), company type (dropdown), licence type (free text), regulatory jurisdiction (UAE default), primary use case (dropdown: VASP compliance monitoring, Fintech/payment compliance, DFSA/ADGM firm compliance, Multi-client consultancy, Other)  
**CTA:** "Continue"  
**Validation:** Company type required. Others optional.  
**Skip rule:** Cannot skip — company profile is used for source pack recommendation.  
**Error state:** "Please select a company type to continue."

### Step 2 — Choose Source Pack

**Screen title:** "Choose your starting source pack"  
**Microcopy:** "Source packs are pre-configured sets of UAE official sources. You can add custom sources or adjust the pack after onboarding."  
**Options:** UAE Core Pack (VARA, CBUAE, UAE FIU — recommended for all UAE regulated firms), UAE VASP Pack (adds DFSA, DIFC Laws for DIFC-regulated VASPs), UAE Fintech Pack (adds Ministry of Finance, UAE Legislation Portal), Custom (select individually)  
**CTA:** "Select pack and continue"  
**Validation:** Selection required  
**Skip rule:** Cannot skip — a source pack is required to start monitoring.  
**Empty state:** N/A (options always shown)  
**Error state:** "Please select a source pack."

### Step 3 — Select Regulators

**Screen title:** "Confirm your monitored sources"  
**Microcopy:** "Based on your source pack selection, these sources will be monitored. You can deselect any source or add others."  
**Fields:** Pre-populated source list based on Step 2 selection. Checkboxes for each source. Extraction quality rating shown per source (GOOD/MEDIUM/LIMITED). Official URL shown per source.  
**CTA:** "Confirm sources"  
**Validation:** At least 1 source must be selected.  
**Skip rule:** Cannot skip — monitoring requires at least one source.  
**Error state:** "Select at least one source to monitor."

### Step 4 — Add Custom Source (Optional)

**Screen title:** "Add a custom source (optional)"  
**Microcopy:** "If you monitor a regulatory source not in our UAE pack, you can add it here. Custom sources are subject to extraction quality testing and may not be immediately active."  
**Fields:** Source URL (required), Source name (required), Regulator/authority name (required), Source type (dropdown: HTML page, PDF document, Official gazette), Monitoring frequency (daily/weekly)  
**CTA:** "Test and add source" | "Skip for now"  
**Validation:** URL must be a valid HTTPS URL. URL must not be a social media, news aggregator, or non-official domain.  
**Skip rule:** Skip available — custom source addition is optional.  
**Empty state:** "No custom sources added yet."  
**Error state:** "This URL did not pass our quality test. [View test results] You can add it manually with a note, or skip for now."

### Step 5 — Book Source Readiness Review (Optional)

**Screen title:** "Request a free UAE source readiness review (optional)"  
**Microcopy:** "A source readiness review gives you a detailed report of which UAE sources are active, which have limitations, and which cannot be monitored. We run this within 2-3 business days."  
**Fields:** Pre-filled: name, email, company. Optional: specific sources of interest (free text), questions/notes  
**CTA:** "Request readiness review" | "Skip for now"  
**Skip rule:** Skip available.  
**Empty state:** N/A

### Step 6 — Dashboard Checklist

**Screen title:** "Your monitoring setup is underway"  
**Microcopy:** "Your first source run will complete within 24 hours. Use the checklist below to complete your setup."  
**Checklist items:**
- [x] Account created
- [x] Sources configured (N sources selected)
- [ ] First source run complete (scheduled: within 24 hours)
- [ ] First brief ready for review
- [ ] Invite a team member (optional)
**CTA:** "View dashboard" | "View sample brief while you wait"

---

## SECTION 7 — AUTHENTICATED APP / DASHBOARD

### Main Navigation

Items (left sidebar or top nav):
1. Dashboard (home overview)
2. Sources (source management)
3. Alerts (change alert feed)
4. Evidence (evidence records)
5. Briefs (weekly briefs and drafts)
6. Settings (org, team, notifications, billing)

Secondary nav items (collapsible):
- Diff Viewer (accessed from evidence/alert detail)
- Review Queue (accessible from Alerts or Briefs)

### Dashboard Widgets (8)

1. **Source Status Overview** — Total sources, count by status (READY/CHANGED/FAILED/QUALITY_DROP). Click → Sources page
2. **Active Alerts** — Count of unreviewed alerts pending human review. Risk breakdown (LOW/MEDIUM/HIGH). Click → Alerts page
3. **Recent Evidence** — Last 5 evidence records with source name, status, and timestamp. Click → Evidence page
4. **Briefs Ready** — Count of briefs approved and ready to view/export. Click → Briefs page
5. **Review Queue** — Count of items waiting for human approval. Shows reviewer name if assigned. Click → Review Queue
6. **Source Health** — Mini table of last-checked status per source. Shows CHANGED/UNCHANGED/FAILED per source. Color-coded.
7. **Last Run Summary** — Timestamp of last monitoring run, sources run, changed count, errors count
8. **Onboarding Checklist** (shown until complete) — Progress bar for setup steps

### Main Alerts Table

**Columns:** Source Name | Regulator | Status | Risk Level | Detected | Change Type | Review Status | Actions

**Status Badges (colors):**

| Status | Color | Tooltip |
|--------|-------|---------|
| FIRST_SEEN | Blue (#3B82F6) | "First snapshot stored for this source" |
| UNCHANGED | Grey (#6B7280) | "No text change detected since last run" |
| CHANGED | Green (#22C55E) | "Text change detected — review evidence record" |
| FAILED | Red (#EF4444) | "Source fetch or extraction failed — check source" |
| QUALITY_DROP | Amber (#F59E0B) | "Extraction quality dropped below threshold" |
| SOURCE_STRUCTURE_CHANGED | Purple (#8B5CF6) | "Source HTML structure changed — adapter may need updating" |

**Actions per row:** View evidence | View diff | Start review | Export

**Empty state (new user):**
"No alerts yet. Your first monitoring run will complete within 24 hours. [View sources] [View sample alert]"

---

## SECTION 8 — SOURCES PAGE

### Source Management Overview

**Filter options:** By regulator, by status, by category (central_bank, financial_regulator, aml, legal_acts, etc.), by tier (P0/P1/P2), by extraction quality (GOOD/MEDIUM/THIN/FAILED)

**Sort options:** Last checked (default), Source name, Regulator, Extraction quality, Status

### Source Card Fields

Each source card (or table row) shows:

- **Source name** (e.g., "VARA — Enforcement Notices")
- **Regulator** (e.g., "Dubai Virtual Assets Regulatory Authority")
- **Official/Custom label** (badge: "OFFICIAL" blue or "CUSTOM" slate)
- **Official URL** (clickable, opens in new tab)
- **Source type** (HTML page, PDF primary, Playwright-required, API)
- **Category** (financial_regulator, central_bank, aml, legal_acts, etc.)
- **Tier** (P0 / P1 / P2 — internal priority classification)
- **Check frequency** (Daily / Weekly / Manual)
- **Last checked** (timestamp, human-readable "2 hours ago")
- **Extraction quality** (GOOD / MEDIUM / THIN / FAILED badge)
- **Current normalized hash** (first 8 chars, monospace)
- **Latest status** (FIRST_SEEN / UNCHANGED / CHANGED / FAILED / QUALITY_DROP)
- **Proof readiness** (COMPLETE / INCOMPLETE / NOT_APPLICABLE)
- **Next check** (scheduled timestamp)
- **Known limitations** (inline text — e.g., "Playwright required", "PDF primary")

**Actions per source card:** View latest run | View evidence history | View diff (if CHANGED) | Pause monitoring | Edit settings (custom sources only)

---

## SECTION 9 — USER-ADDED CUSTOM SOURCES

### Feature Name: "Custom Source Monitoring"

### Allowed Source Types:
- Publicly accessible official regulatory websites (HTML pages)
- Publicly accessible official PDF documents
- Official government portals with stable URLs
- Official regulatory gazette pages
- Official central bank or financial regulator announcement pages

### Not Allowed Sources:
- Social media platforms (Twitter/X, LinkedIn, Telegram public channels)
- News aggregators (Reuters, Bloomberg, Arab News)
- Login-gated resources requiring username/password
- Sources requiring CAPTCHA
- Sources with robots.txt disallowing crawling (unless explicitly permitted by regulator)
- Non-official commentary or analysis sites
- Sources returning dynamic API results without stable URL patterns

### Add Source Form

**Required fields:**
- Source URL (HTTPS only, must be an official domain)
- Source name (what to call this source internally)
- Regulator or authority name
- Jurisdiction (dropdown)
- Category (dropdown: central_bank, financial_regulator, aml, legal_acts, legal_database, finance_ministry, company_registry, other)

**Optional advanced fields:**
- Monitoring frequency (daily / weekly — default: weekly)
- Extraction type preference (auto-detect / HTML only / PDF only / Playwright fallback)
- Custom notes or tags
- Alert threshold (notify on any change / notify only on HIGH risk / notify on MEDIUM or HIGH)

**Legal checkbox (required):**
"I confirm that this URL is a publicly accessible official regulatory source and that I have the right to monitor it for compliance review purposes. I understand that StatuteProof's monitoring of this source is subject to source availability, extraction quality, and access limitations. I understand that StatuteProof does not guarantee that all changes to this source will be detected. [Required checkbox]"

### 5-Step Add-Source Flow

**Step 1 — URL Entry**
User enters URL. Basic validation: HTTPS, valid domain format, not in blocked domain list.
If invalid: "This does not appear to be a valid HTTPS URL. Custom source monitoring requires a publicly accessible official source URL."

**Step 2 — Preview Fetch (Test Fetch)**
StatuteProof fetches the URL using the standard extraction pipeline. User sees: HTTP status code, extracted character count, extraction quality rating (GOOD/MEDIUM/THIN/FAILED), sample extracted text (first 500 chars, truncated). PDF links discovered count shown if PDF-primary source.
If FAILED: "We could not extract content from this URL. Common reasons: the page requires JavaScript rendering, the content is behind a login, the source has a robots.txt restriction, or the server is blocking automated requests. You can proceed with THIN quality (monitoring may miss some changes) or skip this source."
If THIN: "Extraction quality is LOW for this URL. This usually means the page is JavaScript-heavy or has limited text content. Monitoring may be less reliable. Proceed with caution and disclose this limitation."
If GOOD or MEDIUM: "Extraction successful. [N] characters extracted. This source appears suitable for monitoring."

**Step 3 — Quality Check**
Display extraction quality details: chars extracted, PDF count if applicable, recommended extraction method, known limitations. User confirms or cancels.

**Step 4 — Monitoring Settings**
User sets: source name (editable), category, jurisdiction, monitoring frequency, alert threshold, notes. Review legal acknowledgement checkbox.

**Step 5 — Save and Activate**
Source saved to database with status: TEST_PASSED or TEST_FAILED depending on Step 2 result. User sees confirmation: "Custom source added. First monitoring run will complete within 24 hours. Source status will update from DRAFT to ACTIVE after the first successful run." If test failed: "Source added with NEEDS_REVIEW status. First run will attempt monitoring; if quality remains below threshold, source status will be set to QUALITY_DROP and you will be notified."

### Custom Source Statuses

| Status | Meaning |
|--------|---------|
| DRAFT | Added but not yet run |
| TEST_PASSED | Initial fetch succeeded with GOOD or MEDIUM quality |
| TEST_FAILED | Initial fetch failed or returned THIN/FAILED quality |
| ACTIVE | Running successfully, quality acceptable |
| PAUSED | Manually paused by user |
| NEEDS_REVIEW | Quality dropped or fetch failed after a period of success |
| QUALITY_DROP | Extraction quality below threshold — may be missing changes |
| ARCHIVED | Removed from active monitoring, history preserved |

### Validation Rules

- URL must be HTTPS
- URL must resolve (HTTP 200 or successful Playwright render)
- URL must not be in the blocked domain list (social media, news aggregators)
- Extraction must return at least 1 character (FAILED status = source cannot be used)
- Maximum 10 custom sources per organization on Founding Pilot; 25 on VASP Pack; 50 on Consultant Pack

### Error Messages

- "This URL is not a valid HTTPS URL. Please enter the full URL including https://"
- "We could not reach this URL. The server may be down, geo-restricted, or blocking automated access."
- "This domain is not permitted for custom source monitoring. Custom sources must be official regulatory, government, or financial authority domains."
- "Extraction returned 0 characters. This source cannot be monitored at this time."
- "You have reached the custom source limit for your plan. Upgrade to add more custom sources."

### DB Model for Custom Sources

```
custom_sources:
  id (int, primary key)
  org_id (int, FK organizations)
  created_by_user_id (int, FK users)
  source_name (varchar 200)
  regulator_name (varchar 200)
  official_url (text)
  jurisdiction (varchar 5)
  category (varchar 50)
  monitoring_frequency (varchar 20, default 'weekly')
  extraction_type (varchar 20, default 'auto')
  alert_threshold (varchar 20, default 'any_change')
  status (varchar 30, default 'DRAFT')
  test_result_chars (int, nullable)
  test_result_quality (varchar 20, nullable)
  test_result_timestamp (datetime, nullable)
  legal_ack_accepted (bool, default false)
  legal_ack_timestamp (datetime, nullable)
  notes (text, nullable)
  created_at (datetime)
  updated_at (datetime)
  paused_at (datetime, nullable)
  last_run_at (datetime, nullable)
  last_change_status (varchar 30, nullable)
```

### API Endpoints for Custom Sources

- `POST /api/v1/custom-sources/test` — test a URL (no DB write), return fetch result
- `POST /api/v1/custom-sources` — save a custom source (requires legal_ack=true)
- `GET /api/v1/custom-sources` — list org's custom sources
- `GET /api/v1/custom-sources/:id` — get source detail
- `PATCH /api/v1/custom-sources/:id` — update settings
- `POST /api/v1/custom-sources/:id/pause` — pause monitoring
- `POST /api/v1/custom-sources/:id/resume` — resume monitoring
- `DELETE /api/v1/custom-sources/:id` — archive (not hard delete)

### Safety Checks (Backend)

1. URL domain checked against blocklist before fetch
2. robots.txt checked — blocked if crawling disallowed (unless admin override)
3. Rate limit: max 3 test fetches per 10 minutes per organization
4. Playwright usage: only if HTML extraction returns < 500 chars (prevent abuse)
5. Custom sources cannot be added with legal_ack = false

### Legal Disclaimer (shown in-app and in export)

"Custom source monitoring is provided for information purposes only. StatuteProof does not guarantee that all changes to custom sources will be detected. Custom source monitoring may be affected by website changes, access restrictions, extraction limitations, and scheduling. Custom sources are not independently verified as official regulatory sources by StatuteProof. Users are responsible for confirming that any monitored source is an appropriate and authorized official source for their compliance purposes. Not legal advice."

---

## SECTION 10 — EVIDENCE RECORD PAGE

### Header Fields

- Evidence Record ID (e.g., EVR-2026-0610-VARA-ENF-001)
- Source name and regulator
- Official URL (clickable)
- Detection timestamp (UTC)
- Change status (FIRST_SEEN / CHANGED / UNCHANGED / FAILED)
- Risk level badge
- Evidence completeness status (COMPLETE / INCOMPLETE — brief cannot be issued if INCOMPLETE)

### Evidence Details

- Raw snapshot path and character count
- Normalized text character count
- Normalization method (whitespace/encoding/formatting)
- SHA-256 hash of raw text
- SHA-256 hash of normalized text
- PDF links discovered (count + list of URLs)
- PDF text hash if extracted
- Extraction method (HTML / PDF / Playwright)
- Extraction quality (GOOD / MEDIUM / THIN / FAILED)
- Diff available: YES/NO (with link if available)
- Snapshot file paths (for audit trail)

### Review Panel

- Review status (DRAFT / APPROVED_FOR_WEEKLY / APPROVED_FOR_URGENT / REJECTED / NEEDS_REVIEW)
- Reviewer name and timestamp (if reviewed)
- Review note (free text from reviewer)
- Send decision (HOLD / WEEKLY_BRIEF_ONLY / READY_FOR_URGENT)

### Actions

- View diff
- Approve for weekly brief
- Approve for urgent delivery
- Reject (with required note)
- Flag for source adapter review
- Export evidence record (JSON / PDF)
- Copy evidence record link

### Empty/Error States

- "No evidence records yet. Your first monitoring run will complete within 24 hours."
- "Evidence record is incomplete. Diff quality is insufficient for brief generation. Human review required before this alert can proceed."
- "Source fetch failed. Evidence record shows FAILED status. Check source availability on the Sources page."

### Legal-Safety Note

All evidence record pages must include: "This evidence record documents an automated source monitoring event. It does not constitute legal advice, regulatory guidance, or a compliance assessment. Verify this record against the official source before taking any action."

---

## SECTION 11 — DIFF VIEWER

### Display

- Source name, official URL, detection timestamp shown in header
- Old text pane (left, labeled "Previous snapshot — [timestamp]")
- New text pane (right, labeled "Current snapshot — [timestamp]")
- Side-by-side view default; unified view toggle available
- Added text: highlighted green background (#22C55E, low opacity)
- Removed text: highlighted red background (#EF4444, low opacity)
- Unchanged context: normal text, dimmed if context-only

### Controls

- Toggle: side-by-side / unified view
- Toggle: show/hide context lines (default 3 lines of context around changes)
- Section navigation: jump to each changed block
- Export: copy diff as markdown, download diff file
- "View in official source" button (opens official URL in new tab)

### Quality Warnings

If diff quality is flagged as problematic:
- "This diff contains broad content changes that may reflect dynamic page content or aggregated counter updates rather than a discrete regulatory text change. Review the official source before acting on this alert."
- "Extraction quality dropped below reliable threshold. This diff may not accurately represent a regulatory text change."
- "This source requires a custom adapter for item-level monitoring. Broad aggregate-level changes are not suitable for direct customer alerts."

### No AI Legal Conclusions

The diff viewer must never:
- State "this change requires you to update your compliance program"
- State "this change imposes new obligations"
- State "you must act on this by [date]"
- Use language that implies legal interpretation

The diff viewer shows what changed in the source text. What that change means for your compliance is for your legal team to determine.

---

## SECTION 12 — RISK ALERT PAGE

### Risk Levels

| Level | Color | Meaning |
|-------|-------|---------|
| LOW | Grey/Blue | Informational change — minor updates, formatting, general notices |
| MEDIUM | Amber (#F59E0B) | Substantive change — framework updates, new guidance, reporting requirements |
| HIGH | Red (#EF4444) | Significant change — new obligations, licensing changes, AML/CFT requirements, enforcement notices |

### Risk Score Breakdown

Display: "Risk level: HIGH (score: 78/100)"
Breakdown panel (expandable):
- Change type: e.g., "RULEBOOK_UPDATE" 
- Obligation language detected: YES/NO
- Deadline/effective date language: YES/NO
- Penalty/fine language: YES/NO
- Licensing/registration language: YES/NO
- AML/CFT framework reference: YES/NO
- Confidence: HIGH / MEDIUM / LOW

### Affected Entities

Text field from alert draft: e.g., "VASP licence holders, custody service providers, VA broker dealers"
Always labeled: "Affected entity categories (rule-based classification — verify against official source)"

### Human Review Triggers

Alert requires human review before delivery if ANY of:
- Risk level is HIGH
- Confidence is LOW
- Diff quality is INCOMPLETE or UNKNOWN
- Evidence record is INCOMPLETE
- Source requires adapter (UAE Legislation Portal, SCA, etc.)
- Change type is UNKNOWN

### Buttons

- "Review evidence record" (primary)
- "View diff" (primary)
- "Approve for weekly brief" (secondary)
- "Approve for urgent delivery" (secondary, disabled if HIGH risk without explicit unlock)
- "Reject alert" (secondary)
- "Escalate for legal review" (secondary)

### Legal Language

Use "Suggested review steps" — not "required actions" or "legal actions required."
Use "This change may require review of your compliance documentation" — not "you must update your policies."
Use "Consult qualified legal or compliance counsel" — not "contact your regulator immediately."

---

## SECTION 13 — BRIEFS PAGE

### Brief Types

1. **Weekly Monitoring Brief** — generated weekly from approved CHANGED alerts for a given client profile
2. **Urgent Alert Brief** — generated for HIGH-risk approved alerts requiring immediate client awareness
3. **Source Readiness Brief** — generated from a source readiness review run (public or client-specific)

### Brief States

| State | Meaning | User action |
|-------|---------|-------------|
| DRAFT | Generated, not reviewed | Start review |
| NEEDS_REVIEW | Flagged for human review before delivery | Assign reviewer |
| APPROVED | Human review complete, approved for delivery | Export or send |
| EXPORTED | Brief exported or sent to client | View export log |
| ARCHIVED | No longer active — historical record | View only |

### Required Fields per Brief

- Brief ID
- Client profile / organization
- Brief type (weekly / urgent / readiness)
- Monitoring period (from / to dates)
- Sources monitored (list with last-run status)
- Alerts included (list with evidence record IDs)
- Brief text (markdown + HTML)
- Reviewer name and timestamp
- Approval status
- Full disclaimer (mandatory — brief cannot be marked APPROVED without it)
- Evidence record IDs for each included alert

### Actions

- View brief
- Download PDF
- Download Markdown
- Send to email (after approval only)
- Copy brief text
- Archive brief
- View included evidence records

### Gates (Non-Negotiable Rules)

1. **No brief delivered to customer without review** — Brief must be in APPROVED state
2. **No HIGH-risk brief delivered without explicit human review** — System blocks delivery if any included alert is HIGH risk and has not been individually reviewed
3. **No brief without at least one complete evidence record** — Brief with zero complete evidence records cannot be generated
4. **Disclaimer is mandatory** — Brief export must include full disclaimer; disclaimer cannot be removed or hidden

### Disclaimer (mandatory on every brief export)

"StatuteProof reports are generated from monitored official-source records and are provided for information and compliance review support only. StatuteProof reports do not constitute legal advice, regulatory advice, compliance certification, or a legal opinion. StatuteProof does not replace qualified legal counsel, compliance professionals, MLROs, or other professional advisers. StatuteProof does not guarantee compliance, prevent fines, or certify that all regulatory updates have been captured. Source monitoring may be affected by publication delays, website changes, PDF formatting, access limits, or source structure changes. Users should verify official source material directly and review evidence records, hashes, timestamps, and diffs before relying on a report. Users should consult qualified legal or compliance professionals before making regulatory, filing, operational, or customer decisions based on a report."

---

## SECTION 14 — SOURCE READINESS REVIEW FLOW

### Public CTA

"Request a free UAE source readiness review"
Appears on: homepage hero, homepage CTA section, source coverage page, pricing page, onboarding step 5.

### Public Form Fields (Unauthenticated)

- First name (required)
- Last name (required)
- Work email (required, validated)
- Company name (required)
- Job title (required)
- Company type (required — VASP, Fintech/Payment, Bank, DFSA firm, ADGM firm, Consultancy, Other)
- Primary regulator(s) of interest (multi-select: VARA, CBUAE, DFSA, ADGM FSRA, UAE FIU, Other)
- Questions or specific sources of interest (optional, text area)
- I understand this review is not legal advice and not a compliance assessment [required checkbox]

### Logged-in Version

Pre-populates: name, email, company. Shows current source configuration. Allows requesting a re-run of the readiness review for their specific source pack.

### Email: Readiness Review Received (auto-reply)

**Subject:** "Your StatuteProof UAE source readiness review request — received"
**Body:** "Thank you for requesting a UAE source readiness review from StatuteProof. We have received your request and will complete the review within 2-3 business days. You will receive the readiness report by email at [email address]. The report will show which UAE regulatory sources are currently active, which have access limitations, and which are not accessible from outside the UAE. This review is for information purposes only and does not constitute legal advice or a compliance assessment. If you have questions in the meantime, reply to this email."

### Follow-Up Email (on completion)

**Subject:** "Your UAE source readiness review is ready — StatuteProof"
**Body:** Review report attached/linked. Full disclaimer included. CTA: "If you'd like to discuss the report or explore a pilot, reply to this email."

### Dashboard Integration (logged-in users)

Source readiness review results visible in the Sources page as a "Readiness Report" tab. Shows: source status per source, extraction quality, limitations, pilot verdict (FREE_CHECK_READY / PILOT_READY / NEEDS_MORE_WORK).

### CRM Fields

For each readiness review request:
- Timestamp
- Contact details (name, email, company, title, company type)
- Source interests (array)
- Pilot interest flag
- Review completion date
- Follow-up status
- Notes

---

## SECTION 15 — PRICING / PILOT PAGE

### Tier 1: Free Source Readiness Review

**Price:** Free, one-time  
**What's included:**
- Automated test of up to 9 UAE official sources relevant to your licence type
- Written readiness report showing: source status (active/limited/blocked), extraction quality, known limitations
- Pilot recommendation (ready / needs work / specific gaps identified)
- Delivery by email within 2-3 business days
- One follow-up call (optional, if requested)

**What's not included:**
- Ongoing monitoring
- Change detection
- Evidence records
- Weekly briefs
- Access to the authenticated dashboard

**CTAs:** "Request free source readiness review" → /readiness-review form

**Legal note:** Free source readiness review is not legal advice and not a compliance assessment.

---

### Tier 2: Founding Pilot

**Price:** $299-499/month (manual invoice, cancel anytime during pilot)  
**Target:** Small UAE compliance teams who want to test the product before committing to a full pack  
**What's included:**
- Up to 5 monitored UAE official sources (from the standard UAE pack)
- Weekly monitoring brief (human-reviewed)
- Evidence records with SHA-256 hashes and diffs for all CHANGED events
- Source status dashboard (read-only)
- 2 user seats
- Email support
- Monthly check-in call

**What's not included:**
- Custom sources
- Multi-client management
- API access
- Webhook integration
- More than 5 sources without upgrade
- Automatic alert delivery (weekly brief only, no urgent alerts)

**CTAs:** "Request founding pilot" → contact form

**Pricing note:** Founding pilot pricing is introductory and may change after pilot. No automatic renewal without explicit agreement. Manual invoicing — no credit card required to start.

---

### Tier 3: UAE VASP Pack

**Price:** $499-999/month  
**Target:** VARA-licensed VASPs, DFSA/ADGM firms, payment institutions  
**What's included:**
- Up to 13 monitored UAE official sources (full UAE pack)
- Weekly monitoring brief + urgent alert capability (with human review gate)
- Full evidence records with diff viewer
- Custom source monitoring (up to 5 custom sources)
- 5 user seats with role management
- Slack/email alert delivery (post-review)
- Priority email support
- Quarterly review call

**What's not included:**
- Multi-client management (single organization)
- API/webhook for enterprise integrations
- White-label brief export
- SCA or FTA monitoring (currently not accessible from outside UAE)

**CTAs:** "Request UAE VASP Pack" → contact form

---

### Tier 4: Compliance Consultant Pack

**Price:** $999-2000/month  
**Target:** Compliance consultants and advisories serving multiple UAE-regulated clients  
**What's included:**
- Up to 13 UAE official sources + 25 custom sources
- Multi-client workspace (up to 5 client profiles)
- Per-client monitoring configuration and brief delivery
- Weekly briefs per client with separate evidence record trails
- White-label brief export (remove StatuteProof branding for client delivery — note: disclaimer is mandatory and cannot be removed)
- 10 user seats
- API access (read-only evidence records and alert feed)
- Priority email + phone support
- Monthly strategy call

**What's not included:**
- More than 5 client profiles without custom pricing
- Legal interpretation services
- Regulatory advice
- Compliance certification or attestation

**CTAs:** "Request consultant pack" → contact form

---

**Important: No fake logos, no invented customer counts, no testimonials from customers who do not exist.**

If pilot customers exist, their logos or quotes may be added with their explicit written permission.

---

## SECTION 16 — TEAM / ORGANIZATION / SETTINGS

### Settings Pages

1. **Organization Profile** — company name, company type, jurisdiction, time zone, logo upload
2. **Team** — user list with roles, invite new users, change roles, remove users
3. **Sources** — view and manage configured source packs, custom sources, monitoring frequency settings
4. **Notifications** — notification channels (email, Slack, webhook), notification preferences per event type
5. **Billing** — plan information, manual invoice history, upgrade/downgrade request, cancellation
6. **Security** — password change, session management (view active sessions, revoke), 2FA setup (future feature)
7. **API Access** — API key management (on plans with API access)
8. **Audit Log** — organization-level activity log (who approved what, when, evidence record IDs)

### Invite Flow

1. Admin/Owner goes to Settings > Team > Invite User
2. Enters: email address, role assignment
3. System sends invite email (see Section 22)
4. Invitee clicks link → registration form pre-filled
5. Invitee joins org on completion

### Notification Channels

- Email (required, always active)
- Slack (optional, requires webhook URL)
- Generic webhook (optional, POST to custom URL, JSON payload)

### Notification Preferences

| Event | Email | Slack | Webhook |
|-------|-------|-------|---------|
| Source status changed | Configurable | Configurable | Configurable |
| New CHANGED alert | Configurable | Configurable | Configurable |
| HIGH risk alert | Configurable | Configurable | Configurable |
| Brief ready for review | Configurable | Configurable | Configurable |
| Brief approved | Configurable | Configurable | Configurable |
| Source extraction quality drop | Configurable | Configurable | Configurable |
| Source fetch failed | Configurable | Configurable | Configurable |
| Weekly monitoring run complete | Configurable | Configurable | Configurable |

---

## SECTION 17 — BILLING AND SUBSCRIPTION

### MVP: Manual Invoicing

At MVP, billing is handled manually:
- No Stripe integration at MVP
- Monthly invoice sent by email at start of month
- Bank transfer or card payment accepted
- Cancel anytime policy: cancel by end of month, no next invoice
- No automatic renewal without explicit agreement

### Account Limits Per Tier

| Limit | Founding Pilot | UAE VASP Pack | Consultant Pack |
|-------|----------------|---------------|-----------------|
| Monitored sources | 5 | 13 | 13 + 25 custom |
| User seats | 2 | 5 | 10 |
| Client profiles | 1 | 1 | 5 |
| API access | No | No | Yes (read-only) |
| Custom sources | 0 | 5 | 25 |
| Brief history | 3 months | 12 months | 24 months |

### Future: Stripe Integration

Future billing via Stripe:
- Monthly subscription with proration
- Self-serve plan upgrade/downgrade
- Card payment with invoice history
- Failed payment handling with grace period

---

## SECTION 18 — BACKEND DATA MODEL

### User

**Purpose:** Individual account holder  
**Fields:** id, email, password_hash, first_name, last_name, job_title, email_verified (bool), email_verification_token, password_reset_token, password_reset_expires, last_login, created_at, updated_at  
**Relationships:** belongs to many Organizations via Membership  
**Indexes:** email (unique), email_verification_token, password_reset_token  
**Security:** password_hash using bcrypt (min 12 rounds); tokens are single-use and expire

### Organization

**Purpose:** Multi-user workspace (company)  
**Fields:** id, name, company_type, jurisdiction, plan_id (FK SubscriptionPlan), created_at, updated_at, max_sources, max_users, max_custom_sources, max_client_profiles  
**Relationships:** has many Memberships, has many Sources, has many Alerts, has many Briefs  
**Indexes:** id

### Membership

**Purpose:** User-to-Organization relationship with role  
**Fields:** id, user_id (FK User), org_id (FK Organization), role (enum: owner/admin/compliance_user/reviewer/auditor), invited_by_user_id, invite_accepted_at, created_at  
**Indexes:** (user_id, org_id) unique, org_id + role for permission queries

### Source

**Purpose:** A monitored source — either from the official pack or custom-added  
**Fields:** id, org_id (FK Organization), source_name, regulator_name, official_url, jurisdiction, category, source_type (official/custom), tier (P0/P1/P2), monitoring_frequency, extraction_type, alert_threshold, status (enum: ACTIVE/PAUSED/FAILED/QUALITY_DROP/ARCHIVED/DRAFT), is_official_pack (bool), legal_ack (bool), legal_ack_timestamp, notes, created_at, updated_at, last_run_at, last_change_status  
**Status Enums:** ACTIVE, PAUSED, FAILED, QUALITY_DROP, ARCHIVED, DRAFT, TEST_PASSED, TEST_FAILED, NEEDS_REVIEW  
**Indexes:** org_id + status, org_id + jurisdiction, official_url

### SourceRun

**Purpose:** One scheduled monitoring run of one Source  
**Fields:** id, source_id (FK Source), run_id (varchar — composite run identifier), run_timestamp_utc, change_status (enum), extraction_method, raw_chars, normalized_chars, raw_hash (sha256), normalized_hash (sha256), pdf_links_count, pdf_extracted_chars, pdf_text_hash, extraction_quality (GOOD/MEDIUM/THIN/FAILED), snapshot_path, normalized_snapshot_path, pdf_snapshot_path, diff_available (bool), proof_available (bool), error (text), limitations_notes (text), created_at  
**Indexes:** source_id + run_timestamp_utc, source_id + change_status, run_id

### EvidenceRecord

**Purpose:** Formal evidence record for a detected change event  
**Fields:** id, org_id, source_id, source_run_id (FK SourceRun), evidence_record_id (human-readable slug), official_url, source_name, regulator_name, detection_timestamp_utc, change_status, previous_hash, current_hash, previous_snapshot_path, current_snapshot_path, diff_path (JSON), diff_md_path, proof_block_path, extraction_method, extraction_quality, completeness_status (COMPLETE/INCOMPLETE), risk_level, risk_score, review_status, reviewer_user_id, reviewer_timestamp, reviewer_note, send_decision, created_at  
**Status Enums for completeness:** COMPLETE, INCOMPLETE  
**Indexes:** org_id + detection_timestamp, source_id, evidence_record_id (unique), review_status

### Diff

**Purpose:** Structured diff record for a CHANGED event  
**Fields:** id, evidence_record_id (FK EvidenceRecord), old_text (text), new_text (text), added_sections (JSON array of strings), removed_sections (JSON array of strings), changed_blocks_count, diff_quality (GOOD/INCOMPLETE/UNKNOWN), meaningful_change_detected (bool), diff_timestamp_utc, created_at  
**Indexes:** evidence_record_id

### Alert

**Purpose:** An alert generated from a CHANGED evidence event  
**Fields:** id, org_id, evidence_record_id (FK EvidenceRecord), alert_draft_id (varchar slug), source_name, regulator, change_type (RULEBOOK_UPDATE/CIRCULAR_UPDATE/GUIDANCE_UPDATE/AML_CFT/LICENSING/TAX/GENERAL_UPDATE/UNKNOWN), risk_level, risk_score, risk_rationale (text), confidence (HIGH/MEDIUM/LOW), changed_excerpts (JSON), affected_entities (text), suggested_review_steps (text), limitations (text), proof_block_path, review_status (enum), reviewer_user_id, reviewer_timestamp, reviewer_note, send_decision (enum), created_at, updated_at  
**Status Enums:** DRAFT, MANUAL_REVIEW_REQUIRED, APPROVED_FOR_WEEKLY, APPROVED_FOR_URGENT, REJECTED, NEEDS_SOURCE_ADAPTER, NEEDS_LEGAL_REVIEW  
**Send Decision Enums:** HOLD_FOR_REVIEW, DO_NOT_SEND, WEEKLY_BRIEF_ONLY, READY_FOR_URGENT_DELIVERY  
**Indexes:** org_id + review_status, org_id + risk_level, evidence_record_id

### Brief

**Purpose:** A weekly or urgent monitoring brief delivered to a client  
**Fields:** id, org_id, client_profile_id, brief_type (weekly/urgent/readiness), brief_period_from, brief_period_to, sources_monitored (JSON), alert_ids_included (JSON), brief_text_md (text), brief_text_html (text), disclaimer_included (bool — must be true), state (DRAFT/NEEDS_REVIEW/APPROVED/EXPORTED/ARCHIVED), reviewer_user_id, reviewer_timestamp, export_timestamp, export_format, created_at, updated_at  
**Indexes:** org_id + state, org_id + brief_period_from, client_profile_id

### Review

**Purpose:** Audit log of human review actions on alerts and briefs  
**Fields:** id, org_id, reviewer_user_id, object_type (alert/brief/evidence_record), object_id, action (approved_weekly/approved_urgent/rejected/flagged/needs_adapter/needs_legal_review), review_note (text, required for reject/flag), created_at  
**Indexes:** org_id + object_type + object_id, reviewer_user_id, created_at

### SourceReadinessReview

**Purpose:** A source readiness review request (public form or logged-in)  
**Fields:** id, requester_name, requester_email, requester_company, requester_title, company_type, regulators_of_interest (JSON), questions (text), status (pending/in_progress/complete/delivered), report_path, delivered_at, legal_ack_accepted (bool), created_at, org_id (nullable — null for public requests), user_id (nullable)  
**Indexes:** requester_email, status, created_at

### CustomSourceTest

**Purpose:** Record of a test-fetch attempt during custom source add flow  
**Fields:** id, org_id, user_id, test_url, http_status, raw_chars, extraction_quality, extraction_method, sample_text (first 500 chars), error (text), tested_at  
**Indexes:** org_id, tested_at

### NotificationPreference

**Purpose:** Per-organization notification settings  
**Fields:** id, org_id, event_type (varchar), email_enabled (bool), slack_enabled (bool), webhook_enabled (bool), email_recipients (JSON array), slack_webhook_url, custom_webhook_url, created_at, updated_at  
**Indexes:** org_id + event_type

### SubscriptionPlan

**Purpose:** Plan definitions and limits  
**Fields:** id, plan_name, plan_slug, monthly_price_usd, max_sources, max_custom_sources, max_users, max_client_profiles, api_access (bool), white_label (bool), created_at  
**Indexes:** plan_slug (unique)

---

## SECTION 19 — BACKEND API ENDPOINTS

### Auth Group

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| /api/v1/auth/register | POST | None | Register new user |
| /api/v1/auth/verify-email | POST | None | Verify email with token |
| /api/v1/auth/login | POST | None | Login, return JWT + refresh cookie |
| /api/v1/auth/refresh | POST | Refresh cookie | Refresh access token |
| /api/v1/auth/logout | POST | Access JWT | Logout, clear cookie |
| /api/v1/auth/forgot-password | POST | None | Request password reset |
| /api/v1/auth/reset-password | POST | None | Complete password reset |

**Validation:** register requires valid email format, password strength check; login has rate limiting (5 attempts/15 min per IP); all tokens are single-use and time-limited

### Organization Group

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| /api/v1/org | GET | Access JWT | Get org details |
| /api/v1/org | PATCH | Admin/Owner | Update org profile |
| /api/v1/org/members | GET | Access JWT | List org members |
| /api/v1/org/invite | POST | Admin/Owner | Invite user to org |
| /api/v1/org/members/:id/role | PATCH | Admin/Owner | Change member role |
| /api/v1/org/members/:id | DELETE | Admin/Owner | Remove member |

### Sources Group

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| /api/v1/sources | GET | Access JWT | List configured sources |
| /api/v1/sources/:id | GET | Access JWT | Source detail |
| /api/v1/sources/:id/runs | GET | Access JWT | Run history for source |
| /api/v1/sources/:id/pause | POST | Admin | Pause monitoring |
| /api/v1/sources/:id/resume | POST | Admin | Resume monitoring |

**Permissions:** Read = Compliance User, Reviewer, Admin, Owner. Write = Admin, Owner only.

### Custom Source Group

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| /api/v1/custom-sources/test | POST | Admin | Test URL fetch (no DB write) |
| /api/v1/custom-sources | POST | Admin | Create custom source |
| /api/v1/custom-sources | GET | Access JWT | List custom sources |
| /api/v1/custom-sources/:id | GET | Access JWT | Custom source detail |
| /api/v1/custom-sources/:id | PATCH | Admin | Update custom source |
| /api/v1/custom-sources/:id/pause | POST | Admin | Pause |
| /api/v1/custom-sources/:id/resume | POST | Admin | Resume |
| /api/v1/custom-sources/:id | DELETE | Admin | Archive |

**Dangerous actions:** POST /test is rate-limited. POST (create) requires legal_ack=true in body.

### Evidence Group

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| /api/v1/evidence | GET | Access JWT | List evidence records (filter: source, date, status) |
| /api/v1/evidence/:id | GET | Access JWT | Evidence record detail |
| /api/v1/evidence/:id/diff | GET | Access JWT | Diff for evidence record |
| /api/v1/evidence/:id/export | GET | Access JWT | Export as JSON or PDF |

### Alerts Group

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| /api/v1/alerts | GET | Access JWT | List alerts (filter: source, risk, review status) |
| /api/v1/alerts/:id | GET | Access JWT | Alert detail |
| /api/v1/alerts/:id/approve | POST | Reviewer/Admin | Approve alert |
| /api/v1/alerts/:id/reject | POST | Reviewer/Admin | Reject alert (note required) |
| /api/v1/alerts/:id/flag | POST | Reviewer/Admin | Flag for legal review |

**Dangerous actions:** approve urgent delivery of HIGH-risk alert requires force flag and review note.

### Briefs Group

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| /api/v1/briefs | GET | Access JWT | List briefs |
| /api/v1/briefs/:id | GET | Access JWT | Brief detail |
| /api/v1/briefs/:id/approve | POST | Reviewer/Admin | Approve brief |
| /api/v1/briefs/:id/export | GET | Access JWT | Export brief (md/pdf/html) |

**Gate:** Brief export returns error if disclaimer_included=false or if any included HIGH-risk alert lacks a review.

### Source Readiness Review Group

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| /api/v1/readiness-review | POST | None (public) | Submit readiness review request |
| /api/v1/readiness-review/:id | GET | Admin (internal) | Get review status |

### Billing Group (Future/Manual at MVP)

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| /api/v1/billing/plan | GET | Owner | Get current plan |
| /api/v1/billing/upgrade | POST | Owner | Request upgrade (creates support ticket at MVP) |

---

## SECTION 20 — FRONTEND ROUTES

### Public Routes

| Route | Purpose | Components | Loading | Empty | Error | Access |
|-------|---------|-----------|---------|-------|-------|--------|
| / | Homepage | Hero, AlertCard, Problem, HowItWorks, Coverage, EvidenceTrail, Pricing, FAQ, Footer | Immediate (static) | N/A | 500 page | Public |
| /how-it-works | Pipeline explanation | StepFlow, EvidenceExplainer, HumanReview, CTA | Immediate | N/A | 500 page | Public |
| /sources | Source coverage table | SourceCoverageTable, LimitationDisclosure | Immediate | N/A | 500 page | Public |
| /sample-brief | Sample brief display | SAMPLE label, AlertCard, DiffPreview, EvidenceRecord, Disclaimer | Immediate | N/A | 500 page | Public |
| /readiness-review | Readiness review form | ReadinessForm, WhatYouReceive, Timeline | Immediate | N/A | 500 page | Public |
| /pricing | Pricing tiers | PricingTable, FAQ, CTA | Immediate | N/A | 500 page | Public |
| /security | Security/trust page | SecurityDetails, EvidenceStorage | Immediate | N/A | 500 page | Public |
| /about | About/methodology | Methodology, Limitations, Contact | Immediate | N/A | 500 page | Public |
| /login | Login form | LoginForm | Immediate | N/A | Form errors | Public (redirect if authenticated) |
| /register | Registration form | RegisterForm | Immediate | N/A | Form errors | Public (redirect if authenticated) |
| /verify-email | Email verification | VerifyEmailStatus | Loading spinner | Error message | Error message | Public |
| /reset-password | Password reset | ResetPasswordForm | Immediate | N/A | Form errors | Public |
| /terms | Terms of Service | LegalDocument | Immediate | N/A | 500 page | Public |
| /privacy | Privacy Policy | LegalDocument | Immediate | N/A | 500 page | Public |
| /disclaimer | Disclaimer | LegalDocument | Immediate | N/A | 500 page | Public |

### App Routes (Authenticated)

| Route | Purpose | Required Data | Loading | Empty | Error | Access |
|-------|---------|--------------|---------|-------|-------|--------|
| /app | Dashboard | Sources, Alerts, Briefs counts | Spinner | Onboarding checklist | Error card | All authenticated |
| /app/sources | Source management | Source list | Table skeleton | "No sources configured" | Error card | All authenticated |
| /app/sources/:id | Source detail | Source, Run history | Spinner | N/A | 404 card | All authenticated |
| /app/alerts | Alerts feed | Alert list | Table skeleton | "No alerts yet" | Error card | All authenticated |
| /app/alerts/:id | Alert detail | Alert, Evidence, Diff | Spinner | N/A | 404 card | All authenticated |
| /app/evidence | Evidence records | Evidence list | Table skeleton | "No evidence records" | Error card | All authenticated |
| /app/evidence/:id | Evidence detail | Evidence, Diff | Spinner | N/A | 404 card | All authenticated |
| /app/diff/:evidenceId | Diff viewer | Diff data | Spinner | "No diff available" | Error card | All authenticated |
| /app/briefs | Briefs list | Briefs | Table skeleton | "No briefs yet" | Error card | All authenticated |
| /app/briefs/:id | Brief detail | Brief, Alerts | Spinner | N/A | 404 card | All authenticated |
| /app/review-queue | Review queue | Pending items | Table skeleton | "Review queue empty" | Error card | Reviewer, Admin, Owner |
| /app/settings | Settings overview | Org, User | Spinner | N/A | Error | Admin, Owner |
| /app/settings/team | Team management | Members | Table skeleton | "No team members" | Error | Admin, Owner |
| /app/settings/sources | Source settings | Sources | Table skeleton | N/A | Error | Admin, Owner |
| /app/settings/notifications | Notification prefs | Preferences | Spinner | N/A | Error | Admin, Owner |
| /app/settings/billing | Billing info | Plan | Spinner | N/A | Error | Owner only |
| /app/onboarding | Onboarding flow | None required | Immediate | N/A | Error | New users only |

---

## SECTION 21 — UI COMPONENT SYSTEM

**Design system:** Dark navy (#0B1426) base, white (#FFFFFF) primary text, slate (#8B9AB5) secondary text, green (#22C55E) for CHANGED status and CTAs, amber (#F59E0B) for warnings and MEDIUM risk, red (#EF4444) for errors and HIGH risk, blue (#3B82F6) for FIRST_SEEN and info states.

**Typography:** Inter for UI text. JetBrains Mono for hashes, code, and evidence IDs. Font sizes: base 16px body, 14px table text, 12px captions/labels.

**Design principles:** Premium B2B. Evidence-first visual language. Precision over decoration. No crypto hype. No neon. No gradient blobs. No rounded bubbly design. Tables and structured data are a feature, not something to hide.

### Public Components

| Component | Purpose | Props/Data | States | Legal-safety notes |
|-----------|---------|-----------|--------|-------------------|
| Hero | Homepage hero | Headline, subheadline, CTAs | Static | No overclaim language |
| SampleAlertCard | Displays a SAMPLE alert card | Source, status, hashes, diff info | SAMPLE label required | SAMPLE/FAKE label always visible |
| SourceCoverageTable | Lists monitored sources with status | Sources array | Loaded, empty | Limitation disclosure required |
| PricingTable | Tier comparison | Plan array | Static | No guarantee/prevent language |
| ReadinessForm | Public request form | Form fields | Default, loading, success, error | Legal ack checkbox required |
| Disclaimer | Short or full disclaimer text | variant (short/full) | Static | Cannot be toggled off |
| NavBar | Public site navigation | Links | Default, mobile | Login/register links |
| Footer | Site footer | Links, disclaimer | Static | Short disclaimer always in footer |

### App Components

| Component | Purpose | Props/Data | States | Legal-safety notes |
|-----------|---------|-----------|--------|-------------------|
| DashboardWidgets | 8 dashboard widgets | Counts, status summary | Loaded, loading, empty | N/A |
| AlertsTable | Alert feed table | Alerts array, filters | Loaded, loading, empty, error | Review status always shown |
| SourceStatusBadge | Status badge with color and tooltip | status (string) | 6 statuses (see section 7) | Tooltip explains meaning |
| RiskBadge | Risk level badge | risk_level (LOW/MEDIUM/HIGH) | 3 levels | Never "compliance certified" |
| EvidenceRecordDetail | Full evidence record display | EvidenceRecord | Loaded, incomplete warning | Legal note always shown |
| DiffViewer | Side-by-side or unified diff | old_text, new_text, diff_blocks | Loaded, no-diff, quality-warning | No AI legal conclusions |
| AlertDetailCard | Full alert display with review actions | Alert, EvidenceRecord | Loaded, review pending, approved | All review actions logged |
| BriefDetailView | Brief content with export | Brief, included alerts | Loaded, draft, approved | Disclaimer always shown |
| ReviewActions | Approve/reject/flag controls | Alert or Brief ID | Default, loading, success | Note required for rejection |
| SourceCard | Source detail in list/grid | Source, latest run | Active, paused, failed | Limitation text shown |
| OnboardingChecklist | Setup progress | Checklist items | Incomplete, complete | N/A |
| NotificationSettings | Notification prefs form | Preferences | Default, saving, saved | N/A |

---

## SECTION 22 — EMAILS AND NOTIFICATIONS

### Email 1: Email Verification

**Subject:** "Verify your StatuteProof account — action required"  
**Preview text:** "Click the link below to verify your email and complete registration."  
**Body:** "Thank you for registering with StatuteProof. Please verify your email address by clicking the link below. This link expires in 24 hours and can only be used once. If you did not register for StatuteProof, you can ignore this email."  
**CTA:** "Verify email address"  
**Disclaimer:** None required

### Email 2: Password Reset

**Subject:** "Reset your StatuteProof password"  
**Preview text:** "You requested a password reset. This link expires in 1 hour."  
**Body:** "We received a request to reset the password for your StatuteProof account. Click the link below to set a new password. This link expires in 1 hour and can only be used once. If you did not request a password reset, your account is secure and you can ignore this email."  
**CTA:** "Reset password"  
**Disclaimer:** None required

### Email 3: Team Invite

**Subject:** "[Name] has invited you to join [Organization] on StatuteProof"  
**Preview text:** "You've been invited to join the [Organization] compliance monitoring workspace."  
**Body:** "[Inviter Name] has invited you to join [Organization Name]'s StatuteProof account as a [Role]. StatuteProof is an official-source regulatory monitoring tool for UAE compliance teams. Click below to accept the invitation and set up your account. This invite expires in 72 hours."  
**CTA:** "Accept invitation"  
**Disclaimer:** None required

### Email 4: Source Readiness Review Received

**Subject:** "Your UAE source readiness review request — received"  
**Preview text:** "We'll complete your review within 2-3 business days."  
**Body:** "Thank you for requesting a UAE source readiness review from StatuteProof. We have received your request and will complete the review within 2-3 business days. You will receive the readiness report by email at [email]. The report will show which UAE regulatory sources are currently active, which have access limitations, and which are not accessible from outside the UAE. This review is for information purposes only and does not constitute legal advice or a compliance assessment. If you have any questions, reply to this email."  
**CTA:** None (informational)  
**Disclaimer:** "Not legal advice. For monitoring information only."

### Email 5: Source Test Passed

**Subject:** "Custom source test passed — [Source Name]"  
**Preview text:** "Your custom source extraction test returned good quality results."  
**Body:** "The extraction test for your custom source [Source Name] at [URL] passed with [GOOD/MEDIUM] quality. [N] characters were extracted. The source has been added to your monitoring configuration and will be included in your next scheduled run. If quality drops below threshold after activation, you will be notified. Not legal advice. For monitoring information only."  
**CTA:** "View source in dashboard"

### Email 6: Source Test Failed

**Subject:** "Custom source test failed — [Source Name]"  
**Preview text:** "We could not extract content from your custom source."  
**Body:** "The extraction test for your custom source [Source Name] at [URL] did not return usable content. Common reasons: the page requires JavaScript rendering that is not available, the content is behind a login, the source has a geo-restriction, or the server is blocking automated requests. The source has been added with NEEDS_REVIEW status. You can try again from the Sources page or contact us for assistance. Not legal advice."  
**CTA:** "View source in dashboard"

### Email 7: Weekly Brief Ready

**Subject:** "Your StatuteProof weekly monitoring brief is ready — [Period]"  
**Preview text:** "[N] reviewed updates. [N] sources monitored. Review and export."  
**Body:** "Your weekly monitoring brief for [Period Start] to [Period End] is ready for review. [N] regulatory updates were detected and reviewed during this period. [N] were approved for this brief. Sources monitored: [source list]. Log in to view, approve, and export the brief. Not legal advice. This brief is for information and compliance review support only."  
**CTA:** "View and export brief"  
**Disclaimer:** Short disclaimer appended

### Email 8: High-Risk Alert Needs Review

**Subject:** "HIGH RISK alert requires review — [Source Name]"  
**Preview text:** "A HIGH risk regulatory change was detected and requires human review before delivery."  
**Body:** "StatuteProof detected a HIGH risk change event on [Source Name] ([URL]) at [Timestamp UTC]. Risk level: HIGH. Change type: [type]. This alert is currently on HOLD FOR REVIEW and cannot be delivered until it has been reviewed and approved by a qualified member of your team. Log in to review the evidence record, view the diff, and take a review action. Not legal advice. Do not act on this alert without verifying the change against the official source and consulting your legal or compliance counsel."  
**CTA:** "Review alert"  
**Disclaimer:** Full disclaimer

### Email 9: Source Failed / Quality Drop

**Subject:** "Source monitoring issue — [Source Name] [FAILED/QUALITY_DROP]"  
**Preview text:** "We detected an issue with monitoring [Source Name]. No alerts will be generated until resolved."  
**Body:** "We detected a monitoring issue with [Source Name] ([URL]). Status: [FAILED/QUALITY_DROP]. Possible cause: the source website has changed structure, access has been restricted, or extraction quality has dropped below threshold. While this issue persists, changes to this source may not be detected. We are investigating. In the meantime, we recommend checking the official source directly. Log in for details. Not legal advice."  
**CTA:** "View source status"

### Email 10: Pilot Welcome

**Subject:** "Welcome to your StatuteProof pilot — next steps"  
**Preview text:** "Your monitoring has been configured. Here's what happens next."  
**Body:** "Welcome to StatuteProof. Your pilot is now active. Here is what happens next: 1) Your configured sources ([list]) will be checked within the next 24 hours. 2) Your first source readiness report will be ready within 2-3 business days. 3) When a change is detected, it goes through our evidence and review pipeline before reaching you. 4) You will receive a weekly brief every [day] covering the previous monitoring period. Important: StatuteProof reports are for information and compliance review support only. They do not constitute legal advice. You should verify any alert against the official source and consult qualified legal counsel before acting. Full disclaimer at [link]."  
**CTA:** "Log in to your dashboard"  
**Disclaimer:** Full disclaimer

---

## SECTION 23 — LEGAL SAFETY AND DISCLAIMERS

### Disclaimer 1: Standard Brief Disclaimer (Mandatory on all brief exports)

"StatuteProof reports are generated from monitored official-source records and are provided for information and compliance review support only. StatuteProof reports do not constitute legal advice, regulatory advice, compliance certification, or a legal opinion. StatuteProof does not replace qualified legal counsel, compliance professionals, MLROs, or other professional advisers. StatuteProof does not guarantee compliance, prevent fines, or certify that all regulatory updates have been captured. Source monitoring may be affected by publication delays, website changes, PDF formatting, access limits, or source structure changes. Users should verify official source material directly and review evidence records, hashes, timestamps, and diffs before relying on a report. Users should consult qualified legal or compliance professionals before making regulatory, filing, operational, or customer decisions based on a report."

**Where it appears:** Every brief export (PDF, Markdown, HTML), evidence record exports, sample brief page  
**When mandatory:** Cannot be removed from brief exports. Brief cannot be marked APPROVED if disclaimer is not included in the brief object.  
**What blocks user action if not accepted:** brief export blocked, brief cannot transition to APPROVED state

### Disclaimer 2: Short Website Disclaimer

"For monitoring information only. Not legal advice and not a guarantee of compliance."

**Where it appears:** Homepage footer, every email, outreach messages, below all CTAs  
**When mandatory:** Always present in footer

### Disclaimer 3: Custom Source Disclaimer

"Custom source monitoring is provided for information purposes only. StatuteProof does not guarantee that all changes to custom sources will be detected. Custom source monitoring may be affected by website changes, access restrictions, extraction limitations, and scheduling. Custom sources are not independently verified as official regulatory sources by StatuteProof. Users are responsible for confirming that any monitored source is an appropriate and authorized official source for their compliance purposes. Not legal advice."

**Where it appears:** Custom source onboarding step 4, custom source detail page, any export that includes custom source alerts  
**When mandatory:** Custom source creation requires explicit acknowledgement checkbox. Cannot be skipped.

### Disclaimer 4: Registration Acknowledgement

"I understand that StatuteProof reports are for information and compliance review support only and do not constitute legal advice, regulatory advice, or compliance certification."

**Where it appears:** Registration form (checkbox, required)  
**When mandatory:** Registration cannot complete without this checkbox checked. Stored in database with timestamp.  
**What blocks user action:** Registration form submission blocked if unchecked.

### Disclaimer 5: Sample/FAKE Label

"SAMPLE / FAKE — NOT REAL REGULATORY DATA"

**Where it appears:** Any sample brief, sample alert card, demo fixture output, onboarding sample content  
**When mandatory:** Always on any content that uses invented regulatory data  
**Form:** Visible badge/label, not hidden in small print. Must be near the top of the content, not only in the footer.

---

## SECTION 24 — TRUST / SECURITY / AUDITABILITY

### Trust Page Content (/security)

**What StatuteProof does to create auditable records:**

1. **Deterministic change detection:** Change detection is based on SHA-256 hashing of normalized text. The same source text will always produce the same hash. A change in the hash means the text changed. This is deterministic, not probabilistic.

2. **SHA-256 evidence snapshots:** Every monitoring run stores a SHA-256 hash of the normalized source text. Both the previous and current hashes are stored. You can reproduce the hash yourself by fetching the official source and applying the same normalization.

3. **Timestamped records:** Every source run, every evidence record, and every review action is timestamped in UTC. Timestamps are immutable once stored.

4. **Diff view:** Every CHANGED event includes a text-level diff showing exactly what was added, removed, or modified. The diff is based on normalized text to prevent false positives from whitespace formatting changes.

5. **Human review gate:** No alert or brief reaches a customer without explicit human review. The review log includes the reviewer identity, timestamp, action taken, and any notes.

6. **Source failure visibility:** When a source fetch fails or extraction quality drops, the failure is recorded and disclosed to the user. StatuteProof does not silently report UNCHANGED when extraction has failed.

7. **Limitations disclosure:** Known limitations per source (JavaScript-only pages, PDF-only sources, geo-restricted sources) are stored in the source record and shown in every relevant report and alert.

**What StatuteProof does NOT claim:**
- We do not claim SOC 2 certification (not yet certified)
- We do not claim complete UAE regulatory coverage
- We do not claim 100% change detection accuracy
- We do not claim that our risk classification is legally authoritative
- We are not affiliated with, endorsed by, or an official partner of any UAE regulatory authority

**Infrastructure (honest statement):**
StatuteProof runs on standard VPS infrastructure. Data is stored on the server in a SQLite database and JSONL run history files. Snapshots are stored on disk. Production infrastructure is behind nginx with TLS. Backups are manual at current scale. Enterprise cloud infrastructure (multi-region, automated backup, disaster recovery) is planned for commercial-scale deployments.

---

## SECTION 25 — MVP IMPLEMENTATION PLAN

### Phase 0 — Foundation Audit (Day 1-2)

**Goal:** Establish what exists, what is real, what is mock, before writing a line of new code.  
**Files involved:** product/regradar/app/*.py, web/src/components/*, web/src/App.jsx  
**Backend work:** None — audit only  
**Frontend work:** None — audit only  
**Acceptance criteria:** Written inventory of: (a) what backend API endpoints are real vs stubbed, (b) which frontend components use real API data vs mock data, (c) which source runs produce real evidence records, (d) which email flows are implemented  
**What not to do:** Do not start new features before the audit is complete

### Phase 1 — Auth + Organization Model (Days 3-7)

**Goal:** Real multi-user auth with organizations, roles, and invites. Replace single-user JWT system.  
**Files involved:** product/regradar/app/auth.py (extend), new: users table, organizations table, memberships table in DB  
**Backend work:** User/Org/Membership DB schema, registration endpoint with email verification, invite flow, role-based permission check on all endpoints  
**Frontend work:** Register form with all required fields, login, email verification page, onboarding step 1  
**Risks:** Password reset email requires working SMTP; use transactional email service (Resend, Postmark, or SendGrid) — not raw SMTP  
**Acceptance criteria:** User can register, verify email, log in, create an org, invite a team member, member joins with assigned role  
**What not to do:** Do not implement SSO, OAuth, or magic link at this phase

### Phase 2 — Source Configuration UI (Days 8-14)

**Goal:** Admin users can view, configure, pause, and add custom sources from the dashboard  
**Files involved:** New API endpoints for sources, web/src/components/SourceCard, new SourcesPage  
**Backend work:** Sources API (list, detail, pause, resume), custom sources API (test, create, list, update, archive), rate-limiting on test endpoint  
**Frontend work:** SourcesPage, SourceCard component, AddCustomSourceFlow (5 steps), extraction quality display  
**Risks:** Custom source test fetch must be sandboxed — prevent SSRF by blocking internal IP ranges, localhost, and known blocked domains  
**Acceptance criteria:** Admin can view all configured sources, pause/resume a source, add a custom source with test-fetch preview, see extraction quality  
**What not to do:** Do not allow monitoring of internal IP addresses; do not allow sources without legal_ack=true

### Phase 3 — Evidence Record and Diff UI (Days 15-21)

**Goal:** Authenticated users can view evidence records, diffs, and alert detail pages  
**Files involved:** New EvidenceRecord API endpoints, new DiffViewer component, AlertDetailCard  
**Backend work:** Evidence records table, diff storage, API endpoints for evidence list/detail/diff  
**Frontend work:** EvidenceRecordsPage, EvidenceDetailPage, DiffViewer component, AlertsTable  
**Risks:** Diff quality warning logic must be visible — do not show a clean diff for a low-quality change without a warning  
**Acceptance criteria:** User can navigate to an evidence record, see the full details with hashes, view the diff with added/removed highlighting, see quality warnings if applicable  
**What not to do:** Do not add AI legal interpretation to diff viewer; do not hide low-quality diff warnings

### Phase 4 — Human Review Workflow (Days 22-28)

**Goal:** Reviewer can approve/reject/flag alerts and briefs; gate on brief delivery  
**Files involved:** Review API endpoints, ReviewQueue page, ReviewActions component  
**Backend work:** Alert review API (approve_weekly, approve_urgent, reject, flag), Review audit log table, Brief approval gate enforcement  
**Frontend work:** ReviewQueue page, ReviewActions component on alert/evidence pages, status transitions visible  
**Risks:** Brief delivery gate must be enforced at API level, not just UI level — brief export endpoint must check approval status server-side  
**Acceptance criteria:** Reviewer can approve/reject an alert; approved alert appears in Review Queue as complete; unapproved HIGH-risk alert cannot be exported; brief without complete evidence records cannot be marked approved  
**What not to do:** Do not allow brief delivery without server-side approval check; do not allow force-approve without explicit reviewer note

### Phase 5 — Briefs and Exports (Days 29-35)

**Goal:** Weekly brief generation and export (PDF/Markdown) with mandatory disclaimer  
**Files involved:** Brief generation module, brief export API, BriefDetailView, export button  
**Backend work:** Brief object with included alert IDs, brief generation logic, PDF export (fpdf2 or WeasyPrint), Markdown export  
**Frontend work:** BriefsPage, BriefDetailView, export buttons, disclaimer always rendered in preview  
**Risks:** PDF generation can be slow — use async generation or streaming response  
**Acceptance criteria:** Weekly brief generated from approved alerts, includes all required fields and disclaimer, exports to PDF with disclaimer, Markdown export correct  
**What not to do:** Do not allow disclaimer removal from exports; do not include unapproved alerts in exported briefs

### Phase 6 — Email Notifications and Homepage Polish (Days 36-42)

**Goal:** Working transactional emails for all 10 templates; homepage aligned to spec  
**Files involved:** Email templates, notification service, homepage components  
**Backend work:** Transactional email integration (Resend recommended), notification preferences storage, webhook notification delivery  
**Frontend work:** Homepage component updates per Section 4 spec, footer disclaimer update, sample alert card in hero  
**Risks:** Email deliverability requires proper SPF/DKIM setup on the sending domain  
**Acceptance criteria:** All 10 email templates send correctly with proper disclaimer text; homepage hero matches spec with SAMPLE alert card; source coverage table is accurate  
**What not to do:** Do not send marketing emails without explicit opt-in; do not send HIGH-risk alerts by email without prior review

---

## SECTION 26 — WEBSITE GAP AUDIT (TABLE)

See `docs/statuteproof-website-gap-audit.md` for the full gap audit table.

Summary of key gaps identified during inspection of statuteproof.com on 2026-06-12:

| Feature | Current Status | Priority |
|---------|----------------|----------|
| Homepage hero with sample alert card | Minimal — headline only visible | P0 |
| Source readiness review CTA | Present in landing, not prominent | P0 |
| Registration with org model | Single-user JWT only | P0 |
| Multi-user onboarding | Not implemented | P0 |
| Evidence record page (authenticated) | Mock/demo data only | P1 |
| Diff viewer (authenticated) | DiffViewer.jsx exists but wired to mock | P1 |
| Brief export with mandatory disclaimer | Weekly brief generator exists in CLI only | P1 |
| Custom source add flow | Not implemented in UI | P1 |
| Pricing page with 4 tiers | Pricing component exists, prices updated recently | P2 |
| Legal disclaimer on all brief exports | Disclaimer exists in CLI briefs, not in web export | P0 |

---

## SECTION 27 — SINGLE BEST NEXT CODING TASK

**Task:** Wire real source status data to the authenticated dashboard and Sources page — replacing mock data with live API calls.

**Why first:**
1. Everything else (evidence records, diff viewer, briefs) is useless to show a pilot customer if the source status is mocked
2. The backend already has `/api/v1/sources` implemented (router.py has GET /regulations)
3. The regradar pipeline has real run history at `data/source_runs/source_runs.jsonl`
4. The frontend `DashboardPreview.jsx` uses mock data — connecting real data immediately validates the full stack
5. This task has the highest signal-to-effort ratio for a first pilot conversation

**Files involved:**
- `product/regradar/app/api/v1/router.py` — add `/sources` and `/sources/status` endpoints using source history JSONL
- `product/regradar/app/source_readiness.py` — existing readiness report builder
- `product/regradar/web/src/components/DashboardPreview.jsx` — replace mock with API call
- `product/regradar/web/src/components/Coverage.jsx` — update to show live source status
- `product/regradar/web/src/api.js` — add sources fetch function

**Acceptance criteria:**
1. GET /api/v1/sources/status returns real source status from source_runs.jsonl
2. Dashboard source status widget shows real data from API
3. Sources page shows real source list with last-run status
4. If source_runs.jsonl is empty, dashboard shows empty state (not crashed)
5. Test: run `python run.py source-readiness --market AE --record-run` then reload dashboard and see status updated

**Validation command:**
```bash
cd product/regradar
python -m compileall app run.py -q
npm --prefix web run build
```

**Rollback:** Changes are isolated to router.py (new endpoint) and two frontend components. Rollback by removing new endpoint and reverting DashboardPreview.jsx to mock data.

---

## SECTION 28 — NEXT IMPLEMENTATION PROMPT

See `docs/statuteproof-next-implementation-task.md` for the copy-paste implementation prompt.

---

*End of Master Specification. For monitoring information only. Not legal advice.*
