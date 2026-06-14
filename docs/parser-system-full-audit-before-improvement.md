# Parser System Full Audit Before Improvement

Date: 2026-06-14

Scope: `product/regradar` parser/source-intake backend, Source Lab API/UI, source registry, tests, and relevant docs. No parser code was edited before this audit.

## Executive Scores

- Current parser score: **7.2/10**
- Current customer-facing readiness score: **5.8/10**

The parser is real: it has URL safety checks, Playwright fallback, source intake, provider metadata, quality scoring, certification state, evidence writes, Source Lab CLI/API, and tests. It is not yet a 10/10 source-intake operating system because customer-facing surfaces still contain stale status mappings, source-count claims conflict with `sources.json`, and live DFSA verification has not been completed.

## What Works

- `source_tester.validate_public_url()` blocks localhost, private IPs, non-http schemes, and credentials in URLs.
- `scraper.py` has requests-first fetch and Playwright fallback with context cleanup.
- `source_intake.py` exposes `run_source_intake()` with no-save default, optional evidence write, nav-shell detection, hash collision checks, quality score, evidence level, certification status, failure reason, and remediation hint.
- `source_quality.py` applies strict penalties for nav shell, hash collision, selector timeout, shallow content, missing proof, missing canonical URL, and policy warnings.
- `source_certification.py` separates `TEST_PASSED`, `BASELINE_PENDING`, and `MONITORING_CERTIFIED`.
- `providers/html_extraction.py` has a real cascade: selector/selectolax, trafilatura, readability, selectolax default, bs4 fallback.
- `providers/pdf_extraction.py` has PyMuPDF, pdfplumber, and pypdf fallbacks.
- `providers/optional_tools.py` safely degrades for htmldate, courlan, and deepdiff.
- `/api/custom-sources/test` is connected to real `run_source_intake(..., write_evidence=False)`.
- `run.py source-lab` exists and supports `--js`, `--wait-for-selector`, `--content-selector`, `--no-save`, and `--json`.
- Tests cover SSRF blocking, nav-shell detection, hash collision, no-save evidence, baseline requirement, shallow PDF quality, policy warnings, and provider metadata.

## What Is Still Weak

- `sources.json` currently has **13 enabled / 9 active / 4 remediation**, while recent public/app/docs language says **13 enabled / 10 confirmed / 3 remediation**. The fourth remediation source is `AE-difc-laws-and-regulations`.
- `STATUS_LABELS` in `source_intake.py` maps `CONFIRMED_ACCESSIBLE` to `Ready`, which is too broad for no-save preview.
- `/api/custom-sources/test` returns `can_activate = status == CONFIRMED_ACCESSIBLE`, but no-save tests should be framed as `can_save_for_validation`, not activation.
- `/api/custom-sources` saves a source after a second no-save intake check and sets `enabled: false`, but it does not write proof on save. Its message is honest, but the field naming can confuse activation.
- `SourceLabPage.jsx` uses `can_activate` as the save gate and shows successful preview with green treatment. It disables activation, but naming still implies activation.
- `SourcesPage.jsx` still maps raw `PASS`, `Validated`, and `Active` to accessible/confirmed in several helper maps. Those are customer-facing overclaim risks.
- `STATUTEPROOF_CONTEXT.md` is stale: it says this folder does not contain pipeline code, says 9 active sources, and lists DFSA as verified active.
- Evidence writes in `source_intake.py` update `evidence_level` after `certification` is built; returned certification may not reflect the post-write evidence level until run history is rebuilt.
- No WARC capture, rendered screenshot capture, external timestamping, or browser DOM evidence is currently part of core evidence output.
- PDF extraction providers exist, but live monitoring/source intake does not fetch and parse PDF bytes from linked PDFs as a first-class path.
- DFSA live verification is still pending; DFSA should remain remediation until real Playwright no-save checks prove meaningful, unique, non-nav-shell content.

## Required Questions

1. Source Lab UI connected to real endpoint? **Yes.** `SourceLabPage.jsx` posts to `/api/custom-sources/test`.
2. Provider cascade actually used? **Yes for HTML via `extract_best_text()` -> `best_html_extract()`.** PDF provider exists but is not fully wired into Source Lab URL fetch for live PDF bytes.
3. Evidence levels real? **Partly.** Preview and evidence-write paths exist; monitoring-certified evidence requires baseline run history. Current no-save remains `PREVIEW_ONLY`.
4. Source certification/activation readiness real? **Partly.** Certification model exists and baseline is enforced, but UI/API naming still uses `can_activate` too early.
5. Quality scoring strict? **Mostly yes.** It penalizes key failure modes. It needs stronger API/UI contract enforcement and maybe link-density/table metrics later.
6. Confirmed/evidence wording honest? **Mixed.** New Source Lab wording is mostly careful, but source count and `PASS`/`Validated` mappings remain risky.
7. DFSA pending live verification? **Yes.** Do not move DFSA out of remediation before live Playwright Source Lab evidence is reviewed.

## P0 Improvements

- Replace customer-facing `can_activate` semantics with `can_save_for_validation` / `activation_readiness` while keeping backward-compatible fields if needed.
- Change customer-facing labels from `Ready`, `PASS`, `Validated`, and `Active` where they imply unproven readiness.
- Fix source-count consistency to match canonical registry unless live verification changes it. Current registry says 13 enabled, 9 active/confirmed by registry status, 4 remediation.
- Add parser QA gate script checking required modules, endpoints, Source Lab fields, reference repo ignore rules, and forbidden customer-facing claims.
- Add workflow and skill upgrades for source-intake gates.
- Run DFSA live no-save checks and document exact outputs.

## P1 Improvements

- Make evidence-write return certification aligned with post-write evidence level.
- Add tests around API response naming and UI label mapping.
- Add optional rendered HTML/screenshot evidence fields after Playwright fetches.
- Add PDF URL/live bytes extraction path to Source Lab.
- Add table/link-density metrics and source-type confidence to quality score.

## P2 Improvements

- WARC evidence capture.
- OpenTimestamps integration.
- Source-specific adapters for hard regulator sites.
- OCR-needed detection for scanned PDFs.
- 30-day source history dashboard.

## Risks Before Customer Demo

- Source-count inconsistency can damage trust.
- DFSA and DIFC remediation sources must not appear ready.
- Source Lab green states can be misread as activation.
- Old `PASS`/`Validated` mappings in app source tables can overclaim.
- Evidence preview/sample screens must remain clearly labeled.

## Risks Before Customer-Facing Use

- No live baseline history for all sources.
- No external timestamping/WARC/screenshot evidence yet.
- Custom source save does not produce customer-visible evidence proof by itself.
- Multi-tenant custom source storage and authorization need hardening before real customer activation.
- PDF extraction is not fully exercised end-to-end in live monitoring.
