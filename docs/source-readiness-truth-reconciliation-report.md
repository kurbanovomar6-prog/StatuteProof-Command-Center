# Source Readiness Truth Reconciliation Report

Date: 2026-06-15

## Executive Decision

The canonical customer-facing truth for the current StatuteProof UAE source pack is:

**16 enabled UAE sources; 12 readiness-supported in the current registry; 4 under extraction remediation.**

The earlier **13 enabled / 10 confirmed / 3 remediation** story is not safe today. The later **13 enabled / 9 readiness-supported / 4 remediation** story was safe until three proof-backed, repeat-baseline-complete queue sources were promoted to `sources.json` on 2026-06-15.

## Canonical Counts

| Count | Value | Basis |
| --- | ---: | --- |
| Total records in `sources.json` | 153 | Registry file parse after adding three proof-backed UAE sources. |
| Enabled UAE sources | 16 | `enabled: true` and `jurisdiction: AE`. |
| Readiness-supported | 12 | Enabled UAE registry rows with `status: active`, excluding held/remediation rows. |
| Under extraction remediation | 4 | Enabled UAE registry rows with `status: remediation`. |
| Blocked / failed | 0 | Current registry uses remediation rather than blocked for the four not-ready sources. |

## Readiness-Supported Sources

| Source ID used in reports/UI | Source name | Reason it remains readiness-supported |
| --- | --- | --- |
| `AE-central-bank-of-the-uae` | Central Bank of the UAE | Current readiness report lists proof/hash/run artifacts and registry support. |
| `AE-dubai-virtual-assets-regulatory-authority-vara` | Dubai Virtual Assets Regulatory Authority (VARA) | Current readiness report lists proof/hash/run artifacts and meaningful extraction. |
| `AE-abu-dhabi-global-market-adgm` | Abu Dhabi Global Market (ADGM) | Current readiness report keeps main ADGM source readiness-supported with caveats. |
| `AE-uae-ministry-of-finance` | UAE Ministry of Finance | Current readiness report lists meaningful extraction and evidence artifacts. |
| `AE-uae-legislation-portal` | UAE Legislation Portal | Current readiness report lists meaningful extraction and evidence artifacts. |
| `AE-uae-ministry-of-economy` | UAE Ministry of Economy | Current readiness report lists meaningful extraction and evidence artifacts. |
| `AE-vara-enforcement` | VARA Enforcement Notices | Current readiness report lists meaningful extraction and unique hash. |
| `AE-cbuae-regulations` | CBUAE Regulations Sub-page | Current readiness report lists meaningful extraction with known counter-change noise caveat. |
| `AE-uaefiu-circulars` | UAE FIU Circulars and Notices | Current readiness report treats publications/circulars as the readiness-supported FIU source. |
| `AE-sca-circulars-rules-procedures` | SCA Circulars, Rules and Procedures | Promoted from activation-ready queue after proof-backed repeat baseline and mass-monitor dry-run. |
| `AE-dfsa-financial-crime-mlro-letters` | DFSA Financial Crime Prevention Notices and MLRO Letters | Promoted from activation-ready queue after proof-backed repeat baseline and mass-monitor dry-run. |
| `AE-dfsa-aml-rulebook-module` | DFSA AML Rulebook Module | Promoted from activation-ready queue after proof-backed repeat baseline and a scoped monitor-path dry-run reproduced the stored hash. |

## Sources Under Extraction Remediation

| Source ID used in reports/UI | Source name | Reason |
| --- | --- | --- |
| `AE-dubai-financial-services-authority-dfsa` | DFSA Rulebook / DFSA main source | Current configured URL renders a page-not-found/nav-shell result and collides with DFSA notices. A stronger rulebook candidate exists, but only as no-save preview with `BASELINE_REQUIRED`. |
| `AE-dfsa-notices` | DFSA Regulatory Notices | Current configured URL renders a page-not-found/nav-shell result and collides with the DFSA rulebook source. The intended source model is ambiguous. |
| `AE-difc-laws-and-regulations` | DIFC Laws and Regulations | Extraction appears meaningful, but the current readiness report keeps it under registry hold pending Source Monitor and Evidence Trail review. |
| `AE-uae-financial-intelligence-unit-uaefiu` | UAE FIU Homepage | Homepage extraction is too shallow for primary regulatory monitoring. UAE FIU Circulars and Notices is the readiness-supported FIU source. |

## Which Story Is Correct?

**Correct today:** 16 enabled / 12 readiness-supported / 4 under extraction remediation.

**Not correct today:** 13 enabled / 10 confirmed / 3 under extraction remediation.

Reason: three queue sources completed proof-backed repeat baseline and mass-monitor dry-run, while DIFC Laws and the legacy DFSA configured sources remain held/remediation. A source may have meaningful extraction while still not being customer-visible ready if its registry hold, source model, evidence baseline, or activation review is incomplete.

## Allowed Customer-Facing Wording

- "16 enabled UAE sources."
- "12 readiness-supported in the current registry."
- "4 under extraction remediation."
- "Source readiness in progress."
- "DFSA source model under remediation."
- "DIFC Laws and Regulations remains under registry hold pending Source Monitor and Evidence Trail review."
- "UAE FIU Circulars and Notices is the readiness-supported FIU source; the UAE FIU homepage remains under remediation."
- "Evidence-backed monitoring requires proof artifacts and baseline review before activation."

## Forbidden Wording

- "All 16 sources are validated."
- "All 16 sources are confirmed."
- "All 16 sources are ready."
- "10 confirmed" unless DIFC is explicitly released from remediation by Source Monitor and Evidence Trail.
- "DFSA ready."
- "DIFC ready" while the registry hold remains.
- "Certified monitoring."
- "Perfect parsing."
- "Any website can be parsed."
- "Guaranteed compliance."

## Code And UI Result

Current public/app source tables should use the 16/12/4 model:

- `product/regradar/web/src/components/SourceCoverageTable.jsx`
- `product/regradar/web/src/data/appMockData.js`
- Pricing and billing surfaces use "16 enabled" with 12 readiness-supported and 4 under remediation.

This sprint changes `sources.json` only for three proof-backed activation-ready queue sources. Future changes should derive source IDs and counts from one generated registry summary rather than duplicating constants in frontend/docs.

## Next Required Source Readiness Work

1. Resolve the DFSA source model.
2. Decide whether DIFC Laws and Regulations can leave registry hold after Source Monitor and Evidence Trail review.
3. Decide whether the UAE FIU homepage should remain enabled as a remediation/reference source or be replaced by the circulars/publications source in customer-facing pack views.
4. Add a generated source-readiness summary artifact consumed by validators and frontend source tables.
