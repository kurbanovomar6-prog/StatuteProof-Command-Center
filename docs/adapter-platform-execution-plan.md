# Adapter Platform Execution Plan

## 1. Current Repo State

Clean-state gate passed before this plan was created.

Latest visible commit before this sprint:

`04ed211 test: advance UAE source pack toward 50 working sources`

Current public source truth remains:

**13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation.**

The UAE work queue currently records 78 UAE-related entries, 2 activation-ready candidates, 3 proof-backed candidates, 3 baseline-complete candidates, 21 remediation entries, 21 blocked entries, and 28 candidate-only entries.

## 2. Why Adapters Are Needed

The top-40 UAE source validation sprint showed that generic extraction and one-off selectors are not enough for a professional 40-60 source baseline. Official UAE regulator sites often use:

- listing pages with repeated decision/circular rows;
- JS-rendered or custom-element content;
- table layouts;
- PDF document lists;
- register/search pages;
- navigation and service chrome that causes false diffs;
- source-health risks where selectors can silently break.

Adapters let StatuteProof extract the meaningful regulatory unit instead of whole-page chrome.

## 3. Working Source Definition

A source counts as working only if:

1. official or officially linked;
2. public and permitted to monitor;
3. technically testable;
4. extracted by a stable adapter or selector;
5. not nav-shell or shallow text;
6. no duplicate/shell hash collision;
7. noise/source-health risk reviewed;
8. saved proof exists when evidence is claimed;
9. baseline requirement is satisfied before activation;
10. Source Monitor, Evidence Trail, QA/Critic, Legal Language, Code Architect, and Product Manager gates pass.

## 4. Agents / Skills / Tools Used

Repo-scoped skills read and applied:

- `source-monitoring-review`
- `evidence-readiness-review`
- `custom-source-parser`
- `legal-safe-copy-review`
- `test-driven-development`
- `systematic-debugging`
- `verification-before-completion`

Agent gates are applied manually because no callable subagent runner is exposed in this session. This is recorded as “emulated manually,” not as actual subagent execution.

## 5. Files To Inspect

- `product/regradar/app/source_intake.py`
- `product/regradar/app/extractors.py`
- `product/regradar/app/scraper.py`
- `product/regradar/app/adapters/`
- `product/regradar/app/providers/`
- `product/regradar/app/source_quality.py`
- `product/regradar/app/source_certification.py`
- `product/regradar/run.py`
- `product/regradar/app/api.py`
- `product/regradar/config/uae_source_candidates.json`
- `product/regradar/config/uae_source_work_queue.json`
- `product/regradar/tests/`

## 6. Files Likely To Change

- `product/regradar/app/adapters/adapter_platform.py`
- `product/regradar/app/source_intake.py`
- `product/regradar/tests/test_adapter_platform.py`
- `product/regradar/tests/test_source_intake.py`
- `product/regradar/config/uae_source_work_queue.json`
- `tools/validate_uae_50_working_sources.py`
- `tools/validate_parser_quality.py` if Source Lab contract checks need adapter fields
- adapter platform docs and reports

## 7. Adapter Architecture Plan

Build a small universal adapter platform, not a broad rewrite:

- base result schema for adapter output;
- adapter family registry;
- listing adapter;
- table adapter;
- custom-element adapter;
- selector/static HTML wrapper;
- rulebook/module normalization helper;
- source-specific dispatch by explicit config such as `adapter_name` or `adapter_family`;
- safe metadata fields: `adapter_used`, `adapter_family`, `adapter_version`, `extraction_strategy`.

The platform must feed normalized text into the existing Source Lab/evidence path. It must not replace proof, hash, certification, or source-run logic.

## 8. Validation Plan

Required:

- adapter unit tests with local fixtures;
- existing parser benchmark suite;
- full parser tests if practical;
- source-pack validators;
- parser quality validator;
- workspace and Codex skill validators;
- `git diff --check`.

## 9. Commit Plan

If validation passes and fewer than 50 sources are reached:

`feat: strengthen StatuteProof source adapter platform`

If 50 genuinely pass all gates:

`feat: build gated UAE 50-source adapter pack`

## 10. What Will Not Be Touched

- No deployment.
- No Cloudflare or DigitalOcean work.
- No customer delivery.
- No broad monitor/all-source run.
- No source count inflation.
- No `sources.json` activation without proof and gates.
- No large dependency install.
- No third-party repo vendoring.
