---
name: ui-ux-review
description: Review the StatuteProof landing page or dashboard for UX quality, trust signal placement, compliance-audience fit, anti-slop copy, and AI design tells. Use before any public-facing update or customer demo. Trigger with #ui-ux-review.
metadata:
  trigger: "#ui-ux-review"
  version: 1.1.0
  adapted_from: |
    ui-ux-pro-max-skill by nextlevelbuilder (MIT)
    impeccable by pbakaus (Apache 2.0)
    taste-skill by leonxlnx (MIT)
    emilkowalski/skill by Emil Kowalski
---

# Skill: ui-ux-review

## Purpose

Review the StatuteProof landing page or internal dashboard for:
1. Trust signals appropriate for a compliance-professional audience
2. Landing page structure and CTA quality
3. Mock data risks (compliance professionals cannot trust fabricated evidence)
4. Copy quality (anti-slop, forbidden claims, legal safety)
5. Source transparency matrix accuracy (is the data real?)
6. AI design tells and generic SaaS patterns that damage credibility
7. Design register fit (brand vs. product)

## Design Register

State the register before reviewing:

**Brand register (landing page):** Design IS the product. Distinctiveness matters. The page must project evidence-grounded credibility — not RegTech startup hype. Compliance professionals are skeptical. Every claim must be traceable.

**Product register (dashboard):** Design SERVES the product. Users are CCOs and MLROs. Earned familiarity is the goal. They want: clear data hierarchy, fast scannability, trustworthy evidence display. No decorative noise.

## Trust-First Preset for Regulated Industry

Before any aesthetic judgment, apply:
- DESIGN_VARIANCE: 3–4 (precise and controlled, not experimental)
- MOTION_INTENSITY: 2–3 (only purposeful state-change transitions)
- VISUAL_DENSITY: 4–5 (data-dense; compliance professionals read tables, diffs, and hashes)

A compliance professional who sees glassmorphism, animated stat cards, or a "big-number hero" will not trust the platform with their audit trail.

## Review Dimensions

Score each 1–10 independently:

| Dimension | What to Check |
|-----------|--------------|
| Trust Signals | Evidence timestamps, hash displays, human-review badges — real or mocked? Labeled? |
| CTA Clarity | One clear primary action? Low-friction ask? Matches product stage? |
| Copy Safety | No forbidden claims, no guarantee language, disclaimer present? |
| Audience Fit | Speaks to CCO/MLRO pain, not generic SaaS language? |
| Source Transparency | Source health data from real source_runs.jsonl or from mockData.js? |
| Information Hierarchy | Evidence paths, hashes, timestamps findable in under 10 seconds? |
| Design Quality | No AI slop tells? No absolute-ban patterns? Register-appropriate? |

Below 42/70: flag for rework before any customer demo.

## AI Slop Test (Run First)

Before scoring dimensions, check:
- Does the landing page look like every other RegTech SaaS? (purple gradient, Inter, 3-card feature grid, hero metric with big number) → FAIL
- Does the dashboard look like a generic analytics template? (blurred stat cards, colored sidebar icon tiles, animated number counters) → FAIL
- Do any hashes, timestamps, or source health values look fabricated without a SAMPLE/FAKE label? → FAIL
- Does the source health matrix convey real monitoring, or does it look like a demo screenshot? → FAIL without label

Absolute-ban patterns (any = BLOCK):
- Gradient text (`background-clip: text`)
- Glassmorphism as default (every card blurred)
- Hero-metric template (giant number + gradient accent for evidence display)
- Identical card grids on the landing page feature section
- Side-stripe borders (`border-left` colored accent on cards)
- Cream/sand/beige body background (the 2026 AI default)
- Animation on source health data or evidence record display

## StatuteProof-Specific Checks

### Landing Page (Brand Register)

- [ ] Hero statement is evidence-first ("Detected 18 VARA text changes since January" beats "Monitor regulatory updates automatically")
- [ ] Hero does not use the hero-metric template (big stat + gradient accent) — unless the stat is a real run count
- [ ] Disclaimer visible above fold or within one scroll
- [ ] No forbidden claims in any headline, subheading, CTA, or badge
- [ ] Proof section elements (hashes, timestamps, diff excerpts) labeled SAMPLE/FAKE if fabricated
- [ ] Source list contains only actually-enabled sources with real run records
- [ ] Pricing section: no compliance guarantee in tier descriptions
- [ ] Font pairing is on a contrast axis (not two similar sans-serifs)
- [ ] Body text contrast ≥ 4.5:1; no gray text on colored backgrounds

### Dashboard (Product Register)

- [ ] Source health matrix: data from real GET /api/sources/health or clearly labeled SAMPLE/FAKE
- [ ] Last-checked timestamps: real run timestamps from source_runs.jsonl or labeled
- [ ] Alert list: real CHANGED/QUALITY_DROP events or labeled
- [ ] Evidence path links: resolve to real snapshot files or labeled
- [ ] Hash values displayed in monospace font; right-aligned numbers in tables
- [ ] No animation on evidence data updates or source health status changes
- [ ] No decorative motion on data that represents real monitoring state

## Mock Data Risk Severity

| Data Type | Risk if Mock and Unlabeled |
|-----------|--------------------------|
| Source health status (PASS/active) | HIGH — customer believes monitoring is live |
| Last-checked timestamps | HIGH — implies recency that does not exist |
| Risk scores on alerts | HIGH — implies analysis not performed |
| Evidence hashes | HIGH — cryptographic evidence that does not exist |
| Sample brief content | LOW — acceptable if labeled SAMPLE/FAKE |
| Feature graphics in marketing | LOW — acceptable if not presented as real data |

## CTA Guidance (Compliance Audience)

Preferred CTAs:
- "Request a monitoring demo" (specific, low-commitment)
- "See an evidence record" (shows the product, not a promise)
- "Review a SAMPLE/FAKE brief" (proof of capability)
- "Join the founding pilot" (specific, honest about stage)

Avoid:
- "Start your free trial" (implies fully automated product)
- "Get compliant today" (guarantee)
- "Never miss an update" (impossible promise)
- Any CTA with animated pulse rings or glow effects (undermines compliance credibility)

## Output Format

```
Register: [Brand / Product]
AI Slop Test: [PASS / FAIL — specific tells if FAIL]

Score:
- Trust Signals: [1-10] — [note]
- CTA Clarity: [1-10] — [note]
- Copy Safety: [PASS / BLOCK] — [flagged phrases if any]
- Audience Fit: [1-10] — [note]
- Source Transparency: [1-10] — [mock data or "real data confirmed"]
- Information Hierarchy: [1-10] — [note]
- Design Quality: [1-10] — [ban violations or "clean"]
- Total: [X/70]

Mock Data Issues: [list or "none found"]
Absolute Ban Violations: [list or "none"]
Forbidden Copy Claims: [list or "none"]
Required Fixes (before customer demo): [list or "none"]
Decision: DEMO-READY / REVISE / BLOCK
```

Threshold: < 42/70 → REVISE. Any BLOCK in Copy Safety → BLOCK regardless of score. AI Slop Test FAIL → REVISE minimum, BLOCK if mock data or forbidden claim present.

## Example Invocation

```
#ui-ux-review
Page: StatuteProof landing page (local dev)
Register: Brand (landing)
Audience: Head of Compliance, UAE-licensed VASP
Concern: Hero section uses a big "18 changes detected" stat card with a purple gradient — is this the hero-metric ban?
```
