# StatuteProof — Design System

> Source of truth for the frontend design system. Product-register (design SERVES
> the task). Web. Authored 2026-07-12 during the impeccable design pass.

## Register

product

## Platform

web

## Positioning

A **forensic instrument for compliance officers / MLROs**, not SaaS marketing.
Opened daily to answer one question: *"did anything change I must act on, and what
do I do?"* At rest it must feel like a **calm, trustworthy cockpit** — quiet,
in-control, honest about its limits. Reference-adjacent: Linear, Stripe Dashboard,
Vercel, Mercury, GitHub PR-diff. Anti-references: neon-on-black dashboards
(Datadog/Grafana) and any government/regulator portal.

## Colors (dark, opaque; depth by surface ramp, not blur/gradient)

Surface ramp — elevation = lightness step + 1px hairline (`--hairline
rgba(255,255,255,0.045)`), never glassmorphism or gradients:

| Token | Hex | Role |
|---|---|---|
| `--bg-base` | `#050B15` | L0 canvas / body |
| `--bg-navy` | `#070E1A` | L1 app chrome / sidebar |
| `--bg-surface` | `#0A1522` | L2 |
| `--bg-elevated` | `#0C1826` | L2 card fill (default card) |
| `--bg-raised` | `#12202F` | L3 raised / hero panel |
| `--bg-tooltip` | `#16283A` | L4 floating overlay |
| `--paper-strong` | `#F7FBFB` | document surface (evidence, briefs, reports) |
| `--ink` | `#07111F` | text on paper |

Borders: `--border-muted #1B2A40`, `--border #22314A`, `--border-subtle #12223A`.

Text (verify ≥4.5:1 on its surface; the "Not legal advice" disclaimer is legally
load-bearing — never gray-for-elegance):

| Token | Hex | Role |
|---|---|---|
| `--text-primary` | `#E8EEF5` | body, values |
| `--text-secondary` | `#A9B6C6` | labels, captions, disclaimer |
| `--text-muted` | `#6E7E92` | tertiary meta only |

Accent — ONE cyan, ≤10% of pixels, **action/selection/focus/live-dot only, never
decoration**:

| Token | Hex | Role |
|---|---|---|
| `--accent` | `#16D9F5` | primary action, current selection, focus ring |
| `--accent-hover` | `#67E8F9` | hover |
| `--accent-deep` | `#0891B2` | pressed |

Semantic status — muted, meaning not decoration:

| Token | Hex | Means | May appear as |
|---|---|---|---|
| `--success` | `#37D399` | verified / ok / up-to-date | dot, chip, check |
| `--warning` | `#F4B84A` | pending / elevated-risk / needs attention soon | dot, chip |
| `--risk-high` / danger | `#FB7185` | HIGH-risk item or a real failure | **small dot/chip only** — never a hero ring, side-stripe, or decoration |
| `--status-changed` | `#60A5FA` | changed since last check (neutral info) | diff marker, badge |

**Rose rule:** a high number is not danger; danger is danger. Rose is reserved for
overdue / failed / broken / integrity-fail, shown as a small dot or chip. A
first-glance-clean screen shows zero red above the fold.

## Typography

- **One family: Geist** for all UI (headings, buttons, labels, body, data). A
  familiar sans is acceptable and correct for product register.
- **JetBrains Mono** (`--font-mono`, `.sp-mono`) ONLY where mono does work: SHA-256
  hashes, timestamps, record IDs, URLs, diffs.
- **Fixed rem scale** (not fluid clamp — a fluid h1 shrinks badly in a sidebar),
  tight ratio ~1.2: page title ~1.5rem/600, section 1.125rem, card-title
  ~0.9375rem, body 0.875rem, meta 0.8125rem, micro 0.75rem/500. Weights 400/500/600.
- `font-variant-numeric: tabular-nums` globally — numbers align in columns.
- **Labels are sentence case.** No pervasive `text-transform: uppercase` /
  `letter-spacing` eyebrows. At most one short category chip (e.g. `HIGH`) may be
  caps.

## Components

- Surfaces are opaque cards (`.sp-card` / `.sp-glass` / `.sp-panel`), one radius
  `--radius-card` (10px). One elevation strategy per surface: a 1px hairline border
  OR a tight shadow (≤8px, floating overlays only), never both, never a cyan glow.
- Primary button (`.sp-btn-primary`): flat `--accent` fill, no gradient, no
  drop-shadow. Secondary: bordered surface.
- Every interactive element ships default / hover / focus / active / disabled /
  loading. Skeletons (`.sp-skeleton`) for loading, not center spinners.
- Empty states teach the interface, not "nothing here."
- Evidence objects are forensic: inset mono "data fields" (truncate-middle +
  copy), a notarial verified line (`Verified · SHA-256 match · {UTC}`), an honest
  hash-chain (prev → this) with a hairline connector. No blockchain/Merkle wording.

## Motion

- 150–250 ms, conveys state (hover, selection, feedback), not decoration.
- No page-load reveal sequences, no infinite decorative pulses, no bounce/overshoot
  (`--ease-spring` = ease-out `cubic-bezier(0.16, 1, 0.3, 1)`).
- `@media (prefers-reduced-motion: reduce)` alternative required (present).

## Bans (do not reintroduce)

Glassmorphism as default · decorative grid/radial backgrounds · gradient fills &
gradient text · cyan-glow shadows · side-stripe accent borders (`border-l-4`) ·
hero-metric ring · identical card grids · over-rounded (>16px) cards · uppercase
eyebrow on every block · orchestrated fade-up reveals.

## Sample / fake data

Any invented regulatory content in the UI must carry a visible `SAMPLE / FAKE`
label near the top (legal-safety requirement).
