# UAE 50-Source Activation Sprint Plan

Date: 2026-06-14

## 1. Current Repo State

- Clean state gate passed at start.
- Latest commit before this sprint: `0d68472 feat: strengthen StatuteProof source adapter platform`.
- Adapter platform foundation exists with `custom_element`, `listing`, and `table` generic adapters.
- `sources.json` has not been expanded from the current public truth.

## 2. Current Public Source Truth

Public truth remains:

`13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation`

This sprint must not change that truth unless strict proof, baseline, source-health, noise-risk, and agent gates pass.

## 3. Why Target 50 Official Endpoints

A professional UAE compliance monitoring baseline needs wider coverage than a 13-source MVP pack. MLRO/CCO users expect coverage across VARA, ADGM/FSRA, DFSA/DIFC, CBUAE, UAE FIU/EOCN, SCA, AML/corporate compliance, and legislation/tax surfaces.

The target is not vanity source count. The target is a larger official-source pack where every endpoint has a clear regulatory purpose and a verified extraction path.

## 4. Why 50 Must Be Proof/Baseline/Agent-Gated

A source counts as working only when it passes:

1. official/public check,
2. correct adapter/selector,
3. no-save Source Lab test,
4. quality/nav-shell/duplicate-hash checks,
5. saved evidence/proof,
6. repeat baseline,
7. noise-risk review,
8. source-health review,
9. Source Monitor gate,
10. Evidence Trail gate,
11. QA/Critic gate,
12. Legal Language gate,
13. Product Manager relevance gate.

No-save success alone is not evidence. One proof run is not monitoring-ready. A source with unresolved high noise or source-health risk cannot be activation-ready.

## 5. Source Groups To Prioritize

Priority order:

1. VARA: rulebooks, regulatory framework, enforcement/orders, public notices.
2. ADGM/FSRA: financial crime, rules/regulations, consultations, circulars, guidance.
3. DFSA/DIFC: DFSA rulebook, AML/MLRO notices, enforcement actions, consultations, DIFC laws.
4. CBUAE: rulebook/regulations, circulars, publications, AML/CFT-relevant material.
5. UAE FIU / AML / EOCN: publications, notices, sanctions/TFS material.
6. UAE SCA: regulations, decisions, circulars, AML/CFT pages if extractable.
7. Ministry of Economy AML / UAE legislation / FTA only where compliance relevance is clear.

## 6. Source-Specific Adapters Needed

P0:

- SCA rendered listing adapter for regulations and AML/CFT listings.
- ADGM/FSRA custom-element and listing normalization.
- DFSA rulebook/module listing adapter.
- CBUAE listing/PDF-document adapter for regulation/circular lists.

P1:

- FIU/EOCN document listing adapter.
- VARA rulebook/PDF listing adapter.
- DIFC laws/regulations listing adapter.

P2:

- PDF document adapter improvements.
- Screenshot/WARC evidence enrichment.
- Feed/sitemap adapter if official feeds exist.

## 7. Evidence / Baseline Plan

1. Run no-save first for selected targets.
2. Save evidence only for sources that pass no-save strongly.
3. Repeat baseline only for sources with saved proof and acceptable noise/source-health risk.
4. Do not mark monitoring-ready from one run.
5. Do not update `sources.json` until all gates pass.

## 8. Agent Gate Plan

Agents will be emulated manually using repo agent docs and skills:

- Source Monitor: officialness, URL, selector/adapter, source-health.
- Evidence Trail: proof paths, hashes, baseline count, evidence level.
- QA/Critic: false-ready, nav-shell, duplicate hashes, high noise.
- Legal Language: no legal advice, guarantee, certification, or inflated source claims.
- Product Manager: MLRO/CCO buyer relevance and no vanity padding.
- Code Architect: scoped adapters, tests, no broad rewrite.

## 9. Validation Plan

Run:

- `python3 -m compileall product/regradar`
- `python3 -m pytest product/regradar/tests -q`
- `python3 tools/validate_uae_source_pack.py`
- `python3 tools/validate_uae_50_working_sources.py`
- `python3 tools/validate_source_readiness_summary.py` if present
- `python3 tools/validate_parser_quality.py`
- `python3 tools/validate_workspace.py`
- `python3 tools/validate_codex_skills.py`
- `git diff --check`

Frontend validation only if frontend files change.

## 10. Commit Plan

If validation passes, stage only files from this sprint.

- If 50 truly reached: `feat: activate gated UAE 50-source monitoring pack`
- If fewer than 50 but real adapter/pipeline progress: `feat: expand UAE source adapters and activation pipeline`
- If mostly docs/tests: `test: harden UAE 50-source activation gates`

## 11. What Will Not Be Touched

- No deployment.
- No Cloudflare/DigitalOcean changes.
- No secrets or `.env`.
- No Telegram/email/customer delivery.
- No broad monitoring or all-source monitor runs.
- No private portals, CAPTCHA, login, or paywall bypass.
- No fake evidence or fake source readiness.
- No public “50 working” or “60 validated” claims unless validators prove it.
