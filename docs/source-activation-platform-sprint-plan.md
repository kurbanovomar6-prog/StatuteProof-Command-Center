# Source Activation Platform Sprint Plan

Date: 2026-06-15

## 1. Current Repo State

- Clean state gate passed before work began.
- Latest commit at start: `a1c6aa4 feat: expand UAE source adapters and activation pipeline`.
- Current public source truth: `13 enabled UAE sources / 9 readiness-supported / 4 remediation`.
- The adapter platform exists with generic and early source-specific adapters, but the previous 50-source activation attempt did not activate new sources.
- `sources.json` must remain unchanged unless proof, baseline, and gates justify activation.

## 2. Why Mass Source Activation Failed Before

The previous sprint showed that the blocker is not candidate count. The blocker is source activation readiness:

- Several candidate URLs are stale, moved, or return not-found shells.
- Many regulator pages are rendered, listing-heavy, or chrome-heavy.
- Generic full-page extraction often returns navigation, widgets, or shell text instead of regulatory items.
- No-save checks did not provide enough strict passes to justify saved evidence.
- No new source had proof, repeat baseline, noise review, source-health review, and agent gates.

## 3. Internal Meaning of "95%"

Internally, "95%" means a long-term engineering aspiration for public official/regulatory sources that are technically accessible and permitted to monitor. It does not mean all websites, private portals, paywalled pages, CAPTCHA pages, or protected systems.

This must not become public copy. Customer-safe wording remains:

`StatuteProof can test and monitor public official or officially linked sources that are technically accessible and permitted to be monitored.`

## 4. Architecture Goals

This sprint will build the next layer of the source activation platform:

1. Auto DOM Investigator for selector and adapter recommendations.
2. Expanded adapter catalog metadata and source-specific extraction strategies.
3. Quality gate before save with structured failure codes.
4. Evidence/repeat-baseline automation plan and CLI groundwork where safe.
5. Work queue and agent gate hardening.
6. Failure-reason intelligence that explains remediation paths.
7. Source Lab UI improvements for remediation visibility.

## 5. Source Groups To Prioritize

Priority source groups remain:

- SCA: ASP.NET/listing rows/detail links.
- DFSA: rulebook modules, AML/MLRO tabs, enforcement listing.
- CBUAE: circular/regulation/document listings.
- ADGM/FSRA: custom elements and rules/guidance listings.
- VARA: rulebooks/PDF listings and not-found shell detection.
- UAE FIU/EOCN: publication/document listings.

## 6. Files To Inspect

- `product/regradar/app/source_intake.py`
- `product/regradar/app/source_quality.py`
- `product/regradar/app/source_certification.py`
- `product/regradar/app/adapters/`
- `product/regradar/app/extractors.py`
- `product/regradar/app/scraper.py`
- `product/regradar/app/api.py`
- `product/regradar/run.py`
- `product/regradar/web/src/components/app/SourceLabPage.jsx`
- `product/regradar/config/uae_source_work_queue.json`
- `tools/validate_uae_50_working_sources.py`
- `tools/validate_uae_source_pack.py`
- `tools/validate_parser_quality.py`

## 7. Files Likely To Change

- `product/regradar/app/dom_investigator.py`
- `product/regradar/app/adapters/adapter_platform.py`
- `product/regradar/app/source_intake.py`
- `product/regradar/app/api.py`
- `product/regradar/run.py`
- `product/regradar/web/src/components/app/SourceLabPage.jsx`
- `product/regradar/tests/`
- `tools/validate_source_activation_pipeline.py`
- selected docs under `docs/`

## 8. Agent / Skill Gate Plan

Agent gates will be emulated manually unless an executable subagent tool is available:

- Source Monitor blocks unofficial, inaccessible, shell, noisy, or unstable sources.
- Evidence Trail blocks evidence claims without proof and baseline.
- QA/Critic blocks fake readiness and broken status mapping.
- Legal Language blocks legal advice, guarantees, certification, and "any website" claims.
- Product Manager blocks vanity sources that do not help an MLRO/CCO.
- Code Architect blocks broad rewrites and unsafe dependency choices.

## 9. Test Plan

Use TDD for new behavior:

- DOM investigator fixture tests.
- Adapter catalog tests.
- Failure-code mapping tests.
- No-save/evidence/activation gate tests.
- Validator tests where feasible.
- Frontend build/lint/route validation if Source Lab UI changes.

## 10. Live Validation Plan

Live validation is scoped only after unit tests pass. It may include targeted no-save checks for SCA, DFSA, CBUAE, ADGM, VARA, and UAE FIU/EOCN pages. No broad monitoring and no customer delivery.

No save is allowed unless no-save passes strict gates.

## 11. Commit Plan

If validation passes, stage only task files. Commit:

`feat: build StatuteProof source activation platform`

If validation fails, do not commit code. Commit docs only if safe and useful.

## 12. What Will Not Be Touched

- No deployment.
- No Cloudflare or DigitalOcean changes.
- No secrets or `.env`.
- No Telegram/email/customer delivery.
- No broad monitoring.
- No fake readiness.
- No public `50/60 ready` claim.
- No `sources.json` activation unless strict proof/baseline/gates pass.
