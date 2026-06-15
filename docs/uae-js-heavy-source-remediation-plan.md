# UAE JS-Heavy Source Remediation Plan

Date: 2026-06-15

## Current State

- Latest local commit at sprint start: `c54d72e feat: discover 151 UAE endpoints, activate 3 new proof-backed sources`.
- Current public truth used for this sprint: **23 enabled UAE sources / 19 readiness-supported / 4 under extraction remediation**.
- The worktree had one untracked tool/runtime lock file, `.claude/scheduled_tasks.lock`; the user explicitly approved continuing and this file will not be staged.
- The last discovery sprint found 151 official endpoint URLs, 75 accepted net-new endpoints, tested 30 top-priority candidates, and activated 3 proof-backed sources.

## Why Discovery Is Not The Bottleneck

The candidate universe is now large enough for another activation wave. The limiting factor is not URL volume; it is extraction reliability on JS-heavy official portals. Re-running broad discovery would mostly add more unproven URLs without increasing active source count.

## Why JS / NAV_SHELL Is The Bottleneck

The last no-save batch failed primarily with `NAV_SHELL_ONLY` or `JS_RENDERING_NEEDED`. Those failures mean the fetcher reached the public page but the generic extraction path mostly saw menus, layout chrome, empty SPA shells, or pre-rendered placeholders instead of regulatory content.

## Target Groups

1. **UAE FIU knowledge-centre pages**
   - Suspected issue: SPA/web-component content not isolated by generic selectors.
   - Strategy: Playwright rendered DOM and XHR inspection, then FIU-specific listing/document extraction.

2. **SCA JS-filtered pages**
   - Suspected issue: ASP.NET/listing/card pages need item-level selectors and chrome filtering.
   - Strategy: rendered listing/table/card adapter improvements and exact selector presets.

3. **ADGM alternate-component pages**
   - Suspected issue: not all useful ADGM pages use the already-proven `adgm-page` shape.
   - Strategy: inspect media/data-protection pages and add selector fallbacks without regressing existing ADGM sources.

4. **CBUAE / DFSA / DIFC blocked pages**
   - Suspected issue: access restrictions, WAF, or selectors not yet known.
   - Strategy: classify accurately; no bypassing login, CAPTCHA, WAF, or private portals.

## Files Likely To Change

- `product/regradar/app/adapters/adapter_platform.py`
- `product/regradar/app/dom_investigator.py`
- `product/regradar/app/source_intake.py`
- `product/regradar/app/source_discovery.py`
- `product/regradar/config/mass_source_activation_queue.json`
- `product/regradar/config/uae_source_work_queue.json`
- `product/regradar/config/uae_source_candidates.json` if source truth needs reconciliation
- `product/regradar/sources.json` only for fully proven activations
- `product/regradar/tests/test_adapter_platform.py`
- `product/regradar/tests/test_source_intake.py`
- validators only if source truth changes

## Adapter / Test / Validation Plan

- Add fixture tests before adapter changes where behavior changes are needed.
- Improve only source-specific extraction and failure classification needed for FIU/SCA/ADGM.
- Use no-save retests before any evidence save.
- Save evidence only for strong no-save passes.
- Require repeat baseline, mass-monitor `MONITOR_OK`, and agent gates before activation.

## Live Validation Scope

Live checks are limited to high-value blocked targets from the discovery report:

- UAE FIU knowledge-centre/publication pages.
- SCA regulations, AML/CFT, market rules, FATCA/CRS, circulars/procedures/decisions.
- ADGM media, data-protection guidance, and data-protection regulatory actions.

No broad monitoring or customer delivery is allowed.

## Commit Policy

If validation passes, stage only task files. Do not stage `.env`, runtime junk, unrelated files, or the `.claude/scheduled_tasks.lock` tool lock file.

Commit message:

- `feat: activate JS-heavy UAE regulatory sources` if new sources are activated.
- `feat: improve UAE JS-heavy source adapters` if adapters improve but no new sources are activated.
