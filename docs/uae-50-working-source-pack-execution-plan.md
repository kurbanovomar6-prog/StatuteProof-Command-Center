# UAE 50 Working Source Pack Execution Plan

## 1. Current Truth

Customer-facing truth remains:

**13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation.**

The expanded source-pack work has a strong candidate map but not a 50-source active pack. Prior top-40 no-save testing found 2 next-step candidates and 38 remediation candidates. ADGM/SCA remediation later produced three local proof-backed baseline attempts, all still baseline-pending.

## 2. Definition Of Working

A source counts as working only when all of these are true:

1. Official or officially linked.
2. Public and permitted to monitor.
3. Correct final URL.
4. Stable extraction strategy.
5. Not nav-shell.
6. No duplicate/shell hash collision.
7. Meaningful regulatory or compliance content.
8. Noise risk reviewed.
9. Source-health risk reviewed.
10. Saved proof/evidence artifacts exist.
11. At least two successful baseline runs or a documented baseline rule is satisfied.
12. Activation decision is recorded.
13. Source Monitor gate passes.
14. Evidence Trail gate passes.
15. QA/Critic gate passes.
16. Legal Language gate passes.
17. No false `ready`, `validated`, or `certified` claim.

## 3. Source States

| State | Meaning |
|---|---|
| `candidate` | Official/relevant enough for future Source Lab testing, but not tested or not enough data. |
| `no_save_passed` | No-save Source Lab produced meaningful preview content; no evidence claim. |
| `proof_saved` | Saved run created proof artifacts; baseline still may be incomplete. |
| `baseline_pending` | Proof exists but baseline requirement is not complete. |
| `activation_ready` | Proof, baseline, quality, risk, and agent gates all pass. |
| `remediation` | Useful source but selector/adapter/source model needs work. |
| `blocked` | Access or safety policy prevents monitoring. |
| `rejected` | Wrong, duplicate, irrelevant, garbage, or not official enough. |

## 4. Agent-Gated Lifecycle

1. Candidate Discovery.
2. Source Monitor Review.
3. No-Save Parser Test.
4. Evidence Save.
5. Evidence Trail Review.
6. Repeat Baseline.
7. QA/Critic Review.
8. Legal Language Review.
9. Activation Decision.
10. Product Manager Demo Readiness Review.

## 5. Batch Strategy

Priority order:

1. Existing 13 enabled sources and already evidence-backed local candidates.
2. ADGM/FSRA and SCA candidates with successful selector remediation.
3. DFSA candidates that passed no-save and have clear source models.
4. Static official HTML pages.
5. Official listing pages that can support item-level extraction.
6. PDF/document listings where proof and noise controls are feasible.
7. Higher-risk JS/search/register pages only after adapter design.

This sprint should not attempt to brute-force 50 activations. It should build the queue, enforce gates, and only run scoped live checks where the prior reports show a high chance of clean progress.

## 6. Source Groups

- Existing enabled UAE sources.
- ADGM/FSRA.
- SCA.
- DFSA/DIFC.
- VARA.
- CBUAE.
- UAE FIU / sanctions / AML.
- Federal law, tax, corporate compliance, and public-register candidates.

## 7. Validation Commands

Required validation:

- `python3 -m compileall product/regradar`
- `python3 -m pytest product/regradar/tests/test_parser_benchmark_suite.py -q`
- `python3 tools/validate_uae_source_pack.py`
- `python3 tools/validate_uae_50_working_sources.py`
- `python3 tools/validate_parser_quality.py`
- `python3 tools/validate_workspace.py`
- `python3 tools/validate_codex_skills.py`
- `git diff --check`

Frontend validation is only required if frontend files are touched.

## 8. Commit Plan

Stage only files created or changed by this sprint. Do not stage ignored runtime data or evidence artifacts unless a future policy explicitly requires it.

Expected truthful commit if fewer than 50 pass:

`test: advance UAE source pack toward 50 working sources`

## 9. What Will Not Be Touched

- No production deployment.
- No broad monitoring.
- No customer delivery.
- No active source count increase without proof and baselines.
- No `sources.json` activation from no-save previews.
- No live Stripe, Cloudflare, DigitalOcean, Telegram, or email work.
- No scraping of private, login, CAPTCHA, paywalled, or personal-data sources.
