# ADGM/FSRA + SCA Selector Remediation Final Report

## 1. Executive Verdict

Better official URLs and selectors were found for ADGM/FSRA and UAE SCA. Several sources can now progress to a tightly scoped saved-evidence baseline sprint, but none should be shown as evidence-confirmed or monitoring-ready yet.

| Metric | Result |
|---|---:|
| ADGM/FSRA candidates investigated | 10 |
| SCA candidates investigated | 8 |
| Distinct candidate URLs no-save tested outside sandbox | 10 |
| Readiness-supported no-save count | 7 |
| Remediation count | 3 |
| Rejected count | 0 |
| Blocked count in best-run result set | 1 |
| `sources.json` changed | no |
| Public source truth changed | no |

No evidence was saved. No broad monitoring was run. No customer-facing source count changed.

Current customer-facing truth remains:

**13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation.**

## 2. ADGM/FSRA Findings

| Candidate | Recommended URL | Selector | No-save result | Noise risk | Health risk | Recommendation |
|---|---|---|---|---|---|---|
| `AE-adgm-fsra-rulebooks` | `https://www.adgm.com/legal-framework/rules-and-regulations` | `adgm-page > span` | `CONFIRMED_ACCESSIBLE`, 1,849 chars, quality 56 / LIMITED | medium | medium | Save/baseline candidate. |
| `AE-adgm-fsra-guidance-policy` | `https://www.adgm.com/legal-framework/guidance-and-policy-statements` | `adgm-page > span` | `CONFIRMED_ACCESSIBLE`, 12,072 chars, quality 59 / LIMITED | high | medium | Add item-level filters before default-pack activation. |
| `AE-adgm-fsra-consultations` | `https://www.adgm.com/legal-framework/public-consultations` | `adgm-page > span` | `CONFIRMED_ACCESSIBLE`, 69,504 chars, quality 59 / LIMITED | high | medium | Add consultation item diff filters before activation. |
| `AE-adgm-fsra-enforcement` | `https://www.adgm.com/operating-in-adgm/additional-obligations-of-financial-services-entities` | `adgm-page > span` | `CONFIRMED_ACCESSIBLE`, 28,800 chars, quality 54 / LIMITED | medium | medium | Source label is too broad for pure enforcement; split or rename before activation. |
| `AE-adgm-fsra-financial-crime-prevention` | `https://www.adgm.com/operating-in-adgm/financial-and-cyber-crime-prevention` | `adgm-page > span` | `CONFIRMED_ACCESSIBLE`, 4,788 chars, quality 59 / LIMITED | low | medium | Strong MLRO candidate for saved baseline. |
| `AE-adgm-fsra-public-register` | `https://www.adgm.com/public-registers` | `adgm-page > span` | `CONFIRMED_ACCESSIBLE`, 884 chars, quality 49 / LIMITED | medium | high | Keep remediation; needs register/search adapter. |

Key selector decision:

- Use `adgm-page > span` for ADGM page bodies.
- Do not use broad `adgm-page` because it includes navigation and footer.
- Avoid stale `/fsra/...` URLs that return 404/navigation shells.

## 3. SCA Findings

| Candidate | Recommended URL | Selector | No-save result | Noise risk | Health risk | Recommendation |
|---|---|---|---|---|---|---|
| `AE-sca-latest-regulations` | `https://www.sca.gov.ae/en/regulations/regulations` | `[data-icms-list]` | `CONFIRMED_ACCESSIBLE`, 536 chars, quality 49 / LIMITED | medium | high | Listing-only saved baseline candidate with row/item normalization. |
| `AE-sca-aml-cft` | `https://www.sca.gov.ae/en/regulations/anti-money-laundering-and-terrorist-financing` | `[data-icms-list]` | `CONFIRMED_ACCESSIBLE`, 12,133 chars, quality 59 / LIMITED | low | medium | Strong MLRO candidate for saved baseline. |
| `AE-sca-circulars` | `https://www.sca.gov.ae/en/regulations/circulars-rules-and-procedures` | `main section` | `JS_RENDERING_NEEDED`, 314 chars, quality 24 / POOR | medium | high | Keep remediation; needs item/card adapter. |
| SCA regulations listing/filter | `https://www.sca.gov.ae/en/regulations/regulations-listing` | `main` / `#accordion-collapse` tried | `BLOCKED` or `NEEDS_SELECTOR_REVIEW` | high | high | Keep remediation; full page includes CAPTCHA-sensitive/filter chrome. |

Key selector decision:

- Use `[data-icms-list]` for SCA latest regulations and AML/CFT pages.
- Do not use broad `main` for SCA filter/listing pages because it can include feedback/CAPTCHA-sensitive chrome.
- Do not use legacy `/en/legislation*.aspx` URLs; they redirect to home or shell pages.
- Keep source labels as UAE SCA. The English page chrome may say CMA, but this is not Saudi CMA.

## 4. Best Candidate Sources

The best next-step saved-evidence candidates are:

1. `AE-adgm-fsra-financial-crime-prevention`
2. `AE-adgm-fsra-rulebooks`
3. `AE-sca-aml-cft`
4. `AE-sca-latest-regulations`

These are still no-save, preview-only candidates. They require saved proof artifacts and baseline runs before source-readiness claims can change.

## 5. Sources Still Broken

| Source | Why still broken |
|---|---|
| `AE-adgm-fsra-public-register` | Extractable but shallow; register/search source model needed. |
| `AE-sca-circulars` | Correct URL found, but extraction is too shallow and needs an item/card adapter. |
| SCA regulations listing/filter | Selector instability and CAPTCHA-sensitive full-page chrome. |
| Legacy ADGM `/fsra/...` paths | Return 404/nav-shell content. |
| Legacy SCA `/en/legislation*.aspx` paths | Redirect to home/service-shell output. |

## 6. Noise Risk

Low-noise candidates:

- ADGM financial crime prevention.
- SCA AML/CFT.

Medium-noise candidates:

- ADGM rules/regulations.
- ADGM additional obligations / enforcement-adjacent page.
- SCA latest regulations, but only as a listing source.
- ADGM public registers.

High-noise candidates:

- ADGM guidance/policy statements.
- ADGM public consultations.
- SCA regulations listing/filter page.

Noise filters needed:

- normalize listing rows and title/detail URLs;
- ignore footer, navigation, feedback widgets, and filter controls;
- use item-level diffs for consultation and guidance archives;
- avoid whole-page hash alerts on long archive pages.

## 7. Source Health Risk

Medium source-health risk:

- ADGM pages that rely on custom elements and `adgm-page > span`;
- SCA AML/CFT page that relies on `[data-icms-list]`.

High source-health risk:

- ADGM public registers because it is a register/search surface;
- SCA latest regulations unless treated as listing-only;
- SCA circulars and regulations listing until adapter work is complete.

Source-health safeguards needed:

- selector timeout maps to remediation, not confirmed;
- nav-shell and duplicate-hash checks remain required;
- no-save results remain `PREVIEW_ONLY`;
- saved baseline must include proof artifacts before evidence claims.

## 8. Candidate Registry Changes

Updated `product/regradar/config/uae_source_candidates.json` with:

- recommended URLs;
- recommended wait/content selectors;
- no-save test results;
- normalized lengths and hashes;
- readiness statuses;
- activation readiness;
- noise risk;
- source-health risk;
- remediation hints;
- recommended next actions.

Added research-only candidates:

- `AE-adgm-fsra-financial-crime-prevention`
- `AE-sca-aml-cft`

Both are `top_40_candidate: false` and `top_60_candidate: false` because they were discovered during remediation, not part of the original 60-candidate map. They should be considered for a future curated pack only after saved evidence and baseline checks.

## 9. `sources.json` Decision

`product/regradar/sources.json` was not changed.

Reason:

- no saved evidence was created;
- no baseline runs exist;
- some strong candidates still need source-specific noise filters;
- SCA listing candidates need listing-specific normalization;
- public source truth must not change from no-save tests alone.

## 10. Customer-Facing Truth

Current public source truth remains:

**13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation.**

Allowed internal/customer-safe wording:

- “ADGM/FSRA and SCA selector remediation found no-save next-step candidates.”
- “No-save results are preview-only and require saved evidence/baseline runs.”
- “ADGM/FSRA and SCA are still under source-expansion validation.”

Forbidden wording:

- “ADGM/FSRA is monitoring-ready.”
- “SCA is monitoring-ready.”
- “40+ UAE sources monitored.”
- “60 validated sources.”
- “Evidence confirmed” for any no-save-only candidate.

## 11. Next Exact Task

Run a saved-evidence baseline sprint for four strongest candidates only: ADGM financial crime prevention, ADGM rules/regulations, SCA AML/CFT, and SCA latest regulations.
