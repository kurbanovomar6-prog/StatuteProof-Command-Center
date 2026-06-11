# RegRadar Improvement Pack — 2026-05-24

## Summary

This pack covers all source classification improvements, scoring logic changes, and live-site regression documentation made on 2026-05-24 before expanding to new jurisdictions.

---

## 1. Turkey (TR) — Activated

Both previously-mapped Turkish sources were promoted to active.

| Source | Before | After | Extraction |
|--------|--------|-------|-----------|
| KVKK (Data Protection Authority) | `mapped`, disabled | `active`, enabled | 1,835c — good |
| Rekabet (Competition Authority) | `mapped`, disabled | `active`, enabled | 2,248c — good |

TR coverage score: **83 (usable)** with 9 sources, 7 good, 2 low-content.

---

## 2. Saudi Arabia (SA) — Source Reclassification

5 of 7 SA sources are externally inaccessible. All were reclassified from generic `"disabled"` to `"disabled_external_access"` to document the reason and exclude them from the coverage denominator.

| Source | Status | Reason | Alt URL noted |
|--------|--------|--------|---------------|
| SAMA (Central Bank) | `disabled_external_access` | Full SPA migration — Playwright returns 0c; PDF adapter recommended | Root has 5 PDFs with 44,569c |
| CMA (Capital Markets) | `disabled_external_access` | Critical gap — primary SA capital markets regulator | — |
| MoF (Ministry of Finance) | `disabled_external_access` | Arabic SharePoint returns 0c to crawler | `/ar/Pages/default.aspx` |
| BOE (Business Environment) | `disabled_external_access` | Requires in-country access or partner proxy | — |
| SDAIA (Data Authority) | `disabled_external_access` | HTTP/2 protocol block | — |

Active scoreable sources: ZATCA (good, 1,029c) + CST (low_content, ~266c).
SA coverage score: **62 (limited)**.

---

## 3. UAE (AE) — Source Reclassification

3 UAE sources reclassified for accuracy.

| Source | Before | After | Reason |
|--------|--------|-------|--------|
| SCA (Securities & Commodities) | `limited` | `disabled_navigation_only` | Returns identical 944–1,056c on every page — site navigation menu only, cannot detect regulatory changes |
| FTA (Federal Tax Authority) | `disabled` | `disabled_external_access` | Login wall; alt: `tax.gov.ae/en/resources/legislation.aspx` |
| e-Laws (legislation portal) | `disabled` | `disabled_external_access` | Geo-IP block |

All 7 active AE sources extract successfully.
AE coverage score: **100 (strong)**.

---

## 4. New Source Status Categories

Three new status values were added to `app/sources.py` (`_VALID_STATUSES`):

| Status | Meaning |
|--------|---------|
| `disabled_external_access` | Geo-block, JS SPA with 0c extraction, HTTP/2 protocol errors — not adapter-fixable |
| `disabled_navigation_only` | SPA returns only navigation/menu text on all pages — structurally misleading |
| `adapter_required` | Site loads but needs a custom adapter for reliable content extraction |

Without registering these in `_VALID_STATUSES`, `validate_source()` silently dropped all 8 affected sources — fixed.

---

## 5. Coverage Scoring Logic Changes (`app/coverage.py`)

### 5a. Score Exclusion

Sources with `disabled_external_access` or `disabled_navigation_only` are excluded from **both** numerator and denominator. They don't penalise the score — they're not the operator's fault.

```python
_EXCLUDED_FROM_SCORE = frozenset({
    "disabled_external_access",
    "disabled_navigation_only",
})
```

### 5b. Coverage Level Downgrade (`_coverage_level_label`)

When a jurisdiction has many restricted sources, its score may look artificially high. The downgrade rule:

- Requires **≥ 4 restricted sources** AND **≥ 50 % of total**
- Downgrades `strong` → `limited`, `usable` → `limited`

Effect:
- **AE**: 3/10 = 30 % → NOT downgraded → stays `strong`
- **SA**: 5/7 = 71 %, ≥ 4 → would downgrade `strong`/`usable` → SA is already `limited` by score

### 5c. Report Additions

- Jurisdiction table: new `Rst` column (restricted count)
- Summary: `Externally restricted: N` line
- Gaps section: separate message for restricted vs failed sources
- HTML report: `Restricted` column in jurisdiction table

---

## 6. Health Check Changes (`app/health.py`)

- Added `_SKIP_STATUSES` constant for `disabled_external_access` and `disabled_navigation_only`
- Restricted sources display `restricted:<status>` label instead of plain "disabled"
- Result after all changes: **PASS: 40, WARN: 3, SKIP: 23+, FAIL: 0**

---

## 7. Source Audit / Adapter Queue Changes (`app/source_audit.py`)

- `_priority()`: restricted sources return `"LOW"` immediately — they are not adapter tasks
- `_suggest_next_step()`: specific guidance for each restricted status type
- `print_adapter_queue()`: restricted sources shown in a separate **KNOWN RESTRICTIONS** section below actionable adapter tasks

---

## 8. Live Site Regressions (Discovered 2026-05-24)

Three previously-working sources degraded during this session due to site-side SPA migrations:

| Source | Was | Now | Action |
|--------|-----|-----|--------|
| SAMA | 1,589c (active) | 0c | `disabled_external_access` — PDF adapter recommended |
| BDDK (Turkey) | 2,638c (active) | 158c | `limited` — monitoring |
| CST (Saudi Arabia) | 1,198c (active) | ~266c | `limited` — monitoring |
| Resmigazete (Turkey) | 43,875c (active) | ~505c | Still `active`, shows `low_content` in audit |

---

## 9. Coverage Report Results (2026-05-24)

| Jurisdiction | Score | Label | Good | Low | Fail | Restricted |
|-------------|-------|-------|------|-----|------|-----------|
| AE | 100 | strong | 7 | 0 | 0 | 3 |
| AM | 8 | weak | 0 | 1 | 4 | 0 |
| AZ | 67 | usable | 3 | 1 | 1 | 0 |
| BY | 86 | strong | 3 | 1 | 0 | 0 |
| GE | 89 | strong | 4 | 1 | 0 | 0 |
| INT | 75 | usable | 7 | 3 | 0 | 0 |
| KZ | 77 | usable | 6 | 0 | 2 | 0 |
| RU | 75 | usable | 3 | 1 | 1 | 0 |
| SA | 62 | limited | 1 | 1 | 0 | 5 |
| TR | 83 | usable | 7 | 2 | 0 | 0 |
| UZ | 90 | strong | 5 | 0 | 1 | 0 |

**Overall: 78 (limited)** — 74 sources, 8 externally restricted, 20 need adapters.

---

## 10. Files Changed

| File | Changes |
|------|---------|
| `sources.json` | 12 edits: KVKK/Rekabet activated; SAMA/CST/BDDK regressions; 7 SA/AE reclassifications |
| `app/sources.py` | Extended `_VALID_STATUSES` with 3 new statuses |
| `app/coverage.py` | Scoring exclusion, `_coverage_level_label`, restricted column, gap messages |
| `app/health.py` | `_SKIP_STATUSES`, display improvements |
| `app/source_audit.py` | `_RESTRICTED_STATUSES`, priority logic, split adapter queue |
| `reports/source_audit_2026-05-24.json` | Refreshed — 74 sources |
| `reports/coverage_2026-05-24.json` | Generated — all jurisdictions |
| `reports/coverage_2026-05-24.html` | Generated |

---

## 11. Next Steps

- **Singapore (SG)**: next jurisdiction to add (not in this pack)
- **Armenia (AM)**: 4 failed sources need DNS/SSL investigation
- **SAMA PDF adapter**: highest-value adapter task (44,569c of regulatory PDFs)
- **Adapter priority queue**: 20 sources, run `python3 run.py adapter-queue` for ranked list
