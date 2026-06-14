# Source-Specific Remediation Layer Report

Date: 2026-06-15

## Summary

Expanded the source-specific remediation layer without activating any new sources.

## Regulator Strategies

### SCA

Existing `sca_listing` remains the intended strategy for rendered listing rows/detail links.

Live result this sprint: still not activation-ready. SCA targets returned `ACCESS_BLOCKED`, `SHALLOW_CONTENT`, or `NAV_SHELL_ONLY` under strict no-save checks.

### DFSA

Existing `dfsa_rulebook` remains for Thomson Reuters rulebook module listings.

New `dfsa_notice_listing` was added for AML/MLRO notices and enforcement/regulatory action listing pages.

Live result this sprint: strict no-save still blocked by access/source-health and shallow extraction outcomes.

### CBUAE

Existing `cbuae_document_listing` remains for regulation/publication document pages.

Live result this sprint: CBUAE pages remained blocked or nav-shell under strict no-save checks.

### ADGM/FSRA

New `adgm_fsra_listing` was added for guidance/rules/consultation-style links.

Existing `custom_element` remains useful for ADGM custom element content where selectors are known.

Live result this sprint: ADGM targets returned nav-shell under current configs.

### VARA

Existing `vara_pdf_listing` remains for rulebook/PDF listing pages and not-found shell detection.

Live result this sprint: target remained nav-shell.

### UAE FIU/EOCN

Existing `fiu_eocn_document_listing` remains for publication/document listings.

Live result this sprint: FIU publications target remained blocked/nav-shell.

## Source-Health Risk

The main live risk remains high:

- regulator pages are JS/chrome-heavy;
- current selectors still miss item-level DOM;
- some pages return access-blocked or shell content after rendering;
- detail/API endpoints likely need browser DOM investigation per regulator.

## Activation Decision

No source should be activated from this sprint.
