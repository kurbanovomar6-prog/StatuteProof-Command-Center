# SCA / DFSA / CBUAE Current Blocker Inventory

Date: 2026-06-15

## SCA Candidates And Blockers

Current queue entries:

- `AE-sca-latest-regulations`  
  URL: `https://www.sca.gov.ae/en/regulations/regulations`  
  Current state: remediation.  
  Blocker: SCA table/listing candidates exist, but source discovery over-includes generic same-domain pages and listing extraction needs stronger item-level filtering.

- `AE-sca-aml-cft`  
  URL: `https://www.sca.gov.ae/en/regulations/anti-money-laundering-and-terrorist-financing`  
  Current state: remediation.  
  Blocker: prior save-mode attempt produced nav-shell; needs DOM/adapter remediation before evidence save.

Related candidates/work-queue entries:

- `AE-sca-circulars`
- `AE-sca-regulations`
- `AE-sca-decisions`
- `AE-sca-laws`
- legacy `.aspx` SCA candidates now largely replaced by newer `/en/regulations/...` paths.

P0 blockers:

- Reject generic official but low-value links such as About/Services unless clearly register/public-data with buyer relevance.
- Detect or normalize malformed doubled paths such as `/en/regulations/en/regulations/...`.
- Improve SCA item-level extraction for title/link/date/row hash.

## DFSA Candidates And Blockers

Current mass queue entries:

- `AE-dfsa-rulebook-thomsonreuters`  
  URL: `https://dfsaen.thomsonreuters.com/`  
  Current state: candidate.  
  Blocker: rulebook module extraction needs no-save/fixture validation.

- `AE-dfsa-aml-mlro-notices`  
  URL: `https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance`  
  Current state: candidate.  
  Blocker: last live discovery resolved to `/summary`; DOM type was unknown.

More precise candidates exist in `uae_source_candidates.json` / `uae_source_work_queue.json`:

- `https://dfsaen.thomsonreuters.com/rulebook/rulebook-modules`
- `https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/financial-crime-prevention-notices-and-mlro-letters`

P0 blockers:

- Update mass queue entries toward these more precise endpoints.
- Add deterministic selector hints for DFSA summary/tab/listing pages where possible.
- Keep unknown DOM as remediation, not readiness.

## CBUAE Candidates And Blockers

Current mass queue entry:

- `AE-cbuae-regulations`  
  URL: `https://www.centralbank.ae/en/our-operations/regulations/`  
  Current state: candidate.  
  Blocker: last live discovery returned HTTP 403.

Related candidates:

- `AE-cbuae-regulations`
- `AE-cbuae-publications`
- `AE-cbuae-payment-systems`
- `AE-cbuae-aml-cft`
- `AE-cbuae-consultations`
- `AE-cbuae-open-data`

P0 blockers:

- Classify HTTP 403 as access/source-health remediation, not source rejection or readiness.
- Try only safe official alternate discovery methods: robots/sitemap, official same-domain alternate paths, public document links.
- Do not bypass WAF or use private/API endpoints.

## Current Adapter Coverage

Existing adapter families include:

- `sca_listing`
- `dfsa_rulebook`
- `dfsa_notice_listing`
- `cbuae_document_listing`
- generic `listing`
- generic `table`
- generic `pdf_listing`
- generic `public_json_api`

Gaps:

- SCA adapter needs stronger filtering against generic titles and better date/link extraction.
- DFSA rulebook/listing adapter needs fixture-backed confidence.
- CBUAE adapter cannot solve 403 alone; discovery must first find accessible official endpoints.

## Current Selector Coverage

SCA:

- `[data-icms-list]`, `table`, `main`, listing/table heuristics.

DFSA:

- No reliable mass queue selector for `/summary` yet.
- More precise AML/MLRO notices URL exists but is not the current mass queue URL.

CBUAE:

- No confirmed accessible selector in current mass queue.

## Current Discovery / Noise Issues

- SCA same-domain discovery can score pages under official domain even when they are generic About/Services/Open Data pages.
- SCA path joining can surface doubled paths.
- Discovery should favor regulator-relevant paths over official-but-low-value pages.

## Current Evidence / Baseline Status

- No new evidence is recorded in `mass_source_activation_queue.json`.
- No SCA/DFSA/CBUAE mass queue entry is activation-ready.
- Existing UAE 50-source queue has 2 activation-ready candidates overall, but public source truth remains unchanged.

## P0 / P1 / P2 Blockers

P0:

- Safe batch runner missing.
- SCA noisy discovery filtering.
- CBUAE 403 classification and alternate discovery handling.
- DFSA precise endpoint/selector remediation.

P1:

- SCA/DFSA/CBUAE fixtures for source-specific adapter tests.
- Queue updates for precise DFSA endpoints.

P2:

- UI batch runner controls after backend runner is stable.
- Additional regulator-specific adapters after SCA/DFSA/CBUAE prove the pattern.
