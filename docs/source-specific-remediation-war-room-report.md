# Source-Specific Remediation War-Room Report

Date: 2026-06-15

## Summary

This sprint materially improved source-specific remediation for SCA and DFSA and validated the mass-monitoring safety runner. CBUAE remains blocked by access/source-health constraints and was not bypassed.

## Adapters / Gates Improved

- `sca_listing` now handles UAE SCA ASP.NET pages where content is wrapped in `form#aspnetForm`.
- `sca_listing` now supports `.aegov-card[aria-labelledby]` item cards and extracts `h1-h5` titles separately from `View Details` links.
- Listing dedupe now prefers richer rows with complete dates/context.
- Structured adapter output is no longer misclassified as nav-shell when an explicit item-level adapter returns multiple real items.
- Explicit adapters now receive provider-confidence credit in source quality scoring.
- The mass-monitoring runner no longer promotes `adapter_config.content_selector` into fetch-level `content_selector`, avoiding baseline/monitor extraction drift.
- Dry-run mass monitoring no longer mutates queue monitor state.

## Source Results

| Source | Result | Notes |
|---|---:|---|
| SCA circulars/rules/procedures | Improved to proof-backed baseline complete | `sca_listing`, 5 item-level cards, stable hash |
| DFSA financial crime MLRO letters | Improved to proof-backed baseline complete | `dfsa_notice_listing`, 139 listing/document items |
| DFSA AML rulebook module | Proof-backed baseline complete but held | Mass-monitor dry-run showed hash drift after timeout fallback |
| EOCN UN sanctions page | Still remediation | Table extraction works but quality remains too low |
| CBUAE regulations | Still remediation | Access blocking remains; no bypass attempted |

## Remaining Blockers

- DFSA AML rulebook needs a deterministic monitor extraction path before activation.
- SCA latest regulations and AML/CFT still need page-specific selectors/adapters.
- CBUAE needs official alternate endpoints or public document listings; 403/WAF must not be bypassed.
- EOCN table/listing quality needs better item semantics before evidence save.

