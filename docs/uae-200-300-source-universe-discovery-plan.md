# UAE 200–300 Source Universe Discovery Plan

Date: 2026-06-16
Sprint goal: Map the complete known UAE official regulatory source universe (200+ candidate records) to establish a credible, long-term monitoring pipeline roadmap.

---

## 1. Purpose

StatuteProof currently has 79 enabled UAE sources (76 readiness-supported, 3 remediation). This sprint maps the full potential universe of official UAE regulatory and compliance-relevant endpoints — including already-active sources, candidates at various stages, and rejected sources with documented reasons — to give the product a defensible 200+ source research baseline and a clear activation roadmap.

This is a research and planning document. Nothing in this sprint activates monitoring. All source activation requires the full gate sequence: no-save preview → evidence save → repeat baseline → mass-monitor dry-run → 6-agent review gate.

---

## 2. Starting State (Pre-Sprint)

| Metric | Count |
|--------|------:|
| Enabled UAE sources (sources.json) | 79 |
| Readiness-supported | 76 |
| Under extraction remediation | 3 |
| Candidates in uae_source_candidates.json | 69 |
| Rejected in uae_source_candidates.json | 7 |
| Work queue entries (uae_source_work_queue.json) | 127 |
| Endpoints in 150-report (uae-official-endpoint-discovery-150-report.md) | 151 |

Current active regulator distribution:

| Regulator | Active Sources | % of Pack |
|-----------|---------------|-----------|
| CBUAE | 27 | 34.2% |
| ADGM/FSRA | 11 | 13.9% |
| DFSA | 10 | 12.7% |
| DIFC | 8 | 10.1% |
| VARA | 8 | 10.1% |
| UAE FIU/EOCN | 7 | 8.9% |
| SCA | 5 | 6.3% |
| Federal/Legislation | 3 | 3.8% |
| **Total** | **79** | **100%** |

Known gaps at sprint start:
- VARA coverage thin relative to VASP buyer importance (10% of pack, VASP is primary buyer archetype)
- FTA (Federal Tax Authority) entirely absent from active pack
- Ministry of Justice e-laws absent
- DMCC, DFM, ADX free-zone/exchange coverage absent
- TDRA/data protection coverage absent
- Ministry of Economy AML/DNFBP partially absent

---

## 3. Scope — 10 Source Categories

| Category | Label | Target Regulators | Activation Priority |
|----------|-------|------------------|-------------------|
| A | VARA / Dubai Virtual Assets | VARA, rulebooks.vara.ae | P0 for VASP buyers |
| B | UAE FIU / EOCN / AML | UAE FIU, EOCN, goAML public | P0 for MLROs |
| C | CBUAE / Central Bank | centralbank.ae, rulebook.centralbank.ae | P0 for banks/payments |
| D | DFSA / DIFC Financial | dfsa.ae, dfsaen.thomsonreuters.com | P0 for DFSA firms |
| E | ADGM / FSRA | adgm.com, fsra.adgm.com | P1 for ADGM firms |
| F | SCA / Capital Markets | sca.gov.ae | P1 for securities firms |
| G | DIFC Legal/Courts | difc.com, difccourts.ae | P1 for DIFC firms |
| H | Federal Legislation / MoJ | uaelegislation.gov.ae, moj.gov.ae | P2 for legal context |
| I | Tax / FTA | tax.gov.ae | P2 for taxable entities |
| J | Emirate / Free Zone / Other | dmcc.ae, dfm.ae, tdra.gov.ae | P2–P3 niche |

---

## 4. Target Universe Size

| Group | Target Records |
|-------|---------------|
| Already active (sources.json enabled=true) | 79 |
| Work queue candidates (not yet active) | ~35–45 |
| New discovery (not in any existing file) | ~50–70 |
| Rejected with reason (explicit documentation) | ~25–35 |
| **Total universe** | **~200–220** |

Stretch goal: 250+ if free-zone, court, and emirate-level sources are systematically catalogued.

---

## 5. Discovery Methods Used

1. **Existing file analysis** — sources.json (79 enabled), uae_source_candidates.json (69 candidates), uae_source_work_queue.json (127 entries), uae-official-endpoint-discovery-150-report.md (151 endpoints)
2. **Sitemap enumeration** — SCA, ADGM, UAE FIU sitemaps successfully fetched in 150-report sprint
3. **Robots.txt analysis** — CBUAE, VARA, DFSA (blocked sitemaps, URL patterns reconstructed)
4. **Domain crawl** — Same-domain regulatory link following from known root pages
5. **Regulator knowledge base** — Systematic enumeration of known UAE regulatory authority websites not yet covered
6. **Rejection cataloguing** — Explicit documentation of why specific URLs are excluded

---

## 6. Deliverables

| Deliverable | File | Status |
|-------------|------|--------|
| This plan | docs/uae-200-300-source-universe-discovery-plan.md | ✅ Created |
| Source taxonomy (updated) | docs/uae-regulatory-source-taxonomy.md | ✅ Exists (update target) |
| Research log | docs/uae-200-300-official-source-research-log.md | ✅ Created |
| Candidate universe JSON | product/regradar/config/uae_source_universe_candidates.json | ✅ Created |
| Deduplication report | docs/uae-source-universe-deduplication-report.md | ✅ Created |
| Coverage gap map | docs/uae-comprehensive-coverage-gap-map.md | ✅ Created |
| Activation roadmap | docs/uae-source-universe-prioritized-activation-roadmap.md | ✅ Created |
| Top-20 no-save smoke | docs/uae-source-universe-top20-nosave-smoke-report.md | DEFERRED (requires runtime) |
| Validator | tools/validate_uae_source_universe_candidates.py | ✅ Created |
| Final report | docs/uae-200-300-source-universe-final-report.md | ✅ Created |

---

## 7. Hard Rules (Carry Forward from Standing Policy)

- No source is activated without full gate passage. Gate sequence is mandatory, not optional.
- No claims of "complete UAE coverage," "100% capture," or "never miss updates."
- All source IDs must follow AE-{regulator}-{topic} naming convention.
- All official_status must be "official" or "officially_linked" — never "commercial," "news," "aggregator."
- Any source requiring login, CAPTCHA, paywall, or private access is automatically rejected.
- Social media, law firm commentary, news aggregators, and non-UAE regulators are automatically rejected.
- The candidate JSON is research-only and must not be used to claim product coverage.

---

## 8. Success Criteria

- [ ] At least 200 unique URL records in universe candidates JSON
- [ ] All 79 active sources represented with `activation_status: already_active`
- [ ] At least 25 rejected entries with explicit `reject_reason`
- [ ] At least 50 net-new candidate records not previously in sources.json
- [ ] Validator passes with 0 errors
- [ ] No forbidden claims in any document
- [ ] Git commit with message: `docs: map UAE 200-source official monitoring universe`
