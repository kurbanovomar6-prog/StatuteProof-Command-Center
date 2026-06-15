# UAE 50 Saved Evidence Baseline Cycle Report

Date: 2026-06-15

## Saved Evidence

Saved evidence was run only for strong no-save passes.

| Source | Latest proof path | Hash | Baseline runs |
| --- | --- | --- | ---: |
| `AE-adgm-fsra-financial-crime-prevention` | `product/regradar/data/source_snapshots/2026-06-15/AE/AE-adgm-fsra-financial-crime-prevention/intake-20260615T130757Z/proof.json` | `5553253c8a001615c514a71cfba823a940de2fbc89580106149208193c4f81b1` | 5 |
| `AE-adgm-fsra-rulebooks` | `product/regradar/data/source_snapshots/2026-06-15/AE/AE-adgm-fsra-rulebooks/intake-20260615T130757Z/proof.json` | `cae7770f5cfd354292b5b1b0ead14134ea5eb88a5c2f319ff1345dfc3b89efc0` | 4 |
| `AE-adgm-fsra-consultations` | `product/regradar/data/source_snapshots/2026-06-15/AE/AE-adgm-fsra-consultations/intake-20260615T130800Z/proof.json` | `98a1cb43f5d53b2d88fa7e966912b11a9b94a2b700cf23966282c83aacb34515` | 2 |
| `AE-dfsa-aml-rulebook-module` | `product/regradar/data/source_snapshots/2026-06-15/AE/AE-dfsa-aml-rulebook-module/intake-20260615T132231Z/proof.json` | `850da3025a62bc5b9584295b5193dfc37df0459331df91137715967134f9d7b5` | 4 |

## Hash Drift Handling

`AE-dfsa-aml-rulebook-module` initially drifted in mass-monitor dry-run because Source Lab and Mass Monitor were using different selector paths. The runner was fixed so static HTML adapter selectors are promoted into the fetch selector path, then two consecutive saved runs produced the same `850d...` hash. The active registry and queue were updated to that hash.

## Evidence Not Saved

Evidence was not saved for DIFC, VARA, UAE FIU publications, or EOCN because no strong no-save pass existed.
