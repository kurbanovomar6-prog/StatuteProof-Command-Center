---
name: agent-council-review
description: Written multi-agent review process for high-stakes StatuteProof decisions. Not a runtime swarm. Seven agents produce sequential written reviews that challenge each other. Use only for major decisions — new source partnerships, pricing changes, feature scope, pilot terms, or any decision with legal or evidence-integrity implications. Trigger with #agent-council-review.
metadata:
  trigger: "#agent-council-review"
  version: 1.0.0
  inspired_by: Ruflo agent coordination philosophy (ruvnet/ruflo, MIT). Document workflow only — no runtime, no swarm, no MCP.
---

# Skill: agent-council-review

## Purpose

Seven StatuteProof agents produce sequential written reviews of a high-stakes decision. Each agent challenges the previous, and the Chief of Staff issues the final execution decision.

This is a **document workflow**. No runtime. No swarm. No MCP tools. Each agent writes one review section and passes it to the next.

## When to Use

Use only for decisions with real consequences:
- New official source to add to monitoring
- Pricing or pilot offer change
- Customer-facing brief format change
- Dashboard going live with real data
- Feature scope that touches legal safety or evidence integrity
- Any decision that could create a legal, compliance, or trust risk

Do not use for: routine task planning, small copy changes, minor workflow fixes.

## The Seven Reviewers

| # | Agent | Question They Answer |
|---|-------|---------------------|
| 1 | Product Manager | Is this decision correctly scoped and does it serve the ICP? |
| 2 | Source Monitor | Is the source or data feasibility confirmed? |
| 3 | Evidence Trail | Are the evidence and proof requirements met? |
| 4 | Risk + Brief Pipeline | What is the analytical risk and what does the output quality look like? |
| 5 | Legal Language | Is the decision legally safe and free of forbidden claims? |
| 6 | QA / Critic | What assumptions are wrong, overstated, or untested? |
| 7 | Chief of Staff | What is the final execution decision and what happens next? |

## Procedure

### Step 1 — State the Decision

Before invoking the council, write a clear one-paragraph decision statement:
- What is being decided
- What the options are
- Why this decision matters now
- What the consequences of each option are

### Step 2 — Product Manager Review (Stage 1)

**Question:** Is this decision correctly scoped? Does it serve the StatuteProof ICP (CCO/MLRO at a UAE-licensed financial firm)?

Product Manager writes:
- Decision restatement in product terms
- ICP fit: which customer segment does this affect?
- Scope boundary: what is in and what is out?
- Roadmap alignment: does this fit the current MVP scope?
- Recommendation: PROCEED / NARROW / REJECT with one-sentence reason

### Step 3 — Source Monitor Review (Stage 2)

**Question:** Is the data or source feasibility confirmed for this decision?

Source Monitor writes:
- Source availability: can we actually fetch and normalize the relevant data?
- URL verification: are the official source URLs confirmed?
- Quality risk: what fetch failures or quality drops are likely?
- Scope: how many sources does this decision touch?
- Recommendation: FEASIBLE / CONDITIONAL / NOT_FEASIBLE with specific conditions

### Step 4 — Evidence Trail Review (Stage 3)

**Question:** Are the evidence and proof requirements met?

Evidence Trail writes:
- What evidence record is required for this decision?
- Is the evidence_record_status complete?
- Are hashes, timestamps, and diffs available for any brief this decision references?
- What happens if evidence is incomplete?
- Recommendation: EVIDENCE_COMPLETE / EVIDENCE_GAPS (list gaps) / BLOCK

### Step 5 — Risk + Brief Pipeline Review (Stage 4)

**Question:** What is the analytical risk and what does the output look like?

Risk + Brief Pipeline writes:
- Risk score estimate for the decision's outputs
- Score components: source authority, change materiality, operational impact
- Confidence level estimate
- Human review trigger check: would this output require founder review?
- Output quality: would the brief be GOOD, LIMITED, or INCOMPLETE?
- Recommendation: LOW_RISK / MEDIUM_RISK / HIGH_RISK (define human review required if HIGH)

### Step 6 — Legal Language Review (Stage 5)

**Question:** Is the decision legally safe?

Legal Language writes:
- Does any language in the decision description use forbidden claims?
- Does the output of this decision create legal-safety risk?
- Disclaimer check: is the full disclaimer required for this decision's outputs?
- Forbidden phrase scan: any of the 28 forbidden phrases implied?
- Recommendation: SAFE / REVISE (specific edits) / BLOCK (specific reason)

### Step 7 — QA / Critic Review (Stage 6)

**Question:** What is wrong, overstated, or untested?

QA / Critic writes:
- What assumption in this decision has the weakest evidence?
- What did stages 1–5 miss or gloss over?
- What is the worst-case scenario if this decision is wrong?
- What would a skeptical compliance professional say about this?
- Recommendation: SHIP / SHIP_WITH_CONDITIONS (list) / RETURN_TO_REVIEW

### Step 8 — Chief of Staff Final Decision (Stage 7)

**Question:** What is the execution decision and what happens next?

Chief of Staff writes:
- Summary of stages 1–6 findings
- Final decision: EXECUTE / EXECUTE_WITH_CONDITIONS / HOLD / REJECT
- If EXECUTE: what are the first 3 actions?
- If EXECUTE_WITH_CONDITIONS: what must be resolved before execution?
- If HOLD: what must change before re-review?
- If REJECT: what is the permanent reason?
- Owner: who executes? Who reviews the output?
- Timeline: when is the next check-in?

## Output Format

Each stage produces one section. The full council output looks like:

```
# Agent Council Review — [Decision Title]
Date: [YYYY-MM-DD]
Decision: [one-paragraph statement]

## Stage 1 — Product Manager
[review text]
Recommendation: [PROCEED / NARROW / REJECT]

## Stage 2 — Source Monitor
[review text]
Recommendation: [FEASIBLE / CONDITIONAL / NOT_FEASIBLE]

## Stage 3 — Evidence Trail
[review text]
Recommendation: [EVIDENCE_COMPLETE / EVIDENCE_GAPS / BLOCK]

## Stage 4 — Risk + Brief Pipeline
[review text]
Recommendation: [LOW_RISK / MEDIUM_RISK / HIGH_RISK]

## Stage 5 — Legal Language
[review text]
Recommendation: [SAFE / REVISE / BLOCK]

## Stage 6 — QA / Critic
[review text]
Recommendation: [SHIP / SHIP_WITH_CONDITIONS / RETURN_TO_REVIEW]

## Stage 7 — Chief of Staff Final Decision
[final decision text]
Decision: [EXECUTE / EXECUTE_WITH_CONDITIONS / HOLD / REJECT]
Next 3 actions: [list]
Owner: [who]
Timeline: [when]
```

## Block Conditions

Any BLOCK at Stage 3 (Evidence) or Stage 5 (Legal Language) stops execution regardless of other stages.
Any NOT_FEASIBLE at Stage 2 triggers HOLD until Source Monitor condition is resolved.
A RETURN_TO_REVIEW at Stage 6 sends the decision back to Stage 1 with the QA critique appended.

## Example Invocation

```
#agent-council-review
Decision: We want to enable the DFSA laws portal as a new monitored source and deliver the first real brief to a pilot customer.
Options: (A) Enable and deliver this week. (B) Enable but hold delivery until QA pass. (C) Wait for dashboard API connection first.
Stakes: First real customer-facing brief. Evidence record must be complete. Legal-safe wording required.
```
