# ADGM/FSRA + SCA Saved-Evidence Baseline Sprint Plan

## 1. Current State

- Latest commit before this sprint: `8fb0ced test: remediate ADGM FSRA and SCA source selectors`.
- Worktree was clean at sprint start.
- Public source truth remains: **13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation**.
- Prior no-save remediation found four strongest next-step candidates:
  1. `AE-adgm-fsra-financial-crime-prevention`
  2. `AE-adgm-fsra-rulebooks`
  3. `AE-sca-aml-cft`
  4. `AE-sca-latest-regulations`

## 2. Sprint Goal

Run saved Source Lab checks for only the four scoped candidates, capture proof/evidence artifact paths, and decide whether any candidate can move from preview-only toward evidence-confirmed or baseline-pending.

This sprint does not run broad monitoring and does not expand customer-facing source counts.

## 3. Scoped Candidates

| Source ID | URL | Selector | Current risk |
|---|---|---|---|
| `AE-adgm-fsra-financial-crime-prevention` | `https://www.adgm.com/operating-in-adgm/financial-and-cyber-crime-prevention` | `adgm-page > span` | Low noise, medium source-health risk. |
| `AE-adgm-fsra-rulebooks` | `https://www.adgm.com/legal-framework/rules-and-regulations` | `adgm-page > span` | Medium noise and source-health risk. |
| `AE-sca-aml-cft` | `https://www.sca.gov.ae/en/regulations/anti-money-laundering-and-terrorist-financing` | `[data-icms-list]` | Low noise, medium source-health risk. |
| `AE-sca-latest-regulations` | `https://www.sca.gov.ae/en/regulations/regulations` | `[data-icms-list]` | Listing-only source; medium noise, high source-health risk. |

## 4. Evidence Rules

- `--save` may write proof/snapshot/run artifacts.
- No saved result becomes monitoring-ready from a single run unless the existing certification logic proves baseline completion.
- Evidence-confirmed requires proof paths and non-empty normalized hashes.
- Monitoring-ready requires baseline runs completed and certification/activation readiness to pass.
- No-save and saved evidence are distinct states; saved evidence is not the same as active monitoring.

## 5. Commands

Run from `product/regradar`:

```bash
python3 run.py source-lab <URL> --js --wait-for-selector "<selector>" --content-selector "<selector>" --save --json
```

If a command fails because Playwright cannot launch inside the sandbox, rerun the same scoped command outside the sandbox with explicit approval/escalation. Do not change scope.

## 6. Files To Inspect / Change

Inspect:

- `docs/adgm-fsra-sca-selector-remediation-final-report.md`
- `docs/adgm-fsra-sca-source-registry-proposal.md`
- `docs/adgm-fsra-sca-no-save-validation-report.md`
- `product/regradar/config/uae_source_candidates.json`
- `product/regradar/sources.json`
- `product/regradar/run.py`
- `product/regradar/app/source_intake.py`
- `product/regradar/app/proof.py`
- `product/regradar/app/source_runs.py`

Likely changes:

- `docs/adgm-fsra-sca-saved-evidence-baseline-report.md`
- `docs/adgm-fsra-sca-source-activation-decision.md`
- `product/regradar/config/uae_source_candidates.json`
- `tools/validate_uae_source_pack.py` if proof-path validation needs to be stricter.
- generated source-run evidence artifacts under `product/regradar/data/source_runs/` and `product/regradar/data/source_snapshots/` only for the four scoped candidates.

Do not change `product/regradar/sources.json` unless strict criteria unexpectedly pass and the decision report justifies it. The default expectation is no `sources.json` change.

## 7. Validation Plan

Run from repo root:

```bash
python3 -m compileall product/regradar
python3 tools/validate_uae_source_pack.py
python3 tools/validate_parser_quality.py
python3 tools/validate_workspace.py
python3 tools/validate_codex_skills.py
git diff --check
git status --short
```

No frontend validation is required unless frontend files change.

## 8. Commit Plan

If validation passes, stage only task files and scoped evidence artifacts:

```bash
git commit -m "test: save baseline evidence for ADGM FSRA and SCA candidates"
git push origin main
```

Do not stage runtime junk, secrets, reference repositories, unrelated data, or broad monitoring output.

## 9. What This Sprint Will Not Touch

- No deployment.
- No Cloudflare or DigitalOcean changes.
- No customer messages.
- No Telegram/email delivery.
- No all-source monitoring.
- No broad crawler.
- No legal advice or compliance guarantee claims.
- No `40+` or `60` ready-source marketing claim.
