# SOURCE_PORTFOLIO — Phase 0-D (signal-max sprint)

Date: 2026-07-06 · Data: `sources.json` (432 sources, 116 enabled) + 1,406
run records + noise anatomy. Per-source rows with evidence:
`portfolio.jsonl` (432 lines). Tiering rules are mechanical and documented in
`scripts/signal/portfolio.py`.

## Headline counts (truthful triple)

```
432 configured / 116 enabled / 83 fresh-alert eligible
Eligibility = monitoring_mode == "fresh_alert" AND alert_eligible == true
(app/source_summary.py:36-40)
```

| Tier | Count | Definition (evidence per row in portfolio.jsonl) |
|---|---|---|
| A | 56 | enabled + eligible, GOOD extraction seen, no recent access failures, no chrome markers in latest snapshot |
| B | 27 | enabled + eligible but PDF-only, or chrome contamination observed (baseline flips on clean) |
| C | 33 | enabled but NOT fresh-alert eligible (breakdown below) |
| REMEDIATION | 27 | enabled with recent FAILED/restricted access, or status limited/remediation/path_moved |
| EXCLUDE-REVIEW | 153 | disabled: non-UAE (86), covered_by_hub (56), duplicates (6), navigation_only (4), replaced (1) |
| INACTIVE-POOL | 136 | disabled but activatable: static_pdf (48), static_doc (35), geo_blocked (19), mapped (13), needs_playwright (2), other (19) |

## The 33 enabled-but-not-eligible — exact reasons

Full per-source list: `portfolio_output.txt`. Grouped:

| Group | N | Exact reason |
|---|---|---|
| Never classified | 21 | `monitoring_mode` and `alert_eligible` were never set after intake (VARA Public Register, DFSA Public Register, FTA VAT Public Clarifications, DIFC Courts practice/registrar directions, DIFC/ADGM/DFSA news hubs, MoJ/DFM/ICP/TDRA/MOCCAE/JAFZA/DMCC media centres, Dubai Legislation Portal search, MoE AML hub, ADGM Office of Data Protection, DFSA SEO letters). They run in monitoring but can never alert. |
| FTA candidates | 5 | "Candidate only after 2026-06-18 no-save retest: rendered FTA page exposed nav-shell" — extraction proved nav-only, honest downgrade |
| ADGM candidates | 3 | `AE-adgm-fsra-waivers`, `AE-adgm-ra-circulars` (alert_eligible=False, useful-but-unproven), `AE-adgm-fsra-regulatory-alerts` (post-retest candidate) |
| Evidence-library homepages | 4 | VARA homepage (JS SPA degrades to minimal text), UAE MoF homepage (generic portal), MoE homepage (low regulatory signal), DFSA consultation-paper-165 (static rulebook page via Thomson Reuters platform) |

## Top-20 activation candidates (AE-only pool = 115)

Ranking = category value for the assumed personas (UAE compliance officers at
banks / VASPs / DNFBPs / payments firms — **ASSUMED: the only market evidence
in the repo is the legacy RegRadar positioning file `data/market_strategy.json`
dated 2026-05-26; no customer interviews or won deals recorded**) + fresh-alert
potential − technical risk. Full scoring: `scripts/signal/portfolio.py` +
`top20_candidates.txt`.

| # | Source | Category | Technical risk | Persona value |
|---|---|---|---|---|
| 1 | AE-adgm-fsra-waivers | financial_regulator | candidate — needs retest | ASSUMED high (ADGM firms) |
| 2 | AE-adgm-ra-circulars | financial_regulator | candidate — needs retest | ASSUMED high |
| 3 | AE-fta-tax-legislation-listing | tax | JS nav-shell (needs rendering or adapter) | ASSUMED high (every UAE firm) |
| 4 | AE-fta-vat-guides-references | tax | same | ASSUMED high |
| 5 | AE-fta-corporate-tax-guides-references | tax | same | ASSUMED high |
| 6 | AE-fta-media-centre | tax | same | ASSUMED medium |
| 7 | AE-fta-corporate-tax-legislation | tax | same | ASSUMED high |
| 8 | AE-uae-financial-intelligence-unit-uaefiu | aml | geo-blocked (was enabled, then blocked) | ASSUMED high (MLROs) |
| 9 | AE-uaefiu-circulars | aml | geo-blocked | ASSUMED high |
| 10 | AE-uaefiu-typology-reports | aml | geo-blocked | ASSUMED high |
| 11 | AE-uaefiu-aml-cft-laws | aml | geo-blocked | ASSUMED high |
| 12 | AE-uaefiu-publications-hub | aml | geo-blocked | ASSUMED high |
| 13 | AE-uaefiu-annual-reports | uae_fiu | geo-blocked | ASSUMED medium |
| 14 | AE-uaefiu-press-releases | uae_fiu | geo-blocked | ASSUMED medium |
| 15 | AE-uaefiu-system-guides | aml | geo-blocked | ASSUMED medium |
| 16 | DIFC Consultation Papers Index | financial_regulator | JS rendering needed (Playwright) | ASSUMED high (DIFC firms) |
| 17 | UAE FIU Laws and Regulations | aml | geo-blocked | ASSUMED high |
| 18 | AE-central-bank-of-the-uae | central_bank | geo-blocked + heavy chrome (counters) | ASSUMED high (banks/payments) |
| 19 | UAE Federal Tax Authority (FTA) | tax | external access blocked | ASSUMED high |
| 20 | AE-cbuae-regulations | central_bank | geo-blocked + counters | ASSUMED high |

Notes:
- The 48 VARA static PDFs + 35 MOET DNFBP static docs are **evidence-library**
  candidates (document text is regulatory gold; pages never change) — they are
  deliberately NOT in the fresh-alert top-20.
- geo-blocked UAEFIU/CBUAE family: 12 of the top 20 — activation depends on
  fetch strategy (server location / rendering), not on adapters. Real risk;
  no promise until a one-shot fetch proves access (F6).
- All persona-value cells are ASSUMED pending market evidence. This is a
  ranking hypothesis, not a claim.
