# SAMPLE / FAKE Source Spec

This file is SAMPLE / FAKE only. It is not a real regulatory update, real lead, real customer message, or verified source result.

## Verification Status

VERIFY BEFORE PRODUCTION.
This example uses `example.invalid` only.
It must not be copied into production monitoring without replacing every SAMPLE / FAKE value with a manually verified official source.

## Source Identity

source_id: sample_fake_vara_publications_listing
regulator: SAMPLE / FAKE VARA-style regulator context
official_url: https://example.invalid/sample-fake-vara-publications
fetch_method: HTTP GET against static SAMPLE / FAKE HTML fixture
owner_agent: 06 Source Monitor Agent

## Selectors

primary_content_selector: main
document_list_selector: .sample-publication-list
title_selector: .sample-publication-title
date_selector: .sample-publication-date
link_selector: .sample-publication-link
exclude_selectors:
- nav
- footer
- script
- style
- .cookie-banner

## Normalization Rules

- Keep publication title, date, link text, and visible summary.
- Remove navigation, footer, script, style, cookie banner, and duplicate layout text.
- Normalize whitespace to single spaces inside lines.
- Preserve one line per publication item.
- Do not infer missing dates or categories.
- Do not translate or summarize source text during normalization.

## Quality Rules

expected_min_length: 1200 characters
quality_drop_threshold: 35 percent decrease from previous normalized text length
retry_policy: 2 retries with short delay for SAMPLE / FAKE dry run
failed_status_rule: failed fetch is FAILED, never UNCHANGED
structure_change_rule: missing primary selector is SOURCE_STRUCTURE_CHANGED

## Evidence Required

- raw.html
- current.normalized.txt
- previous.normalized.txt when comparing against an earlier run
- diff.txt when run_status is CHANGED
- metadata.json
- evidence_record.json
- current_hash reproduced from current.normalized.txt
- storage path following evidence/{regulator_slug}/{source_id}/{run_id}/

## Human Review

Evidence Trail Agent must review the first dry run before any brief is drafted.
Founder review is required before this source candidate becomes production monitoring.
