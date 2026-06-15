# StatuteProof — Executive Summary for Founder

> Verified 2026-06-15. All numbers and claims grounded in live code/config reading.
> Validation: 188 tests pass, 9 validators pass, worktree has 3 new tool files (uncommitted).

---

## What the system does

StatuteProof monitors selected **public official regulatory sources** (UAE-first),
detects text changes, stores cryptographic evidence records, and produces
**monitoring briefs for human review**.

Core promise (exact, legally safe):
> "StatuteProof can test and monitor public official or officially linked sources
> that are technically accessible and permitted to be monitored. It shows
> extraction quality, evidence readiness, hashes, diffs, activation readiness,
> source-health risk, noise risk, and failure reasons clearly."

It is **not** a legal adviser, compliance certifier, or regulator partner.

---

## What exists now (real and working)

### Backend (production-quality Python pipeline)

| Component | Status |
|-----------|--------|
| Source intake / Source Lab | **Real** — `run_source_intake()` runs live; bs4 + Playwright |
| Auto DOM Investigator | **Real** — detects page type, recommends adapter, selectors |
| Adapter platform (13 adapter families + SCA/DFSA/ADGM/FIU/VARA specific) | **Real** |
| Evidence save + proof artifacts (hashes, snapshots, proof.json) | **Real** |
| Repeat baseline certification (MONITORING_CERTIFIED after 2 runs) | **Real** |
| Mass-monitor runner (activation-ready only, dry-run/no-alerts mode) | **Real** |
| Mass source activation queue + gate system | **Real** |
| API server (`python run.py api`) — 20+ endpoints | **Real** |
| Custom-source discover + test + add (via API) | **Real** — wired to live intake |
| Auth (registration, login, sessions) | **Real** |
| 9 validators enforcing truth integrity | **Real** |
| 188 unit/fixture tests | **Real** |

### Frontend (React/JSX app)

| Page | Real backend? | Notes |
|------|--------------|-------|
| Source Lab (`/app/source-lab`, `/app/sources/new`) | **Yes — calls real API** | URL input → discover → test → save |
| Dashboard | **No — shows mock data** | Charts, source counts are from `mockData.js` |
| Sources page | **No — shows mock data** | Source list from `mockData.js`, not `sources.json` |
| Evidence page | **Partially** — GET /api/evidence reads real `source_runs.jsonl` | |
| Briefs/Alerts | **Partially** — reads real alert queue | Few real entries |
| Settings/Integrations/Billing | **Mock/partial** | Billing UI, Telegram wiring incomplete |

---

## Current source truth (verified from sources.json + validators)

```
28 enabled UAE sources / 24 active (readiness-supported) / 4 under remediation
```
*(Updated 2026-06-15 after SCA Regulations Listing activation — source-specific SCA listing adapter, MONITORING_CERTIFIED, hash stable, mass-monitor MONITOR_OK.)*

Active sources include CBUAE, VARA, DFSA subpages, ADGM/FSRA subpages, SCA
Circulars, UAE Ministry of Finance, UAE Legislation Portal, UAE Ministry of
Economy, VARA Enforcement, CBUAE Regulations, UAE FIU Circulars, EOCN AML/CFT
laws, ADGM RA Circulars, UAE FIU Trends and Typology Reports, EOCN News and
Sanctions Updates, and SCA Regulations Listing.

Remediation: DFSA main site, UAE FIU main, DIFC Laws, DFSA Regulatory Notices.

---

## What is missing

1. **Dashboard and Sources page show mock data** — not wired to `sources.json` or live runs.
2. **50 active UAE sources** — currently 28/24/4. Getting to 50 requires 22 more genuinely passing sources with real evidence + baselines. The live no-save batches show that per-source adapters work, but JS-heavy FIU/SCA/ADGM variants still need selector remediation.
3. **Alert delivery** — Telegram wiring exists but requires per-client setup.
4. **Billing** — not implemented; plan intents recorded but no payment processing.
5. **Custom-source activation UI** — adding a URL via Source Lab saves it as `enabled:false/pending_validation`; there is no UI for the manual review + activation step (done via CLI today).
6. **Dashboard live data wiring** — the largest UX gap visible to a real user.

---

## Is it ready for mass monitoring?

**Partially.** The monitoring engine is solid. For activation-ready/enabled sources, mass-monitor runs correctly in dry-run/no-alerts mode. For real alerts, Telegram delivery needs per-client configuration and the 50-source goal requires the ongoing activation work.

---

## The "add any website" feature — current state

**Fully implemented at the API and Source Lab UI level:**
1. User opens `/app/source-lab` or `/app/sources/new`.
2. Enters any public URL + optional name, jurisdiction, adapter settings.
3. Clicks "Discover" → calls `POST /api/custom-sources/discover` → real source discovery.
4. Clicks "Test" → calls `POST /api/custom-sources/test` → real no-save quality test.
5. If CONFIRMED_ACCESSIBLE + legal_confirmed → Clicks "Save" → calls `POST /api/custom-sources` → saved to `sources.json` with `custom:true, enabled:false, status:pending_validation`.
6. Manual admin step then reviews, runs repeat baseline, and enables if all gates pass.

**Gap**: step 6 (manual activation review) has no frontend UI. It's done via CLI commands today. Building a simple "Review & Activate" admin panel in `/app/sources` would complete the circle.

---

## mattpocock/skills — how it applies

`mattpocock/skills` (MIT) is a collection of structured AI agent skill prompts, not a UI library. Its patterns align with StatuteProof's own `.claude/agents/` + `.agents/skills/` system. Useful ideas:
- **TDD skill pattern** → apply to new adapter development.
- **Systematic debugging** → already implemented as `systematic-debugging` skill.
- **PRD generation** → useful for the "add any website" admin review panel feature spec.

No code to import; adopt patterns into existing skill files.

---

## Exact next task (one thing)

**Wire the Sources page and Dashboard to real `sources.json` + `source_runs.jsonl` data**, removing the mock dependency. This makes the product real-feeling for any logged-in user, and unblocks the "add any website" flow completion (users can see their added sources in the list once wiring is live).

Secondary: process the current batch results, activate genuine strong-pass sources (4+ more today), push truth to 23+.

---

## Forbidden claims (never say these)

- guarantee compliance / prevent fines / avoid all penalties
- we replace lawyers / MLROs / compliance officers
- 100% accurate / never miss an update / stay compliant automatically
- official partner of any regulator / certified by any regulator
- 50/60 working sources (until `validate_uae_50_working_sources.py` confirms it)
- any website can be parsed / perfect parsing

---

*Disclaimer: StatuteProof reports are for monitoring information only. Not legal
advice. Not a guarantee of compliance.*
