# Weak-Zone Current Blocker Map

Date: 2026-06-16

Starting truth before this weak-zone elimination run: **36 enabled / 32 readiness-supported / 4 remediation**. Current truth is updated in the final reports after validation. This map focuses only on known weak-zone candidates that can plausibly move the project toward 50 without fake activation.

## UAE FIU SPA / XHR / Document Listings

| Source ID | Current blocker | Likely fix path | Effort | Activation potential | Priority |
| --- | --- | --- | --- | --- | --- |
| `AE-uaefiu-strategic-analysis` | Nav-shell/shallow route under current document listing adapter. | Find direct official PDF/document endpoint or narrower XHR/listing route. | medium | medium | high |
| `AE-uaefiu-nra-2024` | Nav-shell/shallow route under current document listing adapter. | Find direct NRA report document endpoint. | medium | medium | high |
| `AE-uaefiu-annual-reports` | Passed no-save but duplicate hash with `AE-uaefiu-publications-hub`. | Find annual-report specific document list or keep as duplicate hold. | low-medium | low unless unique | medium |
| `AE-uaefiu-laws-regulations` | Access-blocked/stale older route. | Prefer newer knowledge-centre AML/CFT laws route already activated; search only for distinct official law endpoint. | medium | low-medium | medium |
| `AE-uaefiu-press-releases` | Not fully tested. | Test only if regulatory/FIU update content, not marketing/news noise. | low | medium | medium |

## VARA Rulebooks / Framework / Enforcement

| Source ID | Current blocker | Likely fix path | Effort | Activation potential | Priority |
| --- | --- | --- | --- | --- | --- |
| `AE-vara-rulebooks-overview` | Nav-shell/stale page. | Find direct official rulebook PDF URLs or document listing endpoint. | medium | high | high |
| `AE-vara-aml-cft-rulebook` | Nav-shell on current page. | Find direct AML/CFT rulebook PDF. | medium | high | high |
| `AE-vara-company-rulebook` | Nav-shell on current page. | Find direct Company Rulebook PDF. | medium | high | high |
| `AE-vara-regulatory-framework` | Nav-shell/stale route. | Use official document URLs rather than framework landing page. | medium | high | high |
| `AE-vara-public-register` | Nav-shell risk and possible low signal. | Activate only if public register rows are accessible and useful. | medium | medium | medium |
| `AE-vara-news` | Selector stale; possible marketing noise. | Activate only regulatory/admin-order updates, not generic media. | medium | low-medium | low |

## CBUAE Access / Selector / Alternate Endpoints

| Source ID | Current blocker | Likely fix path | Effort | Activation potential | Priority |
| --- | --- | --- | --- | --- | --- |
| `AE-cbuae-publications` | Public site access-blocked. | Find official rulebook/document alternate endpoints. | medium | high | high |
| `AE-cbuae-circulars` | Public site access-blocked or stale. | Find public circular/regulation alternate or rulebook categories. | medium | high | high |
| `AE-cbuae-aml-cft` | Public site access-blocked. | Use official rulebook AML/financial-crime pages if public. | medium | high | high |
| `AE-cbuae-payment-systems` | Public site access-blocked. | Use official rulebook payment-system/rpscs/stored-value pages if public. | medium | high | high |
| `AE-cbuae-consultations` | Access-blocked. | Search only official public alternates; no bypass. | medium | medium | medium |

## DFSA / DIFC Selector / Access Issues

| Source ID | Current blocker | Likely fix path | Effort | Activation potential | Priority |
| --- | --- | --- | --- | --- | --- |
| `AE-dfsa-published-decisions` | Nav-shell under current selector. | Enforcement listing selector or official document URLs. | medium | high | high |
| `AE-dfsa-enforcement-regulatory-actions` | Selector stale/access issue. | Find current enforcement regulatory actions URL or listing. | medium | high | high |
| `AE-dfsa-consultation-papers` | Access/selector issue. | Consultation listing selector or PDF listing. | medium | medium-high | high |
| `AE-dfsa-publications` | Not fully tested in latest weak-zone cycle. | Publications listing selector/document links. | medium | medium | medium |
| `AE-difc-data-protection` | Selector stale. | DIFC data-protection content selector or official legislation document links. | medium | medium | medium |
| `AE-difc-consultation-papers` | Not fully tested in latest weak-zone cycle. | Consultation listing selector. | medium | medium | medium |
| `AE-difc-legal-database` | Access-blocked under tested URL. | Keep blocked unless official public access is available without bypass. | high | low-medium | low |

## ADGM Alternate Components

| Source ID | Current blocker | Likely fix path | Effort | Activation potential | Priority |
| --- | --- | --- | --- | --- | --- |
| `AE-adgm-dp-regulatory-actions` | Current adapter returns nav-shell or heading-only output. | Extract regulatory-action cards/listing items. | medium | high | high |
| `AE-adgm-media-announcements` | Current adapter collapses to service/nav links. | Stricter announcement-card extraction and noise filtering. | medium | medium | medium |
| `AE-adgm-listing-announcements` | Stale selector/URL. | Find replacement URL or listing-authority announcement component. | medium | medium-high | high |
| `AE-adgm-ra-notices` | Alternate component/stale path. | Search official replacement URL or component selector. | medium | medium | medium |
| `AE-adgm-ra-aml-guides` | Alternate component/stale path. | Search official replacement URL or document list. | medium | medium-high | medium |
| `AE-adgm-abu-dhabi-legislation` | Not fully tested in latest cycle. | Legal-framework page selector. | low-medium | medium | medium |
| `AE-adgm-federal-legislation` | Not fully tested in latest cycle. | Legal-framework page selector. | low-medium | medium | medium |

## Batch Priority

1. VARA and CBUAE official document/PDF alternates: highest chance to add distinct regulatory sources quickly.
2. DFSA/DIFC enforcement/consultation pages: high buyer value if selectors can be found.
3. ADGM alternate components: likely solvable, but must avoid media/noise.
4. UAE FIU leftovers: high relevance but several routes are duplicates of the activated publications hub.
