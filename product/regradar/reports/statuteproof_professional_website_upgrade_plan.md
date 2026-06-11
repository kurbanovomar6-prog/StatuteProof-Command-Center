# StatuteProof — Professional Website Upgrade Plan

**Date:** 2026-05-31
**Status:** Plan only — no implementation, no file edits, no commits
**Product:** StatuteProof — UAE-first official-source regulatory intelligence

---

## PART 1 — Brutally Honest Diagnosis

### 1. Why the current website feels too small

The product description is accurate but the framing is operational rather than commercial. "We monitor 9 sources" is a technical fact, but it reads as the headline of a scraper service rather than the headline of a compliance intelligence platform. Every reference to source count, extraction methods, and delta statuses is correct and important — but it is being shown to buyers before they understand why they need the product. Engineering vocabulary is dominating the first impression.

The dashboard mockup in the hero shows a single-jurisdiction sidebar with "9 sources configured." A compliance officer at a DIFC investment manager with a $500k/year Thomson Reuters contract will look at this and think: "nine sources is what I browse manually in an hour." The number is not the problem — the framing is. Nine officially validated UAE financial regulators are the nine that matter. That is not a small number. It is the precise set. But the site never makes that argument.

The hero headline — "Know when your regulators publish. Before it becomes a compliance gap." — is technically correct but emotionally soft. It describes a feature. It does not land on the pain. A compliance officer who missed a VARA circular and had to explain it to their board does not think "I need to know when regulators publish." They think "I cannot afford to find out about this from a client."

### 2. What makes it look early-stage

- The hero mockup says "9 sources configured" in the sidebar and shows one jurisdiction. This looks like a demo account.
- The Coverage section opens with "Nine active sources. Three with documented access limitations." The number leads. The quality argument does not.
- The HowItWorks steps are labelled "01" through "05" and describe mechanics. There is no before/after emotional frame.
- The status tags (FIRST_SEEN, UNCHANGED, CHANGED, QUALITY_DROP) appear as floating badges with no visual explanation of what they mean in practice.
- The TrustLayer section (Evidence Trail) is the most differentiating content on the site — but it appears fifth or sixth in the scroll, after most buyers have already formed a first impression.
- The DashboardPreview is labelled "Sample source set — illustrative." This is honest, but "illustrative" reads as "not real."
- The pricing cards say "From $99" and "From $249" — the "From" prefix on low prices makes them feel cheap rather than premium-pilot.
- There is no testimonial, no case reference, no usage stat, no specificity that makes the product feel operational. Everything is capability description, not evidence of operation.

### 3. What is already strong and must be preserved

- The disclaimer language is excellent. Every section correctly says "not legal advice," "limitations disclosed," "human review required." This is rare in regtech and builds trust with sophisticated compliance buyers.
- The ConfiguredMonitoring section (client profiles) is well-structured and commercially specific. VARA/CBUAE for VASPs, DFSA/DIFC Laws for DIFC firms — these are accurate and show real domain knowledge.
- The TrustLayer content is genuinely differentiating. "A compliance alert you cannot verify is a liability, not an asset." That is a quotable, true statement.
- The Contact form with regulator selection chips is excellent. It qualifies leads, shows domain knowledge, and creates a structured intake for the source readiness review.
- The HowItWorks step content is accurate and complete. The pipeline description is correct. Only the framing needs work.
- The brand visual (dark #07111F, #16D9F5 accent) is appropriate for a compliance technology product. It does not need a redesign.
- The four-tier pricing structure (Free / $99 / $249 / $499) with "Founding Pilot" framing is commercially sound.

### 4. What must change

- The hero must lead with the pain, not the feature.
- The "9 sources" framing must become "validated core UAE financial authority layer."
- The Coverage section must show a four-tier map (Active / Limited / Under Validation / Not Yet Active) so that 9 active sources appear as the proven layer of a growing coverage map, not the ceiling.
- The TrustLayer must move higher — it belongs in the second or third section, not the fifth.
- The workflow must be shown as a before/after contrast (without StatuteProof / with StatuteProof) with the pipeline showing what happens at each step.
- The dashboard preview must feel like a real monitoring session, not a wireframe labelled "illustrative."
- The hero mockup must show more than one CHANGED alert and must not show "9 sources configured" as the primary status.

---

## PART 2 — New Positioning

### 1. Core positioning in one sentence

StatuteProof monitors official UAE regulatory publications, detects meaningful changes, filters them to your regulatory profile, and delivers evidence-backed compliance briefs — with every alert linked to the source, the timestamp, and the extraction proof.

### 2. The buyer pain

UAE financial regulators publish independently — across CBUAE, VARA, DFSA, ADGM/FSRA, UAE FIU, Ministry of Finance, the UAE Legislation Portal, DIFC Laws, and the Ministry of Economy. There is no unified notification feed. No alert when a new circular is published. No automatic notification when VARA updates its rulebook. No system that tells a compliance team whether a detected change is relevant to their licence type. Compliance teams find out about regulatory changes the same way everyone else does: industry newsletters, legal counsel, or a client who already knows. By that point, the gap has already opened.

### 3. The transformation

**From:** Manual weekly review of nine regulator portals → delayed discovery → generic alerts from news aggregators → compliance team scrambles → legal review under time pressure → reactive compliance posture.

**To:** Scheduled official-source monitoring → normalized change detection → alert draft with source URL, timestamp, and extraction proof → profile-matched relevance filtering → human-reviewed brief → proactive compliance posture with auditable evidence trail.

### 4. Value proposition by client profile

**UAE VASP / crypto firm:**
VARA updates its rulebook across seven activity types. Each update carries licensing implications. StatuteProof monitors VARA official publications and delivers a structured brief when something in your activity scope changes — with the source URL, what changed, and what your licence profile requires next.

**UAE payments / fintech:**
CBUAE publishes payment system regulations, licensing circulars, and supervisory notices independently. StatuteProof monitors CBUAE publications and UAE FIU AML/CFT guidance scoped to payment service providers — no DIFC-specific or VARA-specific content unless your profile includes it.

**DIFC-regulated firm:**
DFSA rulebook changes, DIFC Laws amendments, and UAE FIU AML/CFT guidance applicable to DIFC-licensed entities. StatuteProof monitors all three on a schedule and delivers a brief when something in your DIFC regulatory scope changes.

**ADGM-regulated firm:**
FSRA regulatory notices, ADGM legislative updates, and UAE FIU AML/CFT guidance applicable to ADGM-licensed firms. Symmetric with DIFC coverage. Each profile is configured independently.

**AML / compliance consultant:**
UAE FIU typologies and guidance, CBUAE AML/CFT compliance notices, Ministry of Economy DNFBP supervision, and VARA AML guidance where relevant. Multi-client consultants can request separate monitoring profiles per client.

**Law firm with UAE regulatory practice:**
UAE Legislation Portal for federal law publications, DIFC Laws for DIFC legislative changes, DFSA and FSRA consultation papers for advance notice of upcoming regulatory amendments, Ministry of Finance for federal financial policy. Capital Market Authority coverage under validation.

---

## PART 3 — New Landing Page Structure

### Recommended section order

**1. Hero**
- Purpose: land on the pain, establish the product, drive the CTA
- Must not: lead with source count, lead with extraction vocabulary
- Visual: full-width dark hero, headline above dashboard mockup showing a real monitoring session with 2–3 differentiated alerts

**2. Regulatory fragmentation problem**
- Purpose: validate the buyer's existing pain before selling the solution
- Must not: describe the product — this section is about the problem only
- Visual: a visual showing 9 separate regulator portals with no unified feed, a gap between "published" and "found out"
- Copy direction: "CBUAE, VARA, DFSA, ADGM/FSRA, UAE FIU, Ministry of Finance, UAE Legislation Portal, DIFC Laws, Ministry of Economy — each publishes independently. No unified notification. No feed. No alert."

**3. Without StatuteProof vs With StatuteProof**
- Purpose: make the transformation concrete and felt
- Visual: two-column side-by-side comparison
- Left (Without): manual checking → delayed discovery → generic news alert → scramble → reactive brief under pressure
- Right (With): scheduled monitoring → structured brief → source URL + timestamp → profile-matched → proactive posture

**4. Intelligence pipeline workflow**
- Purpose: show the full workflow as a serious intelligence system
- Visual: horizontal pipeline with 7 stages: Official Source → Extraction Quality Check → Normalized Snapshot → Diff/Proof → Alert Draft → Relevance Filter → Human Review → Brief Delivery
- Must show the CHANGED → HOLD_FOR_REVIEW → APPROVED_FOR_WEEKLY → Brief path
- Copy: not just "what it does" but "what happens at each gate and why"

**5. Evidence-backed brief example**
- Purpose: make abstract claims concrete with a real artifact
- Visual: an annotated brief excerpt showing source name, URL, timestamp, content fingerprint, change status, what changed, relevant to whom, recommended action, limitations, not-legal-advice disclaimer
- Label clearly: "Illustrative — based on UAE regulatory monitoring workflow"

**6. UAE coverage map**
- Purpose: reframe "9 sources" as "validated core layer of a growing map"
- Visual: four-tier table: Active Validated / Limited / Under Validation / Not Yet Active
- Must include expansion map showing what is being validated next

**7. Configured monitoring / client profiles**
- Purpose: show the product understands different buyer needs
- Visual: 5–6 profile cards, each showing which sources, which alert topics, which not included by default
- This section already exists and is strong — preserve it

**8. Source quality and validation process**
- Purpose: make the source quality argument explicitly, not just implicitly
- Visual: a "how we validate a source before adding it" panel — access test → extraction quality → content threshold → limitations documented → then and only then added to a client profile
- This is the differentiator from a scraper: quality gates before activation

**9. Sample monitoring session / dashboard preview**
- Purpose: show what a real monitoring session output looks like
- Visual: the existing DashboardPreview component, reframed as "monitoring session" not "illustrative sample"
- Change the label from "Sample source set — illustrative" to "UAE monitoring session — 9 sources checked · 1 CHANGED · source proof attached"

**10. Weekly brief output**
- Purpose: show what the deliverable looks like
- Visual: a rendered HTML brief excerpt — use the existing weekly_brief HTML output
- Label: "Sample UAE VASP weekly brief — generated from reviewed alert draft"

**11. Pricing / founding pilot**
- Purpose: convert interested buyers
- Visual: existing four-card layout with minor copy improvements
- Remove "From" prefix — replace with exact price with a note that custom scope may vary

**12. Free Source Readiness Review CTA**
- Purpose: low-friction entry point — the main top-of-funnel offer
- Visual: dark section, large headline, single CTA button, 4-step "what happens next" panel
- Must feel like a professional service offer, not a free trial sign-up

**13. Limitations / FAQ / not legal advice**
- Purpose: pre-empt objections from sophisticated buyers who will ask
- Visual: clean accordion or flat list of honest answers
- Questions: "Does this cover all UAE regulations?" / "Is this legal advice?" / "What happens when a source is blocked?" / "How often do you check sources?"

**14. Contact**
- Purpose: intake form for source readiness review requests
- Existing form is strong — minor copy improvements only

---

## PART 4 — Hero Rewrite

### Badge
```
UAE Financial Regulators · Official-Source Monitoring · Human-Reviewed Briefs
```

### Headline
```
CBUAE published a circular.
VARA updated its rulebook.
DFSA issued a notice.

Your team needs to know —
not find out later.
```

Alternative tighter version:
```
Nine UAE financial regulators publish independently.
StatuteProof monitors all of them.
```

### Subheadline
```
StatuteProof monitors official publications from UAE's core financial
regulatory authorities. When a meaningful change is detected, your team
receives a structured brief — linked to the official source, timestamped,
extraction-quality verified, and filtered to your regulatory profile.
```

### Proof line
```
9 officially validated UAE regulatory sources · CBUAE · VARA · DFSA ·
ADGM/FSRA · UAE FIU · Ministry of Finance · UAE Legislation Portal ·
DIFC Laws · Ministry of Economy · Source quality verified before activation ·
Limitations disclosed on every brief
```

### Primary CTA
```
Get a free source readiness review →
```

### Secondary CTA
```
See a sample brief
```

### Small trust note
```
StatuteProof provides early-warning regulatory intelligence, not legal
advice. FTA, Official Gazette, and e-Laws have documented access
limitations — disclosed before any pilot begins.
```

---

## PART 5 — Coverage Strategy

### The reframing argument

Nine active sources is not a small number when those nine sources are:
- The UAE central bank and primary financial regulator (CBUAE)
- The dedicated virtual assets regulator (VARA)
- The DIFC financial services regulator (DFSA)
- The ADGM financial services regulator (FSRA)
- The national financial intelligence unit (UAE FIU)
- The federal finance ministry (Ministry of Finance)
- The federal legislation index (UAE Legislation Portal)
- The DIFC primary legislation database (DIFC Laws)
- The federal commercial and AML supervision authority (Ministry of Economy)

This is the validated core of UAE financial regulatory monitoring. Every source meets an extraction quality threshold before activation. Three additional sources have documented access limitations. Several more are under active validation. And a set of sources are geo-blocked from outside UAE and are disclosed as such.

The framing is not "only 9." The framing is "9 verified, 3 limited, 8+ under validation, and the ones that are blocked are told to you honestly."

### Four-tier presentation

**Tier 1 — Active: Validated, quality-checked, in client profiles**

| Source | Category | Extraction |
|--------|----------|-----------|
| CBUAE | Central bank / banking / payments | HTML (Playwright) |
| VARA | Virtual assets / VASP licensing | HTML + PDF |
| DFSA | DIFC financial services | HTML |
| ADGM / FSRA | ADGM financial services | HTML |
| UAE FIU | AML / CFT guidance | HTML (Playwright) |
| Ministry of Finance | Federal finance policy | HTML |
| UAE Legislation Portal | Federal legislation | HTML (Playwright) |
| DIFC Laws | DIFC primary legislation | HTML |
| Ministry of Economy | AML / DNFBP / commercial | HTML |

Display treatment: green Active badge, source name, what it publishes, extraction method. No caveats.

**Tier 2 — Limited: Accessible with documented constraints**

| Source | Constraint |
|--------|-----------|
| Capital Market Authority / former SCA | Transitional following Federal Decree-Law No. 32 of 2025. Source URL and structure under review. Fallback via UAE Legislation Portal available. |
| Federal Tax Authority (FTA) | Portal renders no extractable content from outside UAE. Monitoring not available until UAE-IP deployment. |

Display treatment: amber Limited badge. State the constraint. State the fallback. State when it will be disclosed to pilots.

**Tier 3 — Under Validation: Official sources, active technical investigation**

Display as a visual list with "Under Validation" badge. No extraction numbers, no quality claims — just: "this is a real official source, we are validating whether we can monitor it reliably."

Sources to show:
- UAE Data Office (PDPL supervisory authority)
- Executive Office for AML/CFT
- Insurance Authority
- VARA publications / rulebook sub-page
- CBUAE publications / circulars sub-page
- DFSA consultation papers
- DFSA rulebook amendments
- ADGM FSRA regulatory notices
- ADGM FSRA consultation papers
- DIFC Data Protection Commissioner
- Capital Market Authority (CMA, new authority — validation in progress)
- DMCC Crypto Centre

Exact disclaimer to use:
> "Under Validation sources are confirmed official UAE regulatory authorities. Technical validation — accessibility, extraction quality, and content threshold — is in progress. These sources are not included in any client scope until validation is complete. Status is updated as validation progresses."

**Tier 4 — Not Yet Active: Geo-blocked or access-restricted, disclosed**

| Source | Reason |
|--------|--------|
| UAE Official Gazette | Geo-blocked — unreachable from outside UAE |
| e-Laws / Ministry of Justice | Access-restricted — connection timeout |
| TDRA | Geo-blocked — connection timeout |
| GCA Customs | Geo-blocked — connection failure |

Exact disclaimer:
> "These sources are confirmed UAE official publications that cannot currently be monitored from outside the UAE. They are listed here because we believe in transparent coverage maps. If your compliance scope requires any of these sources, we will tell you before any pilot begins."

### What must not be implied

- Do not use "comprehensive" or "complete" anywhere near the coverage section
- Do not say "all UAE regulators" — say "UAE's core financial regulatory authorities"
- Do not show Under Validation sources with green badges
- Do not list Not Yet Active sources under the Active heading
- Do not imply that the Under Validation list represents confirmed future coverage

---

## PART 6 — Source Expansion Roadmap

### P0 — Before serious outreach (highest ROI, no UAE-IP needed)

**UAE Legislation Portal — item-level adapter**
- Commercial value: Transforms the most important existing source from "monitoring but no alerts" to "alerts with specific law titles and decree numbers." Currently produces CHANGED signals that are UNKNOWN_REQUIRES_ADAPTER. After fix, every UAE pilot benefits.
- Client profiles: all
- Difficulty: Medium — requires Playwright sub-page targeting; root already works at 14,808c
- Effect: alert quality improvement, not source count increase
- Public: show as "Active" after successful validation
- Internal note: Sprint A target

**VARA publications sub-page adapter**
- Commercial value: Changes VARA alerts from "VARA homepage changed" to "VARA published updated guidance for [activity type]." The most commercially sensitive source for VASP clients.
- Client profiles: all VASP applicants and licensed operators
- Difficulty: Medium — `/news-events/` returned 404; need to find correct publications URL structure
- Effect: alert quality improvement
- Public: show as "Active" after successful validation
- Internal note: Sprint A target

**CBUAE circulars/publications sub-page adapter**
- Commercial value: Same argument as VARA. CBUAE is the most-subscribed source. Item-level circular detection is required for all payment and banking clients.
- Client profiles: payments, banking, VASP
- Difficulty: Medium-hard — root requires Playwright; sub-pages previously at 391c; publications index URL unknown
- Effect: alert quality improvement
- Public: show as "Active" after successful validation
- Internal note: Sprint A target

**UAE Data Office / PDPL**
- Commercial value: PDPL is the broadest commercial gap. Every UAE fintech, VASP, and payments firm processes personal data. Entirely missing from current source set.
- Client profiles: all UAE client profiles
- Difficulty: Unknown — URL `uaedataoffice.gov.ae` untested. Test first.
- Effect: new source, new category
- Public: show as "Under Validation" immediately; "Active" after test-source confirms can_monitor
- Internal note: Sprint B target

**Executive Office AML/CFT (amlcft.ae)**
- Commercial value: National AML/CFT policy and typologies. Complements UAE FIU. AML compliance consultants and VASPs need both.
- Client profiles: AML consultants, VASPs, banks
- Difficulty: Low-medium — static government portal likely
- Effect: new source, completes AML category
- Public: show as "Under Validation" immediately; "Active" after validation
- Internal note: Sprint B target

**Capital Market Authority (CMA, cma.gov.ae)**
- Commercial value: Zero capital markets coverage currently. Law firms and investment managers will ask about this in every pilot conversation.
- Client profiles: capital markets firms, law firms, investment managers
- Difficulty: Unknown — new authority post-FDL No.32/2025; site structure unknown; may be SPA
- Effect: new source, new category (if accessible)
- Public: show as "Under Validation" immediately
- Internal note: Sprint B target; if SPA, escalate to adapter queue

### P1 — After first pilots secured

- Insurance Authority (ia.gov.ae) — missing insurance category; insurtech segment
- DFSA consultation papers — forward-looking signal; DIFC clients
- ADGM FSRA regulatory notices — symmetry with DFSA; ADGM clients
- DFSA rulebook amendments sub-page — precision improvement
- ADGM FSRA consultation papers — forward-looking signal
- DIFC Authority regulations (difc.ae/what-we-do/laws-regulations/) — DIFC corporate/employment
- Ministry of Economy AML sub-page — DNFBP supervision precision
- EOCF sanctions register (amlcft.ae/en/sanctions) — sanctions screening signal
- DMCC Crypto Centre — free zone VASP coverage

### P2 — Scale phase

- Dubai Financial Market (dfm.ae) — capital markets exchange
- Abu Dhabi Securities Exchange (adx.ae) — capital markets exchange
- DIFC Data Protection Commissioner — DIFC data protection
- ADGM Data Protection — ADGM data protection
- VARA licensees register — counterparty due diligence
- DIFC Courts publications — law firms
- Nasdaq Dubai — capital markets/sukuk
- DED Dubai — mainland commercial licensing

### P0 sources: public vs internal

| Source | Show publicly as | Internal note |
|--------|-----------------|---------------|
| UAE Legislation Portal item-level | Active (after validation) | Sprint A — transforms broken signal |
| VARA publications sub-page | Active (after validation) | Sprint A — precision improvement |
| CBUAE circulars sub-page | Active (after validation) | Sprint A — precision improvement |
| UAE Data Office / PDPL | Under Validation now → Active after test | Sprint B |
| EOCF AML/CFT | Under Validation now → Active after test | Sprint B |
| CMA | Under Validation now; outcome unknown | Sprint B |

---

## PART 7 — Visual / UX Upgrade Plan

### Dashboard / control room visual

The hero mockup should feel like an operational monitoring session, not a demo. Current issue: sidebar shows "9 sources configured" as the primary status. Better: show the monitoring session state — "UAE monitoring active · 9 sources · last run 14:32 · 1 CHANGED · 8 UNCHANGED · review queue: 1."

The CHANGED alert in the hero mockup should show more detail: not just "New licensing requirements detected" but something closer to: "VARA — VASP Broker-Dealer Activity: Guidance updated — rulebook amendment detected." This shows what the product actually does.

The low/medium/high risk tier in the mockup (rose/amber/slate color) is effective. Keep it.

### Proof trail visual

The TrustLayer content is excellent but abstract. Add one concrete proof block visual — like the one in the weekly brief HTML — showing:
```
Source: VARA · vara.ae
Checked: 2026-05-28 · 14:32 UTC
Status: CHANGED
Fingerprint: 1298a17b...
Extraction: HTML + PDF · Good quality
Relevant to: VASP operators
```
This visual can appear in the Evidence section and again in the sample brief section.

### Coverage map visual

Replace the current three-table layout (Active / Limited / Not Active) with a four-tier visual:
- Tier 1 (green dot): Active — 9 sources
- Tier 2 (amber dot): Limited — 2–3 sources
- Tier 3 (blue dot): Under Validation — 10–12 sources
- Tier 4 (grey dot): Not Yet Active — 4 sources

The visual weight of "Under Validation" showing 10–12 known official sources communicates: this is a growing, actively maintained coverage map, not a finished 9-source product.

### Client profile cards

The existing ConfiguredMonitoring cards are correct in structure. Upgrade: add a subtle "Primary sources" chip list (CBUAE · VARA · UAE FIU) at the top of each card so the source mapping is immediately scannable without reading the full card text.

### Source quality badges

For each active source in the Coverage table, show:
- Access: green/amber/red
- Extraction: HTML / HTML+PDF / PDF-primary
- Change detection: aggregate / item-level
- Last validated: date

"Item-level" vs "aggregate" is important — it shows which sources currently produce precision alerts vs. which are in Sprint A improvement scope.

### Sample brief panel

Add a dedicated section showing the actual weekly brief output. Use a dark panel with the brief rendered inside it (similar to the existing HTML brief style). Label it "Sample UAE VASP Weekly Brief — reviewed and approved · 2026-05-30." This makes the deliverable tangible.

### Hierarchy and spacing

- TrustLayer (Evidence Trail) should move to position 5 or 6 — currently too far down
- "Without vs With" section should appear before HowItWorks, not after
- Pricing should be preceded by the brief sample so buyers have seen the deliverable before seeing the price
- The contact form disclaimer should be shorter — move the long legal text to a hover tooltip or accordion

### What should be above the fold

- Headline (pain statement)
- Subheadline (product description)
- Primary CTA
- Secondary CTA
- First two rows of the hero mockup (CHANGED alert card + proof panel visible)

### What should be moved lower

- Source count numbers (not the headline stat)
- Extraction method vocabulary (FIRST_SEEN / UNCHANGED — move inside the workflow section)
- The dashboard table (already exists in DashboardPreview — keep it but position after the workflow and brief sections)

---

## PART 8 — Copy Bank

### Hero

> CBUAE published a circular.
> VARA updated its rulebook.
> DFSA issued a notice.
>
> Your team needs to know — not find out later.
>
> StatuteProof monitors official publications from UAE's core financial regulatory authorities. When a meaningful change is detected, your team receives a structured brief — linked to the official source, timestamped, verified, and filtered to your regulatory profile.
>
> 9 officially validated UAE sources · Source quality verified before activation · Limitations disclosed on every brief

### Problem section

> Nine UAE financial regulators publish independently. There is no unified notification feed.
>
> CBUAE, VARA, DFSA, ADGM/FSRA, UAE FIU, Ministry of Finance, UAE Legislation Portal, DIFC Laws, Ministry of Economy — each publishes on its own schedule, in its own format, with no alert when something changes.
>
> Most compliance teams find out about regulatory updates the same way everyone else does: an industry newsletter, a colleague's message, or a client who already knows.
>
> By that point, the compliance gap is already open.

### Without vs With

**Without StatuteProof:**
- Manual review of nine regulator portals — weekly, at best
- No structured record of what was checked or when
- No diff between what was there last week and what is there now
- Alerts come from news aggregators, not official sources
- Relevance to your licence type is your problem to work out
- Compliance review happens reactively, under time pressure
- No audit trail of when the change was discovered

**With StatuteProof:**
- Scheduled monitoring of validated official sources
- Normalized snapshot and diff detection on every run
- Delta status: UNCHANGED, CHANGED, QUALITY_DROP — documented per source per run
- Alert drafts filtered to your regulatory profile — VARA updates go to VASP clients, not payments firms
- Human review before delivery — not automated output
- Weekly evidence-backed brief with source URL, timestamp, extraction quality, and limitations
- Full audit trail from source check to delivered brief

### Workflow section

> From official source to evidence-backed brief — seven verified steps.
>
> **Step 1 — Source validation:** Before any source enters a client profile, it passes an accessibility test, an extraction quality check, and a content threshold confirmation. Access, extraction method, and known limitations are documented. You see this before agreeing to a pilot.
>
> **Step 2 — Scheduled monitoring:** Configured sources are checked on a defined schedule. Every run produces a timestamped record: source identity, extraction method, extracted content volume, and change status.
>
> **Step 3 — Normalized snapshot:** Extracted content is cleaned, normalized, and hashed. The normalized hash drives change detection — not raw HTML differences that produce false positives on navigation or cookie changes.
>
> **Step 4 — Diff and proof artifact:** When a source returns CHANGED, the diff between the current and previous normalized snapshot is computed and stored. The proof artifact records source URL, content fingerprint, extraction method, diff quality, and limitations.
>
> **Step 5 — Alert draft:** A structured alert draft is produced: change type, risk level, affected entities, recommended action, confidence, proof block, and a not-legal-advice disclaimer. All drafts are HOLD_FOR_REVIEW until human approval.
>
> **Step 6 — Client relevance filter:** The alert draft is evaluated against your regulatory profile. A VARA update does not go to a DIFC-regulated payments firm. A Ministry of Finance update without AML content does not go to a VASP AML profile.
>
> **Step 7 — Human review and brief delivery:** A human reviewer approves the alert for weekly brief inclusion or rejects it. No alert is delivered without explicit review. Your brief includes only reviewed, approved items.

### Evidence / proof section

> Every alert is auditable. This is not optional — it is the product.
>
> A compliance alert you cannot verify is a liability, not an asset. Every brief from StatuteProof includes the official source URL we monitored, the timestamp and extraction method, the content fingerprint before and after the change, the diff of what changed, the extraction quality assessment, and the limitations of this monitoring method for this source.
>
> If extraction quality drops, the alert is held for human review — not sent. If a source is inaccessible during a run, that failure is logged and disclosed — not silently dropped. The limitations field is never empty.

### Coverage map intro

> StatuteProof uses a four-tier coverage map.
>
> Active sources have passed extraction quality validation and are available in client monitoring profiles. Limited sources are accessible but have documented technical or access constraints that reduce reliability. Under Validation sources are confirmed official UAE regulatory authorities where technical validation is in progress — they are not included in any client scope until validation is complete. Not Yet Active sources are geo-blocked or access-restricted from our current infrastructure and are disclosed honestly before any pilot begins.
>
> Nine active sources is not a small number when those nine sources are the nine UAE financial regulatory authorities that matter for the clients we serve. It is a quality-controlled core layer, not a ceiling.

### Under Validation disclaimer

> Under Validation sources are confirmed official UAE regulatory authorities at known official URLs. Technical validation — accessibility testing, extraction quality assessment, and content threshold confirmation — is in progress or pending. These sources are not included in any client monitoring profile until validation is complete and results are documented. Status is updated as validation work progresses.

### Source quality explanation

> A source is not added to any client profile until it passes three checks: it must be accessible from our monitoring infrastructure; the extracted content must meet a minimum quality threshold; and the extraction method (HTML structured content, PDF text extraction, or page snapshot) must be documented with its known limitations. Sources that fail these checks are listed as Limited or Not Yet Active, not silently excluded. Every client receives a source readiness report before their pilot begins showing which sources passed, which have constraints, and what the monitoring scope will be.

### Pricing / founding pilot

> StatuteProof is in early access. These are founding pilot rates — lower than our eventual standard pricing — in exchange for working directly with the first clients to validate source coverage, alert quality, and brief format.
>
> Clients who join the founding pilot will receive advance notice of any pricing changes and priority access to source expansions as they are validated.

### Free Source Readiness Review CTA

> Tell us your regulatory profile. We review the official UAE sources relevant to your business activity, run extraction quality checks, document what is active, what has constraints, and what is not yet accessible — and send you a source readiness report within two business days.
>
> No commitment. No automated output. A reviewed document, specific to your profile.
>
> This is how every StatuteProof pilot begins.

### Contact form intro

> Describe your regulatory profile: your business activity, licence type, and the regulators your team needs to monitor. We review the official sources and respond within one to two business days with a source readiness report — not a sales deck.

### Not legal advice disclaimer

> StatuteProof provides early-warning regulatory intelligence. It is not a law firm and does not provide legal advice. Final compliance decisions require review by qualified legal or compliance professionals. Source limitations, extraction quality constraints, and access restrictions are disclosed on every brief and on the source readiness report.

### Limitations section

**Does StatuteProof cover all UAE regulations?**
> No. StatuteProof monitors validated official UAE financial regulatory sources. Coverage is focused on the core UAE financial regulatory authority layer. The Federal Tax Authority, the Official Gazette, and certain other portals have documented access restrictions and are not currently monitorable from our infrastructure. These limitations are disclosed before any pilot begins.

**Is this legal advice?**
> No. StatuteProof provides early-warning regulatory intelligence — structured briefs that tell you what official sources published and what your regulatory profile may require next. Final compliance decisions require qualified legal review.

**How often do you check sources?**
> Sources are checked on a defined schedule. StatuteProof does not claim real-time monitoring or 24/7 coverage. Each monitoring run produces a timestamped record. If you need to know the current check schedule for a specific source, ask during the source readiness review.

**What happens when a source is inaccessible?**
> If a source is inaccessible during a run, the failure is logged and included in the brief as a FAILED status. It is not silently dropped. If a source consistently fails, it is flagged for human review and may be moved to the Limited or Not Yet Active category.

---

## PART 9 — Claims Safety

| Claim to avoid | Why | Safe alternative |
|----------------|-----|-----------------|
| "Complete UAE coverage" | Not true — FTA, Gazette, e-Laws, TDRA are blocked | "Validated core UAE financial regulatory authority layer — 9 active sources, limitations disclosed" |
| "Comprehensive coverage" | Same as above | "Focused coverage of the official UAE financial regulatory authorities that matter for financial services clients" |
| "Never miss a regulatory change" | Cannot monitor geo-blocked sources; extraction can degrade | "Scheduled monitoring of validated official sources — failures logged and disclosed, not silently dropped" |
| "24/7 monitoring" | Monitoring runs on a schedule, not continuously | "Scheduled monitoring runs — frequency disclosed in source readiness review" |
| "15-minute alerts" | No real-time infrastructure | "Alerts delivered via weekly brief after human review — urgent items surfaced for priority review" |
| "Fully automated" | Pipeline ends at human-reviewed weekly brief | "Source monitoring and change detection are automated; alert delivery requires human review and approval" |
| "AI-powered compliance" | AI analysis field currently disabled | Do not mention AI until enabled and validated |
| "Guaranteed delivery" | Telegram can fail; queue is a safety net | "Contact submissions are queued locally and delivered via Telegram — delivery status is confirmed in the submission response" |
| "Live client Telegram delivery" | Telegram client delivery to client profiles is not end-to-end wired | Do not mention client Telegram delivery in outreach until the pipeline is complete |
| "Complete AML coverage" | UAE FIU is active; EOCF is under validation; standalone FIU for all categories not confirmed | "UAE FIU guidance monitored; Executive Office AML/CFT under validation; scope disclosed in source readiness review" |
| "All official UAE sources" | Not true | "Official UAE financial regulatory sources — coverage map, limitations, and tier status disclosed on every pilot" |

---

## PART 10 — Implementation Plan for Codex

### Sprint A — Hero and positioning rewrite

**Goal:** Replace the current hero headline, subheadline, badge, and proof line with the new positioning. Reframe the hero mockup status text.

**Files:** `web/src/components/Hero.jsx`

**Tasks:**
1. Replace badge text with three-part format
2. Replace headline with pain-first version
3. Replace subheadline with product description
4. Replace proof line with validated sources list + quality claims
5. Update hero mockup sidebar text from "9 sources configured" to "UAE monitoring active · 9 sources · 1 CHANGED"
6. Update CTA button label if needed

**Validation:** `npm run build` · `npm run lint` · `git diff --check`

**Do not touch:** backend, .env, nginx, Telegram, sources.json

**Commit message:** `feat(landing): hero pain-first positioning and monitoring session framing`

---

### Sprint B — Coverage map four-tier expansion

**Goal:** Replace the current three-tier coverage table with a four-tier map. Add Under Validation and expand Not Yet Active. Add coverage reframing intro copy.

**Files:** `web/src/components/Coverage.jsx`

**Tasks:**
1. Add UNDER_VALIDATION_SOURCES array with 10–12 named official sources
2. Add fourth tier SourceTable with "Under Validation" badge
3. Rewrite section intro copy to "four-tier coverage map" framing
4. Rewrite "Nine active sources" opening to quality-controlled core layer framing
5. Add exact Under Validation disclaimer text
6. Update Not Yet Active disclaimer to specify geo-blocked reason per source

**Validation:** `npm run build` · `npm run lint` · `git diff --check`

**Do not touch:** sources.json (no source activation), backend, .env

**Commit message:** `feat(coverage): four-tier coverage map with under-validation expansion layer`

---

### Sprint C — Without vs With + pipeline workflow

**Goal:** Add "Without vs With" two-column section. Upgrade HowItWorks copy to show gates and evidence points at each step.

**Files:** `web/src/components/HowItWorks.jsx` · possibly a new `web/src/components/WithoutWith.jsx`

**Tasks:**
1. Create WithoutWith component with two-column layout
2. Add to App.jsx between Problem and HowItWorks
3. Rewrite HowItWorks step descriptions with gate-based framing
4. Update HowItWorks headline to "From official source to evidence-backed brief — seven verified steps"
5. Update status badge display to tie CHANGED/QUALITY_DROP to specific steps

**Validation:** `npm run build` · `npm run lint` · `git diff --check`

**Do not touch:** backend, data pipeline, sources.json

**Commit message:** `feat(workflow): without-vs-with section and pipeline gate framing`

---

### Sprint D — Evidence brief sample + dashboard preview upgrade

**Goal:** Add a rendered brief excerpt panel showing a concrete proof block. Upgrade DashboardPreview label and status text to feel operational.

**Files:** `web/src/components/DashboardPreview.jsx` · possibly a new `web/src/components/SampleBrief.jsx`

**Tasks:**
1. Change DashboardPreview header from "9 sources configured" to "UAE monitoring session · 9 sources · last run 14:32 · 1 CHANGED"
2. Change table label from "Sample source set — illustrative" to "UAE monitoring session — illustrative · access and extraction status shown"
3. Create SampleBrief component showing annotated brief excerpt with proof block (source name, URL, timestamp, fingerprint, change status, relevant to, action, disclaimer)
4. Add SampleBrief to page between TrustLayer and Pricing

**Validation:** `npm run build` · `npm run lint` · `git diff --check`

**Do not touch:** appMockData.js source health data (11 rows already correct), backend

**Commit message:** `feat(evidence): sample brief panel and operational monitoring session framing`

---

### Sprint E — Client profiles and pricing polish

**Goal:** Add source chip lists to ConfiguredMonitoring cards. Improve Pricing copy. Remove "From" prefix on paid tiers.

**Files:** `web/src/components/ConfiguredMonitoring.jsx` · `web/src/data/mockData.js`

**Tasks:**
1. Add `primarySources` array to each profile in ConfiguredMonitoring (e.g. `['CBUAE', 'VARA', 'UAE FIU']`)
2. Render source chips in each profile card
3. In mockData.js pricingPlans: change "$99" display to "$99 / month" without "From" prefix; keep Custom Profile as "from $499"
4. Update Pricing section intro copy to "founding pilot" framing from Part 8
5. Add "advance notice of pricing changes" note below pricing cards

**Validation:** `npm run build` · `npm run lint` · `git diff --check`

**Commit message:** `feat(profiles): source chips on client profiles and pricing copy polish`

---

### Sprint F — P0 source validation (no activation without confirmation)

**Goal:** Run test-source validation on all P0 candidate sources. Document results. Add passing sources to sources.json as enabled=false. Show Under Validation sources in Coverage component.

**Tasks (backend/validation — no frontend changes):**
1. `python run.py test-source https://www.uaedataoffice.gov.ae/ --deep`
2. `python run.py document-test https://www.uaedataoffice.gov.ae/`
3. `python run.py test-source https://www.amlcft.ae/ --deep`
4. `python run.py document-test https://www.amlcft.ae/`
5. `python run.py test-source https://www.ia.gov.ae/ --deep`
6. `python run.py test-source https://www.cma.gov.ae/ --deep`
7. `python run.py test-source https://uaelegislation.gov.ae/en/legislations --deep`
8. `python run.py test-source https://www.vara.ae/en/regulation/ --deep`
9. `python run.py test-source https://www.vara.ae/en/publication/ --deep`
10. `python run.py test-source https://www.centralbank.ae/en/publications/ --deep`
11. `python run.py test-source https://www.dfsa.ae/rules-and-materials/consultation-papers --deep`
12. `python run.py document-test https://www.dfsa.ae/rules-and-materials/consultation-papers`

For each result:
- Report: URL, HTTP status, chars extracted, extraction method, verdict (can_monitor / needs_adapter / cannot_monitor)
- If can_monitor AND chars >= 1500: add to sources.json as enabled=false. Do NOT enable.
- If needs_adapter or cannot_monitor: document only. Do not add to sources.json.

After all tests:
- Run: `python -m compileall app run.py -q`
- If sources.json was modified: run `python run.py health`
- Run: `git diff --check`
- Do not commit.

Report format:
```
Source | URL | HTTP | Chars | Verdict | Action taken
```

---

## PART 11 — Final Codex Prompts

### Prompt 1 — Sprint A: Hero rewrite

```
Review web/src/components/Hero.jsx.

Make these changes only. Do not touch any other files.

1. Replace the badge text with:
   "UAE Financial Regulators · Official-Source Monitoring · Human-Reviewed Briefs"

2. Replace the h1 headline with:
   "CBUAE published a circular.
   VARA updated its rulebook.
   DFSA issued a notice.
   Your team needs to know — not find out later."
   (Keep the cyan underline on the last line)

3. Replace the description paragraph with:
   "StatuteProof monitors official publications from UAE's core financial regulatory
   authorities. When a meaningful change is detected, your team receives a structured
   brief — linked to the official source, timestamped, extraction-quality verified,
   and filtered to your regulatory profile."

4. Replace the small secondary paragraph with:
   "Built for UAE fintech, payments, crypto/VASP, AML, and legal teams.
   Not legal advice. Source limitations disclosed on every brief."

5. In the DashboardMockup sidebar, change:
   "Source monitoring active — 9 sources configured"
   to:
   "UAE monitoring active · 9 sources · 1 CHANGED"

6. In the DashboardMockup sidebar jurisdictions, change the count label from
   "9 sources" to "9 validated"

7. Run: npm run build
8. Run: npm run lint
9. Run: git diff --check
10. Do not commit.
11. Report: files changed, build result, lint result.
```

---

### Prompt 2 — Sprint B: Coverage four-tier map

```
Review web/src/components/Coverage.jsx.

Make these changes only. Do not touch any other files.
Do not edit sources.json. Do not activate any sources.

1. Add a UNDER_VALIDATION_SOURCES array before the component:
   [
     { source: 'UAE Data Office (PDPL)', notes: 'Personal data protection supervisory authority. Validation in progress.' },
     { source: 'Executive Office for AML/CFT (EOCF)', notes: 'National AML/CFT policy and typologies. Validation in progress.' },
     { source: 'Insurance Authority', notes: 'Insurance sector regulator. Validation in progress.' },
     { source: 'Capital Market Authority (CMA)', notes: 'Post-Federal Decree-Law No. 32 of 2025 securities regulator. URL and structure under validation.' },
     { source: 'VARA — Publications sub-page', notes: 'Item-level VARA rulebook/publications detection. Adapter in development.' },
     { source: 'CBUAE — Circulars sub-page', notes: 'Item-level CBUAE circular detection. Adapter in development.' },
     { source: 'DFSA — Consultation papers', notes: 'Forward-looking DFSA regulatory signal. Validation in progress.' },
     { source: 'ADGM FSRA — Regulatory notices', notes: 'FSRA-specific regulatory notices. Validation in progress.' },
     { source: 'DIFC Data Protection Commissioner', notes: 'DIFC data protection law publications. Validation in progress.' },
     { source: 'DMCC Crypto Centre', notes: 'DMCC free zone crypto compliance regulations. Validation in progress.' },
   ]

2. Add a fourth SourceTable section after the Not Yet Active section using these columns:
   { key: 'source', label: 'Source' }, { key: 'notes', label: 'Status' }

3. The fourth section header: "Under Validation — official sources, technical validation in progress"
   Badge variant: "blue"

4. After the fourth table, add this disclaimer paragraph:
   "Under Validation sources are confirmed official UAE regulatory authorities.
   Technical validation — accessibility, extraction quality, and content threshold —
   is in progress. These sources are not included in any client scope until
   validation is complete."

5. Change the section intro copy from:
   "Nine active sources. Three with documented access limitations. Every limitation
   is disclosed before any pilot begins."
   to:
   "StatuteProof uses a four-tier coverage map. Nine active sources form the
   validated core UAE financial regulatory authority layer. Each active source
   has passed extraction quality checks before activation. Three sources have
   documented constraints. A growing set of official sources is under technical
   validation. Sources with geo-restrictions or access failures are disclosed
   honestly — never hidden."

6. Run: npm run build
7. Run: npm run lint
8. Run: git diff --check
9. Do not commit.
10. Report: files changed, build result, lint result.
```

---

### Prompt 3 — Sprint C: Without vs With section

```
Create a new file: web/src/components/WithoutWith.jsx

Content: a two-column "Without StatuteProof / With StatuteProof" comparison section.

Left column (Without):
- Manual review of nine regulator portals — weekly at best
- No structured record of what was checked or when
- No diff between last week and this week
- Alerts come from news aggregators, not official sources
- Relevance to your licence type is your problem
- Compliance review happens reactively, under time pressure
- No audit trail of when the change was discovered

Right column (With):
- Scheduled monitoring of validated official UAE regulatory sources
- Timestamped run record per source per check
- Normalized snapshot diff — UNCHANGED · CHANGED · QUALITY_DROP
- Alert drafts linked to official source URL and extraction proof
- Profile-matched relevance — VARA alerts go to VASP profiles only
- Human-reviewed brief before delivery
- Full audit trail: source → diff → alert draft → approval → brief

Section header: "The difference"
Subheader: "From manual portal checking to evidence-backed regulatory intelligence"

Style: dark background (#07111F), two columns side-by-side on desktop, stacked on mobile.
Left column: slate/red treatment for the Without items
Right column: emerald/cyan treatment for the With items

Then open web/src/App.jsx (or wherever sections are composed) and add
<WithoutWith /> between <Problem /> and <HowItWorks />.

Run: npm run build
Run: npm run lint
Run: git diff --check
Do not commit.
Report: files changed, build result, lint result.
```

---

### Prompt 4 — Sprint D: Dashboard preview operational reframe

```
Review web/src/components/DashboardPreview.jsx.

Make these changes only. Do not touch any other files.

1. In the dark header card, change:
   "Source monitoring active — review period"
   to:
   "UAE monitoring session — active"

2. In the same card, change:
   "9 sources configured · 1 CHANGED · 2 UNCHANGED · Source proof attached"
   to:
   "9 validated sources · last run 14:32 UTC · 1 CHANGED · 8 UNCHANGED · review queue open"

3. Change the table label below from:
   "Sample source set — illustrative. Access status and extraction quality shown.
   Pilot sources confirmed after source review."
   to:
   "Illustrative UAE monitoring session · 9 sources checked · access status and
   extraction quality shown · pilot source set confirmed after source readiness review"

4. Change the section title from:
   "What the source readiness report shows"
   to:
   "What a monitoring session looks like"

5. Change the section badge from:
   "Source Readiness Review"
   to:
   "Monitoring Session"

6. Run: npm run build
7. Run: npm run lint
8. Run: git diff --check
9. Do not commit.
10. Report: files changed, build result, lint result.
```

---

### Prompt 5 — Sprint E: Pricing and client profiles

```
Review web/src/data/mockData.js and web/src/components/ConfiguredMonitoring.jsx.

Task 1 — mockData.js:
In pricingPlans, for the 'Founding Pilot' plan:
  Change price from '$99' to '$99'
  Change desc to:
  "5–8 validated official sources matched to your regulatory profile. Weekly
  evidence-backed brief with source proof, delta status, and extraction quality
  on every alert. Founding pilot rate — in exchange for working directly with
  you to validate coverage and brief format."

In pricingPlans, for the 'Custom Profile' plan:
  Change price from '$499' to '$499+'
  Add period: '/ month from'

Task 2 — ConfiguredMonitoring.jsx:
In the PROFILES array, add a primarySources field to each profile:
  Crypto/VASP: ['VARA', 'CBUAE', 'UAE FIU']
  Payments/fintech: ['CBUAE', 'UAE FIU', 'Ministry of Finance']
  DIFC: ['DFSA', 'DIFC Laws', 'UAE FIU']
  ADGM: ['ADGM / FSRA', 'UAE FIU']
  AML/compliance: ['UAE FIU', 'CBUAE', 'Ministry of Economy']
  Capital markets/law: ['UAE Legislation Portal', 'DIFC Laws', 'Ministry of Finance']

Render these as small pill/chip elements at the top of each profile card,
before the title, in a flex-wrap row with a muted label "Primary sources:".
Style them as small rounded badges matching the existing design system.

Run: npm run build
Run: npm run lint
Run: git diff --check
Do not commit.
Report: files changed, build result, lint result.
```

---

### Prompt 6 — Sprint F: P0 source validation (backend only)

```
Run these validation commands in order. Do not edit any frontend files.
Do not activate any source without confirming the test-source result first.
Record all results.

1. python run.py test-source https://www.uaedataoffice.gov.ae/ --deep
2. python run.py document-test https://www.uaedataoffice.gov.ae/
3. python run.py test-source https://www.amlcft.ae/ --deep
4. python run.py document-test https://www.amlcft.ae/
5. python run.py test-source https://www.ia.gov.ae/ --deep
6. python run.py test-source https://www.cma.gov.ae/ --deep
7. python run.py test-source https://uaelegislation.gov.ae/en/legislations --deep
8. python run.py test-source https://www.vara.ae/en/regulation/ --deep
9. python run.py test-source https://www.vara.ae/en/publication/ --deep
10. python run.py test-source https://www.centralbank.ae/en/publications/ --deep
11. python run.py test-source https://www.dfsa.ae/rules-and-materials/consultation-papers --deep
12. python run.py document-test https://www.dfsa.ae/rules-and-materials/consultation-papers

For each result:
- Report: URL, HTTP status, chars extracted, extraction method, verdict
- If can_monitor AND chars >= 1500: add to sources.json as enabled=false. Do NOT enable.
- If needs_adapter or cannot_monitor: document only. Do not add to sources.json.

After all tests:
- Run: python -m compileall app run.py -q
- If sources.json was modified: run python run.py health
- Run: git diff --check
- Do not commit.

Report format:
Source | URL | HTTP | Chars | Verdict | Action taken
```

---

## PART 12 — Final Verdict

### 1. Can the site be made professional without fake coverage?

Yes, completely. The product is real, the sources are real, the pipeline is real. The gap is entirely in framing and visual communication, not in substance. Nine validated official UAE financial regulatory authorities is a commercially strong coverage set for the target clients. The issue is that the site presents it as a technical fact rather than as a quality argument. Reframing — without changing a single source or adding any fake coverage — makes the product feel substantially more serious.

### 2. Fastest path to professional

In order of impact per hour of work:

1. **Hero rewrite** (Sprint A) — one component, ~30 minutes, changes the first impression entirely
2. **Coverage four-tier map** (Sprint B) — adds Under Validation layer, transforms "9 sources" into an expanding coverage map, ~1–2 hours
3. **Without vs With section** (Sprint C) — makes the value proposition felt rather than described, ~1–2 hours
4. **Dashboard preview reframe** (Sprint D) — changes two text strings, makes the mockup feel operational rather than illustrative, ~20 minutes

These four sprints alone transform the site from "early-stage scraper" to "professional compliance intelligence platform" without touching a single source, backend file, or deployment configuration.

### 3. Best balance of visual strength, honest coverage, and technical quality

The current site is honest and technically accurate. The upgrade required is not to the honesty or the technical quality — it is to the storytelling. The evidence trail (TrustLayer), the alert proof concept, the four-step contact intake, and the client profile cards are all genuinely differentiated features. They need to be surfaced earlier and shown more concretely. A rendered brief excerpt, a concrete proof block, a "monitoring session" label instead of "illustrative sample" — these changes cost nothing technically and gain everything commercially.

The under-validation expansion map is the most important addition. It transforms the site from a product with 9 sources into a product with 9 validated active sources, 3 limited sources, 10+ under validation, and an honest disclosure of what is geo-blocked. That is the map of a serious platform, not a scraper.

### 4. What should be done before serious outreach

In strict priority order:
1. Sprint A (hero rewrite) — the first impression must be fixed before any link is shared
2. Sprint B (coverage four-tier map) — Coverage section is the first thing a sophisticated buyer will navigate to
3. Sprint F P0 validation run — before adding any Under Validation sources to the website, confirm their URLs are real and accessible
4. Sprint C (Without vs With) — makes the transformation concrete
5. Sprint D (dashboard reframe) — small change, meaningful impact
6. Confirm the free source readiness review workflow is operational end-to-end (contact form → Telegram → manual response within 48 hours)

Do not start outreach before Sprint A and B are live and Sprint F has confirmed the Under Validation URL list is accurate.
