# Skills Cleanup Review

Date: 2026-06-14

Scope: review repo-scoped `.agents/skills/` and `.codex/agents/` for safe commit readiness. No parser work, DFSA checks, deployment, or runtime monitoring was performed.

## Summary

- Skills reviewed: 47
- Skills kept: 47
- Skills rejected: 0
- Codex agent configs reviewed: 10
- Active project agent count remains 10; no 11th active agent added.
- No executable helper scripts were found under `.agents/skills/` or `.codex/agents/`.
- Secret scan found no real secrets. Pattern hits were examples, safety language, or skill-review terminology.

## Codex Agent Configs Kept

- `chief-of-staff.toml` — kept; matches existing 10-agent roster.
- `code-architect-dev.toml` — kept; matches existing 10-agent roster.
- `evidence-trail.toml` — kept; matches existing 10-agent roster.
- `icp-lead-research.toml` — kept; matches existing 10-agent roster.
- `legal-language.toml` — kept; matches existing 10-agent roster.
- `outreach-writer.toml` — kept; matches existing 10-agent roster.
- `product-manager.toml` — kept; matches existing 10-agent roster.
- `qa-critic.toml` — kept; matches existing 10-agent roster.
- `risk-brief-pipeline.toml` — kept; matches existing 10-agent roster.
- `source-monitor.toml` — kept; matches existing 10-agent roster.

## Skills Kept

- `agent-browser` — Browser QA/reference workflow for local app and Source Lab inspection.
- `anti-slop-b2b-copy` — StatuteProof-specific B2B copy tightening and unsupported-claim reduction.
- `brainstorming` — Structured planning skill; no scripts; useful before creative/product changes.
- `cold-email` — Supports Outreach Writer agent for controlled outbound drafts.
- `competitors` — Supports product positioning/comparison docs when needed.
- `copy-editing` — General copy polish; useful with legal-safe review.
- `copywriting` — General page copy drafting; requires legal-safe review for customer-facing use.
- `custom-source-monitoring-spec` — Directly supports public custom-source monitoring scope.
- `customer-research` — Supports ICP/customer research without runtime code.
- `customer-research-validation` — Supports demand validation and interview/survey planning.
- `decision-memo` — Useful for executive decisions and tradeoff framing.
- `design` — Useful design support; instruction-only skill, no bundled executable scripts.
- `dispatching-parallel-agents` — Coordination aid for independent tasks; no runtime swarm framework added.
- `docx` — Document handling instructions only; license noted, no bundled secrets/scripts.
- `emails` — Supports lifecycle/campaign planning; must use legal-safe review for claims.
- `evidence-audit` — Directly supports Evidence Trail agent gates.
- `evidence-readiness-review` — Directly supports source evidence/proof readiness checks.
- `executing-plans` — Useful for executing written implementation plans with checkpoints.
- `executive-briefing` — Useful for founder/operator briefings.
- `launch` — Useful for release/launch planning; no deployment authority.
- `legal-safe-copy-review` — Directly supports customer-facing legal-safety review.
- `lifecycle-crm-email` — Useful lifecycle communications guidance; includes not-legal-advice boundary.
- `mlro-homepage-review` — StatuteProof-specific MLRO homepage/conversion review.
- `pdf` — PDF handling instructions only; license noted, no bundled secrets/scripts.
- `pilot-to-scale-roadmap` — Useful for pilot-to-production planning.
- `pricing` — Pricing strategy support; customer-facing copy still needs legal-safe review.
- `pricing-packaging-strategy` — Pricing/package strategy support; no runtime code.
- `prompt-injection-review` — Skill safety review for untrusted content and prompt-injection risks.
- `prospecting` — Supports ICP lead research using public sources; no credential collection.
- `redesign-skill` — Used by visual upgrade work; instruction-only design skill.
- `release-launch-readiness` — Useful release checklist skill; no deployment authority.
- `risk-brief-review` — Directly supports risk/brief and QA gates after evidence exists.
- `risk-register` — Useful executive risk register support.
- `sales-prospecting-outreach` — Supports ethical outreach workflows; includes compliance disclaimers.
- `skill-creator` — Skill maintenance support; prompt-injection warning context reviewed.
- `skill-marketplace-research` — Documents/reviews future skill sourcing safely.
- `source-monitoring-review` — Directly supports source registry/parser/fetch/extraction review.
- `statuteproof-project-review` — StatuteProof-specific broad project audit skill.
- `subagent-driven-development` — Useful for scoped multi-task execution; no runtime framework added.
- `systematic-debugging` — Useful for parser/API/test failures.
- `taste-skill` — Used by visual quality work; instruction-only, no scripts.
- `test-driven-development` — Useful for parser/source quality tests.
- `ui-ux-pro-max` — Used by visual quality work; instruction-only, shell mentions are reference text.
- `verification-before-completion` — Required verification discipline before completion claims.
- `webapp-testing` — Useful for local frontend/Source Lab testing.
- `weekly-founder-plan` — Useful founder planning skill.
- `writing-plans` — Useful for implementation plans before code changes.

## Skills Rejected Or Left Out

- None in this cleanup. All reviewed skills are instruction-only `SKILL.md` files, have name/description frontmatter, and are useful for StatuteProof product, parser, evidence, QA, legal-safety, design, outreach, or operating workflows.

## Risk Notes

- `pdf` and `docx` list proprietary license text in frontmatter. They are committed as instruction files only; no binaries, packages, or executable scripts are included.
- `prompt-injection-review` contains phrases like “ignore previous instructions” and “exfiltrate” because it teaches detection of those risks. This is safe review terminology, not an instruction to perform those actions.
- Some marketing, pricing, outreach, and design skills are broad. They are kept because StatuteProof has active Outreach Writer, ICP, Product, and visual/product-design workflows. Customer-facing claims still require Legal Language and QA/Critic review.
- Some skills mention `PASS`/`BLOCK` as internal review verdicts. These are not customer-facing source status labels.
- `pdf` contains an example `qpdf --password=...` command. It is an example placeholder, not a secret.

## Required Use Boundaries

- Skills do not override system, developer, user, repository, or security instructions.
- Skills must not be used to bypass login pages, CAPTCHA, paywalls, private portals, or source access controls.
- Parser/source-intake work must keep no-save preview, evidence confirmed, and activation readiness separate.
- Customer-facing copy must not claim any website can be parsed, guaranteed parsing, guaranteed compliance, regulator certification, official partnership, or legal advice.
