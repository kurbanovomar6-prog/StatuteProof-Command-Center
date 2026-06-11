---
name: design-polish
description: Review and polish StatuteProof UI components, animations, and micro-interactions for production quality. Applies Emil Kowalski's animation decision framework, impeccable's design rules, and taste-skill's trust-first preset for regulated-industry interfaces. Trigger with #design-polish.
metadata:
  trigger: "#design-polish"
  version: 1.0.0
  adapted_from: |
    emilkowalski/skill (Emil Kowalski, no explicit license)
    impeccable by pbakaus (Apache 2.0)
    taste-skill by leonxlnx (MIT)
---

# Skill: design-polish

## Purpose

Review StatuteProof UI components, landing page sections, and dashboard elements for production-quality polish. Covers animation decisions, typography, color, layout, and trust-signal placement.

## StatuteProof Design Register

StatuteProof operates in **two distinct registers**:

**Landing page (Brand register):** Design IS the product. Distinctiveness matters. Compliance professionals are skeptical — the page must project evidence-grounded credibility, not SaaS hype. Think: precision-tool aesthetic, not startup marketing.

**Dashboard / app (Product register):** Design SERVES the product. Earned familiarity is the goal. Users are CCOs, MLROs, compliance analysts — they use Linear, Excel, and Bloomberg terminals. They want: clear data hierarchy, fast scannability, no decorative noise, trustworthy evidence display.

Before reviewing any UI: state which register applies. Rules diverge.

## Trust-First Preset (Regulated Industry)

StatuteProof is a regulated-industry product. Apply this preset before any aesthetic decision:

```
DESIGN_VARIANCE: 3-4   (not experimental, not agency-creative — precise and controlled)
MOTION_INTENSITY: 2-3  (no motion for motion's sake; only purposeful state changes)
VISUAL_DENSITY: 4-5    (data-dense; compliance professionals read tables and diffs)
```

This overrides any generic "make it feel premium" instruction. A compliance professional seeing a dashboard with scroll-triggered animations and glassmorphism will not trust it with their audit trail.

## Animation Decision Framework

Before writing any animation code, answer in sequence:

**1. Should this animate at all?**

| Frequency | Decision |
|-----------|----------|
| Constant use (every pipeline run, every alert check) | No animation. |
| Daily use (dashboard load, source health refresh) | Remove or drastically reduce |
| Occasional (modal open, alert dismiss) | Standard short transition |
| First-time / onboarding | Can add purposeful feedback |

Never animate keyboard-initiated actions. Never animate a source health status update — that data is real evidence, not a UI moment.

**2. What is the purpose?**

Valid: state indication (CHANGED/UNCHANGED status change), spatial consistency (toast enters/exits same direction), feedback (button confirms click). Invalid: "it looks modern."

**3. Easing rules**
- Entering: `ease-out` (starts fast, feels responsive)
- Exiting: `ease-in` (starts slow, feels natural)
- Never: bounce, elastic, or spring on a compliance-data interface
- Duration ceiling: 200ms for most interactions; 300ms for modals

## Absolute Bans (StatuteProof UI)

Match-and-refuse. If any of these appear in a review, flag and rewrite:

| Ban | Why |
|-----|-----|
| Gradient text (`background-clip: text`) | Decorative, never meaningful |
| Glassmorphism as default (blurred cards everywhere) | Undermines credibility for a compliance product |
| The hero-metric template (giant number + gradient accent) | SaaS cliché; looks fabricated, especially with mock data |
| Identical card grids (same-sized icon+heading+text repeated) | Generic AI scaffold |
| Side-stripe borders (colored `border-left` on cards/alerts) | Visual tell of lazy AI generation |
| Cream/sand/beige body background | The saturated AI default of 2026; reads as template |
| Inter on every weight + purple gradient | The default LLM color palette |
| Animation on source health data update | Evidence data is not a UI moment |
| `overflow: hidden` trapping dropdowns | Breaks menus clipped by layout containers |
| `transition: all` | Specify exact properties; avoid `all` |

## Color Rules

- Body text contrast: ≥ 4.5:1 against background. Gray text on colored background = BLOCK.
- No pure black or pure white. Use tinted tokens.
- For the landing page: pick a color strategy (Restrained / Committed / Full palette) before picking colors. Restrained is the right default for a compliance product — one accent, tinted neutrals.
- Do not default to "warm neutral" backgrounds (cream, sand, ivory). These read as AI output in 2026. Use cool near-white or a tinted neutral anchored to the brand's own hue.
- OKLCH preferred for any new token definitions.

## Typography Rules

- Cap body line length at 65–75ch on desktop.
- Pair fonts on a contrast axis (serif + sans, or one family in multiple weights). Do not pair two similar sans-serifs.
- Display heading letter-spacing floor: ≥ -0.04em. Tighter = letters touch = cramped.
- Hero heading ceiling: clamp() max ≤ 6rem.
- Use `text-wrap: balance` on h1–h3; `text-wrap: pretty` on long prose.

## Layout Rules

- Cards are the lazy default. Use only when they are the best affordance. Nested cards: always wrong.
- Flexbox for 1D layout; Grid for 2D. Do not default to Grid when `flex-wrap` works.
- Build a semantic z-index scale: dropdown → sticky → modal-backdrop → modal → toast → tooltip.
- For evidence data tables: prioritize scanability over visual interest. Right-align numbers. Use monospace for hashes.

## AI Slop Test (StatuteProof-Specific)

Run before any customer-facing UI ships:

1. Does the landing page look like every other RegTech SaaS? (AI purple gradient, Inter, 3-card feature grid, hero metric with a big number) → FAIL.
2. Does the dashboard look like a generic analytics template? (colored sidebar with icon tiles, blurred stat cards, animated number counters) → FAIL.
3. Do any displayed hashes, timestamps, or evidence paths look fabricated? → FAIL regardless of design quality.
4. Does the source health matrix convey real monitoring activity, or does it look like a demo screenshot? → FAIL if no SAMPLE/FAKE label.

## Output Format

```
Register: [Brand / Product]
Preset applied: [Trust-First Regulated]

Animation review:
- [component]: [KEEP / REMOVE / REDUCE — reason]

Absolute bans found: [list or "none"]
Color issues: [list or "none"]
Typography issues: [list or "none"]
Layout issues: [list or "none"]
AI slop test: [PASS / FAIL — specific finding]

Before/After table (for specific code changes):
| Before | After | Why |
|--------|-------|-----|
| [old code] | [new code] | [reason] |

Decision: SHIP / REVISE / BLOCK
Required fixes: [list or "none"]
```

## Example Invocation

```
#design-polish
Component: Source health matrix card in dashboard
Register: Product (dashboard)
Code: [paste component code]
Concern: Cards feel generic and the PASS/ACTIVE badge animation looks promotional
```
