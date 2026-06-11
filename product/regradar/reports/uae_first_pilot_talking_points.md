# UAE First Pilot — Talking Points

Internal reference for sales, onboarding, and prospect conversations.
Not for distribution. Not legal advice.

---

## What Works Well Today

Nine UAE regulatory sources are active and extracting clean content:

| Source | Category | Chars |
|--------|----------|-------|
| Central Bank of UAE (CBUAE) | central_bank | 26,804 |
| VARA | financial_regulator (crypto/VASP) | 2,705 |
| DFSA | financial_regulator | 5,627 |
| ADGM | financial_regulator | 2,135 |
| UAE Ministry of Finance | finance_ministry | 13,340 |
| UAE Legislation Portal | legal_acts | 14,808 |
| UAE FIU (UAEFIU) | aml | 2,026 |
| DIFC Laws and Regulations | legal_database | 9,150 |
| UAE Ministry of Economy | company_registry | 14,646 |

All 9 sources score GOOD (≥2,000 chars extracted). UAE coverage score: 100 / "strong".

---

## What Is Limited

- **FTA (Federal Tax Authority)** — geo-blocked JS SPA, 0 chars extracted. Tax monitoring is not available without a dedicated server-side adapter.
- **SCA (Securities and Commodities Authority)** — navigation-only SPA, 944 chars (nav only). Capital markets monitoring requires a dedicated adapter.
- **UAE e-Laws Portal / Official Gazette** — geo-blocked from external IPs. Not currently extractable.
- **ADGM FSRA subdomain** — direct `fsra.adgm.com` path fails; content accessible via the main ADGM URL only.

---

## Why Free Source Check Is Useful

Prospects receive — before committing to any paid plan:

1. **3–5 sources tested** against their specific jurisdiction and topic area
2. **Readiness snapshot** — which sources are GOOD, MEDIUM, or blocked
3. **Access limitation disclosure** — full transparency about what we cannot monitor
4. **Example alert format** — one sample brief from a live source
5. **Pilot recommendation** — a clear go / no-go with next steps

This builds trust and avoids overselling. The prospect knows exactly what they get.

---

## What a Paid Pilot Includes

Core P0 monitoring set (weeks 1–2):

- **CBUAE** — central bank circulars, licensing updates, consumer protection
- **VARA** — crypto / VASP regulatory guidance and rule updates
- **UAEFIU** — AML/CFT guidance, STR typologies, sanctions updates

Deliverables each week:
- Weekly AI compliance brief (English)
- Telegram push alerts on detected changes
- Source proof links (URL + extraction date)
- Monthly coverage report with source health status
- Known limitations documented in every report

---

## Which Sources Are Monitored Automatically

The 9 active sources listed above are polled automatically on each scheduled run. No manual action required for baseline monitoring.

---

## Which Need Manual Validation

- **FTA** — tax monitoring. Cannot be automated until a dedicated adapter is built.
- **SCA** — capital markets regulation. Navigation-only; content requires a custom adapter.
- **Any new source** not yet in the source registry must be tested with `python run.py test-source <url>` before being added.

---

## What NOT to Promise

- **Complete UAE regulatory coverage** — FTA and SCA are not covered
- **Real-time guaranteed alerts** — monitoring runs on a schedule; breaking changes may have a delay of up to 1 hour
- **Legal advice** — RegRadar is a monitoring tool, not a law firm
- **FTA tax monitoring** — not available before a dedicated adapter is shipped
- **SCA capital markets monitoring** — not available before a dedicated adapter is shipped
- **Zero false positives** — AI summaries are probabilistic; review_required=true items must be validated manually
