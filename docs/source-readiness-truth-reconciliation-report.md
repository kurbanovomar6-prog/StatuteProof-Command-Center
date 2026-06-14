# Source Readiness Truth Reconciliation Report

Date: 2026-06-14

## Executive Decision

The canonical customer-facing truth for the current StatuteProof UAE source pack is:

**13 enabled UAE sources; 9 readiness-supported in the current registry; 4 under extraction remediation.**

The earlier **13 enabled / 10 confirmed / 3 remediation** story is not safe today. It depends on promoting DIFC Laws and Regulations out of remediation, but the current readiness report explicitly keeps that source under a registry hold until Source Monitor and Evidence Trail review the hold.

## Canonical Counts

| Count | Value | Basis |
| --- | ---: | --- |
| Total records in `sources.json` | 150 | Registry file parse. |
| Enabled UAE sources | 13 | `enabled: true` and `jurisdiction: AE`. |
| Readiness-supported | 9 | Enabled UAE registry rows with `status: active`, excluding held/remediation rows. |
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

## Sources Under Extraction Remediation

| Source ID used in reports/UI | Source name | Reason |
| --- | --- | --- |
| `AE-dubai-financial-services-authority-dfsa` | DFSA Rulebook / DFSA main source | Current configured URL renders a page-not-found/nav-shell result and collides with DFSA notices. A stronger rulebook candidate exists, but only as no-save preview with `BASELINE_REQUIRED`. |
| `AE-dfsa-notices` | DFSA Regulatory Notices | Current configured URL renders a page-not-found/nav-shell result and collides with the DFSA rulebook source. The intended source model is ambiguous. |
| `AE-difc-laws-and-regulations` | DIFC Laws and Regulations | Extraction appears meaningful, but the current readiness report keeps it under registry hold pending Source Monitor and Evidence Trail review. |
| `AE-uae-financial-intelligence-unit-uaefiu` | UAE FIU Homepage | Homepage extraction is too shallow for primary regulatory monitoring. UAE FIU Circulars and Notices is the readiness-supported FIU source. |

## Which Story Is Correct?

**Correct today:** 13 enabled / 9 readiness-supported / 4 under extraction remediation.

**Not correct today:** 13 enabled / 10 confirmed / 3 under extraction remediation.

Reason: no reviewed evidence decision has released DIFC Laws and Regulations from registry hold, and DFSA sources remain in remediation. A source may have meaningful extraction while still not being customer-visible ready if its registry hold, source model, evidence baseline, or activation review is incomplete.

## Allowed Customer-Facing Wording

- "13 enabled UAE sources."
- "9 readiness-supported in the current registry."
- "4 under extraction remediation."
- "Source readiness in progress."
- "DFSA source model under remediation."
- "DIFC Laws and Regulations remains under registry hold pending Source Monitor and Evidence Trail review."
- "UAE FIU Circulars and Notices is the readiness-supported FIU source; the UAE FIU homepage remains under remediation."
- "Evidence-backed monitoring requires proof artifacts and baseline review before activation."

## Forbidden Wording

- "13 validated sources."
- "13 confirmed sources."
- "13 ready sources."
- "10 confirmed" unless DIFC is explicitly released from remediation by Source Monitor and Evidence Trail.
- "DFSA ready."
- "DIFC ready" while the registry hold remains.
- "Certified monitoring."
- "Perfect parsing."
- "Any website can be parsed."
- "Guaranteed compliance."

## Code And UI Result

Current public/app source tables already use the 13/9/4 model:

- `product/regradar/web/src/components/SourceCoverageTable.jsx`
- `product/regradar/web/src/data/appMockData.js`
- Pricing and billing surfaces use "13 enabled" with 9 readiness-supported and 4 under remediation.

This sprint does not change `sources.json` because the current registry status is already aligned with the conservative truth. Future changes should derive source IDs and counts from one generated registry summary rather than duplicating constants in frontend/docs.

## Next Required Source Readiness Work

1. Resolve the DFSA source model.
2. Decide whether DIFC Laws and Regulations can leave registry hold after Source Monitor and Evidence Trail review.
3. Decide whether the UAE FIU homepage should remain enabled as a remediation/reference source or be replaced by the circulars/publications source in customer-facing pack views.
4. Add a generated source-readiness summary artifact consumed by validators and frontend source tables.
