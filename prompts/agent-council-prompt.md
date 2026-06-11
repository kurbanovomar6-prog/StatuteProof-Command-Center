# Agent Council Prompt

Use this prompt to trigger a full seven-stage agent council review for a high-stakes StatuteProof decision.

**Only use for decisions with real consequences.** Not for routine tasks.

---

## Prompt

```
You are running a seven-stage StatuteProof Agent Council review.

This is a document workflow. Each agent writes one review section. No runtime. No swarm. No automation.

Decision to review:
[PASTE DECISION STATEMENT HERE — one paragraph: what is being decided, what the options are, what the stakes are]

Run all seven stages in sequence. Do not skip any stage. Do not proceed to Stage 7 if Stage 3 or Stage 5 returns BLOCK.

---

STAGE 1 — PRODUCT MANAGER
Question: Is this decision correctly scoped? Does it serve the StatuteProof ICP?
Write: Decision restatement in product terms, ICP fit, scope boundary, roadmap alignment.
Recommendation: PROCEED / NARROW / REJECT

---

STAGE 2 — SOURCE MONITOR
Question: Is the source or data feasibility confirmed?
Write: Source availability, URL verification status, quality risk, scope of sources affected.
Recommendation: FEASIBLE / CONDITIONAL / NOT_FEASIBLE

---

STAGE 3 — EVIDENCE TRAIL
Question: Are the evidence and proof requirements met?
Write: Evidence record status, required fields check, proof_quality assessment.
Recommendation: EVIDENCE_COMPLETE / EVIDENCE_GAPS (list gaps) / BLOCK
[STOP IF BLOCK]

---

STAGE 4 — RISK + BRIEF PIPELINE
Question: What is the analytical risk and output quality?
Write: Risk score estimate, score components, confidence level, human review trigger check.
Recommendation: LOW_RISK / MEDIUM_RISK / HIGH_RISK

---

STAGE 5 — LEGAL LANGUAGE
Question: Is the decision legally safe?
Write: Forbidden phrase scan, disclaimer check, legal-advice boundary check.
Recommendation: SAFE / REVISE (specific edits required) / BLOCK
[STOP IF BLOCK]

---

STAGE 6 — QA / CRITIC
Question: What is wrong, overstated, or untested?
Write: Weakest assumption, what stages 1-5 missed, worst-case scenario.
Recommendation: SHIP / SHIP_WITH_CONDITIONS (list) / RETURN_TO_REVIEW
[RETURN_TO_REVIEW → append critique and restart from Stage 1]

---

STAGE 7 — CHIEF OF STAFF FINAL DECISION
Write: Summary of stages 1-6, final decision, first 3 actions, owner, timeline.
Decision: EXECUTE / EXECUTE_WITH_CONDITIONS / HOLD / REJECT
```

---

## After the Council Review

1. Save the full output as a dated note
2. If EXECUTE: Chief of Staff assigns actions immediately
3. If EXECUTE_WITH_CONDITIONS: log conditions with owner and deadline
4. If HOLD: define what must change before re-review
5. If REJECT: document the permanent reason

Use `examples/sample-agent-council-decision.md` as a format reference.
