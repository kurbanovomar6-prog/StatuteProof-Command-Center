# Source URL Stability Watch — DFSA frozen-version repoint + SCA→CMA transition

Date: 2026-07-12. Branch: `tenten`. All observations below were verified by direct
fetch from the dev machine on 2026-07-12 unless stated otherwise.

## 1. DFSA AML rulebook module — frozen-version URL repointed

**Problem.** `AE-dfsa-aml-rulebook-module` (enabled, fresh_alert, Tier A) was pinned to

```
https://dfsaen.thomsonreuters.com/rulebook/anti-money-laundering-counter-terrorist-financing-and-sanctions-module-aml-ver3004-26
```

Thomson Reuters `…-verNNNN-NN` paths are frozen snapshots. The page title confirms it:
`… Module (AML) [VER30/04-26]`. When the DFSA next amends the AML module, the canonical
URL moves to VER31 while the frozen URL keeps serving VER30 forever — the monitor would
report UNCHANGED indefinitely and silently miss real changes.

**Verified state on 2026-07-12:**
- Frozen URL: HTTP 200, no redirect, title `[VER30/04-26]`.
- Canonical URL (no `-ver` suffix): HTTP 200, title without any VER tag.
- The rulebook-modules index sidebar shows AML current version IS `VER30/04-26` today,
  so content has not diverged yet — but other modules already carry July 2026 versions
  (GEN VER72/07-26, COB VER51/07-26, AUD VER11/07-26, GLO VER66/07-26, PIB VER53/07-26),
  proving amendments are actively landing on this platform.

**Fix (sources.json):** URL repointed to the canonical current-version page:

```
https://dfsaen.thomsonreuters.com/rulebook/anti-money-laundering-counter-terrorist-financing-and-sanctions-module-aml
```

**REQUIRED AFTER DEPLOY — rebaseline.** The page chrome/title differ between the two
URLs, so the first sweep after this lands will compute a different normalized hash and
fire a spurious CHANGED. On the deployment that owns the baseline, before the next
scheduled sweep, run:

```
python run.py rebaseline --source-id AE-dfsa-aml-rulebook-module
```

This is the documented single-source primitive (`app/source_runs.py::rebaseline_source`):
it reuses the monitor fetch/extract path, refuses empty/undecodable content, writes a
FIRST_SEEN baseline, never alerts, and needs no scheduler stop.

**Guard test added:** `tests/test_sources_validation.py::test_no_enabled_source_url_is_pinned_to_a_frozen_version`
asserts no ENABLED source URL matches `[-_/]ver\d` (case-insensitive). The 22 disabled
evidence-library entries with version-pinned URLs (VARA `_VERyyyymmdd.pdf`, MOET dated
PDFs) are deliberate snapshots and stay as they are.

## 2. SCA→CMA transition — tombstone watch (through 2027-01-01)

**No legacy `sca.gov.ae` URLs are configured.** All `AE-sca-*` sources already point at
`uaecma.gov.ae`; the run trail shows the migration happened earlier (an old run for
`AE-sca-regulations-listing` still records `https://www.sca.gov.ae/en/regulations/regulations-listing`).

**Live tombstone found:** `AE-sca-circulars-rules-procedures` (enabled, fresh_alert)
points at `https://www.uaecma.gov.ae/en/regulations/circulars-and-procedures.aspx`,
which now returns `302 → /404.aspx?aspxerrorpath=…` and lands on `/en/home`. The
pipeline is therefore hashing the homepage/nav shell; its recent UNCHANGED runs are NOT
evidence the circulars listing is unchanged. Probed alternates
(`…/circulars-and-procedures`, `…/circulars.aspx`, `…/circulars`) all 302 to 404.
`/en/regulations` and the other five enabled CMA paths still serve HTTP 200 directly:
regulations-listing, FATCA/CRS, corporate-governance, AML/CFT, fintech-sandbox.

**Decision:** source kept enabled (transition-watch policy, do not delete), tombstone
documented in its `notes`. Follow-up (M effort): discover the new circulars path with
Playwright (uaecma.gov.ae is a JS SPA — plain fetch exposes only 6 hrefs), repoint,
then rebaseline. Re-check all six CMA paths periodically until the transition completes
(2027-01-01).

## 3. DFSA 403 claim — refuted for the real pipeline path

curl (any User-Agent) gets HTTP 403 on most `www.dfsa.ae` paths (`/laws-rules`,
`/what-we-do/enforcement`, `/your-resources/…` — 11 of 12 probed; `/news` serves 200).
This is TLS/client fingerprinting by the WAF, not a UA block. The app's actual fetch
path (python-requests + `REQUESTS_UA` from `app/config.py`) gets HTTP 200 on the same
URLs, and production run logs (`data/source_runs/source_runs.jsonl`, through 2026-07-05)
show zero 403s for any DFSA source — all runs `accessible`/successful extraction.
**No browser adapter is needed for DFSA.** If a future dependency swaps the HTTP client
(e.g. to a curl-based transport), DFSA sources will start failing — keep this in mind.
