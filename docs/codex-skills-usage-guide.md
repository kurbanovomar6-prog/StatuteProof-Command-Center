# Codex Skills Usage Guide

## How Codex Uses `.agents/skills`
Repo-scoped Codex skills live in `.agents/skills/<skill-name>/SKILL.md`. Use them when a task clearly matches the skill description or when the prompt explicitly names the skill.

## Skills Added
- `statuteproof-project-review`: broad project/readiness audits.
- `evidence-readiness-review`: source run and proof artifact checks.
- `source-monitoring-review`: parser/source registry/failure handling review.
- `legal-safe-copy-review`: website, brief, outreach, CTA legal safety.
- `mlro-homepage-review`: homepage conversion for UAE MLRO/CCO buyers.
- `custom-source-monitoring-spec`: safe public custom-source monitoring feature.
- `anti-slop-b2b-copy`: concrete, evidence-first B2B copy cleanup.
- `skill-marketplace-research`: safe marketplace research before adapting skills.

## Explicit Invocation Examples
- "Use statuteproof-project-review to audit product readiness."
- "Use evidence-readiness-review on the latest VARA run."
- "Use source-monitoring-review before enabling this source."
- "Use legal-safe-copy-review on this homepage copy."
- "Use mlro-homepage-review on the landing page."
- "Use custom-source-monitoring-spec for Add Your Source."
- "Use anti-slop-b2b-copy to rewrite this outreach email."
- "Use skill-marketplace-research before adding any new skill."

## How Not To Overuse Skills
Do not invoke every skill for every task. Use the narrowest skill that matches the work. Do not install broad skill packs. Do not add skills for one-off preferences that can live in normal docs.

## Reviewing New Skills Before Adding
Before adding a new skill:
1. Review the original skill source.
2. Check scripts, commands, network use, dependency installs, and secrets requirements.
3. Confirm it solves a StatuteProof-specific need.
4. Rewrite instructions in original StatuteProof language.
5. Document attribution in the marketplace research report.
6. Validate with `python3 tools/validate_codex_skills.py`.
