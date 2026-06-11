# RegRadar Source Onboarding Rules

## Purpose

This document defines the rules for adding a new regulatory source to RegRadar — whether done manually by the team or proposed by a user via the `discover-source` CLI or the "Add Your Own Source" web feature.

---

## 1. Source Quality Gates

Every source must pass all gates before being set to `active`:

| Gate | Rule |
|------|------|
| **Extraction** | ≥ 1,000 extracted chars (BeautifulSoup or Playwright) |
| **Authority** | Must be a primary regulatory, legislative, or supervisory authority |
| **Uniqueness** | URL must not duplicate an existing source in the same jurisdiction + category |
| **Accessibility** | Must respond with HTTP 200 or 301/302 (not behind auth/VPN) |
| **Language** | Must have a readable version (native or `/en` fallback) |

Sources that fail extraction but are critical authorities should be added as `adapter_required`, not skipped.

---

## 2. Status Assignment Rules

| Condition | Assigned Status |
|-----------|----------------|
| ≥ 1,000c, reachable, no Playwright required | `active` |
| ≥ 1,000c, reachable, requires Playwright | `active` (note Playwright in JSON) |
| 500–999c, reachable | `limited` |
| < 500c, reachable | `mapped` (track, check later) |
| IP-blocked / geo-restricted / auth-required | `disabled_external_access` |
| Navigation-only SPA (no extractable content) | `disabled_navigation_only` |
| Requires custom adapter to extract | `adapter_required` |

**Never** set a source to `active` if it extracts < 500c. Use `limited` or lower.

---

## 3. Category Assignment

Use the canonical category key from `app/coverage.py`:

| Key | Description |
|-----|-------------|
| `central_bank` | Central bank or monetary authority |
| `financial_regulator` | Securities, banking, insurance regulator |
| `aml` | Anti-money laundering / CFT authority |
| `tax` | Tax administration |
| `legal_acts` | National statutes / legislation portal |
| `data_protection` | Data protection / privacy authority |
| `company_regulator` | Business / company registry or regulator |
| `cyber` | Cybersecurity agency |
| `competition` | Competition and consumer authority |

If a source covers multiple categories, assign the primary one. Add a second source entry for the secondary category only if extraction at the secondary URL yields ≥ 1,000c independently.

---

## 4. URL Selection Rules

1. **Prefer deep regulatory pages** over homepages (e.g. `/regulation` vs `/`).
2. **Never use a 404 URL** — probe alternatives. Document why you chose the fallback.
3. **Use `/Browse/Act/Current`-style paths** for SPA portals if the root is a search interface.
4. **If a dedicated category page exists** (e.g. `/aml`, `/publications`), prefer it over a generic landing page.
5. **Test both the root and up to 3 candidate paths** using `python run.py test-source <url>`.
6. **Record tested-but-rejected URLs** in the source pack report.

---

## 5. Jurisdiction Coverage Targets

Each jurisdiction should have **at least one source per tier**:

| Tier | Categories | Minimum |
|------|-----------|---------|
| **Tier 1 (Core)** | central_bank OR financial_regulator, aml | 2 |
| **Tier 2 (Legal)** | legal_acts, tax | 1 |
| **Tier 3 (Extended)** | data_protection, company_regulator, cyber, competition | 0+ |

A jurisdiction with only Tier 1 sources is `usable`. Tier 1 + Tier 2 is `strong` (if extraction is good).

---

## 6. New Country Onboarding Procedure

### Step 1 — Identify authorities

Research the following for the target jurisdiction:
- Central bank / financial supervisory authority
- AML/CFT regulator (may be same as central bank)
- Tax administration
- National legislative database (laws, acts)
- Data protection authority (if exists)
- Company / business registry
- Cybersecurity agency (if exists)
- Competition authority (if exists)

### Step 2 — Test each URL

```bash
python3 run.py test-source <url>
python3 run.py test-source <url> --deep   # if Tier 1 returns < 1,000c
python3 run.py discover-source <url> --jurisdiction CODE --category CATEGORY --json
```

Record all tested URLs, char counts, and decisions.

### Step 3 — Add to sources.json

```json
{
  "name": "Authority Name — Section",
  "url": "https://authority.gov.xx/path",
  "jurisdiction": "XX",
  "category": "category_key",
  "status": "active",
  "extractor": "beautifulsoup"
}
```

Set `"extractor": "playwright"` only if Playwright is required for ≥ 1,000c extraction.

### Step 4 — Register jurisdiction and new categories

In `app/coverage.py`:
- Add `"XX": "Country Name"` to `_JURISDICTION_NAME`
- Add `"XX": "Region Name"` to `_REGION`
- Add any new category keys to `_CATEGORY_LABEL`

### Step 5 — Run all reports

```bash
python3 run.py health
python3 run.py source-audit --json
python3 run.py coverage --json
python3 run.py coverage --html
```

Verify: FAIL = 0, no regressions in existing jurisdictions.

### Step 6 — Write source pack report

Save to `reports/{jur_lower}_source_pack_{YYYY-MM-DD}.md` documenting:
- All sources added with char counts
- All URLs tested but not added (and why)
- New category labels added
- Coverage score before/after
- Health check result

### Step 7 — Commit

```bash
git add sources.json app/coverage.py reports/
git commit -m "feat(regradar): add {Country} source pack"
```

---

## 7. Adapter Queue Rules

A source should be added to the adapter queue when:
- It is a primary authority (Tier 1) but returns < 500c due to JS rendering or IP restrictions
- Manual inspection confirms the content is valuable (regulatory updates, notices, guidelines)
- No BeautifulSoup or Playwright path reaches ≥ 500c

Adapter queue entries in `sources.json` use status `adapter_required`. They **count in the coverage denominator** and reduce the coverage score until resolved.

---

## 8. Restricted Source Rules

Sources that are geo-blocked, require authentication, or are behind VPN use:
- `disabled_external_access` — for sources blocked by the target site itself
- `disabled_navigation_only` — for pages that are JS SPAs with no extractable text path

These are stored in `_EXCLUDED_FROM_SCORE` in `app/coverage.py` and **excluded from the coverage score denominator** so they don't penalise jurisdictions for infrastructure they cannot control.

---

## 9. discover-source CLI Reference

```bash
python3 run.py discover-source <url>
python3 run.py discover-source <url> --json
python3 run.py discover-source <url> --jurisdiction CODE --category NAME
python3 run.py discover-source <url> --jurisdiction CODE --category NAME --json
```

The engine runs 4 stages:
1. Core extraction (static HTML → Playwright → feeds → sitemap → documents)
2. Deep URL path probing (20 regulatory path variants on the same domain)
3. Language version discovery (tests `/en`, `/ru`, `/ar`, `/tr`, `/az`, `/ka`, `/kk`, `/hy`, `/uz`)
4. API endpoint hints (15 public API paths for SPA detection)

Output includes: quality score (0–100), recommended status, best monitoring URL, tested methods, limitations, and next steps.
