# Source Discovery Engine Sprint Plan

## 1. Current Repo State

- Clean-state gate passed at start of sprint.
- Latest commit before this sprint: `aaa3c23 feat: build StatuteProof source activation platform`.
- Current public source truth remains: 13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation.
- Auto DOM Investigator, adapter platform, generic adapters, source-specific adapter scaffolding, Source Lab remediation controls, and strict source activation validators already exist.

## 2. Current Public Source Truth

Customer-facing truth must remain unchanged unless proof, repeat baseline, source registry state, and validators prove otherwise:

> 13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation.

This sprint must not claim 50 or 60 working sources.

## 3. Why Previous Mass Source Activation Failed

Previous attempts reached architecture improvements but not 50 working sources because many regulator pages expose their useful content behind one of these layers:

- sitemap-only or deep official endpoints not visible on the submitted page;
- JavaScript-rendered listings;
- public XHR/JSON endpoints;
- PDF/document listings;
- table/register pages;
- custom elements and chrome-heavy pages;
- nav-shell pages with weak normalized content;
- high noise/source-health risk before activation.

Running a parser directly against a generic regulator page is not enough. Discovery must identify the best endpoint and extraction path before no-save and proof/baseline work.

## 4. Why Discovery Must Happen Before Parsing

The source activation lifecycle should be:

1. Confirm official/public/permitted source.
2. Discover better endpoints via robots, sitemap, feeds, DOM links, documents, and network/XHR.
3. Score endpoint candidates for MLRO relevance, source type, adapter family, noise risk, and source-health risk.
4. Run Auto DOM investigation on the best HTML/listing/table candidates.
5. Run no-save only when the endpoint is eligible.
6. Save proof only after no-save passes strongly.
7. Repeat baseline.
8. Apply agent gates before activation.

## 5. Source Discovery Methods To Implement

- robots.txt sitemap discovery.
- sitemap index and urlset parsing.
- RSS/Atom feed discovery from HTML.
- PDF/document link discovery.
- same-domain official link extraction with max-depth and max-link limits.
- metadata discovery: title, canonical, description.
- table/listing/register/rulebook candidate detection.
- Playwright network/XHR candidate capture where scoped and permitted.
- endpoint scoring and recommended activation paths.

## 6. Agent / Skill Gate Plan

The sprint will use or manually emulate the official 10-agent roster:

- Chief of Staff: scope control and no 11th active agent.
- Product Manager: source discovery must solve MLRO/CCO source activation, not vanity source count.
- Code Architect: discovery engine must be scoped, testable, and compatible with existing adapters/evidence.
- QA / Critic: blocks fake-ready states, overclaims, weak tests, and unsafe registry changes.
- Legal Language: blocks legal advice, guarantees, regulator partnership/certification implications, and public 50/60 claims.
- Source Monitor: officialness, URL correctness, endpoint quality, source-health risk.
- Evidence Trail: no evidence or monitoring-ready claim without proof/baseline.
- Risk + Brief Pipeline: no brief eligibility without evidence.
- ICP Lead Research: endpoint relevance for UAE MLRO/CCO/compliance buyers.
- Outreach Writer: not expected unless customer-facing copy changes.

Relevant repo skills to apply or emulate: `source-monitoring-review`, `evidence-readiness-review`, `custom-source-parser`, `custom-source-monitoring-spec`, `legal-safe-copy-review`, `test-driven-development`, `systematic-debugging`, `verification-before-completion`, `webapp-testing`, `prompt-injection-review`, `evidence-audit`, `anti-slop-b2b-copy`, and `statuteproof-project-review`.

## 7. Files To Inspect

- `AGENTS.md`
- `TOOL_ROUTER.md`
- `.claude/agents/`
- `agents/`
- `.agents/skills/`
- `skills/`
- `workflows/`
- `docs/source-onboarding-pipeline-spec.md`
- `docs/source-activation-platform-final-report.md`
- `docs/source-activation-agent-council-final-review.md`
- `docs/parser-quality-gates.md`
- `product/regradar/app/dom_investigator.py`
- `product/regradar/app/source_intake.py`
- `product/regradar/app/source_quality.py`
- `product/regradar/app/source_certification.py`
- `product/regradar/app/source_tester.py`
- `product/regradar/app/scraper.py`
- `product/regradar/app/extractors.py`
- `product/regradar/app/adapters/`
- `product/regradar/app/providers/`
- `product/regradar/app/proof.py`
- `product/regradar/app/source_runs.py`
- `product/regradar/app/diff.py`
- `product/regradar/app/text_normalization.py`
- `product/regradar/app/api.py`
- `product/regradar/run.py`
- `product/regradar/sources.json`
- `product/regradar/config/uae_source_candidates.json`
- `product/regradar/config/uae_source_work_queue.json`
- `product/regradar/web/src/components/app/SourceLabPage.jsx`
- `product/regradar/tests/`
- `tools/validate_source_activation_pipeline.py`
- `tools/validate_uae_source_pack.py`
- `tools/validate_uae_50_working_sources.py`
- `tools/validate_parser_quality.py`

## 8. Files Likely To Change

- `product/regradar/app/source_discovery.py`
- `product/regradar/app/dom_investigator.py`
- `product/regradar/app/source_intake.py`
- `product/regradar/run.py`
- `product/regradar/tests/test_source_discovery.py`
- `tools/validate_source_discovery_engine.py`
- `tools/validate_source_activation_pipeline.py`
- `product/regradar/web/src/components/app/SourceLabPage.jsx` only if safe UI discovery mode is scoped.
- Documentation reports required by this sprint.

## 9. Validation Plan

Run, at minimum:

- `python3 -m compileall product/regradar`
- `python3 -m pytest product/regradar/tests -q`
- `python3 tools/validate_source_discovery_engine.py`
- `python3 tools/validate_source_activation_pipeline.py`
- `python3 tools/validate_uae_source_pack.py`
- `python3 tools/validate_uae_50_working_sources.py`
- `python3 tools/validate_parser_quality.py`
- `python3 tools/validate_workspace.py`
- `python3 tools/validate_codex_skills.py`
- `git diff --check`

If frontend is touched:

- `npm run build`
- `npm run lint`
- `node scripts/validate-routes.mjs`
- `node scripts/pre-demo-smoke.mjs` if present.

## 10. Live Validation Scope

If implementation and tests pass, run scoped discovery only against difficult official UAE source pages:

- SCA latest regulations.
- SCA AML/CFT.
- SCA decisions/circulars if official URL is available.
- DFSA rulebook Thomson Reuters.
- DFSA AML/MLRO notices.
- DFSA enforcement regulatory actions.
- CBUAE regulations.
- CBUAE circulars/publications.
- ADGM financial crime page.
- ADGM rules/regulations.
- VARA rulebook/PDF pages.
- UAE FIU/EOCN publications if public.

No broad monitoring, no all-source run, no evidence save unless no-save passes strongly.

## 11. Commit Plan

If validation passes, stage only files from this task and commit:

- `feat: build StatuteProof source discovery engine`

If the task ends as mostly tests/validators:

- `test: harden StatuteProof source discovery gates`

Push to `origin main` only after validation passes.

## 12. What Will Not Be Touched

- No deployment.
- No Cloudflare or DigitalOcean changes.
- No `.env` or secrets.
- No customer messages, Telegram, or email.
- No broad monitor/all-source runs.
- No private/login/CAPTCHA/paywalled sources.
- No LLM-based change decisions.
- No fake evidence or fake readiness.
- No `sources.json` activation unless proof, baseline, gates, and validators justify it.
- No public claim that 50/60 sources are working.
- No claim that any website can be parsed.
