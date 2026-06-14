# Top-40 Source Health Risk Report

## 1. Executive Summary

The top-40 no-save sprint found high maintenance/source-health risk across most candidates.

| Metric | Count |
|---|---:|
| Tested sources | 40 |
| Low source-health risk | 0 |
| Medium source-health risk | 3 |
| High source-health risk | 37 |

This is not a failure of the product promise. It is the expected result of testing official regulatory websites honestly: many are public but not safely monitorable without exact selectors, item-level extraction, or source-specific adapters.

## 2. High-Maintenance Sources

| Candidate | Health risk | Recommended health status | Maintenance notes |
|---|---|---|---|
| `AE-adgm-fsra-consultations` | high | remediation_required | selector=high; access=low; anti_bot=low; manual_check=True |
| `AE-adgm-fsra-guidance-policy` | high | remediation_required | selector=high; access=low; anti_bot=low; manual_check=True |
| `AE-adgm-fsra-homepage` | high | blocked | selector=high; access=high; anti_bot=high; manual_check=True |
| `AE-adgm-fsra-notices` | high | remediation_required | selector=high; access=low; anti_bot=low; manual_check=True |
| `AE-adgm-fsra-rulebooks` | high | remediation_required | selector=high; access=low; anti_bot=low; manual_check=True |
| `AE-adgm-legal-framework-legislation` | high | remediation_required | selector=high; access=low; anti_bot=low; manual_check=True |
| `AE-adgm-legal-framework-rules` | high | remediation_required | selector=high; access=low; anti_bot=low; manual_check=True |
| `AE-sca-circulars` | high | blocked | selector=low; access=high; anti_bot=high; manual_check=True |
| `AE-sca-decisions` | high | blocked | selector=high; access=high; anti_bot=high; manual_check=True |
| `AE-sca-laws` | high | blocked | selector=high; access=high; anti_bot=high; manual_check=True |
| `AE-sca-legislation` | high | blocked | selector=high; access=high; anti_bot=high; manual_check=True |
| `AE-sca-regulations` | high | blocked | selector=high; access=high; anti_bot=high; manual_check=True |
| `AE-vara-aml-cft-rulebook` | high | remediation_required | selector=high; access=medium; anti_bot=low; manual_check=True |
| `AE-vara-company-rulebook` | high | remediation_required | selector=high; access=medium; anti_bot=low; manual_check=True |
| `AE-vara-enforcement` | high | remediation_required | selector=high; access=medium; anti_bot=low; manual_check=True |
| `AE-vara-homepage` | high | remediation_required | selector=high; access=medium; anti_bot=low; manual_check=True |
| `AE-vara-public-register` | high | remediation_required | selector=high; access=medium; anti_bot=low; manual_check=True |
| `AE-vara-regulatory-framework` | high | remediation_required | selector=high; access=medium; anti_bot=low; manual_check=True |
| `AE-vara-rulebooks-overview` | high | remediation_required | selector=high; access=medium; anti_bot=low; manual_check=True |
| `AE-cbuae-aml-cft` | high | blocked | selector=high; access=high; anti_bot=high; manual_check=True |
| `AE-cbuae-consultations` | high | blocked | selector=high; access=high; anti_bot=high; manual_check=True |
| `AE-cbuae-homepage` | high | blocked | selector=medium; access=high; anti_bot=high; manual_check=True |
| `AE-cbuae-licensing` | high | blocked | selector=medium; access=high; anti_bot=high; manual_check=True |
| `AE-cbuae-payment-systems` | high | blocked | selector=high; access=high; anti_bot=high; manual_check=True |
| `AE-cbuae-publications` | high | blocked | selector=high; access=high; anti_bot=high; manual_check=True |
| `AE-cbuae-regulations` | high | blocked | selector=medium; access=high; anti_bot=high; manual_check=True |
| `AE-uaefiu-goaml-public` | high | blocked | selector=high; access=high; anti_bot=high; manual_check=True |
| `AE-uaefiu-laws-regulations` | high | blocked | selector=high; access=high; anti_bot=high; manual_check=True |
| `AE-uaefiu-publications` | high | blocked | selector=high; access=high; anti_bot=high; manual_check=True |
| `AE-eocn-homepage` | high | blocked | selector=high; access=high; anti_bot=high; manual_check=True |
| `AE-moec-aml` | high | blocked | selector=high; access=high; anti_bot=high; manual_check=True |
| `AE-mof-homepage` | high | blocked | selector=high; access=high; anti_bot=high; manual_check=True |
| `AE-uae-legislation-portal` | high | remediation_required | selector=high; access=high; anti_bot=high; manual_check=True |
| `AE-dfsa-consultation-papers` | high | blocked | selector=high; access=high; anti_bot=high; manual_check=True |
| `AE-dfsa-enforcement-regulatory-actions` | high | blocked | selector=high; access=high; anti_bot=high; manual_check=True |
| `AE-dfsa-rulebook-official` | high | blocked | selector=high; access=high; anti_bot=high; manual_check=True |
| `AE-difc-laws-regulations` | high | blocked | selector=high; access=high; anti_bot=high; manual_check=True |


## 3. Lower-Maintenance Candidates

No candidate earned low source-health risk.

Medium source-health candidates:

| Candidate | Health risk | Why not low risk |
|---|---|---|
| `AE-adgm-fsra-enforcement` | medium | baseline required; listing/module page; noise filters required; evidence level remains `PREVIEW_ONLY`. |
| `AE-dfsa-aml-mlro-notices` | medium | baseline required; listing/module page; noise filters required; evidence level remains `PREVIEW_ONLY`. |
| `AE-dfsa-rulebook-thomsonreuters` | medium | baseline required; listing/module page; noise filters required; evidence level remains `PREVIEW_ONLY`. |


## 4. Sources Needing Manual Selector Review

Priority selector/URL remediation:

1. ADGM/FSRA rulebooks, notices, guidance, and enforcement: current candidate URLs often resolve to 404/nav-shell or mismatched content.
2. SCA legislation/decisions/laws/regulations: current pages share service-directory-like output and identical hashes; item/table selector required.
3. VARA regulatory framework/rulebook/public register: several candidate URLs return not-found shells; discover current official rulebook/PDF URLs.
4. CBUAE regulations/AML/payment pages: access warnings and widget noise require source-specific selectors and possibly stable API/listing discovery.
5. UAE FIU publications/goAML/laws: public pages need search/accessibility chrome filtering and exact content containers.

## 5. Sources That Should Stay Out Of Default Active Pack

Until remediated, keep these out of active default monitoring:

- all ADGM/FSRA top-40 candidates except as remediation examples;
- all SCA top-40 candidates;
- all VARA rulebook/register candidates;
- all CBUAE expansion candidates;
- all UAE FIU expansion candidates;
- broad federal portal/homepage candidates;
- DFSA official/consultation/enforcement pages except the two no-save-accessible candidates.

## 6. Recommended Health-State Handling

Use these customer-facing states:

- `REMEDIATION_REQUIRED` for nav-shell, blocked, 404 shell, or mismatched source model.
- `MANUAL_CHECK_REQUIRED` for pages with medium quality but unresolved noise/health risk.
- `MONITOR_DEGRADED_CANDIDATE` for no-save accessible sources that still require baseline and filters.

Do not show `MONITOR_OK` for any top-40 candidate from this sprint.
