# UAE 60-Source Pack Expansion Plan

## 1. Current Source State

Latest committed truth:

- 13 enabled UAE sources.
- 9 readiness-supported.
- 4 under extraction remediation.
- DFSA remains remediation.
- The product must not claim 40, 60, or “validated” sources until candidate discovery and no-save validation prove it.

## 2. Why 13 Sources Is Too Small

13 sources can demonstrate the product architecture, evidence trail, Source Lab, and readiness honesty. It is not enough to feel like a professional UAE compliance monitoring baseline for MLROs, CCOs, and compliance managers who must track multiple regulators, free zones, circulars, rulebooks, enforcement notices, AML pages, consultations, guidance, registers, and legislation surfaces.

A serious paid UAE Monitor should feel like StatuteProof knows the UAE compliance surface before the buyer starts configuring custom URLs. Source Lab helps personalize monitoring, but it does not replace the trust created by a strong default official-source map.

## 3. Why 60 Must Mean Official Endpoints

60 must mean official or officially linked source endpoints, not random websites. A source count is only useful if each source has:

- official or officially linked provenance;
- clear MLRO/compliance relevance;
- public accessibility;
- testable extraction behavior;
- a readiness status;
- a failure/remediation reason where not ready;
- a non-duplicative role in the pack.

The goal is not “60 validated sources.” The goal is a high-trust candidate and validation pipeline that can eventually support a 40-60 endpoint UAE baseline.

## 4. Expansion Strategy

1. Inventory the current 13-source registry and readiness reports.
2. Define a professional UAE regulatory source taxonomy.
3. Discover official or officially linked candidate endpoints by regulator/category.
4. Store candidates in a separate machine-readable candidate file, not active `sources.json`.
5. Apply a no-garbage policy before testing.
6. Add a validator to prevent duplicate, uncertain, rejected, or overclaimed candidate records.
7. Run only scoped no-save Source Lab tests for priority candidates where safe.
8. Keep untested sources as candidates, remediation, or rejected; do not enable them by default.
9. Propose plan-specific packs for demo, source readiness review, Founding Pilot, UAE Monitor, and Consultant/Enterprise.
10. Update `sources.json` only if strict validation justifies it.

## 5. Source Validation Methodology

Candidate status levels:

- `candidate`: official-looking and relevant, not tested yet.
- `no_save_tested`: Source Lab tested without evidence write.
- `readiness_supported`: no-save extraction produced meaningful content, non-nav-shell, acceptable quality, unique hash, clear source role.
- `remediation`: useful but parser/selector/source model needs work.
- `blocked`: login/CAPTCHA/paywall/private/legally risky/unavailable.
- `rejected`: not official, not relevant, duplicate, marketing page, wrong country, or otherwise garbage.

Strict rules:

- no-save is preview only;
- one successful test is not monitoring-ready;
- evidence confirmed requires saved proof;
- activation readiness requires baseline/approval;
- DFSA stays remediation until strict checks pass.

## 6. Agents / Skills To Use

Conceptual agent gates:

- Product Manager: source pack relevance and plan packaging.
- Source Monitor: source identity, URL, readiness status, and remediation truth.
- Evidence Trail: proof/evidence boundaries.
- QA / Critic: no source-count inflation or fake-ready status.
- Legal Language: no legal advice, no regulator certification, no guarantee claims.
- Code Architect: candidate schema, validators, and clean implementation.
- ICP Lead Research: MLRO/VASP/fintech buyer relevance.

Repo skills to apply conceptually:

- source-monitoring-review
- evidence-readiness-review
- custom-source-monitoring-spec
- custom-source-parser
- legal-safe-copy-review
- statuteproof-project-review
- verification-before-completion
- webapp-testing
- prompt-injection-review
- test-driven-development
- anti-slop-b2b-copy

## 7. Files To Inspect

- `AGENTS.md`
- `TOOL_ROUTER.md`
- `.agents/skills/`
- `skills/`
- `workflows/`
- `prompts/`
- `product/regradar/sources.json`
- `product/regradar/app/source_readiness.py`
- `product/regradar/app/source_intake.py`
- `product/regradar/app/source_quality.py`
- `product/regradar/app/source_certification.py`
- `product/regradar/app/api.py`
- `product/regradar/web/src/data/appMockData.js`
- `product/regradar/web/src/components/app/SourcesPage.jsx`
- `product/regradar/web/src/components/app/DashboardHome.jsx`
- `product/regradar/web/src/components/Coverage.jsx`
- source-readiness, DFSA, parser, and 10/10 reports in `docs/`

## 8. Files Likely To Change

- `docs/uae-source-pack-agent-review-plan.md`
- `docs/current-source-pack-inventory-before-expansion.md`
- `docs/uae-regulatory-source-taxonomy.md`
- `docs/uae-60-source-candidate-discovery.md`
- `product/regradar/config/uae_source_candidates.json`
- `docs/no-garbage-source-policy.md`
- `tools/validate_uae_source_pack.py`
- `docs/uae-source-pack-no-save-validation-report.md`
- `docs/uae-default-source-packs-by-plan.md`
- `docs/source-registry-expansion-change-report.md`
- `docs/source-monitor-operational-risk-alerts.md`
- `docs/acknowledge-and-assess-workflow-spec.md`
- `docs/uae-60-source-pack-final-report.md`

`sources.json` should change only if validation proves a source is safe to add with conservative status. This run will prefer a candidate file over active registry changes.

## 9. Validation Plan

Run from project root:

```bash
git status --short
python3 -m compileall product/regradar
python3 tools/validate_uae_source_pack.py
python3 tools/validate_source_readiness_summary.py  # if present
python3 tools/validate_parser_quality.py
python3 tools/validate_workspace.py
python3 tools/validate_codex_skills.py
git diff --check
```

If frontend is touched:

```bash
cd product/regradar/web
npm run build
npm run lint
node scripts/validate-routes.mjs
node scripts/pre-demo-smoke.mjs  # if present
```

## 10. Commit Plan

If validation passes, stage only files from this source-pack task and commit:

```bash
git commit -m "docs: define UAE 60-source pack validation strategy"
```

If `sources.json` changes because strict validation justified it, use:

```bash
git commit -m "feat: add UAE source pack candidates and readiness validation"
```

Then push to `origin main`.

## 11. What This Task Will Not Touch

- production deployment;
- Cloudflare or DigitalOcean;
- live customer delivery;
- broad monitoring or all-source monitoring;
- `.env` or secrets;
- fake source readiness;
- fake evidence;
- customer-facing 40/60 source claims;
- live Stripe/payment activation;
- private/login/CAPTCHA/paywall sources;
- non-UAE or wrong-country regulator sources.
