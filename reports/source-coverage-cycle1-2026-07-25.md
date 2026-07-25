# Source coverage — cycle 1 (2026-07-25)

Goal: find and add the monitoring sources with the highest impact per effort.
Method: `source-lab` (read-only intake) against every relevant source, then direct
adapter verification, then registry config. Every number below came from a live run
on this machine — nothing is quoted from research claims.

## Headline finding: the readiness gate is ADAPTER-BLIND (confirmed defect)

`app/pipeline.py:320` (the monitoring path) calls `get_adapter_for_url(url, source)`.
`app/source_intake.py` (the readiness gate behind `source-lab`) calls it **zero times**.

Consequence: any source whose content only parses through a registry adapter
(`xml_feed`, `html_listing`, `rulebook_platform`, and ~20 host adapters) is scored
`NAV_SHELL_ONLY` / `POOR` by the gate and **can never be certified or promoted**,
even though monitoring reads it perfectly. This single defect explains most of the
"broken" candidates below.

Proof — each fetched through its configured adapter while the gate called it a nav shell:

| Source | Adapter | Gate said | Adapter actually returns |
|---|---|---|---|
| US OFAC Recent Actions | html_listing | NAV_SHELL (1627) | **1494 chars, 30 listing lines** ("Iran-related Designations…") |
| MENAFATF Publications | html_listing | NAV_SHELL (1160) | **1388 chars, 57 listing lines** |
| VARA Compliance Rulebook | rulebook_platform | NAV_SHELL (1782) | **100,940 chars** |
| DFSA Consultation Papers | rulebook_platform | NAV_SHELL (488) | **2,510 chars** |
| EU Consolidated Sanctions (RSS) | xml_feed | NAV_SHELL (2409) | **970-char deterministic digest**, items dated 20 Jul 2026 |

## The 23 enabled `candidate` sources — verdict

**9 genuinely ready** (CONFIRMED_ACCESSIBLE, content present): UK OFSI consolidated list
(4,145,540 chars), UN Security Council consolidated XML (498,722), SAMA circulars (76,647),
BIS Basel RSS (23,536), QFCRA news (13,800), QFCRA rulebook (11,437), UAE Good Delivery
(10,452), UAE PDPL status (5,020), SAMA news (2,420). Quality 51–59 ("LIMITED") is expected
pre-baseline — the breakdown shows a `no_proof: -25` penalty that clears once evidence is saved.

**5 blocked only by the gate defect** (see table above) — no research needed, they work.

**1 dead URL, mis-diagnosed in the registry:** UAE FIU Articles RSS returns **102 chars of a
404 "Page Not Found"** page. The registry labels the FIU cluster `geo_blocked`; for this URL
that is wrong — it is simply gone.

**8 genuinely need adapter work:** DIFC Courts judgments-orders, ADGM RA public notices,
MoJ AML/CFT, DMCC knowledge bank, Saudi CMA implementing regulations, CBK Kuwait press
releases, SAMA rulebook root (NEEDS_SELECTOR_REVIEW, 871 chars).

## Shipped in this cycle (verified, suite green)

**One config recipe unlocked 4 ADGM sources.** ADGM's enforcement/alerts/judgments listings
*are* fully server-rendered — but inside **custom elements** (`<adgm-table-row>` /
`<adgm-table-cell>`) instead of a `<table>`, so no CSS selector and no generic extractor
finds them. `content_selector: "adgm-table-row"` recovers the dated rows verbatim.

- `app/adapters/html_listing.py`: added `adgm.com` to `_ALLOWED_HOSTS` (deliberate, with the
  verification recorded in the comment).
- **Added** (new, `enabled: false`, `status: candidate`): `AE-adgm-fsra-regulatory-actions`
  (11 rows, 08 Jan 2026 Wealthface enforceable undertaking), `AE-adgm-ra-regulatory-actions`
  (11 rows, 26 Jan 2026 false-beneficial-ownership fine).
- **Fixed two sources that were already in the registry but scoring nav-shell**:
  `AE-adgm-fsra-regulatory-alerts` (40 dated rows, 08 Jul 2026 Veyron Markets) and
  `AE-adgm-courts-judgments` (11 rows, 20 Jul 2026 ADGMCFI-2020-020 NMC Healthcare).
- All four now read through the monitoring path above their `expected_min_length`:
  4261 / 1147 / 1955 / 1806 chars. `ruff` clean; full backend suite exit 0, 0 failures.

Why these matter: FSRA/RA regulatory actions are enforcement decisions and the alerts page is
a warning feed — the highest action-forcing content class for a personally-liable MLRO.

## Honest corrections to my own earlier reporting

1. **"30 Tier-1 sources to add" was overstated.** That list was deduped by *domain*; the
   registry holds 452 URLs across only 164 domains. Re-checking per URL, most were already
   present (FTA CT/VAT guides, FTA Legislation, MoF Financial Legislation, CMA circulars, VARA
   notices/news/enforcement, DIFC practice directions, and ADGM FSRA Alerts). Genuinely new:
   **20 non-WAF + 6 behind CBUAE's WAF**.
2. **"ADGM pages are server-rendered tables" was imprecise.** The content is server-rendered
   (verified: "Wealthface", "Payward", "Final Notice", "2026" all present in the raw HTML), but
   the structure is custom elements, not tables — which is exactly why it needed a recipe.
3. **The FTA pages do not work from here.** `tax.gov.ae` listings returned **28–51 chars**
   locally (ASP.NET + JS) even though WebFetch rendered their content. They need a JS/Playwright
   path, not a selector. Do not add them as plain sources.
4. A probe harness I wrote first used `timeout 90 …`; **macOS has no `timeout`**, so every run
   returned empty and I briefly read that as "all 23 sources broken". Corrected with
   `subprocess.run(..., timeout=)`.

## Next, in impact order

1. **Fix the gate defect** — make `source_intake` consult `get_adapter_for_url` like
   `pipeline` does. This alone unblocks promoting 5 already-working candidates (OFAC, MENAFATF,
   VARA rulebook, DFSA CPs, EU sanctions RSS) through the documented path.
2. **Promote the 9 ready candidates** after 2 prod baselines (2 of the "big four" sanctions
   feeds — UN and OFSI — are in this group).
3. Repair the dead FIU RSS URL; re-check whether the FIU cluster is truly geo-blocked or also
   just moved.
4. Apply the same "find the real container" method to the remaining 8: they are individually
   cheap once a selector is known.
5. Not yet researched: GCC beyond SAMA/QFCRA/CBK (Oman CBO/CMA/FSA, Kuwait CMA, Bahrain CBB
   enforcement are absent from the registry entirely), Wolfsberg, UK OFSI recent-changes page.
