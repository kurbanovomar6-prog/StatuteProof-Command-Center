# RegRadar Source Coverage Standard

**Version:** 1.0  
**Language:** English (primary)  
**Scope:** Internal engineering and product reference

---

## Disclaimer

> RegRadar coverage reflects technical monitoring readiness and source quality. It is not a guarantee of legal completeness and should not be treated as legal advice.

---

## 1. What "Coverage" Means in RegRadar

Coverage in RegRadar refers to the technical ability to monitor a regulatory source and extract meaningful content changes. A market is considered "covered" when RegRadar can:

1. Reach the official regulatory URL reliably.
2. Extract a meaningful amount of text content (HTML or PDF).
3. Detect content changes between monitoring runs.
4. Assign a risk level and generate a structured AI brief.
5. Deliver alerts via Telegram or another configured channel.

Coverage does **not** mean:
- Complete legal coverage of all regulations in a jurisdiction.
- Real-time monitoring of every regulatory publication.
- Legal advice or compliance sign-off.
- Guaranteed delivery of every regulatory update within a specific time window.

---

## 2. Source Statuses

### active
The source is enabled and monitored on schedule. Extraction quality is confirmed and the source produces usable content changes. Health checks pass reliably.

### limited
The source is enabled but extraction quality is reduced. Common reasons include JavaScript-heavy portals, partial geo-restrictions, or low content volume. Alerts may still be generated but with lower confidence.

### mapped
The source is documented in the source registry and has been manually reviewed, but is not yet enabled for active monitoring. Mapped sources require validation via `test-source` before activation.

### disabled
The source is known and documented but is not enabled. Reasons include failed extraction, geo-blocking, auth requirements, or deliberate exclusion pending adapter development.

### candidate
The source is listed in `source_candidates.json` as a planning-level entry. It has not been tested yet. No monitoring is running. Candidates must go through the validation workflow before moving to active status.

---

## 3. Why RegRadar Does Not Claim Full Legal Completeness

Official regulatory information is published across many channels:
- Official gazettes (not always machine-readable)
- Regulator websites (sometimes JS-heavy, geo-restricted, or auth-required)
- Government legal portals (content fragmented across sub-domains)
- PDF publications (may require OCR or custom parsers)
- Press releases and circulars (often unpredictable URL patterns)

RegRadar monitors the sources it can reliably access. For many jurisdictions, important regulatory updates are published on portals that require custom adapters, authentication, or manual review workflows.

RegRadar communicates this honestly: every source has an explicit status, and coverage limitations are documented rather than hidden.

---

## 4. How Sources Are Validated

New sources go through the following workflow:

1. **Candidate registration** — Source is added to `data/source_candidates.json` with metadata and notes.
2. **Test-source run** — `python run.py test-source <url>` checks HTML accessibility, PDF availability, RSS/sitemap, and content quality. Returns a verdict: `can_monitor`, `needs_adapter`, or `cannot_monitor`.
3. **Extraction review** — Output is reviewed for content quality, extraction reliability, and change detection signal quality.
4. **Source pack documentation** — Validated sources are documented in a source pack report (e.g., `reports/ae_source_pack_*.md`).
5. **Activation** — Approved sources are added to `sources.json` with `enabled: true` only after passing steps 2–4.

Sources are **never auto-activated** from `source_candidates.json`.

---

## 5. How PDF and Document Extraction Affects Source Quality

RegRadar has multi-layer extraction:

- **HTML extraction** — standard for most sources. Works well when regulators publish press releases or updates as web pages.
- **PDF extraction** — used for official publications, guidelines, circulars and consultation papers. RegRadar uses PyMuPDF and custom document extractors.
- **SPA / JavaScript rendering** — requires Playwright-based extraction for JavaScript-heavy portals. Higher cost and latency; used only when HTML extraction fails.

Source quality is affected when:
- PDFs are image-only (no text layer) — OCR may be needed.
- Content is in protected PDFs (encryption).
- Portal requires authentication before serving content.
- Content is served dynamically without server-side rendering.

When extraction quality is reduced, the source receives a `limited` status and health score.

---

## 6. How Adapters Work

An adapter is custom extraction logic written for a specific source when standard HTTP + HTML/PDF extraction is insufficient.

Adapters are built for:
- JavaScript SPAs that do not serve meaningful content without rendering.
- Portals with session-based navigation.
- Geo-restricted sources requiring proxy or VPN routing.
- Sources with unusual PDF structures requiring custom parsing.

Adapter development is logged in the adapter queue: `python run.py adapter-queue`.

Adapters are not automatic. They require engineering time and are prioritized based on source importance and client demand.

---

## 7. How Market Tiers Are Determined

Markets are tiered by a combination of factors — not just country size:

| Factor | Weight |
|--------|--------|
| Compliance pain and regulatory activity level | High |
| Fintech / payment / crypto / legal market size | High |
| Realistic ability to sell as a small product | High |
| Client budget expectations | High |
| RegRadar technical readiness | Medium |
| Availability of official public sources | Medium |
| Cross-border relevance | Medium |
| Undercovered-market advantage | High |

Full tier structure is documented in `data/market_strategy.json`.

---

## 8. Why English Is the Default Language

RegRadar's primary audience is international compliance and legal teams — not exclusively local-market teams. Key reasons English is the default:

- International compliance buyers (legal firms, fintech companies, consultants) communicate in English.
- English-language briefs are usable across multi-jurisdiction teams.
- B2B sales in the GCC, Turkey and Kazakhstan increasingly happen in English.
- Positioning RegRadar as a Russian-language product limits the addressable market significantly.

Official sources are in local languages (Arabic, Turkish, Kazakh, Uzbek, Azerbaijani, Georgian etc.). RegRadar extracts these and generates AI compliance briefs in the client's chosen language — English by default.

---

## 9. How Multilingual Briefs Work

RegRadar separates **source language** from **brief language**:

- **Source language** — the language of the official regulatory document. Can be any language.
- **Brief language** — the language of the AI-generated compliance summary. Configurable per workspace.

Brief language options:
- **English** (default) — Full AI analysis output in English.
- **Russian** — Optional; used for CIS-facing teams.
- **Both** — Dual-language output for bilingual teams.

Brief language is configured in the workspace Settings page under "AI Brief Settings."

Source language does not need to match brief language. RegRadar reads Turkish content from TCMB and delivers the compliance brief in English.

---

## 10. Why Russian Is Optional, Not Primary

Russian is available as an output language for AI briefs because many compliance teams in Central Asia, the Caucasus and CIS use Russian as an internal working language.

However, Russian must not be the primary brand language of RegRadar because:
- It limits the international buyer pool (GCC, Turkey, APAC, Western clients).
- It positions RegRadar as a CIS-only product when the target is much broader.
- It may reduce trust with UAE, Saudi Arabia and Malaysia-based buyers.
- It is not the language of the largest and most commercially valuable target markets.

Russian is treated as: optional brief output language, available to clients who need it.

---

## 11. How Client-Specific Source Profiles Work

Each workspace in RegRadar has a monitoring profile consisting of:
- Target markets (jurisdictions)
- Industry focus (fintech, banking, crypto, legal, payments)
- Custom sources added by the workspace

The monitoring profile filters:
- Alerts shown in the dashboard
- Sources shown in the Source Library
- Reports generated for the workspace
- AI briefs generated per run

Custom sources submitted by a workspace go through the source testing workflow (`/api/source-test`) before being saved. Sources that pass testing can be added to the workspace's custom source profile.

---

## 12. How to Interpret Coverage Score

The coverage score (0–100) is a composite metric per market:

| Score | Label | Meaning |
|-------|-------|---------|
| 0–40 | Weak | Few official sources, limited extraction quality |
| 41–60 | Minimum viable | Core sources active, some categories missing |
| 61–75 | Usable | Most key regulators covered, some limitations |
| 76–89 | Strong | Broad official source coverage, good extraction |
| 90–100 | Premium | Near-complete official coverage, high extraction quality |

Coverage score reflects:
- Number of active official sources
- Extraction quality per source
- Categories covered vs. missing
- Health check pass rate

The score is not a legal quality rating.

---

## 13. What Disclaimers Should Be Shown to Clients

Always display:

1. **Legal disclaimer** — "AI compliance briefs are generated for informational purposes only. They do not constitute legal advice and should not be relied upon as a substitute for qualified legal counsel."

2. **Coverage disclaimer** — "RegRadar coverage reflects technical monitoring readiness and source quality. It is not a guarantee of legal completeness."

3. **Source status** — Each source shows its status (Active / Limited / Needs Adapter / Candidate). Clients can see which sources are being monitored.

4. **Secondary sources** — Sources classified as secondary intelligence (law firm updates, consulting analysis) are labeled as such. They are not official regulatory sources and require verification against official regulators before compliance action.

5. **Official sources first** — Official government regulator sources are always prioritized over secondary intelligence sources.

---

*RegRadar source coverage standard — English-first regulatory intelligence platform.*
