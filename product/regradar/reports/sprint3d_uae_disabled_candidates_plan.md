# Sprint 3D — UAE Disabled Candidate Source Plan

## 1. Verdict

- This was config/planning only.
- No sources were activated.
- No entries were added to `sources.json`.
- Five disabled under-validation candidates were added to `data/uae_under_validation_sources.json`.
- Reason for using a separate file: `sources.json` validates a fixed status set and does not support an explicit `under_validation` status without app-code changes. Several preferred candidates also overlap existing active root URLs, so a separate planning registry avoids duplicate active-source ambiguity and prevents accidental monitoring.

## 2. Disabled candidates added

| Source | URL | Category | Status | Enabled | Why selected | Limitation note | Next validation action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ADGM / FSRA main regulatory page | `https://www.adgm.com/financial-services-regulatory-authority` | financial_regulator | under_validation | false | Sprint 3C returned HTTP 200 with usable extracted text; commercially important for ADGM-regulated firms. | Item-level URL structure and repeated-run stability are not validated. | Run 3-5 repeated checks, confirm stable content signature, and map dedicated notices/publication URLs. |
| ADGM / FSRA rulebook | `https://www.adgm.com/financial-services-regulatory-authority` | financial_regulator | under_validation | false | Clean basic access and high value for ADGM firms. | Uses the same FSRA page until a dedicated rulebook listing is mapped; PDF/document dependency unknown. | Map official rulebook location, test document links, and compare repeated extraction output. |
| DIFC Laws item-level validation candidate | `https://www.difc.com/business/laws-and-regulations/` | legal_database | under_validation | false | Sprint 3C returned HTTP 200 with usable extracted text; corrected URL already validated at a basic level. | Base URL already exists as an active source; this is only for item-level validation planning. | Run repeated checks and confirm item-level law/regulation links before any expansion. |
| Ministry of Economy and Tourism AML / DNFBP guidance | `https://www.moet.gov.ae/en/` | aml | under_validation | false | Sprint 3C returned HTTP 200 with strong text volume; commercially useful for AML/DNFBP profiles. | Base MoET URL already exists as active for general Ministry of Economy coverage; AML/DNFBP pages may be PDF-heavy or section-specific. | Locate AML/DNFBP guidance pages or PDFs, then run repeated extraction checks. |
| CBUAE Rulebook | `https://rulebook.centralbank.ae/` | central_bank | under_validation | false | Sprint 3C returned HTTP 200 with usable text and PDF links. | Rulebook sections, PDF dependency, and item-level URL stability are not validated. | Run 3-5 repeated checks, test PDF links, and verify section-level change isolation. |

## 3. Candidates deliberately not added

- UAE Legislation Portal — Sprint 3C returned 403/block-style behavior for the root candidate; item-level monitoring still needs adapter/WAF validation.
- UAE FIU — Sprint 3C returned 403/block-style behavior; do not stage until access behavior is clarified.
- CBUAE main — Sprint 3C returned 403/block-style behavior on the main site.
- CBUAE payments — same root as CBUAE main and returned 403/block-style behavior.
- DFSA Rulebook — accessible in Sprint 3C, but not added in this pass to keep the staged set to the cleanest 3-5 and avoid broadening scope before repeated-run checks.
- VARA main publications and rulebooks — accessible but flagged for PDF validation; should be handled in a PDF-focused validation sprint.
- Federal Tax Authority — accessible in Sprint 3C but historically access-constrained and redirected to Arabic default page; keep out of this disabled set until repeated URL-specific validation is done.
- SCA/CMA — accessible in Sprint 3C but current production entry is disabled navigation-only and authority transition remains unresolved; avoid staging until exact publications/circulars endpoint is mapped.

## 4. Repeated-run stability check plan

For each disabled candidate:

- Run count: 3-5 checks.
- Spacing: 5-10 minutes apart, or separate runs across different times of day.
- Required pass conditions:
  - HTTP 200 or stable acceptable redirect.
  - Response time consistently below 5 seconds.
  - Extracted text above 1,500 characters for HTML-first pages.
  - No WAF/403 response during repeated checks.
  - Stable title and content signature across unchanged runs.
  - PDF links remain resolvable if the source has PDF dependency.
  - Item-level URL confirmed where source-layer monitoring requires item-level changes.

Candidate-specific checks:

- ADGM / FSRA main: confirm FSRA page content is stable and locate notices/publications if present.
- ADGM / FSRA rulebook: identify official rulebook URL or document index before any activation decision.
- DIFC Laws: verify that the corrected `difc.com` page exposes stable item-level law/regulation links.
- MoET AML / DNFBP: locate AML/DNFBP section or PDFs under `moet.gov.ae`.
- CBUAE Rulebook: verify section-level rulebook links and PDF links across repeated runs.

## 5. Recommended Sprint 3E

Run repeated-run stability validation for these disabled candidates only. Do not activate monitoring until repeated-run stability, item-level mapping, and any PDF dependency checks pass in a separate approval sprint.
