# Current Source Discovery System Audit

## 1. Current Discovery Score

Current score: **7.0 / 10**.

StatuteProof has meaningful foundations: `discover-source`, Source Connection Strategy Engine, Auto DOM Investigator, adapter platform, strict Source Lab fields, and validators. The missing piece is a machine-readable endpoint discovery contract that can produce safe candidates from robots/sitemap/feed/DOM/network sources without activating them.

## 2. What Works Now

- `product/regradar/app/source_discovery.py` runs a 6-layer capability check.
- `product/regradar/app/source_connector/source_onboarding.py` orchestrates core extraction, deep URL probing, language fallback, API hints, and scoring.
- `product/regradar/app/dom_investigator.py` recommends content/listing/table/PDF/custom-element strategies from HTML.
- `product/regradar/app/adapters/adapter_platform.py` contains generic and source-specific adapter families.
- `source-lab` output separates no-save preview from evidence and activation semantics.
- Validators block fake source readiness claims and unsafe customer-facing wording.

## 3. What Is Missing

- `discover-source` currently returns a client-style connection report, not the required endpoint candidate map.
- JSON mode writes a report into `reports/`; discovery needs a no-write mode for validators and pipelines.
- No unified candidate schema for sitemap URLs, feeds, PDFs, same-domain links, tables, rulebooks, registers, and public JSON/XHR candidates.
- Network/XHR classification is not exposed as a deterministic helper that tests can mock.
- Candidate generator does not produce agent-gated work queue entries.
- Source Lab UI does not yet show discovery endpoint candidates.

## 4. Why Sources Still Fail

- Many regulator pages are JS-heavy, chrome-heavy, or listing-heavy.
- Submitted URLs are often navigation pages; useful endpoints may be sitemap URLs, PDF links, item detail pages, or public JSON endpoints.
- Generic extraction gets nav-shell content before a source-specific endpoint is found.
- High noise/source-health risk blocks activation even when text can be extracted.

## 5. Discovery Methods Missing Or Incomplete

- Robots.txt sitemap extraction as a first-class structured result.
- Sitemap index and urlset parser with `loc`, `lastmod`, and `changefreq`.
- Feed link discovery from HTML and RSS/Atom parsing.
- Same-domain candidate graph with max depth/max links.
- Endpoint candidate scoring and rejection reasons.
- Public JSON/XHR endpoint classification with content-type/status fields.
- Candidate generation with agent gate placeholders.

## 6. Adapter Gaps

The adapter catalog is broad, but discovery does not yet automatically pick the best adapter path from endpoint signals. SCA/DFSA/CBUAE failures indicate that endpoint discovery must precede adapter use.

## 7. Evidence / Baseline Gaps

Discovery must remain no-save. Evidence and baseline automation exists as policy/contract, but source activation must remain blocked until no-save, proof, repeat baseline, and agent gates pass.

## 8. UI Gaps

Source Lab shows DOM remediation results, but does not yet show discovery mode with sitemap/feed/API/PDF/listing candidates.

## 9. P0 / P1 / P2 Fixes

P0:

- Add structured Source Discovery Engine output.
- Add tests and validator for discovery fields and fake-claim blocking.
- Keep generated candidates inactive by default.

P1:

- Add candidate generator with agent-gate placeholders.
- Integrate DOM investigation into discovery result.
- Extend failure codes for discovery-required cases.

P2:

- Add Source Lab discovery UI mode.
- Add network/XHR live capture command path for scoped browser runs.

## 10. Exact Files To Change

- `product/regradar/app/source_discovery.py`
- `product/regradar/run.py`
- `product/regradar/app/source_intake.py`
- `product/regradar/tests/test_source_discovery_engine.py`
- `tools/validate_source_discovery_engine.py`
- `tools/validate_source_activation_pipeline.py`
- `product/regradar/web/src/components/app/SourceLabPage.jsx` if UI change is scoped.
- Required sprint docs.

