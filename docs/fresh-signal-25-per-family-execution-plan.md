# Fresh Signal 25 Per Family Execution Plan

Date: 2026-06-19

## Clean State

- Worktree clean before start: yes.
- Latest commit before this task: `caa40c1 feat: harden UAE fresh signal monitoring with adapter gates`.
- No Cloudflare/DigitalOcean/deployment work is in scope.
- No secrets, `.env`, customer emails, private portals, CAPTCHA, login, paywall, or private APIs are in scope.

## Current Source Truth

Current enabled UAE source truth from `product/regradar/sources.json`:

- Enabled UAE sources: 226
- `monitoring_mode: fresh_alert`: 96
- `monitoring_mode: evidence_library`: 60
- `monitoring_mode: candidate`: 62
- `monitoring_mode: remediation`: 8
- Sources with any `last_monitor_status: MONITOR_OK`: 150

The product's customer-safe fresh-monitoring number is the `fresh_alert` count with proof/hash/baseline/MONITOR_OK. The 150 MONITOR_OK number includes static evidence-library records and must not be used as the fresh-alert claim.

## Current Count Per Buyer Family

The source registry uses mixed technical categories, so this sprint will use buyer-family mapping based on URL, source owner, source name, and existing audit data.

| Family | Enabled/Matched | Fresh Alert | Fresh Alert + MONITOR_OK | Evidence Library | Candidate | Remediation | Deficit To 25 |
|---|---:|---:|---:|---:|---:|---:|---:|
| CBUAE | 27 | 0 | 0 | 1 | 26 | 0 | 25 |
| VARA | 25 | 16 | 16 | 1 | 8 | 0 | 9 |
| DFSA | 40 | 5 | 5 | 27 | 8 | 0 | 20 |
| DIFC | 25 | 3 | 3 | 15 | 7 | 0 | 22 |
| ADGM/FSRA | 25 | 2 | 2 | 14 | 9 | 0 | 23 |
| UAE FIU | 7 | 2 | 2 | 0 | 4 | 1 | 23 |
| EOCN / sanctions / TFS | 20 | 18 | 18 | 0 | 0 | 2 | 7 |
| SCA | 5 | 1 | 1 | 1 | 0 | 4 | 24 |
| MoJ / UAE Legislation / Gazette | 1 | 0 | 0 | 0 | 0 | 1 | 25 |
| MoF | 1 | 0 | 0 | 1 | 0 | 0 | 25 |
| FTA | 25 | 25 | 25 | 0 | 0 | 0 | 0 |
| MoE / DNFBP AML | 43 | 42 | 42 | 1 | 0 | 0 | 0 |

## Important Interpretation

- A source does not need to change every day.
- A source must be daily-checkable and capable of producing a meaningful official regulatory signal when the authority publishes something new.
- Static detail pages, one-time news articles, generic homepages, duplicate pages, and evidence-only PDFs do not count toward a family being Strong Fresh Signal.
- Direct EOCN and official SCA/FIU/MoJ/MoF coverage must not be hidden behind substitute sources unless the substitution is explicitly labelled partial.

## Official-Source Strategy Per Family

### CBUAE

Primary path:

- Convert existing 25 CBUAE rulebook/regulatory candidates from `candidate` to `fresh_alert` only after proof, repeat baseline, and mass-monitor MONITOR_OK.
- Use the registered CBUAE rulebook adapter for `rulebook.centralbank.ae` modules and revision updates.
- Keep CBUAE homepage as `evidence_library`.

Expected blockers:

- JavaScript-rendered rulebook pages.
- Generic extraction returning skeleton content.
- Need adapter-aligned proof runs, not ad hoc one-off hashes.

### VARA

Primary path:

- Convert 8 existing VARA rulebook PDF/revision/enforcement candidates if they pass PDF/hash/listing monitoring.
- Research additional official VARA admin order, enforcement, guidance, revision, and rulebook module endpoints if fewer than 25 fresh-alert sources remain.

Expected blockers:

- Direct PDF handling must be version/hash monitoring, not static article counting.
- VARA homepage remains weak/static unless adapter extracts useful update listings.

### DFSA

Primary path:

- Keep static individual notice pages in `evidence_library`.
- Activate existing DFSA candidates: AML/MLRO letters, consultation listing, enforcement decisions, regulatory actions, Thomson Reuters rulebook modules if public and safe.
- Research more official DFSA listing/index/update pages, not individual old notice pages.

Expected blockers:

- Thomson Reuters rulebook pages may require rendered DOM.
- Some DFSA sources are useful evidence but not future alert sources.

### DIFC

Primary path:

- Keep static whats-on/news detail pages in `evidence_library`.
- Activate DIFC laws, legal database, data protection, AML/CFT, economic substance, consultations, legal notices, and official PDFs only if accessible and daily-checkable.
- Use official DIFC asset/CDN PDF alternatives only when clearly official and permitted.

Expected blockers:

- Potential 403/geographic/CDN restrictions.
- Static law PDFs may be evidence-library unless version/update pages can be daily monitored.

### ADGM/FSRA

Primary path:

- Convert key ADGM/FSRA candidates using registered FSRA/listing adapter or new ADGM listing adapters.
- Prioritize circulars, regulatory alerts, consultations, guidance, enforcement, RA circulars, listing authority, legal framework, data protection listing.
- Keep old individual announcements as `evidence_library`.

Expected blockers:

- Web-component listings need adapter refinement.
- Individual announcement pages are not enough for fresh signal.

### UAE FIU

Primary path:

- Convert FIU publications, typology reports, AML/CFT laws, circulars/notices, annual reports, and press releases where proof/baseline/MONITOR_OK passes.
- Build a Playwright/listing adapter if the pages need rendered content.

Hard boundary:

- Do not use goAML or private portals.

Expected blockers:

- Official public FIU universe may be smaller than 25 true fresh-alert endpoints.
- If fewer than 25 official endpoints exist, document source-universe limit and exact next remedy.

### EOCN / Sanctions / TFS

Primary path:

- Convert direct EOCN laws/regulations and news sources that already passed Playwright no-save into proof-backed fresh-alert if they pass baseline.
- Use MoE TFS sources as partial substitute coverage only when labelled as MoE-owned TFS support, not direct EOCN coverage.
- Add official guidance/publication/designation-list endpoints only with noise controls.

Expected blockers:

- Direct EOCN official source universe may be smaller than 25 endpoints.
- Designation-list churn can be noisy and requires alert policy.

### SCA

Primary path:

- Convert SCA regulations, FATCA/CRS, corporate governance, circulars/rules/procedures, decisions, enforcement/violations, and document/download endpoints.
- Build/refine Playwright selector and SCA listing/PDF adapters.

Expected blockers:

- Some SCA pages are rendered and require selector-specific extraction.
- Some pages may expose generic shell content unless adapter extracts tables/documents.

### MoJ / UAE Legislation / Gazette

Primary path:

- Investigate UAE legislation portal, MoJ law/gazette pages, federal law/decree listings, and official PDF/document listings.
- Build WAF/access classifier and official alternative endpoint adapter where permitted.

Expected blockers:

- WAF/access controls may block public monitoring.
- If blocked, do not bypass; document exact status and official alternatives.

### MoF

Primary path:

- Replace generic MoF homepage with official decision/news/document/policy/tax treaty/budget publication listings that can be checked daily.
- Build document/news/decision listing adapter.

Expected blockers:

- MoF may have limited high-signal daily-checkable pages.
- Generic homepage remains evidence-library only.

### Already Strong Families

FTA and MoE/DNFBP AML already meet 25+ fresh-alert MONITOR_OK. This task will validate they remain compliant with daily-check metadata and validators, but they are not the primary activation bottleneck.

## Adapter Strategy

Adapter work must precede activation where generic extraction is weak:

- Use registered `CBUAERulebookAdapter` for CBUAE rulebook pages and revision updates.
- Use registered `FSRACircularsAdapter` where it genuinely handles ADGM/FSRA listings.
- Add source-specific adapters only when fixture tests prove the extraction pattern:
  - PDF hash/version adapter for official versioned PDFs.
  - Playwright/rendered listing adapters for JS pages.
  - Table/listing adapters for SCA/FIU/EOCN/MoF/MoJ.
  - Access-blocked classifiers for WAF/403/robots/login/CAPTCHA.

## Proof / Baseline / MONITOR_OK Strategy

For every candidate promoted to `fresh_alert`:

1. Run controlled no-save validation.
2. Save evidence/proof.
3. Store `proof_path`.
4. Store `normalized_text_path`.
5. Store `normalized_hash`.
6. Run repeat baseline at least twice.
7. Verify stable hash or documented safe non-noisy diff.
8. Run mass-monitor dry-run and require `MONITOR_OK`.
9. Set `recommended_check_frequency: daily`.
10. Set `expected_update_pattern`, `fresh_signal_type`, `customer_alert_policy`, `noise_risk`, and `source_health_risk`.
11. Run Source Monitor, Evidence Trail, QA/Critic, Legal Language, Product Manager, and Code Architect gates.

No no-save-only or one-run-only source may become `fresh_alert`.

## Daily-Check Schedule Strategy

All `fresh_alert` sources will be normalized around:

- `recommended_check_frequency: daily`
- `fresh_signal_type`: law, rulebook_revision, circular, notice, consultation, enforcement, sanctions_tfs, tax_guidance, legal_update, document_listing, publication_listing, pdf_version_hash
- `expected_update_pattern`: regulator-dependent; often irregular, not daily-changing
- `customer_alert_policy`: alert only on material listing/document/hash/content changes, not on boilerplate, timestamp-only, layout-only, or low-character diffs

## Validators To Update

Required validators:

- `tools/validate_fresh_signal_sources.py`
- `tools/validate_source_monitoring_modes.py`
- `tools/validate_no_static_sources_as_alerts.py`
- `tools/validate_fresh_signal_25_per_family.py`
- `tools/validate_daily_checkable_sources.py`
- `tools/validate_no_unvalidated_active_sources.py`
- `tools/validate_balanced_source_family_coverage.py`
- `tools/validate_uae_coverage_claims.py`

Validators must fail if a family is marked Strong without 25+ daily-checkable `fresh_alert` sources with proof/hash/baseline/MONITOR_OK.

## Commit Policy

- Stage only files from this task.
- Do not stage runtime junk, `__pycache__`, secrets, `.env`, unrelated files, or customer data.
- Commit only after Python tests, validators, `git diff --check`, and frontend validation if touched.
- Push only after commit succeeds.

## What Will Not Be Claimed

The task will not claim:

- complete UAE coverage;
- complete family coverage unless validators prove it;
- legal advice;
- guaranteed compliance;
- perfect parsing;
- never missing updates;
- regulator certification;
- all-source coverage;
- broad SCA/EOCN/FIU/CBUAE claims before the relevant sources actually have fresh-alert MONITOR_OK.

## Hard Stop Conditions

Stop or hold a source if:

- access requires login, CAPTCHA, paywall, private portal, or private API;
- source is a generic homepage and better official endpoints exist;
- source is static detail content that cannot produce future fresh signal;
- source is duplicate or shell content;
- source lacks proof/hash/baseline/MONITOR_OK;
- source has unresolved high noise or high source-health risk.
