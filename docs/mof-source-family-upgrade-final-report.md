# MoF Source Family Upgrade Final Report

Date: 2026-06-21

## 1. Starting MoF Score

4.0/10.

## 2. Ending MoF Score

7.0/10.

This is a selected-source pilot readiness score, not complete MoF coverage.

## 3. Did MoF Reach 7?

Yes, narrowly and honestly.

Reason: four additional official MoF sources passed strong no-save, proof save,
repeat baseline, stable hash, mass-monitor dry-run `MONITOR_OK`, gated
activation, and canonical evidence generation. The score does not exceed 7
because new MoF records are pending human review and have no exact alert linkage
yet.

## 4. Exact Blockers To 8/10

- New MoF canonical evidence records remain pending review.
- No new MoF alert queue entries are linked to the new records yet.
- Budget Archive, Open Data Statistical Reports, DTAs, CbC, and public debt
  pages were held because they did not pass the same proof gates.
- MoF family is still selected-source only; broad MoF/tax coverage is unsafe.

## 5. Official URLs Inspected

- `https://mof.gov.ae/robots.txt`
- `https://mof.gov.ae/sitemap_index.xml`
- `https://mof.gov.ae/page-sitemap.xml`
- `https://mof.gov.ae/post-sitemap.xml`
- `https://mof.gov.ae/post-sitemap2.xml`
- `https://mof.gov.ae/en/public-finance/tax/top-up-tax/`
- `https://mof.gov.ae/en/public-finance/tax/corporate-tax-in-the-uae/`
- `https://mof.gov.ae/en/public-finance/international-relations/automatic-exchange-of-information-aeoi-fatca-crs/`
- `https://mof.gov.ae/en/public-finance/uae-financial-sustainability/uae-financial-framework/`
- `https://mof.gov.ae/en/open-data/statistical-reports/`
- `https://mof.gov.ae/en/public-finance/uae-federal-budget/uae-federal-budget-archive/`
- `https://mof.gov.ae/en/public-finance/international-relations/double-taxation-agreements-dtas/`
- `https://mof.gov.ae/en/public-finance/international-relations/country-by-country-reporting/`
- `https://mof.gov.ae/en/public-finance/public-debt/t-bonds/`
- `https://mof.gov.ae/en/public-finance/public-debt/t-sukuk/`
- `https://mof.gov.ae/en/public-finance/public-debt/retail-sukuk/`
- `https://mof.gov.ae/en/public-finance/international-relations/regional-and-international-partnerships-and-agreements/`
- `https://mof.gov.ae/en/open-data/open-data-publication-plan/open-data-publication-plan-2026/`

## 6. Repository Candidates Inspected

- `AE-uae-ministry-of-finance`
- `AE-mof-publications-and-releases`
- `AE-mof-financial-legislation`
- `AE-mof-esr`
- MoF rows in `product/regradar/config/uae_source_candidates.json`
- MoF rows in `product/regradar/config/uae_source_work_queue.json`
- MoF source runs in `product/regradar/data/source_runs/source_runs.jsonl`
- MoF canonical evidence under `product/regradar/evidence/uae-ministry-of-finance/`
- MoF alert queue entries in `product/regradar/data/alert_queue/`

## 7. Safe Methods Attempted

1. Current source row inspection.
2. Source run inspection.
3. Alert queue inspection.
4. Canonical evidence inspection.
5. Official robots review.
6. Official sitemap review.
7. Public search for official MoF URLs.
8. Bounded no-save tests on official URLs.
9. Proof save for strong-pass candidates.
10. Repeat baseline for strong-pass candidates.
11. Mass-monitor dry-run with no alerts.
12. Gated activation through `tools/uae50_apply_activation.py`.
13. Canonical evidence dry-run.
14. Canonical evidence write only after `would_create=4`.
15. Validator runs.

## 8. Unsafe Methods Rejected

- No source activation from no-save only.
- No source activation from one run.
- No fake `MONITOR_OK`.
- No broad crawl.
- No WAF/login/CAPTCHA/paywall bypass.
- No FTA source counted as MoF.
- No broad MoF, complete MoF, or complete tax claim.

## 9. Source IDs Added

- `AE-mof-top-up-tax`
- `AE-mof-corporate-tax-in-the-uae`
- `AE-mof-aeoi-fatca-crs`
- `AE-mof-uae-financial-framework`

## 10. Source IDs Changed

The four new source IDs were added to `product/regradar/sources.json` and
`product/regradar/config/uae_source_work_queue.json` through the gated
activation tool.

## 11. Source IDs Held

- `AE-mof-open-data-statistical-reports`
- `AE-mof-federal-budget-archive`
- `AE-mof-double-taxation-agreements-dtas`
- `AE-mof-country-by-country-reporting`
- `AE-mof-t-bonds`
- `AE-mof-t-sukuk`
- `AE-mof-retail-sukuk`
- `AE-mof-regional-international-partnerships-agreements`
- `AE-mof-open-data-publication-plan-2026`

## 12. Source IDs Downgraded

None.

## 13. Proof Created

Yes. Four new proof-backed sources were saved with two baseline runs each.

## 14. Repeat Baseline Completed

Yes. All four activated sources completed baseline 2/2 with stable normalized
hashes.

## 15. Fresh-Alert Source Created

Yes. Four new MoF fresh-alert sources were created.

## 16. Evidence-Library Source Created

No.

## 17. Canonical Evidence Created

Yes. Four new complete, hash-verifiable records:

- `evr_AE-mof-top-up-tax_intake-20260621T205440Z`
- `evr_AE-mof-corporate-tax-in-the-uae_intake-20260621T205506Z`
- `evr_AE-mof-aeoi-fatca-crs_intake-20260621T205905Z`
- `evr_AE-mof-uae-financial-framework_intake-20260621T205938Z`

## 18. Alert Linked

No. No matching new MoF alert queue item exists yet for these new baseline runs.
Future alert linkage must match exact `source_id` + `run_id`.

## 19. Parser / Adapter Changed

No code changes. Existing listing and PDF-listing adapters were used.

## 20. Tests Added

No new tests were added because parser/backend logic did not change.

## 21. Validators Run

Passed during the sprint or final validation:

- `python3 tools/validate_canonical_evidence_records.py`
- `python3 tools/generate_verified_monitoring_digest.py`
- `python3 tools/validate_verified_monitoring_digest.py`
- `python3 product/regradar/reports/validate_audit.py`
- Full final validation is recorded in the final assistant response.

## 22. Source Audit Changed

Yes.

Current truth after MoF activation was superseded by the later four-weak-family
pass. MoF family truth did not change in that later pass, but overall UAE source
truth is now:

- Enabled UAE source records: 246
- Fresh-alert eligible: 180
- Evidence-library only: 60
- Candidate: 4
- Remediation: 2
- MoF: 8 total, 7 fresh-alert, 1 evidence-library

## 23. Safe Claim After Sprint

Selected official MoF monitoring for publications/releases, financial
legislation, ESR, DMTT/top-up tax, corporate tax, AEOI/FATCA/CRS, and UAE
financial framework pages.

## 24. Forbidden Claim After Sprint

Complete MoF coverage, complete tax coverage, all MoF publications monitored,
all UAE financial legislation monitored, legal advice, guaranteed compliance,
perfect parsing, never-miss updates, or customer-delivered evidence-backed
briefs.

## 25. Apollo Readiness Impact

MoF can now be mentioned as a supporting selected-source layer for tax-policy
and federal finance conversations. It should not be the headline ICP unless the
prospect accepts selected-source scope and proof/review caveats.

## 26. ICPs Safe For MoF Positioning

- UAE finance/legal/compliance teams tracking selected MoF tax-policy pages.
- Founder-operators and CCOs who need selected federal finance-policy monitoring
  as part of a broader UAE compliance source map.
- Tax-policy-adjacent prospects when positioned as selected MoF monitoring, not
  complete tax coverage.

## 27. ICPs Unsafe For MoF Positioning

- Buyers needing complete MoF monitoring.
- Buyers needing full FTA/tax portal coverage.
- Buyers needing complete treaty, budget, public debt, open data, or every MoF
  publication category monitored.

## 28. Next Exact Source Task

Build a source-specific adapter for `AE-mof-federal-budget-archive` or
`AE-mof-open-data-statistical-reports`, then repeat no-save, proof, baseline,
mass-monitor, and activation gates.

## 29. Next Exact Evidence Task

Founder/operator review of the seven MoF canonical evidence records; keep
review decisions append-only and hash-bound.

## 30. Next Exact Sales Task

Create a scoped Apollo line: selected MoF fiscal/tax-policy monitoring is
available as part of a named-source pilot; complete MoF/tax coverage is not
claimed.
