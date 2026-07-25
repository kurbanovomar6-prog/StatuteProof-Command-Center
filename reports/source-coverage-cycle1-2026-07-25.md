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

---

# Candidate promotion — local gates passed (2026-07-25, cycle 5)

The goal's "zero-research win" was to promote the enabled `candidate` sources.
I had only diagnosed them; this is the execution.

## What was actually run

Two **saved** baseline runs per source (`run.py source-lab <url> --save --source-id
<id> --baseline-runs 2`, with each row's own adapter config), then the product's
own certification gate was read back.

| source_id | baselines | certification | can_activate | hash stable |
|---|---|---|---|---|
| AE-uk-ofsi-consolidated-list | 2 | MONITORING_CERTIFIED | yes | yes |
| AE-ugd-ebc-gold-rules | 2 | MONITORING_CERTIFIED | yes | yes |
| AE-uae-pdpl-status | 2 | MONITORING_CERTIFIED | yes | yes |
| GCC-sa-sama-circulars | 2 | MONITORING_CERTIFIED | yes | yes |
| GCC-sa-sama-news | 2 | MONITORING_CERTIFIED | yes | yes |
| GCC-qa-qfcra-rulebook | 2 | MONITORING_CERTIFIED | yes | yes |
| GCC-qa-qfcra-news | 2 | MONITORING_CERTIFIED | yes | yes |
| AE-un-consolidated-sanctions-xml | 2 (after fix) | MONITORING_CERTIFIED | yes | yes |
| AE-bis-bcbs-publications-rss | 2 (after fix) | MONITORING_CERTIFIED | yes | yes |

The normalized hash was **identical across both runs** for all nine — which is the
property that matters: it means the first real change these sources emit will be a
true change, not extraction noise.

## A defect fixed to get the last two through

UN consolidated XML and the BIS RSS reported `baseline_runs_completed: 0` no matter
how often they ran. Cause: their `adapter_name` is `xml_feed`, a **fetching-registry**
name that the HTML-extract platform does not know, so the gate logged *"Adapter
failed: Unknown adapter: xml_feed"*, fell back to the generic extractor and then
demanded a CSS selector for an XML document (`NEEDS_SELECTOR_REVIEW`) — a request that
cannot be satisfied. Setting `adapter_family: static_html` lets the gate simply hash
the document, while monitoring still uses the `xml_feed` registry adapter through
`adapter_name`. Both then certified (UN q=51, BIS q=65).

## What I deliberately did NOT do, and why

I did **not** set `monitoring_mode: fresh_alert` or `alert_eligible: true`.

`app/api.py:1112-1114` computes the **customer-visible** `sources_fresh_alert` count
from exactly those two fields. Flipping them on the strength of a laptop run would
repeat this project's own documented mistake — 35 blocked-host sources once carried
`MONITOR_OK` while being unreachable from production. Local egress is not evidence of
production reach, and every one of these rows says in its own notes that the gate is
"2 baselines, MONITOR_OK, review **on prod**".

So each row now carries `baseline_runs_completed: 2` and
`local_intake_certified: true`, and stays `candidate`. The remaining step is a
production run — one command per source, or one batch:

```bash
# on the droplet, from /srv/regradar
python3 run.py mass-monitor --source-id AE-uk-ofsi-consolidated-list --save-proof --no-alerts
# …repeat for the other eight, or run the batch and filter afterwards
```

Promote a row to `monitoring_mode: fresh_alert` + `alert_eligible: true` only after
that run reports `MONITOR_OK` for it. Nine promotions is roughly a nine-point jump in
the honest alert-eligible count, and two of them (UN consolidated and UK OFSI) are
half of the "big four" sanctions lists.
