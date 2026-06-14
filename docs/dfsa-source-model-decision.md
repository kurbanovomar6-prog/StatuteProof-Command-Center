# DFSA Source Model Decision

Date: 2026-06-14

## Executive Decision

DFSA should not be modeled as one vague "notices" source. StatuteProof needs separate DFSA source records because rulebook modules, enforcement regulatory actions, and AML/MLRO notices have different page structures, evidence meaning, and customer-facing labels.

DFSA remains under extraction remediation. No DFSA source is customer-visible ready based on the current saved registry state.

## 1. What Should `AE-dfsa-notices` Mean?

`AE-dfsa-notices` is too ambiguous and should not be used as a long-term customer-facing label.

Recommended handling:

- Treat the current `AE-dfsa-notices` record as a deprecated/remediation placeholder until the product owner chooses the intended notice class.
- Do not silently repurpose it to AML/MLRO notices or enforcement actions without a migration note, because historical hashes/evidence labels would become confusing.

## 2. Should DFSA Rulebook Be Separate?

Yes.

Recommended source:

| Field | Value |
| --- | --- |
| Source ID | `AE-dfsa-rulebook` |
| Transitional existing ID | `AE-dubai-financial-services-authority-dfsa` |
| URL candidate | `https://dfsaen.thomsonreuters.com/rulebook/rulebook-modules` |
| Selector candidate | `article` |
| Purpose | DFSA rulebook/sourcebook modules. |
| Current proof state | No-save preview only; no saved evidence baseline. |
| Customer-visible state | Under extraction remediation / baseline required. |

The no-save selector investigation produced meaningful, unique, non-nav-shell text for the rulebook candidate, but it remains `PREVIEW_ONLY` with `BASELINE_REQUIRED`. That is not enough for readiness-supported or monitoring-ready status.

## 3. Should Enforcement Regulatory Actions Be Separate?

Yes.

Recommended source:

| Field | Value |
| --- | --- |
| Source ID | `AE-dfsa-enforcement-regulatory-actions` |
| URL candidate | `https://www.dfsa.ae/what-we-do/enforcement/regulatory-actions` |
| Selector candidate | Not proven. `.default-block.regulatory-actions .infoPartOne` extracted a short filter/list shell. |
| Purpose | DFSA enforcement notices and regulatory actions. |
| Current proof state | Failed strict no-save check. |
| Customer-visible state | Under extraction remediation. |

Do not mark this source ready until a selector or API/source adapter extracts actual item-level enforcement/regulatory-action content.

## 4. Should AML/MLRO Notices Be Separate?

Yes.

Recommended source:

| Field | Value |
| --- | --- |
| Source ID | `AE-dfsa-aml-mlro-notices` |
| URL candidate | `https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/financial-crime-prevention-notices-and-mlro-letters` |
| Selector candidate | `.financial-crime-prevention-notices-and-mlro-letters .simpleTabsContent` |
| Purpose | DFSA financial crime prevention notices and MLRO letters. |
| Current proof state | No-save preview only; no saved evidence baseline. |
| Customer-visible state | Under extraction remediation / baseline required. |

The selector investigation produced meaningful, unique, non-nav-shell text for this candidate, but it remains a preview. It should not be merged into `AE-dfsa-notices` unless the source ID and label are changed deliberately.

## 5. Source IDs That Should Exist

Recommended future DFSA model:

| Source ID | Label | Status today |
| --- | --- | --- |
| `AE-dfsa-rulebook` | DFSA Rulebook Modules | Proposed replacement for the current DFSA main source; baseline required. |
| `AE-dfsa-enforcement-regulatory-actions` | DFSA Enforcement Regulatory Actions | Proposed new source; selector not proven. |
| `AE-dfsa-aml-mlro-notices` | DFSA AML/MLRO Notices and Financial Crime Prevention Letters | Proposed new source; no-save selector candidate found, baseline required. |

## 6. Existing IDs To Rename Or Deprecate

| Existing ID | Recommendation |
| --- | --- |
| `AE-dubai-financial-services-authority-dfsa` | Keep as remediation until a migration can replace it with `AE-dfsa-rulebook` or alias it to the new ID. |
| `AE-dfsa-notices` | Deprecate or redefine only after choosing whether it means enforcement actions or AML/MLRO notices. Do not reuse the label "Regulatory Notices" for unrelated page classes. |

## 7. Proven URLs / Selectors

Proven enough for no-save preview, not for readiness-supported status:

- Rulebook candidate: `https://dfsaen.thomsonreuters.com/rulebook/rulebook-modules` with selector `article`.
- AML/MLRO candidate: `https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/financial-crime-prevention-notices-and-mlro-letters` with selector `.financial-crime-prevention-notices-and-mlro-letters .simpleTabsContent`.

Still unproven:

- Enforcement regulatory actions selector.
- Any saved evidence baseline for the rulebook or AML/MLRO candidates.
- Whether source-specific adapters are needed for item-level regulatory-action pages.

## 8. What Remains In Remediation

- Current DFSA main/rulebook source.
- Current DFSA regulatory notices source.
- Proposed enforcement regulatory actions source.
- Proposed AML/MLRO notices source until saved proof artifacts and baseline review exist.

## 9. Allowed Customer-Facing Wording

- "DFSA source model under remediation."
- "DFSA rulebook and notices require extraction remediation before activation."
- "DFSA rulebook and AML/MLRO notice candidates have local no-save extraction candidates, but evidence baseline is still pending."
- "DFSA is not treated as readiness-supported in the current UAE source pack."

## 10. `sources.json` Change Decision

No `sources.json` update in this sprint.

Reason: the two better DFSA candidates are no-save previews only, and enforcement regulatory actions still lacks a proven selector. Updating registry IDs/URLs without a saved baseline would create another truth mismatch.

## Next Exact Task

Run a dedicated DFSA source-model update after product-owner approval: add or migrate the three DFSA source IDs, run no-save checks, then run saved baseline checks only for candidates that pass strict no-save gates.
