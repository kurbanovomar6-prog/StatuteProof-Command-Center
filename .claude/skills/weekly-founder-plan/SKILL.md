---
name: weekly-founder-plan
trigger: "#weekly-founder-plan"
description: "Create a strict three-outcome founder plan focused on StatuteProof execution and revenue proof."
context_files:
  - memory/weekly-plans.md
  - memory/open-questions.md
  - docs/statuteproof-mvp-plan.md
  - agents/01-chief-of-staff/system-prompt.md
---

# Skill: weekly-founder-plan

## Purpose

Create a strict three-outcome weekly plan for a solo founder focused on StatuteProof execution and first revenue proof.
This skill filters a noisy founder brain dump into a practical week.
It protects the founder from side projects, premature tooling, and broad roadmap work.
It produces a plan that can be copied into memory/weekly-plans.md after founder approval.

## Scope

Use this skill on Monday planning, Friday reset, or when the founder needs to recover focus.
Use it for StatuteProof MVP execution only during the V3.1 period.
Do not use it to plan V4.
Do not use it to add new active agents.
Do not use it to schedule unrelated freelance or side-project work inside StatuteProof blocks.

## Required Context Files

- memory/weekly-plans.md
- memory/open-questions.md
- docs/statuteproof-mvp-plan.md
- agents/01-chief-of-staff/system-prompt.md

## Required Inputs

- founder brain dump
- current week date
- prior weekly plan status if available
- known blockers
- current StatuteProof milestone
- available workdays
- customer or source deadlines
- do-not-edit or do-not-build constraints

## Procedure

1. Load the listed context files.
2. Receive the founder brain dump without treating every item as equal.
3. Separate StatuteProof tasks from distractions.
4. Filter every candidate through opportunity cost versus StatuteProof first revenue.
5. Keep work that proves source monitoring, evidence records, briefs, ICP learning, outreach, or validation.
6. Park work that belongs to dashboards, V4, new agents, unrelated projects, or premature automation.
7. Select exactly 3 weekly outcomes.
8. Write a done-state for each outcome.
9. Confirm every done-state can be checked by Friday.
10. Create a do-not-do list with at least 3 items and reasons.
11. Assign daily blocks Monday through Friday.
12. Keep each day to max 3 actions.
13. Keep each day to max 1 deep work block.
14. Identify blockers and name the owner for each.
15. Mark source verification blockers separately from product blockers.
16. Produce the weekly output template.
17. Assign PASS if the plan is focused and complete.
18. Assign REVISION NEEDED if there are more than 3 outcomes, missing done-states, no StatuteProof action, or empty do-not-do list.
19. State exactly what to write to memory/weekly-plans.md.
20. State what open questions should be written to memory/open-questions.md.

## Output Format

Decision: PASS / REVISION NEEDED
Outcome 1:
Done-state:
Outcome 2:
Done-state:
Outcome 3:
Done-state:
Do-Not-Do List:
- item: reason
Daily Blocks Mon-Fri:
Blockers:
- blocker: owner
Memory Update:
Founder Approval Field: PASS / REJECT

## Block Conditions

- more than 3 outcomes
- no StatuteProof action in top 3
- outcome has no done-state
- do-not-do list is empty
- daily plan contains unrelated project execution
- automation or dashboard work appears before manual monitoring proof

## Example Invocation

#weekly-founder-plan
Project: StatuteProof
Week of: 2026-06-15
Founder brain dump: verify VARA source URL, draft CBUAE source spec, build dashboard, start V4 agent architecture, research 20 UAE fintech leads, update personal website, learn n8n, run evidence hash dry run, write landing page copy, pitch unrelated freelance client.
Known blockers: official source URLs not yet verified; evidence dry run not complete.
Output needed: exactly 3 outcomes, do-not-do list, daily blocks, blockers, memory update.

## Example Output

Decision: PASS
Outcome 1: Verify first official source candidates for VARA, CBUAE, and DFSA or ADGM FSRA.
Done-state: each candidate is either verified or marked VERIFY BEFORE PRODUCTION with open question owner.
Outcome 2: Create 2 draft source specs and run one SAMPLE / FAKE evidence dry run.
Done-state: two specs exist and one run folder contains raw, normalized, hash, metadata, and audit note.
Outcome 3: Research 20 public-source ICP leads.
Done-state: memory/icp-leads.md contains 20 leads with tier, trigger URL, and contact title status.
Do-Not-Do List:
- Build dashboard: reason, monitoring proof is not complete.
- Start V4 architecture: reason, V3.1 validation and Week 1 proof come first.
- Learn n8n deeply: reason, automation is gated until two manual runs succeed.
- Pitch unrelated freelance client: reason, StatuteProof execution blocks are protected.
Daily Blocks Mon-Fri:
- Monday: verify source candidates, draft source-spec field list, record blockers.
- Tuesday: draft VARA SAMPLE / FAKE source spec, draft CBUAE SAMPLE / FAKE source spec, run validator.
- Wednesday: run evidence dry run, audit hash, fix missing evidence fields.
- Thursday: research 10 leads, score tiers, draft lead notes.
- Friday: research 10 leads, review weekly outputs, prepare next-week blockers.
Blockers:
- Official source URL verification: owner founder.
- Hash procedure confirmation: owner Evidence Trail Agent.
Memory Update:
- Write approved plan to memory/weekly-plans.md.
- Write unresolved URL verification questions to memory/open-questions.md.
Founder Approval Field: PASS / REJECT
