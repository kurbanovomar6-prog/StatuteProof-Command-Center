# UAE JS-Heavy Sources JSON Change Report

Date: 2026-06-15

## Changed

Yes. One source was added to `product/regradar/sources.json`:

`AE-uaefiu-typology-reports` - UAE FIU Trends and Typology Reports.

## Source Record

```json
{
  "name": "UAE FIU Trends and Typology Reports",
  "url": "https://uaefiu.gov.ae/en/more/knowledge-centre/publications/trends-typology-reports/",
  "jurisdiction": "AE",
  "category": "aml",
  "enabled": true,
  "status": "active",
  "source_id": "AE-uaefiu-typology-reports",
  "adapter_family": "fiu_eocn_document_listing",
  "adapter_name": "fiu_eocn_document_listing",
  "expected_min_length": 500,
  "proof_path": "data/source_snapshots/2026-06-15/AE/AE-uaefiu-typology-reports/intake-20260615T173740Z/proof.json",
  "normalized_hash": "f9752fc4906a03d12ab587db00dc1f37c9508688eeda7954d1e2f82ca3ea4c2d",
  "adapter_config": {
    "container_selector": "body"
  }
}
```

## Public Truth

Before this JS-heavy remediation sprint:

- 23 enabled UAE sources.
- 19 readiness-supported.
- 4 under extraction remediation.

After this JS-heavy remediation sprint:

- 24 enabled UAE sources.
- 20 readiness-supported.
- 4 under extraction remediation.

## Why Safe

- The source is official UAE FIU public content.
- It passed no-save at q=65 with meaningful AML/CFT typology content.
- It produced two saved evidence runs.
- Repeat baseline hash was stable.
- Mass-monitor dry-run returned `MONITOR_OK`.
- Agent gates passed.
- Duplicate FIU route variants were not added.

## Still Not Claimed

- No 50-source claim.
- No 60-source claim.
- No "any website can be parsed" claim.
- No legal advice, compliance guarantee, or regulator certification claim.
