# UAE 50 Continuous Activation War-Room Plan

## 1. Current Repo State

- Worktree clean at start: yes.
- Latest commit at start: `3b93688 feat: activate proof-backed UAE monitoring sources`.
- Workspace: `/Users/kurbnovomar/StatuteProof-Command-Center`.
- Product code: `product/regradar`.

### Cycle update 2026-06-15 (verified, supersedes stale numbers above)

- HEAD at this cycle: `7564d79 feat: activate proof-backed UAE monitoring sources`
  (one commit newer than `3b93688`; the 3 proof-backed queue sources — SCA
  circulars, DFSA MLRO letters, DFSA AML rulebook — are already activated).
- Test suite: 188 passed. Validators (9): all PASS. Worktree clean.
- Agent gates are **emulated manually** this session — no StatuteProof subagent
  runtime is available, and none is claimed to have run.

## 2. Current Source Truth

> The `16 / 12 / 4` below is the prior-session truth (commit `3b93688`). The
> verified current truth at HEAD `7564d79` is **19 / 15 / 4**, measured directly
> from `sources.json` (jurisdiction AE: 19 enabled = 15 active + 4 remediation).

- Enabled UAE sources: 19 (was 16).
- Readiness-supported (status:active) UAE sources: 15 (was 12).
- UAE sources under remediation: 4.
- Public truth may only change when `sources.json`, proof artifacts, baselines,
  agent gates, readiness docs, and validators all support the new truth.
- Last full no-save sweep (2026-06-14) passed 0/24 under generic extraction;
  per-source adapters are the gating work (proven: SCA circulars q=0 nav-shell →
  q=62 CONFIRMED_ACCESSIBLE with `sca_listing`).

## 3. Definition Of Useful Active Source

A source counts toward the 50-source goal only when it is:

- official or officially linked;
- UAE-relevant;
- public and permitted to monitor;
- useful to MLRO, CCO, or compliance buyers;
- not a generic homepage when a better regulatory endpoint exists;
- using the correct final URL;
- using a stable adapter, selector, API, PDF, listing, table, register, or rulebook strategy;
- strong no-save passed;
- meaningful regulatory or compliance content;
- not nav-shell and not shallow;
- free of duplicate shell hash collision;
- reviewed for noise risk and source-health risk;
- proof-backed with saved evidence artifacts;
- repeat-baseline complete;
- `MONITOR_OK` in mass-monitor dry-run;
- passed by Source Monitor, Evidence Trail, QA/Critic, Legal Language, Product Manager, and Code Architect gates;
- activation decision recorded;
- added to `sources.json` as enabled only after all gates pass.

## 4. Why Remaining Sources Are Blocked

The earlier sprints proved the platform can activate sources, but many remaining UAE candidates are blocked by one or more of:

- noisy listing pages that need source-specific row extraction;
- JS-heavy pages where DOM selectors differ from static HTML;
- official pages returning nav-shell or low-confidence extraction;
- PDF-only or document-list sources without stable item serialization;
- source-health problems such as 403, 404, stale URLs, or WAF-like blocking;
- high noise risk from mixed marketing/news/service links;
- missing proof or repeat baseline;
- hash drift between source-lab baselines and mass-monitor dry-run.

## 5. Continuous Cycle Strategy

The sprint will run repeated safe cycles over small batches:

1. Research or confirm official endpoints.
2. Run discovery and DOM investigation.
3. Use network/XHR, sitemap, feed, document, PDF, table, listing, or rulebook discovery where needed.
4. Add or improve only the adapter needed for the real blocker.
5. Add fixture tests for the adapter or gate change.
6. Run no-save Source Lab.
7. Save evidence only for strong no-save passes.
8. Run repeat baselines.
9. Run mass-monitor dry-run.
10. Apply agent gates.
11. Update queue and activation decision.
12. Update `sources.json` only for fully proven sources.
13. Run validators.
14. Commit safe checkpoints when validation passes.
15. Continue until 50 useful sources are active or the useful official candidate pool is exhausted with exact blockers.

## 6. Adapter Families To Build Or Improve

- static HTML/article adapter
- Playwright selector adapter
- custom element adapter
- listing adapter
- table adapter
- PDF document adapter
- PDF listing adapter
- rulebook/module adapter
- register adapter
- sitemap/RSS adapter
- public JSON/API adapter
- screenshot/rendered DOM evidence adapter

Source-specific priority:

- SCA: ASP.NET listing/card/table extraction, regulation/circular/decision row hashes, noise filtering.
- ADGM/FSRA: custom element fallback, deterministic static extraction, rulebook/guidance/consultation listings.
- DFSA/DIFC: rulebook modules, Thomson Reuters official-linked modules, AML/MLRO letters, consultations, enforcement.
- VARA: rulebooks/PDF listings, framework pages, orders/enforcement, not-found shell detection.
- UAE FIU/EOCN: publications, sanctions/TFS pages, document listings, tables/registers.
- CBUAE: alternate official endpoints, regulation/circular/publication document listings, 403 classification without bypassing.
- Ministry of Economy/DNFBP: AML/DNFBP public guidance and document listings.

## 7. Source Groups To Prioritize

1. Existing active and readiness-supported sources, to preserve truth.
2. Queue entries already activation-ready or proof-backed.
3. ADGM/FSRA near-ready pages with meaningful extraction.
4. SCA regulatory listings and circulars.
5. DFSA rulebooks, AML/MLRO letters, consultations, enforcement.
6. VARA rulebook/framework/enforcement/document pages.
7. UAE FIU/EOCN public sanctions and guidance pages.
8. CBUAE only through accessible official alternatives.
9. Ministry of Economy/DNFBP, UAE legislation, FTA, and free-zone regulators only when buyer relevance is clear.

## 8. Live Validation Policy

Allowed:

- `discover-source` for specific public URLs.
- `investigate-source` for specific public URLs.
- Source Lab no-save for specific public URLs.
- Source Lab save only after strong no-save pass.
- Mass-monitor dry-run only for activation-ready or enabled sources.
- Safe batch runner with regulator, source id, or limit filters.

Forbidden:

- broad all-source monitor over candidates;
- customer alerts;
- Telegram or email;
- unfiltered all monitors;
- private portal scraping;
- access bypassing;
- LLM change decisions.

## 9. Evidence And Baseline Policy

- No-save output is preview only.
- One saved proof run is evidence, not monitoring-ready.
- Repeat baseline is required unless a written existing policy allows otherwise.
- Proof paths, normalized text paths, hashes, quality fields, evidence level, and source run ids must be recorded.
- Hash drift blocks activation unless the diff is explained and non-noisy.
- Dry-run monitoring must not create evidence or send alerts.

## 10. Sources.json Activation Policy

`sources.json` changes only when a source has:

- official and public source confirmation;
- strong no-save pass;
- proof artifacts;
- repeat baseline;
- `MONITOR_OK` dry-run;
- all required agent gates passing;
- acceptable noise and source-health risk;
- unique source id and URL;
- no duplicate shell hash;
- activation decision recorded.

## 11. Agent Gate Policy

Exactly 10 StatuteProof agents are used or manually emulated:

1. Chief of Staff: scope, sequencing, no 11th agent.
2. Product Manager: buyer value and anti-vanity source selection.
3. Code Architect: adapter and registry design safety.
4. QA/Critic: fake-ready and regression blocking.
5. Legal Language: safe wording and no legal guarantees.
6. Source Monitor: officialness, URL quality, extraction health.
7. Evidence Trail: proof paths, hashes, baselines.
8. Risk + Brief Pipeline: no brief path without evidence.
9. ICP Lead Research: MLRO/CCO relevance.
10. Outreach Writer: only if public copy changes.

If subagent tools are unavailable, gates are emulated manually and documented as such.

## 12. Validation Policy

Before each commit:

```bash
git status --short
python3 -m compileall product/regradar
python3 -m pytest product/regradar/tests -q
python3 tools/validate_source_discovery_engine.py
python3 tools/validate_source_activation_pipeline.py
python3 tools/validate_mass_source_activation_pipeline.py
python3 tools/validate_mass_monitoring_runner.py
python3 tools/validate_uae_source_pack.py
python3 tools/validate_uae_50_working_sources.py
python3 tools/validate_parser_quality.py
python3 tools/validate_workspace.py
python3 tools/validate_codex_skills.py
git diff --check
```

If frontend copy changes:

```bash
cd product/regradar/web
npm run build
npm run lint
node scripts/validate-routes.mjs
node scripts/pre-demo-smoke.mjs
```

The frontend smoke command is skipped only if the script does not exist.

## 13. Commit And Checkpoint Policy

- Commit after each safe validated batch if useful progress is made.
- Do not stage runtime junk, secrets, ignored evidence artifacts, or unrelated files.
- Use `feat: activate proof-backed UAE monitoring sources` when new active sources are added.
- Use `feat: expand UAE source-specific adapters` for adapter-only progress.
- Use `test: harden UAE source activation gates` for validator/test-only progress.
- Push after valid commits.

## 14. What Will Not Be Touched

- No deployment.
- No Cloudflare or DigitalOcean changes.
- No `.env` printing or staging.
- No Telegram/email/customer delivery.
- No private, paywalled, login, CAPTCHA, or personal-data scraping.
- No fake source counts.
- No public 50/60 claim without validator proof.
- No broad parser rewrite.
