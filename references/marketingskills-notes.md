# marketingskills — Reference Notes

**Repo:** https://github.com/coreyhaines31/marketingskills
**License:** MIT
**Inspected:** 2026-06-11

## What marketingskills Is

A collection of agent skills for marketing tasks: cold email, copywriting, customer research, CRO, ASO, ads, competitor profiling, and 40+ more. Built by Corey Haines. Each skill is a SKILL.md file with YAML frontmatter and detailed instructions. Zero dependencies — content only.

## What Was Useful for StatuteProof

**Skill file format:** The YAML frontmatter structure (`name`, `description`, `metadata.trigger`, `metadata.version`) was adopted for all StatuteProof skills.

**Cold-email principles:** "Lead with their world, not yours" → adapted for StatuteProof outreach. The outreach must open with the lead's regulatory situation, not with the product.

**CRO (conversion rate optimization):** The framework for landing page sections — headline, sub-headline, proof, objection handling, CTA. Adapted for the `skills/landing-page-conversion-review/SKILL.md`.

**Customer research extraction framework:** pains, triggers, desired outcomes, language used, objections, alternatives considered. Adapted for ICP research.

**"Check for product-marketing-context.md before asking"** pattern → adapted to "check for STATUTEPROOF_CONTEXT.md before making claims."

**One CTA, low-friction:** The cold-email principle of interest-based CTAs ("Worth exploring?") over meeting requests. Applied to StatuteProof outreach rules.

## What Was Rejected

| Rejected | Why |
|----------|-----|
| 51 Node.js CLI tools | Not relevant to StatuteProof |
| Composio integration layer | Not relevant |
| Ad/ASO/SEO/community-marketing skills | Not in StatuteProof scope |
| General B2B copywriting (non-compliance) | Adapted to compliance-specific context instead |

## What Was Created Based on marketingskills

`skills/marketing-outreach-review/SKILL.md` — Outreach review for UAE compliance buyers, ICP fit check, legal safety check, anti-slop check, one CTA.

`skills/landing-page-conversion-review/SKILL.md` — Conversion review for the StatuteProof landing page: headline clarity, ICP fit, proof elements, objection handling, CTA, founding pilot offer.

## License Note

MIT licensed. Skill format structure adapted; no full skill files copied.
