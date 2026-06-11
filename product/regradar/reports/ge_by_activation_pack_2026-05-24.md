# Georgia + Belarus Activation Pack — 2026-05-24

## Summary

**Georgia:** 0 enabled → 4 enabled, score **80 (usable) → 89 (strong)**
**Belarus:** 0 enabled → 3 enabled, score **75 (usable) → 86 (strong)**
**Overall:** 79 → **81 (usable)**

---

## Georgia (GE) — Sources Enabled

| Action | Name | URL | Category | Chars | Quality | Enabled |
|--------|------|-----|----------|-------|---------|---------|
| ENABLED | National Bank of Georgia | https://www.nbg.gov.ge/ | central_bank | 1,378 | good | true |
| ENABLED | Georgian Revenue Service | https://rs.ge/ | tax | 10,062 | good | true |
| ENABLED | Legislative Herald of Georgia (Matsne) | https://matsne.gov.ge/ | legal_acts | 32,681 | good | true |
| ENABLED | Ministry of Finance of Georgia | https://mof.ge/ | ministry_finance | 12,145 | good | true |
| LIMITED | Financial Monitoring Service of Georgia | https://fms.gov.ge/ | aml | 947 | low_content | false |

### GE Category Coverage (after)

| Category | Source | Status |
|----------|--------|--------|
| central_bank | nbg.gov.ge | active/enabled/good |
| tax | rs.ge | active/enabled/good |
| legal_acts | matsne.gov.ge | active/enabled/good |
| ministry_finance | mof.ge | active/enabled/good |
| aml | fms.gov.ge | limited/disabled (947c — below threshold) |

**Missing:** AML source disabled (fms.gov.ge below 1,000c threshold — needs adapter).

---

## Belarus (BY) — Sources Enabled

| Action | Name | URL | Category | Chars | Quality | Enabled |
|--------|------|-----|----------|-------|---------|---------|
| ENABLED + URL FIX | National Bank of Belarus | https://www.nbrb.by/ | central_bank | 19,068 | good | true |
| ENABLED | Ministry of Finance Belarus | https://minfin.gov.by/ | finance_ministry | 5,897 | good | true |
| ENABLED | National Legal Internet Portal of Belarus | https://pravo.by/ | legal_acts | 6,694 | good | true |
| LIMITED | Ministry of Taxes and Levies of Belarus | https://www.nalog.gov.by/ | tax | 990 | low_content | false |

> **NBRB URL fix:** Changed from `https://www.nbrb.by/legislation` (1,736c) to root `https://www.nbrb.by/` (19,068c) — 11× more content extracted.

### BY Category Coverage (after)

| Category | Source | Status |
|----------|--------|--------|
| central_bank | nbrb.by | active/enabled/good |
| finance_ministry | minfin.gov.by | active/enabled/good |
| legal_acts | pravo.by | active/enabled/good |
| tax | nalog.gov.by | limited/disabled (990c HTML; 3 PDFs 5,237c — needs adapter) |

**Missing:** No enabled tax source. nalog.gov.by extracts only 990c HTML but has 3 PDFs with 5,237c combined — PDF adapter needed.

---

## Audit Results — GE Sources

| URL | Quality | Chars | Enabled | Verdict |
|-----|---------|-------|---------|---------|
| https://www.nbg.gov.ge/ | good | 1,378 | yes | can_monitor |
| https://rs.ge/ | good | 10,062 | yes | can_monitor |
| https://matsne.gov.ge/ | good | 32,681 | yes | can_monitor |
| https://fms.gov.ge/ | low_content | 947 | no | needs_adapter |
| https://mof.ge/ | good | 12,145 | yes | can_monitor |

## Audit Results — BY Sources

| URL | Quality | Chars | Enabled | Verdict |
|-----|---------|-------|---------|---------|
| https://www.nbrb.by/ | good | 19,068 | yes | can_monitor |
| https://minfin.gov.by/ | good | 5,897 | yes | can_monitor |
| https://www.nalog.gov.by/ | low_content | 990 | no | needs_adapter |
| https://pravo.by/ | good | 6,694 | yes | can_monitor |

---

## Health Check Results

All 25 enabled sources across all jurisdictions: **PASS: 25 / WARN: 0 / SKIP: 23 / FAIL: 0**

GE + BY enabled sources: all 7 pass individually (confirmed by `python run.py health`).

---

## Adapter Queue — GE/BY Items

| Priority | Source | Jurisdiction | Category | Issue |
|----------|--------|-------------|----------|-------|
| MEDIUM | Financial Monitoring Service of Georgia | GE | aml | 947c — below 1,000c threshold |
| MEDIUM | Ministry of Taxes and Levies of Belarus | BY | tax | 990c HTML; 3 PDFs found — needs PDF adapter |

---

## Score Delta

| Metric | Before | After |
|--------|--------|-------|
| GE score | 80 | **89** |
| GE label | usable | **strong** |
| GE enabled | 0 | **4** |
| GE good | 0 | **4** |
| BY score | 75 | **86** |
| BY label | usable | **strong** |
| BY enabled | 0 | **3** |
| BY good | 0 | **3** |
| Overall score | 79 | **81** |
| Overall enabled | 18 | **25** |

---

## Next Steps

1. **fms.gov.ge adapter** (GE AML): Site has SSL cert issue (Tier 1 fails, Playwright extracts 947c). Find the press releases or regulatory acts endpoint — try `/news` or `/publications` subpages to improve extraction above 1,000c threshold. Then enable.

2. **nalog.gov.by PDF adapter** (BY tax): HTML extraction gives 990c (10c below threshold), but `document-test` found 3 PDFs with 5,237c combined. Build an adapter that fetches and parses these PDFs. Once good, enable.

3. **AML source for Belarus**: No Belarusian FIU source currently. The Department of Financial Monitoring (subordinate to KGB) — check if there is a public-facing site at a `.gov.by` domain.

4. **Run `python run.py coverage --html`** to refresh the client-facing HTML coverage report.
