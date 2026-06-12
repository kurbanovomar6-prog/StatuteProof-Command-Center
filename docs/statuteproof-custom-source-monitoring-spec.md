# StatuteProof — Custom Source Monitoring Specification

**Version:** 1.0  
**Date:** 2026-06-12  
**Status:** Implementation-ready  
**Not legal advice. Internal spec only.**

---

## Overview

Custom source monitoring allows StatuteProof subscribers (Founding Pilot+) to add official regulatory URLs not included in the standard UAE source pack. This document specifies all aspects of the feature: allowed sources, form, flow, DB model, API, backend safety, legal disclaimers, quality handling.

The feature is available on: UAE VASP Pack (5 custom sources max), Compliance Consultant Pack (25 custom sources max).  
Not available on: Free Source Readiness Review, Founding Pilot.

---

## 1. Allowed and Blocked Source Types

### Allowed

The following source types are eligible for custom source monitoring:

| Type | Examples | Notes |
|------|---------|-------|
| Official regulatory websites (HTML) | New VARA sub-pages, SCA (when accessible), future CBUAE sub-pages | Must be publicly accessible without login |
| Official regulatory PDF documents | Specific CBUAE circular PDFs, DFSA guidance documents | Must have stable URL; PDF must be publicly downloadable |
| Official government portals | Ministry of Economy UAE sub-pages, UAE Federal Register pages | Must be publicly accessible |
| Official gazette pages | Official gazette listing pages | Must be publicly accessible |
| Official central bank / regulator announcement pages | CBUAE press releases, VARA news | Must have stable URL |
| Other official financial authority pages | ADGM FSRA specific sub-pages, DIFC specific content pages | Must be publicly accessible official domain |

### Not Allowed

The following source types are blocked from custom source monitoring:

| Type | Examples | Reason |
|------|---------|--------|
| Social media platforms | Twitter/X regulatory accounts, LinkedIn company pages, Telegram public channels | Content is dynamic, not archivable, ToS prevents crawling |
| News aggregators | Reuters, Bloomberg, Arab News, Gulf News | Not official primary sources; copyright concerns |
| Legal commentary and analysis | Law firm blogs, regulatory advisory newsletters | Not official sources; legal interpretation risk |
| Login-gated resources | Sources requiring username/password, subscriber portals | Cannot be monitored without credentials |
| Sources requiring CAPTCHA | Any source with bot detection that prevents access | Cannot be reliably monitored |
| Sources with robots.txt blocking | Any source whose robots.txt disallows crawling (unless explicit permission granted) | Legal and technical compliance |
| Internal/private IP addresses | Any URL resolving to 192.168.x.x, 10.x.x.x, 127.x.x.x, 172.16-31.x.x | SSRF risk |
| Localhost or metadata endpoints | http://localhost, http://169.254.169.254, http://metadata.google.internal | SSRF risk |
| Non-HTTPS URLs | Any http:// URL | Security requirement |
| File paths or local URLs | file://, ftp:// | Not supported |
| Non-regulatory commercial sites | Competitor products, commercial databases, non-official aggregators | Not primary official sources |

---

## 2. Add Source Form — All Fields

### Required Fields

| Field | Type | Validation | Notes |
|-------|------|-----------|-------|
| source_url | URL input | HTTPS only, valid format, not in blocklist, resolves within 10 seconds | Full URL with path |
| source_name | Text | Min 3, max 200 chars, no HTML | Internal display name |
| regulator_name | Text | Min 2, max 200 chars | Official name of the regulatory body |
| jurisdiction | Select | UAE (AE), Saudi Arabia (SA), Qatar (QA), Bahrain (BH), Other | Default: AE |
| category | Select | central_bank, financial_regulator, aml, legal_acts, legal_database, finance_ministry, company_registry, securities_regulator, other | Source classification |
| legal_ack | Checkbox | Must be true | "I confirm this is a publicly accessible official regulatory source..." |

### Optional Advanced Fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| monitoring_frequency | Select: daily / weekly | weekly | How often to check this source |
| extraction_type | Select: auto / html_only / pdf_only / playwright_fallback | auto | Override extraction method |
| alert_threshold | Select: any_change / medium_or_high / high_only | any_change | Minimum risk level to generate an alert |
| pdf_monitoring | Checkbox | false | Also monitor linked PDFs on this page |
| notes | Textarea | empty | Internal notes about this source (not shown in alerts) |

### Legal Acknowledgement Checkbox Copy

"I confirm that:
1. This URL is a publicly accessible official regulatory, government, or financial authority source
2. I have the right to monitor this source for compliance review purposes
3. This source is not login-gated, CAPTCHA-protected, or restricted from automated access
4. I understand that StatuteProof's monitoring of this source is subject to source availability, extraction quality, website changes, and access limitations
5. I understand that StatuteProof does not guarantee that all changes to this source will be detected
6. I understand that monitoring results for this source do not constitute legal advice

[Required — cannot submit without checking this box]"

---

## 3. Five-Step Add-Source Flow

### Step 1 — URL Entry

**Screen:** Single field — "Enter the official source URL"

**UI elements:**
- URL input (full-width, HTTPS placeholder)
- Help text: "Enter the full URL of an official regulatory source — for example, a regulator's publications page, circular listing, or official gazette. HTTPS only."
- "Supported source types" expandable section (shows allowed/blocked list summary)
- [Test URL] button → triggers Step 2

**Validation (client-side, instant):**
- URL format check (shows red border + error inline if invalid format)
- HTTPS check (shows "URL must start with https://")
- Basic blocked domain check (social media domains etc.)

**Validation (server-side, on Test URL click):**
- Not in blocklist
- Resolves to public IP (SSRF check)
- robots.txt check
- Not already added by this org

**Step 1 error states:**
- "This URL is not valid. Enter the full URL starting with https://"
- "Social media and news aggregator URLs are not permitted. Please enter an official regulatory source URL."
- "This URL is on the blocked domain list. Custom sources must be official regulatory or government URLs."
- "This URL is already being monitored in your account."
- "We could not reach this URL. It may be temporarily unavailable. Try again or check the URL."

---

### Step 2 — Preview Fetch (Test Fetch)

**Triggered by:** [Test URL] click in Step 1

**What happens:**
1. Server fetches the URL using the standard extraction pipeline (HTML → Playwright fallback → PDF detection)
2. Returns: HTTP status, extracted chars, extraction quality, extraction method used, sample text (first 500 chars), PDF links count if any
3. robots.txt check result shown

**UI elements:**
- Loading state: "Testing source — this may take 10-30 seconds..."
- Results card with:
  - URL and domain
  - HTTP status code (200 / 403 / timeout / etc.)
  - Extraction method used (BeautifulSoup HTML / Playwright / PDF)
  - Extracted characters: [N] characters
  - Quality badge: GOOD / MEDIUM / THIN / FAILED
  - PDF links discovered: [N] (if any)
  - Sample text: first 500 characters (truncated, monospace font, scrollable)
  - robots.txt status: Allowed / Disallowed / Not found (neutral)

**Quality outcome messages:**

| Quality | Message | User action |
|---------|---------|-------------|
| GOOD (≥2000 chars) | "Extraction successful. This source appears suitable for automated monitoring." | Proceed to Step 3 recommended |
| MEDIUM (800-1999 chars) | "Extraction returned moderate content. Monitoring may be less reliable for low-content pages. You can proceed with this quality level — limitations will be disclosed in alerts." | Proceed with caution |
| THIN (1-799 chars) | "Extraction returned very little content. This source may be JavaScript-heavy, PDF-primary, or access-restricted. Monitoring results may be unreliable. You can proceed but limitations will be visible in all alerts generated by this source." | Proceed with explicit warning |
| FAILED (0 chars) | "We could not extract any content from this URL. Common reasons: the page requires login, is completely JavaScript-rendered without fallback, is geo-restricted, or is blocking automated access. This source cannot be reliably monitored. You can still save it as DRAFT, but it will show FAILED status and generate no alerts until manually resolved." | Block proceed, offer save as DRAFT |

**Step 2 error states:**
- "Connection timed out. The source may be temporarily unavailable or geo-restricted."
- "This URL returned an error (HTTP [code]). The source cannot be monitored at this time."
- "robots.txt for this domain disallows crawling. We cannot monitor this source automatically. [Learn more]"
- "This URL resolved to a private IP address, which is not permitted."

---

### Step 3 — Quality Check Confirmation

**Purpose:** Show full quality details, get explicit confirmation before saving.

**UI elements:**
- Summary table:
  - Source URL
  - HTTP status
  - Extraction method
  - Extracted chars (raw)
  - Normalized chars (whitespace-stripped)
  - Extraction quality badge
  - PDF links discovered: [N]
  - PDF chars extracted: [N] (if any)
  - Sample text (first 500 chars in scrollable container)
  - Known limitations (if any) — e.g., "Playwright-required", "Low content — may miss changes"
- robots.txt status
- Warning banner (if THIN or FAILED quality): "This source has low extraction quality. Limitations will be disclosed in all alerts from this source."
- [Confirm and continue] button → Step 4
- [Back to URL] link

---

### Step 4 — Monitoring Settings

**Purpose:** Finalize source configuration before saving.

**UI elements:**
- Source name field (pre-filled with domain + page title if detectable, editable)
- Regulator name field (free text)
- Category dropdown
- Jurisdiction dropdown
- Monitoring frequency: Daily / Weekly (radio)
- Extraction type: Auto / HTML only / PDF only / Playwright fallback (dropdown, default: auto)
- Alert threshold: Any change / Medium or High risk only / High risk only (radio)
- Monitor linked PDFs: Yes / No checkbox
- Notes: optional text area
- Legal acknowledgement checkbox (re-displayed, required)
- Full disclaimer text (non-editable): "Custom source monitoring is provided for information purposes only. StatuteProof does not guarantee that all changes to custom sources will be detected..."

**Validation:**
- Source name required
- Regulator name required
- Legal ack must be checked (even if checked in Step 1 — re-confirm on save)

---

### Step 5 — Save and Activate

**What happens:**
1. CustomSource record created in DB
2. CustomSourceTest record created with test results
3. Status set: TEST_PASSED (GOOD/MEDIUM quality) or TEST_FAILED (THIN/FAILED quality)
4. User sees confirmation screen

**Confirmation screen (TEST_PASSED):**
- Green checkmark icon
- "Custom source added successfully"
- Source name, regulator, URL shown
- "First monitoring run will complete within 24 hours"
- "You will be notified if extraction quality drops"
- [View source in dashboard] button
- [Add another source] button

**Confirmation screen (TEST_FAILED / TEST quality THIN):**
- Amber warning icon
- "Custom source added with limitations"
- Source name, regulator, URL shown
- Status: NEEDS_REVIEW
- "Extraction quality was [THIN/FAILED] during testing. This source has been saved but will require attention before reliable monitoring is possible."
- "First run will attempt monitoring. If quality remains below threshold, you will be notified and the source status will be set to QUALITY_DROP."
- [View source in dashboard] button

---

## 4. Database Model

```sql
CREATE TABLE custom_sources (
  id                       INTEGER PRIMARY KEY AUTOINCREMENT,
  org_id                   INTEGER NOT NULL REFERENCES organizations(id),
  created_by_user_id       INTEGER NOT NULL REFERENCES users(id),
  source_name              TEXT NOT NULL,
  regulator_name           TEXT NOT NULL,
  official_url             TEXT NOT NULL,
  jurisdiction             TEXT NOT NULL DEFAULT 'AE',
  category                 TEXT NOT NULL DEFAULT 'other',
  monitoring_frequency     TEXT NOT NULL DEFAULT 'weekly',
  extraction_type          TEXT NOT NULL DEFAULT 'auto',
  alert_threshold          TEXT NOT NULL DEFAULT 'any_change',
  pdf_monitoring           INTEGER NOT NULL DEFAULT 0,
  status                   TEXT NOT NULL DEFAULT 'DRAFT',
  test_result_chars        INTEGER,
  test_result_quality      TEXT,
  test_result_method       TEXT,
  test_result_timestamp    DATETIME,
  test_sample_text         TEXT,
  robots_txt_status        TEXT,
  legal_ack_accepted       INTEGER NOT NULL DEFAULT 0,
  legal_ack_timestamp      DATETIME,
  legal_ack_ip             TEXT,
  notes                    TEXT,
  created_at               DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at               DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  paused_at                DATETIME,
  last_run_at              DATETIME,
  last_change_status       TEXT,
  archived_at              DATETIME,
  CONSTRAINT status_check CHECK (status IN (
    'DRAFT','TEST_PASSED','TEST_FAILED','ACTIVE','PAUSED','NEEDS_REVIEW','QUALITY_DROP','ARCHIVED'
  ))
);

CREATE INDEX idx_custom_sources_org ON custom_sources (org_id, status);
CREATE INDEX idx_custom_sources_url ON custom_sources (official_url);

CREATE TABLE custom_source_tests (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  org_id                INTEGER NOT NULL REFERENCES organizations(id),
  user_id               INTEGER NOT NULL REFERENCES users(id),
  test_url              TEXT NOT NULL,
  http_status           INTEGER,
  raw_chars             INTEGER,
  normalized_chars      INTEGER,
  extraction_quality    TEXT,
  extraction_method     TEXT,
  pdf_links_count       INTEGER,
  pdf_extracted_chars   INTEGER,
  sample_text           TEXT,
  robots_txt_status     TEXT,
  error                 TEXT,
  ssrf_check_result     TEXT,
  blocklist_check       TEXT,
  tested_at             DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_custom_source_tests_org ON custom_source_tests (org_id, tested_at);
```

---

## 5. API Endpoints

### POST /api/v1/custom-sources/test

**Auth:** Admin or Owner  
**Rate limit:** 3 test-fetch attempts per organization per 10 minutes  
**Purpose:** Test-fetch a URL without saving to DB. Returns quality result.

**Request body:**
```json
{ "url": "https://example-regulator.gov.ae/publications/" }
```

**Validation (server-side before any network request):**
1. URL is HTTPS
2. URL hostname resolves to a public IP (block private ranges: 10/8, 172.16/12, 192.168/16, 127/8, 169.254/16, ::1)
3. URL hostname not in blocked domain list (twitter.com, x.com, linkedin.com, instagram.com, bloomberg.com, reuters.com, etc.)
4. URL not already in org's custom sources (check by normalized URL)
5. robots.txt check (fetch and parse, warn if crawling disallowed — do not hard block, show warning)

**Response:**
```json
{
  "url": "https://example-regulator.gov.ae/publications/",
  "http_status": 200,
  "extraction_method": "playwright",
  "raw_chars": 4821,
  "normalized_chars": 4200,
  "extraction_quality": "GOOD",
  "pdf_links_count": 3,
  "pdf_extracted_chars": 28400,
  "sample_text": "Publications — Example Regulator...",
  "robots_txt_status": "allowed",
  "ssrf_safe": true,
  "in_blocklist": false,
  "warning": null
}
```

**Error response (SSRF block):**
```json
{
  "error": "SSRF_BLOCKED",
  "message": "This URL resolves to a private or reserved IP address and cannot be tested."
}
```

---

### POST /api/v1/custom-sources

**Auth:** Admin or Owner  
**Purpose:** Save a custom source after test-fetch approval.

**Request body:**
```json
{
  "source_name": "Example Regulator — Publications",
  "regulator_name": "Example Regulatory Authority",
  "official_url": "https://example-regulator.gov.ae/publications/",
  "jurisdiction": "AE",
  "category": "financial_regulator",
  "monitoring_frequency": "weekly",
  "extraction_type": "auto",
  "alert_threshold": "any_change",
  "pdf_monitoring": false,
  "notes": "Main publications page for custom monitoring",
  "legal_ack": true,
  "test_result": {
    "extraction_quality": "GOOD",
    "raw_chars": 4821,
    "extraction_method": "playwright",
    "tested_at": "2026-06-12T09:00:00Z"
  }
}
```

**Validation:**
- legal_ack must be true (returns 400 if false)
- org has not exceeded max_custom_sources limit
- URL passes SSRF check
- Source name and regulator name present
- Category is valid enum

**Returns:** 201 with source_id and status

---

### GET /api/v1/custom-sources

**Auth:** Any authenticated user  
**Returns:** List of custom sources for org with latest run status

---

### GET /api/v1/custom-sources/:id

**Auth:** Any authenticated user  
**Returns:** Full custom source detail including test history and run history

---

### PATCH /api/v1/custom-sources/:id

**Auth:** Admin or Owner  
**Allowed fields:** source_name, regulator_name, category, monitoring_frequency, extraction_type, alert_threshold, pdf_monitoring, notes  
**Not allowed to patch:** official_url (changing URL requires new test), legal_ack (immutable), status (use pause/resume/archive endpoints)

---

### POST /api/v1/custom-sources/:id/pause

**Auth:** Admin or Owner  
**Action:** Sets status = PAUSED, paused_at = now

---

### POST /api/v1/custom-sources/:id/resume

**Auth:** Admin or Owner  
**Action:** Sets status = ACTIVE (or NEEDS_REVIEW if last quality was THIN/FAILED)

---

### DELETE /api/v1/custom-sources/:id

**Auth:** Admin or Owner  
**Action:** Soft delete — sets status = ARCHIVED, archived_at = now. Evidence records are preserved.

---

## 6. Backend Safety Checks

### SSRF Prevention (Critical)

Every test-fetch must run through SSRF prevention before any network call:

```python
import ipaddress
import socket

PRIVATE_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # link-local / AWS metadata
    ipaddress.ip_network("100.64.0.0/10"),   # shared address space
    ipaddress.ip_network("::1/128"),          # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),         # IPv6 private
]

BLOCKED_METADATA_HOSTS = [
    "169.254.169.254",       # AWS/GCP/Azure metadata
    "metadata.google.internal",
    "metadata.internal",
]

def is_safe_url(url: str) -> tuple[bool, str]:
    """Returns (is_safe, reason)"""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    
    if parsed.scheme != "https":
        return False, "URL must use HTTPS"
    
    hostname = parsed.hostname
    if hostname in BLOCKED_METADATA_HOSTS:
        return False, "Metadata endpoint blocked"
    
    try:
        ip_str = socket.gethostbyname(hostname)
        ip = ipaddress.ip_address(ip_str)
    except Exception:
        return False, "Could not resolve hostname"
    
    for private_range in PRIVATE_RANGES:
        if ip in private_range:
            return False, f"Private IP range blocked: {ip_str}"
    
    return True, "ok"
```

### Domain Blocklist Check

```python
BLOCKED_DOMAINS = {
    # Social media
    "twitter.com", "x.com", "linkedin.com", "instagram.com",
    "facebook.com", "tiktok.com", "youtube.com", "telegram.org",
    "t.me", "discord.com", "discord.gg", "reddit.com",
    # News aggregators  
    "reuters.com", "bloomberg.com", "ft.com", "wsj.com",
    "theguardian.com", "bbc.com", "aljazeera.com", "arabnews.com",
    "gulfnews.com", "thenationalnews.com", "khaleejimes.com",
    # Non-official aggregators
    "lawfare.com", "complianceweek.com", "lexology.com",
    "moneycontrol.com", "investing.com", "tradingeconomics.com",
    # Known problematic
    "bit.ly", "tinyurl.com", "t.co",  # URL shorteners
}

def is_allowed_domain(url: str) -> tuple[bool, str]:
    from urllib.parse import urlparse
    hostname = urlparse(url).hostname or ""
    for blocked in BLOCKED_DOMAINS:
        if hostname == blocked or hostname.endswith("." + blocked):
            return False, f"Domain {blocked} is not permitted for custom source monitoring"
    return True, "ok"
```

### Rate Limiting

- Custom source test: 3 per org per 10 minutes (enforced via Redis or in-memory counter keyed by org_id)
- Custom source create: 10 per org per day

### Extraction Safety

- Playwright usage: only if HTML extraction returns < 500 chars (prevents Playwright abuse)
- Timeout: 30 second maximum per test-fetch
- Max response size: 5MB (prevent memory exhaustion)
- PDF download size cap: 10MB per PDF

---

## 7. Custom Source Statuses

| Status | Meaning | User-visible description |
|--------|---------|--------------------------|
| DRAFT | Added but first run not yet complete | "Setting up — first run scheduled" |
| TEST_PASSED | Test fetch returned GOOD or MEDIUM quality | "Test passed — monitoring scheduled" |
| TEST_FAILED | Test fetch returned THIN or FAILED quality | "Test failed — see quality details" |
| ACTIVE | Running successfully, quality acceptable | "Active — monitoring" |
| PAUSED | Manually paused by admin/owner | "Paused — not monitoring" |
| NEEDS_REVIEW | Quality dropped or errors after a period of success | "Needs review — quality issue detected" |
| QUALITY_DROP | Extraction quality below threshold | "Quality drop — changes may be missed" |
| ARCHIVED | Removed from active monitoring | "Archived" |

### Quality Drop Handling

When a source run returns QUALITY_DROP:

1. Source status updated to QUALITY_DROP
2. Email notification sent to org admins: "Source monitoring issue — [Source Name]"
3. Source continues to run on schedule (does not auto-pause)
4. Any change events generated while in QUALITY_DROP state include a visible quality warning in the alert
5. User must manually resolve: re-test, update extraction type, pause, or contact support
6. If 3 consecutive runs are QUALITY_DROP, status moves to NEEDS_REVIEW and stronger notification sent

---

## 8. Legal Disclaimers

### In-App Disclaimer (Shown on Custom Source Detail Pages and Alerts)

"Custom source monitoring is provided for information purposes only. StatuteProof does not guarantee that all changes to this source will be detected. Monitoring may be affected by website changes, access restrictions, extraction limitations, and scheduling delays. This source is not independently verified as an official regulatory source by StatuteProof. Verify all changes against the official source directly before acting. Not legal advice."

### On-Alert Disclaimer (Added to Every Alert from a Custom Source)

"Note: This alert was generated from a custom source [Source Name]. Custom sources are user-configured and are not part of StatuteProof's validated official UAE source pack. Verify this alert against the official source directly. Not legal advice."

### Export Disclaimer (Any Brief or Report Including Custom Source Alerts)

"This brief includes alerts from custom sources configured by your organization. Custom sources are not independently validated by StatuteProof. StatuteProof does not guarantee the completeness or accuracy of monitoring for custom sources. Not legal advice."

---

## 9. Test-Fetch Preview Design

### Loading State

```
Testing source...

URL: https://example-regulator.gov.ae/publications/
[Progress bar — animated]

Checking URL safety...     ✓
Checking robots.txt...     ✓  
Fetching content...        [spinner]
```

### Success State (GOOD quality)

```
Source Test Results

URL: https://example-regulator.gov.ae/publications/
HTTP status: 200 OK
Extraction method: Playwright (JavaScript-rendered page)
Extracted: 4,821 characters (normalized: 4,200)
PDFs discovered: 3 (combined: 28,400 characters)
robots.txt: Allowed
Quality: [GOOD badge - green]

Sample content:
─────────────────────────────────────────────────
Publications
VARA Enforcement Notice — June 2026
VARA Market Watch Bulletin — June 2026
VARA Rulebook Update — May 2026
...
─────────────────────────────────────────────────

✓ This source appears suitable for automated monitoring.

[Proceed to settings →]   [Test different URL]
```

### Warning State (THIN quality)

```
Source Test Results

URL: https://example-regulator.gov.ae/circular-list/
HTTP status: 200 OK
Extraction method: BeautifulSoup HTML
Extracted: 623 characters (normalized: 580)
PDFs discovered: 0
robots.txt: Allowed
Quality: [THIN badge - amber]

⚠ Low extraction quality. This page may be JavaScript-heavy or have 
limited text content. Monitoring may miss some changes. 
Limitations will be disclosed in any alerts from this source.

Sample content:
─────────────────────────────────────────────────
[Navigation — Home / Publications / Circulars]
Page loading...
─────────────────────────────────────────────────

[Proceed with caution →]   [Try Playwright extraction]   [Test different URL]
```

### Failed State (FAILED quality)

```
Source Test Results

URL: https://restricted-source.example.com/
HTTP status: 403 Forbidden
Extraction method: Attempted HTML + Playwright
Extracted: 0 characters
robots.txt: Unknown (could not fetch)
Quality: [FAILED badge - red]

✗ We could not extract content from this URL.

Possible reasons:
• The page requires login or authentication
• Access is restricted by IP (geo-block)
• The server blocks automated access
• CAPTCHA is required

This source cannot be reliably monitored at this time.

[Save as DRAFT anyway]   [Test different URL]
```

---

*Not legal advice. Internal implementation specification.*
