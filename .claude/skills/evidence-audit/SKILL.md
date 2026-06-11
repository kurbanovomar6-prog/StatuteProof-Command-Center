---
name: evidence-audit
trigger: "#evidence-audit"
description: "Audit evidence records for completeness, integrity, storage path correctness, and brief eligibility."
context_files:
  - docs/evidence-record-spec.md
  - schemas/evidence-record.schema.json
  - agents/07-evidence-trail/system-prompt.md
---

# Skill: evidence-audit

## Purpose

Audit evidence records for completeness, integrity, storage path correctness, and brief eligibility.
This skill is used before a record can support a StatuteProof brief.
It is not a legal review and does not decide regulatory applicability.
It checks whether the evidence package is complete enough for the next agent.

## Scope

Use this skill for evidence_record.json files, evidence folders, monitoring run outputs, and SAMPLE / FAKE evidence dry runs.
Use it when a brief draft is blocked on evidence completeness.
Use it when a hash, path, run_id, or evidence status is disputed.
Do not use it to score risk or rewrite the brief.
Do not use it to verify regulator law beyond checking the recorded official_url field.

## Required Context Files

- docs/evidence-record-spec.md
- schemas/evidence-record.schema.json
- agents/07-evidence-trail/system-prompt.md

## Required Inputs

- evidence_record_id
- evidence_record.json path
- declared storage path
- run_id
- source_id
- regulator_slug
- run_status
- current_hash
- current.normalized.txt path
- raw.html path or raw source snapshot path
- diff.txt path when run_status is CHANGED
- official_url or VERIFY BEFORE PRODUCTION marker

## Procedure

1. Load the listed context files before reviewing the record.
2. Confirm the task is within evidence-audit scope.
3. Confirm the evidence_record_id is present.
4. Confirm the evidence_record.json file exists at the declared path.
5. Check each required schema field against schemas/evidence-record.schema.json.
6. Confirm raw snapshot exists at the declared raw path.
7. Confirm current.normalized.txt exists at the declared normalized path.
8. Read current.normalized.txt for hash verification.
9. Recompute current_hash from the normalized text using the documented hashing rule.
10. Compare recomputed hash with the current_hash in the evidence record.
11. Confirm metadata.json exists when the evidence spec requires it.
12. If run_status is CHANGED, confirm diff.txt exists.
13. If run_status is CHANGED, confirm previous.normalized.txt exists when needed for comparison.
14. Confirm storage path follows evidence/{regulator_slug}/{source_id}/{run_id}/.
15. Confirm run_id is unique within the declared source folder if records are available.
16. Confirm evidence_record_status is complete before allowing brief handoff.
17. Confirm official_url is present or the source is marked VERIFY BEFORE PRODUCTION.
18. List every missing or invalid field explicitly.
19. Assign PASS only when all blocking evidence checks pass.
20. Assign BLOCK when any block condition appears.
21. Name the next handoff: Risk + Brief Pipeline Agent if PASS, Source Monitor Agent if evidence must be repaired, founder if an exception is requested.

## Decision Rules

Decision PASS means the evidence record can be handed to the Risk + Brief Pipeline Agent.
Decision BLOCK means the evidence record cannot support a brief yet.
A pending record is always BLOCK.
A hash mismatch is always BLOCK.
A missing raw snapshot is always BLOCK.
A CHANGED record without diff.txt is always BLOCK.
An absent official_url is BLOCK unless the record is clearly SAMPLE / FAKE or marked VERIFY BEFORE PRODUCTION.

## Output Format

Decision: PASS / BLOCK
Missing Items:
- item
Fields Checked:
- field
Hash Verification:
Storage Path Verification:
Required Fixes if BLOCK:
Next Handoff:
Human Review Required: yes/no

## Block Conditions

- raw snapshot missing
- hash cannot be reproduced
- diff missing for CHANGED record
- evidence_record_status is pending
- official_url missing without a VERIFY BEFORE PRODUCTION marker
- evidence_record.json missing
- current.normalized.txt missing
- storage path does not match the required convention

## Example Invocation

#evidence-audit
Project: StatuteProof
Evidence record: ER-SAMPLE-2026-06-11-001
Storage path question: Does evidence/vara/sample-fee-schedule/run-2026-06-11-sample-001/ match the required convention?
Hash verification question: Does current_hash reproduce from current.normalized.txt?
Output needed: PASS or BLOCK with the field that caused the decision.

## Example Output

Decision: BLOCK
Missing Items:
- diff.txt is missing for run_status CHANGED
Fields Checked:
- evidence_record_id
- run_id
- source_id
- raw.html
- current.normalized.txt
- current_hash
- storage path
Hash Verification: current_hash reproduced successfully
Storage Path Verification: path matches evidence/{regulator_slug}/{source_id}/{run_id}/
Required Fixes if BLOCK:
- Add diff.txt generated from previous.normalized.txt and current.normalized.txt, or correct run_status if no change occurred.
Next Handoff: Source Monitor Agent
Human Review Required: no
