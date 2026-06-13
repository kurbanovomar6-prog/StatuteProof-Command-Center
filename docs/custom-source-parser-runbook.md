# Custom Source Parser — Runbook

**Date:** 2026-06-13  
**Module:** product/regradar/app/source_intake.py  
**Audience:** Engineers and compliance operators onboarding new regulatory sources

---

## Overview

The source intake layer (`source_intake.py`) is the quality gate for adding new sources to StatuteProof. It runs before a source is activated for live monitoring. It produces a `SourceIntakeStatus` verdict that maps directly to dashboard status badges.

---

## Step 1 — Test a new source URL

**CLI:**
```bash
cd product/regradar
python run.py test-source https://www.dfsa.ae/regulation/notices-public-registers
```

**API (authenticated):**
```
POST /api/custom-sources/test
{ "url": "https://...", "name": "DFSA Notices" }
```

**Intake function (Python):**
```python
from app.source_intake import run_source_intake

source = {"url": "https://www.dfsa.ae/regulation/notices-public-registers", "source_id": "AE-dfsa-notices"}
result = run_source_intake(source, all_sources=all_sources_list)
print(result["status"])   # e.g. CONFIRMED_ACCESSIBLE
print(result["chars_normalized"])
print(result["nav_shell_detected"])
```

---

## Step 2 — Interpret the result

| Status | Meaning | Action |
|---|---|---|
| `CONFIRMED_ACCESSIBLE` | Good extraction, unique content, above threshold | Activate |
| `JS_RENDERING_NEEDED` | Too few chars — site needs JS rendering | Add `"fetch_method": "playwright"` to sources.json |
| `PDF_EXTRACTION_NEEDED` | HTML thin but PDFs detected | Ensure PDF extraction is enabled; verify `pypdf` processes the docs |
| `NAV_SHELL_ONLY` | Nav-shell detected or hash collision with another source | Add `wait_for_selector` and `content_selector` to sources.json |
| `QUALITY_DROP` | Chars below `expected_min_length` for this source | Check if site changed; update `expected_min_length` or fix URL |
| `NEEDS_SELECTOR_REVIEW` | Low char count despite Playwright — no selector configured | Add `content_selector` to point at the content area |
| `UNSUPPORTED` | Cannot monitor (JS auth wall, file protocol, etc.) | Do not activate; document in notes |
| `BLOCKED` | HTTP error, SSRF rejection, or private IP | Check URL; do not activate |

---

## Step 3 — Fix a NAV_SHELL_ONLY result

This is the DFSA-class problem: Playwright captures the site's navigation shell before content loads.

**Signs:**
- `nav_shell_detected: true` in intake result
- Extracted text is short navigation items ("About us", "Rules", "Governance")
- `hash_collision: true` — same content as another source

**Fix in sources.json:**
```json
{
  "source_id": "AE-dfsa-notices",
  "url": "https://www.dfsa.ae/regulation/notices-public-registers",
  "fetch_method": "playwright",
  "wait_for_selector": "main",
  "content_selector": "main",
  "expected_min_length": 3000
}
```

`wait_for_selector`: Playwright waits for this CSS selector to appear before capturing. Use browser DevTools to find the element that contains the regulatory content (often `main`, `.content`, `#content`, `[data-content]`).

`content_selector`: After the page loads, only extract HTML from this element. Keeps nav/header/footer out of the snapshot.

**After adding config:** re-run intake and confirm `status: CONFIRMED_ACCESSIBLE` and a unique hash.

---

## Step 4 — Fix a JS_RENDERING_NEEDED result

The site uses client-side rendering but Playwright hasn't been forced. Add:
```json
"fetch_method": "playwright"
```

If chars are still low after Playwright, add `wait_for_selector` to wait for the data to load.

---

## Step 5 — Resolve a hash collision

Two sources with identical hashes means they extract the same content. Steps:
1. Check both URLs in a browser — do they render different content?
2. If yes: add `wait_for_selector` + `content_selector` per Step 3
3. If no: one URL is redundant. Disable the one with lower signal value.
4. Re-run intake. Confirm different hashes.
5. Update `docs/current-uae-source-readiness-validation-report.md`.

---

## Step 6 — Activate a custom source

After a `CONFIRMED_ACCESSIBLE` result, use the API or CLI to add to sources.json:

**API:**
```
POST /api/custom-sources
{
  "url": "https://...",
  "name": "Source Name",
  "jurisdiction": "AE",
  "category": "financial_regulator"
}
```

**CLI:**
```bash
python run.py add-source
```

The source is added with `"status": "pending_validation"` and `"custom": true`. After the first full pipeline run, it will be promoted to `"status": "active"` if extraction passes.

---

## Step 7 — Escalate to needs_adapter

If a source consistently returns `UNSUPPORTED` or very low content despite Playwright + selectors:
- The site may require login, CAPTCHA solving, or API key
- Document in `sources.json` notes: `"status": "adapter_required"`
- Do not count toward any source readiness claim
- Log for future custom adapter work

---

## Nav-Shell Detection — Technical Details

`is_nav_shell_only(text)` in `source_intake.py`:
- Splits extracted text into lines
- Counts lines with fewer than 8 words (short navigation items)
- If ≥ 65% of lines are short AND total chars < 10,000 → `NAV_SHELL_ONLY`
- False positive avoidance: large pages (≥ 10,000 chars) skip the check

---

## Evidence Writing

Pass `write_evidence=True` to store a snapshot for audit purposes:
```python
result = run_source_intake(source, write_evidence=True)
# → writes raw.txt, normalized.txt, proof.json to data/source_snapshots/
```

Only writes evidence when status is `CONFIRMED_ACCESSIBLE`. Skipped for blocked/nav-shell sources.
