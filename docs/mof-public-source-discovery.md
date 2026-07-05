# MoF Public Source Discovery

Date: 2026-06-21

## Scope

This discovery pass used repository search, official MoF sitemap/robots review,
public search, and bounded no-save tests against official `mof.gov.ae` URLs
only. Private mirrors and non-official legal-service copies were rejected as
source-of-truth candidates.

Robots result:

- `https://mof.gov.ae/robots.txt` allows `User-agent: *` and points to
  `https://mof.gov.ae/sitemap_index.xml`.

Sitemap result:

- The official sitemap exposes relevant MoF pages under public finance, tax,
  international relations, public debt, open data, media centre, and federal
  budget sections.

## Candidate Decisions

| Candidate | URL | No-save / proof result | Decision | Reason |
| --- | --- | --- | --- | --- |
| `AE-mof-top-up-tax` | `https://mof.gov.ae/en/public-finance/tax/top-up-tax/` | Strong no-save q=62; proof saved; baseline 2/2; stable hash; mass-monitor `MONITOR_OK` | fresh-alert activated | Official MoF DMTT/top-up tax page, meaningful extraction |
| `AE-mof-corporate-tax-in-the-uae` | `https://mof.gov.ae/en/public-finance/tax/corporate-tax-in-the-uae/` | Strong no-save q=65; proof saved; baseline 2/2; stable hash; mass-monitor `MONITOR_OK` | fresh-alert activated | Official MoF corporate tax page, meaningful extraction |
| `AE-mof-aeoi-fatca-crs` | `https://mof.gov.ae/en/public-finance/international-relations/automatic-exchange-of-information-aeoi-fatca-crs/` | Strong no-save q=65 with PDF-listing adapter; proof saved; baseline 2/2; stable hash; mass-monitor `MONITOR_OK` | fresh-alert activated | Official MoF AEOI/FATCA/CRS page and document-link surface |
| `AE-mof-uae-financial-framework` | `https://mof.gov.ae/en/public-finance/uae-financial-sustainability/uae-financial-framework/` | Strong no-save q=65 with PDF-listing adapter; proof saved; baseline 2/2; stable hash; mass-monitor `MONITOR_OK` | fresh-alert activated | Official MoF financial framework page and document-link surface |
| `AE-mof-open-data-statistical-reports` | `https://mof.gov.ae/en/open-data/statistical-reports/` | Probe `NAV_SHELL_ONLY`; applied adapter q=56, below strong-pass threshold | held | Open-data listing needs better adapter before activation |
| `AE-mof-federal-budget-archive` | `https://mof.gov.ae/en/public-finance/uae-federal-budget/uae-federal-budget-archive/` | Accessible, but q=52/q=58 below strong-pass threshold | held | Official and useful, but quality gate failed; do not activate from almost-pass |
| `AE-mof-double-taxation-agreements-dtas` | `https://mof.gov.ae/en/public-finance/international-relations/double-taxation-agreements-dtas/` | Accessible, q=56/q=58 below strong-pass threshold | held | Needs adapter/parser improvement before monitoring-ready claim |
| `AE-mof-country-by-country-reporting` | `https://mof.gov.ae/en/public-finance/international-relations/country-by-country-reporting/` | `NAV_SHELL_ONLY` | held | No fresh-alert activation without meaningful extraction |
| `AE-mof-t-bonds` | `https://mof.gov.ae/en/public-finance/public-debt/t-bonds/` | `NAV_SHELL_ONLY` | held | Public-debt subpage needs adapter work or remains held |
| `AE-mof-t-sukuk` | `https://mof.gov.ae/en/public-finance/public-debt/t-sukuk/` | `NAV_SHELL_ONLY` | held | Public-debt subpage needs adapter work or remains held |
| `AE-mof-retail-sukuk` | `https://mof.gov.ae/en/public-finance/public-debt/retail-sukuk/` | No strong pass | held | Not activation-ready |
| `AE-mof-regional-international-partnerships-agreements` | `https://mof.gov.ae/en/public-finance/international-relations/regional-and-international-partnerships-and-agreements/` | No strong pass | held | Not activation-ready |
| `AE-mof-open-data-publication-plan-2026` | `https://mof.gov.ae/en/open-data/open-data-publication-plan/open-data-publication-plan-2026/` | `NAV_SHELL_ONLY` | held | Not activation-ready |

## Unsafe Or Rejected Methods

- No broad crawling.
- No bypassing access controls.
- No activation from no-save only.
- No activation from one successful run.
- No private legal-service mirrors used as monitoring sources.
- No FTA source counted as MoF readiness.

## Safe Claim After Discovery

Selected official MoF pages covering publications/releases, financial
legislation, ESR, DMTT/top-up tax, corporate tax, AEOI/FATCA/CRS, and UAE
financial framework can be monitored as proof-backed fresh-alert sources.

## Forbidden Claim After Discovery

Complete MoF coverage, complete tax coverage, all MoF publications monitored,
all UAE financial legislation monitored, or never-miss MoF monitoring.
