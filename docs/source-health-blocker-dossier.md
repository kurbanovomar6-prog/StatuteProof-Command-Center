# StatuteProof Source Health Blocker Dossier

Date: 2026-06-21

## Purpose

This dossier records repeated-failure source runs surfaced by the operator-only
source-health report. It is not customer-facing coverage copy and must not be
used to imply complete UAE or complete family coverage.

## Current Operator Health Result

Command:

```bash
python3 - <<'PY'
import sys, json
sys.path.insert(0, 'product/regradar')
from app.source_health_timeline import build_operator_source_health_report
print(json.dumps(build_operator_source_health_report(), indent=2))
PY
```

Current result after the source-health classification fix:

- Sources checked from saved run history: 284
- Active/current enabled sources requiring operator review: 0
- Disabled or historical source IDs with repeated failures: 5
- Customer delivery: false
- External send: false

## Important Classification

The five repeated-failure rows are still real historical failures, but they are
not active fresh-alert blockers because the current registry either disables the
old source ID or replaced it with a proof-backed active alternative.

This is a classification repair, not a source recovery claim. The failures
remain visible for audit history and should stay disclosed where relevant.

## Disabled / Historical Failure Rows

### AE-adgm-fsra-rules

- Family: ADGM/FSRA
- Name: ADGM FSRA Rulebook
- URL: `https://www.fsra.adgm.com/rules-and-regulations/rulebooks`
- Consecutive failed/quality-drop runs: 3
- Registry state: `enabled=false`, `status=disabled_external_access`, `monitoring_mode=remediation`
- Active replacement: `AE-adgm-fsra-rulebooks` at `https://www.adgm.com/legal-framework/rules-and-regulations`
- Replacement state: fresh-alert, `MONITOR_OK`, proof path present, baseline complete
- Customer claim impact: safe wording is selected ADGM/FSRA sources, not complete ADGM/FSRA coverage or the old FSRA domain.
- Required next action: keep the old source disabled; continue relying only on proof-backed ADGM/FSRA active sources.

### AE-difc-legislation

- Family: DIFC
- Name: DIFC Laws Portal
- URL: `https://www.difc.ae/business/laws-regulations/legislation/`
- Consecutive failed/quality-drop runs: 3
- Registry state: `enabled=false`, `status=disabled_navigation_only`, `monitoring_mode=candidate`
- Active replacement: `AE-difc-laws-and-regulations` at `https://www.difc.com/business/laws-and-regulations/`
- Replacement state: fresh-alert, `MONITOR_OK`, proof path present, baseline complete
- Customer claim impact: safe wording is selected DIFC laws/regulatory pages, not complete DIFC legal database coverage.
- Required next action: keep stale `difc.ae` route disabled; improve DIFC through official `difc.com` legal database/listing work only if proof and baseline pass.

### AE-uae-e-laws-portal-ministry-of-justice

- Family: MoJ / Gazette / UAE Legislation
- URL: `https://elaws.moj.gov.ae/`
- Consecutive failed/quality-drop runs: 14
- Registry state: no current enabled source row under this old ID
- Current related row: `AE-uae-legislation-portal`, `monitoring_mode=remediation`, `alert_eligible=false`
- Customer claim impact: MoJ/Gazette and UAE legislation monitoring must remain a disclosed gap/remediation area.
- Required next action: find a safe official public mirror, feed, document library, or API before any monitoring claim.

### AE-uae-federal-tax-authority-fta

- Family: FTA / Tax
- URL: `https://tax.gov.ae/`
- Consecutive failed/quality-drop runs: 14
- Registry state: no current enabled source row under this old root-portal ID
- Active replacement scope: 25 direct official FTA tax PDF endpoints are fresh-alert eligible
- Customer claim impact: safe wording is 25 selected direct FTA PDF endpoints, not FTA portal monitoring.
- Required next action: keep portal/listing extraction out of claims unless a public, reproducible adapter passes proof and baseline.

### AE-uae-securities-and-commodities-authority-sca

- Family: SCA
- URL: `https://www.sca.gov.ae/`
- Consecutive failed/quality-drop runs: 3
- Registry state: no current enabled source row under this old root-portal ID
- Active replacement scope: selected direct SCA endpoints such as `AE-sca-aml-cft`, `AE-sca-circulars-rules-procedures`, `AE-sca-corporate-governance`, `AE-sca-fatca-crs`, and `AE-sca-fintech-sandbox`
- Customer claim impact: safe wording is selected SCA endpoints, not complete SCA portal or full SCA coverage.
- Required next action: resolve the SCA AML/CFT parser-review warning before using it in any buyer-facing evidence-backed example.

## Current Safe Source-Health Claim

Safe:

- No currently enabled fresh-alert source has 3+ consecutive failed/quality-drop runs in the operator report.
- Five disabled or historical source IDs retain repeated-failure history and must remain disclosed as replaced/remediation history.
- Selected official UAE sources are monitored with evidence and review gates.
- Source-family limitations remain disclosed.

Unsafe:

- Complete UAE coverage.
- Complete family coverage.
- FTA portal monitoring.
- MoJ/Gazette monitoring readiness.
- Full SCA coverage.
- Perfect parsing or never-miss monitoring.
