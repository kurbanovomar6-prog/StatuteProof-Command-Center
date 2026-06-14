# UAE 60-Source Candidate Discovery

## 1. Executive Summary

StatuteProof now has a research-only candidate map for a professional UAE source pack:

- 60 official or officially linked candidate endpoints.
- 40 high-priority candidates for the first professional baseline path.
- 6 rejected examples documented so the no-garbage boundary is explicit.
- 0 new active sources added to `sources.json` in this discovery step.

This is not a “60 validated sources” claim. It is a controlled source intelligence map that must pass no-save extraction, evidence/baseline, and legal-safe claim gates before customer-facing coverage changes.

Current public truth remains:

**13 enabled UAE sources; 9 readiness-supported; 4 under extraction remediation.**

## 2. Discovery Method

Sources were selected from official or officially linked UAE regulator/government domains, the current registry, prior DFSA/source-readiness reports, and focused web/domain checks. Basic direct fetch checks also reinforced that some official pages may be blocked, JavaScript-heavy, selector-sensitive, or shallow; those are candidates/remediation, not ready coverage.

Selection rules:

- UAE official or officially linked only.
- Relevant to MLROs, CCOs, compliance managers, VASPs, DIFC/ADGM firms, fintech/payment firms, legal counsel, or compliance consultants.
- No law firms, blogs, LinkedIn posts, news commentary, search-result pages, private portals, login/CAPTCHA/paywall pages, or wrong-country regulators.
- Generic homepages are allowed only as broad anchors; professional coverage should prefer specific subpages.

## 3. Machine-Readable Candidate File

Candidate file:

`product/regradar/config/uae_source_candidates.json`

The file includes:

- current customer-facing truth;
- status definitions;
- 60 candidates;
- top-40/top-60 flags;
- official status;
- parsing risk;
- buyer relevance;
- initial candidate/remediation/readiness-supported status;
- rejected source examples.

The file is research/configuration only. It does not activate monitoring.

## 4. Candidate Count By Regulator

| Group | Candidate count | Top-40 count | Notes |
|---|---:|---:|---|
| VARA | 8 | 7 | Strong VASP relevance; several rulebook URLs require browser validation. |
| CBUAE | 10 | 7 | Core banking/payment/AML relevance; WAF risk must be handled conservatively. |
| UAE FIU | 5 | 3 | Highest MLRO relevance; homepage remains shallow/remediation. |
| DFSA / DIFC | 12 | 7 | High-value for DIFC firms, but DFSA remains remediation until strict checks pass. |
| ADGM / FSRA | 10 | 8 | Strong ADGM/FSRA coverage path; many subpages need no-save validation. |
| SCA | 7 | 5 | UAE SCA only; do not confuse with Saudi CMA. Selector remediation likely. |
| Federal AML / tax / legislation | 8 | 3 | Useful expansion set; some tax/legal pages are consultant/enterprise scope. |
| Rejected examples | 6 | n/a | Wrong-country, commentary, social/search/private portal examples. |

## 5. Proposed Top 60

The proposed top 60 are all candidates in `product/regradar/config/uae_source_candidates.json` with `top_60_candidate: true`.

They should be treated as:

- discovered official-source candidates;
- not active monitoring;
- not evidence-confirmed;
- not monitoring-ready;
- not marketable as “60 sources” until no-save validation and later activation/baseline gates pass.

## 6. Proposed Top 40

The proposed top 40 are candidates with `top_40_candidate: true`.

This is the recommended first validation path because it focuses on:

- VARA enforcement/rulebook/AML surfaces;
- CBUAE regulations, AML/CFT, payments, consultations;
- UAE FIU publications/goAML/laws;
- DFSA/DIFC high-value remediation targets;
- ADGM/FSRA rulebook/guidance/notices/enforcement;
- SCA decisions/laws/regulations/circulars;
- EOCN sanctions/TFS anchor;
- existing readiness-supported broad federal anchors.

## 7. Official Status Notes

Most candidates are on regulator/government domains. The DFSA Thomson Reuters rulebook candidate is marked `officially_linked`, not simply official, because it is a third-party hosted rulebook platform that must remain documented as regulator-linked before adoption.

## 8. Rejected / No-Garbage Examples

Rejected examples include:

- Saudi CMA: wrong country; must not be confused with UAE SCA.
- Law firm UAE AML articles: useful for human context, not default monitoring.
- LinkedIn/social posts: not official source coverage.
- News/commentary sites: not official default sources.
- Private goAML portal: blocked; public guidance only.
- Search result pages: not official source endpoints.

## 9. Known Candidate Risks

| Risk | Affected examples | Handling |
|---|---|---|
| JavaScript-heavy rendering | VARA, DFSA, registers | Use Playwright only when allowed; require selectors and no-save proof. |
| WAF/Cloudflare/basic fetch challenge | CBUAE, DFSA, legislation portals | Mark candidate/remediation unless Source Lab proves stable extraction. |
| Navigation shell | SCA, DFSA legacy URLs, broad portals | Reject or remediation until selector/source model is proven. |
| Shallow homepage | UAE FIU homepage, broad regulator homepages | Prefer specific publication/notice pages. |
| Duplicates | Existing CBUAE/FIU/VARA duplicates | Do not add duplicate active records; split by purpose only. |
| Search/register complexity | DFSA/ADGM public registers | May need source-specific adapter; do not fake readiness. |

## 10. Discovery Verdict

A professional 40-source validation path is realistic, but not marketable yet.

A 60-source UAE candidate map is realistic, but a 60-source ready pack is not yet proven.

The next evidence-producing step is a controlled no-save Source Lab validation batch, starting with high-priority P0 candidates and stopping on repeated access or selector failures.
