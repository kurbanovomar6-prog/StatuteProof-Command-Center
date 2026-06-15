# UAE 50 Current Gap Inventory

Date: 2026-06-15

## Current Counts

- Enabled UAE sources in `sources.json`: 19 after the ADGM/FSRA activation cycle.
- Readiness-supported active UAE sources: 15 after the ADGM/FSRA activation cycle.
- Enabled UAE remediation sources: 4.
- Current public truth: `19 enabled / 15 readiness-supported / 4 remediation`.
- Mass activation queue entries: 14.
- UAE work queue entries: 78.
- UAE candidate registry entries: 63 candidates plus rejected entries.

## Current Active / Readiness-Supported Sources

Current active UAE sources in `sources.json`:

1. `AE-central-bank-of-the-uae`
2. `AE-dubai-virtual-assets-regulatory-authority-vara`
3. `AE-dfsa-financial-crime-mlro-letters`
4. `AE-dfsa-aml-rulebook-module`
5. `AE-abu-dhabi-global-market-adgm`
6. `AE-uae-ministry-of-finance`
7. `AE-uae-legislation-portal`
8. `AE-sca-circulars-rules-procedures`
9. `AE-uae-ministry-of-economy`
10. `AE-vara-enforcement`
11. `AE-cbuae-regulations`
12. `AE-uaefiu-circulars`
13. `AE-adgm-fsra-financial-crime-prevention`
14. `AE-adgm-fsra-rulebooks`
15. `AE-adgm-fsra-consultations`

## Current Remediation Sources

Enabled UAE sources still under remediation:

1. `AE-dubai-financial-services-authority-dfsa`
2. `AE-uae-financial-intelligence-unit-uaefiu`
3. `AE-difc-laws-and-regulations`
4. `AE-dfsa-notices`

## Queue Activation-Ready Count

The mass activation queue has 6 activation-ready entries:

1. `AE-sca-circulars-rules-procedures`
2. `AE-dfsa-financial-crime-mlro-letters`
3. `AE-dfsa-aml-rulebook-module`
4. `AE-adgm-fsra-financial-crime-prevention`
5. `AE-adgm-fsra-rulebooks`
6. `AE-adgm-fsra-consultations`

The three SCA/DFSA entries were promoted to `sources.json` in commit `3b93688`. The three ADGM/FSRA entries were promoted in the current continuous activation cycle after proof-backed repeat baseline and mass-monitor dry-run.

## Proof-Backed But Held Count

No mass activation queue entry is currently proof-backed but held. Older reports held `AE-dfsa-aml-rulebook-module`, but the all-in-one activation sprint retested it through the monitor path and promoted it.

## Candidates By Regulator

### SCA

Current candidates include SCA regulations, AML/CFT, circulars, decisions, laws, legislation, homepage, and media/news. One SCA source is active:

- active: `AE-sca-circulars-rules-procedures`
- remediation/blocked examples: `AE-sca-latest-regulations`, `AE-sca-aml-cft`, `AE-sca-regulations`, `AE-sca-decisions`

Primary blockers: noisy ASP.NET/listing output, listing adapter required, nav-shell on AML/CFT, duplicated or malformed paths in older candidates.

### ADGM / FSRA

Current candidates include main ADGM, financial crime, rules/regulations, guidance, consultations, enforcement, notices, public register, legislation, and data protection.

Closest candidates:

- `AE-adgm-fsra-financial-crime-prevention`: activated after focused `adgm-page` extraction, repeat baseline, and mass-monitor dry-run.
- `AE-adgm-fsra-rulebooks`: activated on the current `/legal-framework/rules-and-regulations` URL after repeat baseline and dry-run.
- `AE-adgm-fsra-consultations`: activated after focused `adgm-page` extraction, repeat baseline, and dry-run.
- `AE-adgm-fsra-guidance-policy`, `AE-adgm-fsra-enforcement`: still require proof and repeat baseline.

Primary blockers: deterministic selector/adapter path, proof save, repeat baseline, mass-monitor dry-run, and registry reconciliation.

### DFSA / DIFC

Current active queue-promoted DFSA sources:

- `AE-dfsa-financial-crime-mlro-letters`
- `AE-dfsa-aml-rulebook-module`

Current remediation:

- `AE-dubai-financial-services-authority-dfsa`
- `AE-dfsa-notices`
- `AE-difc-laws-and-regulations`

Other work queue candidates include DFSA rulebook modules, consultations, enforcement, public register, publications, DIFC legal database, data protection, and consultation papers.

Primary blockers: legacy DFSA URL source model, nav-shell/page-not-found collisions, and exact selector/source replacement.

### VARA

Active VARA sources:

- `AE-dubai-virtual-assets-regulatory-authority-vara`
- `AE-vara-enforcement`

Candidates/remediation include rulebooks overview, company rulebook, AML/CFT rulebook, public register, current framework, and news.

Primary blockers: 404/not-found shell detection, PDF/document listing extraction, and proof/baseline work.

### UAE FIU / EOCN

Active:

- `AE-uaefiu-circulars`

Remediation:

- `AE-uae-financial-intelligence-unit-uaefiu`

Candidates include FIU guidance/publications/laws/goAML and EOCN laws/regulations.

Primary blockers: homepage too shallow, document listing semantics, EOCN table/listing quality, proof/baseline gaps.

### CBUAE

Active:

- `AE-cbuae-regulations`

Candidates/remediation include homepage, publications, payment systems, AML/CFT, consultations, licensing, circulars, open data, and consumer protection.

Primary blockers: 403/access-source-health on several paths, official alternate endpoint discovery, document listing extraction, no bypassing WAF-like blocks.

## Blocked Candidates By Reason

- Access blocked or likely WAF/403: several CBUAE pages.
- Listing adapter required: SCA regulations/AML variants, EOCN laws/regulations, FIU publications.
- Nav-shell only: legacy DFSA configured sources, SCA AML/CFT.
- Quality below threshold: ADGM financial crime at 59 in prior sprint.
- Source model ambiguous: DFSA main/notices, DIFC laws/remediation hold.
- PDF-only/document listing required: VARA rulebook/framework pages.

## Closest Sources To Activation

The shortest path to more active sources is:

1. `AE-adgm-fsra-financial-crime-prevention`: fix deterministic adapter/selector path, save proof twice, dry-run.
2. `AE-adgm-fsra-rulebooks`: no-save/proof/baseline/dry-run using known rules/regulations page.
3. `AE-adgm-fsra-guidance-policy`: no-save/proof/baseline/dry-run if listing output is meaningful and stable.
4. `AE-adgm-fsra-consultations`: no-save/proof/baseline/dry-run if listing output is meaningful and stable.
5. `AE-adgm-fsra-enforcement`: no-save/proof/baseline/dry-run if official endpoint and extraction remain stable.
6. `AE-difc-laws-and-regulations`: resolve registry hold with proof/baseline/gates or keep remediation.
7. `AE-uae-financial-intelligence-unit-uaefiu`: replace homepage with publications/guidance source or keep homepage remediation.
8. `AE-dfsa-notices` and `AE-dubai-financial-services-authority-dfsa`: replace legacy/nav-shell URLs with proven active DFSA source models or keep remediation.

## Adapter Gaps

- ADGM/FSRA needs a deterministic page/content adapter that does not rely on unavailable custom tags when meaningful static text is present.
- SCA still needs item-level extraction for latest regulations and AML/CFT pages.
- DFSA/DIFC needs source-model replacement for legacy sources and better tab/summary detection.
- VARA needs a reliable PDF/rulebook listing adapter path with not-found shell checks.
- FIU/EOCN needs public document/table/list extraction with stable item hashes.
- CBUAE needs accessible alternate official endpoints before adapter work can be useful.

## Evidence / Baseline Gaps

- Wider work queue entries marked `no_save_passed` or `activation_ready` are not all proof-backed in the mass queue.
- Several legacy active sources have readiness support in reports but limited proof metadata stored directly in `sources.json`.
- New activations should include proof path, normalized hash, adapter metadata, baseline count, and gate summaries where the current schema accepts them.

## Source-Health / Noise Gaps

- SCA and FIU listings risk noisy generic site links unless filtered by regulatory terms.
- VARA framework/rulebook paths may return not-found shells or PDF-only pages.
- CBUAE access blocks must remain remediation unless an accessible official endpoint is found.
- DFSA legacy URLs can collide with page-not-found/nav-shell content and must not be promoted.

## Exact Route To 20

Need 5 additional readiness-supported sources beyond the current 15.

Most realistic route:

1. ADGM guidance/policy statements.
2. ADGM enforcement/additional obligations.
3. DIFC legal database or consultation papers if proof-backed.
4. VARA rulebooks/framework if current official endpoint/PDF listing stabilizes.
5. FIU guidance/publications or EOCN laws/regulations if listing quality passes.

## Exact Route To 30

After route-to-20, add 10 more from:

- SCA latest regulations, AML/CFT, decisions, laws, regulations, circular variants.
- DFSA consultations, enforcement, publications, public register if public and relevant.
- VARA company rulebook, AML/CFT rulebook, public register.
- EOCN sanctions/TFS/legal pages.
- Ministry of Economy AML/DNFBP guidance.

## Exact Route To 40

Requires successful source-specific remediation across at least four regulators:

- SCA item-level listings.
- DFSA/DIFC rulebook/listing replacements.
- VARA PDF/rulebook listings.
- FIU/EOCN document/table extraction.
- CBUAE accessible alternate endpoint discovery.

## Exact Route To 50

Requires a 75+ candidate universe with proof/baseline/gated conversion. The likely blocker is not queue mechanics anymore; it is official endpoint accessibility and source-specific extraction. If CBUAE and SCA remain blocked/noisy, 50 requires expanding into Ministry of Economy/DNFBP, UAE legislation, tax, free-zone regulatory pages, and official public registers without adding vanity or non-regulatory pages.
