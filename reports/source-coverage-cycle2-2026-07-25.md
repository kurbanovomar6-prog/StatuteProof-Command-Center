# Source coverage — cycle 2 (2026-07-25)

Method: five research agents (change-log hunt, enforcement map, Oman/Kuwait census,
UAE selector hunt, sanctions delta hunt), then solo verification of every claim through
**our own fetcher and adapters** before anything entered the registry. Nothing below is
taken on an agent's word: where our code disagreed with an agent, our code wins and the
disagreement is recorded.

Branch `tenten`. No production deploy — that stays owner-gated.

---

## 1. The structural blocker is closed (the headline)

The readiness gate fetched every document itself and could only transform HTML, so any
source served by a **fetching-registry adapter** (`xml_feed`, `html_listing`,
`rulebook_platform`, the per-host adapters) was uncertifiable by construction: the gate
read raw XML or a listing shell, ran the generic extractor over it, and scored
NAV_SHELL_ONLY / NEEDS_SELECTOR_REVIEW — while the monitoring pipeline read the same
source perfectly. For the UN and BIS feeds the gate was demanding a CSS selector for an
XML document. This was documented as "impossible" three times in prior cycles.

`run_source_intake` now offers the fetch to an opted-in registry adapter first. It is
**strictly opt-in**: the source must NAME the adapter (`adapter_name == adapter.name`)
and direct-PDF sources are never delegated. That narrowness was learned the hard way —
the first version delegated on any host match and hijacked a PDF source, breaking eight
tests. `tests/test_registry_adapter_delegation.py` now pins every clause of the boundary.

**Measured effect: 18 registry rows engage the delegation; 18 of 19 tested rows certify
TEST_PASSED with a stable hash across two runs.** That is roughly double what I expected
when writing the fix — it unblocked rows I had not been tracking (ADGM Courts judgments,
ADGM RA regulatory actions, ADGM FSRA alerts, EU consolidated sanctions RSS, OFAC civil
penalties, the DFSA AML rulebook module).

---

## 2. Two live defects found and fixed

### 2.1 An enabled AML source was monitoring a ministry homepage

`AE-moj-aml-cft-legislation` (enabled) pointed at the single-segment MoJ URL, which
**302-redirects to `https://www.moj.gov.ae/default.aspx`** — the ministry homepage.
Verified directly, not inferred: status 200, final URL `default.aspx`, redirect chain
`[302]`. So the source named "AML/CFT legislation" was diffing the homepage. A homepage
edit would have been reported as an AML legislation change, and an actual amendment to
the AML law would have been invisible.

Fixed to the doubled-segment path and given the accordion selector. Verified: **4,026
normalized chars, stable hash**, carrying Federal Decree-Law 10/2025 (AML), Cabinet
Resolution 134/2025 (executive regulations) and Cabinet Resolution 74/2020 (terrorist
lists) — i.e. the actual binding instruments.

### 2.2 A dead URL's 404 page was offered to the gate as content

`AE-uaefiu-articles-guidelines-rss` returns **HTTP 404**. Playwright escalates on a
failed requests tier *without consulting the status*, so it rendered the site's 404
template and handed **78,130 chars** of chrome to the gate. That run only failed because
the template happened to normalize to 102 chars and tripped the nav-shell heuristic.

A 404 page carrying a paragraph of prose — the common shape — would have cleared both
the length floor and the nav-shell check, been certified, and then the monitor would
hash the error template and raise a **regulatory-change alert every time the regulator
edited its own 404 wording**. That is a false alert about a change that never happened.

New gate: `_reject_stale_url` refuses **404/410 only**, mapping to the existing
`URL_STALE` failure code. Deliberately not every 4xx/5xx — a 403 or a Cloudflare 503 is
a gate in front of real content that the Playwright tier or the owner's egress proxy
legitimately gets past, which is exactly how the WAF-blocked regulator hosts are
monitored. Verified: the dead source now reports `URL_STALE`, `chars_raw=0`.

---

## 3. Registry integrity correction (self-inflicted, caught and undone)

In the previous cycle I wrote `baseline_runs_completed: 2` onto three rows from **local**
intake runs. The prod promotion gate (`mass_source_activation._has_completed_baseline`)
reads that field, so local evidence would have counted toward a production baseline —
the same class of error as the previously-recorded "35 blocked-host sources sold as
MONITOR_OK". Reset to 0 on the rows with no saved proof, with the count preserved in
`local_baseline_runs_completed` and a note explaining why.

Local certification is now recorded only in explicitly-local fields
(`local_intake_certified`, `local_intake_chars`, `local_baseline_runs_completed`).
**Promotion still requires a saved proof that only a prod `mass-monitor` run can
produce.** 21 rows carry local certification; **zero customer-visible rows were touched**
(138 `fresh_alert` + `alert_eligible` before and after).

Related pre-existing finding, attributed by git history rather than assumption: two rows
are `fresh_alert` + `alert_eligible` with **no saved proof** —
`AE-vara-regulatory-notices-and-enforcement-index` (from `df3c669`) and
`AE-vara-compliance-risk-rulebook-html` (from `579e1b2`/`45417ec`), both predating this
cycle. I did **not** demote them, because I tested them and both work (10,323 and 93,826
chars, stable hashes): the gap is bookkeeping, not capability. They need a prod proof run.

---

## 4. Added to the registry (verified through our own adapters, candidate/disabled)

| Source | Verified output | Why it matters |
|---|---|---|
| `AE-dfsa-rulebook-revision-updates` | 40 rows / 1,324 chars normalized, stable | The AML Module itself changed **02 July 2026**. One page carries every dated rulebook amendment, waiver/modification notice (W-numbers) and consultation paper — the change is visible without diffing a whole module. |
| `GCC-qa-qfcra-legislation-revision-updates` | 40 rows / 2,084 chars normalized, stable | Includes `GENE 8.1.1` (01 May 2026); GENE ch.8 governs mandatory controller-change notice to the Regulatory Authority. |

Both are the same Drupal `view_revision_updates` shape as the already-proven CBB
change-log — the highest-value page shape found so far.

### Second batch — enforcement channels (added after verification)

| Source | Verified output | Why it matters |
|---|---|---|
| `GCC-sa-cma-announcements` | 4,512 chars normalized, 30 dated rows, stable | Saudi CMA enforcement flows through announcements, not a separate enforcement page: a fine for Offer-of-Securities violations (28-June-2026) and a >20,000-investor compensation action (29-June-2026). |
| `GCC-kw-cbk-penalties` | 760 chars normalized, stable | A dedicated supervisory penalties register — "your peer category was just fined". Verified rows e.g. "18.11.25 CBK Imposes a Penalty on an Exchange Company"; 28 items in 2025. |

Both selectors were chosen for **signal**, not size. The Saudi CMA card bodies contain
escaped HTML that surfaces as literal text — 25% of extracted lines were `<p style=…>` —
so monitoring them would raise a regulatory alert on a styling tweak. Restricting the
selector to date + headline gives 0 markup lines and all 30 dates.

### A dedup catch worth recording

`AE-adgm-ra-public-notices` was **already in the registry, enabled, with no adapter config
at all** — so it ran the generic path, which sees only the page shell (the notices are
server-rendered inside ADGM custom elements). The value here was configuration, not
addition. With the verified selector it returns 5,063 chars / 112 dated lines (newest
22–24 Jul 2026). Proposed-deregistration notices open a fixed s867A objection window, so
learning late forfeits the right to object — this is among the most concrete harms found.

Intake now reports `SOURCE_STRUCTURE_CHANGED` for it, which is the gate behaving
**correctly**: changing the monitored region from page shell to notice rows is exactly the
structural change it is built to catch. Content is stable across two runs (identical hash,
1,803 chars). Row flagged `rebaseline_required` and explicitly **not** marked certified;
it needs `run.py rebaseline` for this source id at deploy time.

### EOCN un-page — verified working, but signal-diluted

The UAE local terrorist list delta page (already in the registry) does carry the dated
designation notices — "Adding 16", "Resolution No 63", "Removal of" all confirmed present
in the fetched HTML. But a `.view-content` extract is 71,140 chars dominated by the static
legal-framework preamble about Cabinet Decision 74/2020, so a real designation notice is a
small delta inside a large static blob. Not a defect, and not something I changed: this is
the most binding channel for our ICP, and a tighter selector on the notices list would
raise its signal materially. Queued rather than guessed at.

**A verified negative worth keeping:** the QFCRA instance's date filter is broken.
`?f_days=on&changed=-30 day` returns HTTP 200 with **zero rows**, so only the bare URL
works. Our own fetch confirmed the agent's caveat. The registry row records this so a
future "add the window param for consistency" edit does not silently empty the source.

---

## 5. Verified but NOT added, with the reason

Honest refusals matter as much as additions here.

- **SAMA rulebook revision updates** — an agent reported 22 dated rows (CCyB rate change
  25 May 2026, account-opening rules 30 June 2026). **Does not reproduce with our
  fetcher**: 195 chars on every parameter form tried (`-30 day`, `-365 day`,
  `items_per_page=40&sort_by=…`, bare), below the 300-char floor that protects against
  selector drift. Not added on an unreproducible claim. Worth one more attempt with a
  different vantage — the content, if real, is high value (CCyB has an implementation
  window for banks).
- **EU consolidated sanctions list (XML 24.8 MB / CSV ~17 MB)** — fetchable and
  well-characterised (root `<export>`; semicolon-delimited CSV with per-entity
  `Entity_Regulation_PublicationUrl`), but our `_MAX_RESPONSE_BYTES` guard is 10 MB and
  exists to bound peak memory against decompression bombs. **I am not raising it** for a
  source add. If these are wanted, they need a streaming adapter, not a bigger ceiling.
- **EUR-Lex OJ L feed** (`display-feed.rss?rssId=222`) — works cleanly through our
  `xml_feed` (root `rss`, 100 items, 32,699 chars) and is a genuine *delta* channel that
  announces each amending regulation. **Not added as an alert source**: it carries every
  OJ L act, not just restrictive measures, and it changes daily — so as-is it would
  produce daily noise. `xml_feed` has no keyword filter. This is a feature request
  (item-level filtering), not a config change.
- **Qatar NCTC list updates** — the dated notices are genuinely there and
  server-rendered (found `<h2>` "Updating the list of sanctions (Local section):
  Designation on 07-07-2026, Decision No. 102 for the year 2026"), but every reasonable
  container selector missed; only `body` extracts, at 7,872 chars of mixed chrome.
  Needs a proper selector pass before it earns a row.

---

## 6. High-value findings queued, not built (each needs real work)

Ranked by harm-from-learning-late per unit of effort.

1. **SCA "Violations and Violators" register** (`uaecma.gov.ae/en/open-data/violations-and-violators.aspx`)
   — the named-violator penalty register for UAE onshore securities, and we capture
   **none** of it. Columns confirmed (Violator / Violation / Decision-Penalty / Date) but
   rows load via `POST /api/PublicApi/GetContentList`, which returns **401** without a
   front-end token. Needs Playwright. This is the single biggest uncovered UAE item.
2. **CBK Kuwait penalties register** (`cbk.gov.kw/en/supervision/penalties`) — 200, dated
   batch disclosures ("CBK Imposes a Penalty on an Exchange Company", 18.11.25; 28 items
   in 2025). Note the sibling path `/en/supervision/cbk-regulations-and-instructions`
   is a **404** — the canonical instruction paths are under
   `/en/legislation-and-regulation/…/<sector>`.
3. **Saudi CMA announcements** — host and path both moved: `cma.org.sa` 301s to
   `cma.gov.sa`, and `/en/Market/NEWS/` became `/en/MediaCenter/NEWS/Pages/default.aspx`.
   Real enforcement flows through it (a fine for Offer-of-Securities violations,
   28-June-2026; a 20,000-investor compensation action, 29-June-2026). Our
   `GCC-sa-cma-regulations` row already uses the correct `cma.gov.sa` host, so only the
   news channel is missing.
4. **UAE local terrorist list (EOCN)** — the most directly binding channel for our ICP
   (Cabinet Decision 74/2020 TFS regime). The delta page `eocn.gov.ae/en-us/un-page` is
   **already in the registry** and is server-rendered with explicit change notices
   ("Cabinet Resolution No 63 of 2026 Adding 16 individuals and 5 entities to UAE
   Terrorist List"). The list file itself is legacy BIFF `.xls` behind a GUID `FileID`
   that almost certainly rotates per update — so anchor on the un-page and re-resolve the
   FileID each run. Verifying that our existing row actually captures those notices is
   cheap and high value.
5. **Oman CBO + FSA** — blocked by a **fixable** cause, not a bot-wall: both serve the
   leaf certificate without the intermediate (`verify error:num=21: unable to verify the
   first certificate`); with verification skipped both return 200 with full content. Fix
   is a per-host CA-bundle/intermediate exception — **not** `verify=False`. CBO
   additionally needs Playwright (SharePoint client-side circular catalog).
6. **ADGM RA public notices, DIFC Courts judgments, DMCC knowledge bank** — all
   confirmed STATIC_HTML_OK with selectors (`div.aadgmra-search-content`,
   `div.each_result`, `div.jplist-item.resource-link-item`). ADGM strike-off notices open
   fixed objection windows, which is real harm. Caveat for ADGM: notice bodies contain
   Word-export XML islands (10,426 `<w:` tags) — extract from the head cells, not the
   full body.
7. **MSX Oman circulars RSS** (`msx.om/rss.aspx?t=Circulars`) — 20 dated items,
   2026-06-02 → 2026-07-20. Gotcha: the item link element is capitalised `<Link>`, which
   our `xml_feed` would need to match case-insensitively. The `?t=Decisions` and `?t=News`
   variants return an empty 267-byte channel shell — do not add them.

---

## 7. Do NOT promise coverage for (evidence-backed refusals)

- **Kuwait CMA** — no HTTP response at all from our vantage (`ECONNREFUSED`, then timeout
  on both 443 and 80, apex and `www`). A network/geo block, not a bot-wall. Confirms the
  standing note. Kuwait can honestly be claimed as **banking + FIU only**.
- **Boursa Kuwait** — Akamai bot manager, 403.
- **Oman FIU (NCFI)** — `ncfi.gov.om` does not resolve; no public site found to monitor.
- **FSA Oman as a dated-alert source** — reachable after the TLS fix, but no verified
  dated regulatory listing exists: only a JS news widget and a POST-driven legislation
  search app.
- **FATF (fatf-gafi.org)** — 403 on every endpoint including the RSS, from both WebFetch
  and curl with a Chrome UA. Mitigation that matters: for a UAE-licensed firm the
  *enforceable* trigger is the MoET high-risk-country circular, and those are **already
  in our registry**.
- **QFMA (Qatar)** — no verifiable enforcement channel: the documented disciplinary URL
  404s, the live committee page lists no decisions, the news page is JS-loaded.
- **CBUAE enforcement page** and **DFSA alerts** — 403 from this network. Both already in
  the registry; whether prod (with the egress proxy) gets 200 needs checking, because
  CBUAE enforcement is where AML fines are published.

---

## 8. State

- Registry: 464 rows, 140 enabled. 21 rows locally certified today; **zero
  customer-visible rows changed** (138 `fresh_alert` + `alert_eligible`, unchanged).
- `ruff` clean. Full suite: no new failures attributable to this cycle; the delegation's
  four blast-radius files (`test_source_intake`, `test_adapter_platform`,
  `test_vara_source_depth`, `test_difc_source_remediation`) are green.
- **Owner action to convert this into customer-visible coverage:** a prod `mass-monitor
  --save-proof` run over the locally-certified rows. That produces the saved proof the
  promotion gate requires; local runs deliberately cannot.
