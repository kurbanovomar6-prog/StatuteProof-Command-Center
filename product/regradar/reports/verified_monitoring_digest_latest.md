# StatuteProof Verified Monitoring Digest

Generated: 2026-06-21T21:53:35Z

**Scope:** operator-only triage of saved alert queue entries. This is not a customer brief.

## Summary

- Alerts queued: 43
- Pending review: 43
- Linked to canonical evidence: 13
- Brief-input eligible after evidence gate: 1
- Review-ready, hold, or parser-review candidates: 43
- Alerts with parser/noise indicators: 33
- Clean likely-noise alerts: 0
- Source-health blockers: 0
- Historical disabled-source failures: 5
- Customer delivery allowed: 0

## Active Source Health Blockers

- None detected at the configured threshold.

## Historical / Disabled Source Failures

- AE-adgm-fsra-rules: 3 historical failed/quality-drop runs; registry_enabled=False; status=disabled_external_access; not counted as an active monitoring blocker.
- AE-difc-legislation: 3 historical failed/quality-drop runs; registry_enabled=False; status=disabled_navigation_only; not counted as an active monitoring blocker.
- AE-uae-e-laws-portal-ministry-of-justice: 14 historical failed/quality-drop runs; registry_enabled=False; status=unknown; not counted as an active monitoring blocker.
- AE-uae-federal-tax-authority-fta: 14 historical failed/quality-drop runs; registry_enabled=False; status=unknown; not counted as an active monitoring blocker.
- AE-uae-securities-and-commodities-authority-sca: 3 historical failed/quality-drop runs; registry_enabled=False; status=unknown; not counted as an active monitoring blocker.

## Review Queue Triage

- HOLD: AE-central-bank-of-the-uae (CBUAE) - 1 added, 0 removed, 7 changed chunks; 556 unchanged.. Reasons: missing_canonical_evidence_record_id, meaningful change detected by source diff. Evidence: not linked.
- HOLD: AE-dubai-financial-services-authority-dfsa (DFSA) - 2 added, 0 removed, 15 changed chunks; 11 unchanged.. Reasons: missing_canonical_evidence_record_id. Evidence: not linked.
- HOLD: AE-uae-ministry-of-finance (MoF/FTA) - 0 added, 0 removed, 452 changed chunks; 2409 unchanged.. Reasons: missing_canonical_evidence_record_id, large diff requires human review before interpretation. Evidence: not linked.
- HOLD: AE-uae-financial-intelligence-unit-uaefiu (UAE FIU) - 0 added, 0 removed, 1 changed chunks; 10 unchanged.. Reasons: missing_canonical_evidence_record_id. Evidence: not linked.
- HOLD: AE-uae-ministry-of-economy (MoE/DNFBP) - 0 added, 0 removed, 19 changed chunks; 1 unchanged.. Reasons: missing_canonical_evidence_record_id. Evidence: not linked.
- HOLD: AE-dubai-virtual-assets-regulatory-authority-vara (VARA) - 0 added, 0 removed, 299 changed chunks; 0 unchanged.. Reasons: missing_canonical_evidence_record_id, large diff requires human review before interpretation. Evidence: not linked.
- HOLD: AE-uae-legislation-portal (MoJ/Gazette) - 0 added, 0 removed, 3 changed chunks; 0 unchanged.. Reasons: canonical_evidence_not_brief_eligible, meaningful change detected by source diff. Evidence: evr_AE-uae-legislation-portal_AE-20260611T224414Z-2a59324c.
- HOLD: AE-uae-ministry-of-economy (MoE/DNFBP) - 0 added, 0 removed, 1 changed chunks; 14 unchanged.. Reasons: missing_canonical_evidence_record_id. Evidence: not linked.
- HOLD: AE-adgm-fsra-financial-crime-prevention (ADGM/FSRA) - 0 added, 0 removed, 46 changed chunks; 0 unchanged.. Reasons: canonical_evidence_not_brief_eligible. Evidence: evr_AE-adgm-fsra-financial-crime-prevention_intake-20260615T125638Z.
- HOLD: AE-adgm-fsra-rulebooks (ADGM/FSRA) - 11 added, 4 removed, 4 changed chunks; 7 unchanged.. Reasons: canonical_evidence_not_brief_eligible, meaningful change detected by source diff. Evidence: evr_AE-adgm-fsra-rulebooks_intake-20260615T130729Z.
- HOLD: AE-dfsa-aml-rulebook-module (DFSA) - 0 added, 0 removed, 25 changed chunks; 0 unchanged.. Reasons: missing_canonical_evidence_record_id. Evidence: not linked.
- HOLD: AE-uaefiu-typology-reports (UAE FIU) - 0 added, 5 removed, 0 changed chunks; 100 unchanged.. Reasons: missing_canonical_evidence_record_id, meaningful change detected by source diff. Evidence: not linked.
- HOLD: AE-dubai-financial-services-authority-dfsa (DFSA) - 0 added, 0 removed, 284 changed chunks; 0 unchanged.. Reasons: missing_canonical_evidence_record_id, large diff requires human review before interpretation. Evidence: not linked.
- HOLD: AE-sca-aml-cft (SCA) - 0 added, 0 removed, 153 changed chunks; 0 unchanged.. Reasons: missing_canonical_evidence_record_id, large diff requires human review before interpretation. Evidence: not linked.
- NEEDS_PARSER_REVIEW: AE-sca-aml-cft (SCA) - 0 added, 0 removed, 153 changed chunks; 0 unchanged.. Reasons: large diff requires human review before interpretation, normalized hash returned to an earlier baseline. Evidence: evr_AE-sca-aml-cft_intake-20260619T143025Z.
- HOLD: AE-cbuae-retail-payment-services-rulebook (CBUAE) - 0 added, 1 removed, 6 changed chunks; 15 unchanged.. Reasons: missing_canonical_evidence_record_id. Evidence: not linked.
- HOLD: AE-cbuae-exchange-business-regulation-doclist (CBUAE) - 5 added, 2 removed, 0 changed chunks; 103 unchanged.. Reasons: missing_canonical_evidence_record_id. Evidence: not linked.
- HOLD: AE-cbuae-model-management-standards-doclist (CBUAE) - 12 added, 3 removed, 0 changed chunks; 37 unchanged.. Reasons: missing_canonical_evidence_record_id. Evidence: not linked.
- HOLD: AE-cbuae-tbml-transshipment-guidance-doclist (CBUAE) - 4 added, 0 removed, 0 changed chunks; 226 unchanged.. Reasons: missing_canonical_evidence_record_id. Evidence: not linked.
- HOLD: AE-eocn-laws-regulations-en (EOCN/TFS) - 84 added, 0 removed, 20 changed chunks; 19 unchanged.. Reasons: missing_canonical_evidence_record_id. Evidence: not linked.
- HOLD: AE-uaefiu-typology-reports (UAE FIU) - 0 added, 1 removed, 0 changed chunks; 99 unchanged.. Reasons: canonical_evidence_not_brief_eligible, meaningful change detected by source diff. Evidence: evr_AE-uaefiu-typology-reports_intake-20260619T150224Z.
- HOLD: AE-uaefiu-publications-hub (UAE FIU) - 0 added, 4 removed, 159 changed chunks; 18 unchanged.. Reasons: missing_canonical_evidence_record_id, large diff requires human review before interpretation. Evidence: not linked.
- HOLD: AE-sca-circulars-rules-procedures (SCA) - 0 added, 0 removed, 1 changed chunks; 16 unchanged.. Reasons: canonical_evidence_not_brief_eligible. Evidence: evr_AE-sca-circulars-rules-procedures_intake-20260619T150551Z.
- HOLD: AE-vara-compliance-risk-rulebook-pdf (VARA) - 0 added, 0 removed, 815 changed chunks; 0 unchanged.. Reasons: missing_canonical_evidence_record_id, large diff requires human review before interpretation. Evidence: not linked.
- HOLD: AE-vara-technology-information-rulebook-pdf (VARA) - 0 added, 0 removed, 400 changed chunks; 0 unchanged.. Reasons: missing_canonical_evidence_record_id, large diff requires human review before interpretation. Evidence: not linked.

## Required Next Actions

- Link or generate canonical evidence for 30 alert queue entries before brief use.
- Founder review can start from 1 brief-input eligible alert(s), but customer delivery remains blocked.
- Keep 5 disabled or historical repeated-failure source(s) disclosed as replaced/remediation history; do not count them as active blockers.
- Generate an internal non-customer brief only after canonical evidence and human review gates pass.

## Boundary

Operator-only monitoring intelligence. Not legal advice, not customer delivery, and not evidence of complete UAE coverage.
