# StatuteProof Command Center — Claude Code Instructions

## Workspace Scope

This workspace is **only** for StatuteProof: official-source regulatory monitoring with evidence-backed compliance briefs.

Do not use this workspace for: Polymarket, Excel orders, YouTube pipelines, Ruflo, random automation, or any non-StatuteProof project.

## Priority Order

When given any StatuteProof task, prioritize in this sequence:

1. Official source monitoring (get real evidence first)
2. Evidence trail (store and verify before proceeding)
3. Risk brief (score and draft after evidence is complete)
4. Legal-safe wording (check every customer-facing sentence)
5. QA review (check before delivery)
6. Outreach (only after evidence exists and QA passes)

## Correct Positioning

> "Official-source regulatory monitoring with evidence-backed compliance briefs."

StatuteProof monitors selected public official sources, detects text changes, stores cryptographic evidence records, and drafts monitoring briefs for human review.

## Forbidden Claims (Never Write These)

- AI lawyer
- guarantee compliance
- prevent fines
- replace lawyers
- automatic legal advice
- official partner of [any regulator]
- certified by [any regulator]
- 100% accurate
- never miss an update
- stay compliant automatically
- we handle compliance for you
- automated compliance decisions
- avoid all penalties

See `docs/forbidden-phrases-reference.md` for the full table with approved replacements.

## Standard Disclaimer

All StatuteProof briefs and outreach must include one of:

**Full (briefs):** StatuteProof reports are generated from monitored official-source records and are provided for information and compliance review support only. StatuteProof reports do not constitute legal advice, regulatory advice, compliance certification, or a legal opinion. StatuteProof does not replace qualified legal counsel, compliance professionals, MLROs, or other professional advisers. StatuteProof does not guarantee compliance, prevent fines, or certify that all regulatory updates have been captured. Source monitoring may be affected by publication delays, website changes, PDF formatting, access limits, or source structure changes. Users should verify official source material directly and review evidence records, hashes, timestamps, and diffs before relying on a report. Users should consult qualified legal or compliance professionals before making regulatory, filing, operational, or customer decisions based on a report.

**Short (outreach):** For monitoring information only. Not legal advice and not a guarantee of compliance.

## Tool Router

See `TOOL_ROUTER.md` for which agent or skill to use for each task type.

## Agent Rules

- Never create an 11th active StatuteProof agent.
- Agents in `.claude/agents/` are the authoritative role definitions.
- Agents in `agents/` are the human-readable system prompt docs.
- Chief of Staff is the routing coordinator — do not bypass it for multi-agent tasks.

## SAMPLE / FAKE Label Rule

Any example brief, example evidence record, or example output that uses invented regulatory content **must** be labeled `SAMPLE / FAKE` near the top. This is a legal safety requirement.

## Evidence-First Rule

No brief is drafted before evidence_record_status is complete. No score is assigned without a diff excerpt. No customer delivery without human review when risk >= 70 or confidence < 0.70.

## File Organization

- Source code: `../regradar/` (separate repo, not this folder)
- Agents: `.claude/agents/` (Claude Code subagents) and `agents/` (docs)
- Skills: `.claude/skills/` (Claude Code skills) and `skills/` (docs)
- Docs: `docs/`
- Prompts: `prompts/`
- Workflows: `workflows/`
- Examples: `examples/`
- Checklists: `checklists/`
- Tools: `tools/`
