# Family Upgrade Audit: SCA

Date: 2026-06-21

- Score before this pass: 5.8/10
- Score after this pass: 6.5/10
- Chosen upgrade path: direct official regulations listing proof-backed activation, then canonical evidence and exact alert linkage.
- Customer delivery approved: no
- Safe claim: selected SCA direct/regulations endpoints only.
- Forbidden claim: SCA root portal monitoring or full SCA coverage.

## Source Rows

| Source ID | Mode | Status | Alert eligible | Proof / hash | Baseline | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `AE-sca-regulations-listing` | fresh_alert | active | true | proof path + normalized hash present | 5/2 | Upgraded after proof-backed repeat baseline and mass-monitor `MONITOR_OK` |
| `AE-sca-aml-cft` | fresh_alert | active | true | proof path + normalized hash present | 4/2 | Keep, but parser/noise review still needed |

## Source Runs And Proof

- `AE-sca-regulations-listing` latest proof: `data/source_snapshots/2026-06-21/AE/AE-sca-regulations-listing/intake-20260621T214501Z/proof.json`
- Normalized hash: `61d0df8f31cc3015411091d3051dc7e84038e89ad0d56865516814ddc85d1e8a`
- `AE-sca-aml-cft` no-save retest did not resolve the parser/noise warning because the target table selector was not found.

## Canonical Evidence

| Evidence record | Source ID | Run ID | Status | Review |
| --- | --- | --- | --- | --- |
| `evr_AE-sca-aml-cft_intake-20260619T143025Z` | `AE-sca-aml-cft` | `intake-20260619T143025Z` | CHANGED | latest external review approved |
| `evr_AE-sca-circulars-rules-procedures_intake-20260619T150551Z` | `AE-sca-circulars-rules-procedures` | `intake-20260619T150551Z` | CHANGED | pending |
| `evr_AE-sca-fintech-sandbox_intake-20260619T164145Z` | `AE-sca-fintech-sandbox` | `intake-20260619T164145Z` | FIRST_SEEN | pending |
| `evr_AE-sca-regulations-listing_intake-20260621T214120Z` | `AE-sca-regulations-listing` | `intake-20260621T214120Z` | CHANGED | pending |

## Alerts Linked

| Alert | Evidence record |
| --- | --- |
| `20260619T150551-AE-sca-circulars-rules-procedures-intake-2-6587.json` | `evr_AE-sca-circulars-rules-procedures_intake-20260619T150551Z` |
| `20260621T214120-AE-sca-regulations-listing-intake-2-44d1.json` | `evr_AE-sca-regulations-listing_intake-20260621T214120Z` |

## Blockers Remaining

- The `AE-sca-aml-cft` parser/noise issue is still unresolved and blocks broad SCA positioning.
- SCA root portal monitoring is still unclaimed.
- New SCA regulations evidence is pending review and not customer-brief eligible.

## Stop / Continue

Continue with `AE-sca-aml-cft` parser/noise review and direct endpoint depth only; do not use root portal claims.
