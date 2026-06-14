# ADGM/FSRA + SCA DOM Selector Investigation

## 1. Executive Summary

This investigation found better official URLs and selectors for ADGM/FSRA and UAE SCA candidates. It does not make any source evidence-confirmed or monitoring-ready.

Current customer-facing source truth remains:

**13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation.**

## 2. Browser / DOM Findings

### ADGM/FSRA

Official ADGM pages use custom light-DOM elements. Broad selectors like `adgm-page` include the mega-menu and footer, which caused prior nav-shell output. The useful body content is the third child of `adgm-page`, selectable as:

`adgm-page > span`

This selector skips `adgm-navigation` and `adgm-footer` and extracts the actual page body.

Important official URL corrections:

| Prior candidate | Prior URL issue | Better official URL / model | Selector | Verdict |
|---|---|---|---|---|
| `AE-adgm-fsra-rulebooks` | `/fsra/rules-and-regulations` returned a 404/nav shell. | `https://www.adgm.com/legal-framework/rules-and-regulations` | `adgm-page > span` | no-save-test-now |
| `AE-adgm-fsra-guidance-policy` | `/fsra/guidance-and-policy-statements` returned a 404/nav shell. | `https://www.adgm.com/legal-framework/guidance-and-policy-statements` | `adgm-page > span` | no-save-test-now |
| `AE-adgm-fsra-consultations` | `/fsra/consultations` returned a 404/nav shell. | `https://www.adgm.com/legal-framework/public-consultations` | `adgm-page > span` | no-save-test-now |
| `AE-adgm-fsra-enforcement` | Prior page parsed but source model was unclear. | `https://www.adgm.com/operating-in-adgm/additional-obligations-of-financial-services-entities` | `adgm-page > span` | no-save-test-now, but model is broader than enforcement. |
| New ADGM MLRO candidate | Not in original top-40 as a direct source. | `https://www.adgm.com/operating-in-adgm/financial-and-cyber-crime-prevention` | `adgm-page > span` | no-save-test-now |
| `AE-adgm-fsra-public-register` | Deferred because of search/table risk. | `https://www.adgm.com/public-registers` | `adgm-page > span` | no-save-test-now, but likely register adapter needed. |

Rejected ADGM selector:

- `adgm-page`: matches the custom page wrapper but includes navigation and footer. It produced nav-shell output for ADGM rules/regulations and should not be used for activation.

### UAE SCA

The prior SCA URLs under `/en/legislation.aspx` and `/en/legislation/...` are obsolete. Header checks showed `/en/legislation.aspx` redirects through `/404.aspx?aspxerrorpath=/en/legislation.aspx` to `/en/home`, which explains the identical service-shell hashes in the top-40 sprint.

The official SCA site currently exposes better English paths under:

`https://www.sca.gov.ae/en/regulations/...`

The site labels itself “Capital Market Authority” or “CMA” in English page chrome, but the official domain and page metadata are UAE SCA. Source labels must say UAE SCA to avoid confusion with Saudi CMA.

| Prior candidate | Prior URL issue | Better official URL / model | Selector | Verdict |
|---|---|---|---|---|
| `AE-sca-regulations` | `/en/legislation/regulations.aspx` redirected to home/service shell. | `https://www.sca.gov.ae/en/regulations/regulations` | `[data-icms-list]` | no-save-test-now |
| `AE-sca-circulars` | `/en/circulars.aspx` produced common service shell. | `https://www.sca.gov.ae/en/regulations/circulars-rules-and-procedures` | `main section` | no-save-test-now, but likely shallow/listing adapter needed. |
| New SCA AML/CFT candidate | Not in original candidate map. | `https://www.sca.gov.ae/en/regulations/anti-money-laundering-and-terrorist-financing` | `[data-icms-list]` | no-save-test-now |
| `AE-sca-legislation` / `AE-sca-laws` | Legacy legislation URLs are stale. | `https://www.sca.gov.ae/en/regulations/regulations-listing` | `main` was noisy; `#accordion-collapse` timed out. | keep-remediation |

SCA selector notes:

- `main` is useful for inspection, but can include feedback/CAPTCHA-related fragments that trigger the protected-source policy.
- `[data-icms-list]` successfully narrowed SCA latest-regulations and AML/CFT pages and avoided the false CAPTCHA block.
- `main section` extracted SCA circular card titles but remained below the reliable content threshold.
- `#accordion-collapse` was not present in the rendered SCA regulations-listing page within the Source Lab timeout.

## 3. Recommended Source IDs

ADGM/FSRA:

- `AE-adgm-fsra-rulebooks`: keep as candidate, but point future tests to `https://www.adgm.com/legal-framework/rules-and-regulations`.
- `AE-adgm-fsra-guidance-policy`: update future tests to `https://www.adgm.com/legal-framework/guidance-and-policy-statements`.
- `AE-adgm-fsra-consultations`: update future tests to `https://www.adgm.com/legal-framework/public-consultations`.
- `AE-adgm-fsra-enforcement`: do not use a pure enforcement label unless a pure enforcement listing is found. Use the additional-obligations page as a broader FSRA obligations/enforcement/circulars candidate.
- Add or consider `AE-adgm-fsra-financial-crime-prevention` as a distinct MLRO-relevant candidate.
- Keep `AE-adgm-fsra-public-register` as a candidate, but do not activate without a register/search adapter.

SCA:

- Replace legacy legislation URLs with specific current paths.
- Consider new `AE-sca-latest-regulations` for `https://www.sca.gov.ae/en/regulations/regulations`.
- Consider new `AE-sca-aml-cft` for `https://www.sca.gov.ae/en/regulations/anti-money-laundering-and-terrorist-financing`.
- Keep `AE-sca-circulars` in remediation until a listing adapter or lower listing threshold is implemented.
- Keep `AE-sca-regulations-listing` in remediation because the filter/search page still includes CAPTCHA-sensitive chrome and selector instability.

## 4. Noise And Health Risk Notes

- ADGM guidance and consultations are long official listings. They are promising but high-churn unless monitored with item-level diff filters.
- ADGM public register is a search/register surface. It should not be treated as a normal text page.
- SCA latest regulations is a compact table/list. It is useful but shallow and should be monitored as a listing only.
- SCA AML/CFT is the strongest SCA candidate because it contains substantive AML/financial-crime text.
- SCA regulations listing and circulars need adapter work before default-pack activation.

## 5. Customer-Facing Boundary

Do not say ADGM or SCA is ready, evidence-confirmed, or part of a 40-source monitored pack.

Allowed internal wording:

- “ADGM/FSRA and SCA selector remediation found several no-save next-step candidates.”
- “No-save checks are preview-only; saved evidence and baselines are still required.”
- “Current public source truth remains 13 enabled / 9 readiness-supported / 4 remediation.”
