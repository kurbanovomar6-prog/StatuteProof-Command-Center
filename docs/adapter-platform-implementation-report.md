# Adapter Platform Implementation Report

Date: 2026-06-14

## 1. Executive Result

Implemented a small Source Lab-compatible adapter platform with three adapter families:

1. `custom_element`
2. `listing`
3. `table`

This improves the source-onboarding architecture, but it does not make 50 UAE sources working. Public source truth remains:

`13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation`

## 2. Files Changed

- `product/regradar/app/adapters/adapter_platform.py`
- `product/regradar/app/source_intake.py`
- `product/regradar/run.py`
- `product/regradar/app/api.py`
- `product/regradar/tests/test_adapter_platform.py`
- `tools/validate_uae_50_working_sources.py`
- `product/regradar/config/uae_source_work_queue.json`

## 3. Adapters Added

### Custom Element Adapter

Purpose:
- Extract ADGM-style custom tag content such as `adgm-page > span`.

Output:
- normalized text
- adapter family/name/version
- selector metadata
- noise/source-health risk hints

Live no-save smoke:
- ADGM financial crime page: passed no-save, preview-only, baseline required.
- ADGM rules/regulations page: passed no-save, preview-only, baseline required.

### Listing Adapter

Purpose:
- Extract official listing pages into stable item rows.

Capabilities:
- container selector
- item selector
- title/date/category/url selectors
- row hashes
- stable sorting
- boilerplate exclusion
- fallback when configured container is missing

Live no-save smoke:
- SCA latest regulations remains remediation. The adapter metadata was exposed, but item rows were not isolated and the Source Lab result stayed blocked due policy warnings.

### Table Adapter

Purpose:
- Serialize official table/register rows into stable normalized text.

Capabilities:
- table selector
- headers
- rows
- row hashes
- optional stable row sorting

Live no-save smoke:
- Not run in this sprint.

## 4. Source Lab / API Contract

Source Lab results can now expose:

- `adapter_used`
- `adapter_family`
- `adapter_name`
- `adapter_version`
- `extraction_strategy`
- `adapter_metadata`
- `adapter_warnings`

CLI now supports:

```bash
python3 run.py source-lab <url> --adapter-family listing --adapter-config-json '{"container_selector":"main"}'
```

The authenticated custom-source test API now accepts and returns adapter metadata. No-save results still cannot claim evidence or monitoring readiness.

## 5. Evidence Pipeline Impact

Evidence writing remains in the existing source-intake proof path.

Adapter metadata is recorded in:

- source-intake result
- provider report
- source run record fields when evidence is saved

No new evidence store was created. Proof validity still depends on normalized text, hashes, proof path, baseline runs, and certification status.

## 6. Tests Added

`product/regradar/tests/test_adapter_platform.py`

Tests cover:

- listing item extraction
- listing boilerplate exclusion
- listing fallback when configured container is missing
- table extraction and stable row sorting
- ADGM-like custom-element extraction
- Source Lab explicit adapter metadata
- no-save remains preview-only

TDD red/green evidence:

- First run failed because `app.adapters.adapter_platform` did not exist.
- Fallback test failed before implementing body/main fallback.
- Final focused adapter test run: `5 passed`.

## 7. Validator Upgrade

`tools/validate_uae_50_working_sources.py` now requires work queue adapter fields:

- `adapter_family`
- `adapter_name`
- `adapter_version`
- `adapter_config`
- `extraction_strategy`
- `last_adapter_test_at`
- `adapter_status`
- `adapter_failure_reason`
- `adapter_remediation_hint`

It also blocks activation-ready entries that lack required adapter metadata.

## 8. Backward Compatibility

- Generic extraction remains the fallback.
- Existing sources do not require adapter config.
- `sources.json` was not changed.
- Public source counts were not changed.
- No broad monitoring was run.

## 9. Known Limits

- Listing adapter is generic; SCA still needs a source-specific DOM/data investigation or SCA listing adapter.
- Table adapter is fixture-tested only.
- No PDF listing, rulebook module, screenshot, or WARC adapter was implemented in this sprint.
- Adapter success is not evidence confirmation unless saved proof artifacts exist.
- Adapter no-save success is not monitoring readiness.
