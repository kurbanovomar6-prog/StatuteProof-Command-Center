# ADGM/FSRA + SCA No-Save Validation Report

## 1. Executive Verdict

Scoped no-save Source Lab checks were run only for ADGM/FSRA and SCA remediation candidates. The first sandboxed Playwright attempt failed locally with macOS Mach port permission errors, so the same scoped no-save checks were rerun outside the sandbox where Playwright could launch.

No evidence was saved. No active monitor was run. No `sources.json` source was changed.

| Metric | Count |
|---|---:|
| Distinct candidate URLs no-save tested outside sandbox | 10 |
| Readiness-supported no-save candidates | 7 |
| Remediation candidates | 3 |
| Rejected candidates | 0 |
| Blocked candidates in final best run | 1 |

Customer-facing source truth remains:

**13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation.**

## 2. Commands Run

Representative command shape:

```bash
python3 run.py source-lab <URL> --js --wait-for-selector "<selector>" --content-selector "<selector>" --no-save --json
```

Selectors used:

- ADGM/FSRA: `adgm-page > span`
- SCA latest regulations: `[data-icms-list]`
- SCA AML/CFT: `[data-icms-list]`
- SCA circulars: `main section`
- SCA regulations listing: `main`, then `#accordion-collapse` retry

## 3. ADGM/FSRA Results

| Candidate / model | Tested URL | Selector | Provider | Length | Hash prefix | Quality | Readiness | Nav shell | Result |
|---|---|---|---|---:|---|---|---|---|---|
| ADGM rules/regulations | `https://www.adgm.com/legal-framework/rules-and-regulations` | `adgm-page > span` | bs4 | 1,849 | `81d1ce45e633` | 56 / LIMITED | `CONFIRMED_ACCESSIBLE` | no | Readiness-supported no-save; baseline required. |
| ADGM guidance/policy | `https://www.adgm.com/legal-framework/guidance-and-policy-statements` | `adgm-page > span` | bs4 | 12,072 | `c18f5c160341` | 59 / LIMITED | `CONFIRMED_ACCESSIBLE` | no | Readiness-supported no-save; high listing/noise risk. |
| ADGM public consultations | `https://www.adgm.com/legal-framework/public-consultations` | `adgm-page > span` | bs4 | 69,504 | `3427e1f1bb66` | 59 / LIMITED | `CONFIRMED_ACCESSIBLE` | no | Readiness-supported no-save; high churn/noise risk. |
| ADGM FSRA obligations / enforcement-adjacent | `https://www.adgm.com/operating-in-adgm/additional-obligations-of-financial-services-entities` | `adgm-page > span` | bs4 | 28,800 | `d286c551c87f` | 54 / LIMITED | `CONFIRMED_ACCESSIBLE` | no | Readiness-supported no-save; model is broader than enforcement. |
| ADGM financial crime prevention | `https://www.adgm.com/operating-in-adgm/financial-and-cyber-crime-prevention` | `adgm-page > span` | bs4 | 4,788 | `fa442e94df6d` | 59 / LIMITED | `CONFIRMED_ACCESSIBLE` | no | Strong MLRO-relevant no-save candidate. |
| ADGM public registers | `https://www.adgm.com/public-registers` | `adgm-page > span` | bs4 | 884 | `e931da9c7b8a` | 49 / LIMITED | `CONFIRMED_ACCESSIBLE` | no | Extractable but shallow; keep remediation until register adapter/baseline. |

ADGM normalized preview examples:

- Rules/regulations: “ADGM Regulations and Rules / Legal Framework / ADGM published its first set of commercial rules and regulations…”
- Financial crime prevention: “Financial & Cyber Crime Prevention / Developing sound practices in AML/TFS and cybercrime prevention compliance…”
- Consultations: “Consultation Paper No. 1 of 2026 – Proposed Enhancements to the Anti-Money Laundering Framework of the FSRA…”

## 4. SCA Results

| Candidate / model | Tested URL | Selector | Provider | Length | Hash prefix | Quality | Readiness | Nav shell | Result |
|---|---|---|---|---:|---|---|---|---|---|
| SCA latest regulations | `https://www.sca.gov.ae/en/regulations/regulations` | `main` | bs4 | 995 | `4856dc07e167` | 0 / POOR | `BLOCKED` | yes | `main` included CAPTCHA/feedback chrome; rejected selector. |
| SCA latest regulations | `https://www.sca.gov.ae/en/regulations/regulations` | `[data-icms-list]` | bs4 | 536 | `5b0c842d72fe` | 49 / LIMITED | `CONFIRMED_ACCESSIBLE` | no | Readiness-supported no-save as listing-only; baseline required. |
| SCA circulars/rules/procedures | `https://www.sca.gov.ae/en/regulations/circulars-rules-and-procedures` | `main section` | bs4 | 314 | `c436f687616a` | 24 / POOR | `JS_RENDERING_NEEDED` | no | Remediation; shallow listing needs adapter or item-level threshold. |
| SCA AML/CFT | `https://www.sca.gov.ae/en/regulations/anti-money-laundering-and-terrorist-financing` | `[data-icms-list]` | bs4 | 12,133 | `ad340acbc7bd` | 59 / LIMITED | `CONFIRMED_ACCESSIBLE` | no | Strong readiness-supported no-save candidate; baseline required. |
| SCA regulations listing | `https://www.sca.gov.ae/en/regulations/regulations-listing` | `main` | bs4 | 9,868 | `9318b50adae7` | 29 / POOR | `BLOCKED` | no | Useful text but CAPTCHA-sensitive filter/feedback chrome; keep remediation. |
| SCA regulations listing | `https://www.sca.gov.ae/en/regulations/regulations-listing` | `#accordion-collapse` | n/a | 0 | n/a | 5 / POOR | `NEEDS_SELECTOR_REVIEW` | no | Selector timeout; keep remediation. |

SCA normalized preview examples:

- Latest regulations: “The Chairman of the Authority’s Board of Directors’ Decision No. (11/ Chairman) of 2026…”
- AML/CFT: “The UAE Capital Market Authority (CMA) is committed to promoting integrity, transparency, and resilience across the UAE’s capital markets…”
- Circulars: “Passporting Rules / FinTech regulatory framework / Guidelines Regulation of Virtual Assets and Virtual Assets Services Providers…”

## 5. Readiness-Supported No-Save Candidates

These are not evidence-confirmed and not monitoring-ready. They may progress to a future saved evidence/baseline task:

1. ADGM rules/regulations.
2. ADGM guidance/policy statements.
3. ADGM public consultations.
4. ADGM additional obligations / enforcement-adjacent page.
5. ADGM financial crime prevention.
6. SCA latest regulations listing.
7. SCA AML/CFT page.

## 6. Remediation Candidates

1. ADGM public registers: extractable but shallow and better treated as a register/search adapter source.
2. SCA circulars/rules/procedures: correct URL found, but current extraction is below reliable threshold.
3. SCA regulations listing/filter page: official and useful, but current selectors either include CAPTCHA-sensitive chrome or time out.

## 7. What Did Not Change

- `sources.json` was not changed.
- No source was marked evidence-confirmed.
- No source was marked monitoring-ready.
- Public source truth did not change.
- No 40-source or 60-source marketing claim is allowed.

## 8. Next Exact Task

Run a saved-evidence baseline sprint for the strongest no-save candidates only: ADGM financial crime prevention, ADGM rules/regulations, SCA AML/CFT, and SCA latest regulations.
