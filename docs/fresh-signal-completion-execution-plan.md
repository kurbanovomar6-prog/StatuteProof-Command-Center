# Fresh Signal Completion Execution Plan

## Current Truth

Clean-state gate passed on 2026-06-19. The latest source-signal audit reports 226 enabled UAE sources:

| Signal tier | Count | Meaning |
|---|---:|---|
| Tier A | 136 | Commercially critical official regulation/rulebook/circular/enforcement/tax/AML sources |
| Tier B | 21 | Useful official context, indexes, annual reports, discovery pages |
| Tier C | 60 | Static detail pages, generic homepages, duplicates, low future-change signal |
| Remediation | 9 | Important sources with blocked/unconfirmed live monitoring |
| MONITOR_OK | 149 | Confirmed-live monitoring sources in current audit |
| Proof-backed snapshots | 216 | Sources with proof paths in current audit |

`sources.json` currently has no `monitoring_mode` or `alert_eligible` fields on the 226 enabled UAE rows. That means customer-facing code cannot yet distinguish fresh-alert sources from static evidence-library sources.

## Family Truth Table

| Family | Tier A | Tier B | Tier C | Remediation | MONITOR_OK | Current verdict |
|---|---:|---:|---:|---:|---:|---|
| FTA | 22 | 3 | 0 | 0 | 25 | Strong; validate and preserve |
| MoE/DNFBP | 35 | 7 | 1 | 0 | 42 | Strong; validate and preserve |
| VARA | 24 | 0 | 1 | 0 | 16 | Good but 9 sources still need MONITOR_OK/proof reconciliation |
| DFSA | 11 | 2 | 27 | 0 | 32 | Inflated by static notice pages; listing/rulebook sources need priority |
| DIFC | 9 | 1 | 15 | 0 | 17 | Inflated by static pages; legal/database/listing sources need priority |
| ADGM/FSRA | 10 | 1 | 14 | 0 | 15 | Partial; static announcements need demotion and adapters need registry work |
| CBUAE | 25 | 1 | 1 | 0 | 0 | Critical gap; high-value sources but no live MONITOR_OK |
| UAE FIU | 2 | 4 | 0 | 1 | 2 | Weak; annual reports/press work, circulars/typologies need adapter work |
| EOCN/TFS | 0 | 0 | 0 | 2 | 0 | Blocked/critical; direct EOCN is not saleable yet |
| SCA | 0 | 0 | 0 | 5 | 0 | Blocked/critical; exact access blockers must be proven |
| UAE Legislation/MoJ/Gazette | 0 | 0 | 0 | 1 | 0 | WAF/access remediation |
| MoF | 0 | 0 | 1 | 0 | 0 | Generic homepage only; replace with specific official update/document pages |

## Adapter Registry Truth

`product/regradar/app/adapters/registry.py` currently registers only:

- `CBRAdapter`
- `MinfinAdapter`
- `RosfinmonitoringAdapter`

Two UAE extraction modules exist but are intentionally unregistered prototypes:

- `product/regradar/app/adapters/uae_cbuae_rulebook.py`
- `product/regradar/app/adapters/uae_fsra_circulars.py`

Both are function-based prototypes rather than registered `SourceAdapter` subclasses. They must be wrapped or rewritten before production monitoring can select them.

## Source Modes To Add

`fresh_alert`:
Official source can produce future customer-relevant change signal. Requires `MONITOR_OK`, proof/hash/baseline, acceptable source-health/noise risk, and `alert_eligible: true`.

`evidence_library`:
Official source can remain as an evidence/reference record, may have proof and even `MONITOR_OK`, but must not trigger customer update alerts or count in fresh-monitoring claims.

`remediation`:
Important source currently blocked/unreliable/incomplete. Must not count in fresh monitoring claims.

`candidate`:
Researched but not activated.

## Execution Order

1. Add source-mode specification and validators so static sources cannot remain in fresh-alert claims.
2. Register or wrap existing UAE adapters for CBUAE rulebook and ADGM/FSRA circulars.
3. Add a generic official-listing/PDF hash adapter where the existing scraper cannot support fresh signal safely.
4. Reclassify static DFSA/DIFC/ADGM detail pages as `evidence_library`.
5. Target highest-risk families first: CBUAE, SCA, EOCN/TFS, UAE FIU, MoJ/Gazette, MoF.
6. For each family, run controlled no-save tests, then proof/baseline/MONITOR_OK only for strong passes.
7. Update frontend/audit data only with honest `fresh_alert` counts.

## Validation Plan

Validators must block:

- `fresh_alert` without `last_monitor_status == MONITOR_OK`.
- `fresh_alert` without `proof_path`, `normalized_hash`, and baseline.
- Static individual detail pages counted as fresh alerts.
- Generic homepages counted as fresh alerts without explicit justification.
- Remediation sources counted in customer monitoring claims.
- Claims of complete UAE coverage or complete family coverage without validator proof.
- Legal/compliance overclaims.

Existing tests and validators must continue to pass. Frontend build/lint/route checks are required if frontend data or UI copy changes.

## Commit Policy

Only commit after:

- Plan docs exist.
- Code/tests/validators are complete.
- Full backend validation passes.
- Frontend validation passes if touched.
- No runtime junk, secrets, or unrelated files are staged.

## What Will Not Be Claimed

- Complete UAE coverage.
- Complete family coverage unless actually proven by validators.
- Legal advice.
- Guaranteed compliance.
- Perfect parsing.
- Never missing updates.
- Live monitoring for CBUAE/SCA/EOCN/FIU circulars until MONITOR_OK is proven.
