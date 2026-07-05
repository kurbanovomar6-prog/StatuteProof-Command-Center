# Four Weak UAE Families Upgrade Final Report

Date: 2026-06-21

## Summary

This pass improved three of four target families through real source and evidence work:

- ADGM/FSRA: `AE-adgm-fsra-guidance-policy` moved from candidate to fresh-alert after proof-backed repeat baseline and mass-monitor `MONITOR_OK`; canonical evidence and an exact alert link were created.
- DIFC: `AE-difc-legal-database` moved from evidence-library to fresh-alert after a corrected selector, proof-backed repeat baseline, and mass-monitor `MONITOR_OK`; canonical evidence and an exact alert link were created.
- SCA: `AE-sca-regulations-listing` moved from remediation to fresh-alert after proof-backed repeat baseline and mass-monitor `MONITOR_OK`; canonical evidence and an exact alert link were created.
- UAE FIU: held at 6.3/10. No distinct official circulars/notices endpoint was proven, so no circulars monitoring claim was added.

Customer delivery remains false. The new evidence is pending review and not customer-brief eligible.

## Scores

| Family | Starting score | Ending score | Verdict |
| --- | ---: | ---: | --- |
| ADGM/FSRA | 6.8 | 7.0 | Improved to selected-source pilot-ready with candidate caveats |
| DIFC | 6.5 | 7.0 | Improved to selected-source pilot-ready with legal database caveats |
| UAE FIU | 6.3 | 6.3 | Held; circulars still unproven |
| SCA | 5.8 | 6.5 | Improved, but not 7 because AML/CFT parser/noise review remains unresolved |

## Methods Attempted

- Repository source audit across `sources.json`, source runs, alert queue, evidence records, audit JSON/Markdown, and frontend source-quality data.
- No-save previews for official/public candidates.
- Proof-backed saved runs and repeat baseline checks where no-save was strong.
- Mass-monitor save-proof checks to confirm `MONITOR_OK`.
- Canonical evidence dry-run before write.
- Exact alert linkage only where `source_id + run_id` matched canonical evidence.
- Claim-safety review against complete coverage, FIU circulars, and SCA root portal overclaims.

## Unsafe Methods Rejected

- No bypassing access controls, login, CAPTCHA, WAF, robots, private portals, or paywalls.
- No source was activated from no-save only.
- No one-run-only source was activated.
- No parser noise was described as a regulatory change.
- No customer-delivery approval was added.

## Source IDs

### Added

- None. This pass changed existing source rows only.

### Changed

- `AE-adgm-fsra-guidance-policy`: candidate -> fresh_alert
- `AE-difc-legal-database`: evidence_library -> fresh_alert
- `AE-sca-regulations-listing`: remediation -> fresh_alert

### Held

- `AE-adgm-fsra-waivers`: held as candidate; current gates did not pass cleanly enough.
- `AE-adgm-ra-circulars`: held as candidate; latest source-run status/gate consistency was not clean enough.
- `AE-adgm-fsra-regulatory-alerts`: held/disabled candidate after NAV_SHELL/no reliable alert rows.
- `AE-uaefiu-circulars`: held as candidate; no distinct official circulars/notices endpoint proven.
- `AE-sca-aml-cft`: held for parser/noise review before material-change claims.

### Downgraded

- None.

## Proof And Evidence

| Source ID | Proof created | Repeat baseline | Canonical evidence | Alert linked | Review |
| --- | --- | --- | --- | --- | --- |
| `AE-adgm-fsra-guidance-policy` | yes | yes, 6/2 | `evr_AE-adgm-fsra-guidance-policy_intake-20260621T214439Z` | yes | pending |
| `AE-difc-legal-database` | yes | yes, 5/2 | `evr_AE-difc-legal-database_intake-20260621T214518Z` | yes | pending |
| `AE-sca-regulations-listing` | yes | yes, 5/2 | `evr_AE-sca-regulations-listing_intake-20260621T214120Z` | yes | pending |

## Source Truth After This Pass

- Enabled UAE source records: 246
- Fresh-alert eligible: 180
- Evidence-library only: 60
- Candidate: 4
- Remediation: 2
- Canonical evidence records: 28
- Verified monitoring digest alerts: 43
- Canonical-evidence-linked alerts: 13
- Customer delivery: false

## Claims Gate

Allowed:

- Selected ADGM/FSRA rulebook/guidance/policy/circular monitoring.
- Selected DIFC laws/data-protection/legal database/legal notice monitoring.
- Selected FIU publications/typologies/system guides.
- Selected SCA direct/regulations endpoints only.

Rejected:

- Complete UAE coverage.
- Complete ADGM/FSRA coverage.
- Complete DIFC legal database coverage.
- UAE FIU circulars monitored.
- SCA root portal monitoring.
- Full SCA coverage.
- Legal advice, guaranteed compliance, regulator certification, perfect parsing, never-miss updates, or all-source coverage.

## Apollo Readiness Impact

- ADGM/FSRA: safer for scoped selected-source pilots, with candidate caveats.
- DIFC: safer for scoped selected-source pilots, with Legal Database caveats.
- UAE FIU: unchanged; safe only with circulars caveat.
- SCA: somewhat stronger for selected direct endpoints, but still weak for SCA-heavy buyers.

Safe ICPs:

- ADGM/FSRA compliance teams open to selected-source pilots.
- DIFC firms that accept selected legal database/listing monitoring with caveats.
- MLRO/compliance teams where FIU is positioned as selected publications/typologies/system guides, not circulars.

Unsafe ICPs:

- Buyers requiring complete ADGM/FSRA coverage.
- Buyers requiring complete DIFC legal database coverage.
- Buyers requiring FIU circulars monitoring.
- Buyers requiring SCA root portal or broad securities-law coverage.

## Next Exact Tasks

- Next source task: resolve or formally hold `AE-adgm-fsra-waivers` and `AE-adgm-ra-circulars` with a source-specific selector/status consistency pass.
- Next evidence task: founder/operator review the three new pending evidence records and keep delivery blocked unless review and legal gates pass.
- Next sales task: update Apollo segmentation to pitch ADGM/FSRA and DIFC as selected-source pilots only; keep SCA/FIU caveats explicit.
