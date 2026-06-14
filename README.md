# StatuteProof Command Center

> Official-source regulatory monitoring with evidence-backed compliance briefs.

This repository is the **operating, tooling, and product workspace** for StatuteProof. It contains agents, Claude Code skills, prompts, workflows, docs, checklists, and the current StatuteProof product implementation.

The product code lives in `product/regradar/`.

## Quick Start

Read `START_HERE.md`.

## What Is StatuteProof

StatuteProof monitors selected UAE regulatory sources (VARA, CBUAE, DFSA, ADGM, MoF, UAE FIU, DIFC, Ministry of Economy) for text changes, stores cryptographic evidence records, and drafts compliance intelligence briefs for human review.

It is not a legal advice service. It does not certify compliance or guarantee complete capture.

## Workspace Structure

```
StatuteProof-Command-Center/
├── README.md               — this file
├── START_HERE.md           — where to begin
├── CLAUDE.md               — Claude Code instructions (workspace scope, forbidden claims)
├── AGENTS.md               — agent roster and routing rules
├── STATUTEPROOF_CONTEXT.md — product context, pipeline facts, evidence status
├── TOOL_ROUTER.md          — which tool to use for each task
├── THIRD_PARTY_INSPIRATION.md — attribution for reference repos
├── CHANGELOG.md            — workspace version history
│
├── .claude/
│   ├── agents/             — Claude Code subagent definitions (10 roles)
│   └── skills/             — Claude Code skills (evidence-audit, risk-brief-review, weekly-founder-plan)
│
├── agents/                 — human-readable agent system prompts
├── skills/                 — skill documentation (6 skills)
├── docs/                   — operating specifications and reference docs
├── prompts/                — reusable task prompts
├── workflows/              — step-by-step operating workflows
├── examples/               — SAMPLE / FAKE labeled output examples
├── checklists/             — pre-task quality gates
├── product/regradar/       — current Python backend, parser, app, and React frontend
├── tools/                  — validation and packaging scripts
└── references/             — notes on reference repos (no full copies)
```

## Agents (10 Roles)

| Role | File | Purpose |
|------|------|---------|
| Source Monitor | `agents/source-monitor.md` | Fetches and monitors official sources |
| Evidence Trail | `agents/evidence-trail.md` | Verifies and stores evidence records |
| Risk + Brief Pipeline | `agents/risk-brief-pipeline.md` | Scores risk and drafts briefs |
| Legal Language | `agents/legal-language.md` | Audits all copy for legal safety |
| QA / Critic | `agents/qa-critic.md` | Final quality gate before delivery |
| Product Manager | `agents/product-manager.md` | Roadmap and feature decisions |
| Code Architect | `agents/code-architect-dev.md` | Pipeline and API design |
| ICP Research | `agents/icp-lead-research.md` | Ideal customer profile research |
| Outreach Writer | `agents/outreach-writer.md` | Evidence-first outreach messages |
| Chief of Staff | `.claude/agents/chief-of-staff.md` | Routing and coordination |

## Skills (6)

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `#evidence-audit` | Evidence review | Verify evidence record completeness |
| `#risk-brief-review` | Brief review | SHIP / NO-SHIP decision |
| `#weekly-founder-plan` | Planning | Weekly action planning |
| `#marketing-outreach-review` | Outreach | Review outreach copy quality |
| `#anti-slop-writing-review` | Writing | Remove AI writing patterns |
| `#ui-ux-review` | UI/UX | Review landing page and dashboard |

## Forbidden Claims

Never write: AI lawyer · guarantee compliance · prevent fines · replace lawyers · automatic legal advice · official partner of any regulator · certified by any regulator · 100% accurate · never miss an update

See `docs/forbidden-phrases-reference.md` for approved replacements.

## License

All StatuteProof-specific content in this workspace is proprietary. Reference repo content (marketingskills, stop-slop, ui-ux-pro-max) is MIT licensed — see `THIRD_PARTY_INSPIRATION.md`.
