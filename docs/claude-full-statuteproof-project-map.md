# StatuteProof Full Project Map

> Verified 2026-06-15 by direct code/config/config reading. All counts are live
> measurements, not estimates. Validation run: 188 tests pass, 9 validators pass.
> Worktree has 3 uncommitted tool files (uae50_batch_nosave.py, uae50_activate.py,
> uae50_apply_activation.py).

---

## 1. Executive Summary

StatuteProof is a Python + React web application that monitors configured public
official regulatory sources, detects text changes using hash-based comparison,
stores cryptographic evidence records, and produces compliance monitoring briefs
for human review. It is not an AI lawyer, a compliance certifier, or a regulator
partner. Its first market is UAE-regulated firms (MLROs, CCOs, compliance officers
at CBUAE/DFSA/ADGM/VARA/SCA/FIU-regulated entities).

---

## 2. Product Explanation

### What it does today
- Fetches configured official UAE regulatory web pages (HTML + Playwright JS, PDFs,
  document listings, custom-element pages, rulebooks) on a schedule.
- Computes normalized text hashes to detect changes.
- Stores snapshots, proof artifacts, and diff records on each run.
- Certifies sources as monitoring-ready only after repeat baseline + agent gates.
- Exposes a web UI for source management, Source Lab testing, evidence review.
- Delivers Telegram alerts (operator-configured) when monitored change is detected.
- Allows users to add custom public URLs via Source Lab and `/api/custom-sources/`.

### What it does NOT do
- Not a legal adviser, compliance certifier, or regulator partner.
- Does not bypass login/CAPTCHA/paywalls.
- Does not process private, personal, or non-public data.
- Does not guarantee that all regulatory changes are captured.
- Does not make autonomous compliance decisions.
- Does not handle billing/payment (UI exists, not wired).

### Legal safety boundary
Approved: "official-source regulatory monitoring", "source-backed compliance
briefs", "monitoring information only", "not legal advice".
Forbidden: see Section 18.

---

## 3. Current Source Truth (measured)

Measured from `product/regradar/sources.json` (jurisdiction="AE"):

| Metric | Count |
|--------|-------|
| Total AE entries | 28 |
| Enabled | **19** |
| Status: active | **15** |
| Status: remediation | 4 |
| Status: disabled_navigation_only | 3 |
| Status: disabled_external_access | 3 |
| Status: duplicate_url | 3 |

**Active sources** (15):
1. Central Bank of UAE — `centralbank.ae/`
2. VARA — `vara.ae/`
3. DFSA MLRO Letters — `dfsa.ae/what-we-do/aml-ctf.../`
4. DFSA AML Rulebook Module — Thomson Reuters official link
5. ADGM main — `adgm.com/fsra`
6. ADGM Financial/Cyber Crime — `adgm.com/operating-in-adgm/financial-and-cyber...`
7. ADGM Rules and Regulations — `adgm.com/legal-framework/rules-and-regulations`
8. ADGM Public Consultations — `adgm.com/legal-framework/public-consultations`
9. UAE Ministry of Finance — `mof.gov.ae/`
10. UAE Legislation Portal — `uaelegislation.gov.ae/`
11. SCA Circulars, Rules and Procedures — `sca.gov.ae/en/regulations/circulars...`
12. UAE Ministry of Economy — `moet.gov.ae/en/`
13. VARA Enforcement Notices — `vara.ae/en/enforcement/`
14. CBUAE Regulations — `centralbank.ae/en/regulations/`
15. UAE FIU Circulars and Notices — `uaefiu.gov.ae/en/Publications/`

**Remediation** (4):
- DFSA main — selector issue
- UAE FIU main homepage — extraction quality
- DIFC Laws and Regulations — JS rendering issue
- DFSA Regulatory Notices — selector issue

**Work queue** (`config/uae_source_work_queue.json`, 78 entries):
- activation_ready: 3 | baseline_pending: 5 | blocked: 21 | remediation: 21 | candidate: 28

---

## 4. Interface / Pages

### Public views (landing site)

| Route | File | Content |
|-------|------|---------|
| `/` | Landing.jsx / Hero.jsx | Product description, features, CTA |
| `/pricing` | Pricing.jsx | 3 plans: Free readiness review, $199 pilot, $399/mo UAE Monitor |
| `/source-readiness-review` | SourceReadinessReviewPage.jsx | Source readiness table (mock data) |
| `/login` `/register` | auth/ components | Real auth against backend DB |
| `/terms` `/privacy` `/disclaimer` | LegalPage.jsx | Legal pages |

### App pages (authenticated, `/app/*`)

| Route | File | Backend? | Description |
|-------|------|----------|-------------|
| `/app/dashboard` | DashboardHome.jsx | **MOCK** | Source health table, risk trend chart — uses `mockData.js` |
| `/app/sources` | SourcesPage.jsx | **MOCK** | Sources list — uses `mockData.js` not `sources.json` |
| `/app/source-lab` | SourceLabPage.jsx | **REAL** | Form: URL+options → discover → test → save. Calls real API |
| `/app/sources/new` | → SourceLabPage.jsx | **REAL** | Same as source-lab |
| `/app/evidence` | EvidencePage.jsx | **Partial** | Reads real `source_runs.jsonl` via GET /api/evidence |
| `/app/alerts` | AlertsPage.jsx | **Partial** | Reads real alert queue |
| `/app/briefs` | AIBriefPage.jsx | **Partial** | Shows generated briefs |
| `/app/reports` | ReportsPage.jsx | **Mock** | Static sample reports |
| `/app/integrations` | IntegrationsPage.jsx | **Partial** | Telegram setup wired |
| `/app/billing` | BillingPage.jsx | **Mock** | No payment processing |
| `/app/settings` | SettingsPage.jsx | **Partial** | Profile, Telegram settings |

**Key gap**: Dashboard and Sources page display `mockData.js` — not live data from
sources.json or source_runs.jsonl. A user logging in sees static sample data,
not their real monitoring state.

### "Add any website" feature (Source Lab)

**This feature is real and working** when the API server runs (`python run.py api`):
1. `/app/source-lab` form: URL, name, jurisdiction, adapter config, legal checkbox.
2. "Discover" → `POST /api/custom-sources/discover` → runs real `discover_source()`.
3. "Test" → `POST /api/custom-sources/test` → runs real `run_source_intake(write_evidence=False)`.
4. "Save" → `POST /api/custom-sources` → validates URL, re-tests, saves to `sources.json`
   with `custom:true, enabled:false, status:pending_validation`.
5. **Gap**: the manual activation review (run baseline, enable, gate) has no frontend;
   it's done via CLI. An "Admin review panel" on the Sources page would complete this.

---

## 5. Backend Architecture

53 Python modules in `product/regradar/app/`. Key ones:

### Source intake pipeline
- **`source_intake.py`** — core function `run_source_intake(source, write_evidence)`.
  Fetches URL (bs4 or Playwright), applies adapter, runs quality checks, optionally
  writes evidence. Returns rich dict: status, quality_score, normalized_hash,
  can_save_evidence, failure_code, dom_investigation, adapter metadata.
- **`source_quality.py`** — quality scoring, nav-shell detection, shallow content,
  duplicate hash, noise_risk, source_health_risk classification.
- **`text_normalization.py`** — normalize HTML → stable text for hash comparison.

### DOM intelligence
- **`dom_investigator.py`** — given Playwright-rendered HTML, detects page type
  (listing/table/rulebook/document), recommends adapter family and selectors,
  classifies nav-shell risk and noise risk. Returns JSON with `recommended_adapter_name`,
  `content_selector`, `item_selector`, `wait_selector`, `selector_confidence`.

### Discovery
- **`source_discovery.py`** — given a base URL, discovers: sitemap URLs, RSS/Atom feeds,
  robots.txt, related regulatory page links, PDF documents, public API endpoints.
  Used by `POST /api/custom-sources/discover`. Never writes evidence.

### Adapters (`app/adapters/`)
- **`adapter_platform.py`** — 13 adapter families:
  `static_html`, `playwright_selector`, `custom_element`, `listing`, `table`,
  `pdf_document`, `pdf_listing`, `rulebook`, `document_listing`, `register`,
  `sitemap_feed`, `public_json_api`, `rendered_dom_evidence`.
  Source-specific: `sca_listing`, `dfsa_rulebook`, `dfsa_notice_listing`,
  `cbuae_document_listing`, `adgm_fsra_listing`, `fiu_eocn_document_listing`,
  `vara_pdf_listing`. Plus `uae_cbuae_rulebook.py`, `uae_fsra_circulars.py`.
- Adapters take Playwright-rendered HTML, apply CSS selectors, extract item titles/
  dates/links, produce stable hashes at item level, filter nav/footer noise.

### Evidence trail
- **`source_runs.py`** — `append_run(record)` → persists to `source_runs.jsonl`.
  Writes snapshots (raw, normalized, PDF text), proof artifact, diff artifact.
  Runs keyed by source_id; baseline count = successful runs per source.
- **`proof.py`** — builds `proof.json` artifact: source URL, timestamp, hash,
  quality score, evidence level, extraction warnings, chain of custody.
- **`source_certification.py`** — `build_certification_from_runs()` counts successful
  runs → `BASELINE_PENDING` (1 run) → `MONITORING_CERTIFIED` (≥2 runs).
  Proof paths returned for validator enforcement.

### Hash + diff
- **`chunk_diff.py`** — item-level diff between baseline and current run. Produces
  structured diff JSON + Markdown for brief generation.
- **`text_normalization.py`** — `stable_normalized_hash()` is the canonical
  change-detection hash. Normalized text strips nav boilerplate.

### Mass activation
- **`mass_source_activation.py`** — gate-evaluation library. Evaluates each queue
  entry against pass criteria. Builds compliant queue entries with all required
  schema fields. Does NOT run live fetches.
- **`mass_source_activation_runner.py`** — safe batch runner. Reads queue, filters
  by activation_decision/state, calls `run_source_intake` per source, records
  results. Skips candidate/blocked/rejected by default. Has dry-run mode.
- **`mass_monitoring_runner.py`** — runs monitoring for `enabled:true` sources in
  `sources.json`. MONITOR_OK / NEEDS_ATTENTION / BLOCKED per source. Has
  `--dry-run --no-alerts --activation-ready-only` flags.

### API server
- **`api.py`** — pure Python `http.server.HTTPServer` (no FastAPI/Flask dependency).
  20+ endpoints. Key custom-source endpoints are live and wired to real intake.
  Start: `python run.py api` (listens on `127.0.0.1:5001`).

### Supporting modules
- `auth.py` / `db.py` — user auth, SQLite sessions.
- `telegram.py` / `telegram_clients.py` — alert delivery via Telegram Bot API.
- `ai.py` / `ai_brief.py` — brief generation (requires API key in env).
- `scheduler.py` — cron-style run scheduling.
- `monitor.py` / `pipeline.py` — monitoring orchestration.
- `scraper.py` / `extractors.py` — low-level fetch/HTML extract.
- `weekly_brief.py` / `report.py` — weekly status generation.

### CLI (`run.py`)
Key commands (53 total): `url`, `all`, `source-lab`, `investigate-source`,
`discover-source`, `source-discovery-lab`, `mass-source-activate`, `mass-monitor`,
`test-source`, `source-readiness`, `source-audit`, `source-history`,
`backfill-artifacts`, `alert-queue`, `weekly-brief`, `adapter-research`,
`source-diff`, `api`, `demo`, `health`, `coverage`, and more.

---

## 6. Folder-by-Folder Map

```
StatuteProof-Command-Center/
├── CLAUDE.md                 — Project rules, agent routing, forbidden claims
├── TOOL_ROUTER.md            — Which agent/skill to use for each task
├── AGENTS.md                 — Agent roster reference
├── product/regradar/         — Main product
│   ├── app/                  — 53 Python backend modules
│   ├── app/adapters/         — Adapter platform + source-specific adapters
│   ├── web/src/              — React/JSX frontend (13440 files incl. node_modules)
│   │   ├── components/app/   — 16 app page components
│   │   ├── components/       — 30+ shared components
│   │   ├── data/mockData.js  — Static mock data (Dashboard, Sources use this)
│   │   └── routeMap.js       — All routes/pages defined here
│   ├── sources.json          — 156 sources total, 19 AE enabled
│   ├── config/               — Work queues, candidate registries
│   │   ├── uae_source_work_queue.json      — 78-entry gated queue (activation_ready=3)
│   │   ├── uae_source_candidates.json      — 63 candidates + 6 rejected
│   │   ├── mass_source_activation_queue.json — 14-entry activation queue
│   ├── data/source_runs/     — source_runs.jsonl (220 AE run records)
│   ├── data/source_snapshots/— Proof artifacts per run
│   └── tests/                — 17 test files, 188 tests
├── agents/                   — 10 agent system-prompt docs
├── .claude/agents/           — 10 Claude Code subagent definitions
├── .agents/skills/           — 60+ skill definitions (SKILL.md per skill)
├── skills/                   — Human-readable skill docs
├── docs/                     — 100+ documentation/report files
├── tools/                    — 9 validators + 3 new activation helpers
│   ├── validate_*.py         — 9 strict validators (all passing)
│   ├── uae50_batch_nosave.py — NEW: batch no-save harness with auto adapter
│   ├── uae50_activate.py     — NEW: evidence save + repeat baseline helper
│   └── uae50_apply_activation.py — NEW: gated sources.json applier
├── workflows/                — Step-by-step workflow docs
└── prompts/                  — Prompt templates for agents
```

---

## 7. Source Monitoring Pipeline (end to end)

```
1. CANDIDATE DISCOVERY
   discover_source(url) → sitemap / robots / feeds / links / PDFs / API endpoints
   Files: source_discovery.py, dom_investigator.py

2. DOM INVESTIGATION
   dom_investigator.py → page type, recommended adapter, selectors, nav-shell risk
   Inputs: Playwright-rendered HTML, URL
   Outputs: recommended_adapter_name, content_selector, item_selector, wait_selector

3. NO-SAVE SOURCE LAB TEST
   run_source_intake(source, write_evidence=False)
   Pass criteria: status=CONFIRMED_ACCESSIBLE, quality_score≥60, meaningful_content=True,
   nav_shell=False, duplicate_hash=False, can_save_evidence=True
   Failure codes: NAV_SHELL_ONLY, LIKELY_WAF_403, JS_REQUIRED, LISTING_ADAPTER_REQUIRED, etc.

4. EVIDENCE SAVE (run 1)
   run_source_intake(source, write_evidence=True)
   → append_run(record) → source_runs.jsonl
   → _write_snapshots() → data/source_snapshots/{date}/{AE}/{source_id}/
   → _write_proof_artifact() → proof.json

5. REPEAT BASELINE (run 2+)
   Second call to run_source_intake(write_evidence=True) with same source_id
   build_certification_from_runs() → MONITORING_CERTIFIED after 2 successful runs

6. MASS-MONITOR DRY-RUN
   python run.py mass-monitor --activation-ready-only --dry-run --no-alerts
   MONITOR_OK required → no change_detected false alarm, stable hash

7. AGENT GATES (6 gates, emulated manually)
   Source Monitor: official? correct URL? meaningful extraction? source-health ok?
   Evidence Trail: proof_path exists? hash? baseline complete? evidence meaningful?
   QA/Critic: no fake-ready? no nav-shell? no dup hash? no high noise?
   Legal Language: no legal advice? no guarantee? wording safe?
   Product Manager: useful to MLRO/CCO? not vanity padding?
   Code Architect: adapter stable? maintainable? no unsafe deps?

8. SOURCES.JSON ACTIVATION
   Add with enabled:true, status:active, source_id, adapter metadata, proof_path
   Truth counters recomputed, validators run

9. MONITORING LOOP
   mass_monitoring_runner.py processes enabled sources
   Hash comparison → MONITOR_OK / NEEDS_ATTENTION / BLOCKED
   On change: diff artifact → alert_queue → Telegram delivery

10. BRIEF ELIGIBILITY
    No brief without monitored change evidence
    brief = diff excerpt + source citation + standard disclaimer
```

**Anti-fake guards at every stage:**
- `validate_uae_50_working_sources.py` requires proof_path + completed baseline + 6 gates pass
- Sources.json can only be updated when all gates pass
- nav_shell / duplicate_hash / high noise_risk each block activation
- No claim of "50 working sources" until validator confirms

---

## 8. Source Discovery / DOM Investigator / Adapter System

### Source Discovery (`source_discovery.py`)
- Checks sitemap.xml, robots.txt, RSS/Atom feeds, known regulatory URL patterns.
- Discovers PDF document links, public JSON endpoints (XHR/network discovery).
- Returns candidates ranked by relevance. Never activates automatically.

### Auto DOM Investigator (`dom_investigator.py`)
- Loads Playwright-rendered HTML, scans for listing patterns (article, li, tr, .card).
- Detects: listing / table / rulebook / document / register / custom-element page types.
- Returns: `selector_confidence` (0–100), recommended adapter, selectors, nav-shell risk.
- Key output: if `selector_confidence ≥ 70` → usually reliable for listing adapter.

### Adapter Platform (`adapters/adapter_platform.py`)
13 generic families + 7 source-specific. Each adapter:
- Takes BeautifulSoup HTML object + config dict.
- Applies container_selector → isolates content area.
- Applies item_selector → extracts item titles, dates, links.
- Produces stable per-row hashes + listing-level hash.
- Filters nav/footer/search/form noise.
- Returns `AdapterResult` with items, content text, hash, warnings.

Source-specific adapters with hardcoded selectors:
- `ScaListingAdapter` — SCA website card/listing extraction
- `DfsaRulebookAdapter` / `DfsaNoticeListingAdapter` — DFSA
- `CbuaeDocumentListingAdapter` — CBUAE document pages
- `AdgmFsraListingAdapter` — ADGM custom element pages
- `FiuEocnDocumentListingAdapter` — UAE FIU/EOCN
- `VaraPdfListingAdapter` — VARA PDF listings

---

## 9. Evidence Trail / Proof System

**Artifacts written per successful run** (to `data/source_snapshots/{date}/{AE}/{source_id}/`):
- `raw.html` / `rendered.html` — raw or Playwright-rendered page
- `normalized.txt` — boilerplate-stripped, hash-stable text
- `metadata.json` — URL, adapter, timestamp, quality score
- `diff.json` / `diff.md` — structured diff vs previous run
- `proof.json` — chain-of-custody record: hash, timestamp, evidence level,
  quality score, source_id, source_url, extraction warnings

**`source_runs.jsonl`** — append-only ledger. Each line = one run record with:
source_id, run_id, timestamp_utc, normalized_hash, proof_block_path, change_status,
access_status, quality_score, fetch_method, adapter_name.

**Certification states**: `CERTIFICATION_FAILED` → `TEST_PASSED` → `BASELINE_PENDING`
(1 run) → `MONITORING_CERTIFIED` (≥2 runs with proof) → `MONITORING_READY` (contract
allows activation).

---

## 10. Mass Activation / Mass Monitoring System

### Queue states (`uae_source_work_queue.json`)
- `candidate` — identified, not yet tested
- `remediation` — tested, adapter/selector needs improvement
- `blocked` — tested, WAF/403/nav-shell, not currently fixable
- `baseline_pending` — strong no-save pass, evidence saved, awaiting 2nd baseline
- `activation_ready` — all gates passed, proof + baseline complete, ready for sources.json
- `rejected` — not a suitable source (garbage, dupe, private)

### `mass_source_activation_runner.py`
- Reads queue, filters to `activation_ready` entries.
- Calls `run_source_intake` per source (no-save by default, or with evidence).
- Records results back to queue. Safe batch mode: limit, regulator filter, dry-run.

### `mass_monitoring_runner.py`
- Reads `sources.json` enabled sources.
- Fetches each, computes hash, compares to previous run via `source_runs.py`.
- Returns per-source: `MONITOR_OK`, `NEEDS_ATTENTION`, `BLOCKED`, `QUALITY_DROP`.
- `--dry-run --no-alerts`: no evidence written, no Telegram, reads only.
- `--activation-ready-only`: skips candidate/remediation/blocked.

---

## 11. Agents and Skills

### 10 agents (no 11th may be added)

| Agent | File | Purpose |
|-------|------|---------|
| Chief of Staff | `agents/chief-of-staff.md` | Routing coordinator for multi-agent tasks |
| Product Manager | `agents/product-manager.md` | ICP clarity, MVP scope, relevance gate |
| Code Architect | `agents/code-architect-dev.md` | Implementation, schemas, safe code gate |
| QA / Critic | `agents/qa-critic.md` | Red-team, fake detection, ship/no-ship |
| Legal Language | `agents/legal-language.md` | Forbidden claim detection, safe wording |
| Source Monitor | `agents/source-monitor.md` | Source config, fetch, hash, alerts |
| Evidence Trail | `agents/evidence-trail.md` | Proof paths, hashes, baseline, integrity |
| Risk + Brief Pipeline | `agents/risk-brief-pipeline.md` | Risk scoring, brief drafting (evidence-first) |
| ICP Lead Research | `agents/icp-lead-research.md` | B2B prospect research |
| Outreach Writer | `agents/outreach-writer.md` | Outbound copy, only after evidence + QA |

In `.claude/agents/` there is a corresponding subagent definition for each.

### Skills (60+ in `.agents/skills/`)

Key source-monitoring skills:
- `source-monitoring-review` — review a source configuration
- `evidence-readiness-review` — check evidence completeness
- `custom-source-parser` — design parser for a new source type
- `custom-source-monitoring-spec` — spec a new source monitoring setup
- `evidence-audit` — audit evidence records
- `systematic-debugging` — debug extraction failures
- `verification-before-completion` — gate before claiming done
- `prompt-injection-review` — check skills for injection risk

From `mattpocock/skills` (MIT), adopt patterns for: TDD workflow into new adapter
development, systematic debugging into source remediation, PRD template for admin
review panel feature.

---

## 12. Config / Data Registries

| File | Purpose | Key schema | Current state |
|------|---------|------------|---------------|
| `sources.json` | Master source registry | name, url, jurisdiction, enabled, status | 156 total, 19 AE enabled |
| `uae_source_work_queue.json` | Gated activation tracking (78 entries) | All 35 fields per source + 7 gates | 3 activation_ready |
| `uae_source_candidates.json` | Research candidate registry (63 entries) | source_id, regulator, url, status, next_action | 63 candidates |
| `mass_source_activation_queue.json` | Mass activation subset (14 entries) | Similar to work queue | 14 entries |
| `source_runs.jsonl` | Append-only run ledger | source_id, hash, proof_path, change_status | 220 AE records |

---

## 13. Tests and Validators

### Tests (`product/regradar/tests/`, 188 passing)

| File | Coverage |
|------|---------|
| `test_adapter_platform.py` | Adapter extraction, hash stability, nav filtering |
| `test_source_intake.py` | Intake pipeline, quality gate, evidence schema |
| `test_source_quality_policy.py` | Nav-shell, shallow, duplicate hash detection |
| `test_mass_source_activation.py` | Queue gate evaluation |
| `test_mass_source_activation_runner.py` | Safe batch runner behavior |
| `test_mass_monitoring_runner.py` | Monitor runner, MONITOR_OK logic |
| `test_dom_investigator.py` | DOM investigator recommendations |
| `test_source_discovery_engine.py` | Discovery candidate generation |
| `test_chunk_diff_and_proof.py` | Diff artifacts, proof generation |
| `test_parser_benchmark_suite.py` | Parser quality benchmarks |
| Others | Alerts, auth, report, text normalization |

**Gap**: all tests use fixtures (no live network in unit tests — correct design).
Missing: end-to-end API integration tests, test that Sources page is wired to real
data (currently would pass even with mock data because there is no such test).

### Validators (9 passing)

| Validator | What it enforces |
|-----------|-----------------|
| `validate_uae_50_working_sources.py` | No "50 sources" claim without proof+baseline+gates |
| `validate_uae_source_pack.py` | Truth string matches sources.json |
| `validate_mass_source_activation_pipeline.py` | Queue schema integrity |
| `validate_mass_monitoring_runner.py` | Runner skips unsafe states |
| `validate_source_activation_pipeline.py` | DOM investigator, Source Lab fields present |
| `validate_source_discovery_engine.py` | Generated candidates stay inactive by default |
| `validate_parser_quality.py` | No fake-ready claims, sample brief guard |
| `validate_workspace.py` | File structure, forbidden claim check |
| `validate_codex_skills.py` | 8 required skills present in `.agents/skills/` |

---

## 14. Docs and Reports

Over 100 documents in `docs/`. Key ones verified current:

| Doc | Current? | Content |
|----|---------|---------|
| `uae-50-continuous-activation-war-room-plan.md` | Current (updated today) | Sprint plan |
| `uae-50-current-gap-inventory.md` | Current | 19/15/4 truth, candidate breakdown |
| `docs/parser-quality-gates.md` | Current | Quality gate definitions |
| `docs/no-garbage-source-policy.md` | Current | What counts as a useful source |
| `docs/source-onboarding-pipeline-spec.md` | Current | Pipeline spec |
| `docs/forbidden-phrases-reference.md` | Current | Forbidden/approved wording table |

Stale: many prior-sprint reports with old truth numbers (16/12/4 or earlier). They
are historical records, not operational truth — the validators and `sources.json` are
the live truth.

---

## 15. Real vs Mock vs Planned

| Feature | Real runtime? | Mock/demo? | Planned? |
|---------|--------------|------------|---------|
| Source Lab (test any URL) | ✅ Real | — | — |
| Custom-source discover + add via API | ✅ Real | — | — |
| Evidence save + proof artifacts | ✅ Real | — | — |
| Repeat baseline + certification | ✅ Real | — | — |
| Mass-monitor runner | ✅ Real | — | — |
| Auth (register, login) | ✅ Real | — | — |
| Adapter platform (13 families) | ✅ Real | — | — |
| DOM investigator | ✅ Real | — | — |
| Source discovery engine | ✅ Real | — | — |
| Telegram alert delivery | ✅ Wired | — | Config required |
| Dashboard source counts | ❌ Mock | mockData.js | Wire to sources.json |
| Sources page list | ❌ Mock | mockData.js | Wire to API |
| AI briefs | Partial | — | Requires API key + real diff |
| Billing / payment | ❌ Mock | — | Not implemented |
| Customer-facing brief delivery | Partial | — | Requires Telegram + human review |
| Admin review panel for custom sources | ❌ Missing | — | Planned (highest value gap) |

---

## 16. Current Blockers

1. **JS-heavy SPAs** — CBUAE, FIU homepage, DFSA main site, VARA main produce
   nav-shell without a precise adapter. Per-source adapter tuning is required.
2. **WAF / 403** — some CBUAE subpages return 403; not bypassed (documented).
3. **Duplicate endpoint candidates** — several candidate entries point to pages
   already in sources.json (deduplication needed in discovery).
4. **Frontend mock data** — Dashboard and Sources page show static data, not live.
5. **Custom source activation gap** — users can add URLs but no UI for the admin
   baseline + activation review step.
6. **50-source goal** — 31 more active sources needed; current live batch (30/49
   tested) finding ~4–6 strong passes per 30 tested with per-adapter approach.

---

## 17. Why Not at 50 Sources

The last full no-save sweep (2026-06-14, 24 tested) passed **0** under generic
extraction. The root cause: most UAE official sites use JavaScript-rendered SPAs
or custom web components that produce only navigation menu text (~850 chars) when
extracted generically. The adapters are built but require per-source configuration
that the old sweep did not apply.

With the per-adapter harness built today: 30/49 tested, ~4–6 strong passes. At
this hit rate (~15%), the 49 testable candidates would yield ~7–10 additional
genuine sources, reaching ~26–29. Remaining gap to 50 requires new endpoint
discovery (deeper ADGM/SCA/FIU/VARA subpages, FSRA specific pages, additional
regulators like EOCN, UAE Ministry of Justice, FTA).

Specific per-regulator blockers:

| Regulator | Blocker |
|-----------|--------|
| SCA | 9 candidates; circulars pass with sca_listing; decisions/regulations need selector tuning |
| CBUAE | WAF on some endpoints; 10 candidates; document_listing may work |
| DFSA | Thomson Reuters rulebook linked externally works; DFSA.ae main is nav-shell |
| ADGM/FSRA | Custom elements work; 8 candidates; most already active or activation_ready |
| VARA | 8 candidates; PDF listings may pass; main site nav-shell |
| UAE FIU | 5 candidates; Publications page (active); others need document_listing adapter |
| DIFC | 4 candidates; JS-heavy; nav-shell; remediation |
| FTA | 3 candidates; public but low MLRO/CCO buyer value |

---

## 18. Forbidden Claims

Never write or imply:
- guarantee compliance / prevent fines / avoid all penalties
- replace lawyers / MLROs / compliance officers
- 100% accurate / never miss an update / stay compliant automatically
- official partner of any regulator / certified by any regulator
- 50/60 working sources (until validator proves it)
- any website can be parsed / perfect parsing
- legal advice / regulatory advice / compliance certification

---

## 19. Open-Source / Internet Ideas (mattpocock/skills + broader)

### mattpocock/skills (MIT) — adopt patterns, not code
- TDD skill → use test-first approach when building new source adapters.
- Systematic debugging → already implemented as `systematic-debugging` skill; ensure it's used for every new source failure.
- PRD generation → write a product spec for the "Admin review panel" feature.
- Session handoff pattern → document current activation state in CLAUDE.md for continuity.

### Extraction improvements (ideas to evaluate)
| Tool | Idea | Risk |
|------|------|------|
| trafilatura | Better boilerplate removal than bs4 | Try in no-save mode first |
| selectolax | Faster CSS selector parsing than bs4 | Low risk, consider for speed |
| Crawl4AI | Playwright + structured extraction in one | Evaluate license + deps |
| pdfplumber | Better PDF table extraction than pymupdf in some cases | Already using pymupdf |
| feedparser | RSS/Atom feed following | Useful for circulars RSS if available |
| changedetection.io | Reference design for change detection UX | Ideas only, not to vendor |
| Playwright CDP | XHR/network request interception for SPA JSON endpoints | High value for JS portals |
| htmldate | Date extraction from pages | Useful for circular/notice date parsing |

Do NOT vendor large dependencies (Browsertrix, ArchiveBox, Firecrawl) without
clear license review and justified need. StatuteProof's pipeline is already solid;
targeted improvements to specific adapter families are preferred over wholesale
replacement.

---

## 20. One Best Next Task

**Wire the Sources page and Dashboard to real `sources.json` + `/api/sources/status`
data**, removing the `mockData.js` dependency.

This is the highest-visibility gap: a real user logging in sees static fake data.
Fixing it requires:
1. Connect `SourcesPage.jsx` to `GET /api/sources/status` (endpoint exists).
2. Connect `DashboardHome.jsx` source health table to the same endpoint.
3. Show real source counts (19 enabled / 15 active / 4 remediation).
4. Preserve mock data as the fallback if API is unreachable.

After this, the "add any website" Source Lab flow closes the full circle: user adds
URL → tests it → sees it in Sources list → admin activates after review.

---

*Standard disclaimer: StatuteProof reports are provided for information and
compliance review support only. Not legal advice. Not a guarantee of compliance.*
