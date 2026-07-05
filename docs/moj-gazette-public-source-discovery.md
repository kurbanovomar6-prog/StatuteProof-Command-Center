# MoJ / Gazette Public Source Discovery

Date: 2026-06-21

## Verdict

PASS for one official/public selected source.

The public internet review found that the UAE Legislation platform is official and includes legislation and Official Gazette metadata. The root/sitemap access path is still not safe enough for a broad readiness claim, but the `/en/legislations` listing is a usable selected source after proof and baseline.

## Official URLs Inspected

| URL | Result | Decision |
| --- | --- | --- |
| `https://www.uaelegislation.gov.ae/en` | Public page says UAE Legislation is the official platform of UAE government legislation; includes sector counts and Official Gazette links. | Official context, not the activated monitor URL. |
| `https://www.uaelegislation.gov.ae/en/legislations` | Public legislation listing; no-save strong pass; proof-backed baseline passed. | Activated as one scoped fresh-alert source. |
| `https://uaelegislation.gov.ae/en/legislations/1990` | Official Gazette law page; accessible, but no-save did not pass strong gate. | Reference/evidence-library candidate only, not activated. |
| `https://www.moj.gov.ae/en/laws-and-legislation.aspx` | Official MoJ laws and legislation hub linking to UAE Legislations. | Discovery/context only. |
| `https://www.moj.gov.ae/en/laws-and-legislation/latest-legislations-and-laws.aspx` | No-save `NAV_SHELL_ONLY`; page showed `Total Count: 0`. | Held, not activated. |
| `https://www.moj.gov.ae/en/laws-and-legislation/legislative-framework-of-the-judicial-system-in-uae/main-legislations.aspx` | Accessible but no strong no-save pass. | Held, not activated. |
| `https://www.moj.gov.ae/robots.txt` | Public robots allows `/`, disallows `/cp/` and `/login.aspx`; sitemap listed. | Safe to inspect public pages only. |
| `https://www.moj.gov.ae/sitemap.xml` | Public sitemap available; contains laws-and-legislation pages. | Discovery only. |
| `https://uaelegislation.gov.ae/robots.txt` | Public robots did not disallow crawling. | Access still constrained by Cloudflare on root/sitemap. |
| `https://uaelegislation.gov.ae/sitemap.xml` | Direct curl returned `HTTP 403` with Cloudflare headers. | Do not bypass; not used. |

## Public Evidence Notes

- UAE Legislation platform describes itself as the official platform for UAE government legislations and lists federal legislation categories.
- The platform exposes Official Gazette fields on legislation detail pages, including Official Gazette date and number.
- The official UAE government portal states federal laws can be found through the MoJ legal portal and the Official Gazette.

## Unsafe Methods Rejected

- No CAPTCHA/WAF bypass.
- No private endpoint guessing.
- No hidden API scraping.
- No broad crawl.
- No claim that root `uaelegislation.gov.ae` is fully monitor-ready.

## Safe Claim After Discovery

Selected UAE Legislation Platform listing monitoring is available for a scoped pilot.

## Forbidden Claim After Discovery

Do not claim complete UAE legislation, MoJ/e-Laws, or Official Gazette monitoring.

