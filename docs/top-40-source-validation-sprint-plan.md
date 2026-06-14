# Top-40 Source Validation Sprint Plan

## 1. Current State

- Latest source-pack strategy commit: `83c6f39`.
- Candidate source map exists at `product/regradar/config/uae_source_candidates.json`.
- Candidate sources discovered: 60.
- Previous no-save checks run: 5.
- Previous no-save readiness-supported candidates: 2.
- Previous no-save remediation/blocked candidates: 3.
- Current customer-facing source truth remains: **13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation**.
- `sources.json` must not change unless a focused validation result clearly justifies a conservative non-active/candidate update.

## 2. Source Candidates Available

The sprint will use the 60-candidate official UAE map and select the 40 records with `top_40_candidate: true`.

Priority order:

1. ADGM/FSRA
2. SCA
3. VARA
4. CBUAE
5. UAE FIU / AML / sanctions
6. DFSA/DIFC where the source model is clear
7. Federal legislation/tax/company-register sources only when compliance-relevant

## 3. Batch Order

Batch 1: ADGM/FSRA candidates.

Batch 2: UAE SCA candidates.

Batch 3: VARA candidates.

Batch 4: CBUAE candidates.

Batch 5: UAE FIU / AML / sanctions candidates.

Batch 6: remaining high-priority DFSA/DIFC/federal candidates.

The first pass will stop or narrow scope if a domain repeatedly blocks, returns CAPTCHA/login warnings, or produces mostly navigation shells.

## 4. Validation Methodology

For each selected candidate:

1. Run no-save Source Lab only.
2. Do not write evidence.
3. Do not send alerts.
4. Do not run all-source monitoring.
5. Capture provider, extraction method if exposed, normalized length/hash, quality score/label, readiness status, activation readiness, evidence level, nav-shell flag, collision flag, warnings, failure reason, remediation hint, and preview.
6. Treat no-save success as preview/readiness input only, never evidence-confirmed or monitoring-ready.

Default command:

```bash
python3 run.py source-lab <URL> --no-save --json
```

For likely JavaScript/known selectors:

```bash
python3 run.py source-lab <URL> --js --wait-for-selector "<selector>" --content-selector "<selector>" --no-save --json
```

## 5. Alert-Fatigue / Noise-Risk Checks

Each tested source will receive:

- `noise_risk`: low / medium / high / unknown
- likely false-positive causes
- dynamic content signal
- footer/nav-heavy signal
- listing-page churn risk
- pagination/changing counters risk
- timestamp-only risk
- duplicate boilerplate risk
- CSS/script-only risk
- recommendation

A source that parses but is likely to spam MLROs should remain remediation or require noise filters.

## 6. Source-Health Risk Checks

Each tested source will receive:

- `source_health_risk`: low / medium / high / unknown
- parser maintenance risk
- selector fragility
- JavaScript dependency
- PDF complexity
- access-blocking risk
- anti-bot risk
- manual-check requirement
- recommended health status

No source should enter a default pack if it is likely to fail silently.

## 7. Files To Inspect

- `docs/uae-60-source-pack-expansion-plan.md`
- `docs/uae-source-pack-agent-review-plan.md`
- `docs/current-source-pack-inventory-before-expansion.md`
- `docs/uae-regulatory-source-taxonomy.md`
- `docs/uae-60-source-candidate-discovery.md`
- `docs/no-garbage-source-policy.md`
- `docs/uae-source-pack-no-save-validation-report.md`
- `docs/uae-default-source-packs-by-plan.md`
- `docs/source-registry-expansion-change-report.md`
- `docs/source-monitor-operational-risk-alerts.md`
- `docs/acknowledge-and-assess-workflow-spec.md`
- `docs/uae-60-source-pack-final-report.md`
- `product/regradar/config/uae_source_candidates.json`
- `product/regradar/sources.json`
- `tools/validate_uae_source_pack.py`

## 8. Files Likely To Change

- `docs/top-40-source-validation-selection.md`
- `docs/top-40-alert-fatigue-risk-report.md`
- `docs/top-40-source-health-risk-report.md`
- `docs/top-40-source-no-save-validation-report.md`
- `product/regradar/config/uae_source_candidates.json`
- `tools/validate_uae_source_pack.py`

`sources.json` should not change in this sprint unless a conservative candidate/non-active metadata update becomes clearly necessary.

## 9. Validation Plan

Run from project root:

```bash
git status --short
python3 -m compileall product/regradar
python3 tools/validate_uae_source_pack.py
python3 tools/validate_parser_quality.py
python3 tools/validate_workspace.py
python3 tools/validate_codex_skills.py
git diff --check
```

Run `python3 tools/validate_source_readiness_summary.py` only if the script exists.

Frontend validation is not required unless frontend files change.

## 10. Commit Plan

If validation passes:

```bash
git add <only task files>
git commit -m "test: validate top UAE source candidates for readiness and noise risk"
git push origin main
```

Do not stage runtime data, reference repos, secrets, or unrelated files.

## 11. What Not To Touch

- Deployment, Cloudflare, DigitalOcean.
- `.env` or secrets.
- Telegram/email/customer delivery.
- Broad monitoring or all-source monitoring.
- Evidence saving unless separately scoped.
- Customer-facing 40/60 source claims.
- Legal advice or guaranteed compliance wording.
- Private/login/CAPTCHA/paywall sources.
- Active `sources.json` source count.
