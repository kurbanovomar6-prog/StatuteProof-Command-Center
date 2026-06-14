# DFSA Selector Investigation Report

Date: 2026-06-14

Scope: live browser/Playwright investigation plus no-save Source Lab checks for the two DFSA remediation sources only. No evidence was saved, no broad monitoring was run, no alerts were sent, and `sources.json` was not changed.

## 1. Executive Result

| Source | Result |
|---|---|
| `AE-dubai-financial-services-authority-dfsa` | Failed strict remediation-exit gate. A strong replacement URL/selector was found, but no-save result remains `PREVIEW_ONLY` with `quality_label: LIMITED` and `activation_readiness: BASELINE_REQUIRED`. |
| `AE-dfsa-notices` | Failed strict remediation-exit gate. The original/current URL is 404. The enforcement regulatory-actions candidate is nav-shell/filter-list output. The AML/MLRO notices candidate extracts meaningful text, but no-save result remains `PREVIEW_ONLY` with `quality_label: LIMITED` and `activation_readiness: BASELINE_REQUIRED`. |
| Can DFSA leave remediation? | No. |

Playwright launched successfully outside the sandbox. Correct candidate URLs/selectors were found for further validation, but strict criteria to move DFSA out of remediation were not met.

## 2. Current Config

| source_id | Current URL | wait_for_selector | content_selector | expected_min_length | Previous failure reason |
|---|---|---|---|---:|---|
| `AE-dubai-financial-services-authority-dfsa` | `https://www.dfsa.ae/rules-and-standards` | `main` | `main` | 3000 | HTTP 404 rendered as page-not-found shell. Normalized length 77. Same hash as DFSA notices. |
| `AE-dfsa-notices` | `https://www.dfsa.ae/regulation/notices-public-registers` | `main` | `main` | 3000 | HTTP 404 rendered as page-not-found shell. Normalized length 77. Same hash as DFSA rules source. |

Current registry status for both sources remains `remediation`.

## 3. Browser Investigation

### `https://www.dfsa.ae/rules-and-standards`

- Rendered status: 404.
- Title: `Page Not Found | DFSA`.
- DOM result: not regulatory content. The page includes global DFSA navigation, but the page body is a not-found shell.
- Rejected selector: `main`; it does not provide meaningful regulatory content for this URL.
- Rejected URL: current URL should not be used for readiness claims.

### `https://www.dfsa.ae/regulation/notices-public-registers`

- Rendered status: 404.
- Title: `Page Not Found | DFSA`.
- DOM result: not regulatory content. Same not-found shell pattern as the rules URL.
- Rejected selector: `main`; it does not provide meaningful regulatory content for this URL.
- Rejected URL: current URL should not be used for readiness claims.

### Candidate: `https://www.dfsa.ae/your-resources/regulatory/laws-and-rules`

- Rendered status: 200.
- Title: `Laws and Rules | DFSA`.
- Meaningful selector candidates:
  - `.default-block.laws-and-rules .infoPartOne`: about 3,310 rendered characters, low nav density, includes legal framework and rulebook links.
  - `.default-block.laws-and-rules .container.animation-on`: about 3,504 rendered characters, includes side navigation and the page body.
- Important observation: DFSA links the actual rulebook to `https://dfsaen.thomsonreuters.com/` and rulebook modules to `https://dfsaen.thomsonreuters.com/rulebook/rulebook-modules`.
- Verdict: useful official landing page, but the linked rulebook modules page is stronger for the DFSA rules/sourcebook monitoring intent.

### Candidate: `https://dfsaen.thomsonreuters.com/rulebook/rulebook-modules`

- Rendered status: 200.
- Title: `Rulebook Modules | Rulebook`.
- Meaningful selector candidates:
  - `article`: about 10,980 rendered characters in browser inspection.
  - `main`: about 12,334 rendered characters, includes more surrounding page chrome.
- Selected no-save candidate selector: `article`.
- Reason: `article` extracts actual rulebook modules such as AML, AMI, AUD, COB, CIR, FER, GEN, GLO, PIB, PIN, REP, and other DFSA sourcebook/rulebook modules with lower page chrome than `main`.

### Candidate: `https://www.dfsa.ae/what-we-do/enforcement/regulatory-actions`

- Rendered status: 200.
- Title: `Decision Notices & Regulatory Actions | DFSA`.
- Selector candidates:
  - `.default-block.regulatory-actions .infoPartOne`: about 1,106 rendered characters in browser inspection.
  - `.default-block.regulatory-actions .container.animation-on`: about 1,384 rendered characters in browser inspection.
- Rejected as a ready selector: Source Lab normalized output is mostly filter/category/year labels and was detected as nav-shell/filter-list output.

### Candidate: `https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/financial-crime-prevention-notices-and-mlro-letters`

- Rendered status: 200.
- Title: `Financial Crime Prevention Notices and MLRO Letters | DFSA`.
- Meaningful selector candidates:
  - `.financial-crime-prevention-notices-and-mlro-letters .simpleTabsContent`: about 3,325 rendered characters in browser inspection.
  - `.financial-crime-prevention-notices-and-mlro-letters .container.animation-on`: about 3,787 rendered characters, with more side navigation.
- Selected no-save candidate selector: `.financial-crime-prevention-notices-and-mlro-letters .simpleTabsContent`.
- Reason: this selector extracts actual financial-crime notices and MLRO-letter titles rather than global navigation.

## 4. Source Lab Results

| source_id | Tested URL | Selector | normalized_length | hash | quality | nav_shell | collision | readiness | Preview |
|---|---|---|---:|---|---|---|---|---|---|
| `AE-dubai-financial-services-authority-dfsa` | `https://dfsaen.thomsonreuters.com/rulebook/rulebook-modules` | `article` | 10,634 | `352dcfd27d1bf437bccb879df1546c6bb44239b4c4cf53486b614a1c19e8ea61` | `LIMITED` / 59 | false | false | `CONFIRMED_ACCESSIBLE`, `BASELINE_REQUIRED`, `PREVIEW_ONLY` | `Rulebook Modules Anti-Money Laundering, Counter-Terrorist Financing and Sanctions Module (AML) [VER30/04-26] AML 1 Introduction AML 2 Overview and Purpose of the Module...` |
| `AE-dfsa-notices` candidate A | `https://www.dfsa.ae/what-we-do/enforcement/regulatory-actions` | `.default-block.regulatory-actions .infoPartOne` | 903 | `ecb8d7728f0857bb2cccf89119acf58d6b3db6da520682394275af469cbf2614` | `POOR` / 0 | true | false | `NAV_SHELL_ONLY`, `NEEDS_REMEDIATION`, `PREVIEW_ONLY` | `Decision Notice Enforceable Undertaking Notice of Authorised Individual Suspension Notice of Cancellation of Registration...` |
| `AE-dfsa-notices` candidate B | `https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/financial-crime-prevention-notices-and-mlro-letters` | `.financial-crime-prevention-notices-and-mlro-letters .simpleTabsContent` | 3,175 | `2585e5910649e63c81d404e6d573fd4fa9a89ed5bd2c72dfb914f4affa9a79d9` | `LIMITED` / 59 | false | false | `CONFIRMED_ACCESSIBLE`, `BASELINE_REQUIRED`, `PREVIEW_ONLY` | `Amendments to the DFSA AML and Glossary Modules and the AML FAQ document Open Updates to Federal Anti-Money Laundering (AML) Legislation...` |

Hashes for the two best candidates are unique. They are not unique evidence records because no evidence was saved.

## 5. Recommendation

Do not update `sources.json` yet.

Recommended future config if founder/source-monitor approval accepts the URL intent change:

```json
{
  "source_id": "AE-dubai-financial-services-authority-dfsa",
  "url": "https://dfsaen.thomsonreuters.com/rulebook/rulebook-modules",
  "fetch_method": "playwright",
  "wait_for_selector": "article",
  "content_selector": "article",
  "expected_min_length": 8000,
  "notes": "DFSA-linked rulebook modules page. Local no-save extraction verified, but evidence save and baseline are still pending."
}
```

Recommended future config if `AE-dfsa-notices` is intended to mean AML/financial-crime notices and MLRO letters:

```json
{
  "source_id": "AE-dfsa-notices",
  "url": "https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/financial-crime-prevention-notices-and-mlro-letters",
  "fetch_method": "playwright",
  "wait_for_selector": ".financial-crime-prevention-notices-and-mlro-letters .simpleTabsContent",
  "content_selector": ".financial-crime-prevention-notices-and-mlro-letters .simpleTabsContent",
  "expected_min_length": 2500,
  "notes": "Official DFSA financial-crime notices and MLRO letters page. Local no-save extraction verified, but evidence save and baseline are still pending."
}
```

Do not use the enforcement `regulatory-actions` page as the ready replacement yet. It currently extracts mostly filters/categories and Source Lab marks it `NAV_SHELL_ONLY`.

Before any `sources.json` change, the product owner should confirm whether `AE-dfsa-notices` should represent:

1. decision notices and enforcement regulatory actions, or
2. financial-crime prevention notices and MLRO letters.

After URL-intent approval, rerun no-save checks, then run one explicit `--save` validation pass per source only if no-save remains meaningful and unique. Baseline runs are still required before monitoring-ready language.

## 6. Customer-Facing Wording

UI should still say:

> DFSA under extraction remediation.

Do not change customer-facing source counts. Do not say DFSA is ready, evidence confirmed, or monitoring-ready.

Allowed internal wording:

> DFSA rulebook and AML/MLRO notice candidate extraction verified in local no-save Source Lab checks; evidence save and baseline still pending.

Blocked wording:

> DFSA validated.
> DFSA monitoring-ready.
> DFSA evidence confirmed.
> DFSA certified.

## 7. Next Exact Task

Decide the intended scope of `AE-dfsa-notices` (enforcement regulatory actions vs AML/MLRO notices), then approve or reject the candidate URL/selector changes before any `sources.json` edit.
