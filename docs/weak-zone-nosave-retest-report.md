# Weak-Zone No-Save Retest Report

Date: 2026-06-16

Primary weak-zone candidates tested: 20
Primary adapter attempts: 52
Primary strong no-save passes: 3 (AE-uaefiu-aml-cft-laws, AE-uaefiu-annual-reports, AE-uaefiu-publications-hub)
Alternate endpoint candidates tested: 5
Alternate strong no-save passes: 1 (AE-cbuae-rulebook-revision-updates)

## Activation Candidates From No-Save

- `AE-uaefiu-aml-cft-laws`: q=62, len=1283, hash=2943fe70bf015fa1bb89ce9c1e46771649624ad1c544278797df8cce9984ffff, adapter=listing, can_save=True
- `AE-uaefiu-publications-hub`: q=65, len=7489, hash=98c0b91f69ed9f971f0379783dd8ed50aca6cc6972f37af8e599b1de84b0736e, adapter=fiu_eocn_document_listing, can_save=True
- `AE-cbuae-rulebook-revision-updates`: q=65, len=2162, hash=f9591437d188e373a496c8799d19e0d94230785fc22c6cbd58a6ecd8afc79d52, adapter=cbuae_document_listing, can_save=True

## Held Despite No-Save

- `AE-uaefiu-annual-reports` passed no-save but produced the same normalized hash as `AE-uaefiu-publications-hub`; it remains held as a duplicate alias until a narrower annual-report endpoint is found.
- ADGM alternate pages, VARA pages, DFSA/DIFC listing pages, and CBUAE non-rulebook public paths remain remediation/blocked with exact failure codes in `docs/weak-zone-nosave-retest-report.json` and `docs/weak-zone-alternate-nosave-results.json`.
