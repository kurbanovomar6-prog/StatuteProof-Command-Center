# RegRadar — Handoff

_Update this file whenever an agent finishes work and is about to be replaced._

---

## Current owner

Human (ready for next task)

---

## Latest known commit

Current branch HEAD after this handoff update. Run `git log --oneline -1` for the exact hash.

---

## Current project state

RegRadar landing page and app are feature-complete for first pilot conversations.
Contact queue recovery tools (`contact-queue` CLI) are in place.

**Backend:** Python stdlib HTTP server on port 5001. All sources compile clean. **98 active monitored sources across 16 markets** (added 8 HK + 2 AE + 9 QA + 12 BH + 11 MY sources; SA revalidated). Health run completed 2026-05-27: PASS 96 · WARN 2 · SKIP 42 · FAIL 0. Overall coverage: 69 → **90** (+21 points). Commercial priority markets now have refreshed scores, with limitations preserved: AE 100 strong, HK 94 strong, QA 100 limited, BH 88 strong, MY 92 strong, SA 100 limited, SG 100 strong, TR 100 strong, KZ 100 strong. `/api/contact` queues prospect requests locally before Telegram delivery and includes watchlist context.

**Frontend:** React 19 + Vite 8 + Tailwind CSS v4. Build passes. Public landing is branded as StatuteProof and positioned UAE-first around official-source monitoring, source readiness reviews, evidence-backed briefs, profile-scoped alerts, and disclosed coverage limitations. Latest value pass reduced repetitive "UAE" copy, added the Problem section back into the public flow, moved workflow before coverage, and reframed the source-readiness output as a professional review rather than a generic dashboard. Lint status from prior audit: no errors; one TanStack/React Compiler compatibility warning remained in the old `DashboardPreview.jsx` path.

**Public landing page sections (in order):**
- Hero, DashboardPreview / UAE Source Check sample output, Features, UAE Coverage, ConfiguredMonitoring, HowItWorks, Evidence Trail, Pricing, Contact, Footer

The public landing page is now UAE-first for pilot positioning under the public brand **StatuteProof**. It does not claim complete UAE coverage, does not provide legal advice, and discloses source access limitations near coverage claims. The stale watchlist-builder landing flow is not part of the public funnel.

Public pricing now starts with a free one-time **Free Source Check**. Founding pilot prices are Starter Pilot $99/mo, Regional Compliance Pack $249/mo, and Custom Market Watch $499/mo. The free check is positioned as source readiness review, not a free SaaS trial.

Public sample output is available at `/samples/uae-fintech-source-readiness-snapshot.html` and linked from the landing hero as "View sample source report." It is clearly marked as sample/demo output and supports the Free Source Check offer with readiness, limitations, alert format, evidence trail and Starter Pilot recommendation.

**App (authenticated):** AlertsPage with SourceProofPanel, DashboardHome, Reports, Sources, Settings, Integrations.

---

## Recently completed

- `0df4e29` Saudi Arabia source pack validated and activated
- `3e29c56` Frontend refocus: product repositioned from "source count" to "actionable intelligence"
- `26f6e61` Post-refocus regression fixes (broken hrefs, SA missing from COVERAGE_MARKETS, "85 tested" ambiguity)
- `ccd04e1` Gitignore generated validation report artifacts
- `7c607eb` Source proof panel added to app alerts (SourceProofPanel shared component)
- `826da9c` Source proof added to public landing interactive demo (DemoProofTrail, SOURCE_DETAILS, DEMO badge, "Request Pilot" CTA)
- `8c70601` Client Watchlist Builder added to landing page (4-step configurator, live preview, recommendation logic, coverage disclaimer)
- `1c5a905` Watchlist-to-Contact flow (pilotRequest state lifted to App.jsx, WatchlistSummaryCard, CopyButton, form pre-fill, structured POST body)
- Codex audit: `/api/contact` now preserves full contact submissions in an ignored JSONL queue, forwards watchlist context to Telegram, removes Telegram Markdown parsing for user text, adds explicit Telegram fallback on frontend delivery errors, removes placeholder footer links, and tightens source proof URL normalization.
- `contact-queue` CLI added to `run.py`: list queued requests (`--limit N`, `--latest`, `--json`). Operational recovery documented in `docs/contact_delivery.md`.
- Codex audit: contact-queue `--json` now returns a valid empty JSON array for missing/empty queues, and recovery docs no longer recommend re-posting queued entries through `/api/contact`.
- Production contact smoke test performed locally (`ok: true, queued: true, delivered: true`). Key finding: `config.py` uses `load_dotenv(override=True)` — shell env var overrides do not suppress Telegram delivery if `.env` has credentials. Guide added at `docs/production_contact_smoke_test.md`.
- Codex audit: added `REGRADAR_CONTACT_DELIVERY_DISABLED=1` for safe `/api/contact` smoke tests. The flag still queues requests, skips only contact-form Telegram delivery, and returns `queued: true, delivered: false` without affecting other Telegram commands.
- Deployment architecture planned. Recommended MVP path: VPS + nginx (serves `web/dist/` + proxies `/api/*` to Python). Alternatives documented. `docs/deployment_architecture.md` created. `.env.example` updated with deployment variables. `run.py` `api` help text updated with `--host` flag.
- VPS deployment runbook created at `docs/vps_deployment_runbook.md` — step-by-step commands for Ubuntu 22.04, nginx, systemd, HTTPS, smoke test, rollback, troubleshooting. `requirements.txt` created with pinned project dependencies.
- Codex audit: hardened VPS runbook/package guidance. `requirements.txt` now includes `python-docx`, docs require full `requirements.txt` even for API-only deployment, and troubleshooting no longer prints Telegram credential values.
- Coverage reality audit completed. `reports/coverage_reality_audit_2026-05-26.md` — 12-country analysis. 56 active sources across 9 countries. 4 countries demo-ready (AE, SG, KZ, TR). AZ has 1 active source but 4 pre-mapped sources ready for activation. SA has quality issues (54 score). BH/QA/HK/MY had zero sources.
- **Hong Kong source pack activated.** 8 sources added covering: central_bank (HKMA), financial_regulator/securities (SFC), tax (IRD), finance_ministry (FSTB), aml (JFIU), company_registry (CR), legal_database (e-Legislation SFO cap571), insurance_regulator (IA). 2 additional disabled entries documented (PCPD data_protection, HK Gazette). Coverage score shows 50 (unknown quality — health audit not yet run on new sources; all 8 tested GOOD individually). Full report: `reports/hk_validated_source_pack_2026-05-27.md`.
- **UAE source quality audit and expansion completed.** All 7 pre-existing AE sources revalidated — all confirmed GOOD. 2 new sources activated: DIFC Laws and Regulations (legal_database, 9,150c) and UAE Ministry of Economy (company_registry, 14,646c). AE total: 12 entries (9 active, 3 disabled). AE score: 89 — strong (will reach 100 after health audit). Geo-blocked: Official Gazette (uag.gov.ae), TDRA, GCA Customs — all unreachable outside UAE. FTA: all 3 tested URL variants return 0c — stays disabled. Full report: `reports/ae_source_quality_expansion_2026-05-27.md`.
- **Qatar source pack activated.** 9 sources added: QFCRA (financial_regulator), QFC (financial_free_zone), MoF (finance_ministry), GTA (tax), MOCI (company_registry), Al-Meezan (legal_database), QFIU (aml), NCSA (cybersecurity), CRA (digital_regulation). 4 additional disabled entries: QCB (SSL/JS failure), QFMA (SPA), MoJ (geo-blocked), Customs (SSL failure). QA total: 13 entries (9 active, 4 disabled). Score: 50 (unknown — run health to update). 8–12 target: ACHIEVED (9 sources). Full report: `reports/qa_validated_source_pack_2026-05-27.md`.
- **Saudi Arabia source quality audit completed.** All 7 existing SA sources revalidated. Key findings: SAMA/CMA/Commerce are PDF-primary and still monitorable through Playwright plus document extraction; BeautifulSoup-only extraction is degraded. CST remains enabled but limited (1,198c via Playwright/trafilatura; adapter advised). NCA upgraded from limited to active (2,744c confirmed GOOD). ZATCA confirmed (1,029c). 14 new SA candidate URLs tested — all geo-blocked or DNS-dead from outside Saudi Arabia. No new activations possible. 2 new disabled entries added (SAFIU geo-blocked, Umm Al-Qura geo-blocked). SA total: 12 entries (7 enabled, 5 disabled). Score: 54. PARTIAL verdict (7 enabled sources, target 8–12). Full report: `reports/sa_source_quality_expansion_2026-05-27.md`.
- **Malaysia source pack activated.** 11 sources added: BNM (central_bank/banking/payments/insurance; partial FI AML/CFT policy only, not standalone FIU), SC Malaysia (securities_regulator/crypto/digital assets), Bursa Malaysia (capital_markets), HASiL/LHDN (tax), Belanjawan Budget Portal (finance_ministry, 9,618c + 194,422c PDF), AGC/LOM (legal_database), JPDP/PDP (data_protection), MCMC (digital_regulation), NACSA (cybersecurity), MyCC (competition), SSM guidelines (company_registry). 3 disabled: MoF SPA, Federal Gazette DNS-dead, Customs SPA. MY total: 14 entries (11 enabled, 3 disabled). Score: 50 (unknown — run health to update). 8–12 target: ACHIEVED. Full report: `reports/my_validated_source_pack_2026-05-27.md`.
- **Bahrain source pack activated.** 12 sources added: CBB (central_bank), CBB Fintech (fintech/crypto), Bahrain Bourse (capital_markets), MoFNE (finance_ministry), NBR (tax), LLOC (legal_database/gazette), PDPA (data_protection), Customs, Sijilat (company_registry), MOIC (commerce), TRA (digital_regulation, PDF-primary), iGA (digital_government, PDF-primary). 2 disabled entries: Bahrain FIU (all 3 AML domains DNS-dead or blocked) and MoJ (judiciary-only PDFs). GCC4 bundle complete: AE + SA + QA + BH. BH total: 14 entries (12 enabled, 2 disabled). Score: 50 (unknown — run health to update). 8–12 target: ACHIEVED (12 sources). Full report: `reports/bh_validated_source_pack_2026-05-27.md`.
- **Saudi Arabia access & adapter sprint completed.** Deep retest of all 12 blocked SA candidates confirmed: all remain geo-blocked or DNS-dead. CST regulations subdomain (mutasilind.cst.gov.sa) separately geo-blocked. CST root IS accessible (HTTP 200) — failure is SPA rendering only, not geo-block. A CST SPA adapter (Playwright component-wait) would upgrade CST from limited (266c) to active (2,000–5,000c) without Saudi-IP. Saudi-IP (Oracle Cloud me-jeddah-1, ~$0–15/mo) is the unlock for SAFIU, Umm Al-Qura, BOE, and SDAIA — the 4 critical missing SA categories. Full report: `reports/sa_access_adapter_sprint_2026-05-27.md`.
- **Full health refresh completed.** `python run.py health` + `python run.py source-audit --json` run across all 140 sources. Health: PASS 96 · WARN 2 · SKIP 42 · FAIL 0. Overall coverage 69 → 90 (+21). New-source packs now have refreshed scores; iGA Bahrain remains WARN/low HTML but is accepted as PDF-primary. AE 89→100 (strong), HK 50→94 (strong), QA 50→100 (limited), BH 50→88 (strong), MY 50→92 (strong), SA 54→100 (limited), TR 83→100 (strong), KZ 93→100 (strong). 2 WARN sources: CBUAE 301c (readability extraction issue — Playwright fetches fine), iGA Bahrain 323c (PDF-primary by design). GE 89→72 and UZ 90→75 regressions noted — likely transient (DNS/rendering). Full report: `reports/source_health_refresh_2026-05-27.md`.
- **Production deployment preflight completed.** `docs/production_deployment_checklist.md` — 10-section command-ready VPS+nginx+systemd+SSL checklist. `docs/first_pilot_readiness_checklist.md` — pilot offer structure, safe claims, per-market caveats, ideal customer profiles. `.env.example` confirmed no changes needed. Deployment docs internally consistent. Exact next human action: provision a VPS.
- **Codex frontend cleanup audit completed.** Logo/favicons verified, pricing retained from latest repo source-of-truth, and Coverage cards hardened to show the current 9 commercial priority markets (AE, SA, QA, BH, HK, SG, MY, TR, KZ) without raw internal pass/restricted counts. QA/SA limitations remain disclosed. Build passes.
- **Codex landing funnel QA completed.** Audited `242a8ea fix(landing): simplify funnel and align pilot positioning`; landing funnel confirmed as 7 sections. Follow-up fix `307210d` restored navbar wordmark beside the octopus icon, reordered Coverage to UAE/SA/SG/HK/QA/BH/MY/TR/KZ, removed remaining CIS-first hero/contact examples, tightened pricing note, clarified dashboard preview labels, and removed stale watchlist-builder coupling from Contact. `npm run build` PASS. `npm run lint` still fails on pre-existing app lint debt outside the landing cleanup (`SourceProofPanel`, `AlertsPage`, `DashboardHome`) plus a TanStack table warning.
- **Free Source Check pricing tier added.** `ea7ec12` adds a free one-time source readiness review tier and lowers paid founding pilot pricing to $99/$249/$499. Hero, header, pricing card, and contact form CTAs now route prospects toward the free source check. Old public landing prices ($149/$399/$799/$999/$1,500/$199/$599) were scanned and removed from `web/src`, `web/public`, and `web/index.html`. `npm run build` and `git diff --check` PASS; `npm run lint` still fails only on known unrelated app lint debt.
- **Sample UAE source readiness snapshot added.** `d40bb60` adds `/samples/uae-fintech-source-readiness-snapshot.html`, a static public sample artifact for UAE fintech prospects. It includes source readiness table, demo alert, evidence trail, limitations, not-legal-advice language, and Starter Pilot recommendation. Landing hero now links to "View sample source check." `npm run build` and `git diff --check` PASS.
- **Codex sample snapshot audit completed.** `68bb7f5` keeps the sample artifact and hero link intact, replaces a realistic-looking fake `.gov.ae` URL with an explicit placeholder, and softens footer disclaimer wording to avoid even negative "complete coverage" phrasing. Build confirms the sample is copied to `web/dist/samples/uae-fintech-source-readiness-snapshot.html`. `npm run build` and `git diff --check` PASS; lint still fails only on known unrelated app lint debt.
- **Codex first-customer product readiness audit completed.** Small fixes align AI analysis scope and authenticated app market selectors with GCC/APAC-first positioning, mark dashboard AI/Telegram status as demo mode, and remove frontend lint errors around SourceProofPanel/AlertsPage/DashboardHome. Core finding: monitoring and extraction are real; the authenticated app and report delivery remain demo/semiautomated until live alert/report APIs and stronger evidence persistence are built.
- **Codex parsing/information-quality benchmark completed.** 15 priority-market official sources tested across UAE, Saudi Arabia, Singapore, Hong Kong, Bahrain, and Malaysia. Result: mixed but usable for Free Source Check; strongest value comes from Playwright-rendered HTML plus PDF extraction. `document-test` now falls back to the scraper/Playwright path when requests HTML is thin or contains no document links, preventing false "no PDFs found" results on sources such as CBUAE and SAMA.
- **UAE source run history foundation added.** `python run.py source-readiness --market AE --record-run` now appends source run evidence to `data/source_runs/source_runs.jsonl` (ignored runtime data), including source identity, extraction quality, extracted chars, PDF contribution, content hash, limitations, errors, and change status. `python run.py source-history --market AE` shows the latest run per source. This supports paid-pilot evidence tracking without a DB migration.
- **StatuteProof UAE-first public repositioning completed.** Public landing brand copy changed from RegRadar to StatuteProof while preserving asset paths and internal identifiers. Hero, source-check preview, features, UAE coverage matrix, configured monitoring profiles, evidence trail, pricing copy, contact form, footer, metadata, and sample source readiness page now focus on UAE official sources (CBUAE, VARA, DFSA, ADGM/FSRA, UAE FIU, Ministry of Finance, UAE Legislation Portal, DIFC Laws, Ministry of Economy) with limitations disclosed. Pricing values unchanged. Backend logic unchanged.
- **StatuteProof website value pass completed.** Public landing narrative now leads with the compliance gap, explains the source-to-brief workflow, shows source coverage with Active/Limited/Not Active status, strengthens alert-profile routing, replaces evidence tiles with auditable proof panels, reframes the Free Source Check as a Source Readiness Review, and updates founding pilot copy without changing pricing numbers. Stale public `regradar_founder` contact links removed from landing/contact/footer. Backend logic and asset paths unchanged.
- **StatuteProof product quality Sprint 1 completed.** Source-run evidence now uses normalized regulatory text as the change-detection trust anchor while preserving the legacy `content_hash` field for compatibility. New records include `raw_chars`, `normalized_chars`, `raw_hash`, `normalized_hash`, `pdf_text_hash`, and snapshot paths. Runtime snapshots are written under ignored `data/source_snapshots/YYYY-MM-DD/<market>/<source_id>/<run_id>/` with `raw.txt`, `normalized.txt`, optional `pdf_text.txt`, and `metadata.json`. PDF text is hashed separately when available; if PDF links exist but no text is extracted, the run records a manual validation/OCR limitation. `source-history` now shows normalized chars, short hash prefixes, and snapshot paths. Remaining gaps before customer alerts: paragraph diff artifacts, proof block rendering, actionable alert drafts, client relevance filtering, human review workflow, and weekly brief generation.

---

## Validation status

| Check | Result | Date |
|-------|--------|------|
| compileall | PASS | 2026-05-26 |
| health | PASS: 56, SKIP: 29, FAIL: 0 | 2026-05-26 |
| npm build | PASS (571ms, chunk-size warning only) | 2026-05-26 |
| overclaim scan | 0 actionable overclaims found | 2026-05-26 |
| contact-queue CLI | PASS (all 3 modes verified with test data) | 2026-05-26 |
| contact-queue missing/empty JSON | PASS (`[]`) | 2026-05-26 |
| security scan | PASS (no exposed secrets) | 2026-05-26 |
| local smoke test (queue+deliver) | PASS (`ok: true, queued: true, delivered: true`) | 2026-05-26 |
| local smoke test (queue-only) | PASS (`ok: true, queued: true, delivered: false`) | 2026-05-26 |
| npm build | PASS (494ms, chunk-size warning only) | 2026-05-26 |
| deployment architecture | documented in `docs/deployment_architecture.md` | 2026-05-26 |
| coverage reality audit | 12 countries audited, report at `reports/coverage_reality_audit_2026-05-26.md` | 2026-05-26 |
| compileall (post-audit) | PASS | 2026-05-26 |
| HK source pack — 8 sources activated | PASS (all 8 tested GOOD via test-source) | 2026-05-27 |
| compileall (post-HK) | PASS | 2026-05-27 |
| coverage --json (post-HK) | PASS: 95 sources, 64 enabled; HK score 50 (unknown — run health to update) | 2026-05-27 |
| UAE source audit — all 7 revalidated GOOD | PASS (CBUAE 26,804c, VARA 2,705c, DFSA 5,627c, ADGM 2,135c, MoF 13,340c, Legislation 14,808c, FIU 2,026c) | 2026-05-27 |
| UAE expansion — 2 new sources activated | PASS (DIFC Laws 9,150c, MoECT 14,646c tested GOOD via test-source) | 2026-05-27 |
| compileall (post-AE) | PASS | 2026-05-27 |
| coverage --json (post-AE) | PASS: 97 sources, 66 enabled; AE score 89 strong (run health to reach 100) | 2026-05-27 |
| npm build (post-AE) | PASS (758ms, chunk-size warning only) | 2026-05-27 |
| QA source pack — 9 sources activated | PASS (all 9 tested GOOD via test-source) | 2026-05-27 |
| compileall (post-QA) | PASS | 2026-05-27 |
| coverage --json (post-QA) | PASS: 110 sources, 74 enabled; QA score 50 (unknown — run health to update) | 2026-05-27 |
| SA source audit — 7 revalidated, NCA upgraded | PASS (MISA 8,028c, ZATCA 1,029c, NCA 2,744c confirmed; SAMA/CMA/Commerce PDF-primary stable) | 2026-05-27 |
| SA new candidates — 14 URLs tested | ALL BLOCKED (geo-IP or DNS failure from outside SA) | 2026-05-27 |
| compileall (post-SA) | PASS | 2026-05-27 |
| coverage --json (post-SA) | PASS: 112 sources; SA score 54 limited (run health to update) | 2026-05-27 |
| SA access & adapter sprint — blocked source deep retest | CONFIRMED: all 12 blocked SA candidates remain geo-blocked/DNS-dead. CST root accessible (SPA only — adapter viable). Saudi-IP needed for SAFIU, Umm Al-Qura, BOE, SDAIA. | 2026-05-27 |
| MY source pack — 11 sources activated | PASS (BNM 2,046c, SC 9,128c, Bursa 14,029c via Playwright despite 403 surface, HASiL 7,351c, Belanjawan 9,618c+194K PDF, LOM 6,310c, PDP 13,248c, MCMC 3,758c+38K PDF, NACSA 12,890c, MyCC 9,054c, SSM 2,607c+11,834c sampled PDFs) | 2026-05-27 |
| compileall (post-MY) | PASS | 2026-05-27 |
| coverage --json (post-MY) | PASS: 140 sources, 98 enabled; MY score 50 (unknown — run health to update) | 2026-05-27 |
| BH source pack — 12 sources activated | PASS (CBB 2,972c, CBB-Fintech 24,241c, Bourse 10,090c, MoFNE 3,086c, NBR 5,093c, LLOC 2,358c, PDPA 3,633c, Customs 1,802c, Sijilat 3,554c, MOIC 1,104c, TRA PDF-primary 84,352c, iGA PDF-primary 195,616c) | 2026-05-27 |
| compileall (post-BH) | PASS | 2026-05-27 |
| coverage --json (post-BH) | PASS: 126 sources, 87 enabled; BH score 50 (unknown — run health to update) | 2026-05-27 |
| health run (all 140 sources) | PASS 96 · WARN 2 · SKIP 42 · FAIL 0. WARN: CBUAE 301c (readability issue), iGA BH 323c (PDF-primary by design). | 2026-05-27 |
| source-audit --json (all 140 sources) | PASS — source_audit_2026-05-27.json created (140 sources audited) | 2026-05-27 |
| coverage --json (post-health) | PASS — overall 69→90. AE 100 strong, HK 94 strong, QA 100 limited, BH 88 strong, MY 92 strong, SA 100 limited, SG 100, TR 100, KZ 100. GE 89→72 and UZ 90→75 regressions noted (likely transient). | 2026-05-27 |
| compileall (post-health) | PASS | 2026-05-27 |
| compileall (post-preflight) | PASS | 2026-05-27 |
| coverage --json (post-preflight) | PASS — overall 90, commercial markets confirmed (AE 100, HK 94, QA 100 limited, BH 88, MY 92, SA 100 limited, SG 100, TR 100, KZ 100) | 2026-05-27 |
| compileall (product readiness audit) | PASS | 2026-05-29 |
| coverage --json (product readiness audit) | PASS — 140 sources, 98 enabled, overall 90 limited | 2026-05-29 |
| npm build (product readiness audit) | PASS (chunk-size warning only) | 2026-05-29 |
| npm lint (product readiness audit) | PASS with 1 warning: TanStack table React Compiler compatibility warning in `DashboardPreview.jsx` | 2026-05-29 |
| git diff --check (product readiness audit) | PASS | 2026-05-29 |
| parser benchmark — 15 representative sources | MIXED: 12 useful/GOOD, 2 thin/needs adapter, 1 blocked/failed | 2026-05-30 |
| document-test fallback validation | PASS: CBUAE and SAMA PDF discovery works via scraper fallback | 2026-05-30 |
| UAE source-readiness --record-run | PASS: first live run produced FIRST_SEEN for stable active sources; blocked FTA/e-Laws remained disclosed | 2026-05-30 |
| UAE source-readiness --record-run second pass | PASS: most active sources UNCHANGED; UAE Legislation and MoE showed CHANGED due content hash differences; no QUALITY_DROP | 2026-05-30 |
| source-history --market AE | PASS: latest run per UAE source displays quality, chars, PDF chars, change status, limitations/errors | 2026-05-30 |
| compileall (StatuteProof public repositioning) | PASS | 2026-05-30 |
| npm build (StatuteProof public repositioning) | PASS (Vite build completed; no chunk-size warning shown) | 2026-05-30 |
| git diff --check (StatuteProof public repositioning) | PASS | 2026-05-30 |
| public overclaim scan (StatuteProof public repositioning) | PASS for active landing/sample files; remaining RegRadar references are internal/demo app components or legacy brand assets | 2026-05-30 |
| npm build (StatuteProof value pass) | PASS | 2026-05-30 |
| git diff --check (StatuteProof value pass) | PASS | 2026-05-30 |
| public risk phrase scan (StatuteProof value pass) | PASS for active landing/sample files. `fully automated`, `complete UAE coverage`, `guaranteed compliance`, `24/7`, and `15-minute` returned no matches. `SCA` appears only as `Capital Market Authority / former SCA`. | 2026-05-30 |
| compileall (normalized source snapshots) | PASS | 2026-05-30 |
| text normalization tests | PASS via `.venv/bin/python tests/test_text_normalization.py` (pytest not installed) | 2026-05-30 |
| UAE source-readiness --record-run x2 (normalized snapshots) | PASS: snapshots created and JSONL fields populated. Final pass: 8/9 active UAE sources UNCHANGED; UAE Legislation Portal still CHANGED and needs Sprint 2 diff/adapter review. | 2026-05-30 |
| source-history --market AE --limit 20 (normalized snapshots) | PASS: shows normalized chars, normalized/raw hash prefixes, snapshot paths, and change status. | 2026-05-30 |
| git diff --check (normalized source snapshots) | PASS | 2026-05-30 |

---

## Known risks

1. **Contact queue needs operational review in deployment.** `/api/contact` writes `data/contact_requests.jsonl` before Telegram delivery, and that file is ignored because it contains prospect details. Ensure production storage/backups or log shipping preserve it if Telegram delivery is down.

2. **No deployment is live yet.** Architecture is documented in `docs/deployment_architecture.md`. Recommended path: VPS + nginx. Frontend uses relative `/api/contact` — static-only hosting will silently drop all pilot requests. The Vite dev proxy is dev-only and does not apply to built assets.

3. **`load_dotenv(override=True)` still makes shell credential overrides ineffective.** If `.env` contains real Telegram credentials, setting `TELEGRAM_BOT_TOKEN=""` in the shell before `run.py api` does NOT suppress delivery — `.env` wins. Use `REGRADAR_CONTACT_DELIVERY_DISABLED=1` for no-Telegram `/api/contact` smoke tests. See `docs/production_contact_smoke_test.md`.

4. **Install the full `requirements.txt` on the VPS.** `run.py api` imports the monitoring pipeline before command dispatch, so API-only deployments still need scraper/parser packages importable. The Playwright Chromium browser download is only needed when running monitoring/health/source fetches.

5. **Generated tracked reports.** Some `reports/` files matched by `.gitignore` patterns may still be tracked from before the ignore rules were added. If they appear as modified after a health run, use `git restore reports/`.

6. **Source count must not be marketed as core value.** Copy across the landing page has been cleaned, but future edits should be scanned with the overclaim check before commit.

7. **Authenticated app is still partly demo-only.** Dashboard, alerts, AI briefs, reports, and integration screens use frontend mock data. `SourcesPage` can call `/api/source-test`, but live monitoring results, AI briefs, Telegram sends, and report downloads are not wired end-to-end through the app UI.

8. **Evidence persistence is incomplete.** Runtime pipeline results include extraction quality, diffs, AI fields, and Telegram status, but SQLite/report storage still centers on URL/content/hash/risk/AI summary. Customer-facing reports need durable source name, jurisdiction/category, last-checked timestamp, extraction method/status, diff evidence, and risk rationale fields.

9. **Risk scoring is useful for triage, not final classification.** Rule-based scoring relies on keyword/context heuristics and can over-score generic "update/amendment" language. Human review or AI semantic analysis should remain part of pilot delivery for high-confidence briefs.

10. **Source run history is append-only JSONL.** Stored at `data/source_runs/source_runs.jsonl` and ignored by git. It is suitable for first-pilot evidence but not a durable production database. Back it up or migrate to DB storage before scale.

11. **Delta detection now uses normalized hashes, but is still a foundation.** New source-run records store both `raw_hash` and `normalized_hash`; `normalized_hash` drives FIRST_SEEN / UNCHANGED / CHANGED / FAILED / QUALITY_DROP, while legacy `content_hash` remains for compatibility with older records. Raw-only changes are classified as UNCHANGED and annotated. Snapshot files are ignored runtime evidence under `data/source_snapshots/`. UAE Legislation Portal still produced CHANGED on the final Sprint 1 validation pass, likely due dynamic source content/extraction variance; Sprint 2 needs paragraph diff artifacts and a proof block before customer alerts.

7. **`source_candidates.json` is planning-only.** It is never a production coverage claim.

8. **Saudi Arabia sources.** Some Saudi sources have geo-restrictions or auth requirements. Documented in Coverage.jsx and InteractiveDemo notes.

9. **HK sources — coverage confirmed 94 (strong).** All 8 HK sources individually GOOD and confirmed in `source_audit_2026-05-27.json`. Score 50 (unknown) updated to 94 (strong). HK is demo-ready.

10. **HK IA circulars source has HTTP 404 SPA routing.** The Insurance Authority circulars page returns HTTP 404 from the server but Playwright renders 11,694c of genuine content. This is a known IA website behavior. Monitor for URL instability — if it stops rendering, fall back to the IA root domain (600c, needs adapter).

11. **HK PCPD is not activated.** The data_protection category is uncovered. PCPD website renders the same 4,292c app-shell on all URLs. A navigation adapter is required before this can be activated.

12. **AE score confirmed 100 (strong).** DIFC Laws (9,150c) and UAE MoECT (14,646c) now registered in `source_audit_2026-05-27.json`. AE score 89→100. All 9 AE active sources confirmed GOOD. CBUAE shows 301c low_content WARN (readability extraction issue under Playwright — 26,804c fetched successfully) but does not affect the 100 score.

13. **AE geo-blocked sources.** UAE Official Gazette (uag.gov.ae), TDRA (data_protection), and GCA Customs are all unreachable from outside UAE — confirmed via connection timeout. Cannot be activated without a UAE-IP deployment node.

14. **AE FTA is blocked for non-UAE clients.** Federal Tax Authority renders 0c on all tested URL variants. Tax monitoring for UAE mainland is not possible without a UAE-IP adapter.

15. **QA score confirmed 100 (limited).** All 9 QA sources confirmed GOOD in `source_audit_2026-05-27.json`. Score 50→100. "Limited" qualifier reflects 4 restricted sources (QCB, QFMA, MoJ, Customs) excluded from denominator. Disclose in demos: QCB (central bank) and QFMA (securities) not accessible from outside Qatar.

16. **QA QCB (central_bank) is not activated.** Qatar Central Bank has SSL certificate verification failure on all tested URLs; Playwright renders 0c JS shell. Critical missing source — needs SSL/SNI adapter or direct QCB publications URL bypass.

17. **QA QFMA (securities_regulator) is not activated.** Qatar Financial Markets Authority website is a pure SPA — root 0c, all alternate paths return 404. Needs adapter targeting QFMA publications/decisions API. Important for capital markets monitoring.

18. **QA Al-Meezan and QFIU require Playwright.** Both sources have SSL certificate issues that prevent Tier 1 (requests) extraction. Playwright handles both successfully. Monitor for performance impact in production health runs.

19. **SA SAMA/CMA/Commerce are PDF-primary and Playwright-dependent.** BeautifulSoup-only extraction is degraded, but targeted checks on 2026-05-27 returned usable Playwright text plus strong PDF extraction (SAMA 68,237c, CMA 40,177c, Commerce 134,346c via `test-source`). A SharePoint/API/RSS adapter would make monitoring more robust.

20. **SA geo-blocking blocks all critical missing categories.** SAFIU (AML), Umm Al-Qura (official gazette), Bureau of Experts (legal database), MoF, and SDAIA are all geo-blocked from outside Saudi Arabia. A Saudi-IP VPS (AWS me-central-1 or local provider) is required to activate these categories.

21. **SA CST is enabled but limited.** Communications, Space and Technology Commission is important for fintech/payments digital regulation. Current targeted validation extracts 1,198c via Playwright/trafilatura, but only 266c through BeautifulSoup. CST adapter remains the highest-ROI SA adapter task.
22. **BH score confirmed 88 (strong).** All BH sources confirmed in `source_audit_2026-05-27.json`. Score 50→88. 11/12 active sources GOOD; iGA HTML 323c shows WARN (PDF-primary by design — 195,616c from 3 PDFs). BH is demo-ready.
23. **BH AML/FIU is not covered.** All tested Bahrain FIU domains (fiu.gov.bh, fid.gov.bh, amlu.gov.bh) are DNS-dead or connection timeout. CBB partially covers banking-sector AML supervision. A standalone AML source requires domain discovery or Ministry of Interior sub-page investigation.
24. **BH TRA and iGA are PDF-primary.** HTML extraction is 746c (TRA) and 323c (iGA) — below thresholds. Both are activated on strong PDF grounds (84,352c and 195,616c respectively). Monitor for PDF availability changes; if PDFs stop publishing, these sources would need HTML adapters to remain useful.
25. **BH CBB and CBB Fintech share the same root domain.**
26. **MY score confirmed 92 (strong).** All 11 MY sources confirmed GOOD in `source_audit_2026-05-27.json`. Score 50→92. MY is demo-ready. SEA pair (SG 100 + MY 92) both confirmed strong.
27. **MY MoF (mof.gov.my) is not activated.** All tested paths return <500c (deep SPA). The Malaysia Budget Portal (belanjawan.mof.gov.my) is activated instead and covers fiscal policy and budget documents. General MoF policy circulars are not monitored.
28. **MY Customs portal is inaccessible.** customs.gov.my is a SharePoint SPA — all tested sub-paths return 404 or 0c. Customs/trade compliance monitoring for Malaysia is not possible without a SharePoint adapter.
29. **MY Federal Gazette DNS-dead.** Both known gazette domains (federalgazette.agc.gov.my, gazette.gov.my) do not resolve. Official gazette publication monitoring is unavailable. AGC/LOM (enacted legislation) is active.
30. **MY SSM source uses guidelines sub-page.** The SSM root (ssm.com.my/) returns only 1,341c via Playwright with no PDFs. The guidelines page (/Pages/Legal_Framework/Guidelines.aspx) returns 2,607c and is the activated entry. Monitor for URL stability — if SSM restructures navigation, the guidelines URL may change.
31. **MY standalone AML/FIU is not active.** BNM publishes AML/CFT policy for BNM-licensed financial institutions, but it is not a dedicated FIU source. Do not market Malaysia as having standalone AML/FIU coverage until a public FIU/AML source is validated.
32. **GE regression — score 89→72.** Georgia dropped 17 points in the 2026-05-27 audit (2 sources now low_content vs GOOD in 2026-05-25). Likely transient rendering variation. Run `python run.py test-source` on GE URLs before the next demo if GE is in scope.
33. **UZ regression — score 90→75.** Uzbekistan dropped 15 points — tax.gov.uz returned DNS failure (ERR_NAME_NOT_RESOLVED) in the 2026-05-27 audit. Likely transient DNS flicker. Monitor and re-test before UZ demos.

---

## Next recommended task

**Option F — ~~Production deployment preflight~~ (COMPLETED 2026-05-27):**
`docs/production_deployment_checklist.md` and `docs/first_pilot_readiness_checklist.md` created. Deployment docs consistent with architecture and runbook.

**Production blockers (human action required before going live):**
- VPS not created — must provision Hetzner CX11 (~$6/mo) or DigitalOcean Basic
- Domain not pointed — DNS A record must be set to VPS IP before certbot
- Telegram env vars not set — `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` must be in `/srv/regradar/.env`
- Production smoke test not run — must verify `ok: true, queued: true, delivered: true` before outreach

**Option A — Deploy (highest ROI if pilots are imminent):**
Provision a VPS and follow `docs/production_deployment_checklist.md` (new, task-oriented) or `docs/vps_deployment_runbook.md` (full command reference). All code and docs are ready. Exact first step: pick a provider and run `apt update && apt install -y git nginx python3 python3-venv curl ufw`. All 9 commercial priority markets have refreshed scores; QA and SA require disclosed limitations.

**Option B — CST SPA adapter (highest-ROI SA improvement, no Saudi-IP needed):**
Build a CSTAdapter class following the CBR anchor-page pattern. Use Playwright with targeted component-wait (find the CSS selector for CST's news/announcements after Vue mount). Expected yield: 2,000–5,000c, upgrading CST from limited (1,198c) to active. Effort: 2–4 hours.

**Option C — ~~Malaysia source pack~~ (COMPLETED 2026-05-27):**
11 MY sources activated and confirmed 92 (strong). See `reports/my_validated_source_pack_2026-05-27.md`.

**Option D — ~~Full health refresh~~ (COMPLETED 2026-05-27):**
New-source packs refreshed. Overall 69→90. Commercial markets are demo-ready only with documented limitations, especially QA and SA. See `reports/source_health_refresh_2026-05-27.md`.

**Option E — Saudi-IP deployment (Oracle Cloud me-jeddah-1, ~$0–15/mo):**
Unlocks SAFIU (AML), Umm Al-Qura (gazette), BOE (legal database), SDAIA (data protection) — the 4 critical missing SA categories. See `reports/sa_access_adapter_sprint_2026-05-27.md`.

For deployment path:
1. Provision a VPS — Hetzner CX11 (~$6/mo) or DigitalOcean Basic recommended.
2. Point a domain's DNS A record to the VPS IP.
3. Follow `docs/vps_deployment_runbook.md` section by section.
4. Confirm `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` before going live.
5. Run the production smoke test (Section 11 of the runbook) before sharing with prospects.

No code changes are needed before deployment.

---

## Files not to touch unless task-specific

| File | Reason |
|------|--------|
| `sources.json` | Production monitoring config — only edit when activating validated sources |
| `source_candidates.json` | Planning only — not coverage |
| `reports/*` | Generated artifacts — not tracked |
| `app/` monitoring engine | Backend logic — only edit for backend-specific tasks |
| `web/src/components/SourceProofPanel.jsx` | Shared component — changes affect both app and landing |

---

## Handoff protocol

**When Claude finishes a task:**
1. Run validation (compileall + npm build)
2. Run overclaim scan
3. `git add <specific files>` → commit → push
4. Update this file with new commit hash and state
5. Tell the human: "Ready for Codex audit" or "Ready for next task"

**When Codex finishes a task:**
1. Commit only meaningful fixes (no reformatting noise)
2. Push
3. Update this file
4. Return short summary to human:
   - Verdict
   - Files changed
   - Tests passed
   - Commit hash
   - Remaining risks
5. Human pastes only that short summary back to Claude (not full Codex log)

---

## 2026-05-30 — Sprint 2 source diff/proof artifacts

Implemented product-quality Sprint 2 on top of normalized snapshot runs:

- `app/chunk_diff.py` adds paragraph/line-level normalized snapshot diffs.
- `app/proof.py` builds reusable source proof blocks with URL, hashes, snapshot paths, extraction metadata, limitations, and the not-legal-advice disclaimer.
- `app/source_runs.py` now writes `diff.json` and `diff.md` beside the current run snapshot when `change_status == CHANGED`, and writes `proof.json` for new recorded source runs.
- JSONL compatibility is preserved. New records may include `diff_json_path`, `diff_md_path`, `proof_block_path`, `meaningful_change_detected`, and `diff_quality`; old records remain readable.
- Runtime artifacts stay under ignored storage:
  `data/source_snapshots/YYYY-MM-DD/<market>/<source_id>/<run_id>/`.

Inspection command:

```bash
.venv/bin/python run.py source-diff --market AE --latest-changed
```

Validation run:

```bash
.venv/bin/python -m compileall app run.py -q
.venv/bin/python tests/test_text_normalization.py
.venv/bin/python tests/test_chunk_diff_and_proof.py
.venv/bin/python run.py source-readiness --market AE --record-run
.venv/bin/python run.py source-readiness --market AE --record-run
.venv/bin/python run.py source-history --market AE --limit 20
.venv/bin/python run.py source-diff --market AE --latest-changed
```

UAE Legislation Portal diagnosis:

- Latest changed artifact: `data/source_snapshots/2026-05-30/AE/AE-uae-legislation-portal/AE-20260530T160721Z-b650bff3/diff.json`.
- Classification: `UNKNOWN_REQUIRES_ADAPTER`.
- The diff shows a broad Arabic homepage aggregate-count chunk changed, not a discrete legal title/body change. Do not turn this source into customer alerts until a source-specific adapter produces item-level legislation/change records.

Remaining gaps before customer alerts:

- Actionable alert draft engine.
- Client relevance filtering.
- Human review/approval workflow.
- Weekly brief generator.
- Telegram delivery after approval only.

---

## 2026-05-30 — Sprint 3 draft alert engine

Implemented product-quality Sprint 3 as a draft-only layer on top of source diff/proof artifacts:

- `app/alert_drafts.py` builds structured alert drafts from a source run, `diff.json`, and `proof.json`.
- All generated alerts are `review_status=DRAFT` and `send_decision=HOLD_FOR_REVIEW`.
- Draft fields include source metadata, change type, risk level, rationale, changed excerpts, affected entities, recommended action, confidence, limitations, proof block, and the not-legal-advice disclaimer.
- Alert artifacts are written beside the source snapshot as `alert_draft.json` and `alert_draft.md`.
- Markdown starts with `DRAFT — HUMAN REVIEW REQUIRED` and is suitable for later human-edited email/Telegram formatting.

Classifier notes:

- Change type is rule-based only: examples include `RULEBOOK_UPDATE`, `CIRCULAR_UPDATE`, `GUIDANCE_UPDATE`, `CONSULTATION`, `AML_CFT`, `TAX`, `LICENSING`, and `GENERAL_UPDATE`.
- Risk classification is conservative. `HIGH` requires obligation language plus stronger deadline/licensing/penalty/custody/AML signals.
- `REVIEW` is used for incomplete diff/proof, unknown changes, and adapter-required sources.
- UAE Legislation Portal broad Arabic homepage aggregate-count changes are forced to `risk_level=REVIEW`, `confidence=LOW`, and `HOLD_FOR_REVIEW`.

Inspection command:

```bash
.venv/bin/python run.py alert-draft --market AE --latest-changed
```

Remaining gaps before customer delivery:

- Client relevance filtering.
- Human review/approval workflow.
- Weekly brief generator.
- Telegram delivery after approval only.

---

## 2026-05-30 — Sprint 4 client relevance filtering

Implemented product-quality Sprint 4 as a draft/review-only relevance layer:

- `app/client_profiles.py` defines client profile loading, UAE source/topic metadata, and `score_alert_relevance(...)`.
- `data/client_profiles.example.json` includes five demo profiles: `uae_payments_demo`, `uae_vasp_demo`, `difc_financial_demo`, `adgm_financial_demo`, and `uae_tax_demo`.
- Source metadata tags cover CBUAE, VARA, UAE FIU, DFSA, ADGM/FSRA, Ministry of Finance, UAE Legislation Portal, DIFC Laws, Ministry of Economy, Capital Market Authority / former SCA, and FTA.
- Delivery decisions are review/planning decisions only: `URGENT_ALERT`, `WEEKLY_BRIEF_ONLY`, `SUPPRESS_NOT_RELEVANT`, and `MANUAL_REVIEW_REQUIRED`.
- `alert-draft --profile <client_id>` now writes `relevance.json` beside the alert draft when a profile is supplied, and keeps the alert itself `DRAFT` / `HOLD_FOR_REVIEW`.
- `relevance-test --market AE --profile <client_id>` scores the latest alert draft, or falls back to a synthetic VARA custody fixture if no changed alert exists.

Relevance behavior:

- Explicitly excluded sources are suppressed.
- Source, topic, and jurisdiction overlap raise relevance score.
- Topic-only overlap without source or jurisdiction scope is suppressed to avoid generic cross-client alerts.
- `REVIEW` risk, low confidence, incomplete proof, or adapter limitations force `MANUAL_REVIEW_REQUIRED` when there is relevant overlap.
- UAE Legislation Portal aggregate-count changes remain review-only or suppressed, never urgent.

Commands:

```bash
.venv/bin/python run.py alert-draft --market AE --latest-changed --profile uae_vasp_demo
.venv/bin/python run.py relevance-test --market AE --profile uae_vasp_demo
```

Remaining gaps before customer delivery:

- Human review/approval workflow.
- Weekly brief generator.
- Telegram delivery after approval only.

---

## 2026-05-30 — Sprint 5 human alert review workflow

Implemented product-quality Sprint 5 as a local CLI approval layer:

- `app/alert_review.py` discovers local `alert_draft.json` artifacts, appends immutable review records, and safely updates draft review fields.
- Runtime review records are stored in ignored JSONL storage: `data/alert_reviews/reviews.jsonl`.
- Supported review statuses: `DRAFT`, `MANUAL_REVIEW_REQUIRED`, `APPROVED_FOR_WEEKLY`, `APPROVED_FOR_URGENT`, `REJECTED`, `NEEDS_SOURCE_ADAPTER`, `NEEDS_LEGAL_REVIEW`.
- Supported send decisions: `HOLD_FOR_REVIEW`, `DO_NOT_SEND`, `WEEKLY_BRIEF_ONLY`, `READY_FOR_URGENT_DELIVERY`.
- Every future delivery-ready status must come from an explicit human CLI action.

Commands:

```bash
.venv/bin/python run.py alert-review list --market AE
.venv/bin/python run.py alert-review show --alert-id <id>
.venv/bin/python run.py alert-review approve --alert-id <id> --weekly --reviewer "Omar" --note "..."
.venv/bin/python run.py alert-review approve --alert-id <id> --urgent --reviewer "Omar" --note "..."
.venv/bin/python run.py alert-review reject --alert-id <id> --reviewer "Omar" --note "..."
.venv/bin/python run.py alert-review needs-adapter --alert-id <id> --reviewer "Omar" --note "..."
```

Safety rules:

- Urgent approval is blocked unless `--force` is used when proof is incomplete, confidence is low, risk is `REVIEW`, meaningful change is false, diff quality is incomplete, relevance requires manual review, or UAE Legislation Portal still needs adapter review.
- `--force` requires a review note.
- Weekly approval is still explicit and local; it does not send anything.

Remaining gaps before customer delivery:

- Weekly brief generator.
- Telegram delivery after approval only.
- Telegram account linking.
- Customer dashboard later.

---

## 2026-05-30 — Sprint 6 reviewed weekly brief generator

Implemented product-quality Sprint 6 as a local brief generator:

- `app/weekly_brief.py` generates Markdown and HTML weekly briefs from reviewed alert drafts only.
- Included alerts must have `review_status` `APPROVED_FOR_WEEKLY` or `APPROVED_FOR_URGENT`, and `send_decision` `WEEKLY_BRIEF_ONLY` or `READY_FOR_URGENT_DELIVERY`.
- Excluded alerts include `DRAFT`, `HOLD_FOR_REVIEW`, `REJECTED`, `DO_NOT_SEND`, `NEEDS_SOURCE_ADAPTER`, and `NEEDS_LEGAL_REVIEW`.
- Output is written under ignored generated-report storage:
  `reports/weekly_briefs/<client_id>/<YYYY-MM-DD>_weekly_brief.md`
  and `.html`.
- Brief sections: header, executive summary, reviewed regulatory updates, source coverage and limitations, no-action/suppressed note, and disclaimer.
- Empty periods generate an honest “No reviewed updates were approved for this brief period” brief. It does not claim no changes occurred.
- `--demo-fixture` creates clearly marked `SAMPLE / DEMO - NOT CUSTOMER DATA` output without writing demo data into review storage.

Command:

```bash
.venv/bin/python run.py weekly-brief --client uae_vasp_demo --market AE --days 7
.venv/bin/python run.py weekly-brief --client uae_vasp_demo --market AE --days 7 --demo-fixture
```

Remaining gaps before customer delivery:

- Telegram delivery after approval only.
- Telegram account linking.
- Customer dashboard later.
