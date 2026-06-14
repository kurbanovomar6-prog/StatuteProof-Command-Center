# Top-40 Alert Fatigue Risk Report

## 1. Executive Summary

The top-40 no-save sprint found high alert-fatigue risk across most candidate sources.

| Metric | Count |
|---|---:|
| Tested sources | 40 |
| Low noise risk | 0 |
| Medium noise risk | 3 |
| High noise risk | 37 |

No source should enter default active monitoring without noise filtering. Even the accepted no-save candidates are listing/module sources and should be monitored with filters rather than raw text diffs.

## 2. Sources Likely To Create Noise

| Candidate | Noise risk | Likely false-positive causes | Recommendation |
|---|---|---|---|
| `AE-adgm-fsra-consultations` | high | nav_or_accessibility_chrome, listing_page_churn, low_quality_score | remediation_needed |
| `AE-adgm-fsra-enforcement` | medium | listing_page_churn | remediation_needed |
| `AE-adgm-fsra-guidance-policy` | high | nav_or_accessibility_chrome, low_quality_score | remediation_needed |
| `AE-adgm-fsra-homepage` | high | nav_or_accessibility_chrome, js_or_waf_rendering, access_policy_warning, low_quality_score | remediation_needed |
| `AE-adgm-fsra-notices` | high | nav_or_accessibility_chrome, listing_page_churn, low_quality_score | remediation_needed |
| `AE-adgm-fsra-rulebooks` | high | nav_or_accessibility_chrome, listing_page_churn, low_quality_score | remediation_needed |
| `AE-adgm-legal-framework-legislation` | high | nav_or_accessibility_chrome, listing_page_churn, low_quality_score | remediation_needed |
| `AE-adgm-legal-framework-rules` | high | nav_or_accessibility_chrome, listing_page_churn, low_quality_score | remediation_needed |
| `AE-sca-circulars` | high | nav_or_accessibility_chrome, access_policy_warning, low_quality_score | remediation_needed |
| `AE-sca-decisions` | high | nav_or_accessibility_chrome, listing_page_churn, access_policy_warning, low_quality_score | remediation_needed |
| `AE-sca-laws` | high | nav_or_accessibility_chrome, listing_page_churn, access_policy_warning, low_quality_score | remediation_needed |
| `AE-sca-legislation` | high | nav_or_accessibility_chrome, listing_page_churn, access_policy_warning, low_quality_score | remediation_needed |
| `AE-sca-regulations` | high | nav_or_accessibility_chrome, listing_page_churn, access_policy_warning, low_quality_score | remediation_needed |
| `AE-vara-aml-cft-rulebook` | high | nav_or_accessibility_chrome, js_or_waf_rendering, low_quality_score | remediation_needed |
| `AE-vara-company-rulebook` | high | nav_or_accessibility_chrome, listing_page_churn, js_or_waf_rendering, low_quality_score | remediation_needed |
| `AE-vara-enforcement` | high | nav_or_accessibility_chrome, listing_page_churn, js_or_waf_rendering, low_quality_score | remediation_needed |
| `AE-vara-homepage` | high | nav_or_accessibility_chrome, js_or_waf_rendering, low_quality_score | remediation_needed |
| `AE-vara-public-register` | high | nav_or_accessibility_chrome, listing_page_churn, js_or_waf_rendering, low_quality_score | remediation_needed |
| `AE-vara-regulatory-framework` | high | nav_or_accessibility_chrome, listing_page_churn, js_or_waf_rendering, low_quality_score | remediation_needed |
| `AE-vara-rulebooks-overview` | high | nav_or_accessibility_chrome, listing_page_churn, js_or_waf_rendering, low_quality_score | remediation_needed |
| `AE-cbuae-aml-cft` | high | nav_or_accessibility_chrome, js_or_waf_rendering, access_policy_warning, low_quality_score | remediation_needed |
| `AE-cbuae-consultations` | high | nav_or_accessibility_chrome, listing_page_churn, js_or_waf_rendering, access_policy_warning, low_quality_score | remediation_needed |
| `AE-cbuae-homepage` | high | js_or_waf_rendering, access_policy_warning, low_quality_score | remediation_needed |
| `AE-cbuae-licensing` | high | nav_or_accessibility_chrome, js_or_waf_rendering, access_policy_warning, low_quality_score | remediation_needed |
| `AE-cbuae-payment-systems` | high | nav_or_accessibility_chrome, js_or_waf_rendering, access_policy_warning, low_quality_score | remediation_needed |
| `AE-cbuae-publications` | high | nav_or_accessibility_chrome, listing_page_churn, js_or_waf_rendering, access_policy_warning, low_quality_score | remediation_needed |
| `AE-cbuae-regulations` | high | nav_or_accessibility_chrome, listing_page_churn, js_or_waf_rendering, access_policy_warning, low_quality_score | remediation_needed |
| `AE-uaefiu-goaml-public` | high | nav_or_accessibility_chrome, access_policy_warning, low_quality_score | remediation_needed |
| `AE-uaefiu-laws-regulations` | high | nav_or_accessibility_chrome, listing_page_churn, access_policy_warning, low_quality_score | remediation_needed |
| `AE-uaefiu-publications` | high | nav_or_accessibility_chrome, listing_page_churn, access_policy_warning, low_quality_score | remediation_needed |
| `AE-eocn-homepage` | high | nav_or_accessibility_chrome, access_policy_warning, low_quality_score | remediation_needed |
| `AE-moec-aml` | high | nav_or_accessibility_chrome, access_policy_warning, low_quality_score | remediation_needed |
| `AE-mof-homepage` | high | nav_or_accessibility_chrome, access_policy_warning, low_quality_score | remediation_needed |
| `AE-uae-legislation-portal` | high | nav_or_accessibility_chrome, listing_page_churn, js_or_waf_rendering, low_quality_score | remediation_needed |
| `AE-dfsa-aml-mlro-notices` | medium | js_or_waf_rendering | monitor_with_noise_filters |
| `AE-dfsa-consultation-papers` | high | nav_or_accessibility_chrome, listing_page_churn, js_or_waf_rendering, access_policy_warning, low_quality_score | remediation_needed |
| `AE-dfsa-enforcement-regulatory-actions` | high | nav_or_accessibility_chrome, listing_page_churn, js_or_waf_rendering, access_policy_warning, low_quality_score | remediation_needed |
| `AE-dfsa-rulebook-official` | high | nav_or_accessibility_chrome, listing_page_churn, js_or_waf_rendering, access_policy_warning, low_quality_score | remediation_needed |
| `AE-dfsa-rulebook-thomsonreuters` | medium | listing_page_churn, js_or_waf_rendering | monitor_with_noise_filters |
| `AE-difc-laws-regulations` | high | listing_page_churn, access_policy_warning, low_quality_score | remediation_needed |


## 3. Sources Safer For Monitoring

No candidate in this sprint earned low noise risk.

The two best candidates are medium-noise only:

- `AE-dfsa-rulebook-thomsonreuters`: monitor with module-level filters and ignore navigation/header/footer boilerplate.
- `AE-dfsa-aml-mlro-notices`: monitor listing items with title/date/link extraction rather than whole-page diffing.

## 4. Sources Needing Special Diff Filters

- DFSA rulebook modules: module/title/version filters; ignore boilerplate navigation and static layout text.
- DFSA AML/MLRO notices: listing item extraction; ignore tab/container chrome.
- SCA pages: extract actual legislation table/list only; current output appears service-directory/chrome-heavy.
- CBUAE pages: filter notifications/accessibility/date widgets; source-specific selectors required.
- UAE FIU pages: filter search/accessibility chrome; public guidance pages may need item-level extraction.
- VARA pages: avoid not-found shells; use verified current URLs and selectors or PDF-aware extraction.

## 5. Alert-Fatigue Recommendation

Do not market or activate a 40-source pack yet. The next engineering task should build source-specific selectors and item-level extraction for high-value regulators before increasing coverage claims.
