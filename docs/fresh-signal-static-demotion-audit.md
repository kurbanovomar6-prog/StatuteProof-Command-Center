# Fresh Signal Static Demotion Audit

Date: 2026-06-19

## Purpose

This audit separates sources that can produce future fresh regulatory signal from official/static sources that are useful as evidence references but should not generate customer update alerts.

## Source Modes After This Pass

From `product/regradar/sources.json`:

- `fresh_alert`: 156
- `evidence_library`: 61
- `candidate`: 6
- `remediation`: 3

## Static / Evidence-Library Classes

The following classes must remain `evidence_library` and must not count toward Strong Fresh Signal:

- old individual DFSA notice/news detail pages;
- old DIFC whats-on/news/detail pages;
- old individual ADGM announcement pages;
- generic regulator homepages;
- static/specific historical consultation pages that do not represent a live listing;
- duplicate or low-future-change pages where a parent listing is the actual fresh signal.

## Specific Decisions In This Pass

- DFSA individual notice pages remain evidence-library.
- DIFC whats-on/news detail pages remain evidence-library.
- ADGM individual announcement pages remain evidence-library.
- `AE-dfsa-consultation-paper-165` was left as evidence-library only even though it passed technical extraction, because it is a specific historical consultation paper rather than a future-update listing.
- CBUAE homepage remains evidence-library.
- CBUAE generic regulations portal remains candidate/held after access-risk classification; 25 CBUAE rulebook/regulatory pages are the fresh-alert layer.
- VARA homepage remains evidence-library; VARA enforcement remains held after nav-shell result.
- MoF generic homepage remains evidence-library.

## Customer Claim Rule

Only sources with all of the following count in fresh-monitoring claims:

- `monitoring_mode: fresh_alert`
- `alert_eligible: true`
- `last_monitor_status: MONITOR_OK`
- `proof_path`
- `normalized_text_path`
- `normalized_hash`
- `baseline_runs_completed >= 2`
- `recommended_check_frequency: daily`

Evidence-library sources may support audit packs and source review, but they are not customer update-alert sources.
