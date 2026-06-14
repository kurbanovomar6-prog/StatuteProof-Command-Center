# UAE 50 Extraction Strategy Report

## Executive Result

No broad parser rewrite was done. One scoped Source Lab contract mapping fix was implemented after repeat baselines exposed an inconsistency: aggregate certification could reach `MONITORING_CERTIFIED` / `CERTIFIED_EVIDENCE` while `can_activate_monitoring` remained false because the contract preferred the single-run `FULL_EVIDENCE` level.

Files changed:

- `product/regradar/app/source_intake.py`
- `product/regradar/tests/test_source_intake.py`

## Adapters Added Or Changed

No new listing/table/PDF adapter was added in this sprint. The project still needs targeted adapters before a 50-source default pack is realistic.

## Why The Contract Fix Was Needed

Three repeat saved baselines completed successfully. The certification aggregate correctly recorded two proof-backed runs and stable hashes, but the Source Lab activation contract did not expose certified evidence. This would confuse frontend/API users and future validators.

## Deferred Extraction Strategies

| strategy | targets | notes |
| --- | --- | --- |
| listing_adapter | SCA latest regulations, DFSA notices, CBUAE/FIU publications | Extract item title/date/link, ignore pagination and chrome. |
| table_adapter | SCA regulations/decisions and future official registers | Extract stable rows/cells and normalize ordering. |
| pdf_listing_adapter | VARA/CBUAE/ADGM official document pages | Extract PDF title, URL, date and optionally scoped PDF text. |
| playwright_selector | ADGM custom elements, SCA ASP.NET listings, DFSA pages | Use exact wait/content selector and selector timeout failure mapping. |

## Code Architect Review

Pass for the Source Lab contract fix: it is small, tested, and preserves the evidence pipeline.

Hold for broad 50-source extraction: source-specific adapters are still required and must be implemented one regulator group at a time.

## Source Monitor Review

Two ADGM candidates are now activation-ready candidates after two saved baselines. SCA latest regulations remains remediation because high source-health/listing risk is unresolved.
