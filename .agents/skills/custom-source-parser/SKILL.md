---
name: custom-source-parser
description: Use for reviewing StatuteProof Source Lab/parser results before saving, validating, or activating a public custom source.
---

# Custom Source Parser

## Purpose

Review one public source-intake result without overclaiming readiness.

## When to use

Use when testing a Source Lab URL, reviewing a parser result, debugging nav-shell or hash-collision output, deciding whether a source can be saved for validation, or deciding whether a remediation source can move toward customer-visible ready.

## When not to use

Do not use for broad crawls, all-source monitoring, private portals, login pages, CAPTCHA bypass, paywall bypass, scraping personal/private data, or legal advice.

## Required inputs

- Source URL and source_id if available.
- Source Lab JSON or parser result.
- Source registry entry if built-in.
- Evidence/proof paths if save mode was used.
- Baseline run count if activation readiness is being considered.

## Review stages

1. URL safety: public http(s), no credentials, no localhost/private IP/file URL.
2. Access policy: reject or block login, CAPTCHA, paywall, private portal, and restricted-source signs.
3. Fetch/extraction route: requests, Playwright, content selector, wait selector, PDF path, provider used.
4. Quality: normalized length, quality score/label, policy warnings, selector timeout, PDF shallow text.
5. Nav shell: review nav_shell flag and first 500 chars for menu-only output.
6. Hash uniqueness: check normalized_hash/content_hash and collision_source_id.
7. Evidence: no-save must stay PREVIEW_ONLY; evidence confirmed requires proof artifacts.
8. Activation: monitoring-ready requires baseline completion and QA/Legal-safe wording.

## Output format

- Verdict: BLOCK / NEEDS_REMEDIATION / CAN_SAVE_FOR_VALIDATION / BASELINE_PENDING / MONITORING_READY.
- Reason.
- Provider and extraction method.
- Evidence level.
- Activation readiness.
- Failure reason.
- Remediation hint.
- Customer-facing wording allowed.
- Customer-facing wording blocked.

## Safety rules

- One successful no-save test is not evidence confirmed.
- One successful evidence run is not monitoring-ready.
- Do not say any website can be parsed.
- Do not imply legal advice, guaranteed parsing, or regulator certification.
- Founder approval is required before a source moves from remediation to customer-visible ready when live verification is incomplete.
