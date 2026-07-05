# StatuteProof Alert Triage To 8/10 Readiness

Date: 2026-06-21

## Purpose

This document records the current alert queue triage required before StatuteProof can honestly claim 8/10 internal pilot-delivery readiness. It is an operator artifact, not a customer brief.

## Current Digest Snapshot

Commands:

```bash
python3 tools/generate_verified_monitoring_digest.py
python3 tools/validate_verified_monitoring_digest.py
```

Current facts:

- Alerts queued: 39
- Pending review: 39
- Canonical evidence linked: 9
- Brief-input eligible: 1
- Missing evidence links: 30
- Alerts with parser/noise indicators: 30
- Active source-health blockers: 0
- Historical disabled-source failures: 5
- Customer delivery allowed: 0

## One Internal Brief Candidate

### AE-sca-aml-cft

- Family: SCA
- Company use case: securities, capital markets, AML/CFT teams
- Evidence record: `evr_AE-sca-aml-cft_intake-20260619T143025Z`
- Brief-input eligible: yes
- Triage status: `NEEDS_PARSER_REVIEW`
- Diff summary: `0 added, 0 removed, 153 changed chunks; 0 unchanged.`
- Review reasons:
  - large diff requires human review before interpretation;
  - normalized hash returned to an earlier baseline.
- Noise indicators:
  - possible full-page or PDF reflow;
  - possible locale/template switch;
  - transient extraction/source-state candidate.
- Current safe use: internal non-customer gated-cycle proof only.
- Customer use: blocked.

Why this is useful but not customer-ready:

- It proves the source -> canonical evidence -> review -> alert -> brief draft -> legal scan -> blocked delivery path can run.
- It does not prove the SCA change is a meaningful regulatory change.
- It does not prove founder approval.

## Top 5 Alert Candidates For Founder Review

These are not customer-ready. They are prioritized because their family/use case is commercially relevant and the diff has at least some high-signal characteristics, but they still need canonical evidence links and human review.

1. `AE-adgm-ra-circulars`
   - Family: ADGM/FSRA
   - Diff: `71 added, 0 removed, 319 changed chunks; 34 unchanged.`
   - Blocker: missing canonical evidence link.
   - Why review: ADGM circulars can matter to FSRA-regulated firms.

2. `AE-adgm-fsra-guidance-policy`
   - Family: ADGM/FSRA
   - Diff: `276 added, 0 removed, 1 changed chunks; 64 unchanged.`
   - Blocker: missing canonical evidence link.
   - Why review: guidance/policy content can affect regulated activity review.

3. `AE-adgm-fsra-rulebooks`
   - Family: ADGM/FSRA
   - Diff: `11 added, 4 removed, 4 changed chunks; 7 unchanged.`
   - Evidence: `evr_AE-adgm-fsra-rulebooks_intake-20260615T130729Z`
   - Blocker: canonical evidence exists but remains pending review, so it is
     not brief-input eligible.
   - Why review: rulebook changes are high relevance if extraction is real.

4. `AE-dfsa-financial-crime-mlro-letters`
   - Family: DFSA
   - Diff: `17 added, 0 removed, 0 changed chunks; 441 unchanged.`
   - Evidence: `evr_AE-dfsa-financial-crime-mlro-letters_intake-20260619T151120Z`
   - Blocker: canonical evidence exists but remains pending review, so it is
     not brief-input eligible.
   - Why review: MLRO/financial crime content maps directly to compliance buyer pain.

5. `AE-uaefiu-typology-reports`
   - Family: UAE FIU
   - Diff: `0 added, 5 removed, 0 changed chunks; 100 unchanged.`
   - Evidence: `evr_AE-uaefiu-typology-reports_intake-20260619T150224Z`
   - Blocker: canonical evidence exists but remains pending review, so it is not brief-input eligible.
   - Why review: typology report list changes can matter to AML teams, but the removal must be verified as real and not parser/source-state noise before any claim.

## Newly Evidence-Linked Alerts This Pass

These alerts now have exact canonical evidence links, but they remain pending
review and blocked from customer brief use.

| Family | Source ID | Evidence record |
| --- | --- | --- |
| ADGM/FSRA | `AE-adgm-fsra-financial-crime-prevention` | `evr_AE-adgm-fsra-financial-crime-prevention_intake-20260615T125638Z` |
| ADGM/FSRA | `AE-adgm-fsra-rulebooks` | `evr_AE-adgm-fsra-rulebooks_intake-20260615T130729Z` |
| DIFC | `AE-difc-data-protection-regulation-10` | `evr_AE-difc-data-protection-regulation-10_intake-20260619T151736Z` |
| SCA | `AE-sca-circulars-rules-procedures` | `evr_AE-sca-circulars-rules-procedures_intake-20260619T150551Z` |
| DFSA | `AE-dfsa-consultation-current` | `evr_AE-dfsa-consultation-current_intake-20260619T151155Z` |
| DFSA | `AE-dfsa-what-we-do-enforcement-1a837c50` | `evr_AE-dfsa-what-we-do-enforcement-1a837c50_intake-20260619T164008Z` |

## Top Parser/Noise Candidates

These should not become customer alerts without parser/source review.

1. `AE-sca-aml-cft`
   - `153 changed chunks; 0 unchanged`
   - Flags: possible page/PDF reflow, template switch, transient hash revert.

2. `AE-uae-ministry-of-finance`
   - `452 changed chunks; 2409 unchanged`
   - Flags: large portal reflow; likely mixed news/homepage content.

3. `AE-uaefiu-publications-hub`
   - `159 changed chunks; 18 unchanged`
   - Flags: boilerplate/navigation/widget candidate.

4. `AE-dubai-virtual-assets-regulatory-authority-vara`
   - `299 changed chunks; 0 unchanged`
   - Flags: possible full-page/PDF reflow and template switch.

5. `AE-vara-compliance-risk-rulebook-pdf`
   - `815 changed chunks; 0 unchanged`
   - Flags: likely full PDF reparse; needs PDF-level review before interpreting content.

## Evidence Link Requirements

Before any alert enters a customer-facing or pilot brief path:

1. The alert must reference the exact matching canonical `evidence_record_id`.
2. The canonical evidence record must validate.
3. The append-only review hash must match the current evidence record hash.
4. The latest review must be `approved` or the record must be explicitly `not_required`.
5. The alert must remain `delivery_approved=false` until a separate delivery gate is passed.
6. Legal scan must pass.
7. Any parser/noise indicators must be reviewed and either cleared or documented.

## Source Family Caveats

- SCA: selected direct endpoints exist; old root SCA portal failure remains historical/remediation history and full SCA coverage is still unsafe.
- ADGM/FSRA: selected active sources exist; old `AE-adgm-fsra-rules` failure is disabled/replaced history, not an active blocker.
- DIFC: selected active `difc.com` sources exist; old `difc.ae` legislation route remains disabled navigation-only history.
- FTA: selected direct PDFs are monitored; old root portal/listing failure remains historical/remediation history.
- MoJ/Gazette: e-Laws portal remains a disclosed gap/remediation area.

## Current 8/10 Decision

The alert queue now supports a reproducible internal gated-cycle proof, but the queue is not customer-ready.

Current blockers to full 8/10:

- Founder/operator approval is still not proven; current SCA approval is audit/test context.
- 30 alerts lack canonical evidence links.
- 30 alerts have parser/noise indicators.
- 0 active source-health blockers remain, but 5 disabled/historical source failures must stay disclosed as replacement/remediation history.
- No real customer or design partner has reviewed a brief.
