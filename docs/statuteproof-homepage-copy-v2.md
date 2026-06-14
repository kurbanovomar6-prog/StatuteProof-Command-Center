# StatuteProof — Homepage Copy v2

**Version:** 2.0  
**Date:** 2026-06-12  
**Status:** Implementation-ready  
**IMPORTANT:** All sample/demo data in this document is labeled [SAMPLE — NOT REAL REGULATORY DATA]. The homepage copy is legal-safe and has been reviewed for forbidden phrases.

---

## Design Notes

**Color system:**
- Page background: #0B1426 (dark navy)
- Card/panel background: #0F1E35 (slightly lighter navy)
- Section alternating background: #081020 (even darker for contrast variation)
- Primary text: #FFFFFF
- Secondary text: #8B9AB5 (slate-400 equivalent)
- Muted text: #4B5A6E
- Green (CHANGED, primary CTA text-on-dark): #22C55E
- Amber (MEDIUM risk, warnings): #F59E0B
- Red (HIGH risk, errors): #EF4444
- Blue (FIRST_SEEN, info): #3B82F6
- Borders/dividers: #1A2D44
- Input backgrounds: #0F1E35

**Typography:**
- Headings: Inter or Geist, weight 600-700, tracking -0.02em
- Body text: Inter, weight 400, line-height 1.7
- Mono (hashes, code, IDs): JetBrains Mono or Fira Code, weight 400
- Font sizes: H1 48-56px desktop / 32px mobile, H2 32-36px, H3 20-24px, body 16px, caption 13-14px

**Logo:** Keep existing logo. No redesign of logo.

**Aesthetic register:** Premium B2B compliance tool. Not a crypto startup. Not consumer fintech. Closer to Bloomberg data terminal or a serious legal research tool than a SaaS landing page. Use whitespace purposefully. Let the evidence card and data speak. Avoid: gradient blobs, glowing orbs, animated particles, cartoon illustrations, generic stock photos of businesspeople.

---

## HEADLINE OPTIONS

**Option 1 (CHOSEN WINNER):**
> "Monitor UAE regulatory sources. Know what changed. Have the evidence to show it."

**Option 2:**
> "Official-source regulatory monitoring with an audit trail for UAE compliance teams."

**Option 3:**
> "Your UAE compliance team doesn't need another tool. They need proof of what changed."

**Option 4:**
> "SHA-256. Diff. Timestamp. That's what a regulatory change looks like at StatuteProof."

**Option 5:**
> "When VARA publishes a rule change, StatuteProof detects it, stores the evidence, and drafts the brief. You review it."

**Chosen winner: Option 1**

Rationale: Evidence-first without being cryptic. "Know what changed" addresses the MLRO's core fear. "Have the evidence to show it" speaks to audit readiness — the real business driver. Not AI-first. Not "prevent fines" (forbidden). Not "replace your team" (forbidden). Directly addresses Persona 1 (MLRO at VASP) and Persona 2 (CCO at fintech) most clearly.

---

## HERO SECTION

**Headline:**
Monitor UAE regulatory sources.
Know what changed.
Have the evidence to show it.

**Subheadline:**
StatuteProof monitors selected UAE official regulatory sources — VARA, CBUAE, DFSA, ADGM FSRA, UAE FIU, and more — detects text changes, stores SHA-256 evidence records, and delivers human-reviewed compliance briefs. For UAE-regulated VASPs, fintechs, and financial firms.

**Primary CTA button:**
Request a free UAE source readiness review

**Secondary CTA button (ghost/outlined):**
View sample evidence-backed brief

**Trust line (below CTAs, small, secondary text color):**
Monitoring information only — not legal advice — source coverage and limitations disclosed

**Disclaimer line (smallest text, muted):**
StatuteProof reports are for information and compliance review support only. Not legal advice, not a compliance determination. See full disclaimer →

**Hero visual:** The Sample Evidence Alert Card below (see next section). No hero photography. The card IS the proof of concept.

---

## SAMPLE EVIDENCE ALERT CARD

**Label (prominent, amber badge):** [SAMPLE — NOT REAL REGULATORY DATA]

```
╔══════════════════════════════════════════════════════════════════╗
║  REGULATORY CHANGE DETECTED                   [SAMPLE / FAKE]   ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  Source:      VARA — Enforcement Notices                         ║
║  Regulator:   Dubai Virtual Assets Regulatory Authority          ║
║  URL:         https://www.vara.ae/en/enforcement/               ║
║  Status:      ● CHANGED                                          ║
║  Detected:    2026-06-10 09:14:22 UTC                           ║
║  Risk Level:  MEDIUM                                             ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║  Evidence Record                                                 ║
║  ────────────────────────────────────────────────────────────── ║
║  Previous hash:   a3f8d2c1b9e4f7a0  (2026-06-03 07:02 UTC)     ║
║  Current hash:    7c1a9b3ed2f6e8c4  (2026-06-10 09:14 UTC)     ║
║  Diff available:  YES — 3 sections changed                      ║
║  Extraction:      Playwright  |  Quality: GOOD  |  4,821 chars  ║
║  Snapshot saved:  data/source_snapshots/2026-06-10/AE/VARA/     ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║  Affected entities:   VASP licence holders, custody providers   ║
║  Change type:         RULEBOOK_UPDATE                           ║
║  ────────────────────────────────────────────────────────────── ║
║  ⚠  Human review required before delivery                       ║
╠══════════════════════════════════════════════════════════════════╣
║  Disclaimer: Not legal advice. For monitoring information only. ║
║  Verify change against official source before acting.           ║
╚══════════════════════════════════════════════════════════════════╝
```

**Design notes for implementation:**
- Card background: #0F1E35
- Left border: 3px solid #22C55E (green — CHANGED)
- "CHANGED" status: green pill badge (#22C55E bg, dark text)
- "SAMPLE / FAKE" badge: amber (#F59E0B bg, dark text), top-right corner, must be visible
- Hash values: JetBrains Mono, #8B9AB5 (slate)
- Evidence Record section: slightly lighter background (#14263D)
- "Human review required" row: amber left-accent with amber text
- Section dividers: #1A2D44
- Disclaimer row: muted text (#4B5A6E), italic

**Caption below card:**
Every change event on a monitored source produces an evidence record like this one. SHA-256 hashes, diff, extraction quality, and snapshot path — all stored and verifiable.
This card is labeled [SAMPLE / FAKE] and uses no real regulatory data.

---

## PROBLEM SECTION

**Section background:** #081020 (darker for contrast)

**Headline:**
The problem with manual regulatory monitoring is the gap you don't see.

**Body:**
Most compliance teams at UAE VASPs and fintechs check regulatory websites manually — a few times a week when discipline holds, less often when it doesn't. VARA publishes rulebook updates on its website. CBUAE posts circulars as PDFs. The UAE FIU publishes AML/CFT guidance without alert emails. DFSA updates its rules without notifying every regulated firm by name.

The real risk is not the update you catch. It is the one that sat on an official website for three weeks before anyone on your team noticed.

And when your supervisory reviewer asks when you became aware of a rule change, "we checked the website regularly" is not the same as "here is the timestamped evidence record with the diff."

**Supporting bullets:**
- UAE official regulatory sources require active monitoring for most licensed firms, but each source needs a readiness status before activation
- No consolidated UAE regulatory change notification service exists
- Website restructures, PDF reformats, and JavaScript rendering can cause missed changes even when teams are checking regularly
- Manual monitoring creates an audit gap: you know you checked, but you cannot prove it

---

## HOW STATUEPROOF WORKS

**Headline:**
From official source to evidence-backed brief — the complete workflow.

**Step 1 — Monitor official sources**
StatuteProof fetches selected UAE official regulatory sources on a scheduled basis. Sources are fetched from their official URLs. Limitations are disclosed per source — JavaScript-only pages, PDF-primary sources, and geo-restricted pages are flagged, not silently ignored.

**Step 2 — Detect changes with evidence**
Fetched content is normalized and hashed using SHA-256. When the current hash differs from the stored baseline, the source is marked CHANGED. A diff is generated showing what was added, removed, or modified. Raw snapshot, normalized text, hash, and diff are stored together as an evidence record.

**Step 3 — Score risk and draft alert**
The detected change is assessed against a rule-based risk classifier. Risk levels: LOW, MEDIUM, HIGH. High-risk signals include obligation language, deadline references, penalty language, licensing changes, and AML/CFT framework updates. All drafts are held for review — nothing reaches a customer automatically.

**Step 4 — Human review, then brief delivery**
No alert or brief reaches a customer without explicit human review and approval. HIGH-risk alerts require an additional review step. After approval, the brief includes the evidence record, diff excerpt, risk score, and the full not-legal-advice disclaimer.

**Visual:** A horizontal flow diagram (or vertical steps on mobile) connecting the four steps with icons (source icon → hash icon → risk badge → brief document). No stock photography.

---

## UAE SOURCE COVERAGE SECTION

**Headline:**
13 enabled UAE regulatory sources. 10 confirmed. 3 under extraction remediation. Limitations disclosed.

**Subheadline:**
These are the official UAE sources currently mapped in StatuteProof's UAE source pack. Status and extraction quality are shown honestly before monitoring activation.

**Source table:**

| Source | Regulator | Category | Status |
|--------|-----------|----------|--------|
| VARA — Enforcement Notices | Dubai Virtual Assets Regulatory Authority | Financial Regulator | CONFIRMED |
| CBUAE Regulations | Central Bank of the UAE | Central Bank | CONFIRMED |
| DFSA Rulebook | DFSA | Financial Regulator | UNDER EXTRACTION REMEDIATION |
| DFSA Regulatory Notices | DFSA | Financial Regulator | UNDER EXTRACTION REMEDIATION |
| ADGM FSRA Main | ADGM | Financial Regulator | CONFIRMED |
| DIFC Laws and Regulations | DIFC | Legal Database | CONFIRMED |
| UAE FIU Circulars and Notices | UAE Financial Intelligence Unit | AML/CFT | CONFIRMED |
| UAE Ministry of Finance | Ministry of Finance | Finance Ministry | CONFIRMED |
| UAE Legislation Portal | UAE Government | Legal Acts | CONFIRMED |
| UAE Ministry of Economy | Ministry of Economy | Company Registry | CONFIRMED |
| VARA Homepage | Dubai Virtual Assets Regulatory Authority | Financial Regulator | CONFIRMED |
| Central Bank UAE Homepage | Central Bank of the UAE | Central Bank | CONFIRMED |
| UAE FIU Homepage | UAE Financial Intelligence Unit | AML/CFT | UNDER EXTRACTION REMEDIATION |

**Limitation disclosure (mandatory, inline):**
Certain UAE sources are not currently monitorable from outside the UAE: UAE Federal Tax Authority (FTA), UAE Official Gazette, certain SCA pages. These appear as BLOCKED in your source readiness report. StatuteProof does not claim complete UAE regulatory coverage. Source status and limitations are disclosed per source.

**CTA below table:**
Want to see which sources are confirmed for your specific licence type?
[Request a free UAE source readiness review]

---

## EVIDENCE TRAIL SECTION

**Section background:** Alternating section background

**Headline:**
Every change comes with a proof record you can audit yourself.

**Body:**
When StatuteProof detects a change on an official source, it stores an evidence record containing everything you need to verify the detection independently:

- The official source URL
- SHA-256 hash of the normalized text before and after the change
- Full text diff — what was added, what was removed
- Extraction method (HTML, PDF, or Playwright-rendered) and quality rating
- Detection timestamp in UTC
- Known limitations for this source (if any)

This is not a summarization tool. The evidence record is the foundation. The brief is built on top of it. A brief cannot be delivered if the evidence record is incomplete.

**Design element:** A simplified visual of the evidence record card — not a card in full detail, but a representation of the key fields (source, hash before/after, diff indicator, timestamp) in a clean monospace-styled layout.

---

## WEEKLY BRIEF SECTION

**Headline:**
One brief per week, per client profile — reviewed before it reaches you.

**Body:**
StatuteProof generates weekly monitoring briefs from approved change events. Each brief includes:

- The monitoring period covered
- Reviewed regulatory updates with source, risk level, and brief description
- Source coverage and limitations for the period
- The full not-legal-advice disclaimer

Briefs come only from alerts that a human reviewer has explicitly approved for delivery. An empty monitoring period generates an honest "no reviewed updates were approved" brief — not a false "nothing changed" statement.

**Brief formats:** Markdown (copy into your compliance system), PDF export. Later: direct email delivery.

---

## HUMAN REVIEW SECTION

**Headline:**
StatuteProof detects and documents. Your team reviews and decides.

**Body:**
Every StatuteProof alert and brief is produced by an automated monitoring pipeline and reviewed by a human before delivery.

We do not send automated legal interpretations. We do not claim to tell you whether you are compliant. We do not replace your legal team or your MLRO.

**What StatuteProof does:**
Detects text changes on monitored official sources. Stores evidence of the change. Classifies risk using a rule-based classifier. Drafts a brief for human review. Delivers the brief with the evidence record attached.

**What you do:**
Review the brief with your compliance team. Verify the change against the official source. Consult legal counsel if the risk level requires it. Update your compliance programme accordingly.

**Disclaimer block (styled as a highlighted info box):**
StatuteProof reports are for information and compliance review support only. They do not constitute legal advice, regulatory advice, compliance determination, or a legal opinion.

---

## SOURCE READINESS REVIEW CTA SECTION

**Headline:**
See exactly which UAE sources are monitorable for your firm — before you commit.

**Subheadline:**
A free UAE Source Readiness Review gives you a detailed report of which UAE regulatory sources are confirmed, which need remediation, which have access limitations, and which are not currently accessible.

**What you receive:**
- A report of which UAE official sources are CONFIRMED, UNDER EXTRACTION REMEDIATION, LIMITED, or BLOCKED for your licence type
- Extraction quality ratings per source
- Known limitations disclosed per source (JavaScript rendering, geo-restrictions, PDF-only sources)
- A pilot recommendation based on your source coverage

**Process:**
Fill out the form → 1 business day response → 2-3 business days to complete → Report delivered by email

No commitment required. No automatic subscription.

**Primary CTA:** Request a free UAE source readiness review

**Supporting text (small, muted):**
Not legal advice. Not a compliance assessment. The readiness review is for information purposes only.

---

## PRICING PREVIEW SECTION

**Headline:**
Start with a free source readiness review. Pilot after scope is confirmed.

**4 tiers (preview cards):**

**Free Source Readiness Review**
Free, one-time
See which UAE sources are monitorable for your firm. No commitment.
[Request free review]

**Founding Pilot**
$299–499/mo
5 UAE sources · Weekly brief · Evidence records · 2 seats
[Request pilot]

**UAE VASP/Fintech Pack**
$499–999/mo
13 enabled UAE sources, with 10 confirmed and 3 under extraction remediation · Custom sources · Urgent alerts · 5 seats
[Request details]

**Compliance Consultant Pack**
$999–2000/mo
Multi-client · 25 custom sources · API access · 10 seats
[Request details]

**Note below pricing:**
Manual invoicing. No credit card required to start. Pricing may change after pilot period.

Full pricing details → [Pricing page]

---

## FAQ SECTION

**Headline:** Frequently asked questions

**Q1: Is StatuteProof a legal adviser or compliance consultant?**
No. StatuteProof is an official-source monitoring tool that detects text changes, stores evidence records, and delivers human-reviewed compliance briefs. It does not provide legal advice, regulatory interpretations, or compliance opinions. Always consult qualified legal counsel before making regulatory decisions.

**Q2: Which UAE regulatory sources does StatuteProof monitor?**
Currently: 13 enabled UAE sources, with 10 confirmed and 3 under extraction remediation. DFSA Rulebook, DFSA Regulatory Notices, and UAE FIU Homepage remain under extraction remediation and are not treated as confirmed for monitoring. Some UAE sources — including the Federal Tax Authority and certain SCA pages — may require additional item-level checks or be disclosed as limited/blocked. See the Source Coverage page for the full status of every source.

**Q3: What happens if a source website changes its structure?**
When a source structure change is detected, it is flagged as SOURCE_STRUCTURE_CHANGED, not silently treated as a content change. The failure is surfaced to you. You can see which sources are FAILED or QUALITY_DROP at any time in the dashboard. We do not report UNCHANGED when extraction has failed.

**Q4: Does StatuteProof cover all UAE regulators?**
No. StatuteProof covers selected official UAE sources and discloses which sources are monitored, which have limitations, and which are not accessible. Adding new sources requires source testing, quality validation, and configuration. We do not claim complete UAE regulatory coverage.

**Q5: Can I add my own custom sources?**
Yes, on the UAE VASP Pack and Consultant Pack. Custom source monitoring allows you to add official regulatory URLs not in the default UAE pack. Custom sources are tested for extraction quality before activation, and limitations are disclosed in every alert generated by a custom source.

**Q6: What does "human review required" mean?**
Every alert generated by the monitoring pipeline is reviewed by a human before delivery. No automated alert or brief is sent to customers without an explicit review and approval step. HIGH-risk alerts require mandatory review — they cannot be delivered without it.

**Q7: How does the evidence record work?**
Each change event produces an evidence record containing: the official source URL, SHA-256 hashes before and after the change, a text diff of what changed, extraction method and quality, and a UTC timestamp. You can verify any record independently by re-fetching the official source and applying the same normalization steps.

**Q8: What if I need monitoring for a regulator not in the current UAE pack?**
Request a source readiness review and specify the regulator or URL. We will test the source, disclose its extractability, and if it passes quality standards, add it to your monitoring profile. Custom source additions are subject to extraction quality testing and our standard safety checks.

---

## FOOTER

**Left column:**
StatuteProof [logo]
Official-source regulatory monitoring for UAE compliance teams.

**Middle column — Links:**
Product: How It Works · Source Coverage · Sample Brief · Pricing
Company: About · Security · Contact
Legal: Terms of Service · Privacy Policy · Disclaimer

**Right column — Contact:**
For pilot enquiries: pilots@statuteproof.com
For readiness reviews: [readiness review form]

**Full disclaimer (footer):**
StatuteProof monitors selected official UAE regulatory sources. Reports generated by StatuteProof are provided for information and compliance review support only. They do not constitute legal advice, regulatory advice, compliance determination, or a legal opinion. StatuteProof does not replace qualified legal counsel, compliance professionals, MLROs, or other professional advisers. StatuteProof does not determine compliance outcomes, prevent fines, or confirm that all regulatory updates have been captured. Source monitoring may be affected by publication delays, website changes, PDF formatting, access limits, or source structure changes. Users should verify official source material directly and consult qualified legal or compliance professionals before making regulatory, filing, or operational decisions. StatuteProof is not affiliated with, endorsed by, or an official partner of VARA, CBUAE, DFSA, ADGM, UAE FIU, DIFC, or any UAE regulatory authority.

**Copyright line:**
© 2026 StatuteProof. All rights reserved.

---

## LEGAL SAFETY AUDIT CHECKLIST (FOR THIS PAGE)

Before implementing this homepage copy, verify:

- [ ] No compliance outcome guarantee claim → None present
- [ ] No claim of "prevent fines" → None present
- [ ] No claim of "replace lawyers" → None present
- [ ] No claim of "100% accurate" → None present
- [ ] No absolute update-detection claim → None present
- [ ] No claim of "official partner of VARA/CBUAE/DFSA/ADGM" → None present
- [ ] No regulator approval or endorsement claim → None present
- [ ] No claim of "AI lawyer" or "automated legal advice" → None present
- [ ] All sample data labeled [SAMPLE / FAKE] → Yes — hero card, sample brief
- [ ] Short disclaimer in footer → Yes — "Monitoring information only. Not legal advice."
- [ ] Full disclaimer in footer → Yes — full paragraph
- [ ] "Not legal advice" appears in hero → Yes — trust line below CTAs
- [ ] Source coverage limitations disclosed → Yes — in coverage section
- [ ] SAMPLE label visible on sample alert card → Yes — amber badge, top-right

---

*For monitoring information only. Not legal advice.*
