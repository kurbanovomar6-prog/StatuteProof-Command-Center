# Universal Parser — Current State Audit

**Date:** 2026-06-13  
**Auditor:** code-architect-dev agent  
**Scope:** product/regradar/app/ scraping and extraction stack  
**Purpose:** Document what exists, what works, what is broken, and what gaps must be filled before implementing the Universal Source Intake engine.

---

## Files Audited

| File | Lines | Role |
|---|---|---|
| `app/scraper.py` | 362 | HTTP fetcher — tier 1 (requests) and tier 2 (Playwright) |
| `app/extractors.py` | 318 | Multi-strategy text extractor |
| `app/text_normalization.py` | 210 | Text cleaning + chunking |
| `app/source_tester.py` | 499 | Source diagnostic tool (test without DB write) |
| `app/source_discovery.py` | exists | Deep capability discovery (6-layer) |
| `app/pipeline.py` | 429 | Full monitoring pipeline |
| `app/proof.py` | 62 | Evidence block builder |
| `app/source_runs.py` | ~300 | Run record + snapshot writer |
| `sources.json` | 150 entries | Source registry |

---

## Current Fetch Architecture

### Tier 1 — requests (fast path)

`scraper.py:_fetch_via_requests()`:
- Standard HTTP GET with browser-like headers
- Checks `is_low_content_html()` threshold: 500 chars visible text
- If low content → returns status `needs_js_render`
- Falls through to Playwright if triggered

### Tier 2 — Playwright (JS rendering)

`scraper.py:_fetch_via_playwright()`:
- Uses `networkidle` wait state, falls back to `domcontentloaded`
- Fixed 3-second sleep after page load (`asyncio.sleep(3)`)
- **No per-source `wait_for_selector`** — waits for network idle only
- **No per-source `content_selector`** — extracts full page body
- Returns raw HTML regardless of whether content area loaded

### Low-Content Detection

`is_low_content_html(html)`:
- Strips tags, checks visible text length
- Threshold: 500 chars
- **GAP:** DFSA nav shell returns 4,701 chars and passes this check. The shell is above 500 chars but is still navigation-only. No paragraph-density or nav-ratio check exists.

---

## Current Extraction Architecture

`extractors.py:extract_text(html)` runs four strategies in order of preference:

1. **BeautifulSoup** — removes nav/header/footer tags, extracts `<p>`, `<li>`, `<article>` text
2. **Trafilatura** (`trafilatura==2.0.0`) — semantic extraction library
3. **readability-lxml** (`readability-lxml==0.8.4.1`) — article extraction fallback
4. **Crawl4AI** — last-resort fallback (optional dependency)

Scoring formula: `score = len(text) + unique_paragraphs * 200 - duplicate_paragraphs * 100`

Best-scoring strategy wins. Result stored as `normalized.txt`.

**GAP:** The scoring does not penalize nav-shell content. Short navigation menu items have high unique-paragraph count (each nav item is "unique") and score above zero.

---

## Current Source Tester

`source_tester.py` already has:

| Function | Purpose |
|---|---|
| `validate_public_url(url)` | SSRF protection — blocks private IPs, localhost, non-http schemes |
| `test_source_url(url, deep=False)` | Full diagnostic without DB write, no AI, no Telegram |
| `_build_verdict(result)` | Maps metrics to `can_monitor` / `needs_adapter` / `cannot_monitor` |
| `append_source_to_json(source)` | Safely adds entry to sources.json |

Verdict thresholds in `_build_verdict()`:
- `can_monitor`: chars >= 500 and no error
- `needs_adapter`: chars 100-499 or JS-render flagged
- `cannot_monitor`: error, blocked, or chars < 100

**GAP:** `can_monitor` threshold of 500 chars would still pass DFSA nav shell (4,701 chars). No nav-shell detection in the verdict builder.

---

## Current Source Registry Format

`sources.json` entry (AE tier):
```json
{
  "name": "Dubai Financial Services Authority (DFSA)",
  "url": "https://www.dfsa.ae/rules-and-standards",
  "jurisdiction": "AE",
  "category": "financial_regulator",
  "enabled": true,
  "status": "active",
  "source_id": "AE-dubai-financial-services-authority-dfsa",
  "notes": "...",
  "tier": "1"
}
```

**GAP:** No per-source fetch config fields. Missing:
- `fetch_method` — override (requests / playwright / feed / pdf)
- `wait_for_selector` — CSS selector to wait for before Playwright captures HTML
- `content_selector` — CSS selector to extract content from (skip nav)
- `expected_min_length` — per-source minimum char count threshold
- `scraper_notes` — engineering notes about known issues

---

## Critical Bug: DFSA Hash Collision

Both DFSA sources produce **identical** content hash `3021317a497a76b0...`:

| source_id | URL | Hash | Chars | Status |
|---|---|---|---|---|
| AE-dubai-financial-services-authority-dfsa | dfsa.ae/rules-and-standards | `3021317a497a` | 4,701 | ⚠ REMEDIATION |
| AE-dfsa-notices | dfsa.ae/regulation/notices-public-registers | `3021317a497a` | 4,701 | ⚠ REMEDIATION |

**Root cause:** DFSA uses client-side rendering. Playwright captures the navigation shell ("About us Go Back Who we are The DFSA Governance...") before the content area renders. Both URLs share the same nav shell — hence identical hash.

**How it passes current checks:**
- Char count 4,701 > 500 threshold → not flagged as low content
- No nav-ratio or paragraph-depth check → passes `can_monitor` verdict
- Both sources pass all current quality gates → stored with `proof_quality: LIMITED`

**Fix required:**
1. Add nav-shell detector to extractor scoring
2. Add `wait_for_selector` per-source config to sources.json
3. Add `content_selector` to allow scraper to extract from specific DOM area
4. Update `_fetch_via_playwright()` to use per-source config when available

---

## Other Identified Gaps

| Gap | Impact | Source affected |
|---|---|---|
| No nav-ratio detection | Nav-only content passes quality gate | DFSA (critical), possibly others |
| No per-source wait_for_selector | JS SPAs scraped before content loads | DFSA, VARA homepage |
| No per-source content_selector | Full page body extracted including nav | DFSA |
| UAE FIU too shallow (2,026c) | Homepage not regulatory content | AE-uae-financial-intelligence-unit-uaefiu |
| CBUAE rating-counter noise | 69 false CHANGED chunks per run | AE-cbuae-regulations |
| No custom source management API | Cannot add sources without editing JSON | All (product gap) |
| No source readiness UI | Dashboard shows no readiness status | All (product gap) |

---

## What Already Works Well

- **Two-tier fetcher** is functional. Requests fast path + Playwright fallback works for most sites.
- **Multi-strategy extraction** is solid. Trafilatura + readability-lxml already installed. Handles most HTML sites well.
- **PDF extraction** with pypdf works. Detected 20 PDFs on CBUAE, 6 on DIFC, 6 on MoF.
- **Deterministic hashing** is correct. SHA-256 of normalized text. Change detection reliable.
- **Evidence chain** is complete. raw.txt → normalized.txt → proof.json → diff.json artifacts.
- **source_tester.py** is a solid foundation. SSRF protection, verdict builder, JSON append already built.
- **run.py CLI** has `test-source <url>` and `add-source` commands.

---

## Conclusion

The scraper stack is production-capable for simple HTML sources. The three gaps that must be fixed immediately:

1. **Nav-shell detection** — paragraph density scoring to catch nav-only content
2. **Per-source Playwright config** — `wait_for_selector` and `content_selector` in sources.json
3. **Custom source API + UI** — so sources can be tested and added without JSON file edits

The new `source_intake.py` should extend `source_tester.py`, not replace it. The intake layer adds: nav-shell detection, per-source config application, readiness verdict with richer status vocabulary, and optional evidence writing.
