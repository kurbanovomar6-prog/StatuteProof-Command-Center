# FTA / ADGM Eight-Source Truth Repair Plan

## Current Truth Gate

Last verified committed truth:

- 79 enabled UAE sources
- 78 readiness-supported / monitoring-active sources
- 1 remediation source

Current dirty worktree claim:

- 87 enabled UAE sources
- 86 active sources
- 1 remediation source

The dirty increase comes from eight FTA/ADGM rows that are marked active before completing the activation evidence chain. These rows must not remain active unless they pass proof, repeat baseline, mass-monitor dry-run, source-health, noise, and review gates.

## Eight Unvalidated Rows

| Proposed source_id | Current source | URL | Missing activation fields |
| --- | --- | --- | --- |
| AE-fta-tax-legislation-listing | Federal Tax Authority - All Tax Legislation | https://tax.gov.ae/en/legislation.aspx | source_id, proof_path, normalized_hash, baseline_runs_completed, last_monitor_status |
| AE-fta-vat-guides-references | Federal Tax Authority - VAT Guides and References | https://tax.gov.ae/en/taxes/vat/guides.references.aspx | source_id, proof_path, normalized_hash, baseline_runs_completed, last_monitor_status |
| AE-fta-corporate-tax-guides-references | Federal Tax Authority - Corporate Tax Guides and References | https://tax.gov.ae/en/taxes/corporate.tax/corporate.tax.guides.references.aspx | source_id, proof_path, normalized_hash, baseline_runs_completed, last_monitor_status |
| AE-fta-media-centre | Federal Tax Authority - Media Centre | https://tax.gov.ae/en/media.centre.aspx | source_id, proof_path, normalized_hash, baseline_runs_completed, last_monitor_status |
| AE-fta-corporate-tax-legislation | Federal Tax Authority - Corporate Tax Legislation | https://tax.gov.ae/en/legislation/corporate-tax.aspx | source_id, proof_path, normalized_hash, baseline_runs_completed, last_monitor_status |
| AE-adgm-fsra-supervision-circulars | ADGM FSRA Supervision Circulars | https://www.adgm.com/operating-in-adgm/additional-obligations-of-financial-services-entities/supervision/circulars | source_id, proof_path, normalized_hash, baseline_runs_completed, last_monitor_status |
| AE-adgm-fsra-regulatory-alerts | ADGM FSRA Regulatory Alerts | https://www.adgm.com/operating-in-adgm/additional-obligations-of-financial-services-entities/enforcement/regulatory-alerts | source_id, proof_path, normalized_hash, baseline_runs_completed, last_monitor_status |
| AE-adgm-data-protection-regulations-2021-pdf | ADGM Data Protection Regulations 2021 - Official PDF | https://www.adgm.com/documents/office-of-data-protection/resources/adgm-data-protection-regulations-2021-updated.pdf | source_id, proof_path, normalized_hash, baseline_runs_completed, last_monitor_status |

## Why These Rows Matter

- FTA sources would improve a currently thin tax/corporate compliance family if they extract official document listings rather than navigation shells.
- ADGM FSRA circulars and regulatory alerts would improve ADGM/FSRA operational coverage if listings are stable and not duplicate shells.
- ADGM Data Protection Regulations PDF is commercially useful for privacy/data-protection buyers if PDF extraction is meaningful and stable.

## No-Save Strategy

Each row will be tested through controlled no-save investigation before any registry activation:

- Use only public unauthenticated URLs.
- Do not broad crawl.
- Capture final URL, status, content type, normalized length, normalized hash, quality label, shell/shallow/access-block status, noise/source-health risk, and whether evidence can safely be saved.
- Use the stable source_id proposals only in test configs and reports until activation gates pass.

## Evidence / Baseline Strategy

Only strong no-save passes may proceed to saved evidence:

1. save proof/evidence;
2. complete two repeat baseline runs;
3. verify stable normalized hash or safe non-noisy diff;
4. run mass-monitor dry-run;
5. require MONITOR_OK;
6. run/emulate Source Monitor, Evidence Trail, QA/Critic, Legal Language, Product Manager, and Code Architect gates.

## Demotion Strategy

If any row fails the activation-ready definition, it will not remain active. It will be:

- moved to `enabled:false` / `status:candidate` when useful but not proven;
- moved to remediation only if the source should remain transparent as a known technical work item;
- rejected/disabled if generic, duplicate, shallow, access-blocked, too noisy, or commercially weak.

Customer-facing coverage cards and source-family copy must not count unvalidated rows as Strong/Good coverage.

## Validator Plan

Create or update `tools/validate_no_unvalidated_active_sources.py` so it fails when a new active UAE source lacks:

- `source_id`;
- official URL;
- `proof_path`;
- `normalized_hash`;
- `baseline_runs_completed >= 2`;
- `last_monitor_status == MONITOR_OK`;
- legal-safe notes.

The validator must also block no-save-only rows, active rows without proof, and customer-facing claims of complete UAE coverage.

## Commit Policy

- Stage only files from this repair/universe task.
- Do not stage runtime junk, secrets, generated caches, or unrelated files.
- Do not commit unless validators and tests pass.
- If the eight-row repair passes but 1000-source mapping is not completed in the same commit, use a repair-specific commit message.

## What Will Not Be Claimed

- No complete UAE coverage claim.
- No legal advice.
- No guaranteed compliance.
- No perfect parsing.
- No "never miss updates".
- No regulator certification.
- No active status for unvalidated FTA/ADGM rows.
