---
name: source-monitoring-review
description: Use for reviewing StatuteProof source registry, parser, fetcher, normalization, hashing, compare logic, failure handling, QUALITY_DROP, and source IDs.
---

# Source Monitoring Review

## Purpose
Check whether official-source monitoring is deterministic, reproducible, and safe.

## When to use
Use for parser/source registry audits, new source activation review, source-health checks, adapter review, and failure-status review.

## When not to use
Do not use for outreach, design-only work, or legal-copy review. Do not run live source checks without user approval.

## Required inputs
- sources.json path.
- Relevant source entry or URL.
- Fetcher/parser files.
- Prior run records if available.

## Step-by-step procedure
1. Confirm the source is public, official, and relevant to UAE regulated firms.
2. Check source_id stability and enabled/status fields.
3. Trace fetch method: requests, Playwright, adapter, PDF extraction.
4. Trace normalization and hash functions used for comparison.
5. Confirm old-vs-new comparison is deterministic and not LLM-based.
6. Check failure paths: FAILED, QUALITY_DROP, SOURCE_STRUCTURE_CHANGED if present.
7. Check if boilerplate stripping can hide material content.
8. Document extraction limitations.

## Output format
- Source readiness verdict.
- Fetch/extraction route.
- Hash/compare route.
- Failure-handling issues.
- Activation recommendation.

## Safety rules
- No CAPTCHA bypass.
- No private portals.
- No login-protected content.
- No broad crawls without explicit approval.

## StatuteProof-specific constraints
A source is monitored only if it is in sources.json, enabled, and has current evidence of successful extraction.

## Example invocation
"Use source-monitoring-review for the CBUAE regulations source before activation."
