---
name: risk-brief-review
trigger: "#risk-brief-review"
description: "Review draft risk briefs against evidence, risk scoring, schema, legal boundary, and ship/no-ship gates."
context_files:
  - docs/risk-scoring-guide.md
  - schemas/risk-brief-output.schema.json
  - docs/legal-safety-system.md
  - agents/08-risk-brief-pipeline/system-prompt.md
---

# Skill: risk-brief-review

## Purpose

Review a draft StatuteProof risk brief against evidence, risk scoring, affected entity precision, ambiguity handling, and disclaimer completeness.
This skill does not create legal advice.
It determines whether a brief is ready to ship, needs fixes, or must be stopped.
It is used after the Evidence Trail Agent has confirmed that the evidence record is complete.

## Scope

Use this skill for SAMPLE / FAKE briefs, pilot brief drafts, internal risk summaries, and customer-facing brief candidates.
Do not use it to approve a brief when evidence_record_status is pending.
Do not use it to invent affected entities or obligations.
Do not use it to bypass founder review for High-risk or low-confidence output.

## Required Context Files

- docs/risk-scoring-guide.md
- schemas/risk-brief-output.schema.json
- docs/legal-safety-system.md
- agents/08-risk-brief-pipeline/system-prompt.md

## Required Inputs

- draft brief path or pasted draft
- evidence_record_id
- evidence_record_status
- diff.txt path or stored source excerpt
- risk score
- score component rationale
- confidence value
- affected entities section
- ambiguity notes
- disclaimer text
- intended audience
- human review status if risk >= 70 or confidence < 0.70

## Procedure

1. Load the listed context files.
2. Verify the evidence_record is complete before reviewing brief content.
3. If evidence is not complete, return NO-SHIP or BLOCK rather than editing around the gap.
4. Check the risk score against docs/risk-scoring-guide.md.
5. Review every named risk component.
6. Confirm each score component is supported by diff text or source excerpt.
7. Check whether quoted or paraphrased source text is traceable to stored evidence.
8. Check affected entities against the source text.
9. Mark inferred or unclear affected entities as ambiguity notes.
10. Check that confidence is stated numerically.
11. If confidence is below 0.70, confirm human review flag exists.
12. If confidence is below 0.50, treat customer-facing use as blocked.
13. Check ambiguity notes for scope, dates, source limitations, and entity coverage.
14. Check disclaimer completeness against the required 7 elements.
15. Check for legal advice language.
16. Check for compliance guarantees or regulator-affiliation implications.
17. Check that SAMPLE / FAKE examples are labeled.
18. Assign SHIP only when no required fixes remain.
19. Assign SHIP AFTER FIXES when the brief is mostly sound but specific corrections are required.
20. Assign NO-SHIP when evidence, safety, score support, or disclaimer failure blocks use.
21. Name the next handoff: QA / Critic, Legal Language, Evidence Trail, or founder.

## Output Format

Decision: SHIP / SHIP AFTER FIXES / NO-SHIP
Score Component Review:
- component:
Issues Found:
- issue:
Required Fixes if not SHIP:
- fix:
Affected Entity Review:
Disclaimer Review:
Human Review Required: yes/no
Next Handoff:

## Block Conditions

- evidence not complete
- invented obligation not present in diff
- no disclaimer
- High-risk without human review flag
- confidence < 0.50 for customer-facing use
- affected entities guessed without ambiguity note
- SAMPLE / FAKE label missing from example brief

## Example Invocation

#risk-brief-review
Project: StatuteProof
Draft brief: SAMPLE / FAKE VARA fee schedule update brief
Evidence record: ER-SAMPLE-2026-06-11-001, status complete
Risk score: 72
Confidence: 0.65
Concern: affected entities section says all VASPs, but the diff excerpt only mentions licensed exchange operators.
Output needed: SHIP / SHIP AFTER FIXES / NO-SHIP with required fixes.

## Example Output

Decision: SHIP AFTER FIXES
Score Component Review:
- Source authority: supported by stored evidence path.
- Change materiality: supported by diff.txt lines 6-14.
- Operational impact: plausible but should be phrased as review needed.
Issues Found:
- Affected entities are broader than the source excerpt supports.
Required Fixes if not SHIP:
- Replace "all VASPs" with "licensed exchange operators named in the SAMPLE / FAKE excerpt" or mark scope unclear.
Affected Entity Review: needs narrowing before QA.
Disclaimer Review: all 7 elements present.
Human Review Required: yes because risk is 72 and confidence is 0.65.
Next Handoff: QA / Critic after affected-entity fix.
