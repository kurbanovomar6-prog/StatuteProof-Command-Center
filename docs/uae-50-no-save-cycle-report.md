# UAE 50 No-Save Cycle Report

Date: 2026-06-15

## Summary

No-save tested this sprint (all cycles): **56** (7 earlier + 49 batch 2).

## Batch 2 — 2026-06-15 (live batch harness, per-adapter auto-apply, 49 sources)

Tested: 49 | Strong passes: 6 | New activatable: 1 | Rejected after evidence gate: 1

Strong no-save passes in batch 2 (6):
1. `AE-abu-dhabi-global-market-adgm` — custom_element q=62 (already enabled) ✓
2. `AE-adgm-fsra-guidance-policy` — custom_element q=65 — **NEW, activated** ✓
3. `AE-adgm-legal-framework-rules` — custom_element q=62 (already enabled) ✓
4. `AE-dfsa-aml-mlro-notices` — pdf_listing q=60 (already enabled) ✓
5. `AE-sca-circulars` — listing q=62 (already enabled) ✓
6. `AE-vara-news` — pdf_listing q=65 — evidence save failed (NEEDS_SELECTOR_REVIEW); not activated

Failure breakdown (43 non-passes): NAV_SHELL_ONLY 32, ACCESS_BLOCKED 3, SHALLOW_CONTENT 2, LISTING_ADAPTER_REQUIRED 1, TABLE_ADAPTER_REQUIRED 1, unknown probe failure 4.

## Earlier Cycles (batch 1)

Strong no-save passes:

1. `AE-adgm-fsra-financial-crime-prevention` — quality 65, hash `5553253c8a001615c514a71cfba823a940de2fbc89580106149208193c4f81b1`.
2. `AE-adgm-fsra-rulebooks` — quality 62, hash `cae7770f5cfd354292b5b1b0ead14134ea5eb88a5c2f319ff1345dfc3b89efc0`.
3. `AE-adgm-fsra-consultations` — quality 65, hash `98a1cb43f5d53b2d88fa7e966912b11a9b94a2b700cf23966282c83aacb34515`.
4. `AE-dfsa-aml-rulebook-module` recheck — quality 65, hash `850da3025a62bc5b9584295b5193dfc37df0459331df91137715967134f9d7b5`.

Failed/held no-save checks:

| Source | Result | Reason |
| --- | --- | --- |
| `AE-difc-laws-and-regulations` | Hold | Static path quality 59 and table path quality 53; no strong pass. |
| `AE-vara-current-framework` | Remediation | Stale/not-found framework URL produced nav-shell after Playwright fallback. |
| `AE-uae-fiu-publications` | Blocked | HTTP 403 / likely WAF on publications path. |
| `AE-eocn-laws-regulations` | Remediation | `table` selector not found on current URL. |

## Verdict

No-save produced three new ADGM/FSRA activation candidates and confirmed the corrected DFSA AML extraction path. It did not produce additional VARA/FIU/EOCN/DIFC candidates.
