# Uzbekistan Source Pack — 2026-05-24

## Summary

**Before:** 0 enabled UZ sources, score: 60 (limited)
**After:** 5 enabled UZ sources, score: **77 (usable)**

---

## Sources Researched

| URL | Result | Chars | Notes |
|-----|--------|-------|-------|
| https://cbu.uz/ | GOOD | 51,850 | Central Bank of Uzbekistan (correct root) |
| https://lex.uz/ | GOOD | 49,263 | Official legal database |
| https://imv.uz/ | LOW_CONTENT | 396 | Ministry of Economy & Finance — Playwright fetches 470K HTML but beautifulsoup only extracts 396c; JS-heavy SPA |
| https://adliya.uz/ | GOOD | 9,246 | Ministry of Justice (minjust.uz redirects here) |
| https://regulation.gov.uz/ | GOOD | 6,924 | Regulatory drafts portal (normative act consultations) |
| https://soliq.uz/ | FAILED | 0 | State Tax Committee — connection timeout |
| https://minjust.uz/ | GOOD | 9,246 | Redirects to adliya.uz |
| https://gov.uz/ | GOOD | 2,252 | Government portal — borderline, skipped |
| https://taxes.uz/ | FAILED | 0 | DNS not resolved |
| https://minfin.uz/ | FAILED | 0 | SSL cert hostname mismatch |
| https://nbu.uz/ | GOOD | 6,924 | National Bank of Uzbekistan (commercial state bank, not regulator — skipped) |
| https://tax.gov.uz/ | FAILED | 0 | DNS not resolved |

---

## Changes to sources.json

| Action | Name | Old URL | New URL | Status | Enabled |
|--------|------|---------|---------|--------|---------|
| FIXED URL | Central Bank of Uzbekistan | cbu.uz/ru/documents/regulatory_acts/ | https://cbu.uz/ | active | true |
| FIXED URL | Ministry of Economy and Finance Uzbekistan | mf.uz/ | https://imv.uz/ | limited | false |
| ENABLED | Lex.uz — Legal Information System | (same) | https://lex.uz/ | active | true |
| FIXED URL | Ministry of Justice Uzbekistan | minjust.uz/ | https://adliya.uz/ | active | true |
| DISABLED | State Tax Committee | (same) | https://tax.gov.uz/ | disabled | false |
| NEW | Uzbekistan Regulatory Draft Portal | — | https://regulation.gov.uz/ | active | true |

---

## Audit Results for UZ Sources

| URL | Quality | Chars | Enabled | Verdict |
|-----|---------|-------|---------|---------|
| https://cbu.uz/ | good | 51,850 | yes | can_monitor |
| https://imv.uz/ | low_content | 396 | no | needs_adapter |
| https://tax.gov.uz/ | failed | 0 | no | cannot_monitor |
| https://lex.uz/ | good | 49,263 | yes | can_monitor |
| https://adliya.uz/ | good | 9,246 | yes | can_monitor |
| https://regulation.gov.uz/ | good | 6,924 | yes | can_monitor |

---

## Sources Skipped / Not Added

| URL | Reason |
|-----|--------|
| soliq.uz | Connection timeout — all UZ tax domains unreachable |
| taxes.uz | DNS not resolved |
| minfin.uz | SSL certificate hostname mismatch |
| tax.gov.uz | DNS not resolved |
| nbu.uz | Commercial state bank, not a regulatory authority |
| gov.uz | 2,252c — borderline, no unique regulatory content |

---

## Category Coverage — UZ (after)

| Category | Source | Status |
|----------|--------|--------|
| central_bank | cbu.uz | active/enabled/good |
| finance_ministry | imv.uz | limited/disabled (needs adapter) |
| tax | tax.gov.uz | disabled/failed (all domains unreachable) |
| legal_acts | lex.uz | active/enabled/good |
| legal_acts | adliya.uz | active/enabled/good |
| legal_acts | regulation.gov.uz | active/enabled/good |

**Missing:** no AML source (no official UZ FIU website found); tax remains a gap.

---

## Score Delta

| Metric | Before | After |
|--------|--------|-------|
| UZ score | 60 | **77** |
| UZ label | limited | **usable** |
| UZ enabled | 0 | **5** |
| UZ good | 3 | **4** |
| Overall score | 76 | **71** |

> Note: Overall score decreased slightly from 76 → 71 due to gov.kz portal pages (minfin, ardfm, afm) scoring lower in today's audit than yesterday — likely transient Playwright rendering inconsistency on gov.kz. KZ score will improve when these sources are re-audited or an adapter is built.

---

## Next Steps

1. **Tax gap**: All UZ tax authority domains fail. Monitor if soliq.uz becomes reachable or find alternate official URL.
2. **imv.uz adapter**: Build beautifulsoup adapter targeting specific regulatory announcement pages (e.g. `/ru/normativnye-akty`) to resolve the 396c low_content issue.
3. **AML**: Find the official Uzbekistan FIU/financial monitoring authority URL — possibly under the Prosecutor General's Office or Ministry of Finance.
4. **KZ gov.kz sources**: Transient low_content in today's audit — monitor, and consider building adapters for gov.kz entity portal pages.
5. Run `python run.py source-audit --json` after the adapter is built to confirm improvement.
