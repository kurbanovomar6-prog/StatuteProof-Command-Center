# Armenia Source Pack — 2026-05-24

## Summary

**Before:** 0 enabled AM sources, score: 25 (weak)
**After:** 1 enabled AM source (arlis.am), score: **33 (weak)**

Root cause for limited improvement: Armenian government websites are geo-blocked from outside Armenia. Nearly all .am government domains return either "Connection denied by Geolocation" or connection timeout.

---

## Sources Researched

| URL | Result | Chars | Error |
|-----|--------|-------|-------|
| https://www.cba.am/ | FAILED | 0 | Self-signed SSL cert (ERR_CERT_AUTHORITY_INVALID) |
| http://www.cba.am/ | LOW_CONTENT | 217 | Returns "Connection denied by Geolocation" page |
| https://www.arlis.am/ | **GOOD** | **1,185** | Works — official legal acts database |
| https://www.src.am/ | FAILED | 0 | Geo-blocked / internal DNS |
| https://www.petekamutner.am/ | FAILED | 0 | Resolves to private IP 10.3.17.39 (internal network) |
| https://minfin.am/ | FAILED | 0 | Connection timeout — geo-blocked |
| https://moj.am/ | FAILED | 0 | Connection timeout — geo-blocked |
| https://www.gov.am/ | FAILED | 0 | Connection timeout — geo-blocked |
| https://laws.am/ | FAILED | 0 | SSL cert hostname mismatch |
| https://e-draft.am/ | LOW_CONTENT | 676 | Playwright renders but low extraction |
| https://www.parliament.am/ | FAILED | 0 | Connection timeout — geo-blocked |
| https://armenpress.am/ | GOOD | 24,754 | State news agency — not a regulatory body |

---

## Changes to sources.json

| Action | Name | Status Before | Status After | Enabled |
|--------|------|---------------|--------------|---------|
| ENABLED | ARLIS — Armenia Legal Acts System | mapped | active | true |
| UPDATED | Central Bank of Armenia | mapped | disabled | false |
| UPDATED | Ministry of Finance of Armenia | mapped | disabled | false |
| UPDATED | State Revenue Committee of Armenia | mapped | disabled | false |
| NEW | Ministry of Justice of Armenia | — | disabled | false |

---

## Audit Results for AM Sources

| URL | Quality | Chars | Enabled | Verdict |
|-----|---------|-------|---------|---------|
| https://www.cba.am/ | failed | 0 | no | cannot_monitor |
| https://minfin.am/ | failed | 0 | no | cannot_monitor |
| https://www.arlis.am/ | **good** | **1,185** | **yes** | **can_monitor** |
| https://www.src.am/ | failed | 0 | no | cannot_monitor |
| https://moj.am/ | failed | 0 | no | cannot_monitor |

---

## Sources Skipped

| URL | Reason |
|-----|--------|
| https://armenpress.am/ | State news agency — not a regulatory body; no category fit |
| https://e-draft.am/ | LOW_CONTENT (676c) — not above threshold |
| https://laws.am/ | SSL cert hostname mismatch |
| https://www.petekamutner.am/ | Resolves to private IP 10.3.17.39 — only accessible from inside AM government network |

---

## Root Cause: Geo-blocking

The vast majority of Armenian government websites block requests from foreign IPs. The pattern observed:
- `http://www.cba.am/` → HTML page titled "Connection denied by Geolocation"
- Most `.am` domains return connection timeout (consistent with geo-IP blocking)
- `petekamutner.am` DNS resolves to a private IP (10.3.17.39) — internal government intranet

**arlis.am is the only exception** — it has global CDN/access and works reliably.

---

## Score Delta

| Metric | Before | After |
|--------|--------|-------|
| AM score | 25 | **33** |
| AM label | weak | **weak** |
| AM enabled | 0 | **1** |
| AM good | 1 | **1** |
| Overall score | 71 | **79** |

---

## Next Steps

1. **CBA Armenia adapter**: The CBA website is a SharePoint site accessible only from Armenian IPs. Options:
   - Use a proxy/VPN endpoint in Armenia to scrape cba.am
   - Subscribe to CBA press release email/RSS if available outside AM
   - Check if CBA publishes regulatory circulars on a third-party (EBRD, IMF) platform

2. **minfin.am**: Same geo-blocking issue. Monitor if the situation changes.

3. **AML authority**: Armenia's FIU is the Financial Monitoring Center (FMC) at fmc.am — test this URL as a candidate if geo-restriction improves.

4. **MONEYVAL**: Armenia is subject to MONEYVAL (Council of Europe AML evaluations) — reports available on moneyval.coe.int — consider adding as an international source for AM compliance context.

5. **Long-term**: AM sources require either geo-proxying infrastructure or relying on MONEYVAL/IMF international reports for Armenia coverage.
