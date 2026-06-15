# Autonomous Live Validation Log

Date: 2026-06-15

## Cycle 1: JS-Heavy Near-Term Batch

Scope: 8 official UAE candidates from the current scoreboard. No broad monitoring, no customer alerts, no evidence save during no-save phase.

| Source ID | URL | Adapter/config | No-save result | Decision |
| --- | --- | --- | --- | --- |
| `AE-uaefiu-aml-cft-laws` | `https://uaefiu.gov.ae/en/more/knowledge-centre/aml-cft-laws-related-decisions/` | `fiu_eocn_document_listing`, `body` | `NAV_SHELL_ONLY`, q=0, 338 chars | Remediation: needs FIU DOM/XHR or direct document URL. |
| `AE-uaefiu-nra-2024` | `https://uaefiu.gov.ae/en/more/knowledge-centre/publications/national-risk-assessment-report-2024/` | `fiu_eocn_document_listing`, `body` | `NAV_SHELL_ONLY`, q=0, 128 chars | Remediation: likely route/content alias issue. |
| `AE-uaefiu-strategic-analysis` | `https://uaefiu.gov.ae/en/more/knowledge-centre/publications/strategic-analysis-guidelines/` | `fiu_eocn_document_listing`, `body` | `NAV_SHELL_ONLY`, q=0, 128 chars | Remediation: likely route/content alias issue. |
| `AE-uaefiu-mutual-evaluation` | `https://uaefiu.gov.ae/en/more/knowledge-centre/publications/uae-mutual-evaluation-report/` | `fiu_eocn_document_listing`, `body` | q=65 but hash duplicates active `AE-uaefiu-typology-reports` | Held: duplicate active normalized hash; find a specific document URL. |
| `AE-eocn-news-en` | `https://www.eocn.gov.ae/en-us/news` | initial generic `listing`, then `eocn_news_listing` | Generic listing over-scored navigation; source-specific adapter passed q=65 with 6 news cards | Activated after proof, baseline, dry-run, and gates. |
| `AE-adgm-ra-notices` | `https://www.adgm.com/registration-authority/notices` | `custom_element` | `NAV_SHELL_ONLY`, q=0, 1173 chars | Remediation: alternate ADGM component selector needed. |
| `AE-adgm-ra-aml-guides` | `https://www.adgm.com/registration-authority/aml-cft-quick-guides` | `custom_element` | `NAV_SHELL_ONLY`, q=0, 1173 chars | Remediation: alternate ADGM component selector needed. |
| `AE-adgm-listing-rules` | `https://www.adgm.com/financial-services-regulatory-authority/listing-authority/rules-and-guidance` | `custom_element` | `NAV_SHELL_ONLY`, q=0, 1188 chars | Remediation: alternate ADGM component selector needed. |

## Evidence And Baseline

`AE-eocn-news-en` and `AE-sca-regulations-listing` proceeded beyond no-save.

- Evidence run 1: `data/source_snapshots/2026-06-15/AE/AE-eocn-news-en/intake-20260615T180807Z/proof.json`
- Evidence run 2: `data/source_snapshots/2026-06-15/AE/AE-eocn-news-en/intake-20260615T180845Z/proof.json`
- Hash stability: stable, `65507c102bc975d9a13f0cf3def4a59b2215cc5604d3404ddfa7e9e19df730ba`
- Mass-monitor dry-run: `MONITOR_OK`, `change_detected=false`, `evidence_written=false`, `alert_sent=false`

- Evidence run 1: `data/source_snapshots/2026-06-15/AE/AE-sca-regulations-listing/intake-20260615T182128Z/proof.json`
- Evidence run 2: `data/source_snapshots/2026-06-15/AE/AE-sca-regulations-listing/intake-20260615T182145Z/proof.json`
- Hash stability: stable, `fecd262a251402488e62b2fcfc2cefc71cd50ac41b7312550a85f4d0dd5cdada`
- Mass-monitor dry-run: `MONITOR_OK`, `change_detected=false`, `evidence_written=false`, `alert_sent=false`

## Cycle 2: SCA No-Save Retest

| Source ID | No-save result | Decision |
| --- | --- | --- |
| `AE-sca-corporate-governance` | `NAV_SHELL_ONLY`, q=0, two extracted items only | Remediation: likely better represented inside the general regulations listing or needs a detail-specific adapter. |
| `AE-sca-fatca-crs` | q=59, 3 items, can_save=false | Near-pass hold: needs richer context/direct document extraction. |
| `AE-sca-market-rules` | `NAV_SHELL_ONLY`, q=0, two official external links to ADX/DFM | Hold: consider ADX/DFM officially linked sources separately, not this shallow SCA page. |
| `AE-sca-regulations-listing` | q=65, 59 regulatory items, can_save=true | Activated after invalid pseudo-link cleanup, proof, baseline, dry-run, and gates. |

## Batch-Onboarding Lesson

The factory can safely batch-test and classify candidates, but generic listing adapters can over-score navigation-heavy pages. Source-specific adapters must be available before evidence save. The EOCN adapter converted one false generic pass into one honest activation-ready source, and the SCA adapter cleanup converted one broader regulatory listing into a stable active source.

## Continuation Cycle: SCA FATCA/CRS + ADGM Listing Authority

Date: 2026-06-16

| Source ID | URL | Adapter | No-save | Evidence | Baseline | Mass-monitor dry-run | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `AE-sca-fatca-crs` | `https://www.sca.gov.ae/en/regulations/automatic-exchange-of-information-fatca-and-crs` | `sca_listing` with `main`, candidate scan 800 | q=65, `CONFIRMED_ACCESSIBLE`, `can_save_evidence=true`, hash `903d395f...` | 2 proof runs written | 2/2 stable, `MONITORING_CERTIFIED` | `MONITOR_OK`, no change, no alert, no evidence write | Activated |
| `AE-adgm-listing-rules` | `https://www.adgm.com/financial-services-regulatory-authority/listing-authority/rules-and-guidance` | `adgm_fsra_listing` with `adgm-section` | q=62, `CONFIRMED_ACCESSIBLE`, `can_save_evidence=true`, hash `05953b82...` | 2 proof runs written | 2/2 stable, `MONITORING_CERTIFIED` | `MONITOR_OK`, no change, no alert, no evidence write | Activated |

No broad monitoring was run. The mass-monitor check used a temporary activation-ready queue containing only these two proven candidates.
