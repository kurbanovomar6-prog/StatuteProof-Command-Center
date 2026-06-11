# AI-Company-Agent-OS — Reference Notes

**Repo:** https://github.com/kurbanovomar6-prog/AI-Company-Agent-OS
**License:** MIT
**Inspected / Source:** Internal (own repo), June 2026

## What AI-Company-Agent-OS Is

A lightweight multi-agent operating system built by Omar Kurbanov. Provides a structured framework for running specialized Claude Code agents as an AI company: a Chief of Staff coordinates, domain agents execute, and a sequential pipeline ensures decisions pass through the right specialists before execution.

The OS consists of 10 agents (34 files total): chief-of-staff, product-manager, code-architect-dev, qa-critic, legal-language, source-monitor, evidence-trail, risk-brief-pipeline, icp-lead-research, outreach-writer. Each agent has a system prompt in `.claude/agents/` for Claude Code subagent use.

## What Was Useful for StatuteProof

**All 10 agent definitions:** StatuteProof is built on AI-Company-Agent-OS. All agent system prompts were imported directly as-is into `StatuteProof-Command-Center/.claude/agents/` and `agents/` (human-readable copies).

**The Chief of Staff routing pattern:** One agent coordinates all others. Multi-agent tasks always go through the coordinator first. Applied as the routing rule in `CLAUDE.md` and `TOOL_ROUTER.md`.

**Sequential pipeline architecture:** Source Monitor → Evidence Trail → Risk + Brief Pipeline → Legal Language → QA / Critic → Outreach Writer. This sequence maps directly to StatuteProof's monitoring-to-brief workflow.

**10-agent ceiling:** The AI-Company-Agent-OS is designed for exactly this set of 10 specialists. The "never create an 11th active agent" rule comes from the OS design — each agent has a specific bounded scope, and adding more creates coordination overhead without benefit.

**The `.claude/agents/` format:** Claude Code subagent definitions with YAML frontmatter, description, and system prompt. This is the canonical format for all StatuteProof agents.

## What Was Rejected

| Rejected | Why |
|----------|-----|
| Generic company use cases | AI-Company-Agent-OS is generic; StatuteProof agents have domain-specific instructions injected |
| Any agents beyond the 10 | 10-agent ceiling enforced |
| Workflow templates (if any generic) | StatuteProof uses its own workflows specific to the monitoring-to-brief pipeline |

## What Was Created Based on AI-Company-Agent-OS

`.claude/agents/` (10 files) — All 10 agent definitions copied and present in StatuteProof-Command-Center.

`agents/` (10 .md files) — Human-readable copies of agent system prompts for reference.

StatuteProof's sequential pipeline architecture (Workflows 01–07) follows the AI-Company-Agent-OS coordination pattern.

## Relationship Note

AI-Company-Agent-OS is Omar's own project. It exists at:
- Local: `/Users/kurbnovomar/AI-Company-Agent-OS/`
- GitHub: `https://github.com/kurbanovomar6-prog/AI-Company-Agent-OS`

StatuteProof-Command-Center is the domain-specific command center built on top of this OS, not a fork of it. The agents are used, but StatuteProof adds its own skills, docs, workflows, and evidence pipeline on top.

## License Note

MIT licensed. Agents are Omar's own work, imported directly.
