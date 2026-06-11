# taste-skill — Reference Notes

**Repo:** https://github.com/leonxlnx/taste-skill
**License:** MIT
**Inspected:** 2026-06-11

## What taste-skill Is

A Claude Code skill by leonxlnx providing a systematic three-dial design evaluation system: DESIGN_VARIANCE, MOTION_INTENSITY, and VISUAL_DENSITY. Each dial is rated 1–10 and set to a project-specific preset before any review. The skill includes a trust-first preset for regulated or enterprise products, where all three dials are pulled toward precision, restraint, and density.

## What Was Useful for StatuteProof

**The three-dial system (DESIGN_VARIANCE, MOTION_INTENSITY, VISUAL_DENSITY):** A concrete, non-subjective way to characterize target design values for a product category. Applied directly to `skills/design-taste-review/SKILL.md`.

**The trust-first preset:** A pre-configured dial set for regulated industries and enterprise B2B software:
- DESIGN_VARIANCE: 3–4 (precise, not experimental)
- MOTION_INTENSITY: 2–3 (purposeful state changes only)
- VISUAL_DENSITY: 4–5 (data-dense; compliance professionals read tables and diffs)

This was adopted without modification as the **fixed non-adjustable StatuteProof preset** — the dials are not tunable per-review for StatuteProof; the regulated-industry preset is always used.

**5-dimension scoring with threshold:** Dimensions × 10 points = pass/fail threshold. Adapted: StatuteProof uses 5 dimensions / 50 points, threshold 35 REVISE / 45 SHIP.

**The "before any other check" pattern:** Run the disqualifying test (slop test) before proceeding to scoring. Adopted as the AI Slop Test gate in `skills/design-taste-review/SKILL.md`.

## What Was Rejected

| Rejected | Why |
|----------|-----|
| Adjustable dial presets per-review | StatuteProof dials are fixed; compliance industry requires consistency |
| Consumer/lifestyle product examples | Not relevant |
| Expressive motion dimension | StatuteProof has near-zero motion; motion check is minimal |
| Dynamic trust-score output | StatuteProof uses a simpler SHIP/REVISE/BLOCK decision |

## What Was Created Based on taste-skill

`skills/design-taste-review/SKILL.md` — Trust-first dial settings as fixed preset, 5-dimension scoring table, 35/50 REVISE threshold, 45/50 SHIP threshold, "run disqualifier first" pattern.

`docs/design-quality-system.md` — Formal reference for the fixed dial settings and their rationale.

## License Note

MIT licensed. Three-dial system and trust-first preset adapted; no full skill file content copied.
