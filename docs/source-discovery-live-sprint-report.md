# Source Discovery Live Sprint Report

Date: 2026-06-15

## Scope

This sprint ran scoped discovery/no-save checks only. No broad monitoring, evidence save, customer delivery, or `sources.json` activation was performed.

## Targets Tested

| Target | Method | Result | Next action |
|---|---|---|---|
| SCA latest regulations | discover-source + no-save | Table/listing detected; no-save remained selector review with limited two-row extraction. | Build SCA row/detail adapter before save. |
| SCA AML/CFT | no-save with SCA adapter | Public content extracted through fallback, quality 59, `CONFIRMED_ACCESSIBLE`; SCA adapter failed item isolation. | Fix SCA item-level listing/table adapter. |
| DFSA rulebook modules | no-save with DFSA rulebook adapter | 98 modules extracted, quality 53, `CONFIRMED_ACCESSIBLE`; preview only and below save threshold. | Improve rulebook/module quality scoring and run evidence baseline only after threshold passes. |
| DFSA AML/MLRO notices | discover-source | RSS/sitemap found; many PDF notice links detected on official DFSA page but hosted on S3. | Treat off-domain documents as `officially_linked` candidates requiring manual review and evidence gates. |
| CBUAE regulations | discover-source | HTTP 403. | Remediation; investigate public sitemap/API/document alternatives. |
| ADGM financial crime | discover-source | Custom element content detected with `adgm-page`; no-save/save eligibility path identified. | Candidate for scoped baseline follow-up using existing ADGM selector strategy. |
| VARA rulebooks / regulatory framework URLs | discover-source | HTTP 404 on tested URLs. | Mark URLs stale; rediscover current VARA rulebook/PDF paths. |
| UAE FIU publications | discover-source | HTTP 403. | Remediation; investigate sitemap/API/document alternatives without bypassing access controls. |
| EOCN homepage / laws listing | discover-source + no-save | Laws/regulations listing discovered; no-save extracted one item but failed quality as shallow/nav-shell. | Improve FIU/EOCN document-listing adapter and selector. |

## Counts

- Live discovery targets tested: 8
- No-save checks run: 4
- Preview-accessible no-save results: 2
- Save-eligible results: 0
- Saved evidence runs: 0
- Baseline-complete sources: 0
- Activation-ready sources: 0
- Public source truth changed: no

Discovery surfaced more than 150 raw endpoint/document/link candidates across the scoped targets, with DFSA AML/MLRO notices producing a large set of document links. These are not active sources.

## Useful Endpoints Found

- `https://dfsaen.thomsonreuters.com/rulebook/rulebook-modules` as a high-value DFSA rulebook module listing.
- `https://www.dfsa.ae/rss` and `https://www.dfsa.ae/sitemap.xml` as low-risk DFSA discovery anchors.
- DFSA AML/MLRO notice PDFs linked from the official DFSA page, now modeled as `officially_linked` manual-review candidates.
- `https://www.adgm.com/operating-in-adgm/financial-and-cyber-crime-prevention` as an ADGM custom-element candidate.
- `https://www.eocn.gov.ae/ar-ae/laws-regulations-listing` as a high-relevance EOCN laws/regulations candidate that needs better item extraction.
- SCA AML/CFT and latest regulations pages as public accessible targets that need SCA-specific item-level extraction.

## What Did Not Pass

No source in this sprint passed the full working-source definition. No source has new saved proof, repeat baseline, Evidence Trail pass, QA pass, Legal Language pass, and Product Manager activation approval from this task.

## Next Remediation Batch

Build and test source-specific item-level adapters for:

1. SCA table/listing rows and detail links.
2. EOCN/FIU laws/publication listings.
3. DFSA officially linked PDF provenance and document evidence handling.
4. DFSA rulebook module quality threshold improvement.
