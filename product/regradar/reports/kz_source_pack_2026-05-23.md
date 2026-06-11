# Kazakhstan Source Pack — 2026-05-23

## Summary

**Before:** 2 enabled KZ sources (NBK + CBR-proxy), score: ~45 (limited)
**After:**  7 enabled KZ sources, score: **93 (strong)**

---

## Sources Added / Updated

| Action   | Name                                              | URL                                                | Category             | Quality | Chars |
|----------|---------------------------------------------------|----------------------------------------------------|----------------------|---------|-------|
| FIXED    | Ministry of Finance Kazakhstan                    | https://www.gov.kz/memleket/entities/minfin        | finance_ministry     | good    | 6,054 |
| FIXED    | ARDFM Kazakhstan — Financial Market Regulation    | https://www.gov.kz/memleket/entities/ardfm         | financial_regulator  | good    | 7,355 |
| FIXED    | Ministry of Justice of Kazakhstan                 | https://www.gov.kz/memleket/entities/adilet        | legal_acts           | good    | 7,295 |
| ENABLED  | Committee of State Revenue of Kazakhstan          | https://kgd.gov.kz/                                | tax                  | good    | 2,610 |
| NEW      | Financial Monitoring Committee of Kazakhstan      | https://www.gov.kz/memleket/entities/afm           | aml                  | good    | 6,403 |
| NEW      | Astana International Financial Centre (AIFC)      | https://aifc.kz/                                   | financial_regulator  | good    | 3,016 |

## Sources Skipped / Kept Disabled

| Name                                   | URL                         | Reason                                         |
|----------------------------------------|-----------------------------|------------------------------------------------|
| Adilet Legal Information System        | https://adilet.zan.kz/      | Connection timeout on all paths — unreachable  |
| nationalbank.kz/ru/normativnye-pravovye-akty | (old URL)             | Returns 404                                    |
| nationalbank.kz/ru/news                | (old URL)                   | Returns 404                                    |
| finreg.kz                              | https://finreg.kz/          | DNS not resolved                               |
| egov.kz news subpages                  | SPA dynamic routes          | low_content (SPA-rendered)                     |

## Category Coverage — KZ (after)

| Category            | Sources | Quality |
|---------------------|---------|---------|
| central_bank        | 1       | good    |
| finance_ministry    | 1       | good    |
| financial_regulator | 2       | good    |
| tax                 | 1       | good    |
| legal_acts          | 1       | good    |
| aml                 | 1       | good    |

**Missing:** no enabled source for `legal_acts` from Adilet (adilet.zan.kz unreachable — gov.kz portal covers partial).

## Score Delta

| Metric        | Before | After  |
|---------------|--------|--------|
| KZ score      | ~45    | 93     |
| KZ label      | limited | strong |
| KZ enabled    | 2      | 7      |
| KZ good       | 1      | 7      |
| Overall score | ~70    | 76     |

## Next Steps

1. Monitor AIFC for regulatory publications (currently extracts site content — consider RSS adapter for press releases)
2. Find working Adilet replacement — the `gov.kz/memleket/entities/adilet` page is the MoJ portal, not the legal acts database
3. Enable NBK (nationalbank.kz) with a correct URL — the legal base link is broken; try `/ru` or `/en/news/normativnye-pravovye-akty`
4. Run `python run.py coverage-plan --jurisdiction KZ` monthly to track improvement
