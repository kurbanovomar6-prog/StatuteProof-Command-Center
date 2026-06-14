# UAE Source Pack No-Save Validation Report

## 1. Executive Summary

This run tested a small controlled batch of high-priority UAE source-pack candidates.

- Candidates discovered: 60.
- Candidates tested in this batch: 5.
- No-save readiness-supported candidates for next validation step: 2.
- Remediation/blocked results in this batch: 2.
- Evidence writes: 0.
- Customer delivery: 0.
- Broad/all-source monitoring: not run.

Current customer-facing truth remains:

**13 enabled UAE sources; 9 readiness-supported; 4 under extraction remediation.**

Do not market 40+ or 60 sources from this batch. The result supports a professional validation path, not customer-facing coverage expansion.

## 2. Commands Run

All commands were run from:

`/Users/kurbnovomar/StatuteProof-Command-Center/product/regradar`

```bash
python3 run.py source-lab https://www.uaefiu.gov.ae/en/Publications/ --no-save --json
python3 run.py source-lab https://www.vara.ae/en/enforcement/ --no-save --json
python3 run.py source-lab https://dfsaen.thomsonreuters.com/rulebook/rulebook-modules --js --wait-for-selector article --content-selector article --no-save --json
python3 run.py source-lab https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/financial-crime-prevention-notices-and-mlro-letters --js --wait-for-selector ".financial-crime-prevention-notices-and-mlro-letters .simpleTabsContent" --content-selector ".financial-crime-prevention-notices-and-mlro-letters .simpleTabsContent" --no-save --json
python3 run.py source-lab https://www.centralbank.ae/en/regulations/ --no-save --json
```

The batch includes five command lines because VARA was also checked as an existing high-value source; the count by candidate status below counts five tested URLs. No command used `--save`.

## 3. Validation Results

| Candidate | URL | Selector | Provider | Length | Hash | Quality | Readiness | Nav shell | Collision | Result |
|---|---|---|---|---:|---|---|---|---|---|---|
| `AE-uaefiu-publications` | `https://www.uaefiu.gov.ae/en/Publications/` | generic | bs4 | 5,742 | `9f0a1819339a56d62042a74fa522eeb06f654858592987ee3e0d665f854cb43c` | POOR / 0 | BLOCKED | yes | no | Remediation. Rendered content was search/accessibility/nav-heavy and policy warnings included CAPTCHA/access risk. |
| `AE-vara-enforcement` | `https://www.vara.ae/en/enforcement/` | generic | bs4 | 4,506 | `7e5ab9c8d3566b2b06ee62f55fd45cb6a4d1c013d5a65a2508db0d4e2ff33d3c` | POOR / 0 | NAV_SHELL_ONLY | yes | no | Remediation for generic parser. Preview had useful enforcement text, but strict gate requires a precise selector/adapter before promotion. |
| `AE-dfsa-rulebook-thomsonreuters` | `https://dfsaen.thomsonreuters.com/rulebook/rulebook-modules` | `article` | bs4 | 10,634 | `352dcfd27d1bf437bccb879df1546c6bb44239b4c4cf53486b614a1c19e8ea61` | LIMITED / 59 | CONFIRMED_ACCESSIBLE | no | no | No-save accessible. Good candidate for saved validation/baseline, but not evidence-confirmed or monitoring-ready. |
| `AE-dfsa-aml-mlro-notices` | `https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/financial-crime-prevention-notices-and-mlro-letters` | `.financial-crime-prevention-notices-and-mlro-letters .simpleTabsContent` | bs4 | 3,175 | `2585e5910649e63c81d404e6d573fd4fa9a89ed5bd2c72dfb914f4affa9a79d9` | LIMITED / 59 | CONFIRMED_ACCESSIBLE | no | no | No-save accessible. Good candidate for saved validation/baseline, but not evidence-confirmed or monitoring-ready. |
| `AE-cbuae-regulations` | `https://www.centralbank.ae/en/regulations/` | generic | bs4 | 14,484 | `51c99b6ffc252c140f0156cf4b8c55aeb312d63bf127a8fe6f292c1b067de64b` | POOR / 22 | BLOCKED | no | no | Remediation for generic Source Lab. Policy warnings included CAPTCHA/login risk and preview included broad page chrome. |

## 4. Preview Evidence

The two DFSA candidates produced meaningful previews:

- DFSA rulebook modules preview began with AML module headings, business risk assessment, customer due diligence, sanctions, and money laundering topics.
- DFSA AML/MLRO notices preview began with AML module amendments, federal AML legislation updates, sanctions operational risk, high-risk jurisdictions, FIU notifications, and suspicious activity/transaction reporting review items.

The failed/remediation results produced page chrome, accessibility controls, search UI, or access-warning signals. These are useful diagnostic results, not source-readiness proof.

## 5. Counts From This Batch

| Metric | Count | Notes |
|---|---:|---|
| URLs tested | 5 | All no-save Source Lab checks. |
| No-save accessible / next validation candidates | 2 | DFSA rulebook and DFSA AML/MLRO notices. |
| Remediation / blocked | 3 | UAE FIU publications, VARA enforcement generic extraction, CBUAE regulations generic extraction. |
| Evidence confirmed | 0 | No `--save`; no proof paths. |
| Monitoring-ready | 0 | Baseline runs required. |
| Hash collisions | 0 | Tested hashes were distinct. |

## 6. Important Interpretation

This batch does not invalidate the committed customer-facing source truth. It shows that generic Source Lab checks can be stricter or less source-specific than existing registry readiness. That is acceptable and useful: the expansion process should require precise selectors/adapters before increasing public source counts.

The DFSA candidates are promising because they passed no-save accessibility with distinct hashes and meaningful text. They still cannot move DFSA out of remediation because:

- evidence level is `PREVIEW_ONLY`;
- baseline runs completed is 0;
- quality label is `LIMITED`;
- no proof paths exist;
- `sources.json` still has old/remediation DFSA IDs and URLs;
- Source Monitor and Evidence Trail review are still required.

## 7. Is A 40-Source Pack Realistic Now?

Yes as a validation roadmap, no as customer-facing ready coverage.

A 40-source professional pack is realistic after:

- top-40 no-save batch validation;
- selectors/adapters for JS/nav-shell pages;
- saved evidence for sources intended to be shown with evidence;
- baseline/activation readiness checks;
- registry migration plan.

## 8. Is A 60-Source Pack Realistic Now?

Yes as a researched candidate map, no as marketed coverage.

A 60-source pack should not be marketed until the majority of the top-60 candidates have passed no-save validation and the activated subset has evidence/baseline records.

## 9. Customer-Facing Wording Allowed Now

Allowed:

- “13 enabled UAE sources; 9 readiness-supported; 4 under extraction remediation.”
- “60 official UAE source candidates mapped for validation.”
- “40-source professional pack path under no-save validation.”
- “DFSA remediation has two promising no-save candidates, but evidence/baseline is still pending.”

Forbidden:

- “60 validated sources.”
- “40+ monitored sources.”
- “DFSA ready.”
- “comprehensive UAE monitor.”
- “perfect parsing.”
- “guaranteed compliance.”

## 10. Next Fixes Needed

1. Run top-40 candidate no-save validation in regulator batches.
2. Add source-specific selectors/adapters for VARA enforcement, CBUAE regulations, UAE FIU publications, and SCA pages.
3. Create a DFSA registry migration prompt that replaces ambiguous DFSA IDs with explicit rulebook, AML/MLRO notices, and enforcement sources only after saved validation.
4. Add saved evidence/baseline runs for the candidate subset selected for demo and paid pilot.
