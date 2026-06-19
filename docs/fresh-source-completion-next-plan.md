# Fresh Source Completion Next Plan

Date: 2026-06-19

## Current Truth

Clean-state gate passed before this plan. Latest pushed commit: `6f8c825`.

| Metric | Count |
| --- | ---: |
| Enabled UAE sources | 232 |
| Legacy monitoring-active rows | 231 |
| Fresh-alert eligible daily monitors | 162 |
| MONITOR_OK rows | 216 |
| Evidence-library-only rows | 61 |
| Candidate/pending rows | 6 |
| Fresh-signal remediation rows | 3 |

## Current Family Counts And Deficits

| Family | Fresh Alert MONITOR_OK | Target | Deficit |
| --- | ---: | ---: | ---: |
| CBUAE | 25 | 25 | 0 |
| FTA | 25 | 25 | 0 |
| MoE/DNFBP AML | 42 | 25 | 0 |
| EOCN/TFS | 24 | 25 | 1 |
| VARA | 23 | 25 | 2 |
| DFSA | 15 | 25 | 10 |
| DIFC | 10 | 25 | 15 |
| ADGM/FSRA | 8 | 25 | 17 |
| UAE FIU | 5 | 25 | 20 |
| SCA | 5 | 25 | 20 |
| MoJ/Gazette | 0 | 25 | 25 |
| MoF | 0 | 25 | 25 |

## Source Types That Count

Count only official/public sources that can produce future customer alerts:

- Listing pages that update with new official publications.
- Rulebook revision or update pages.
- Consultation, circular, notice, enforcement, administrative order, law, regulation, sanctions/TFS, gazette, or official publication listings.
- Versioned official PDFs only when hash-monitored.
- Public unauthenticated official endpoints only when permitted.

Do not count homepages, marketing pages, old individual news/detail pages, stale one-off articles, duplicates, login/CAPTCHA/paywall/private portals, nav-shell pages, or no-save-only rows.

## Fastest Wins

1. EOCN/TFS needs one more direct official source. First try official `eocn.gov.ae` and `uaeiec.gov.ae` listing/publication endpoints already near passing or not yet tested.
2. VARA needs two. First try official regulatory notices, rulebook update, enforcement/admin-order, and versioned PDF endpoints. A prior regulatory-notices candidate reached quality 59 but did not pass save gates.
3. DFSA needs ten. Prior blockers were duplicate hashes and static notice pages. Priority is unique official listing endpoints, not individual notices.

## Hard Families

- SCA: many official pages collapse to nav-shell or duplicate shell hashes. Needs table/list/PDF adapter work before broad activation.
- MoJ/Gazette: WAF/access and selector issues remain the main blocker. Respect access controls and use official alternatives only.
- MoF: generic and service pages are nav-shell-heavy. Needs a specific news/document/decision listing adapter or better official subpages.
- UAE FIU: public source universe appears small; goAML is forbidden. Need proof of official-source limits before claiming exhaustion.

## Adapter-First Strategy

Use existing adapters where they pass gates. Build or refine source-specific adapters only when a useful official endpoint fails generic extraction:

- EOCN/TFS listing and noise-control adapter.
- VARA regulatory notices/admin-order/rulebook update adapter.
- DFSA listing/rulebook/publication adapter with duplicate-hash isolation.
- DIFC legal/document/CDN PDF adapter.
- ADGM/FSRA component/listing adapter.
- UAE FIU publication/circular adapter.
- SCA listing/table/PDF/download adapter.
- MoJ/Gazette access-safe legal listing adapter.
- MoF decision/news/document listing adapter.

## Evidence / Baseline / MONITOR_OK Strategy

For each strong no-save pass:

1. Save proof/evidence with `write_evidence=True`.
2. Require `proof_path`, `normalized_text_path`, and `normalized_hash`.
3. Run at least two saved baselines.
4. Run mass-monitor dry-run.
5. Activate only if mass-monitor returns `MONITOR_OK`.
6. Add daily-check metadata, fresh-signal type, expected update pattern, customer alert policy, and legal-safe notes.

## Validators

Create `tools/validate_fresh_source_completion_next.py` and update existing fresh-signal/source-truth validators only when registry truth changes. Validators must fail on:

- Fresh-alert rows without MONITOR_OK/proof/hash/baseline/daily frequency.
- Homepages, static detail pages, duplicates, nav-shell, access-blocked rows counted as fresh alerts.
- Evidence-library/remediation counted as fresh monitoring.
- Family marked Strong with fewer than 25 fresh-alert MONITOR_OK rows.
- Complete UAE coverage, complete family coverage, legal advice, guaranteed compliance, perfect parsing, or never-miss claims.

## Commit Policy

Commit only after compile, tests, validators, `git diff --check`, and frontend validation if frontend data is touched. Stage only files from this task. Do not stage runtime junk, secrets, or unrelated files.

## What Will Not Be Claimed

- Complete UAE coverage.
- Complete coverage for any family below 25 fresh-alert MONITOR_OK rows.
- Legal advice or guaranteed compliance.
- Regulator certification.
- Perfect parsing or never-miss monitoring.
- That a no-save pass, one saved run, static page, generic homepage, or evidence-library source is monitoring-ready.
