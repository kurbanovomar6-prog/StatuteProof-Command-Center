# Parser Reference Comparison Report

Date: 2026-06-14

Scope: compare StatuteProof parser/source-intake architecture against local reference repos and GitHub discovery candidates.

## What StatuteProof Does Well

- Uses deterministic normalized-text hashing; no LLM in change detection.
- Blocks unsafe URLs before fetch: localhost, private IPs, file schemes, and credentials.
- Has requests-first and Playwright fallback with headless browser context cleanup.
- Supports explicit `wait_for_selector` and `content_selector`.
- Uses a provider cascade for HTML extraction and records provider metadata.
- Handles optional dependency absence safely in provider wrappers.
- Has PDF extraction provider wrappers for PyMuPDF, pdfplumber, and pypdf.
- Has quality scoring with penalties for nav shell, hash collision, selector timeout, shallow text, missing proof, and policy warnings.
- Separates no-save preview from evidence writes and baseline certification at the model level.
- Has Source Lab CLI/API/UI connected to real intake code.

## What It Lacks

- Customer-facing frontend still has stale `PASS`, `Validated`, `Active`, and `can_activate` mappings.
- Source count currently conflicts: `sources.json` says 13 enabled, 9 active, 4 remediation; some docs/UI say 10/3.
- Source Lab API names no-save success as `can_activate`, which is semantically too strong.
- No rendered screenshot or rendered HTML evidence path for Playwright runs.
- No WARC capture.
- No external timestamping.
- PDF providers exist, but Source Lab does not fetch linked/live PDF bytes as a first-class extraction mode.
- No robots/access-policy informational report.
- Limited metadata extraction: htmldate/courlan wrappers exist, but not fully surfaced in Source Lab evidence report.
- No OCR-needed detector for scanned PDFs.

## P0 Improvements

- Rename/add API fields: `can_save_for_validation`, `activation_readiness`, and `evidence_level`; keep `can_activate` only as backward-compatible alias if necessary and avoid customer-facing activation copy.
- Replace customer-facing raw `PASS`, `Validated`, `Active`, and `Ready` source-status labels with safer labels.
- Align readiness counts with registry truth unless live checks prove otherwise.
- Add `tools/validate_parser_quality.py`.
- Add `docs/parser-quality-gates.md`.
- Add parser/source-intake workflow and skill updates.
- Run DFSA live no-save Playwright checks.

## P1 Improvements

- Store rendered HTML and screenshot paths for Playwright evidence runs.
- Surface provider candidates and metadata extraction in API/UI.
- Add robots/access-policy informational field.
- Add PDF live bytes extraction path with shallow/OCR-needed detection.
- Add regression tests for API/UI status mapping.

## P2 Improvements

- WARC capture via `warcio` or browsertrix-style optional provider.
- OpenTimestamps for hash attestations.
- OCR pipeline for scanned PDFs.
- Source-specific adapters for hard regulator sites.
- 30-day source stability report.

## Too Heavy Now

- Scrapy/Crawlee/browsertrix migration.
- ArchiveBox-style full web archive runtime.
- OCRmyPDF as default dependency.
- Camelot/tabula PDF tables as default.
- Legal NLP or LLM-based source change decisions.

## Optional Providers To Keep Optional

- Crawl4AI/firecrawl-style web-to-markdown providers.
- WARC/OpenTimestamps.
- OCR/table extraction.
- Robots/access-policy parser.

## Recommended Code Changes

- Tighten `source_intake.STATUS_LABELS`.
- Add `activation_readiness` / `can_save_for_validation` fields in Source Lab API and CLI JSON.
- Update Source Lab and Sources UI labels.
- Add parser quality validator.
- Add focused tests for no-save vs evidence vs activation naming.

## Agent/Skill Use For Future Parser Tasks

- Source Monitor: source registry, fetch/extraction status, readiness verdict.
- Code Architect: API/CLI/provider design.
- Evidence Trail: proof paths, hashes, evidence level, baseline history.
- QA / Critic: blocks false confirmed/ready labels.
- Legal Language: customer-facing source status wording.
- Risk + Brief Pipeline: only after evidence exists.
- Prompt Injection Review: external repo/skill/doc ingestion.
- Verification Before Completion: before completion claims or commit.
