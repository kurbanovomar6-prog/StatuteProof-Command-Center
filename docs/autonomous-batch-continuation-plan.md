# Autonomous Batch Continuation Plan

Verified start state: clean worktree at `deff94f` on `main`.

Current source truth: 28 enabled UAE sources / 24 readiness-supported active sources / 4 remediation sources. The 50-source target has not been reached; 26 additional useful, proof-backed activation-ready sources are still required.

## Batch Goal

This run is a batch execution continuation, not a one-source remediation pass. The run should continue until at least one hard stop condition is met:

- at least 10 candidate sources are no-save tested in this run;
- at least 5 new sources become activation-ready in this run;
- at least 3 regulator/source batches are attempted;
- repeated access blocking or validator failure prevents safe continuation;
- context is genuinely too low to continue safely.

No source may be added to `sources.json` unless it has a strong no-save pass, saved evidence, repeat baseline, mass-monitor dry-run `MONITOR_OK`, and all manual agent gates pass.

## Highest-Potential Candidate Set

The next 15 candidates are selected from `uae_50_activation_scoreboard.json`, `uae_source_work_queue.json`, and the current next-execution prompt. They prioritize close quality scores, existing adapters, official listing/rulebook pages, and known source-specific remediation paths.

| Batch | Source ID | Why selected | Expected adapter/selector work |
| --- | --- | --- | --- |
| 1 | `AE-sca-aml-cft` | q=55, low noise, official SCA AML/CFT page; near threshold | improve SCA listing/content selector, avoid carousel/nav text |
| 1 | `AE-adgm-legal-framework-rules` | q=56, ADGM custom element already close | tighten ADGM custom_element focus/exclusion and baseline if q>=60 |
| 1 | `AE-adgm-fsra-enforcement` | q=54, official FSRA enforcement page | ADGM custom element/listing selector and item extraction |
| 1 | `AE-dfsa-aml-mlro-notices` | q=59, source-specific DFSA adapter exists | selector/nav-shell remediation or hold if duplicate shell |
| 1 | `AE-dfsa-rulebook-thomsonreuters` | q=59, official-linked rulebook module page | rulebook/listing module extraction and selector stability |
| 2 | `AE-uaefiu-aml-cft-laws` | named next-prompt blocker; high MLRO relevance | Playwright DOM/XHR; direct official document links; avoid typology duplicate |
| 2 | `AE-adgm-ra-notices` | named next-prompt blocker; official RA notices | find valid ADGM RA replacement URL or mark stale |
| 2 | `AE-adgm-ra-aml-guides` | named next-prompt blocker; high DNFBP relevance | find valid ADGM RA AML/CFT guide URL or mark stale |
| 2 | `AE-sca-corporate-governance` | named next-prompt blocker; official SCA governance source | decide distinct source vs covered by SCA regulations; improve selector if distinct |
| 2 | `AE-vara-rulebooks-overview` | official VARA rulebook area; current nav-shell | Playwright selector/PDF listing discovery; no WAF bypass |
| 3 | `AE-adgm-dp-guidance` | untested official ADGM data protection guidance | ADGM alternate/custom component selector |
| 3 | `AE-adgm-dp-regulatory-actions` | untested official ADGM regulatory action source | ADGM alternate/custom component selector |
| 3 | `AE-adgm-media-announcements` | untested ADGM announcements; prior alternate-component blocker | ADGM media/listing component selector |
| 3 | `AE-adgm-listing-announcements` | untested FSRA listing authority source | ADGM FSRA listing adapter or custom element selector |
| 3 | `AE-cbuae-circulars` | official CBUAE regulatory page, untested target | official public access only; classify 403/WAF honestly |

## Execution Order

1. Run no-save and targeted DOM/XHR investigation for Batch 1.
2. If a source reaches q>=60, not nav-shell, not shallow, unique hash, and `can_save_evidence=true`, save two evidence runs and run mass-monitor dry-run before activation.
3. Continue to Batch 2 even if Batch 1 activates one or more sources.
4. Continue to Batch 3 if safe, or stop only after the batch minimum/hard stop conditions are satisfied.
5. Update queue/scoreboard and reports for every tested source, including exact failure code and remediation hint.

## Expected Code Areas

Likely files if adapter work is required:

- `product/regradar/app/adapters/adapter_platform.py`
- `product/regradar/app/source_intake.py`
- `product/regradar/app/source_quality.py`
- `product/regradar/tests/test_adapter_platform.py`
- `product/regradar/config/uae_50_activation_scoreboard.json`
- `product/regradar/config/uae_source_work_queue.json`
- `product/regradar/sources.json` only for fully proven sources

## Validation Policy

After any source activation or adapter change, run:

- `python3 -m compileall product/regradar`
- `python3 -m pytest product/regradar/tests -q`
- `python3 tools/validate_uae_source_pack.py`
- `python3 tools/validate_uae_50_working_sources.py`
- `python3 tools/validate_source_readiness_summary.py` if present
- `python3 tools/validate_parser_quality.py`
- `python3 tools/validate_workspace.py`
- `python3 tools/validate_codex_skills.py`
- `git diff --check`

Frontend validation is not required unless frontend files are touched.

## Commit Policy

Commit only after validation passes. Stage only files changed for this task, no runtime junk, no secrets, and no unrelated files.
