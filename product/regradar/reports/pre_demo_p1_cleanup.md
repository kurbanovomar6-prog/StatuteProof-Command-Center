# Pre-Demo P1 Cleanup

## 1. Verdict

Pre-demo P1 cleanup is complete.

The dashboard no longer says personalized routing is the next step. It now describes current manual sample and reviewed-alert preview delivery accurately, while explicitly stating that automatic scheduled delivery is not enabled.

The VASP Source Readiness sample was regenerated for operator/demo use, but it remains untracked and was not staged because generated report artifacts should not be committed.

The old multi-market compliance brief sample is now clearly archived as not for client demo, and a new UAE-first StatuteProof sample brief was added for demo-safe reference.

## 2. Files changed

- `web/src/components/app/DashboardHome.jsx`
- `web/src/data/watchlistOptions.js`
- `reports/sample_compliance_brief_en.md`
- `reports/sample_compliance_brief_uae_en.md`
- `reports/pre_demo_p1_cleanup.md`

Generated but not staged:

- `reports/source_readiness_vasp_crypto_sample.html`

## 3. DashboardHome copy fix

Updated stale workspace delivery copy:

- `Brief delivery` now shows `Manual`.
- Subcopy now says sample and reviewed-alert previews are available.
- Checklist now says sample brief delivery can be tested from Integrations.
- The right-side panel now says manual reviewed-alert preview delivery is available from Alerts when Telegram is connected.
- The same panel explicitly says automatic scheduled delivery is not enabled yet.

No functionality was changed.

## 4. Source readiness sample regeneration

Regenerated:

```bash
python3 scripts/generate_source_readiness.py --buyer-profile vasp_crypto --company-name "Test Corp" --contact-name "Test Contact" --date 2026-06-02 --output reports/source_readiness_vasp_crypto_sample.html
```

Generator output:

- Sources reviewed: 5
- Active in monitoring: 3
- Under validation / needs adapter: 2
- Access-limited / deferred: 0

Confirmed in generated HTML:

- StatuteProof branding
- `Source Readiness Review`
- responsive CSS with `@media (max-width: 900px)`
- `SAMPLE — ILLUSTRATIVE ONLY`
- `NOT REAL DATA — NOT A REAL REGULATORY CHANGE`
- `Not legal advice`
- `Limitations`

This generated HTML remains untracked and was not committed.

## 5. Legacy sample brief handling

Updated `reports/sample_compliance_brief_en.md` with a top warning:

```text
ARCHIVED LEGACY SAMPLE — NOT FOR CLIENT DEMO
```

The file is retained only for historical reference and now points operators to:

- `reports/source_readiness_vasp_crypto_sample.html`
- `reports/sample_compliance_brief_uae_en.md`

Created `reports/sample_compliance_brief_uae_en.md` as the demo-safe UAE-first StatuteProof sample. It includes:

- `SAMPLE — ILLUSTRATIVE ONLY`
- `NOT REAL DATA — NOT A REAL REGULATORY CHANGE`
- VARA / VASP sample format
- source proof placeholder
- limitation note
- Not legal advice disclaimer

## 6. Validation result

Commands run:

```bash
cd web && npm run build
python3 -m compileall app run.py -q
git diff --check
grep -R "personalized routing is next step\|next pilot step\|weekly briefs delivered\|automatic scheduled delivery is enabled\|production delivery active" web/src --exclude-dir=node_modules || true
grep -i "complete coverage\|all regulators\|real-time\|35 active\|guaranteed compliance\|never miss\|trusted by" reports/source_readiness_vasp_crypto_sample.html || true
grep -R "RegRadar\|Turkey\|Kazakhstan\|MASAK\|ARDFM" web/src app/templates reports/source_readiness_vasp_crypto_sample.html reports/sample_compliance_brief_uae_en.md --exclude-dir=node_modules || true
```

Results:

- Frontend build: PASS
- Backend compile: PASS
- Diff whitespace check: PASS
- Stale dashboard delivery copy grep: PASS
- Source readiness unsafe claims grep: PASS
- Old branding/non-UAE active demo grep: PASS

Note:

- Vite build still prints the existing Node deprecation warning for `module.register()`. Build succeeds.

## 7. Remaining demo cautions

- Do not use the archived legacy sample brief in prospect demos.
- Do not commit generated source readiness HTML artifacts unless policy changes.
- Do not claim automatic scheduled delivery, scheduled weekly briefs, complete UAE coverage, real-time alerts, or guaranteed compliance.
- The regenerated source readiness HTML is an operator-reviewed demo artifact, not an automatically delivered SaaS report.
