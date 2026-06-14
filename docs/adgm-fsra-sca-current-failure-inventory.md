# ADGM/FSRA + SCA Current Failure Inventory

## 1. Scope

This inventory covers only ADGM/FSRA and UAE Securities and Commodities Authority (SCA) candidates from the top-40 UAE source validation sprint.

Current customer-facing source truth remains unchanged:

**13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation.**

No evidence was saved in the prior sprint. No ADGM/FSRA or SCA candidate is evidence-confirmed or monitoring-ready.

## 2. ADGM/FSRA Candidates

| Candidate | Tested URL | Prior readiness | Quality | Nav shell | Blocked/access risk | Noise risk | Health risk | Failure inventory verdict |
|---|---|---:|---:|---|---|---|---|---|
| `AE-adgm-fsra-homepage` | `https://www.adgm.com/fsra` | `BLOCKED` | 0 / POOR | Partial/chrome-heavy | Yes | high | high | Retry only as a discovery page, not a default monitoring source. It is official, but broad and navigation-heavy. |
| `AE-adgm-legal-framework-rules` | `https://www.adgm.com/legal-framework/rules-and-regulations` | `NAV_SHELL_ONLY` | 0 / POOR | Yes | No explicit block | high | high | Retry with current legal-framework URL investigation. Prior URL likely stale or selector too broad. |
| `AE-adgm-legal-framework-legislation` | `https://www.adgm.com/legal-framework/legislation` | `NAV_SHELL_ONLY` | 0 / POOR | Yes | No explicit block | high | high | Replace or retry only if an official current legislation listing is found. Prior output was 404/navigation shell. |
| `AE-adgm-fsra-rulebooks` | `https://www.adgm.com/fsra/rules-and-regulations` | `NAV_SHELL_ONLY` | 0 / POOR | Yes | No explicit block | high | high | Replace. Prior URL appears stale; it produced the same 404/nav-shell hash as other broken ADGM pages. |
| `AE-adgm-fsra-guidance-policy` | `https://www.adgm.com/fsra/guidance-and-policy-statements` | `NAV_SHELL_ONLY` | 0 / POOR | Yes | No explicit block | high | high | Replace or keep remediation. Prior URL appears stale. |
| `AE-adgm-fsra-notices` | `https://www.adgm.com/fsra/notices` | `NAV_SHELL_ONLY` | 0 / POOR | Yes | No explicit block | high | high | Replace or keep remediation. Prior URL appears stale. |
| `AE-adgm-fsra-public-register` | `https://www.adgm.com/fsra/public-register` | Untested/deferred | n/a | Unknown | Unknown | unknown | unknown | Investigate current official public-register path. Likely search/table adapter risk. |
| `AE-adgm-fsra-consultations` | `https://www.adgm.com/fsra/consultations` | `NAV_SHELL_ONLY` | 0 / POOR | Yes | No explicit block | high | high | Replace or keep remediation. Prior URL appears stale. |
| `AE-adgm-fsra-enforcement` | `https://www.adgm.com/fsra/enforcement` | `CONFIRMED_ACCESSIBLE` | 54 / LIMITED | No strict nav-shell flag, but preview mismatch | No | medium | medium | Retry with official URL and tighter selector. It is the only ADGM/FSRA prior no-save result that looked partially useful, but the content model was unclear. |
| `AE-adgm-data-protection` | `https://www.adgm.com/operating-in-adgm/office-of-data-protection` | Untested/deferred | n/a | Unknown | Unknown | unknown | unknown | Out of first-pass MLRO scope. Keep as later privacy/compliance candidate unless official page proves high signal. |

## 3. SCA Candidates

| Candidate | Tested URL | Prior readiness | Quality | Nav shell/hash issue | Blocked/access risk | Noise risk | Health risk | Failure inventory verdict |
|---|---|---:|---:|---|---|---|---|---|
| `AE-sca-homepage` | `https://www.sca.gov.ae/` | Untested/deferred | n/a | Unknown | Unknown | unknown | unknown | Discovery only. Do not add as default monitoring source if subpages exist. |
| `AE-sca-legislation` | `https://www.sca.gov.ae/en/legislation.aspx` | `BLOCKED` | 23 / POOR | Same `63df29361568` hash as other SCA tested pages | Yes | high | high | Retry only after DOM investigation finds a precise content/list selector or official alternative. |
| `AE-sca-decisions` | `https://www.sca.gov.ae/en/legislation/sca-decisions.aspx` | `BLOCKED` | 23 / POOR | Same `63df29361568` hash as other SCA tested pages | Yes | high | high | Retry only with precise selector or official alternative. Current output is service-directory/chrome-like. |
| `AE-sca-laws` | `https://www.sca.gov.ae/en/legislation/laws.aspx` | `BLOCKED` | 23 / POOR | Same `63df29361568` hash as other SCA tested pages | Yes | high | high | Retry only with precise selector or official alternative. |
| `AE-sca-regulations` | `https://www.sca.gov.ae/en/legislation/regulations.aspx` | `BLOCKED` | 23 / POOR | Same `63df29361568` hash as other SCA tested pages | Yes | high | high | Retry only with precise selector or official alternative. |
| `AE-sca-circulars` | `https://www.sca.gov.ae/en/circulars.aspx` | `BLOCKED` | 23 / POOR | Same `63df29361568` hash as other SCA tested pages | Yes | high | high | Retry only after URL/DOM investigation. Current source model may be wrong. |
| `AE-sca-news` | `https://www.sca.gov.ae/en/media-center/news.aspx` | Untested/deferred | n/a | Unknown | Unknown | unknown | unknown | Lower-signal publication source. Investigate only after legislation/decisions/circulars. |

## 4. Shared Failure Patterns

- Several ADGM/FSRA paths appear stale and return a 404/navigation shell rather than a source-specific listing.
- SCA selected pages produced the same hash and service-directory style preview, which means the parser likely extracted a common page shell rather than the intended legislation content.
- High noise and source-health risks are justified for both groups until precise official URLs, selectors, and source models are proven.
- No prior no-save result for ADGM/FSRA or SCA is enough to create evidence claims, monitoring-ready status, or customer-facing expanded source counts.

## 5. Remediation Direction

- ADGM/FSRA: start from current official ADGM FSRA pages, especially the official `fsra/regulation`, `legal-framework`, `public-registers`, and `publications` surfaces, then test only specific selectors that extract meaningful regulatory text or listings.
- SCA: investigate the official SCA site DOM and any official legislation/listing endpoints before retrying. If SCA keeps returning identical service-shell output, keep SCA in remediation and consider a source-specific adapter or manual official-document inventory next.
- For both groups, accept no-save results only as `PREVIEW_ONLY`. Evidence confirmation still requires save/proof artifacts and baseline runs.
