# Workflow 07: Agent Council Review

**When:** A high-stakes decision requires cross-agent validation before execution.
**Agents:** All 7 (Product Manager, Source Monitor, Evidence Trail, Risk + Brief Pipeline, Legal Language, QA / Critic, Chief of Staff).
**Skill:** `#agent-council-review`
**Output:** A final written decision (EXECUTE / EXECUTE_WITH_CONDITIONS / HOLD / REJECT) with a named owner and 3 next actions.

---

## Rule: Do Not Over-Use This Workflow

Workflow 07 is for consequential decisions only. It takes time. Using it for routine tasks adds bureaucracy without value.

Use it when: enabling a new production source, changing pilot terms, delivering the first real customer brief, or making any decision that touches legal safety or evidence integrity.

Do not use it for: copy edits, single source spec creation, or weekly task planning.

---

## Step 1 — Write the Decision Statement

Before invoking the council, write one paragraph:
- What is being decided
- What the specific options are (A / B / C)
- What the stakes are if the wrong option is chosen
- What context the council needs to know

Good decision statement: "We have a complete DFSA evidence record from last Tuesday's run. We want to deliver the first real compliance brief to a pilot customer this week. Options: (A) deliver with full disclaimer and human review flag, (B) deliver only a SAMPLE/FAKE version this week, (C) wait until dashboard API is connected. Stakes: first real customer-facing brief; must not contain forbidden claims; evidence record must be complete."

---

## Step 2 — Run Before-Agent-Council-Decision Checklist

`checklists/before-agent-council-decision.md` — complete all items before starting the review.

---

## Step 3 — Invoke the Skill

```
#agent-council-review
Decision: [paste decision statement]
```

Or use the full prompt template from `prompts/agent-council-prompt.md`.

---

## Step 4 — Run All 7 Stages

Complete every stage in sequence. Do not skip.

**Critical stop conditions:**
- Stage 3 returns BLOCK → Stop. Do not proceed. Fix evidence gaps first.
- Stage 5 returns BLOCK → Stop. Do not proceed. Fix legal safety first.
- Stage 6 returns RETURN_TO_REVIEW → Append the critique and restart from Stage 1.

---

## Step 5 — Record the Output

Format the full output using `examples/sample-agent-council-decision.md` as the template.
Date it. Store it as a dated note (not in the workspace — in your own notes or Obsidian).

---

## Step 6 — Execute the Decision

| Decision | Next step |
|----------|-----------|
| EXECUTE | Chief of Staff assigns the 3 named actions immediately |
| EXECUTE_WITH_CONDITIONS | Log conditions with owner and deadline before any action |
| HOLD | Define what must change before re-review; set a date |
| REJECT | Document the permanent reason; do not revisit without new evidence |

---

## Connection to Ruflo

This workflow is inspired by Ruflo's multi-agent coordination philosophy (ruvnet/ruflo, MIT). The value extracted: specialized agents challenge each other before execution. The implementation here is pure document workflow — no Ruflo runtime, no MCP, no swarm. See `references/ruflo-notes.md` for the full attribution and adaptation decision.
