# Design Quality System

## Purpose

This document defines the design quality standards for StatuteProof's landing page and dashboard. It exists because compliance professionals are pattern-matching experts who will immediately detect a generic AI-generated interface and lose trust in the product.

## Two Registers

**Brand register (landing page):** Design IS the product. A compliance professional scanning the landing page decides in under 10 seconds whether this looks like a tool built for their world. Distinctiveness matters — but not startup-creative distinctiveness. Compliance-grade credibility.

**Product register (dashboard, evidence panels):** Design SERVES the product. Compliance professionals use dense information tools daily. They want: clear data hierarchy, fast scannability, trustworthy evidence display. No decorative noise.

## Trust-First Design Preset

StatuteProof is a regulated-industry product. These dial settings are fixed:

| Dial | Value | Meaning |
|------|-------|---------|
| DESIGN_VARIANCE | 3–4 | Precise and controlled, not experimental |
| MOTION_INTENSITY | 2–3 | Purposeful state changes only |
| VISUAL_DENSITY | 4–5 | Data-dense, compliance-professional density |

## Absolute Bans

These patterns appear in 60–90% of AI-generated SaaS interfaces. Any of them on a StatuteProof page will signal "AI template" to a compliance professional.

| Ban | Reason |
|-----|--------|
| Gradient text (`background-clip: text`) | Decorative, never meaningful |
| Glassmorphism as default | Undermines credibility for a compliance product |
| Hero-metric template (giant number + gradient accent) | SaaS cliché; looks fabricated especially with mock data |
| Identical card grids (icon + heading + text × 3) | Generic AI scaffold |
| Side-stripe borders (`border-left` colored accent) | Lazy AI visual tell |
| Cream/sand/beige/ivory body background | The saturated AI default of 2026 |
| Inter font + slate-900 + purple gradient | The LLM default palette |
| Animation on evidence data or source health status | Evidence data is not a UI moment |
| Animated stat counter on evidence counts | Makes real data look like a demo |
| Uppercase tracked eyebrow on every section | AI scaffold pattern |
| Numbered section markers as default scaffolding | 01 / 02 / 03 = AI grammar |
| Rounded cards ≥ 32px on a compliance dashboard | Over-rounded = amateurish |
| `transition: all` in CSS | Specify exact properties |

## Color Rules

- Body text contrast: ≥ 4.5:1. No gray text on colored backgrounds.
- Color strategy: **Restrained** — one accent, tinted neutrals. Do not pick "warm neutral" by default.
- OKLCH preferred for any new token definitions.
- No pure black or pure white. Use tinted tokens.

## Typography Rules

- Body line length: ≤ 75ch on desktop.
- Font pairing: contrast axis (serif + sans, or one family in multiple weights). Never two similar sans-serifs.
- Display heading letter-spacing floor: ≥ -0.04em.
- Hero heading ceiling: clamp() max ≤ 6rem.
- `text-wrap: balance` on h1–h3; `text-wrap: pretty` on long prose.

## Evidence Display Rules

These are specific to StatuteProof:
- Hash values: monospace font, full 64 characters, left-aligned
- Timestamps: ISO 8601 format, no relative time ("2 hours ago") for evidence records
- Source names: official name only (VARA, CBUAE, DFSA — not "major UAE regulator")
- Risk scores: numerical (72/100) not traffic-light-only
- SAMPLE/FAKE label: visible near the top of any fabricated data display

## Animation Rules

**Before adding any animation, answer:**
1. How often will the user see this? (Daily/constant = no animation)
2. What is the purpose? (State change, spatial consistency, feedback — valid. "Looks modern" — not valid.)
3. What easing? (Entering: ease-out. Exiting: ease-in. Never bounce or elastic on compliance UI.)

**Evidence-specific rule:** Never animate source health status changes, evidence record saves, or run timestamp updates. These data points are real — they are not UI moments.

## Skills Reference

| Task | Skill |
|------|-------|
| Taste + spacing + typography + restraint | `#design-taste-review` |
| UX + trust signals + mock data check | `#ui-ux-review` |
| Component polish + animation decisions | `#design-polish` |
| Landing page copy safety | `#anti-slop-writing-review` |
| Landing page conversion quality | `#landing-page-conversion-review` |
