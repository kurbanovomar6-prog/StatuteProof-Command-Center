# MoJ / Gazette Repo Forensics

Date: 2026-06-21

## Verdict

PASS for one selected-source recovery path.

MoJ/Gazette was not empty: the repo already had an enabled remediation row for the UAE Legislation Portal, a disabled e-Laws row, historical proof-backed UAE Legislation Portal runs, and one pending alert. The old root/e-Laws blocker remains real, but a safer official listing path was found and activated separately.

## Source IDs Inspected

| Source ID | Current decision | Evidence |
| --- | --- | --- |
| `AE-uae-legislation-portal` | Held as remediation | Root portal remains noisy/access-risk; historical proof-backed `CHANGED` run exists at `AE-20260611T224414Z-2a59324c`; one pending alert now linked to canonical evidence. |
| `AE-uae-e-laws-portal-ministry-of-justice` | Held disabled/remediation | Existing source history says restricted/blocked; do not reactivate without safe access proof. |
| `AE-uae-legislation-legislations-listing-20260621` | Added as scoped fresh-alert | Official `/en/legislations` listing passed no-save, two proof-backed baseline runs, stable normalized hash, and mass-monitor dry-run `MONITOR_OK`. |

## Files Inspected

- `product/regradar/sources.json`
- `product/regradar/data/source_runs/source_runs.jsonl`
- `product/regradar/data/alert_queue/20260611T224847-AE-uae-legislation-portal-AE-20260-a261.json`
- `product/regradar/reports/source_signal_quality_audit.json`
- `product/regradar/reports/source_signal_quality_audit.md`
- `product/regradar/web/src/data/sourceQualityAudit.ts`
- `docs/source-family-readiness-scorecard.md`
- `product/regradar/config/uae_source_candidates.json`
- `product/regradar/config/uae_source_universe_candidates.json`
- `product/regradar/data/source_candidates.json`

## Commands Run

```bash
rg -n "moj|gazette|legislation|e-laws|elaws|uae legislation|official gazette|federal decree|cabinet resolution|ministerial resolution" .
python3 tools/uae50_batch_nosave.py --url https://www.uaelegislation.gov.ae/en/legislations --source-id AE-uae-legislation-list-nosave-20260621 --regulator UAE-Legislation --out /tmp/uae_legislation_list_nosave.json
python3 tools/uae50_activate.py --source-id AE-uae-legislation-legislations-listing-20260621 --url https://www.uaelegislation.gov.ae/en/legislations --name "UAE Legislation Platform - Legislations Listing" --jurisdiction AE --category legislation --adapter-family listing --adapter-name listing --adapter-config-json '{"container_selector":"main","content_selector":"main","item_selector":"article, li, tr, .card, .item, a[href]"}' --wait-for-selector main --content-selector main --fetch-method playwright --runs 2 --baseline-required 2
python3 product/regradar/run.py mass-monitor --queue /tmp/moj_gazette_mass_monitor_queue.json --source-id AE-uae-legislation-legislations-listing-20260621 --dry-run --no-alerts --json
python3 tools/generate_canonical_evidence.py --source-id AE-uae-legislation-legislations-listing-20260621 --run-id intake-20260621T181016Z --status FIRST_SEEN --limit 1 --write --report-path /tmp/moj_gazette_new_listing_write.md
python3 tools/generate_canonical_evidence.py --source-id AE-uae-legislation-portal --run-id AE-20260611T224414Z-2a59324c --status CHANGED --limit 1 --write --report-path /tmp/moj_uae_legislation_write.md
```

## Blockers Found

- `https://uaelegislation.gov.ae/en` and `/sitemap.xml` returned `HTTP 403` with Cloudflare headers via direct curl. Do not bypass.
- `https://www.moj.gov.ae/en/laws-and-legislation/latest-legislations-and-laws.aspx` no-save returned `NAV_SHELL_ONLY`.
- `https://www.moj.gov.ae/en/laws-and-legislation/legislative-framework-of-the-judicial-system-in-uae/main-legislations.aspx` was accessible but did not pass strong no-save; it is not a fresh-alert source.
- `https://uaelegislation.gov.ae/en/legislations/1990` was accessible but did not pass strong no-save; it is useful as reference context, not fresh-alert.

## Safe Alternative That Worked

`https://www.uaelegislation.gov.ae/en/legislations` worked as a selected official listing source:

- no-save strong pass
- two saved proof-backed runs
- normalized hash stable
- baseline 2/2
- mass-monitor dry-run `MONITOR_OK`
- canonical evidence generated

## Customer Claim Impact

Allowed:

- Selected UAE Legislation Platform listing monitoring.

Forbidden:

- Complete UAE legislation coverage.
- Complete Official Gazette coverage.
- Complete MoJ/e-Laws coverage.
- Legal advice or guaranteed compliance.

