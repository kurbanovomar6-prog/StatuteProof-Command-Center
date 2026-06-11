# RegRadar — Source Discovery & Onboarding Architecture

## Overview

RegRadar uses a 6-layer parsing architecture to classify each regulatory source
into the best available monitoring mode.  The goal is not to parse every website
automatically — it is to give you an honest picture of what each source supports.

## Monitoring modes

| Mode          | Meaning                                                         |
|---------------|-----------------------------------------------------------------|
| `html`        | Static HTML extraction works — generic monitoring ready         |
| `js_html`     | JS-rendered HTML extraction works via Playwright                |
| `feed`        | RSS or Atom feed found — most reliable for structured updates   |
| `sitemap`     | Sitemap with usable links found — can track document inventory  |
| `documents`   | PDF/DOCX/XLSX documents found and extractable                   |
| `adapter`     | Site reachable but content needs a custom extraction adapter    |
| `unavailable` | Site cannot be reached (DNS error, timeout, SSL failure, block) |

## Verdicts

| Verdict           | Meaning                                               |
|-------------------|-------------------------------------------------------|
| `can_monitor`     | Source is ready for monitoring in a specific mode     |
| `needs_adapter`   | Site is reachable but extraction needs custom work    |
| `cannot_monitor`  | Site is unreachable — not a monitoring candidate      |

## Fast test-source (unchanged behavior)

```bash
python run.py test-source <url>
```

Runs Layers 1–2 only:
- Layer 1: Static HTML fetch (requests) + multi-extractor (BeautifulSoup, Trafilatura, readability)
- Layer 2: JS rendering via Playwright if Layer 1 is low-content

No feed/sitemap/document discovery. Fast (5–30 seconds).

## Deep test-source (6-layer discovery)

```bash
python run.py test-source <url> --deep
```

Runs all 6 layers:
- Layer 1: Static HTML extraction
- Layer 2: JS rendering (Playwright fallback)
- Layer 3: RSS/Atom feed discovery (8–11 candidate paths probed)
- Layer 3: Sitemap discovery (/sitemap.xml, /sitemap_index.xml, robots.txt)
- Layer 4: Document link detection (PDF, DOCX, XLSX, XLS)
- Layer 4: Sample document extraction (up to 3 documents, max 15 MB each)
- Layer 5: Adapter recommendation if no other mode works
- Layer 6: Structured report with suggested next step

Takes 60–120 seconds depending on site responsiveness.

## Deep test-mapped (batch discovery)

```bash
python run.py test-mapped --limit 10 --deep
```

Runs deep 6-layer discovery for mapped sources only.
Shows a table with: Source | Jur | Chars | Feed | Sitemap | Docs | Mode | Verdict.
Does not write to DB, does not enable sources, does not call AI.

## Document extraction (optional)

Install to enable document monitoring mode:

```bash
.venv/bin/python -m pip install pypdf python-docx openpyxl
```

Without these libraries, document links are still detected and counted,
but extraction returns empty string (graceful fallback, no crash).

| Library      | Handles        |
|--------------|----------------|
| `pypdf`      | PDF files      |
| `python-docx`| DOCX files     |
| `openpyxl`   | XLSX/XLS files |

## What RegRadar does NOT claim

- No universal parsing — some sites will always return `cannot_monitor`
- No CAPTCHA bypass
- No login/authentication bypass
- No SSL certificate disabling
- No private/internal URL access
- No AI calls during source testing or discovery
- No automatic source activation — all decisions require human confirmation

## Common failure reasons

| Failure                    | Cause                                    | Next step                        |
|----------------------------|------------------------------------------|----------------------------------|
| DNS resolution failed      | Domain not found or misspelled           | Find correct official URL        |
| SSL certificate error      | Expired/self-signed cert                 | Playwright fallback may help     |
| Connection timeout         | Server slow or blocking scrapers         | Try Playwright mode              |
| Low content (< 1000 chars) | Heavy JS rendering or bot protection     | Build custom adapter             |
| 403 / 401 response         | Access restricted                        | Source unavailable               |
| Empty document extraction  | Install pypdf/python-docx/openpyxl       | Install optional dependencies    |

## Suggested next steps by verdict

| Verdict          | Mode         | Suggested next step                              |
|------------------|--------------|--------------------------------------------------|
| `can_monitor`    | `html`       | Activate as HTML source via add-source           |
| `can_monitor`    | `js_html`    | Activate as JS-rendered source                   |
| `can_monitor`    | `feed`       | Activate as feed source                          |
| `can_monitor`    | `sitemap`    | Activate as sitemap source                       |
| `can_monitor`    | `documents`  | Activate as document source                      |
| `needs_adapter`  | `adapter`    | Build custom source adapter                      |
| `cannot_monitor` | `unavailable`| Find correct official URL or mark as unavailable |
