# emilkowalski/skill — Reference Notes

**Repo:** https://github.com/emilkowalski/skill
**License:** MIT
**Inspected:** 2026-06-11

## What emilkowalski/skill Is

A Claude Code skill by Emil Kowalski (emilkowalski.com), a design engineer known for precise UI craft. The skill provides a structured framework for reviewing UI/UX work with specificity: the reviewing agent is trained to produce concrete, actionable feedback tied to exact values (tracking, spacing, contrast ratios) rather than vague "looks good" or "too generic" observations.

Core philosophy: design taste is not subjective preference — it is the consistent application of specific principles that separate professional-grade UI from AI-generated templates.

## What Was Useful for StatuteProof

**The "One-Line Design Read" pattern:** Before reviewing, state what you are reading and for whom. Forces the reviewer to commit to a register before evaluating. Applied directly to `skills/design-taste-review/SKILL.md`.

**Specificity-first feedback:** The skill trains reviewers to name exact values: not "the heading is too loose" but "letter-spacing should be ≤ -0.04em at display sizes." Applied to StatuteProof's typography checks.

**Audience mental model mapping:** Emil's approach grounds every design critique in the user's daily visual context — what they see at work, what they trust. Applied as the "Audience Mental Model" section of the design-taste-review skill (CCO/MLRO daily context: Bloomberg terminal, VARA circulars, precision tools).

**Critique output format:** Problem → Why it matters → Specific fix. Applied to the design-taste-review output template.

## What Was Rejected

| Rejected | Why |
|----------|-----|
| Framer Motion specifics | StatuteProof does not use Framer Motion |
| Animation curves and spring configs | Too implementation-specific; adapted to MOTION_INTENSITY dial instead |
| Consumer product aesthetics | Emil's examples often target consumer/creative products; adapted to regulated-industry B2B context |

## What Was Created Based on emilkowalski/skill

`skills/design-taste-review/SKILL.md` — The "One-Line Design Read," audience mental model, specificity-first taste checks, and feedback output format.

## License Note

MIT licensed. Design critique methodology adapted; no full skill file content copied.
