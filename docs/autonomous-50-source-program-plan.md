# Autonomous UAE 50-Source Program Plan

Date: 2026-06-15

## 1. Current Repo State

- Worktree clean before this plan.
- Latest commit: `b3a3dbd feat: activate JS-heavy UAE FIU source`.
- Current product path: `product/regradar`.
- Current mode: autonomous, iterative source activation cycles with strict proof/baseline/gate requirements.

## 2. Current Public Source Truth

Verified from the current registry and validators after the latest FIU activation:

- 28 enabled UAE sources.
- 24 readiness-supported active UAE sources.
- 4 under extraction remediation.
- 50 has not been reached.

Older reports that mention 13/9/4, 19/15/4, 20/16/4, 23/19/4, 24/20/4, or 25/21/4 are historical, not current truth.

## 3. Current Activation-Ready Count

- `sources.json`: 22 enabled UAE `status: active` sources.
- `uae_source_work_queue.json`: 10 activation-ready queue entries.
- `mass_source_activation_queue.json`: 7 activation-ready mass-queue entries.
- The 50-source target requires 28 more readiness-supported active UAE sources in `sources.json`.

## 4. Working Source Definition

A source counts only when it is official or officially linked, public, UAE-relevant, meaningful to MLRO/CCO users, extracted by a correct adapter/selector/API/PDF strategy, passes no-save, is not nav-shell/shallow/duplicate-shell, has reviewed noise/source-health risk, has saved proof, has repeat baseline, passes Source Monitor, Evidence Trail, QA/Critic, Legal Language, Product Manager, and Code Architect gates, passes validators, and is safely added to `sources.json`.

No-save-only, evidence-only, one-run-only, duplicate-hash, high-noise, high-health-risk, generic homepage, or nav-shell sources do not count.

## 5. Why 50 Must Be Gated

The product promise is evidence-backed monitoring intelligence, not URL collection. A fake 50 would damage trust, pollute alerts, and create legal/commercial risk. The pack must prove extraction quality, hashes, evidence paths, baseline stability, source-health status, and clear failure reasons.

## 6. Why Batch-Onboarding Matters

Manual one-by-one activation is too slow. The target architecture is a factory:

candidate discovery -> official/public check -> adapter recommendation -> no-save -> quality/noise/source-health scoring -> evidence save -> repeat baseline -> agent gates -> validators -> `sources.json` activation.

Batch-onboarding is only safe if weak candidates stay candidate/remediation/blocked and cannot become active by accident.

## 7. Current Adapter Platform Status

Implemented platform capabilities include:

- generic adapter platform;
- Auto DOM Investigator;
- Source Discovery Engine;
- Source Lab remediation controls;
- safe batch activation runner;
- mass monitoring runner;
- source-specific adapter families for ADGM, DFSA, SCA, FIU/EOCN, VARA, CBUAE in partial form;
- validators for source discovery, activation, mass activation, mass monitoring, parser quality, workspace, and skills.

## 8. Biggest Parser Weaknesses

- JS-heavy SPA pages still frequently render nav/filter shells.
- SCA listing/filter pages need deeper item selectors or XHR endpoint isolation.
- ADGM alternate media/data-protection components need a selector map beyond `adgm-page`.
- Some document listings are close to threshold and need richer metadata/context extraction.
- The activation applier only recently learned to update existing source records and preserve adapter config; this must stay tested.

## 9. Biggest Source-Onboarding Weaknesses

- Candidate volume exists, but no-save strong-pass conversion is low.
- Duplicate route variants can produce identical normalized hashes and must be held.
- Work queues and scoreboards are fragmented across multiple JSON files.
- Batch runner can process candidates, but automatic evidence/baseline promotion must stay conservative.

## 10. Biggest Evidence/Baseline Weaknesses

- Evidence artifacts are generated safely, but certification history can mix pre-normalization and post-normalization hashes.
- Baseline stability should be evaluated against the relevant current extraction/normalization version, and historical drift must be documented.
- Some source entries lack full adapter config unless validators/tools enforce it.

## 11. Biggest Validator Weaknesses

- Current validators block fake truth counts and active sources without proof/baseline/gates.
- Missing or future validators should cover batch-onboarding scoreboard integrity, noise/materiality status, source-health status, and duplicate normalized hashes across active records.

## 12. Alert-Fatigue And Source-Health Risks

- Listing pages can churn due to pagination, counters, cards, and timestamps.
- News/media pages may generate noisy low-materiality updates.
- Public source access can change from Playwright-accessible to 403 or selector-broken.
- Mass monitoring must default to no alerts and activation-ready/enabled sources only.

## 13. Autonomous Cycle Plan

Each cycle:

1. Recompute current truth and scoreboard.
2. Select the highest-leverage batch of 5-10 official candidates.
3. Research if local selectors/adapters are insufficient.
4. Write fixture tests before adapter changes.
5. Implement scoped parser/adapter/noise/source-health improvements.
6. Run no-save.
7. Save evidence only for strong passes.
8. Run repeat baseline and mass-monitor dry-run.
9. Apply agent gates.
10. Update queue, scoreboard, and `sources.json` only when gates pass.
11. Run validators, commit, push.
12. If under 50, write/execute the next cycle prompt if context allows.

## 14. Source Groups To Prioritize

1. UAE FIU/EOCN document and AML/CFT listings that are already close to threshold.
2. SCA JS-rendered regulatory listings and circulars.
3. ADGM alternate component pages and RA/FSRA registers.
4. VARA rulebook/PDF/enforcement pages with stable official endpoints.
5. DFSA/DIFC exact module URLs where access allows Playwright extraction.
6. CBUAE official alternate PDF/document endpoints where no WAF bypass is needed.
7. Ministry of Economy DNFBP/AML and official legislation/tax pages only when MLRO/CCO relevance is clear.

## 15. Internet/GitHub/YouTube Research Plan

Use official docs and open-source research only when local remediation is blocked. Priority topics:

- Playwright wait/network patterns for JS-heavy listings.
- Robust listing/document extraction patterns.
- PDF metadata/text extraction best practices.
- Website change-detection false-positive filtering.
- Alert-fatigue/materiality scoring.

Evaluate licenses before adapting ideas. Do not vendor repositories or copy code blindly.

## 16. Files Likely To Change

- `product/regradar/app/adapters/`
- `product/regradar/app/source_intake.py`
- `product/regradar/app/source_quality.py`
- `product/regradar/app/source_certification.py`
- `product/regradar/app/scraper.py`
- `product/regradar/app/mass_source_activation_runner.py`
- `product/regradar/app/mass_monitoring_runner.py`
- `product/regradar/run.py`
- `product/regradar/sources.json`
- `product/regradar/config/uae_50_activation_scoreboard.json`
- `product/regradar/config/uae_source_work_queue.json`
- `product/regradar/config/mass_source_activation_queue.json`
- `product/regradar/tests/`
- `tools/validate_*.py`
- `docs/autonomous-*.md`

## 17. Validation Plan

After each cycle:

- `python3 -m compileall product/regradar`
- `python3 -m pytest product/regradar/tests -q`
- `python3 tools/validate_uae_source_pack.py`
- `python3 tools/validate_uae_50_working_sources.py`
- `python3 tools/validate_source_readiness_summary.py` if present
- `python3 tools/validate_parser_quality.py`
- `python3 tools/validate_workspace.py`
- `python3 tools/validate_codex_skills.py`
- `python3 tools/validate_batch_onboarding.py` if created
- `git diff --check`

Frontend validation only if frontend changes.

## 18. Commit Plan

Commit only after validation passes. Stage only task files. Do not stage secrets, runtime junk, unrelated files, or ignored evidence artifacts. Push to `origin/main` after safe commits.

## 19. What Must Not Be Touched

- No deploys.
- No Cloudflare/DigitalOcean changes.
- No `.env` printing or commits.
- No customer/Telegram/email messages.
- No broad all-source monitoring over candidates.
- No access-control bypass.
- No private portals, personal data, CAPTCHA, paywall scraping.
- No fake evidence or source readiness.
- No 50/60 claims unless validators prove them.
- No legal advice, compliance guarantee, or regulator certification claim.
