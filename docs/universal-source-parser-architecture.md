# Universal Source Parser — Architecture

**Date:** 2026-06-13  
**Status:** Approved for implementation  
**Implements:** Steps 3–8 of Universal Source Intake task

---

## Design Principles

1. **Extend, don't replace.** `source_intake.py` wraps `source_tester.py` and `scraper.py`. No functionality is duplicated or removed.
2. **Smallest safe change.** The DFSA fix is one field in sources.json + one guard in `_fetch_via_playwright()`. No scraper rewrite.
3. **Per-source config drives behavior.** New optional fields in sources.json give the scraper instructions for specific sites. If fields are absent, current behavior is unchanged.
4. **Richer status vocabulary.** The intake layer adds a `readiness_status` enum that maps to UI states in the dashboard.
5. **Evidence-optional.** The intake layer can run in dry-run (no DB writes, no evidence) or intake mode (writes evidence artifact).

---

## New Fields in sources.json

Optional fields added to source entries (all backward-compatible — absent = use defaults):

```json
{
  "wait_for_selector": "main",
  "content_selector": "main",
  "expected_min_length": 5000,
  "fetch_method": "playwright"
}
```

| Field | Type | Purpose |
|---|---|---|
| `wait_for_selector` | string | Playwright waits for this CSS selector before capturing HTML |
| `content_selector` | string | BeautifulSoup extracts from this selector instead of full body |
| `expected_min_length` | int | Per-source minimum char threshold (overrides global 500) |
| `fetch_method` | string | Force a specific fetch method: `requests`, `playwright`, `feed`, `pdf` |

---

## source_intake.py — Module Design

### Status Constants

```python
class SourceIntakeStatus:
    CONFIRMED_ACCESSIBLE  = "CONFIRMED_ACCESSIBLE"   # Good extraction, unique hash
    JS_RENDERING_NEEDED   = "JS_RENDERING_NEEDED"    # Low chars, JS SPA suspected
    PDF_EXTRACTION_NEEDED = "PDF_EXTRACTION_NEEDED"  # HTML thin, PDFs detected
    NAV_SHELL_ONLY        = "NAV_SHELL_ONLY"         # Hash collision or nav-density triggered
    QUALITY_DROP          = "QUALITY_DROP"           # Chars fell below expected_min_length
    NEEDS_SELECTOR_REVIEW = "NEEDS_SELECTOR_REVIEW"  # Low content despite Playwright
    UNSUPPORTED           = "UNSUPPORTED"            # Cannot monitor (error/blocked)
    BLOCKED               = "BLOCKED"                # HTTP 403/429/SSL error
```

### Nav-Shell Detection

`is_nav_shell_only(text, threshold=0.65)`:
- Split text into lines
- Count lines < 8 words long ("About us", "Rules", "Governance")
- Count lines >= 8 words long (substantive sentences)
- If short-line ratio >= threshold AND total unique chars < 10,000 → nav shell
- Also triggers if content hash matches another enabled source (collision check)

### SourceIntakeResult

```python
{
    "source_id": str,
    "url": str,
    "status": SourceIntakeStatus,           # primary verdict
    "chars_raw": int,
    "chars_normalized": int,
    "pdf_chars": int,
    "nav_shell_detected": bool,
    "hash_collision": bool,                 # True if same hash as another source
    "collision_source_id": str | None,
    "quality": str,                         # GOOD / LIMITED / POOR
    "evidence_written": bool,
    "errors": list[str],
    "notes": str,
}
```

### Main Function

```python
def run_source_intake(
    source: dict,
    all_sources: list[dict] | None = None,
    write_evidence: bool = False,
) -> SourceIntakeResult:
```

Flow:
1. `validate_public_url(source["url"])` — SSRF check
2. Read per-source config fields from source dict
3. Call `scraper.fetch(url, fetch_method=..., wait_for_selector=..., content_selector=...)`
4. Call `extractors.extract_text(html)`
5. Run `is_nav_shell_only(text)`
6. If `all_sources` provided: check hash against other enabled sources
7. Map metrics → `SourceIntakeStatus`
8. If `write_evidence`: write raw.txt, normalized.txt, proof.json
9. Return `SourceIntakeResult`

---

## scraper.py Changes (Minimal)

Add per-source Playwright config support in `_fetch_via_playwright()`:

```python
async def _fetch_page(url, wait_for_selector=None, content_selector=None):
    ...
    if wait_for_selector:
        await page.wait_for_selector(wait_for_selector, timeout=10000)
    else:
        await page.wait_for_load_state("networkidle")
    
    if content_selector:
        element = await page.query_selector(content_selector)
        html = await element.inner_html() if element else await page.content()
    else:
        html = await page.content()
```

This is a surgical change — existing calls with no kwargs are unchanged.

---

## sources.json DFSA Fix

Add to `AE-dubai-financial-services-authority-dfsa`:
```json
{
  "wait_for_selector": "main",
  "content_selector": "main",
  "expected_min_length": 3000,
  "fetch_method": "playwright"
}
```

Add to `AE-dfsa-notices`:
```json
{
  "wait_for_selector": "main",
  "content_selector": "main", 
  "expected_min_length": 3000,
  "fetch_method": "playwright"
}
```

After fix: re-run extraction and verify the two sources produce **different** hashes.

---

## API Layer — New Endpoints

All in `app/api.py`:

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/custom-sources/test` | POST | Test a URL without saving: runs intake, returns result |
| `/api/custom-sources` | GET | List all custom (user-added) sources |
| `/api/custom-sources` | POST | Save a tested custom source to sources.json |
| `/api/custom-sources/:id` | DELETE | Remove a custom source |
| `/api/sources/readiness` | GET | Readiness summary for all enabled sources |

`POST /api/custom-sources/test` payload:
```json
{ "url": "https://...", "name": "optional label" }
```

`POST /api/custom-sources/test` response:
```json
{
  "status": "CONFIRMED_ACCESSIBLE",
  "chars": 12400,
  "nav_shell_detected": false,
  "hash_collision": false,
  "quality": "GOOD",
  "can_activate": true,
  "message": "Source accessible and extracting well."
}
```

---

## Dashboard — SourcesPage.jsx Changes

Replace mock-data Sources page with three sections:

1. **Built-in Sources** — read from `/api/sources/status`, show readiness status badge per source
2. **Custom Sources** — read from `/api/custom-sources`, show user-added sources with same badges
3. **Add Source wizard** — URL input → test → result card → activate button

Status badge vocabulary:
- `CONFIRMED_ACCESSIBLE` → green "Ready"
- `JS_RENDERING_NEEDED` → amber "JS rendering"
- `NAV_SHELL_ONLY` → red "Remediation needed"
- `QUALITY_DROP` → amber "Quality check"
- `UNSUPPORTED` → gray "Not supported"
- `BLOCKED` → red "Blocked"

---

## Source Readiness Summary API

`GET /api/sources/readiness` returns:
```json
{
  "total_enabled": 13,
  "confirmed_ready": 10,
  "remediation_needed": 3,
  "breakdown": [
    { "source_id": "AE-...", "status": "CONFIRMED_ACCESSIBLE", "chars": 12677, "last_run": "2026-06-12" }
  ]
}
```

This drives the dashboard summary card and the PlanBanner "source pack staged for validation" message.

---

## Skill + Runbook

`docs/custom-source-parser-runbook.md` covers:
- How to test a new source URL
- How to interpret intake results
- How to add `wait_for_selector` for JS SPAs
- How to resolve hash collisions
- How to escalate to needs_adapter

Skill at `skills/custom-source-parser/SKILL.md` (in skills/, not .claude/agents/) provides the agent-council-style prompt for running a parser intake review.

---

## Test Plan

`product/regradar/tests/test_source_intake.py`:

1. `test_valid_url_passes_ssrf_check` — good URL clears validate_public_url
2. `test_private_ip_blocked` — 192.168.x.x rejected
3. `test_nav_shell_detected_on_short_lines` — synthesized nav-only text triggers NAV_SHELL_ONLY
4. `test_good_content_passes_nav_check` — substantive paragraphs return CONFIRMED_ACCESSIBLE
5. `test_hash_collision_detected` — two sources with same hash → hash_collision=True
6. `test_low_char_source_status` — 300 chars → JS_RENDERING_NEEDED
7. `test_per_source_expected_min_length` — 4,000 chars vs expected_min_length=5000 → QUALITY_DROP
8. `test_intake_result_fields` — result dict has all required keys
9. `test_intake_dry_run_no_evidence_written` — write_evidence=False → evidence_written=False
10. `test_intake_verdict_mapping` — comprehensive status mapping check

All tests use mocked HTTP responses — no live network calls in test suite.
