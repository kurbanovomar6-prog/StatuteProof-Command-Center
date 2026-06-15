# UAE 50 Target Candidate Universe

Date: 2026-06-15

## Executive Summary

The candidate universe is the existing 78-entry UAE work queue plus the 14-entry mass activation queue. It is large enough to give margin for a 50-source target, but not enough sources are technically ready today.

Current usable truth after this cycle: **19 enabled UAE sources / 15 readiness-supported / 4 under extraction remediation**.

## Candidate Coverage

The 78-entry work queue covers SCA, DFSA/DIFC, ADGM/FSRA, CBUAE, VARA, UAE FIU, EOCN, Ministry of Economy, Ministry of Justice, UAE legislation, FTA, and selected free-zone/regulatory pages. The highest-value candidates remain regulatory pages, circulars, rulebooks, AML/CFT pages, sanctions/TFS pages, consultations, enforcement pages, official registers, and official document/PDF listings.

## Priority Groups

| Group | Queue coverage | Current action |
| --- | ---: | --- |
| CBUAE | 10 | Hold/remediate access and alternate official endpoints. |
| SCA | 9 | Build item-level listing extraction for regulations/AML pages. |
| ADGM/FSRA | 8 | Three activated; continue guidance/enforcement/notices. |
| DFSA | 8 | Two activated; legacy URL models remain remediation. |
| VARA | 8 | Current framework path is stale/nav-shell; rediscover official PDF endpoints. |
| UAE FIU | 5 | Publications path blocked by likely WAF/403; use safe official alternate discovery only. |
| DIFC | 4 | Laws page still quality-limited; needs source-specific table/document adapter. |
| Other UAE official sources | 26 | Use only if official, public, buyer-relevant, and proof-backed. |

## Rejections / Holds

- Generic homepages are not counted when a better regulatory endpoint exists.
- Login/CAPTCHA/paywall/private portals remain blocked.
- Stale URLs, 403/WAF paths, 404 shells, nav-shell output, and shallow extraction remain remediation/blocked.
- No source is added to `sources.json` from no-save only.

## Next Candidate Pool

Closest candidates for the next batch:

1. `AE-adgm-fsra-guidance-policy`
2. `AE-adgm-fsra-enforcement`
3. `AE-difc-laws-and-regulations`
4. `AE-sca-latest-regulations`
5. `AE-sca-aml-cft`
6. `AE-vara-current-framework` after current official endpoint rediscovery
7. `AE-uae-fiu-publications` after safe alternate endpoint discovery
8. `AE-eocn-laws-regulations` after selector remediation
