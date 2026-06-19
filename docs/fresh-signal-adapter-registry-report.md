# Fresh Signal Adapter Registry Report

## Registry Truth

`product/regradar/app/adapters/registry.py` previously registered only Russia-oriented adapters:

- `CBRAdapter`
- `MinfinAdapter`
- `RosfinmonitoringAdapter`

Two UAE modules existed as unregistered manual-validation prototypes:

- `uae_cbuae_rulebook.py`
- `uae_fsra_circulars.py`

## Change Implemented

Added production `SourceAdapter` wrappers:

- `CBUAERulebookAdapter`
- `FSRACircularsAdapter`

Registered both in `_ADAPTERS` before the legacy Russian adapters so production pipeline dispatch can select them before falling back to generic scraping.

## CBUAE Adapter

Class: `CBUAERulebookAdapter`

Handles:

- `rulebook.centralbank.ae` rulebook module pages.
- `rulebook.centralbank.ae/en/view-revision-updates...` revision listing pages.

Behavior:

- Uses existing structured revision-row extractor for revision pages.
- Uses official page fetch + parser extraction for module pages.
- Returns `None` when content is too shallow, letting the pipeline fall back to generic scraping rather than faking success.

## ADGM/FSRA Adapter

Class: `FSRACircularsAdapter`

Handles:

- ADGM supervision circulars.
- ADGM regulatory-alert/guidance/consultation-like listing URLs.
- Source entries explicitly configured as `adgm_fsra_listing`.

Behavior:

- Uses existing structured circular-row extractor for supervision circulars.
- Uses official page fetch + parser extraction for other ADGM/FSRA listing pages.
- Returns `None` when extraction is too shallow.

## Limitations

Adapter registration alone does not prove monitoring readiness. Each source still requires no-save extraction, proof/evidence, repeat baseline, and `MONITOR_OK` before it can be counted as `fresh_alert`.

## Next Steps

- Add validator coverage for adapter registration.
- Run controlled source tests for CBUAE and ADGM/FSRA sources.
- Promote only proof-backed `MONITOR_OK` sources to `fresh_alert`.
