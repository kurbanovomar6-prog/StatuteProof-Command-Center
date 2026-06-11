# RegRadar — Adaptive Parsing & Source Connection Engine
## Implementation Report — 2026-05-25

---

## Summary

A full Source Connection Strategy Engine has been built and integrated into RegRadar. It provides:
- A 4-stage automated source discovery pipeline
- A `discover-source` CLI command for analyst and user-submitted source evaluation
- A 0–100 quality scoring system calibrated to RegRadar's extraction thresholds
- Deep URL probing across 20 regulatory path patterns
- Language fallback detection (9 language variants)
- API endpoint hints for SPA sites
- A machine-readable JSON report format (camelCase)
- A web component skeleton for user-submitted sources

---

## New Package: `app/source_connector/`

| File | Purpose |
|------|---------|
| `__init__.py` | Public API: `run_source_onboarding`, `build_json_report` |
| `quality_scoring.py` | 0–100 scorer: content quality (0–70) + structural signals (0–30) + JS penalty (−5) |
| `deep_url_discovery.py` | Probes 20 regulatory paths on same domain, returns sorted candidates |
| `language_discovery.py` | Tests 9 language variants (`/en`, `/ru`, `/ar`, `/tr`, `/az`, `/ka`, `/kk`, `/hy`, `/uz`) |
| `api_discovery.py` | Tests 15 public API paths for SPA detection (no auth bypass) |
| `source_onboarding.py` | 4-stage orchestrator: discovery → probe → language → API → score → verdict |
| `connection_report.py` | camelCase JSON report builder |

---

## Quality Scoring Scale (Updated)

| Score | Label | Description |
|-------|-------|-------------|
| 80–100 | **excellent** | Rich content + structured monitoring available |
| 65–79 | **good** | Strong content, ideally with RSS or sitemap |
| 50–64 | **acceptable** | Good content (≥ 5,000c), basic HTML monitoring |
| 35–49 | **weak** | Low-moderate content, use with caution |
| 0–34 | **unusable** | Extraction failed or < 500c |

Content quality (0–70):
- ≥ 20,000c → 70
- ≥ 5,000c → 60
- ≥ 1,000c → 50
- ≥ 500c → 30
- ≥ 100c → 15
- 0c → 0

Structural signals (0–30 additive): RSS/Atom feed → +12, sitemap → +10, documents → +8, API endpoint → +5.

---

## CLI: `discover-source`

```bash
python3 run.py discover-source <url>
python3 run.py discover-source <url> --json
python3 run.py discover-source <url> --jurisdiction CODE --category NAME --json
```

### Example Results (2026-05-25)

| Source | Type | Chars | Score | Label | Status |
|--------|------|-------|-------|-------|--------|
| IRAS Tax Newsroom (SG) | strong | 6,986c | 60 | acceptable | active |
| ACRA Singapore | good | 3,497c | 60 | acceptable | active |
| CCCS Singapore (SPA) | SPA | 4,268c | 60 | acceptable | active |
| IOSCO Publications | document-heavy | 3,766c | 50 | acceptable | limited |
| ARLIS Armenia | weak | 1,169c | 45 | weak | limited |
| SAMA Saudi Arabia | restricted | 0c | 3 | unusable | limited |

---

## `discover-source` JSON Output Format

```json
{
  "submittedUrl": "https://iras.gov.sg/news-events/newsroom",
  "bestMonitoringUrl": "https://iras.gov.sg/news-events/newsroom",
  "sourceName": "strong_source",
  "jurisdiction": "SG",
  "category": "tax",
  "recommendedStatus": "active",
  "connectionMethod": "static_html",
  "qualityScore": 60,
  "qualityLabel": "acceptable",
  "extractedChars": 6986,
  "documentsFound": 0,
  "rssFeedsFound": 0,
  "sitemapsFound": 0,
  "apiEndpointsFound": 0,
  "language": "Unknown",
  "limitations": ["No RSS feed or sitemap found for structured monitoring"],
  "testedMethods": ["static_html", "sitemap_discovery", "rss_discovery", "document_discovery", "deep_url_discovery", "language_fallback", "api_discovery"],
  "deepUrlCandidates": [],
  "languageVersions": [],
  "apiEndpoints": [],
  "verdict": "can_monitor",
  "reason": "Static HTML extraction succeeded (6,986 chars via beautifulsoup). Ready for generic HTML monitoring.",
  "summary": "Source monitorable with limitations. 6,986 chars extracted. Quality score: 60/100.",
  "nextSteps": ["Activate for pilot monitoring and review extraction quality periodically."],
  "generatedAt": "2026-05-25"
}
```

---

## `run.py` Changes

- Added `_cmd_discover_source(url, json_export, jurisdiction, category)` function
- Added `elif cmd == "discover-source":` dispatcher block with `--json`, `--jurisdiction`, `--category` flag parsing
- Updated help text with 4 new usage lines
- Updated unknown-command error to include `discover-source`

---

## Quality Gates — Results

| Gate | Status |
|------|--------|
| Health FAIL count | **0** (PASS: 48, WARN: 3, SKIP: 31) |
| No fake coverage | **PASS** — restricted sources remain excluded from score |
| No regressions | **PASS** — all pre-existing WARNs are the same 3 known sources |
| Source count | **82 total** (unchanged) |
| SG sources | **8 / 8 PASS** |

---

## Files Created or Modified

| File | Type | Change |
|------|------|--------|
| `app/source_connector/__init__.py` | new | Package entry point |
| `app/source_connector/quality_scoring.py` | new | 0–100 scorer (thresholds updated) |
| `app/source_connector/deep_url_discovery.py` | new | 20-path deep URL probing |
| `app/source_connector/language_discovery.py` | new | 9 language variant detection |
| `app/source_connector/api_discovery.py` | new | 15 API path hints |
| `app/source_connector/source_onboarding.py` | new | 4-stage orchestrator + scraper fallback |
| `app/source_connector/connection_report.py` | new | camelCase JSON builder |
| `run.py` | modified | `discover-source` command + help |
| `docs/source_onboarding_rules.md` | new | Future country onboarding procedure |
| `reports/source_discovery_examples_2026-05-25.json` | new | 5 example source types |
| `reports/coverage_2026-05-25.json` | refreshed | Updated coverage |
| `reports/coverage_2026-05-25.html` | refreshed | Updated HTML dashboard |
| `reports/source_audit_2026-05-25.json` | refreshed | Updated audit |
