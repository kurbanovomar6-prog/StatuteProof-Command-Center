# Final Remediation Activation Plan

> **For agentic workers:** Execute in evidence-first cycles. Do not mark a source active unless no-save, saved proof, repeat baseline, mass-monitor dry-run, and agent gates all pass.

**Goal:** Investigate the final three enabled UAE remediation sources and convert as many as honestly possible to readiness-supported active sources.

**Architecture:** Treat the three remediation entries as legacy placeholders until proven otherwise. Prefer source-specific official endpoints with stable regulatory value over generic homepages or ambiguous labels. Registry truth changes only after proof paths, baseline runs, dry-run status, and review gates are recorded.

**Tech Stack:** Python source-intake pipeline, adapter platform, `sources.json`, UAE activation queue JSON files, local proof artifacts, pytest, validator scripts.

---

## Current State

- Starting public truth for this sprint: **79 enabled UAE sources / 76 readiness-supported / 3 remediation**.
- Latest pushed commit before task: `f784ffe`.
- Target if evidence allows: **79 enabled / 79 readiness-supported / 0 remediation**.
- Not allowed: fake activation, source-count inflation, complete UAE coverage claims, or changing customer truth without validators.

## Exact Remediation Source List

| Source ID | Current URL | Current issue from registry/docs | Initial stance |
| --- | --- | --- | --- |
| `AE-dubai-financial-services-authority-dfsa` | `https://www.dfsa.ae/rules-and-standards` | Legacy DFSA rules source. Prior reports say current URL renders page-not-found/nav-shell and collided with DFSA notices. Stronger DFSA rulebook/module endpoints may exist. | Attempt only if canonical DFSA rules endpoint extracts meaningful non-navigation content; otherwise replace/hold. |
| `AE-dfsa-notices` | `https://www.dfsa.ae/regulation/notices-public-registers` | Ambiguous label. Prior reports say current URL is 404/nav-shell and duplicates/collides with DFSA rules placeholder. | Do not activate ambiguous placeholder. Either redefine as a specific DFSA notice class with proof, or keep/remediate. |
| `AE-uae-financial-intelligence-unit-uaefiu` | `https://www.uaefiu.gov.ae/` | FIU homepage is shallow; FIU circulars/publications sources are already stronger readiness-supported sources. | Activate only if homepage proves meaningful and unique; otherwise replace with FIU NRA/strategic/annual source or keep honest remediation. |

## Why Each Source Matters

- DFSA rules and notices matter for DIFC/DFSA compliance teams, MLROs, and legal counsel.
- UAE FIU matters to all AML/CFT buyers, but the generic FIU homepage is less useful than specific FIU publications, circulars, NRA, or strategic analysis pages.
- Commercially, activating weak placeholders is worse than leaving remediation visible. The goal is trust, not cosmetic 79/79/0.

## Official Replacement Endpoint Strategy

1. **DFSA rules placeholder**
   - Prefer official DFSA rulebook/publications/guidance endpoint with stable listing or official-linked Thomson Reuters rulebook endpoint already supported by adapters.
   - Candidate classes: guidance notes, policy statements, official rulebook page, publications hub.
   - Reject generic DFSA marketing pages and 404/nav-shell pages.

2. **DFSA notices placeholder**
   - Decide specific model before activation: enforcement regulatory actions vs AML/MLRO notices vs public notices/registers.
   - Prefer one stable official listing and a precise source ID/name.
   - Do not keep "Regulatory Notices" if it hides multiple unrelated page classes.

3. **UAE FIU homepage**
   - Prefer high-value official FIU documents/listings: NRA 2024, strategic analysis, annual reports, mutual evaluation, publications/circulars not already active.
   - Do not use goAML private portal.
   - Do not activate the homepage if it remains shallow or duplicate.

## Adapter / Selector Strategy

- Use existing `dfsa_rulebook`, `dfsa_notice_listing`, `fiu_eocn_document_listing`, `pdf_listing`, `listing`, or `custom_element` patterns when they match.
- Add source-specific fixture coverage if selectors/adapters change.
- Improve classification only if it blocks honest source decisions:
  - generic homepage suppression;
  - stale/404/nav-shell detection;
  - duplicate hash/URL detection;
  - access-blocked classification;
  - FIU document listing extraction.

## Evidence / Baseline / Gate Strategy

For any source proposed for active status:

1. Run no-save Source Lab.
2. Save evidence/proof only after strong no-save pass.
3. Run repeat baseline at least twice.
4. Run mass-monitor dry-run and require `MONITOR_OK`.
5. Emulate/record gates:
   - Source Monitor;
   - Evidence Trail;
   - QA/Critic;
   - Legal Language;
   - Product Manager;
   - Code Architect.
6. Update registry/config/docs only after gates pass.

## Validators To Run

- `python3 -m compileall product/regradar`
- `python3 -m pytest product/regradar/tests -q`
- `python3 tools/validate_final_remediation_activation.py`
- `python3 tools/validate_difc_source_remediation.py`
- `python3 tools/validate_vara_source_depth.py`
- `python3 tools/validate_uae_coverage_claims.py`
- `python3 tools/validate_uae_source_universe_candidates.py`
- `python3 tools/validate_uae_source_pack.py`
- `python3 tools/validate_uae_50_working_sources.py`
- `python3 tools/validate_parser_quality.py`
- `python3 tools/validate_workspace.py`
- `python3 tools/validate_codex_skills.py`
- `git diff --check`

## Commit Policy

- Stage only files from this remediation task.
- Do not stage local proof runtime junk unless project policy explicitly requires it.
- Do not stage secrets, `.env`, cache folders, or unrelated files.
- Commit only after full validation passes.

## Hard Stop Conditions

- Official pages require login, CAPTCHA, private portal, or paywall.
- Source only yields nav-shell/shallow/generic homepage content.
- Source duplicates an already active URL/hash without adding distinct monitoring value.
- Hash drift/noise cannot be explained or filtered safely.
- Validators fail and cannot be fixed without weakening gates.

## What Will Not Be Claimed

- No complete UAE coverage.
- No 79/79/0 unless validators prove it.
- No legal advice, guaranteed compliance, perfect parsing, "never miss updates", or regulator certification.
- No production deployment or customer messaging.
