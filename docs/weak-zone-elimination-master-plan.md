# Weak-Zone Elimination Master Plan

Date: 2026-06-16

## Current Truth

- Starting public truth before this run: **36 enabled UAE sources / 32 readiness-supported / 4 remediation**. Current truth is updated in the final reports after validation.
- Target: **50 readiness-supported monitored UAE sources**.
- Current gap: **18** additional proof-backed, baseline-tested, gate-passing sources.
- Latest pushed commit verified before work: `dd51c04`.
- Worktree clean before start: yes.

## Weak Zones

1. **UAE FIU SPA/XHR/document listings**: high MLRO relevance, but several pages are route aliases, shallow shells, or duplicate hub hashes.
2. **VARA rulebooks/framework/enforcement/PDF listings**: high buyer relevance for VASPs, but current URLs often return nav shell or stale pages.
3. **CBUAE public site and alternates**: core regulator, but public website paths often block automated access; official rulebook alternates are promising.
4. **DFSA/DIFC notices/enforcement/laws**: useful for DIFC-regulated firms, but several URLs are selector-stale, blocked, or need listing/tab handling.
5. **ADGM alternate components/media/listings**: strong zone overall, but alternate pages use components beyond the proven `adgm-page`/custom-element pattern.

## Why These Zones Block Scale

- Candidate volume is no longer the primary blocker; 50 requires turning known official candidates into deterministic extraction paths.
- Generic DOM extraction still over-selects nav shells on JS-heavy official sites.
- Several pages have useful regulatory content behind generic link text like `View`, `Download`, or `Read more`; adapters need surrounding-card context.
- Some official pages are aliases of broader hubs and produce duplicate hashes, so activating both would inflate counts without adding monitoring value.
- Access-blocked pages must remain blocked unless a public official alternate endpoint is found.

## Top 30 Candidates To Investigate

| # | Source ID | Zone | Expected work |
| ---: | --- | --- | --- |
| 1 | `AE-uaefiu-strategic-analysis` | UAE FIU | Find narrower public document/PDF endpoint or hold duplicate/shallow route. |
| 2 | `AE-uaefiu-nra-2024` | UAE FIU | Find direct NRA report document endpoint. |
| 3 | `AE-uaefiu-annual-reports` | UAE FIU | Find annual-report specific selector/document; avoid duplicate publications hub hash. |
| 4 | `AE-uaefiu-press-releases` | UAE FIU | Test media route only if regulatory/public guidance content is present. |
| 5 | `AE-uaefiu-laws-regulations` | UAE FIU | Retest official law route and classify access safely. |
| 6 | `AE-vara-rulebooks-overview` | VARA | Locate stable official rulebook/PDF URLs or public listing endpoint. |
| 7 | `AE-vara-aml-cft-rulebook` | VARA | Find direct official AML/CFT rulebook document. |
| 8 | `AE-vara-company-rulebook` | VARA | Find direct official Company Rulebook document. |
| 9 | `AE-vara-regulatory-framework` | VARA | Find framework page/documents or hold as shell. |
| 10 | `AE-vara-public-register` | VARA | Test only if public and useful for compliance monitoring. |
| 11 | `AE-cbuae-publications` | CBUAE | Look for public official alternate listing/document endpoints. |
| 12 | `AE-cbuae-circulars` | CBUAE | Look for official circular/regulation alternate endpoint. |
| 13 | `AE-cbuae-aml-cft` | CBUAE | Look for official AML/CFT alternate or rulebook pages. |
| 14 | `AE-cbuae-payment-systems` | CBUAE | Test public payment-system rulebook/document pages. |
| 15 | `AE-cbuae-consultations` | CBUAE | Classify access and test official alternatives. |
| 16 | `AE-dfsa-published-decisions` | DFSA/DIFC | Enforcement listing selector/XHR remediation. |
| 17 | `AE-dfsa-enforcement-regulatory-actions` | DFSA/DIFC | Enforcement listing selector or hold if blocked. |
| 18 | `AE-dfsa-consultation-papers` | DFSA/DIFC | Consultation listing selector. |
| 19 | `AE-dfsa-publications` | DFSA/DIFC | Publications listing selector. |
| 20 | `AE-difc-data-protection` | DFSA/DIFC | Compliance-relevant DIFC page selector. |
| 21 | `AE-difc-consultation-papers` | DFSA/DIFC | Consultation listing selector. |
| 22 | `AE-difc-legal-database` | DFSA/DIFC | Access classification and public alternate search. |
| 23 | `AE-adgm-dp-regulatory-actions` | ADGM alternate | Data-protection regulatory action cards/listing selector. |
| 24 | `AE-adgm-media-announcements` | ADGM alternate | Announcement cards with noise controls. |
| 25 | `AE-adgm-listing-announcements` | ADGM alternate | Listing authority announcements replacement/selector. |
| 26 | `AE-adgm-ra-notices` | ADGM alternate | Replacement URL or alternate component selector. |
| 27 | `AE-adgm-ra-aml-guides` | ADGM alternate | Replacement URL or public document listing. |
| 28 | `AE-adgm-abu-dhabi-legislation` | ADGM alternate | Legal-framework subpage extraction. |
| 29 | `AE-adgm-federal-legislation` | ADGM alternate | Legal-framework subpage extraction. |
| 30 | `AE-adgm-data-protection` | ADGM alternate | Hub page extraction only if distinct and compliance-useful. |

## Expected Adapter / Selector / XHR / PDF Work

- Improve document/listing adapters when generic action links need surrounding-card titles.
- Add or refine source-specific URL normalization for direct PDF/document endpoints.
- Use Playwright/network capture only for public unauthenticated pages and public document URLs.
- Add fixture tests before adapter behavior changes.
- Keep duplicate-hash aliases in remediation or hold state.
- Use official alternate domains only where they are clearly official or officially linked.

## Research Plan

- Official-site research first for stable URLs and public documents.
- Package/open-source research only for techniques: Playwright network capture, robust listing extraction, PDF/document link extraction, source-health classification.
- No vendoring, no copied incompatible code, and no huge dependencies.
- Document useful findings in `docs/weak-zone-research-log.md`.

## Batch Order

1. VARA official rulebook/PDF endpoints.
2. CBUAE official rulebook/regulation/publication alternates.
3. DFSA/DIFC enforcement/consultation/law selectors.
4. ADGM alternate components/replacement URLs.
5. UAE FIU remaining direct-document routes and duplicate cleanup.
6. Highest-potential leftovers if context and validation remain healthy.

## Activation Rules

A source can be activated only when it has:

- official/public/UAE-relevant status;
- strong no-save pass;
- meaningful non-shell normalized content;
- no duplicate/shell hash collision;
- acceptable noise/source-health risk;
- proof/evidence paths;
- two stable baseline runs;
- mass-monitor dry-run `MONITOR_OK`;
- Source Monitor, Evidence Trail, QA/Critic, Legal Language, Product Manager, and Code Architect gates passing;
- validators passing after `sources.json` changes.

## Validation Plan

Run:

```bash
git status --short
python3 -m compileall product/regradar
python3 -m pytest product/regradar/tests -q
python3 tools/validate_source_discovery_engine.py
python3 tools/validate_source_activation_pipeline.py
python3 tools/validate_mass_source_activation_pipeline.py
python3 tools/validate_mass_monitoring_runner.py
python3 tools/validate_batch_onboarding.py
python3 tools/validate_uae_source_pack.py
python3 tools/validate_uae_50_working_sources.py
python3 tools/validate_parser_quality.py
python3 tools/validate_workspace.py
python3 tools/validate_codex_skills.py
git diff --check
```

## Commit Policy

- Stage only files changed for this task.
- Do not stage runtime junk or secrets.
- Do not force-add ignored evidence artifacts unless project policy explicitly requires it.
- Commit only after validation passes.
- Commit message: `feat: eliminate weak UAE source remediation zones`.

## Hard Stop Conditions

- Dirty worktree before start.
- Repeated access blocking from one domain.
- Any need for login/CAPTCHA/paywall/private portal access.
- Validator failure that cannot be fixed safely.
- Context low enough that the next continuation prompt must be created.
