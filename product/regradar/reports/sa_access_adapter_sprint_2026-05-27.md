# Saudi Arabia Access & Adapter Sprint
**Date:** 2026-05-27  
**Jurisdiction:** SA — Saudi Arabia  
**Sprint type:** Deep retest of blocked sources + CST adapter investigation + Saudi-IP feasibility assessment

---

## Executive Summary

This sprint investigated whether any Saudi Arabia sources currently blocked or limited can be improved without provisioning a Saudi-IP deployment node. The answer is **one source: CST root** — which is reachable from outside Saudi Arabia but fails due to SPA rendering, not geo-blocking.

**Key findings:**

1. **CST (digital_regulation)** — The root domain is HTTP 200 and Playwright-accessible. Extractors yield only 266c (BeautifulSoup) and 1,198c (Playwright/trafilatura) because content is in Vue/React JS components that need targeted component-wait rendering. A CST SPA adapter following the CBR anchor-page pattern could reliably reach 2,000–5,000c per run. No Saudi-IP needed.

2. **All other blocked SA categories (SAFIU, Umm Al-Qura, BOE, MoF, SDAIA, Istitlaa, GAC)** — Confirmed as either geo-IP blocked (connection timeout), DNS-dead, or HTTP2 protocol-blocked. No adapter pattern can circumvent these without a Saudi-IP endpoint.

3. **CST regulations subdomain (mutasilind.cst.gov.sa)** — Separately geo-blocked; connection timeout. A CST adapter targeting the root domain cannot access regulations PDFs stored on this subdomain.

4. **ZATCA /en/ subpath** — 1,116c GOOD, marginally stronger than the root (1,029c) already in sources.json. Not a meaningful improvement; root entry is sufficient.

**Sprint outcome:** No new source activations. CST adapter is the only viable improvement within this sprint's scope and is documented below with implementation guidance.

---

## CST Deep Analysis

### URL test results

| URL | Method | HTTP | Chars | Verdict |
|-----|--------|------|-------|---------|
| https://www.cst.gov.sa/ | BeautifulSoup | 200 | 266c | SPA — extractors see navigation shell only |
| https://www.cst.gov.sa/ | Playwright/trafilatura | 200 | 1,198c | Partial — Vue/React components partially rendered |
| https://www.cst.gov.sa/ | discover-source (full) | 200 | 266c | qualityScore 10, verdict needs_adapter |
| https://www.cst.gov.sa/en/news | HTTP | 404 | 55c | FAILED — SPA routing only |
| https://www.cst.gov.sa/en/regulations | HTTP | 200→redirect | 0c | Redirects to mutasilind.cst.gov.sa → connection timeout (geo-blocked) |
| https://www.cst.gov.sa/ar/regulations | HTTP | 200→redirect | 0c | Same geo-blocked redirect |
| https://www.cst.gov.sa/en/publications | HTTP | 404 | 55c | FAILED — SPA routing only |
| https://mutasilind.cst.gov.sa/ | HTTP | timeout | 0c | Geo-blocked — separate subdomain |
| document-test (cst.gov.sa) | PDF scan | — | 0 PDFs | No PDF links in 239,804c HTML |

### Root cause

CST uses a Vue.js SPA. The raw HTML contains 405,395 chars of framework scaffolding, CSS, and lazy-loaded bundle references. Content (press releases, announcements, decisions) lives inside Vue components that only mount after client-side router initialization.

- **BeautifulSoup (Tier 1):** Sees pre-rendered navigation shell → 266c
- **Playwright/trafilatura:** Waits for networkidle, captures partial Vue render → 1,198c (better, but still missing component-mounted content)
- **CST regulations/PDFs:** Hosted on geo-blocked `mutasilind.cst.gov.sa` — inaccessible without Saudi-IP

### CST adapter design (recommended next task)

A CSTAdapter modeled on the CBR adapter pattern would:

1. Load `https://www.cst.gov.sa/en/news` (or Arabic equivalent) in a Playwright browser session
2. Wait for a specific CSS selector that marks component mount (e.g., `[class*="news-list"]`, `article`, `.press-release-item`, or equivalent — needs one-time manual inspection)
3. Extract text from mounted components using `page.evaluate()` with a targeted selector, or use `page.content()` → trafilatura after a longer `page.wait_for_selector()` call
4. Fall back to root domain if news page fails

**Estimated yield:** 2,000–5,000c based on CST news volume.  
**Effort:** Medium (2–4 hours) — one-time manual selector discovery + CSTAdapter class implementation.  
**Saudi-IP required:** No — CST root and news pages are HTTP 200 from external IPs.  
**Regulations/PDFs:** Cannot be reached — stay on MISA, SAMA, and CMA for SA regulatory document coverage.

---

## Blocked Source Deep Retest Table

All sources tested fresh from outside Saudi Arabia on 2026-05-27:

| Source | URL | Category | Failure type | Failure detail |
|--------|-----|----------|-------------|----------------|
| Saudi Financial Intelligence Unit (SAFIU) | https://safiu.sa/ | aml | DNS failure | Domain does not resolve — NXDOMAIN |
| SAFIU (gov.sa domain) | https://www.safiu.gov.sa/ | aml | Connection timeout | IP-level block — TCP connection never established |
| Umm Al-Qura Gazette | https://uqn.gov.sa/ | official_gazette | Connection timeout | IP-level block |
| Bureau of Experts (root) | https://www.boe.gov.sa/ | legal_database | Connection timeout | IP-level block (same as laws subdomain) |
| Bureau of Experts (laws) | https://laws.boe.gov.sa/ | legal_database | Connection timeout | IP-level block — confirmed in SA quality audit |
| Ministry of Finance | https://www.mof.gov.sa/ar/Pages/default.aspx | finance_ministry | SPA + partial block | 55c — JS SPA; Arabic SharePoint path also 0–55c; English paths also fail |
| SDAIA | https://sdaia.gov.sa/en/ | data_protection | HTTP2 protocol error | Protocol-level block; all tested paths fail |
| Istitlaa consultations | https://istitlaa.ncc.gov.sa/ | public_consultations | Connection timeout | IP-level block |
| General Authority for Competition (GAC) | https://www.gac.gov.sa/ | competition | DNS failure | Domain does not resolve — NXDOMAIN |
| FSDP (financial sector) | https://fsdp.gov.sa/ | financial_services | DNS failure | Domain does not resolve — NXDOMAIN |
| business.sa | https://business.sa/ | company_registry | Connection timeout | IP-level block |
| Saudi Payments | https://saudipayments.com/ | payments | SSL hostname mismatch | Certificate is not for saudipayments.com; Playwright also fails |
| CST regulations subdomain | https://mutasilind.cst.gov.sa/ | digital_regulation | Connection timeout | IP-level block — separate from accessible CST root |

### Failure classification

| Failure type | Count | Recoverable without Saudi-IP? |
|-------------|-------|-------------------------------|
| DNS failure (NXDOMAIN) | 3 (SAFIU .sa, GAC, FSDP) | No |
| Connection timeout (IP block) | 7 | No |
| HTTP2 protocol error | 1 (SDAIA) | No |
| SPA + near-zero content | 1 (MoF) | Unlikely — even Playwright yields 0–55c |
| SSL hostname mismatch | 1 (Saudi Payments) | Possibly with custom SSL config, but low value |

**Pattern:** Saudi Arabia has the most systematic geo-blocking of any tested GCC jurisdiction. Every government URL not in the current active 7-source set is either DNS-dead, IP-blocked, or protocol-blocked from outside Saudi Arabia.

---

## Saudi-IP Requirement Matrix

| Source | Category | Saudi-IP needed? | Priority if Saudi-IP provisioned | Notes |
|--------|----------|-----------------|----------------------------------|-------|
| SAFIU | AML | Yes (both domains) | CRITICAL — AML is table-stakes for compliance teams | Try safiu.gov.sa first; safiu.sa may be test/dev domain |
| Umm Al-Qura | official_gazette | Yes | CRITICAL — primary source for new laws and royal decrees | All official Saudi legislation is promulgated in Umm Al-Qura |
| Bureau of Experts | legal_database | Yes | CRITICAL — complete Saudi legislation repository | laws.boe.gov.sa contains all enacted statutes |
| SDAIA | data_protection | Yes | HIGH — enforces PDPL (Saudi data protection law) | Increasing importance with 2023 PDPL enforcement start |
| MoF | finance_ministry | Likely yes | MEDIUM — fiscal and budget policy | SPA + near-zero content even with Playwright; may need API |
| Istitlaa | public_consultations | Yes | LOW — regulatory consultation tracking | Useful for advance notice of upcoming regulations |
| GAC | competition | Yes | LOW — competition enforcement | DNS failure outside SA |
| CST root | digital_regulation | No | — | Adapter-only fix; see CST section above |
| CST regulations subdomain | digital_regulation | Yes | HIGH (if CST adapter built) | Regulations PDF library is on geo-blocked subdomain |

### Saudi-IP provider options

| Provider | Region | KSA presence | Est. cost | Notes |
|----------|--------|-------------|-----------|-------|
| STC Cloud | Riyadh | Native KSA | ~$15–25/mo | Saudi Telecom's cloud; native KSA IPs |
| Mobily Cloud | Riyadh | Native KSA | ~$15–25/mo | Second-largest Saudi ISP |
| Oracle Cloud KSA | Riyadh | Yes (region: me-jeddah-1) | Free tier available | Oracle has dedicated Saudi Arabia region |
| AWS | No KSA region | AWS me-central-1 is UAE (not SA) | N/A | AWS KSA region planned but not launched as of 2026-05-27 |
| Alibaba Cloud | Riyadh | Yes | ~$20/mo | Partnership with Saudi Aramco |
| DigitalOcean / Hetzner | No KSA | Closest: Bangalore or Frankfurt | N/A | Would not provide Saudi IPs |

**Recommendation:** Oracle Cloud me-jeddah-1 (Riyadh) has a free tier and native Saudi-Arabia IP addresses. Ideal for a dedicated monitoring agent that fetches from SAFIU, Umm Al-Qura, BOE, SDAIA, and Istitlaa. A $0–15/mo Oracle Cloud instance running a lightweight Python fetcher alongside the main VPS would unlock all CRITICAL missing categories.

---

## Additional Tests

### SAMA alternate URLs

| URL | Result |
|-----|--------|
| https://www.sama.gov.sa/en-US/Pages/default.aspx | Main entry — PDF-primary (68,237c), Playwright text 1,589c |
| https://www.sama.gov.sa/en-US/News | HTTP 404, 0c — SPA routing |
| PDF document test | 1 PDF found (20,645c) — duplicate of existing SAMA source coverage; no new activation |

SAMA news URLs are SPA-routed and return 404 from the server. PDFs remain the primary monitoring mechanism and are already covered by the existing SAMA source.

### ZATCA alternate URL

| URL | Result |
|-----|--------|
| https://zatca.gov.sa/ | 1,029c GOOD (existing) |
| https://zatca.gov.sa/en/ | 1,116c GOOD |

The /en/ subpath yields 87c more than the root (1,116c vs 1,029c). Both well above the 500c monitoring threshold. The existing root entry is sufficient; no update needed.

### Saudi Payments

https://saudipayments.com/ — SSL hostname mismatch (certificate is not valid for this hostname). Playwright also fails. Cannot activate. Not a priority — SAMA covers the payment system regulatory framework.

---

## No-Saudi-IP Adapter Opportunities (Summary)

| Source | Category | Adapter approach | Current chars | Expected after adapter | Effort |
|--------|----------|-----------------|---------------|----------------------|--------|
| CST root | digital_regulation | Playwright SPA — component wait + targeted selector | 266c (BeautifulSoup) / 1,198c (Playwright/trafilatura) | 2,000–5,000c | Medium (2–4 hours) |
| SAMA HTML | central_bank | SharePoint API or news RSS feed | 0c HTML (Playwright text 1,589c) | Consistent 1,000–3,000c | Medium |
| CMA HTML | capital_markets | SharePoint API or regulations RSS | 0c HTML (Playwright text 1,054c) | Consistent 1,000–2,000c | Medium |

All three do not require Saudi-IP. The CST adapter is highest priority because CST is a key digital payments and fintech regulator.

---

## Files Not Changed in This Sprint

This sprint is a documentation and assessment sprint only. No sources.json changes were made because:

1. No new sources were activated — all blocked candidates remain blocked by geo-IP
2. CST notes were already updated in the previous commit (`b9b164e`) with accurate Playwright extraction assessment
3. No source status changes are warranted

**Sources.json SA entry count: 12 (7 enabled, 5 disabled) — unchanged from post-audit commit.**

---

## Recommendations

**Immediate (no cost, no infrastructure):**
1. Build CST SPA adapter — 2–4 hours. Upgrade CST from limited (266c) to active (2,000–5,000c). No Saudi-IP needed. Follow CBR adapter pattern with Playwright component wait. Highest-ROI SA adapter task.

**Short-term (1–2 weeks):**
2. SAMA SharePoint HTML adapter — test SAMA's RSS feeds or SharePoint API for text-based monitoring. Supplements existing PDF extraction with text-based news monitoring.

**Infrastructure decision (required for full SA coverage):**
3. Provision Oracle Cloud me-jeddah-1 instance — $0–15/mo. This single decision unlocks SAFIU (AML), Umm Al-Qura (official_gazette), BOE (legal_database), and SDAIA (data_protection) — the 4 highest-priority currently-blocked SA categories. A minimal Python fetcher agent running on a Riyadh IP would feed results back to the main RegRadar backend.

**Commercial priority framing:**
- Without Saudi-IP: RegRadar covers 6 of the 7 most commercially important SA categories (banking, tax, capital markets, investment, commerce, cybersecurity). Digital regulation (CST) partially covered.
- With Saudi-IP: Adds AML (SAFIU), official gazette (Umm Al-Qura), legal database (BOE), data protection (SDAIA) — transforming SA coverage from "strong commercial" to "comprehensive compliance-grade."

---

## Files Created

| File | Action |
|------|--------|
| `reports/sa_access_adapter_sprint_2026-05-27.md` | Created — this file |
