# impeccable — Reference Notes

**Repo:** https://github.com/pbakaus/impeccable
**License:** Apache 2.0
**Inspected:** 2026-06-11

## What impeccable Is

A design-quality skill by pbakaus focused on distinguishing generic AI-generated design output from intentional, considered design. Introduces a two-register system (brand vs. product), an AI slop detection methodology, and an absolute ban list of visual patterns that signal low-effort or AI-default output.

The core insight: "AI slop" in design is not just bad aesthetics — it is a set of predictable, identifiable patterns that LLM-generated UI defaults to, most of which destroy trust with sophisticated audiences.

## What Was Useful for StatuteProof

**The two-register framework (brand vs. product):** Brand register = distinctiveness, positioning, first impression. Product register = earned familiarity, trustworthy density, tool-grade reliability. Applied directly to StatuteProof's design-taste-review and ui-ux-review skills.

**AI slop detection methodology:** Systematic checklist of tells that identify AI-generated or AI-templated design. Applied as the "AI Slop Test" table in `skills/design-taste-review/SKILL.md`.

**The absolute ban list:** Specific visual patterns forbidden in any StatuteProof output — gradient text, glassmorphism, identical 3-card grids, purple hero meshes, cream backgrounds, hero-metric animations. Each adapted to the StatuteProof compliance-industry context with audience-specific rationale.

**Trust destruction patterns:** Patterns that specifically destroy trust with compliance professionals (animated stat counters on evidence data, hero metrics with regulatory numbers, rounded cards on compliance dashboards). Extended with StatuteProof-specific rationale from the regulated-industry context.

## What Was Rejected

| Rejected | Why |
|----------|-----|
| Creative industry examples | Not relevant to compliance B2B context |
| Consumer-facing design heuristics | StatuteProof audience is institutional professionals, not consumers |
| Brand expressiveness guidance | StatuteProof needs trust over distinctiveness; expressiveness dial is set low |

## What Was Created Based on impeccable

`skills/design-taste-review/SKILL.md` — The two-register framework, the full AI slop test checklist (10 tells), the absolute ban list embedded in the Restraint and Color taste checks.

`skills/ui-ux-review/SKILL.md` (v1.1.0 update) — Added the brand/product register distinction and the AI slop test to the UX review skill.

`docs/design-quality-system.md` — Formal documentation of the two registers, trust-first preset, and absolute ban table.

## License Note

Apache 2.0 licensed. Design register concept and AI slop detection methodology adapted; no source files copied.
