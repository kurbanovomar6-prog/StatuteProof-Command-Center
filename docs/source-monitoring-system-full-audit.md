# Source Monitoring System Full Audit

Date: 2026-06-15

## Scope

This audit inspected the StatuteProof source-monitoring surface needed for mass official-source activation:

- repo inventory from `rg --files`: 669 tracked/workspace-visible files;
- backend source discovery, DOM investigation, source intake, adapters, proof, source runs, diff/hash, API;
- source registry and candidate/work queue config;
- Source Lab, Sources, and Dashboard frontend surfaces;
- tools/validators, docs, workflows, prompts, and agent instructions.

Generated/vendor/runtime paths were not deeply audited except for ignore/validator relevance.

## Source Discovery Flow

Relevant files:

- `product/regradar/app/source_discovery.py`
- `product/regradar/run.py`
- `product/regradar/app/api.py`
- `product/regradar/web/src/components/app/SourceLabPage.jsx`
- `tools/validate_source_discovery_engine.py`

What exists:

- `discover-source` and `source-discovery-lab` CLI commands exist.
- Discovery covers robots/sitemap, feeds, DOM links, document/PDF links, network candidates, same-domain candidates, metadata, and candidate generation.
- Source Lab exposes discovery mode and does not make discovered candidates active by default.

Issues:

- `run.py` still contains old help text describing `discover-source` as the "Source Connection Engine" and saying JSON exports `reports/discover_source_*.json`; the current implementation prints structured JSON.
- Legacy `source_connector` discovery remains reachable through older command paths and should be refactored/deprecated carefully, not deleted blindly.

## DOM Investigator Flow

Relevant files:

- `product/regradar/app/dom_investigator.py`
- `product/regradar/app/source_intake.py`
- `product/regradar/tests/test_dom_investigator.py`

What exists:

- Deterministic HTML investigator detects likely article/main content, listings, tables, PDF links, custom elements, nav-shell risk, shallow content, noise risk, source-health risk, and selectors.
- Source intake integrates DOM investigation into Source Lab output.

Mass activation blocker:

- DOM investigation is per-source. It is not yet tied to a general batch queue that records state transitions across discovery, no-save, proof save, repeat baseline, and gate review.

## Adapter Registry Flow

Relevant files:

- `product/regradar/app/adapters/adapter_platform.py`
- `product/regradar/app/adapters/registry.py`
- `product/regradar/app/adapters/base.py`
- `product/regradar/tests/test_adapter_platform.py`

What exists:

- Generic adapter platform exists with static HTML, Playwright selector, custom element, listing, table, PDF/listing/register/feed/API/rendered evidence placeholders, and several UAE-specific adapter names.
- Adapter metadata flows through Source Lab output.

Mass activation blocker:

- Adapter existence does not mean source activation. Source-specific regulator pages still require tested selectors, proof, repeat baselines, and noise/source-health review.

## Source Lab No-Save Flow

Relevant files:

- `product/regradar/app/source_intake.py`
- `product/regradar/run.py`
- `product/regradar/app/api.py`
- `product/regradar/web/src/components/app/SourceLabPage.jsx`

What exists:

- No-save tests can run through Source Lab.
- No-save output includes quality score, status, failure code, remediation hint, DOM investigation, adapter metadata, hash, noise risk, source-health risk, and customer-safe evidence/activation fields.
- `build_source_lab_contract()` prevents no-save tests from claiming evidence or monitoring activation.

Mass activation blocker:

- No-save success is still source-local. There is no general mass activation validator outside the UAE 50 queue that enforces the same state model for future jurisdictions/source packs.

## Evidence Save Flow

Relevant files:

- `product/regradar/app/source_intake.py`
- `product/regradar/app/proof.py`
- `product/regradar/app/source_runs.py`
- `product/regradar/app/source_certification.py`
- `product/regradar/tests/test_chunk_diff_and_proof.py`

What exists:

- Evidence write is gated by source-intake status.
- Proof records include hashes, timestamps, official URL, disclaimer, and artifact references.
- Source runs are append-only JSONL records with hash/diff metadata.
- One saved run is not monitoring-ready; certification requires repeat baseline policy.

Mass activation blocker:

- Evidence flow exists, but batch activation needs a queue-level validator that checks proof paths and baseline counts before any source can become `activation_ready`.

## Source Runs / Proof Flow

Relevant files:

- `product/regradar/app/source_runs.py`
- `product/regradar/app/proof.py`
- `product/regradar/app/source_certification.py`

What exists:

- Source runs store append-only state.
- Proof paths and normalized hashes can support evidence review.
- Certification model has explicit `baseline_runs_required` / `baseline_runs_completed`.

Risk:

- Alert/delivery logic must never run from batch onboarding unless explicitly scoped. This sprint does not run broad monitoring.

## Repeat Baseline Flow

Relevant files:

- `product/regradar/app/source_certification.py`
- `product/regradar/config/uae_source_work_queue.json`
- `tools/validate_uae_50_working_sources.py`

What exists:

- Baseline completion is already enforced for UAE 50-source activation.

Gap:

- The enforcement is UAE queue-specific. A jurisdiction-agnostic mass activation queue is needed for future batches.

## Diff / Hash Flow

Relevant files:

- `product/regradar/app/text_normalization.py`
- `product/regradar/app/diff.py`
- `product/regradar/app/chunk_diff.py`
- `product/regradar/app/source_runs.py`

What exists:

- Text normalization and hash creation are centralized.
- Diff/proof logic can support update review.

Mass activation blocker:

- Duplicate boilerplate/hash checks exist at source-intake level, but mass queue activation needs validator enforcement too.

## Activation Readiness Flow

Relevant files:

- `product/regradar/app/source_intake.py`
- `product/regradar/app/source_certification.py`
- `product/regradar/config/uae_source_work_queue.json`
- `tools/validate_uae_50_working_sources.py`

What exists:

- Current UAE queue has 78 entries and gate fields.
- The UAE 50 validator blocks activation-ready sources unless proof, baseline, gates, adapter status, and risk fields pass.

Gap:

- There is no general-purpose mass source activation queue/validator for the broader monitoring system.

## Sources JSON Update Flow

Relevant files:

- `product/regradar/sources.json`
- `tools/validate_uae_source_pack.py`
- `tools/validate_source_readiness_summary.py` if present

Current decision:

- `sources.json` must not be expanded from this audit. It remains the active registry, and public truth remains 13 enabled / 9 readiness-supported / 4 remediation.

Gap:

- The system needs an explicit activation-decision stage before any queue entry becomes an active source registry change.

## Source Lab UI / API Flow

Relevant files:

- `product/regradar/app/api.py`
- `product/regradar/web/src/components/app/SourceLabPage.jsx`
- `product/regradar/web/src/components/app/SourcesPage.jsx`
- `product/regradar/web/src/components/app/Dashboard.jsx`

What exists:

- Source Lab exposes remediation controls and discovery mode.
- The UI distinguishes preview/no-save from evidence/save states.

Remaining concern:

- Browser-based batch activation is not yet implemented; this audit focuses on backend queue/validator hardening first.

## Validators Flow

Relevant files:

- `tools/validate_source_discovery_engine.py`
- `tools/validate_source_activation_pipeline.py`
- `tools/validate_uae_source_pack.py`
- `tools/validate_uae_50_working_sources.py`
- `tools/validate_parser_quality.py`
- `tools/validate_workspace.py`
- `tools/validate_codex_skills.py`

What exists:

- Discovery, source activation, UAE pack, UAE 50-source, parser quality, workspace, and skills validators already exist.

Gap:

- Missing validator: general mass source activation pipeline queue validator.

## Broken / Duplicate / Legacy Code

- `product/regradar/app/source_connector/` overlaps conceptually with the newer Source Discovery Engine but is still referenced by CLI paths; do not delete yet.
- `product/regradar/run.py` has stale `discover-source` help lines; safe to update.
- `product/regradar/repopack-output.txt` appears to be a historical bundled output file; not a runtime blocker in this audit.
- Legacy helper/fallback names exist in `telegram_clients.py`, `extractors.py`, and `report.py`; they are not proven harmful to source activation.

## Missing Tests

Needed tests for mass source activation:

- candidate entries are inactive by default;
- no-save pass cannot claim evidence;
- proof saved without repeat baseline cannot activate;
- activation-ready requires proof paths, completed baseline, and all gates;
- high noise or high source-health risk blocks activation;
- rejected/blocked sources cannot activate;
- validator blocks fake 50/60 and unsafe parsing/compliance claims.

## P0 / P1 / P2 Blockers

P0:

- Missing general mass activation queue and validator.
- Need queue-level enforcement for proof paths, baselines, gates, noise/source-health, nav-shell, duplicate hash, and false public claims.

P1:

- Stale `run.py` source discovery help text.
- Legacy `source_connector` should be refactored or deprecated after parity review with `source_discovery.py`.

P2:

- Batch UI can be improved later once the backend mass queue is stable.
- Source-specific adapters still need regulator-by-regulator remediation before 50+ activation-ready sources are realistic.
