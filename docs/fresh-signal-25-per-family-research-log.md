# Fresh Signal 25 Per Family Research Log

Date: 2026-06-19

## Scope

This pass prioritized existing official candidates and remediation rows already present in the source registry, then validated them through proof, repeat baseline, and mass-monitor dry-run. It did not pretend that every family has 25 official daily-checkable endpoints.

## Existing Candidates Tested

Families tested in this pass:

- CBUAE
- VARA
- ADGM/FSRA
- DFSA
- DIFC
- UAE FIU
- EOCN / sanctions / TFS
- SCA

## Official/Public Rationale

All tested sources were already in the official UAE source registry and were limited to official or officially linked public regulator/government domains:

- `rulebook.centralbank.ae`
- `rulebooks.vara.ae`
- `dfsa.ae`
- `dfsaen.thomsonreuters.com`
- `difc.com`
- `adgm.com`
- `uaefiu.gov.ae`
- `eocn.gov.ae`
- `sca.gov.ae`

No private portal, login, CAPTCHA, paywall, private API, or customer data source was used.

## Source-Family Exhaustion Status

This pass did not complete full external discovery for every weak family. Remaining hard gaps require additional official-source discovery and adapter work:

- VARA: needs 2 more official fresh-alert endpoints or a fixed enforcement/admin-order listing adapter.
- EOCN/TFS: needs 3 more sources for the broad TFS family target; direct EOCN public universe may be smaller than 25.
- DFSA: needs 13 more fresh-alert listing/rulebook/enforcement/consultation endpoints; static notice pages cannot be counted.
- DIFC: needs 15 more fresh-alert legal/data-protection/consultation/publication endpoints; static whats-on pages cannot be counted.
- ADGM/FSRA: needs 17 more fresh-alert endpoints; quality drops and nav-shell failures need adapter refinement.
- UAE FIU: needs 20 more fresh-alert endpoints; public FIU universe may be smaller than 25 and goAML is forbidden.
- SCA: needs 21 more fresh-alert endpoints; one regulations listing still failed nav-shell.
- MoJ/Gazette: still blocked/remediation; WAF/access-safe alternatives needed.
- MoF: generic homepage only; specific decision/news/document endpoints still need discovery.

## Conclusion

The sprint materially improved fresh-signal coverage by activating or confirming 60 sources, but the official-source universe still does not prove 25 daily-checkable fresh-alert endpoints for every family. The correct next task is targeted discovery plus source-specific adapters for the remaining weak families.
