# Mass Source Activation System Audit Plan

Date: 2026-06-15

## 1. Current Repo State

- Clean worktree at start: yes.
- Latest commit inspected before work: `a803fb7 feat: build StatuteProof source discovery engine`.
- Product code lives under `product/regradar`.

## 2. Current Source Truth

Customer-facing truth remains:

- 13 enabled UAE sources.
- 9 readiness-supported.
- 4 under extraction remediation.

This sprint must not change that truth unless `sources.json`, proof/baseline artifacts, activation gates, and validators prove a new state.

## 3. Why Mass Source Activation Is Blocked

The current system has strong pieces but still needs a safer batch layer:

- Source Discovery Engine can find candidate endpoints, but candidates are not yet governed by a single mass activation queue.
- Auto DOM Investigator and adapters can recommend extraction strategies, but source-specific listing/table/PDF adapters still fail on several UAE regulator pages.
- Evidence/proof and repeat baseline gates exist, but batch activation needs a validator that blocks fake `activation_ready` states.
- Source Lab UI explains preview/evidence states, but mass onboarding needs a queue-level state contract and audit trail.
- Some legacy discovery/source connector paths may still overlap with the new discovery engine and need classification as keep/refactor/deprecate/delete.

## 4. Files / Systems To Inspect

- `product/regradar/app/`
- `product/regradar/app/adapters/`
- `product/regradar/app/providers/`
- `product/regradar/app/source_connector/`
- `product/regradar/run.py`
- `product/regradar/sources.json`
- `product/regradar/config/`
- `product/regradar/tests/`
- `product/regradar/web/src/components/app/SourceLabPage.jsx`
- `product/regradar/web/src/components/app/SourcesPage.jsx`
- `product/regradar/web/src/components/app/Dashboard.jsx`
- `tools/`
- `docs/`
- `workflows/`
- `prompts/`
- Repo file inventory from `rg --files`.

Generated/vendor/runtime directories may be checked for ignore hygiene but will not be deeply audited.

## 5. Agent Gate Plan

Agents will be emulated manually unless executable subagent tooling is available:

- Chief of Staff: scope control and no 11th agent.
- Product Manager: blocks vanity source-count padding.
- Code Architect: blocks broad rewrites and unsafe dependencies.
- QA/Critic: blocks fake-ready states and broken gates.
- Legal Language: blocks overclaims and compliance/legal-advice language.
- Source Monitor: checks officialness, source IDs, extraction, health states.
- Evidence Trail: checks proof paths, source runs, hashes, repeat baselines.
- Risk + Brief Pipeline: ensures no brief pipeline uses incomplete evidence.
- ICP Lead Research: checks MLRO/CCO source relevance.
- Outreach Writer: only used if public copy changes.

## 6. Safe Cleanup Policy

No code will be deleted merely because it is old or messy. Cleanup is allowed only when:

1. `rg` references show it is unused or superseded.
2. It is not required by CLI/API/tests/docs.
3. A rollback risk is documented.
4. Tests and validators pass after the change.

If uncertain, mark as `deprecate` in the cleanup inventory instead of deleting.

## 7. Validation Plan

Run from repo root:

- `python3 -m compileall product/regradar`
- `python3 -m pytest product/regradar/tests -q`
- `python3 tools/validate_source_discovery_engine.py`
- `python3 tools/validate_source_activation_pipeline.py`
- `python3 tools/validate_mass_source_activation_pipeline.py`
- `python3 tools/validate_uae_source_pack.py`
- `python3 tools/validate_uae_50_working_sources.py`
- `python3 tools/validate_parser_quality.py`
- `python3 tools/validate_workspace.py`
- `python3 tools/validate_codex_skills.py`
- `git diff --check`

If frontend changes:

- `npm run build`
- `npm run lint`
- `node scripts/validate-routes.mjs`

## 8. Commit Plan

If validation passes and code improves:

`git commit -m "feat: harden StatuteProof mass source activation pipeline"`

If mostly audit/docs:

`git commit -m "docs: audit StatuteProof mass source activation system"`

Push to `origin main` after commit.

## What Will Not Be Touched

- No deployment or infrastructure.
- No Cloudflare/DigitalOcean changes.
- No secrets or `.env`.
- No customer messages.
- No broad monitoring or all-source monitor run.
- No fake evidence or fake readiness.
- No active `sources.json` expansion without proof/baseline/gates.
