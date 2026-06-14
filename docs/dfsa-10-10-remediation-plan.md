# DFSA 10/10 Remediation Plan

Date: 2026-06-14

## 1. Current DFSA Source IDs And URLs

| Source ID | Current label | Current URL | Current selector | Current status |
| --- | --- | --- | --- | --- |
| `AE-dubai-financial-services-authority-dfsa` | Dubai Financial Services Authority (DFSA) | `https://www.dfsa.ae/rules-and-standards` | `main` | remediation |
| `AE-dfsa-notices` | DFSA Regulatory Notices | `https://www.dfsa.ae/regulation/notices-public-registers` | `main` | remediation |

## 2. Current Issue

Previous no-save Source Lab checks launched Playwright successfully, but the configured pages/selectors extracted page-shell or navigation-shell content. The two DFSA configured sources also produced non-unique hashes. They cannot leave remediation.

## 3. Proposed Source IDs

| Proposed ID | Purpose |
| --- | --- |
| `AE-dfsa-rulebook` | DFSA rulebook/sourcebook modules. |
| `AE-dfsa-enforcement-regulatory-actions` | DFSA enforcement notices and regulatory actions. |
| `AE-dfsa-aml-mlro-notices` | DFSA financial crime prevention notices and MLRO letters. |

## 4. Exact Candidate URLs / Selectors

| Proposed ID | URL | Selector |
| --- | --- | --- |
| `AE-dfsa-rulebook` | `https://dfsaen.thomsonreuters.com/rulebook/rulebook-modules` | `article` |
| `AE-dfsa-enforcement-regulatory-actions` | `https://www.dfsa.ae/what-we-do/enforcement/regulatory-actions` | not proven |
| `AE-dfsa-aml-mlro-notices` | `https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/financial-crime-prevention-notices-and-mlro-letters` | `.financial-crime-prevention-notices-and-mlro-letters .simpleTabsContent` |

## 5. Which Are Proven

- `AE-dfsa-rulebook`: proven only as a local no-save candidate, not as a saved baseline.
- `AE-dfsa-aml-mlro-notices`: proven only as a local no-save candidate, not as a saved baseline.
- `AE-dfsa-enforcement-regulatory-actions`: not proven; prior selector candidate extracted a filter/list shell.

## 6. Which Are Not Proven

- No DFSA source has saved proof artifacts and baseline history for the proposed model.
- Enforcement actions still needs selector/API/item-level investigation.
- Current `sources.json` DFSA IDs are not ready.

## 7. Should No-Save Checks Be Rerun?

Yes, but only in a dedicated DFSA task:

- One URL at a time.
- No save.
- No alerts, delivery, all-source monitor, or broad crawling.
- Capture provider, extraction method, length, hash, quality, nav-shell flag, collision flag, failure reason, remediation hint, and preview.

## 8. Is Saved Baseline Appropriate?

Only after a candidate passes strict no-save checks:

- URL reachable.
- Selector extracts meaningful regulatory content.
- Normalized text above threshold.
- Not nav-shell.
- Hash unique.
- Quality label GOOD or ACCEPTABLE.
- Evidence level remains preview in no-save.

Then a separate saved baseline run can be approved with Evidence Trail and QA review.

## 9. Should `sources.json` Change Now?

No change in this 10/10 pass.

Reason: updating `sources.json` without a fresh no-save result and saved baseline would make the registry look more settled than the evidence supports.

## 10. What Remains Remediation

- Current DFSA main/rulebook source.
- Current DFSA notices source.
- Proposed enforcement source.
- Proposed AML/MLRO notices source until proof/baseline exists.

## Customer-Facing Wording

Allowed:

- "DFSA source model under remediation."
- "DFSA rulebook and notice sources require extraction remediation before activation."
- "DFSA candidates need fresh no-save checks and evidence baseline before they can be readiness-supported."

Forbidden:

- "DFSA ready."
- "DFSA validated."
- "DFSA evidence confirmed."
- "DFSA monitoring certified."
