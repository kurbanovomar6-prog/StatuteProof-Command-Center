# Source Quality Audit — sources.json
**Date:** 2026-06-24  
**File:** `product/regradar/sources.json`  
**Total sources:** 424 (271 enabled, 153 disabled)

---

## Section 1 — PDF Sources Problem

**Count: 48 enabled sources have a URL that ends in `.pdf` (or is a Liferay document-store download with an embedded PDF path).**

A monitoring system that fetches a static PDF URL will never detect a change. The PDF at that URL is an immutable binary asset. The correct monitoring target is the listing page (e.g. the FTA legislation index or the VARA revision-updates page) which changes when new documents are published. The 48 static PDF sources therefore generate no signal — they are noise with infrastructure cost attached.

Both FTA and VARA already have listing pages enabled that cover the full set of their PDFs. Monitoring the individual PDF files on top of the listing pages adds zero incremental coverage.

### 1a — VARA PDFs (22 enabled)

All 22 VARA PDF sources point to `rulebooks.vara.ae/sites/default/files/en_net_file_store/VARA_EN_*.pdf`.

The listing page `https://rulebooks.vara.ae/view-revision-updates` (source `AE-vara-rulebook-revision-updates`) is already enabled and covers all rulebook changes. The VARA News source (`https://www.vara.ae/en/news`) and Regulatory Notices source (`https://www.vara.ae/en/regulations/regulatory-notices/`) are also enabled.

| source_id | name | url |
|---|---|---|
| AE-vara-compliance-risk-rulebook-pdf | VARA Compliance and Risk Management Rulebook PDF | .../VARA_EN_123_VER20250519.pdf |
| AE-vara-technology-information-rulebook-pdf | VARA Technology and Information Rulebook PDF | .../VARA_EN_169_VER20250519.pdf |
| AE-vara-va-issuance-rulebook-pdf | VARA Virtual Asset Issuance Rulebook PDF | .../VARA_EN_293_VER20250519.pdf |
| AE-vara-broker-dealer-rulebook-pdf | VARA Broker-Dealer Services Rulebook PDF | .../VARA_EN_226_VER20250519.pdf |
| AE-vara-lending-borrowing-rulebook-pdf | VARA Lending and Borrowing Services Rulebook PDF | .../VARA_EN_279_VER20250519.pdf |
| AE-vara-va-regulations-2023-pdf | VARA Virtual Assets and Related Activities Regulations 2023 PDF | .../VARA_EN_18_VER992_2.pdf |
| AE-vara-pdf-exchange-services-rulebook | VARA PDF - Exchange Services Rulebook | .../VARA_EN_258_VER20260331.pdf |
| AE-vara-pdf-va-management-investment-rulebook | VARA PDF - Va Management Investment Rulebook | .../VARA_EN_317_VER20250519.pdf |
| AE-vara-pdf-company-rulebook | VARA PDF - Company Rulebook | .../VARA_EN_36_VER20250519.pdf |
| AE-vara-pdf-administrative-order-01-2022 | VARA PDF - Administrative Order 01 2022 | .../VARA_EN_341_VER1.pdf |
| AE-vara-pdf-advisory-services-rulebook | VARA PDF - Advisory Services Rulebook | .../VARA_EN_215_VER20250519.pdf |
| AE-vara-pdf-va-transfer-settlement-rulebook | VARA PDF - Va Transfer Settlement Rulebook | .../VARA_EN_347_VER20250519.pdf |
| AE-vara-pdf-cabinet-decision-111-2022 | VARA PDF - Cabinet Decision 111 2022 | .../VARA_EN_339_VER1.pdf |
| AE-vara-pdf-custody-services-rulebook | VARA PDF - Custody Services Rulebook | .../VARA_EN_243_VER20250519.pdf |
| AE-vara-pdf-guidance-virtual-asset-issuance | VARA PDF - Guidance Virtual Asset Issuance | .../VARA_EN_516_VER1.pdf |
| AE-vara-pdf-administrative-order-02-2022 | VARA PDF - Administrative Order 02 2022 | .../VARA_EN_342_VER1.pdf |
| AE-vara-pdf-market-conduct-rulebook | VARA PDF - Market Conduct Rulebook | .../VARA_EN_190_VER20250519.pdf |
| AE-vara-pdf-cabinet-decision-112-2022 | VARA PDF - Cabinet Decision 112 2022 | .../VARA_EN_340_VER1.pdf |
| AE-vara-pdf-law-no-4-2022-virtual-assets | VARA PDF - Law No 4 2022 Virtual Assets | .../VARA_EN_338_VER1.pdf |
| AE-vara-pdf-grievance-committee-resolution-2023 | VARA Grievance Committee Administration Resolution PDF | .../VARA_EN_345_VER2.pdf |
| AE-vara-pdf-rulebook-introduction | VARA Rulebook Introduction PDF | .../VARA_EN_419_VER1.pdf |
| AE-vara-pdf-virtual-assets-regulations-2023-latest-revision | VARA Virtual Assets and Related Activities Regulations 2023 Latest Revision PDF | .../VARA_EN_18_VER993.pdf |

**Listing page that already covers these:** `AE-vara-rulebook-revision-updates` (enabled)

### 1b — FTA PDFs (25 enabled)

All 25 FTA PDF sources point to dated files under `tax.gov.ae/Datafolder/` or `tax.gov.ae/DownloadOpenTextFile`. These are snapshots of guides and decisions. FTA already has 6 listing pages enabled that cover legislation, VAT guides, corporate tax guides, and clarifications.

| source_id | name | notes |
|---|---|---|
| AE-fta-pdf-cabinet-decision-no-74-of-2023-... | FTA PDF — Cabinet Decision No 74 of 2023... | Static PDF |
| AE-fta-pdf-fta-decisio-no-5-03-2026 | FTA PDF — FTA Decisio No 5 03 2026 | Typo + static PDF |
| AE-fta-pdf-qpbes | FTA PDF — QPBEs | Unclear name + static PDF |
| AE-fta-pdf-fta-decision-no-6-of-2025-... | FTA PDF — FTA Decision No 6 of 2025 on Standards Controls | Static PDF |
| AE-fta-pdf-ministerial-decision-no-173-of-2025 | FTA PDF — Ministerial Decision No 173 of 2025 | Static PDF |
| AE-fta-pdf-cabient-decision-no-55-of-2025 | FTA PDF — Cabient Decision No 55 of 2025 | Typo + static PDF |
| AE-fta-pdf-fta-decision-no-11-of-2025-... | FTA PDF — FTA Decision No. 11 of 2025... | Static PDF |
| AE-fta-pdf-fta-decision-no-10-of-2025-... | FTA PDF — FTA Decision No. 10 of 2025... | Static PDF |
| AE-fta-pdf-cabinet-decision-no-153-of-2025-... | FTA PDF — Cabinet Decision No. 153 of 2025... | Static PDF |
| AE-fta-pdf-vat-refund-for-uae-nationals-...-09-06 | FTA PDF — VAT Refund for UAE Nationals EN 09 06 2026 | Duplicate + static PDF |
| AE-fta-pdf-vat-refund-for-uae-nationals-...-10-04 | FTA PDF — VAT Refund for UAE Nationals EN 10 04 2026 | Duplicate + static PDF |
| AE-fta-pdf-profit-margin-scheme-en-02-01-2026-re | FTA PDF — Profit Margin Scheme EN 02 01 2026 re | Trailing "re" + static PDF |
| AE-fta-pdf-vat-administrative-exceptions-guide-... | FTA PDF — VAT Administrative Exceptions Guide EN 05 12 2025 | Static PDF |
| AE-fta-pdf-input-tax-apportionment-guide-... | FTA PDF — Input Tax Apportionment Guide EN 30 09 2025 | Static PDF |
| AE-fta-pdf-private-clarifications-en-24-07-2025 | FTA PDF — Private Clarifications EN 24 07 2025 | Duplicate pair |
| AE-fta-pdf-private-clarifications-en-18-11-2024 | FTA PDF — Private Clarifications EN 18 11 2024 | Duplicate pair |
| AE-fta-pdf-family-foundations-guide-... | FTA PDF — Family Foundations Guide EN 05 06 2026 | Static PDF |
| AE-fta-pdf-ctp010-... | FTA PDF — CTP010 Clarification of director and officer 04 2026 | Internal code name |
| AE-fta-pdf-ct-corporate-tax-de-registration-... | FTA PDF — CT Corporate Tax De Registration User Manual V4 EN | Static manual |
| AE-fta-pdf-ct-registration-of-deactivated-... | FTA PDF — CT Registration of Deactivated Corporate Tax RN taxpayer | Static manual |
| AE-fta-pdf-apa-guide-en-30-12-2025 | FTA PDF — APA Guide EN 30 12 2025 | Static PDF |
| AE-fta-pdf-ct-corporate-tax-payments-user-manual-fv | FTA PDF — CT   Corporate Tax Payments User Manual FV | Triple space + "FV" |
| AE-fta-pdf-ctp009-... | FTA PDF — CTP009 Application of Transitional Rules... | Internal code name |
| AE-fta-pdf-ctp008-... | FTA PDF — CTP008 Corporate Tax treatment of family wealth management structures | Internal code name |
| AE-fta-pdf-ctp007-... | FTA PDF — CTP007 Aggregate Financial Statements... | Internal code name |

**Listing pages that already cover these:** `AE-fta-legislation-all`, `AE-fta-vat-guides-references`, `AE-fta-corporate-tax-guides-references`, `AE-fta-vat-public-clarifications`, `AE-fta-corporate-tax-legislation` (all enabled)

### 1c — ADGM Data Protection PDF (1 enabled)

| source_id | url |
|---|---|
| AE-adgm-data-protection-regulations-2021-pdf | https://www.adgm.com/documents/office-of-data-protection/resources/adgm-data-protection-regulations-2021-updated.pdf |

The ADGM Office of Data Protection listing (`https://www.adgm.com/operating-in-adgm/office-of-data-protection/`) is enabled and covers this.

**Recommendation:** Disable all 48 static PDF sources. Monitoring the listing pages is the correct architecture.

---

## Section 2 — Duplicate and Near-Duplicate Sources

### 2a — Same Document, Two Version Files

These pairs each point to two different version snapshots of the exact same regulatory document. Both versions are static PDFs and will never change. Only the latest version matters, and even that should be replaced by a listing page monitor.

| Pair | source_id A | source_id B |
|---|---|---|
| VARA VA Regulations 2023 | AE-vara-va-regulations-2023-pdf (VER992_2) | AE-vara-pdf-virtual-assets-regulations-2023-latest-revision (VER993) |
| FTA VAT Refund UAE Nationals | AE-fta-pdf-vat-refund-for-uae-nationals-...-09-06-20 | AE-fta-pdf-vat-refund-for-uae-nationals-...-10-04-20 |
| FTA Private Clarifications | AE-fta-pdf-private-clarifications-en-24-07-2025 | AE-fta-pdf-private-clarifications-en-18-11-2024 |

### 2b — Trailing Slash Duplicate (Same Page, Different URL)

| source_id A | source_id B | URL |
|---|---|---|
| AE-difc-legal-database | AE-difc-static-legal-database-c192df94 | https://www.difc.com/business/laws-and-regulations/legal-database (with/without trailing slash) |

Both sources resolve to the same DIFC Legal Database page. One should be disabled.

### 2c — DFSA News Hub Parent + 27 Individual Child Pages

The source `DFSA — News Hub (legislative amendment notices)` at `https://www.dfsa.ae/news` is enabled. In addition, 27 individual DFSA news article pages are separately enabled, all under `https://www.dfsa.ae/news/notice-*`. These are historical articles that will never change content. The News Hub parent already surfaces new articles when they are published.

**Examples of redundant children:**
- `AE-dfsa-news-notice-amendment-dfsa-forms-3` → `/news/notice-amendment-dfsa-forms-3`
- `AE-dfsa-news-notice-amendments-rulebook-1` → `/news/notice-amendments-rulebook-1`
- `AE-dfsa-news-notice-consultation-paper-2` → `/news/notice-consultation-paper-2`
- (24 more at the same pattern)

All 27 child pages are redundant given the hub is monitored.

### 2d — DIFC Laws Hub + Child Pages

`AE-difc-laws-and-regulations` (`/business/laws-and-regulations/`) is enabled alongside:
- `AE-difc-legal-database` (`/business/laws-and-regulations/legal-database/`)
- `AE-difc-static-legal-notices-9f800f67` (`/business/laws-and-regulations/legal-notices`)
- `AE-difc-data-protection-law-2020` (specific law page under the legal database)
- `AE-difc-companies-law-2018` (specific law page under the legal database)

Monitoring the parent `/business/laws-and-regulations/` does not automatically capture all changes to every sub-page. The child pages may be legitimate targets if they carry distinct content that changes independently of the hub. However, monitoring both the hub and its specific sub-pages without a clear architectural reason creates ambiguity.

### 2e — MoE Homepage + Section Pages

`AE-uae-ministry-of-finance` (`https://mof.gov.ae/`) is enabled alongside four sub-section pages on the same domain (Publications, Financial Legislation, Top-Up Tax, Corporate Tax). The homepage is a generic portal that changes frequently with unrelated news; the specific section pages are the ones with regulatory signal.

Similarly, `AE-uae-ministry-of-economy` (`https://www.moet.gov.ae/en/`) is enabled alongside `UAE Ministry of Economy — AML/CFT Hub` (`/en/aml`). The homepage adds noise.

---

## Section 3 — Category Consistency

The `category` field has 46 distinct values across 424 sources. This volume of categories is unmanageable. More specifically, the same regulatory body is assigned different categories in different sources, meaning category-based filtering produces unreliable groupings.

### 3a — Full Category Inventory (enabled sources)

| Category | Enabled | Convention |
|---|---|---|
| financial_regulator | 55 | snake_case, correct |
| regulatory | 55 | too generic — used as a catch-all |
| tax | 31 | correct |
| dnfbp_aml | 26 | correct |
| aml | 12 | overlaps dnfbp_aml — same concept, two names |
| virtual_assets | 18 | correct |
| adgm_fsra | 14 | correct |
| difc | 13 | correct |
| eocn_tfs | 16 | correct |
| difc_legal_regulatory | 4 | duplicates 'difc' — same entity |
| data_protection | 2 | correct |
| data_protection_regulatory | 2 | duplicates 'data_protection' |
| data_protection_enforcement | 1 | duplicates 'data_protection' |
| data_protection_guidance | 1 | duplicates 'data_protection' |
| financial_regulation | 2 | duplicates 'financial_regulator' |
| uae_fiu | 2 | these sources also exist under 'aml' |
| ADGM/FSRA | 1 | **uppercase, not snake_case** |
| SCA | 1 | **uppercase, not snake_case** |
| DIFC | 1 | **uppercase, not snake_case** |
| consultations | 1 | one-off, no consistent use |
| rulebook | 1 | one-off, no consistent use |
| sanctions | 1 | one-off, no consistent use |
| legal_database | 3 | ambiguous — used for both DIFC and other legal databases |

### 3b — Same Entity, Multiple Category Names

| Entity | Categories Used |
|---|---|
| ADGM/FSRA | `adgm_fsra`, `ADGM/FSRA`, `financial_regulator`, `regulatory`, `aml`, `financial_regulation`, `data_protection`, `consultations` (8 distinct values) |
| DIFC | `difc`, `DIFC`, `difc_legal_regulatory`, `financial_regulator`, `legal_database`, `data_protection_regulatory`, `data_protection_enforcement`, `data_protection_guidance` (8 distinct values) |
| UAE FIU | `aml`, `uae_fiu` |
| Data Protection sources | `data_protection`, `data_protection_regulatory`, `data_protection_enforcement`, `data_protection_guidance` |

### 3c — Uppercase Category Values (3 violations)

These three sources use PascalCase or all-caps category names, breaking the snake_case convention used by all other sources:

| source_id | name | category |
|---|---|---|
| (ADGM FSRA Guidance) | ADGM FSRA Guidance and Policy Statements | `ADGM/FSRA` |
| (UAE CMA Regulations Listing) | UAE CMA Regulations Listing | `SCA` |
| (DIFC Legal Database) | DIFC Legal Database | `DIFC` |

---

## Section 4 — Non-UAE Sources Still Enabled

**None.** All 271 enabled sources have jurisdiction `AE` or `UAE`. The 153 disabled sources include 128 non-UAE sources (Bahrain, Malaysia, Qatar, Saudi Arabia, Hong Kong, Turkey, Kazakhstan, Singapore, Uzbekistan, Russia, Azerbaijan, Georgia, Armenia, Belarus, and International).

No action required on jurisdiction filtering for enabled sources.

### 4a — Jurisdiction Code Inconsistency (AE vs UAE)

While no non-UAE sources are enabled, the UAE itself uses two different jurisdiction codes:

- `AE` — used by 252 enabled sources (ISO 3166-1 alpha-2, correct)
- `UAE` — used by 19 enabled sources (non-standard)

The 19 sources with `UAE` jurisdiction include: VARA Public Register, VARA Regulatory Notices, DFSA Public Register, UAE Ministry of Economy AML/CFT Hub, UAE CMA pages, FTA VAT Public Clarifications, ADGM Office of Data Protection, MOHRE pages, UAE Cabinet News, Dubai Legislation Portal, DIFC Courts pages, DIFC News Hub, ADGM Media Announcements Hub, DFSA News Hub, DFSA SEO Letters.

These should be normalised to `AE` for consistent filtering.

---

## Section 5 — eocn_tfs Category (16 sources)

All 16 `eocn_tfs` sources are enabled. Every single one is a **Liferay document-store URL** from `www.moet.gov.ae/documents/20121/...` — the internal document management system behind the UAE Ministry of Economy website.

The URL structure is:
```
https://www.moet.gov.ae/documents/20121/{folder-id}/{filename}.pdf/{uuid}?t={timestamp}
```

This is not a web page — it is a direct link to a PDF binary served by a Liferay content server. Monitoring this URL will not detect when the Ministry publishes a new circular or updates a document, because the URL is a permalink to a specific stored binary. When the Ministry publishes an update, it creates a new Liferay document with a new UUID and new timestamp — the old URL remains alive forever, pointing to the old document.

**What these sources actually are:**

| Document content | Domain |
|---|---|
| Cabinet Decision No 3 of 2025 (TFS thresholds) | MoE |
| Circular No 2 2025 (ICA) | MoE |
| Circular No 5 2025 (High Risk list update) | MoE |
| Circular No 4 2024 (High Risk list update) | MoE |
| Circular No 3 2024 (High Risk list update) | MoE |
| Cabinet Resolution No 71 2024 (DNFBP penalties) | MoE |
| Cabinet Decision 107 2022 (AML) | MoE |
| Cabinet Decision 102 2022 | MoE |
| Cabinet Decision 47 2022 | MoE |
| Circular No 5 2021 (goAML deadline) | MoE |
| Cabinet Decision 109 2023 | MoE |
| Supplemental Guidance for Auditors | MoE |
| Supplemental Guidance for Dealers in Precious Metals and Stones | MoE |
| Supplemental Guidance for Real Estate Sector | MoE |
| Supplemental Guidance for Trust and Company Service Providers | MoE |
| Federal Decree-Law No 10 of 2025 (AML/CFT/PF) | MoE |

These are all legitimate, high-value UAE regulatory documents. The problem is the monitoring method, not the content choice. The MoE AML listing page (`https://www.moet.gov.ae/aml`) is already enabled under `dnfbp_aml` and surfaces new publications. The `eocn_tfs` sources should be disabled and replaced by ensuring the MoE AML listing page is monitored reliably.

Additionally, the category name `eocn_tfs` is an unexplained internal code. "EOCN" refers to the Executive Office for Control of Non-Proliferation; "TFS" refers to Targeted Financial Sanctions. These are legitimate regulatory categories, but the category value is opaque to anyone reading the source database without that background.

---

## Section 6 — dnfbp_aml Category (26 sources)

All 26 `dnfbp_aml` sources are enabled. All are from `www.moet.gov.ae`. The category breaks into two distinct types:

**Type A — HTML listing pages (7 sources, high quality):**

| name | url |
|---|---|
| Ministry of Economy — AML | https://www.moet.gov.ae/aml |
| Ministry of Economy — Auditing Accounts Legislations | https://www.moet.gov.ae/auditing-accounts-legislations |
| Ministry of Economy — Economic Substance Regulations | https://www.moet.gov.ae/economic-substance-regulations |
| Ministry of Economy — Registering Companies In goAML | https://www.moet.gov.ae/registering-companies-in-goaml |
| Ministry of Economy — Regulation Of Business | https://www.moet.gov.ae/regulation-of-business |
| Ministry of Economy — Regulation Of Competition | https://www.moet.gov.ae/regulation-of-competition |
| Ministry of Economy — Targeted Financial Sanctions | https://www.moet.gov.ae/targeted-financial-sanctions |

These 7 are correct monitoring targets. They are HTML listing pages that update when the Ministry publishes new content.

**Type B — Liferay document-store URLs (19 sources, same architectural problem as eocn_tfs):**

These are all `https://www.moet.gov.ae/documents/20121/...` URLs serving individual PDFs. Examples include the MoE DNFBP circular series (2024–2026 high-risk jurisdiction updates, risk-based CDD measures, responsible gold sourcing), supplemental guidance documents for real estate agents, DPMS, trust and company service providers, and the independent accountants guidance.

The 19 Liferay document URLs will never change and cannot detect new publications. The HTML listing pages (Type A) already provide the correct monitoring signal for new DNFBP circulars.

**Assessment:** The 7 HTML listing pages are high-priority, high-quality sources. The 19 Liferay document URLs should be disabled in favour of monitoring the listing pages that already surface all new documents.

---

## Section 7 — Sources With Bad Names

**33 enabled sources** have naming problems across two distinct clusters:

### 7a — eocn_tfs: All 16 Names Are Auto-Generated Document IDs

Every `eocn_tfs` source has a name of the pattern `MoE DNFBP AML/TFS Document {folder-id}-{hex-hash}`. Examples:
- `MoE DNFBP AML/TFS Document 0-14503b23`
- `MoE DNFBP AML/TFS Document 469920-6d81bc73`

These names describe nothing about the document content. They appear to be auto-generated from the Liferay document IDs. A user looking at the source list cannot determine what regulation these sources track without inspecting the URL.

The actual documents are: Cabinet Decisions on AML penalties, FATF high-risk jurisdiction circulars, goAML registration circulars, supplemental guidance for specific DNFBP sectors. All should carry descriptive names.

### 7b — FTA PDFs: Typos, Embedded Version Dates, and Internal Codes

| source_id | name | issue |
|---|---|---|
| AE-fta-pdf-fta-decisio-no-5-03-2026 | `FTA PDF — FTA Decisio No 5 03 2026` | Typo: "Decisio" should be "Decision" |
| AE-fta-pdf-cabient-decision-no-55-of-2025 | `FTA PDF — Cabient Decision No 55 of 2025` | Typo: "Cabient" should be "Cabinet" |
| AE-fta-pdf-qpbes | `FTA PDF — QPBEs` | Acronym with no expansion — "Qualifying Public Benefit Entities" |
| AE-fta-pdf-vat-refund-for-uae-nationals-...-09-06 | `FTA PDF — VAT Refund for UAE Nationals   EN   09 06 2026` | Version date embedded in name with inconsistent spacing |
| AE-fta-pdf-vat-refund-for-uae-nationals-...-10-04 | `FTA PDF — VAT Refund for UAE Nationals EN 10 04 2026` | Same document, duplicate with version date |
| AE-fta-pdf-profit-margin-scheme-en-02-01-2026-re | `FTA PDF — Profit Margin Scheme EN 02 01 2026 re` | "re" suffix unexplained |
| AE-fta-pdf-vat-administrative-exceptions-guide-... | `FTA PDF — VAT Administrative Exceptions Guide   EN   05 12 2025` | Version date + triple space |
| AE-fta-pdf-input-tax-apportionment-guide-... | `FTA PDF — Input Tax Apportionment Guide EN   30 09 2025` | Version date embedded |
| AE-fta-pdf-private-clarifications-en-24-07-2025 | `FTA PDF — Private Clarifications EN 24 07 2025` | Version date embedded |
| AE-fta-pdf-private-clarifications-en-18-11-2024 | `FTA PDF — Private Clarifications EN 18 11 2024` | Duplicate pair, version date |
| AE-fta-pdf-family-foundations-guide-... | `FTA PDF — Family Foundations Guide   EN   05 06 2026` | Triple space + version date |
| AE-fta-pdf-apa-guide-en-30-12-2025 | `FTA PDF — APA Guide EN 30 12 2025` | "APA" unexpanded — Advance Pricing Agreement |
| AE-fta-pdf-ct-corporate-tax-payments-user-manual-fv | `FTA PDF — CT   Corporate Tax Payments User Manual FV` | Triple space; "FV" unexplained |
| AE-fta-pdf-ctp009-... | `FTA PDF — CTP009 Application of Transitional Rules...` | "CTP009" is an internal FTA document code |
| AE-fta-pdf-ctp008-... | `FTA PDF — CTP008 Corporate Tax treatment of family wealth management structures` | "CTP008" is an internal code |
| AE-fta-pdf-ctp007-... | `FTA PDF — CTP007 Aggregate Financial Statements and Audit Requirement for Tax Groups 27 082025 final` | "CTP007" code + malformed date "27 082025" |
| AE-fta-pdf-ctp010-... | `FTA PDF — CTP010 Clarification of director and officer 04 2026` | "CTP010" code + partial date |

---

## Section 8 — Jurisdiction Field Audit

### Full Jurisdiction Distribution

| Code | Country | Total | Enabled |
|---|---|---|---|
| AE | United Arab Emirates (ISO code, correct) | 262 | 252 |
| UAE | United Arab Emirates (non-standard) | 34 | 19 |
| BH | Bahrain | 14 | 0 |
| MY | Malaysia | 14 | 0 |
| QA | Qatar | 13 | 0 |
| SA | Saudi Arabia | 12 | 0 |
| INT | International (FATF, Basel, IOSCO) | 10 | 0 |
| HK | Hong Kong | 10 | 0 |
| TR | Turkey | 9 | 0 |
| KZ | Kazakhstan | 8 | 0 |
| SG | Singapore | 8 | 0 |
| UZ | Uzbekistan | 6 | 0 |
| RU | Russia | 5 | 0 |
| AZ | Azerbaijan | 5 | 0 |
| GE | Georgia | 5 | 0 |
| AM | Armenia | 5 | 0 |
| BY | Belarus | 4 | 0 |

No non-UAE jurisdictions are currently enabled. The 128 non-UAE disabled sources (Bahrain, Malaysia, Qatar, Saudi Arabia, and others) are correctly disabled for a UAE-only product scope.

### AE vs UAE Inconsistency (19 enabled sources)

The following enabled sources use `jurisdiction: "UAE"` instead of the correct ISO code `"AE"`. This inconsistency can break jurisdiction-based filtering:

- VARA Public Register
- VARA Regulatory Notices and Enforcement Index
- DFSA Public Register
- UAE Ministry of Economy — AML/CFT Hub
- UAE CMA Laws and Legislation, Regulations Index, and Circulars
- FTA VAT Public Clarifications
- ADGM Office of Data Protection
- MOHRE Ministerial Resolutions and Laws Index
- UAE Cabinet News and Decisions
- Dubai Legislation Portal
- DIFC Courts Practice Directions and Registrar's Directions
- DIFC News and Announcements Hub
- ADGM Media Announcements Hub
- DFSA News Hub
- DFSA SEO Letters

---

## Priority Recommendations

### 1 — Disable All 48 Static PDF Sources (highest impact)

All 48 enabled PDF sources are monitoring immutable file assets. They can never detect a regulatory change because the PDF at a fixed URL never updates — a new decision produces a new URL. The monitoring cost is real (fetches, storage, evidence records) but the signal value is zero. All relevant listing pages are already enabled and cover the same content. Disabling the 48 PDF sources will eliminate ~18% of enabled sources immediately, reduce noise, and make the enabled list genuinely signal-focused.

**Action:** Set `enabled: false` on all sources where `url` ends in `.pdf` or contains `/Datafolder/Files/` (FTA) or `/en_net_file_store/VARA_EN_` (VARA).

### 2 — Replace eocn_tfs and dnfbp_aml Liferay Document URLs With Listing Page Monitoring

The 16 `eocn_tfs` sources and 19 of the 26 `dnfbp_aml` sources point to Liferay document-store URLs (`moet.gov.ae/documents/20121/...`). These have the same static-asset problem as the PDF sources: a new publication creates a new URL, the old URL never changes. The 7 HTML listing pages already enabled under `dnfbp_aml` (especially `moet.gov.ae/aml` and `moet.gov.ae/targeted-financial-sanctions`) provide the correct detection surface.

**Action:** Disable the 35 Liferay document-store sources. Invest effort in verifying the 7 MoE listing pages reliably detect changes. Rename the 16 `eocn_tfs` sources to use the `dnfbp_aml` category and give them descriptive names before enabling the replacement listing pages.

### 3 — Consolidate Category Values to a Controlled Vocabulary

The current 46-value category field is unusable for reliable filtering. The same regulatory body (ADGM/FSRA) has 8 different category values across its sources; DIFC has another 8. This makes programmatic grouping by category unreliable.

**Action:** Define a controlled vocabulary of approximately 12–15 categories: `central_bank`, `financial_regulator`, `securities_regulator`, `virtual_assets`, `tax`, `aml`, `dnfbp`, `data_protection`, `free_zone`, `legal_acts`, `government`, `international`. Run a migration to reassign every source. Fix the three uppercase outliers (`ADGM/FSRA`, `SCA`, `DIFC`) immediately as they are trivial one-line fixes. Merge `aml` and `dnfbp_aml` or clearly separate them by entity type.

### 4 — Disable the 27 DFSA Individual News Pages in Favour of the Hub

The DFSA News Hub at `https://www.dfsa.ae/news` is already enabled and monitors for new amendments, consultation papers, and notices. The 27 individual news article URLs are historical articles that published once and never change. They produce zero monitoring signal and inflate the enabled source count by 27 entries.

**Action:** Disable all 27 `AE-dfsa-news-notice-*` sources. Confirm the DFSA News Hub scraper reliably detects new article additions.

### 5 — Normalise Jurisdiction Code and Fix Source Names

Two cleanup tasks with no monitoring impact but significant data quality impact:

**Jurisdiction:** Change `jurisdiction: "UAE"` to `jurisdiction: "AE"` on 19 enabled sources. This makes jurisdiction filtering consistent.

**Source names:** Fix the 17 FTA PDF sources with typos, embedded version dates, triple spaces, and unexplained abbreviations. Even if the sources are disabled (per recommendation 1), the names will survive as historical records and should be readable. Priority fixes: `Decisio` typo, `Cabient` typo, `QPBEs` expansion, `FV` and `re` suffixes, CTP-prefixed names.
