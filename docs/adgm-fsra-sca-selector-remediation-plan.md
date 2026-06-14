# ADGM/FSRA + SCA Selector Remediation Plan

## 1. Current State

- Latest pushed source-validation commit: `dca9f59`.
- Current public source truth remains: **13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation**.
- A 60-candidate UAE official source map exists.
- Top-40 no-save validation was completed.
- Only two candidates were accepted as no-save next-step candidates, both DFSA.
- ADGM/FSRA and SCA are still high-risk remediation groups.

## 2. What Failed In The Top-40 Sprint

ADGM/FSRA issues:

- several candidate URLs resolved to 404/nav-shell pages;
- ADGM homepage/source pages included broad marketing/navigation text;
- one ADGM/FSRA enforcement candidate was accessible but the preview did not clearly match the expected enforcement source model;
- high noise risk and high source-health risk remained.

SCA issues:

- selected SCA legislation/decisions/laws/regulations/circulars pages returned service-directory-like text;
- several SCA candidate pages shared the same hash/preview pattern;
- parser saw access/login-policy warnings;
- no SCA candidate was accepted for default pack consideration.

## 3. Why ADGM/FSRA And SCA Are Next

ADGM/FSRA and UAE SCA are high-value compliance surfaces:

- ADGM/FSRA matters for ADGM regulated firms, fintechs, funds, exchanges, and compliance consultants.
- SCA matters for UAE securities/capital markets regulation and should not be confused with Saudi CMA.
- Both groups are necessary for a credible professional UAE source pack, but the current candidate URLs/selectors are not strong enough.

## 4. Files And Reports To Read

- `docs/top-40-source-no-save-validation-report.md`
- `docs/top-40-source-validation-selection.md`
- `docs/top-40-alert-fatigue-risk-report.md`
- `docs/top-40-source-health-risk-report.md`
- `docs/uae-60-source-pack-final-report.md`
- `docs/uae-60-source-candidate-discovery.md`
- `docs/no-garbage-source-policy.md`
- `docs/uae-source-pack-no-save-validation-report.md`
- `docs/source-registry-expansion-change-report.md`
- `docs/source-monitor-operational-risk-alerts.md`
- `docs/acknowledge-and-assess-workflow-spec.md`
- `product/regradar/config/uae_source_candidates.json`
- `product/regradar/sources.json`
- `tools/validate_uae_source_pack.py`
- `docs/parser-quality-gates.md`

## 5. Browser / DOM Investigation Plan

For ADGM/FSRA and SCA only:

1. Review current candidate URLs and top-40 failure results.
2. Use web search and direct official-domain checks to find current official or officially linked URLs.
3. Inspect page titles, final URLs, static/JS/PDF/table/search behavior, and source purpose.
4. Identify best wait selectors, content selectors, and fallback selectors.
5. Reject generic homepages, marketing pages, service-directory shells, private/login/CAPTCHA/paywall pages, and wrong-country sources.
6. Prefer specific official listing pages or document indexes over broad landing pages.

## 6. No-Save Validation Plan

Run only scoped Source Lab checks:

```bash
python3 run.py source-lab <URL> --no-save --json
python3 run.py source-lab <URL> --js --no-save --json
python3 run.py source-lab <URL> --js --wait-for-selector "<selector>" --content-selector "<selector>" --no-save --json
```

Rules:

- no `--save`;
- no evidence writes;
- no Telegram/email/customer delivery;
- no broad monitoring;
- small batches only;
- stop or narrow scope on repeated blocking.

## 7. Noise-Risk / Source-Health Plan

Every tested candidate receives:

- noise risk: low / medium / high / unknown;
- likely false-positive causes;
- footer/nav-heavy risk;
- dynamic timestamp/listing churn risk;
- duplicate boilerplate risk;
- source-health risk;
- selector fragility;
- access-blocking risk;
- anti-bot risk;
- manual-check requirement;
- recommendation.

No source can progress if it only returns navigation, service directory, 404 shell, duplicate boilerplate, or access warnings.

## 8. What Can And Cannot Change

Can change:

- ADGM/FSRA and SCA candidate metadata in `product/regradar/config/uae_source_candidates.json`;
- selector investigation docs;
- no-save validation docs;
- validator checks for selector investigation fields.

Cannot change:

- public source truth;
- active `sources.json` sources unless a future task explicitly approves a conservative registry migration;
- evidence/proof claims from no-save checks;
- customer-facing 40/60 source claims.

## 9. Validation Plan

Run:

```bash
git status --short
python3 -m compileall product/regradar
python3 tools/validate_uae_source_pack.py
python3 tools/validate_parser_quality.py
python3 tools/validate_workspace.py
python3 tools/validate_codex_skills.py
git diff --check
```

Run `python3 tools/validate_source_readiness_summary.py` only if present.

Frontend validation is not required unless frontend files change.

## 10. Commit Plan

If validation passes:

```bash
git add <only task files>
git commit -m "test: remediate ADGM FSRA and SCA source selectors"
git push origin main
```

Do not stage runtime data, secrets, reference repos, or unrelated files.
