# StatuteProof Source and Evidence Gap Analysis
Audit date: 2026-06-24
Source truth: sources.json (116 enabled, all AE)
Evidence source: source_runs.jsonl (866 runs, 289 unique sources)

---

## Authoritative Source Counts (from sources.json)

| Metric | Count |
|---|---|
| Total records | 432 |
| Enabled (all AE) | 116 |
| Active + enabled | 116 |
| Candidate (active in JSON) | 0 |
| Geo-blocked | 18 |
| disabled_non_uae | 86 |
| disabled_static_pdf | 48 |
| disabled_covered_by_hub | 56 |
| disabled_static_doc | 35 |
| disabled_path_moved | 15 |
| disabled_external_access | 13 |
| disabled_duplicate | 3 |
| disabled_navigation_only | 4 |
| disabled_needs_playwright | 2 |
| disabled_geo_blocked | 1 |
| disabled (generic) | 6 |
| limited | 11 |
| mapped | 13 |
| remediation | 1 |
| replaced | 1 |
| duplicate_url | 3 |

**NOTE**: The source_signal_quality_audit.md and sourceQualityAudit.ts both claim 246 enabled sources. This is stale from a previous state of sources.json. The current authoritative count is 116.

---

## Strongest Source Families

### 1. CBUAE — 25 active sources
**Why strong**: Covers the core central bank regulatory output. Rulebook modules (AML/CFT, Consumer Protection, Open Finance, Payment Token Services, Risk Management, Model Management, Exchange Business Regulation, Retail Payment Services) are high-value for banks, payment firms, and any CBUAE-licensed entity. 25 sources is the deepest family coverage in the product.

**Fresh-alert eligible**: Yes (all 25 are active)
**Evidence trail**: Proof files generated on source runs
**Customer fit**: Banks, payment service providers, exchange houses, insurance firms, any CBUAE-supervised entity

### 2. DFSA — 16 active sources
**Why strong**: Covers DFSA rulebook modules via Thomson Reuters platform (a specialized adapter), consultation papers, enforcement decisions, AML reports, and annual reports. The 16 fresh-alert eligible sources are the listing/hub pages, not individual static detail pages (28 of which are evidence-library only). Hub-level change detection is high-value because it signals new items appearing in the listing.

**Fresh-alert eligible**: 16 of 44 total DFSA sources enabled
**Evidence trail**: Custom DFSA adapter, proof files
**Customer fit**: DFSA-regulated firms, DIFC-based financial services

### 3. ADGM / FSRA — 14 active sources
**Why strong**: Covers FSRA rules and regulations, guidance notes, supervision circulars, public consultations, RA circulars, ADGM enforcement, and data protection. 14 sources across multiple regulatory surfaces. Strong for ADGM-regulated firms.

**Fresh-alert eligible**: 14 of 27 total ADGM sources enabled (internal audit says 11 fresh-alert eligible — discrepancy noted)
**Evidence trail**: Playwright adapter for ADGM content
**Customer fit**: ADGM-regulated entities, FSRA-supervised firms

### 4. DIFC — 12 active sources
**Why strong**: Covers the DIFC Legal Database listing, data protection (Commissioner, guidance, enforcement), DIFC Courts practice and registrar directions, and DFM circulars. Good depth for a free-zone financial center.

**Fresh-alert eligible**: 12 of 25 DIFC sources
**Evidence trail**: DIFC-specific Playwright adapter (SPA handling)
**Customer fit**: DIFC-licensed firms, financial services, legal firms operating in DIFC

### 5. MoE / DNFBP AML — 9 active sources
**Why strong**: Ministry of Economy AML/CFT guidance for Designated Non-Financial Businesses and Professions is a high-volume regulatory topic. 9 sources covering DNFBP licensing, AML guidance, and commercial regulation.

**Fresh-alert eligible**: 9 active sources
**Customer fit**: Law firms, accountants, real estate agents, dealers in precious metals, any DNFBP category

---

## Weakest Source Families

### 1. MoJ / UAE Legislation / Official Gazette — 2 active sources, 0 fresh-alert eligible (per SourceTransparencyMatrix)
**Why weak**: Federal legislation is the highest-value regulatory signal for any firm operating in the UAE. Access is severely limited: Official Gazette is geo-IP blocked, UAE e-Laws Portal is geo-IP blocked, and the UAE Legislation Portal root is in remediation (WAF/access issues). Only 2 sources are active and their fresh-alert eligibility is disputed between components.

**Gaps**: Complete federal legislation monitoring, Official Gazette, UAE e-Laws portal
**Mitigation**: UAE-based server/proxy, or partnership with a UAE data provider
**Customer impact**: HIGH — any firm that needs federal law monitoring gets nothing from this family

### 2. UAE FIU — Limited circulars coverage
**Why weak**: The FIU circulars page resolves to the general publications index, not a distinct circular/notice endpoint. Circulars are often the highest-urgency FIU output. Without circulars coverage, FIU monitoring is incomplete for the most compliance-critical use case.

**Gaps**: FIU circulars (cannot be claimed as monitored), broader FIU notice coverage
**Customer impact**: MEDIUM-HIGH — AML compliance teams specifically need FIU circulars

### 3. UAE CMA / SCA — 6 sources, partial
**Why weak**: SCA/UAE CMA has 6 active sources but the AML/CFT parser/noise review is blocking broader coverage. The root SCA portal is not monitored. Capital markets compliance teams need broader SCA coverage.

**Gaps**: SCA root portal, broader UAE CMA regulations listing, SCA AML/CFT remediation
**Customer impact**: MEDIUM — less critical than VARA/DFSA for most firms

### 4. VARA — 6 direct sources (deeper via PDF adapters)
**Why weak at the direct level**: Only 6 sources are direct VARA portal pages. The audit notes VARA has higher counts via PDF rulebook adapters — but these may not be counted in sources.json as separate entries or may be consolidated differently. If a VASP prospect sees "6 VARA sources" they may be underwhelmed.

**Note**: The internal audit claims 25+ VARA sources — the discrepancy vs 6 from URL analysis may be due to PDF sources not having vara.ae URLs. Investigation needed.
**Customer impact**: MEDIUM — VASP customers expect deep VARA coverage

### 5. FTA Tax — 6 direct portal sources (separate PDF endpoint count)
**Why weak**: The FTA has extensive guidance, decisions, and clarifications that are high-value for corporate tax compliance teams. Only 6 active sources via direct FTA portal URLs. The MoF family includes FTA PDF endpoints, but portal/listing extraction for FTA item-level content is still candidate/roadmap.

**Gaps**: FTA item-level portal extraction, broader FTA listing coverage
**Customer impact**: MEDIUM — tax advisers and corporate finance teams need this

---

## Sources That Should NOT Be Counted in Sales Claims

1. **UAE Legislation Portal** — in remediation, not accessible reliably
2. **UAE Official Gazette** — geo-IP blocked from outside UAE
3. **UAE e-Laws Portal (MoJ)** — geo-IP blocked from outside UAE
4. **UAE Data Office / TDRA (uaedp.gov.ae)** — geo-IP blocked from outside UAE
5. **CBUAE main homepage** — evidence-library only (navigation shell, not document listing)
6. **CBUAE generic regulations page** — candidate/held, not active
7. **UAE FIU Homepage** — navigation shell, evidence-library only
8. **UAE FIU Circulars** — resolves to general publications index, not a distinct circulars endpoint
9. **Static DFSA detail pages (28 of them)** — evidence-library only, not fresh-alert eligible
10. **Static DIFC individual pages** — evidence-library only
11. **ADGM FSRA dedicated regulatory-alerts page** — candidate pending selector remediation
12. **ADGM FSRA rulebook on Thomson Reuters** — restricted external access

---

## Evidence Gaps (What Is Missing for Customer-Grade Evidence Pack)

### Gap 1: Zero completed canonical evidence records with human review
The canonical evidence record pipeline exists and enforces hash verification. But no canonical evidence record with a completed review decision (approved/rejected) exists in local data. The `data/evidence_reviews/canonical_evidence_reviews.jsonl` path exists but the actual directory state shows only subdirectories for internal_briefs.

**Impact**: Cannot demonstrate the full evidence chain to a customer auditor

**Fix**: Pick one CHANGED source from alert queue, run `python3 tools/generate_canonical_evidence.py`, complete review with `python3 tools/review_canonical_evidence.py`

### Gap 2: 7 alert queue items are PENDING_REVIEW from June 11-15 (13 days old)
CBUAE, DFSA, MoF, UAE FIU, MoE, VARA, UAE Legislation Portal all have CHANGED alerts that were never human-reviewed. They sit in the queue with delivery_approved: False.

**Impact**: Demonstrates that the review workflow is not being executed — the core human-review gate exists but no one is using it

**Fix**: Founder reviews each alert, records decision, moves to approved or rejected

### Gap 3: No monitor_ok flag in source run records
866 source runs exist but none have `monitor_ok` set. This field is used by the source quality audit to distinguish validated monitoring from raw runs. Without it, "MONITOR_OK" claims in the audit are based on a separate validation pass that is not persisted in the run record.

**Impact**: Cannot programmatically prove which sources have passed all quality gates

**Fix**: Add monitor_ok flag to the intake pipeline run record when all quality checks pass

### Gap 4: No customer-facing evidence export has been generated
The `AuditBinderExport.jsx` component exists in the frontend. The `audit_export.py` backend module exists. But no evidence export has been generated for a real customer. The "Audit Binder" is a sample/fake on the landing page.

**Impact**: Cannot demonstrate the audit binder to a prospect using real data

**Fix**: Generate one complete audit binder from a real CHANGED alert with completed canonical evidence

### Gap 5: Source quality audit file is stale (246 vs 116)
The `source_signal_quality_audit.json` that drives both `sourceQualityAudit.ts` and `source_signal_quality_audit.md` is from a previous state of sources.json with 246 enabled sources. It needs to be regenerated.

**Fix**: Run `python3 product/regradar/reports/validate_audit.py` (or the equivalent audit script) against the current sources.json and regenerate

---

## Canonical Evidence Record Gaps

For a canonical evidence record to be customer-grade, it needs:
- `run_id` — present
- `source_id` and `source_name` — present
- `official_url` — present
- `timestamp_utc` — present
- `proof_block_path` — present (773/866 runs have this)
- `snapshot_normalized_path` + `normalized_hash` — present (815/866 runs have hash)
- `snapshot_raw_path` — present
- `snapshot_metadata_path` — present in most runs
- `change_status` in {FIRST_SEEN, UNCHANGED, CHANGED} — present (51 FAILED excluded)
- Verified hash match: `sha256(snapshot_normalized) == normalized_hash` — enforced in evidence_records.py
- Human review decision: `review_status` in {approved, rejected, blocked} — **MISSING for all records**

**Conclusion**: The data artifacts exist for many runs. The missing piece is completing the human review step.

---

## Risk-Brief Eligibility Gaps

For a source to produce a customer risk brief:
1. Source must be enabled and active — 116 sources meet this
2. Source run must have `change_status = CHANGED` — 66 runs across 39 sources meet this
3. Proof file must exist — 773/866 runs have proof_block_path
4. Hash must verify — enforced in code
5. Run must not be FAILED or QUALITY_DROP — 61 such runs are excluded
6. Canonical evidence record must exist — **0 exist**
7. Human review decision must be "approved" — **0 exist**
8. Brief must be reviewed before delivery — **0 briefs delivered**

**Conclusion**: 0 briefs are eligible for customer delivery. All 66 CHANGED runs are stuck at step 6.

---

## Reliability Gaps (7/30/90-Day)

**What exists**: `source_health_timeline.py` exists and appears to compute per-source reliability. 7 tests for source health timeline pass.

**What is missing from the product**:
- The dashboard does not display 7-day or 30-day reliability metrics
- The source runs JSONL has 866 entries covering May 29 - June 21 (~23 days), so 30-day data exists
- No customer-visible "source reliability score" or "access success rate" is displayed
- No alerts when a source drops below a reliability threshold

**Rough reliability from source runs data**:
- accessible: 804/866 = 92.8%
- failed: 10/866 = 1.2% (distinct from change_status FAILED)
- restricted: 41/866 = 4.7%
- dynamic/adapter_needed: 11/866 = 1.3%
- QUALITY_DROP: 10/866 = 1.2%

This 92.8% accessibility rate is a strong metric but is not surfaced to customers.

---

## Next Exact Source Improvement Tasks

In priority order:

1. **Regenerate source_signal_quality_audit.json** from actual sources.json (116 enabled). Update sourceQualityAudit.ts and source_signal_quality_audit.md. Fix 5 failing tests.

2. **Complete human review for the 7 June 11-15 CHANGED alerts**:
   - AE-central-bank-of-the-uae
   - AE-dubai-financial-services-authority-dfsa
   - AE-uae-ministry-of-finance
   - AE-uae-financial-intelligence-unit-uaefiu
   - AE-uae-ministry-of-economy
   - AE-dubai-virtual-assets-regulatory-authority-vara
   - AE-uae-legislation-portal

3. **Generate first canonical evidence record** for one of the reviewed alerts.

4. **Add monitor_ok flag** to the source intake pipeline run record.

5. **Investigate VARA source count discrepancy**: Direct URL analysis shows 6 VARA sources; internal audit claims 25. Reconcile — likely PDF adapters or renamed sources are not being caught by simple URL grep. Determine actual count.

6. **Remediate SCA AML/CFT parser noise** — this blocks broader UAE CMA/SCA coverage claims.

7. **Remediate ADGM FSRA dedicated regulatory-alerts listing** — candidate, pending selector fix.

8. **Activate geo-mitigation strategy for Official Gazette** — either accept the gap permanently or plan UAE-based access.

9. **Add UAE FIU circulars investigation** — confirm whether a distinct circulars endpoint exists or document definitively that it does not.

10. **Surface reliability metrics in dashboard** — 92.8% access rate is a good metric, make it visible.

---

*Analysis based on sources.json at audit date. Source counts may change as sources are activated or disabled.*
