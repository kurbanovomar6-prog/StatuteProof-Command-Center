# Current Adapter System Audit

Date: 2026-06-14

## 1. Verdict

Current adapter score: 5.8/10.

The project has useful extraction pieces, but not yet a coherent source-adapter platform for fast, safe UAE source onboarding. The existing adapter registry is mainly a legacy production-pipeline hook for a few non-UAE sources. The Source Lab / source intake path, which is where new official UAE sources are tested, does not currently use adapter families, adapter result metadata, noise scoring, or source-health scoring.

This is the central blocker to reaching a professional 50-source pack. Adding more URLs without a richer adapter platform would only create more remediation rows.

## 2. What Works

- `product/regradar/app/source_intake.py` has strong safety gates for public URL validation, nav-shell detection, hash collision checks, no-save vs save behavior, evidence level, and activation readiness.
- `product/regradar/app/extractors.py` already has a provider cascade with BeautifulSoup baseline and optional trafilatura/readability/Crawl4AI.
- `product/regradar/app/scraper.py` supports requests plus Playwright fallback, `wait_for_selector`, and `content_selector`.
- `product/regradar/app/source_quality.py` and `product/regradar/app/source_certification.py` keep quality and evidence readiness separate from extraction success.
- `product/regradar/app/adapters/uae_cbuae_rulebook.py` and `product/regradar/app/adapters/uae_fsra_circulars.py` contain useful prototype item extraction ideas, while correctly warning that they are not production-registered.
- `product/regradar/config/uae_source_work_queue.json` already records agent gates and activation decisions for the 50-source target.

## 3. What Is Missing

- Source Lab cannot explicitly select a first-class adapter family such as listing, table, custom element, rulebook module, or PDF listing.
- Adapter outputs are not standardized. Existing `SourceAdapter.fetch_content()` returns only text, not structured metadata, item counts, noise/source-health hints, failure reasons, or adapter version.
- Existing adapter registry is URL-matched and not wired into `run_source_intake()`.
- There is no reusable listing adapter for SCA/ADGM/CBUAE item pages.
- There is no reusable table adapter for official register/table pages.
- There is no reusable custom-element adapter for ADGM-style rendered/custom tag pages.
- Source Lab CLI/API does not expose `adapter_used`, `adapter_family`, `adapter_version`, or `extraction_strategy`.
- Work queue entries do not yet consistently store adapter family/config/status fields.
- Unit tests cover source-intake quality gates well, but not adapter-family behavior.

## 4. Adapter Gaps By Source Type

| Source type | Current status | Gap |
|---|---:|---|
| Static HTML content | Partial | Generic extraction works, but no adapter metadata or boilerplate policy per source. |
| Playwright selector pages | Partial | Selector support exists, but selector failures do not carry adapter-family diagnostics. |
| Custom element pages | Missing | ADGM pages often extract from custom tags; this needs a stable adapter instead of ad hoc selectors. |
| Listing pages | Missing | SCA, ADGM, CBUAE, DFSA notices need item-level extraction, row hashes, and noise filtering. |
| Tables/registers | Missing | Public registers and tables need deterministic row serialization. |
| PDF pages | Partial | PDF extraction exists elsewhere, but Source Lab needs better shallow/OCR-needed failure mapping. |
| Rulebooks/modules | Partial | CBUAE prototype exists, but no general module adapter with stable module-level hashes. |
| Screenshot/WARC evidence | Roadmap | Useful future layer, not required for this scoped implementation. |

## 5. Why The Current System Cannot Reach 50 Working Sources Yet

A source counts as working only after officialness, technical extraction, proof artifacts, repeat baseline, source-health/noise review, and agent gates. The current parser can test many pages, but many official UAE sources are listings, custom-element rendered pages, tables, or rulebook indexes. Generic extraction often returns shell text, duplicate boilerplate, or unstable listing chrome.

The system needs adapter families that convert those page shapes into stable normalized regulatory records before evidence/baseline gates can honestly pass.

## 6. P0 / P1 / P2 Adapter Needs

P0:
- Add a Source Lab-compatible adapter result schema.
- Add listing, table, and custom-element adapter families.
- Expose adapter metadata in Source Lab JSON.
- Add unit tests for adapter extraction and no false activation.
- Preserve existing no-save/evidence/baseline gates.

P1:
- Add source-specific config for high-priority UAE candidates in `uae_source_work_queue.json`.
- Add SCA listing and ADGM custom-element recommended configs.
- Add validator checks that activation-ready sources must have adapter/gate metadata when adapter extraction is used.

P2:
- Add rulebook/module adapter.
- Add PDF listing adapter.
- Add screenshot/rendered HTML evidence enrichment.
- Add WARC/archive evidence layer if the evidence policy later requires it.

## 7. Code Files To Change

- `product/regradar/app/adapters/adapter_platform.py` new small adapter-family implementation.
- `product/regradar/app/source_intake.py` to optionally run explicit adapter extraction before generic extraction.
- `product/regradar/run.py` to expose adapter metadata and optional adapter CLI config.
- `product/regradar/app/api.py` to expose adapter metadata in custom-source test responses.
- `product/regradar/tests/test_adapter_platform.py` new adapter unit tests.
- `tools/validate_uae_50_working_sources.py` to understand adapter fields.
- `product/regradar/config/uae_source_work_queue.json` to record adapter family/config/status fields.

## 8. Tests To Add

- Listing adapter extracts item titles.
- Listing adapter ignores nav/footer/search controls.
- Table adapter extracts headers and rows.
- Table adapter can stable-sort rows when configured.
- Custom-element adapter extracts ADGM-like text.
- Source intake result exposes adapter metadata when an explicit adapter is configured.
- No-save adapter result remains preview-only.
- One saved run still cannot claim monitoring-ready.
- Work queue validator blocks fake 50-source claims.

## 9. Risk To Evidence Pipeline

Risk is moderate if adapter extraction replaces normalized text too broadly. The safer design is explicit adapter use only when a source config asks for it. Generic extraction remains the fallback. Evidence writing continues through the existing `_write_intake_evidence()` path and must include adapter metadata only as supplemental proof context, not as a separate evidence pipeline.

## 10. Agent Gate Summary

- Source Monitor: HOLD until adapter output proves meaningful regulatory content rather than nav/listing chrome.
- Evidence Trail: HOLD until proof paths and baseline counts exist.
- QA / Critic: HOLD for any source with high noise, high source-health risk, nav shell, or duplicate hash.
- Legal Language: PASS only for candidate/readiness wording; block “validated,” “certified,” or “50 working sources” until validators pass.
- Code Architect: PASS for a small explicit adapter layer; block a broad parser rewrite.
- Product Manager: PASS for adapters that improve MLRO-relevant official source onboarding; block vanity source-count padding.
