# UAE 60-Source Pack Final Report

## 1. Executive Verdict

The 60-source pack is not ready to market as active or validated coverage.

What is ready:

- 60 official or officially linked UAE source candidates mapped.
- 40-candidate first validation path defined.
- 6 rejected/no-garbage examples documented.
- Candidate registry created outside active `sources.json`.
- Source-pack validator created and passing.
- Five scoped no-save Source Lab checks completed.
- Two DFSA candidates produced meaningful, distinct no-save preview extraction.
- Current public source truth preserved.

Current customer-facing source truth remains:

**13 enabled UAE sources; 9 readiness-supported; 4 under extraction remediation.**

Counts from this task:

| Metric | Count |
|---|---:|
| Candidate sources discovered | 60 |
| Candidates tested in no-save batch | 5 |
| No-save accessible / next validation candidates | 2 |
| Remediation or blocked from no-save batch | 3 |
| Rejected/no-garbage examples | 6 |
| Active `sources.json` changes | 0 |

Can StatuteProof safely market 40+ sources now? **No.**

Can StatuteProof safely market 60 sources now? **No.**

Safe statement now:

“StatuteProof has mapped 60 official UAE source candidates and is validating a professional 40-source monitoring baseline. Current active source truth remains 13 enabled UAE sources, 9 readiness-supported, and 4 under extraction remediation.”

## 2. Source Strategy

13 sources is enough for an MVP and evidence demo, but too small for a professional UAE compliance monitor. MLROs, CCOs, VASPs, payment firms, DIFC/ADGM firms, and consultants need coverage across VARA, UAE FIU, CBUAE, DFSA/DIFC, ADGM/FSRA, SCA, sanctions/TFS, federal legislation, and selected tax/compliance sources.

Source Lab does not replace default expertise. It lets users test custom public sources, but the default pack should prove StatuteProof understands the UAE compliance surface before a buyer configures anything.

The correct path is:

1. map official candidate endpoints;
2. reject garbage;
3. test in no-save Source Lab batches;
4. add selectors/adapters for hard sites;
5. save proof for sources that will be evidence-backed;
6. complete baselines before monitoring-ready status;
7. update customer-facing source counts only from canonical readiness truth.

## 3. Current Source Truth

The active product truth did not change:

- 13 enabled UAE sources.
- 9 readiness-supported.
- 4 under extraction remediation.
- DFSA remains remediation.
- No “13 validated sources” wording is allowed.

The four remediation surfaces remain:

- DFSA main/rulebook model.
- DFSA notices model.
- UAE FIU homepage/shallow source.
- DIFC laws source pending review.

## 4. Candidate Discovery

Candidate file:

`product/regradar/config/uae_source_candidates.json`

Candidate distribution:

| Group | Candidates | Notes |
|---|---:|---|
| VARA | 8 | VASP-heavy; rulebook pages need browser/selector checks. |
| CBUAE | 10 | Core banking, AML/CFT, payment, consultation, licensing coverage; WAF risk noted. |
| UAE FIU | 5 | MLRO critical; generic extraction can produce page chrome. |
| DFSA / DIFC | 12 | High-value but DFSA remains remediation until saved/baseline validation. |
| ADGM / FSRA | 10 | Strong ADGM regulated-firm candidate set; needs batch validation. |
| UAE SCA | 7 | UAE-only SCA candidates; likely selector remediation. |
| Federal AML / tax / legislation | 8 | EOCN, MoEc AML, MoF, FTA, legislation/e-laws. |

Rejected examples:

- Saudi CMA: wrong country.
- Law firm articles: commentary, not official source.
- LinkedIn/social posts: not official source coverage.
- News sites: commentary/noise.
- Private goAML portal: blocked.
- Search result pages: not official endpoints.

## 5. No-Garbage Policy

Created:

`docs/no-garbage-source-policy.md`

The policy requires official provenance, public access, compliance relevance, meaningful content, non-duplication, stable ownership/category, readiness status, and an MLRO-relevant reason. It rejects marketing pages, social/blog/news commentary, private portals, paywalls, login/CAPTCHA pages, search results, wrong-country regulators, 404 shells, and duplicate hashes/content without purpose.

## 6. No-Save Validation Results

Created:

`docs/uae-source-pack-no-save-validation-report.md`

Five no-save checks were run:

| Source | Result |
|---|---|
| UAE FIU Publications | BLOCKED/nav-shell/access-warning remediation. |
| VARA Enforcement | Meaningful preview but generic extraction flagged NAV_SHELL_ONLY; needs selector/adapter. |
| DFSA Rulebook Modules | CONFIRMED_ACCESSIBLE preview, unique hash, meaningful AML/rulebook content, baseline required. |
| DFSA AML/MLRO Notices | CONFIRMED_ACCESSIBLE preview, unique hash, meaningful notice titles, baseline required. |
| CBUAE Regulations | BLOCKED/access-warning remediation under generic Source Lab. |

Interpretation:

- Two DFSA candidates are strong next-step candidates for saved validation/baseline.
- No source became evidence-confirmed.
- No source became monitoring-ready.
- No public source count changed.

## 7. Default Packs By Plan

Created:

`docs/uae-default-source-packs-by-plan.md`

Recommended packaging:

- Internal demo pack: 5-10 sources, clearly labeled, includes remediation states.
- Free Source Readiness Review: 1 custom source plus recommended source map.
- Founding Pilot at $199/month: around 20 manually activated endpoints tailored to licence type.
- UAE Monitor at $399/month: 40-60 official endpoints only after validation.
- Consultant/Enterprise: 100+ eventual endpoints with multi-client controls and custom onboarding.

## 8. Source Registry Changes

Created:

`docs/source-registry-expansion-change-report.md`

`sources.json` was not changed.

Why:

- Most candidates are not no-save tested.
- Promising DFSA results are preview-only and baseline-required.
- Several important current/generic pages still produced blocked/nav-shell quality results.
- Active source counts must not change without canonical readiness proof.

## 9. DFSA Status

DFSA remains remediation.

However, two specific DFSA candidates now have useful no-save evidence for the next task:

- `AE-dfsa-rulebook-thomsonreuters`
  - URL: `https://dfsaen.thomsonreuters.com/rulebook/rulebook-modules`
  - selector: `article`
  - result: meaningful preview, unique hash, `CONFIRMED_ACCESSIBLE`, baseline required.

- `AE-dfsa-aml-mlro-notices`
  - URL: `https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/financial-crime-prevention-notices-and-mlro-letters`
  - selector: `.financial-crime-prevention-notices-and-mlro-letters .simpleTabsContent`
  - result: meaningful preview, unique hash, `CONFIRMED_ACCESSIBLE`, baseline required.

These are candidates for a focused DFSA saved-validation/baseline task, not customer-facing “DFSA ready” proof yet.

## 10. Operational Risk Alerts

Created:

`docs/source-monitor-operational-risk-alerts.md`

Proposed source health states:

- `MONITOR_OK`
- `MONITOR_DISCONNECTED`
- `QUALITY_DROP`
- `SELECTOR_BROKEN`
- `HASH_COLLISION`
- `NAV_SHELL_ONLY`
- `SOURCE_STRUCTURE_CHANGED`
- `REMEDIATION_REQUIRED`
- `MANUAL_CHECK_REQUIRED`

This was documented, not fully implemented, because full operational alerting belongs in a focused parser/UI sprint.

## 11. Acknowledge & Assess Workflow

Created:

`docs/acknowledge-and-assess-workflow-spec.md`

The workflow defines:

- saved evidence requirement;
- MLRO “Acknowledge & Assess” action;
- impact note;
- reviewer/timestamp/status;
- locked hash/diff/proof/URL references;
- exportable audit record;
- not legal advice disclaimer.

No fake functionality was added.

## 12. Customer-Safe Claims

Allowed now:

- “13 enabled UAE sources; 9 readiness-supported; 4 under extraction remediation.”
- “60 official UAE source candidates mapped for validation.”
- “40-source professional pack path under no-save validation.”
- “Default source pack under validation.”
- “Source Lab tests public official sources and explains extraction readiness.”
- “Monitoring intelligence only. Not legal advice.”
- “DFSA has promising no-save candidates, but saved evidence and baseline are still pending.”

## 13. Forbidden Claims

Do not say:

- “60 validated sources.”
- “40+ monitored sources.”
- “13 validated sources.”
- “comprehensive UAE monitor.”
- “DFSA ready.”
- “perfect parsing.”
- “any website can be parsed.”
- “never miss updates.”
- “legal advice.”
- “guaranteed compliance.”
- “official regulator certified.”
- “official regulator partner.”

## 14. Validation Results

Passed:

```bash
python3 tools/validate_uae_source_pack.py
python3 -m compileall product/regradar
python3 tools/validate_parser_quality.py
python3 tools/validate_workspace.py
python3 tools/validate_codex_skills.py
git diff --check
```

Not run:

- `python3 tools/validate_source_readiness_summary.py` because that script is not present.
- Frontend build/lint because no frontend code changed.

## 15. Remaining Gaps

The product is stronger after this task, but the 40-60 source pack is not ready yet.

Remaining work:

1. Run top-40 no-save validation in regulator batches.
2. Add precise selectors/adapters for VARA, CBUAE, UAE FIU, SCA, ADGM/FSRA, and remaining DFSA candidates.
3. Execute DFSA saved evidence/baseline task for the two promising DFSA candidates.
4. Add source health state mapping to backend/frontend.
5. Implement Acknowledge & Assess for saved evidence only.
6. Generate canonical source readiness summary from active registry plus source run evidence.
7. Update customer-facing source counts only after validation and evidence gates.

## 16. Next Exact Task

Run a focused top-40 UAE source no-save validation sprint in regulator batches, starting with ADGM/FSRA and SCA selector discovery, while keeping current public source truth at 13/9/4.
