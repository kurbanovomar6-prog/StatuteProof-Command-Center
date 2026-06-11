# Agent Council Decision System

## Purpose

This document defines when and how to use the seven-agent written review process for high-stakes StatuteProof decisions.

The Agent Council is a **document workflow**. It is not a runtime system, not a swarm, and not an automated orchestrator. Seven agents write sequential reviews that challenge each other. The Chief of Staff issues the final decision.

## When to Use

Use the Agent Council for decisions with real consequences — decisions where a wrong call creates legal risk, trust failure, or irreversible pipeline changes.

**Use it for:**
- Enabling a new official source for production monitoring
- Pricing or pilot offer change
- Customer-facing brief format change
- Dashboard going live with real (not mock) data
- Any decision that involves legal-safety language
- Any decision where you need to know if you are missing something

**Do not use it for:**
- Routine task planning
- Small copy edits
- Minor workflow fixes
- Single-source spec creation (that has its own workflow)

## The Seven-Stage Structure

| Stage | Agent | Blocks if |
|-------|-------|-----------|
| 1 | Product Manager | Decision is out of scope or harms ICP |
| 2 | Source Monitor | Source is not feasible |
| 3 | Evidence Trail | Evidence record is incomplete or missing |
| 4 | Risk + Brief Pipeline | Output quality is INCOMPLETE or confidence very low |
| 5 | Legal Language | Forbidden claim or legal-safety failure |
| 6 | QA / Critic | Assumptions are wrong or untested |
| 7 | Chief of Staff | Final execution decision |

## Block Rules

- Stage 3 BLOCK (Evidence incomplete) → stops execution regardless of other stages
- Stage 5 BLOCK (Legal safety) → stops execution regardless of other stages
- Stage 2 NOT_FEASIBLE → HOLD until condition resolved
- Stage 6 RETURN_TO_REVIEW → sends back to Stage 1 with the critique appended

## Decision Outcomes

| Outcome | Meaning | Next step |
|---------|---------|-----------|
| EXECUTE | All stages passed, no conditions | Chief of Staff assigns first 3 actions |
| EXECUTE_WITH_CONDITIONS | Mostly passed, specific items must resolve first | List conditions, assign owner |
| HOLD | Significant gap needs resolution | Define what changes before re-review |
| REJECT | Decision is wrong permanently | Document reason, close |

## How to Run a Council Review

1. Write a clear one-paragraph decision statement (what, options, stakes)
2. Invoke `#agent-council-review` skill
3. Complete all 7 stages sequentially
4. Record the output in `examples/sample-agent-council-decision.md` format
5. If EXECUTE: Chief of Staff assigns work immediately
6. If EXECUTE_WITH_CONDITIONS: log conditions in a dated note

## Relationship to Ruflo

The Agent Council is inspired by Ruflo's multi-agent coordination philosophy (ruvnet/ruflo). However, it uses no Ruflo runtime, no MCP tools, no swarm initialization, and no daemon. The value extracted from Ruflo: the idea that specialized agents should challenge each other sequentially before any execution happens. The implementation here is pure document workflow — seven agents, seven written sections, one final decision.

## Reference

Full skill: `skills/agent-council-review/SKILL.md`
Prompt template: `prompts/agent-council-prompt.md`
Workflow: `workflows/07-agent-council-review.md`
Checklist: `checklists/before-agent-council-decision.md`
Example output: `examples/sample-agent-council-decision.md`
