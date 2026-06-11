# Landing Page Review Guide

## Purpose

This document defines what a StatuteProof landing page must and must not say, and how to evaluate it before any customer sees it.

## Audience

UAE financial compliance professionals (CCO, MLRO, Head of Compliance, in-house Legal) at licensed VASPs, banks, or financial intermediaries required to monitor VARA, CBUAE, DFSA, or ADGM publications.

They read dense regulatory text daily. They will notice vague claims, impossible promises, and AI-generated filler instantly. One credibility failure ends the conversation.

## Required Elements

### Hero Section

Must have:
- A specific, evidence-grounded headline (not a promise)
- A sub-headline explaining what StatuteProof actually does
- One primary CTA (low-friction, no guarantee implied)
- Short disclaimer or link to full disclaimer

Good headline: "We detected 18 VARA text changes since January. Each one has a hash, a timestamp, and a diff."
Bad headline: "Never miss a compliance update again."

Good CTA: "See an evidence record"
Bad CTA: "Stay compliant automatically"

### Proof Section

Must:
- Show a real or clearly labeled SAMPLE / FAKE evidence record
- Display actual or SAMPLE hash values, timestamps, run IDs
- Show a real or SAMPLE diff excerpt
- Include the disclaimer near any evidence display

Must not:
- Show fabricated source health data without SAMPLE / FAKE label
- Imply the hashes are real if they are from `mockData.js`

### Source List

Only list sources that are actually enabled in `sources.json` and have at least one successful real run record.
Do not list sources to make the product look more comprehensive than it is.

Current verified active UAE sources: VARA, CBUAE, DFSA, ADGM, MoF UAE, UAE FIU, DIFC Laws, UAE Legislation Portal, Ministry of Economy.

### Pricing / Pilot Section

Must:
- Describe what is included (number of sources, monitoring frequency, brief format)
- Include the short disclaimer

Must not:
- Promise guaranteed coverage
- Imply automated compliance decisions
- Use "replace your legal team" or equivalent

## Forbidden Phrases (Landing Page)

See `docs/forbidden-phrases-reference.md` for full table. Key ones for landing pages:

| Phrase | Why |
|--------|-----|
| "Never miss an update" | Cannot guarantee complete capture |
| "AI lawyer" | Implies legal services |
| "Guarantee compliance" | Warranty claim |
| "Official partner of VARA" | False affiliation |
| "100% accurate" | False precision |
| "Replace your compliance team" | Replacement claim |
| "Automatic compliance decisions" | Removes human judgment |
| "Sleep easy knowing you're compliant" | Emotional guarantee |

## Mock Data Risk (Current Status: HIGH)

As of 2026-06-11, the dashboard `sourceHealthRows` in `mockData.js` shows all 9 UAE sources as `verdict: PASS, status: active`. This is fabricated.

**Do not demo the dashboard to any customer until either:**
1. The dashboard is connected to live `GET /api/sources/health` data, OR
2. Every data point displayed is clearly labeled SAMPLE / FAKE

## Review Checklist Before Any Customer Demo

Use `checklists/before-website-copy.md`.

## Skill Reference

For automated review: invoke `#ui-ux-review` with a URL or screenshot.
