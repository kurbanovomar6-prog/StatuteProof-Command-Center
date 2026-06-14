# ADGM/FSRA + SCA Noise And Source-Health Risk Report

## 1. Executive Summary

The selector remediation sprint found several promising no-save extraction paths, but most require source-specific noise controls before default-pack activation.

No result in this report is evidence-confirmed. No result is monitoring-ready.

## 2. Per-Source Risk Table

| Source model | Noise risk | Source-health risk | Main false-positive causes | Maintenance risks | Recommendation |
|---|---|---|---|---|---|
| ADGM rules/regulations | medium | medium | Rulebook index changes, footer/legal links, linked Thomson Reuters platform changes | ADGM custom elements; source should probably point to official index plus linked rulebook platform | `monitor_with_noise_filters` |
| ADGM guidance/policy statements | high | medium | Large guidance/template/document listing; many document links; possible template churn | Long page, custom elements, PDF/docx link changes | `monitor_with_noise_filters` |
| ADGM public consultations | high | medium | Closed consultation archive, year filters, old consultation entries, pagination/archive churn | Very long listing; item-level diff needed | `monitor_with_noise_filters` |
| ADGM additional obligations / enforcement-adjacent | medium | medium | Broad page mixes supervision, reporting, circulars, enforcement, regulatory actions, alerts | Source model is broad; may need split selectors later | `monitor_with_noise_filters` |
| ADGM financial crime prevention | low | medium | Static AML/TFS explainer plus linked references; lower listing churn than consultations | Custom elements; no proof/baseline yet | `good_monitoring_candidate` after saved evidence/baseline |
| ADGM public registers | medium | high | Search/register copy, entity counts, search-widget changes | Register/search adapter needed; shallow text | `remediation_needed` |
| SCA latest regulations | medium | high | Compact latest-regulations list, changing order, counters, new item titles | ASP.NET widgets; must avoid CAPTCHA/feedback chrome with `[data-icms-list]` | `monitor_as_listing_only` |
| SCA circulars/rules/procedures | medium | high | Card ordering, view-detail links, shallow listing text | Current extraction below threshold; item adapter needed | `remediation_needed` |
| SCA AML/CFT | low | medium | AML page content plus linked/listing widgets; likely lower noise than general filter pages | ASP.NET widget; selector must stay `[data-icms-list]` to avoid CAPTCHA chrome | `good_monitoring_candidate` after saved evidence/baseline |
| SCA regulations listing/filter | high | high | Search filters, category lists, feedback/CAPTCHA fragments, dynamic filter UI | Selector instability; `#accordion-collapse` timed out | `remediation_needed` |

## 3. Sources Safe For Next Validation

These are the best candidates for a future saved evidence/baseline sprint:

- ADGM financial crime prevention.
- ADGM rules/regulations.
- ADGM guidance/policy statements.
- SCA AML/CFT.
- SCA latest regulations, but only as a listing source with `[data-icms-list]`.

## 4. Sources Needing Noise Filters

- ADGM public consultations: item-level title/date/status diffing is required; whole-page hash diffs would likely be noisy.
- ADGM guidance/policy statements: document-list changes should be normalized to title, URL, and document type.
- ADGM additional obligations: split into section-level monitors if possible.
- SCA latest regulations: monitor item titles and detail URLs, not the full page chrome.

## 5. Sources Needing Source-Health Safeguards

- ADGM custom-element pages: selectors should prefer `adgm-page > span`; broad `adgm-page` is unsafe because it includes navigation/footer.
- SCA ASP.NET pages: selectors should avoid feedback forms, CAPTCHA fragments, and full `main` on filter-heavy pages.
- SCA regulations listing: needs a source-specific adapter or a stable rendered list selector before it can be trusted.
- ADGM public registers: needs a register/search-source model instead of normal page-text monitoring.

## 6. Sources To Keep Out Of Default Pack For Now

- ADGM public registers.
- SCA circulars/rules/procedures.
- SCA regulations listing/filter page.
- Legacy SCA `/en/legislation*.aspx` URLs.
- Legacy ADGM `/fsra/rules-and-regulations`, `/fsra/guidance-and-policy-statements`, `/fsra/notices`, and `/fsra/consultations` URLs.

## 7. Source-Specific Remediation Hints

- ADGM: use `adgm-page > span`, then consider section-level selectors only after saved evidence proves stable output.
- ADGM consultations: implement item-level normalization with fields such as title, year, consultation date, closing date, status, source authority, and detail/PDF URL.
- SCA latest regulations: use `[data-icms-list]`; monitor as listing-only and normalize rows/title links.
- SCA AML/CFT: use `[data-icms-list]`; save proof/baseline before any customer-visible readiness change.
- SCA circulars: implement card extraction from `main section` with item title and detail URL; current normalized length is below threshold.
- SCA regulations listing: investigate official API/list endpoints or rendered post-load selectors; do not activate with `main`.
