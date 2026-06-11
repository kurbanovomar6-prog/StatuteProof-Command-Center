# RegRadar — Coverage Quality Improvement Report
## 2026-05-25

---

## Overall Status

| Metric | Value |
|--------|-------|
| Total sources | **82** |
| Health PASS | **48** |
| Health WARN | **3** (BDDK TR 158c, CST SA 266c, ARLIS AM 33c — same as before) |
| Health SKIP | **31** (disabled/restricted sources) |
| Health FAIL | **0** |
| Jurisdictions | **12** (AE, AZ, AM, BY, GE, INT, KZ, RU, SA, SG, TR, UZ) |

No regressions. All 8 SG sources pass.

---

## Coverage by Jurisdiction (Latest)

| Jurisdiction | Score | Label | Good | Low | Fail | Restricted |
|-------------|-------|-------|------|-----|------|-----------|
| **SG** | **100** | **strong** | **8** | **0** | **0** | **0** |
| AE | 100 | strong | 7 | 0 | 0 | 3 |
| KZ | 93 | strong | 7 | 0 | 1 | 0 |
| UZ | 90 | strong | 5 | 0 | 1 | 0 |
| GE | 89 | strong | 4 | 1 | 0 | 0 |
| BY | 86 | strong | 3 | 1 | 0 | 0 |
| TR | 83 | usable | 7 | 2 | 0 | 0 |
| RU | 75 | usable | 3 | 1 | 1 | 0 |
| INT | 75 | usable | 7 | 3 | 0 | 0 |
| AZ | 67 | usable | 3 | 1 | 1 | 0 |
| SA | 62 | limited | 1 | 1 | 0 | 5 |
| AM | 8 | weak | 0 | 1 | 4 | 0 |

---

## Improvements Made (2026-05-24 → 2026-05-25)

### Singapore (SG) Added — 2026-05-24

8 sources added, all active, all passing health checks. 100/100 strong.
See `reports/sg_source_pack_2026-05-24.md`.

### Source Connection Engine Built — 2026-05-25

New `app/source_connector/` package enabling:
- Automated source quality scoring (0–100 calibrated scale)
- Deep URL discovery (20 regulatory path patterns)
- Language fallback detection
- API endpoint hints for SPA sites
- Full `discover-source` CLI command with JSON export

### Quality Scoring Calibrated

Previous scoring gave 6,986c sources "unusable" (38/100). Fixed:
- Content ≥ 5,000c now scores 60 (was 38) → "acceptable"
- Content ≥ 1,000c now scores 50 (was 30) → "acceptable"
- Structural signals now award up to 30 pts (was 25)
- "excellent" threshold: 80+ (unchanged)

---

## Known Limitations and Next Actions

### Armenia (AM) — Score 8 / weak

4 of 5 AM sources fail (ARLIS consistently low at 33c). AM needs custom adapters for:
- ARLIS (legal database)
- CBA Armenia (central bank)
- State Revenue Committee (tax)
- PDPD Armenia (data protection)

**Recommended**: Mark as `adapter_required`; build lightweight adapters for CBA and ARLIS.

### Saudi Arabia (SA) — Score 62 / limited

5 SA sources are geo-blocked (`disabled_external_access`). Excluded from denominator.
Only ZATCA (1,029c good) and CST (266c low) are reachable. SAMA is completely blocked.

**Recommended**: No near-term fix possible without proxy infrastructure. Document as known limitation.

### WARNs (TR, SA)

- BDDK (TR) 158c: Turkish banking regulator, likely JS-SPA. Needs Playwright adapter.
- CST (SA) 266c: Saudi IT regulator, geo-restricted content.
- ARLIS (AM) 33c: Armenian legal database, consistently fails extraction.

---

## Discover-Source API Endpoint (Needed for Web Component)

`DiscoverSource.jsx` component calls `GET /api/discover-source?url=...&jurisdiction=...&category=...`.

This API endpoint is **not yet implemented** in `run.py api` server. Required addition:

```python
@app.route("/api/discover-source")
def api_discover_source():
    url = request.args.get("url", "")
    jurisdiction = request.args.get("jurisdiction", "")
    category = request.args.get("category", "")
    if not url:
        return jsonify({"error": "url required"}), 400
    result = run_source_onboarding(url, jurisdiction=jurisdiction, category=category)
    return jsonify(build_json_report(result))
```

This should be added to the Flask/API server in a future task.

---

## Reports Generated

| File | Content |
|------|---------|
| `reports/coverage_2026-05-25.json` | Full coverage data for all 12 jurisdictions |
| `reports/coverage_2026-05-25.html` | HTML dashboard |
| `reports/source_audit_2026-05-25.json` | Source audit with extraction quality |
| `reports/source_discovery_examples_2026-05-25.json` | 5 discover-source example outputs |
| `reports/adaptive_source_connection_report_2026-05-25.md` | Engine implementation report |
| `docs/source_onboarding_rules.md` | Future country onboarding rules |
| `web/src/components/DiscoverSource.jsx` | "Add Your Own Source" web component |
