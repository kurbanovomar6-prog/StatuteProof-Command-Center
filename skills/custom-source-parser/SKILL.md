# Custom Source Parser Skill

**Trigger:** `#custom-source-parser`  
**Role:** Source Intake Review  
**Purpose:** Run a structured intake review before activating any new regulatory source

---

## When to Use

Use this skill when:
- Adding a new source to sources.json
- Debugging a source that produces unexpected content
- Investigating a hash collision between two sources
- Investigating a source that passes checks but returns navigation-only content

---

## Review Protocol (Sequential)

### Stage 1 — URL Safety
- Confirm URL is publicly accessible (not private IP, not localhost, not file://)
- Confirm URL resolves to an official regulator domain
- Confirm no redirect to a login page or CAPTCHA wall

### Stage 2 — Fetch Quality
- Confirm extracted char count is above expected minimum
- Confirm fetch method is appropriate (requests vs playwright)
- Flag if char count < 500 without PDF augmentation

### Stage 3 — Nav-Shell Check
- Run `is_nav_shell_only()` on extracted text
- Review first 500 chars of normalized.txt
- If > 65% lines are short (< 8 words): nav shell confirmed

### Stage 4 — Hash Uniqueness
- Confirm content hash is unique across all enabled sources
- If identical hash found: hash collision — must fix before activating

### Stage 5 — Content Relevance
- Review normalized.txt manually for 30 seconds
- Confirm text contains regulatory content (rules, notices, guidance) not navigation/marketing
- Flag if text is primarily UI elements ("Submit", "Cookie policy", "Back")

### Stage 6 — Verdict
- `CONFIRMED_ACCESSIBLE`: all stages pass → recommend activate
- `NAV_SHELL_ONLY`: stage 3 or 4 fail → add wait_for_selector + content_selector, re-run
- `JS_RENDERING_NEEDED`: stage 2 fail → add fetch_method: playwright, re-run
- `BLOCKED`: stage 1 fail → do not activate, document reason
- `UNSUPPORTED`: consistent failure → escalate to adapter_required

---

## Output Format

```
## Source Intake Review — [source_id]
**Date:** YYYY-MM-DD
**URL:** https://...
**Status:** CONFIRMED_ACCESSIBLE | NAV_SHELL_ONLY | ...

### Stage Results
- Stage 1 URL Safety: PASS / FAIL — [reason]
- Stage 2 Fetch Quality: PASS / FAIL — [chars]
- Stage 3 Nav-Shell: PASS / FAIL — [short-line ratio]
- Stage 4 Hash Uniqueness: PASS / FAIL — [collision_source_id or none]
- Stage 5 Content Relevance: PASS / FAIL — [brief description of content]
- Stage 6 Verdict: [status]

### Recommended Action
[Specific steps to fix or activate]
```

---

## Reference

- Runbook: `docs/custom-source-parser-runbook.md`
- Module: `product/regradar/app/source_intake.py`
- Status vocabulary: `SourceIntakeStatus` constants in source_intake.py
- DFSA fix example: `sources.json` entries for `AE-dubai-financial-services-authority-dfsa` and `AE-dfsa-notices`
