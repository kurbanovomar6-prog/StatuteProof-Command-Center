---
name: custom-source-monitoring-spec
description: Use for specifying the StatuteProof feature where users add their own public official websites or public sources for monitoring.
---

# Custom Source Monitoring Spec

## Purpose
Define safe custom-source onboarding for public sources without creating scraping, privacy, or legal risk.

## When to use
Use when planning or implementing user-added source monitoring, source test forms, custom watchlists, or source readiness review flow.

## When not to use
Do not use to build broad crawlers, private portal scraping, customer-data ingestion, or CAPTCHA bypass.

## Required inputs
- Proposed source URL.
- Source owner/regulator context.
- Customer profile and monitoring purpose.
- Current source-test capability.

## Step-by-step procedure
1. Validate URL format and domain.
2. Confirm the source is public and official or clearly customer-authorized public material.
3. Reject login-protected, paywalled, private portal, CAPTCHA-gated, or terms-conflicting sources.
4. Run only a single approved source test before activation.
5. Record fetch method, extraction quality, normalized hash, limitations, and source_id.
6. Require human approval before enabling scheduled monitoring.
7. Show customers source limitations and proof path.

## Output format
- Feature objective.
- Accepted source types.
- Rejected source types.
- Source test flow.
- Data model fields.
- Safety gates.
- Acceptance criteria.

## Safety rules
- No login-protected sources.
- No paywalled sources.
- No CAPTCHA bypass.
- No private portals.
- No customer secrets in URLs.
- No broad crawl by default.

## StatuteProof-specific constraints
Custom sources must still produce source proof and cannot bypass evidence-readiness review.

## Example invocation
"Use custom-source-monitoring-spec to define the Add Custom Source flow for UAE firms."
