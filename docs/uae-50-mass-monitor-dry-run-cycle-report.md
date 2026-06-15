# UAE 50 Mass Monitor Dry-Run Cycle Report

Date: 2026-06-15

## Final Dry-Run Result

Command:

```bash
python3 product/regradar/run.py mass-monitor --activation-ready-only --dry-run --no-alerts --limit 50 --json
```

Final result:

- Processed: 6 activation-ready queue sources.
- `MONITOR_OK`: 6.
- `change_detected`: 0.
- Evidence written: 0.
- Alerts sent: 0.
- Unsafe states skipped: 8.
- `sources.json` changed by runner: false.

## MONITOR_OK Sources

1. `AE-adgm-fsra-financial-crime-prevention`
2. `AE-adgm-fsra-rulebooks`
3. `AE-adgm-fsra-consultations`
4. `AE-sca-circulars-rules-procedures`
5. `AE-dfsa-financial-crime-mlro-letters`
6. `AE-dfsa-aml-rulebook-module`

## Runner Fix

The dry-run initially exposed selector-path drift:

- DFSA AML needed static selector promotion into fetch.
- ADGM custom elements must not be fetch-restricted because the custom-element adapter needs the full DOM.

The runner now promotes adapter selectors only for `static_html` and `playwright_selector`, and leaves `custom_element` selector handling inside the adapter.
