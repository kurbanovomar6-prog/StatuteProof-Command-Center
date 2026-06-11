---
name: design-taste-review
description: Review StatuteProof UI for taste, spacing, typography, restraint, and product credibility. Applies B2B seriousness and compliance-buyer trust standards. Catches the generic AI website look before it reaches a customer. Trigger with #design-taste-review.
metadata:
  trigger: "#design-taste-review"
  version: 1.0.0
  adapted_from: |
    emilkowalski/skill (Emil Kowalski — design engineering philosophy)
    impeccable by pbakaus (Apache 2.0 — design register, AI slop detection)
    taste-skill by leonxlnx (MIT — three-dial system, trust-first preset)
---

# Skill: design-taste-review

## Purpose

Catch the generic AI website look. Enforce product credibility and B2B seriousness for StatuteProof's compliance-professional audience.

This is not a broad UX review. It is a taste check: does this look like a real, credible compliance-intelligence tool, or does it look like an AI-generated SaaS landing page template?

## Audience Mental Model

Target: CCO or MLRO at a UAE-licensed financial firm.
Daily context: Bloomberg terminal, VARA circulars, PDF regulations, compliance dashboards.
What they trust: evidence, hashes, timestamps, precision tools.
What destroys trust immediately: gradient text, purple glow effects, "never miss an update" badges, animated stat cards, hero metrics with fake numbers.

## The One-Line Design Read

Before any review, state:
> "Reading this as: [page type] for [audience], in the [register] register."

- **Brand register** (landing page): distinctiveness matters — but not SaaS-startup distinctiveness. Compliance-grade credibility.
- **Product register** (dashboard, evidence panel): earned familiarity is the goal. Users should trust it like they trust Airtable or Stripe Dashboard.

## Trust-First Dial Settings (Fixed for StatuteProof)

These are not adjustable:
```
DESIGN_VARIANCE: 3-4   (precise, not experimental)
MOTION_INTENSITY: 2-3  (purposeful state changes only)
VISUAL_DENSITY: 4-5    (data-dense; compliance professionals read tables and diffs)
```

## Taste Checks (Run on Every Review)

**Spacing:**
- [ ] Is whitespace consistent and intentional? Not "lots of padding = premium."
- [ ] Are related elements visually grouped? Unrelated elements clearly separated?
- [ ] Is the section rhythm varied? (Not: every section = heading + 3 equal cards)

**Typography:**
- [ ] Body line length ≤ 75ch on desktop. Wider = unreadable.
- [ ] Font pairing on contrast axis (serif + sans, or one family in multiple weights). Not two similar sans-serifs.
- [ ] Display heading letter-spacing ≥ -0.04em. Tighter = cramped.
- [ ] Is the type hierarchy clear in 3 seconds? Can you tell H1 from H2 from body instantly?
- [ ] No uppercase tracking on every section header (the AI-scaffold pattern).

**Color:**
- [ ] Body text contrast ≥ 4.5:1. Not light gray on white for "elegance."
- [ ] No cream/sand/beige/ivory body background (the 2026 AI default).
- [ ] No gradient text (`background-clip: text`).
- [ ] No gray text on a colored background (looks washed out).
- [ ] Color strategy declared: Restrained (one accent, tinted neutrals) is correct for StatuteProof.

**Restraint:**
- [ ] No glassmorphism as default (blurred cards everywhere).
- [ ] No hero-metric template (giant number + gradient accent for the evidence count).
- [ ] No identical card grid (same-sized icon + heading + text × 3).
- [ ] No numbered section markers as scaffolding (01 About / 02 Process / 03 Pricing).
- [ ] No side-stripe borders (colored `border-left` on cards or alerts).
- [ ] No animated counter for evidence stats (evidence data is not a moment to celebrate).

**Product Credibility:**
- [ ] Does this look like a tool a compliance officer would use, or a startup's marketing site?
- [ ] Evidence hashes displayed in monospace font.
- [ ] Risk score presented as a number with components, not as a traffic-light emoji badge.
- [ ] Source health data presented as a table, not as animated status dots.
- [ ] Does the proof/evidence panel look like it contains real cryptographic data?

## The AI Slop Test

Run this before any other check. If any is YES, fix before proceeding to scoring:

| Tell | YES/NO |
|------|--------|
| AI-purple gradient in the hero | |
| Centered hero over dark mesh background | |
| Identical 3-card feature grid | |
| Glassmorphism on every card | |
| Gradient text on headline | |
| Animated stat counter on evidence data | |
| Inter font + slate-900 + purple accent (the default LLM palette) | |
| Cream/sand/beige/ivory body background | |
| "Never miss an update" badge with a pulse ring | |
| Rounded cards ≥ 32px on a compliance dashboard | |

Any YES = REVISE before scoring.

## Scoring

Rate 1–10 on each:

| Dimension | Question |
|-----------|----------|
| Spacing discipline | Consistent, intentional rhythm? |
| Typography hierarchy | Readable in 3 seconds? Contrast axis pairing? |
| Color restraint | No banned patterns? Tinted neutrals only? |
| Product credibility | Looks like a real compliance tool, not a startup template? |
| Evidence display quality | Hashes, timestamps, diffs presented with precision? |

Below 35/50: REVISE before any customer sees this.
Above 45/50: SHIP.

## Output Format

```
Register: [Brand / Product]
Design Read: [one-line]

AI Slop Test: [PASS / FAIL — specific tells]

Taste Checks:
- Spacing: [note]
- Typography: [issues or "clear"]
- Color: [issues or "clear"]
- Restraint: [violations or "clear"]
- Product credibility: [note]

Score:
- Spacing discipline: [1-10]
- Typography hierarchy: [1-10]
- Color restraint: [1-10]
- Product credibility: [1-10]
- Evidence display quality: [1-10]
- Total: [X/50]

Required fixes: [list or "none"]
Decision: SHIP (>45) / REVISE (35-45) / BLOCK (<35 or slop test FAIL)
```

## Example Invocation

```
#design-taste-review
Component: Landing page hero section and feature cards
Register: Brand (landing)
Concern: Hero uses a big "18 changes detected" counter with animated increment and purple glow — is this the hero-metric ban? Feature section has three identical cards.
```
