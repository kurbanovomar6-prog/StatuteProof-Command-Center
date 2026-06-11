# Ruflo — Reference Notes

**Repo:** https://github.com/ruvnet/ruflo
**License:** MIT
**Inspected:** 2026-06-11

## What Ruflo Is

Ruflo is a multi-agent AI harness for Claude Code and Codex. It provides swarm initialization, agent spawning, federated memory, self-learning hooks, MCP tool orchestration, and a daemon for background coordination. It operates at massive scale (98+ agents, 60+ CLI commands, 30+ skills, MCP server with 314 tools).

Formerly known as Claude Flow — renamed to Ruflo by rUv, who loves Rust and flow states. Built on Cognitum.One agentic architecture with Rust-based AI engine.

Key architecture: LEDGER (claude-flow/Ruflo tracks state and memory) + EXECUTOR (Codex/Claude Code does the actual work).

## What Was Useful for StatuteProof

The core philosophical idea: specialized agents should challenge each other sequentially before any execution decision is made. Ruflo calls this a "swarm with hierarchical coordination." The concept is right — but the implementation (runtime daemon, MCP server, federated agents) is overkill for StatuteProof's current stage.

Extracted idea: a **written sequential review** where each agent has a defined role and question, and the final decision comes only after all agents have challenged it. This maps directly to the StatuteProof Agent Council workflow.

Also useful: the division-of-labor concept (coordinator tracks state, worker executes). Applied to StatuteProof: Chief of Staff tracks the decision state, individual agents provide their domain assessment, and execution happens only after the council completes.

## What Was Rejected and Why

| Rejected | Why |
|----------|-----|
| Runtime swarm initialization | StatuteProof does not need 98 agents or daemon coordination |
| MCP tool integration | Adds unnecessary complexity and dependency |
| Federated agent communication | Not relevant at pilot stage |
| Memory backend (AgentDB, HNSW) | The regradar pipeline has its own evidence storage |
| Self-learning hooks | Too much infrastructure for a 10-agent document workflow |
| CLI commands (npx ruflo) | StatuteProof agents are Claude Code subagents, not Ruflo agents |
| Full install path | This workspace is documentation, not a runtime |

## What Was Created Based on Ruflo

`skills/agent-council-review/SKILL.md` — A seven-stage written review process where agents challenge each other. Document workflow only. No Ruflo runtime.

`workflows/07-agent-council-review.md` — How to run the council review.

`docs/agent-council-decision-system.md` — When to use it and how decisions are structured.

`prompts/agent-council-prompt.md` — The prompt template for triggering a council review.

`examples/sample-agent-council-decision.md` — A SAMPLE/FAKE example of a completed council review.

## Adaptation Decision

The Ruflo philosophy was distilled to its essential value for StatuteProof: agents challenge each other before execution, and a designated coordinator (Chief of Staff) makes the final call. The implementation is purely in documents, prompts, and workflows — no code, no runtime, no dependencies.

## License Note

Ruflo is MIT licensed. The concepts adapted here (sequential agent review, division of labor between coordinator and executor) are architectural patterns, not copied code.
