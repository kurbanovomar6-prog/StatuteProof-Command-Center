# UAE 50 No-Save Cycle Report

Date: 2026-06-15

## Summary

No-save tested in this cycle: **7**.

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
