# Sprint — Source Readiness Report Generator

## 1. Verdict

Implemented a manual Source Readiness Review generator for StatuteProof.

The generator reads existing UAE source data, filters source layers by buyer profile, maps internal source statuses to safe client-facing labels, and renders a branded HTML report with limitations, recommended pilot scope, and a clearly illustrative sample brief.

This is a manual sales/product deliverable for operator review. It is not a SaaS feature, API endpoint, dashboard feature, scheduler, or delivery workflow.

## 2. Files created

- `scripts/generate_source_readiness.py`
- `app/templates/source_readiness_report.html`
- `reports/source_readiness_vasp_crypto_sample.html`
- `reports/sprint_source_readiness_report_generator.md`

Note: `reports/source_readiness_vasp_crypto_sample.html` was generated for validation and operator review. It is not committed because repo instructions classify `reports/source_readiness_*.html` as generated report artifacts that should not be committed.

## 3. CLI usage

```bash
python3 scripts/generate_source_readiness.py \
  --buyer-profile vasp_crypto \
  --company-name "Acme Digital Assets Ltd" \
  --contact-name "Omar K" \
  --date 2026-06-02 \
  --output reports/source_readiness_acme_2026-06-02.html
```

If `--output` is omitted, the script writes:

```text
reports/source_readiness_{buyer_profile}_{date}.html
```

## 4. Buyer profiles supported

- `vasp_crypto`
- `payments_fintech`
- `difc_dfsa`
- `adgm_fsra`
- `aml_fiu`
- `tax_corporate`
- `data_protection`

Profile mappings are conservative and use `client_profiles` from `data/uae_source_candidates.json`. If profile mapping is missing, the script includes a source only when it appears broadly relevant and adds an operator-review limitation.

## 5. Data files read

Read-only data inputs:

- `data/uae_source_candidates.json`
- `data/uae_under_validation_sources.json`
- `sources.json`

Reference files inspected:

- `reports/source_readiness_AE_2026-05-30.html`
- `reports/sample_compliance_brief_en.md`
- `web/src/components/BuyerSourcePacks.jsx`
- `web/src/components/SourceTransparencyMatrix.jsx`

## 6. Status taxonomy

Internal statuses are mapped to safe client-facing labels:

- `active` -> `Active in monitoring`
- `under_validation` -> `Under technical validation`
- `disabled_external_access` -> `Access limited — monitoring deferred`
- `disabled_navigation_only` -> `Navigation-only — monitoring deferred`
- `limited` -> `Monitoring limited`
- `needs_adapter` -> `Needs extraction adapter`
- `blocked` -> `Blocked — not in current monitoring scope`
- `mapped` -> `Mapped — outside current scope`
- fallback -> `Under review`

The script does not expose raw internal labels such as `disabled_external_access` in the client-facing report.

Mapped candidates are not counted as active. Under-validation sources are not called active.

## 7. Generated sample report

Generated:

```text
reports/source_readiness_vasp_crypto_sample.html
```

VASP sample output:

- Sources reviewed: 5
- Active in monitoring: 3
- Under validation / needs adapter: 2
- Access-limited / deferred: 0

All seven buyer profile samples were also generated successfully into `/tmp`.

## 8. Claims safety validation

Commands passed:

```bash
python3 -m py_compile scripts/generate_source_readiness.py
python3 scripts/generate_source_readiness.py --buyer-profile vasp_crypto --company-name "Test Corp" --contact-name "Test Contact" --date 2026-06-02 --output reports/source_readiness_vasp_crypto_sample.html
grep -i "complete coverage|all regulators|real-time|35 active|guaranteed compliance|never miss|trusted by" reports/source_readiness_vasp_crypto_sample.html || true
grep -i "legal advice" reports/source_readiness_vasp_crypto_sample.html || true
grep -i "SAMPLE — ILLUSTRATIVE ONLY|NOT REAL DATA|Not legal advice|Limitations" reports/source_readiness_vasp_crypto_sample.html || true
git diff --check
```

Claims safety result:

- Unsafe claims grep returned no matches.
- Legal advice grep matched only disclaimer / not-legal-advice text.
- Required sample labels and limitations text are present.

## 9. What was deliberately not changed

- `sources.json` was not modified.
- `data/uae_source_candidates.json` was not modified.
- `data/uae_under_validation_sources.json` was not modified.
- No backend API endpoints were added.
- No dashboard feature was added.
- No Auth/Profile/Telegram/Delivery modules were modified.
- No source monitoring behavior was changed.
- No source was activated.
- No automatic delivery was added.
- No pricing or landing copy was changed.

## 10. Remaining limitations

- The report is manually generated and must be human-reviewed before sending.
- Status derivation depends on current source candidate metadata and `sources.json` matching.
- URL/name matching is conservative but not a full entity-resolution system.
- The `data_protection` profile currently has no publicly shown candidate matches in the inspected UAE source candidate data.
- Generated HTML reports are static artifacts and are not part of product delivery automation.
- The sample brief is illustrative only and not generated from live regulatory data.

## 11. Next recommendation

Add a human-review checklist for operators before sending Source Readiness Reviews to prospects:

- confirm buyer profile and source scope;
- verify no generated artifact claims full coverage;
- verify limitations are complete;
- confirm active source list against current `sources.json`;
- print/save PDF manually after review.
