# SCA / DFSA / CBUAE Batch Remediation Plan

Date: 2026-06-15

## 1. Current Repo State

- Clean worktree before start: yes.
- Latest commit inspected: `5af6feb feat: harden StatuteProof mass source activation pipeline`.
- Product code lives in `product/regradar`.

## 2. Current Public Source Truth

Customer-facing source truth remains:

- 13 enabled UAE sources.
- 9 readiness-supported.
- 4 under extraction remediation.

This sprint must not change public truth unless proof, repeat baseline, source gates, registry updates, and validators prove it.

## 3. What Last Sprint Proved

- Source Discovery Engine, Auto DOM Investigator, adapter platform, Source Lab remediation UI, mass source activation state machine, queue, and validator exist.
- The system now blocks fake activation states.
- SCA discovery finds table/listing candidates but also noisy generic official links.
- DFSA AML/MLRO resolves to a `/summary` page but DOM type was unknown in the scoped check.
- CBUAE regulations returned HTTP 403.
- ADGM no-save extracted content but stayed below save quality threshold.
- VARA framework test URL returned HTTP 404.

## 4. Why SCA / DFSA / CBUAE Are Next

- SCA can unlock multiple regulatory/listing/register endpoints if item extraction and noisy-link filtering improve.
- DFSA is core to UAE/DIFC compliance monitoring, but selector/module handling must be more deterministic.
- CBUAE is a high-value regulator, but 403/access-safe alternate discovery must be handled honestly.

## 5. Source-Specific Blockers

SCA:

- Same-domain discovery over-includes generic pages.
- Some SCA URLs appear malformed with repeated path segments.
- Listing/table extraction needs stable row-level title/link/date handling.

DFSA:

- AML/MLRO resolved `/summary` page needs better DOM/selector classification.
- Rulebook/module extraction needs fixture-backed parsing.
- Unknown DOM must map to remediation, not readiness.

CBUAE:

- Tested regulations page returned 403.
- The system must classify access blocks clearly and try only safe official alternate discovery paths.

## 6. Batch Runner Design

Build a safe queue runner around `mass_source_activation_queue.json`:

- default mode is discovery/no-save only;
- no evidence save unless explicit `--save-passing`;
- no repeat baseline unless explicit `--repeat-baseline`;
- no `sources.json` update;
- no customer messages;
- no broad monitoring;
- updates queue entries and re-evaluates activation state with `evaluate_activation()`;
- outputs structured JSON summary.

## 7. Agent / Skill Gate Plan

Use or emulate the 10 official agents:

- Chief of Staff: scope, no broad monitoring, no 11th agent.
- Product Manager: source relevance for MLRO/CCO buyers.
- Code Architect: safe architecture and no broad rewrites.
- QA / Critic: blocks fake readiness and weak tests.
- Legal Language: blocks overclaims.
- Source Monitor: officialness, selectors, source-health/noise.
- Evidence Trail: proof/baseline/evidence status.
- Risk + Brief Pipeline: no brief use without complete evidence.
- ICP Lead Research: buyer relevance.
- Outreach Writer: only if public/customer copy changes.

Relevant skills: source-monitoring-review, evidence-readiness-review, custom-source-parser, custom-source-monitoring-spec, legal-safe-copy-review, systematic-debugging, test-driven-development, verification-before-completion, prompt-injection-review.

## 8. Files To Inspect

- `product/regradar/app/source_discovery.py`
- `product/regradar/app/dom_investigator.py`
- `product/regradar/app/source_intake.py`
- `product/regradar/app/mass_source_activation.py`
- `product/regradar/app/adapters/`
- `product/regradar/run.py`
- `product/regradar/config/mass_source_activation_queue.json`
- `product/regradar/config/uae_source_candidates.json`
- `product/regradar/config/uae_source_work_queue.json`
- `product/regradar/sources.json`
- `product/regradar/tests/`
- `tools/validate_mass_source_activation_pipeline.py`
- `tools/validate_source_discovery_engine.py`
- `tools/validate_source_activation_pipeline.py`
- `tools/validate_uae_50_working_sources.py`

## 9. Files Likely To Change

- `product/regradar/app/source_discovery.py`
- `product/regradar/app/adapters/adapter_platform.py`
- `product/regradar/app/mass_source_activation_runner.py`
- `product/regradar/run.py`
- `product/regradar/config/mass_source_activation_queue.json`
- `product/regradar/tests/`
- `tools/validate_mass_source_activation_pipeline.py`
- sprint reports in `docs/`

## 10. Validation Plan

Run:

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

Frontend validation only if frontend files are touched.

## 11. Live Validation Scope

Scoped discovery/no-save only:

1. SCA latest regulations.
2. SCA AML/CFT.
3. SCA circulars/rules if discovered.
4. DFSA AML/MLRO resolved `/summary`.
5. DFSA rulebook if official endpoint is clear.
6. CBUAE regulations or safe official alternate endpoint.

No evidence save unless a later explicit scoped command is justified and strong no-save passes.

## 12. Commit Plan

If validation passes and code improves:

`git commit -m "feat: add safe batch source activation runner"`

If mostly tests/docs:

`git commit -m "test: harden SCA DFSA CBUAE source remediation gates"`

Push to `origin main`.

## 13. What Will Not Be Touched

- No deployment or infrastructure.
- No Cloudflare/DigitalOcean.
- No secrets or `.env`.
- No customer messages.
- No broad monitoring or all-source runs.
- No fake evidence/readiness.
- No `sources.json` activation for unproven sources.
- No public 50/60-source claims.
