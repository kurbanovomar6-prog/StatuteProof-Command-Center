# Risk Scoring Guide

## Purpose
This guide defines how StatuteProof classifies official-source regulatory changes as Low, Medium, or High risk for compliance intelligence support.
It is a scoring aid for monitoring and review workflows, not legal advice.
It does not determine legal obligations, certify compliance, or replace qualified legal/compliance professionals.
The score helps prioritize human review, customer brief urgency, and affected-team routing.
Every score must trace to official-source evidence captured in an evidence record.
If evidence is missing, the correct output is BLOCK, not a risk score.

## Inputs Required
- evidence_record_id
- evidence_record_status
- source_name
- regulator
- official_url
- source_type
- source_publication_type
- detected_at timestamp
- run_id
- current_hash
- previous_hash when applicable
- raw snapshot path
- normalized current text path
- normalized previous text path when applicable
- diff path
- diff excerpt
- changed clauses or paragraphs
- publication date if visible
- effective date if visible
- affected entity text from source
- obligation verbs from source
- enforcement or penalty text from source
- filing/reporting/submission text from source
- confidence assessment
- ambiguity notes
- human reviewer name if already reviewed

## Risk Levels
Low risk: 0-34.
Low risk changes are usually layout-only changes, minor wording clarifications, FAQ updates without obligation language, or changes with narrow operational impact.
Low risk still needs evidence, but it may not require urgent customer escalation unless the customer has opted into all-change alerts.
Low risk example: a regulator updates the footer date on a page with no change to normalized regulatory text.
Low risk example: a FAQ answer adds a clarifying sentence using may/can language and no deadline.

Medium risk: 35-69.
Medium risk changes may affect compliance review but do not obviously create immediate broad obligations.
Medium risk examples include guidance changes, changed reporting cadence, new clarification affecting a specific activity, or obligations with long effective dates.
Medium risk usually requires a human review before client delivery when confidence is below 0.85 or ambiguity exists.
Medium risk example: a guidance page states that firms should update an internal policy within 90 days.

High risk: 70-100.
High risk changes include new obligations, short deadlines, enforcement language, licensing implications, broad entity scope, AML/CFT/sanctions/KYC/STR impact, or new reporting/submission requirements.
High risk always requires human review before any customer-facing brief.
High risk example: an official circular says all VASPs shall submit a monthly transaction report within 21 days and includes penalty language.
High risk does not mean StatuteProof gives legal advice; it means the update should be reviewed promptly by qualified professionals.

## Human Review Mandatory When
- final_score is 70 or higher
- confidence is below 0.70
- evidence_record_status is not complete
- official_url is missing or not verifiable
- source text references another document not captured in evidence
- obligation scope is unclear
- affected entities are unclear
- source monitor status is QUALITY_DROP
- source monitor status is SOURCE_STRUCTURE_CHANGED
- source monitor status is FAILED
- diff excerpt is truncated or incomplete
- normalized text length changed by more than expected quality thresholds
- enforcement, penalty, sanction, suspension, or license language is present
- deadline is immediate or within 30 days
- customer-facing output will be sent

## Score Components Table
| Component | Trigger | Points | Notes |
|---|---:|---:|---|
| Source authority | Official regulator publication | +10 | Use only when source is directly hosted by or clearly published by regulator. |
| Source authority | Consultation, discussion paper, non-binding guidance | +7 | Still official, but usually lower certainty than rulebook/circular. |
| Obligation language | must, shall, required, obligation | +20 | Strongest obligation signal; quote exact wording in brief. |
| Obligation language | should, expected, encouraged | +10 | Indicates review relevance but lower certainty than mandatory language. |
| Obligation language | may, can, permitted | +3 | Usually permissive; do not overstate. |
| Deadline / effective date | immediate or less than 30 days | +15 | Always consider human review and urgency. |
| Deadline / effective date | 30-90 days | +10 | Material planning window. |
| Deadline / effective date | more than 90 days | +5 | Lower urgency but still relevant. |
| Enforcement and penalty language | penalty, fine, sanction, suspension | +12 | Quote exact phrase; human review strongly favored. |
| Enforcement and penalty language | supervisory concern or review concern | +7 | Less direct than penalty but still meaningful. |
| Reporting / filing / submission impact | new report, filing, or submission required | +10 | Important operational impact for compliance teams. |
| Reporting / filing / submission impact | changed cadence, format, or recipient | +8 | Material if recurring process changes. |
| Licensing or registration impact | license condition changed | +15 | Strong signal because license continuity can be affected. |
| Licensing or registration impact | registration update or notification required | +10 | Important but may be narrower than license condition change. |
| AML / CFT / sanctions / KYC / STR | new obligation | +12 | High sensitivity area; use exact source language. |
| AML / CFT / sanctions / KYC / STR | policy reference only | +5 | Lower unless attached to new requirement. |
| Affected entity breadth | all VASPs, all regulated firms, broad class | +8 | Broad customer relevance. |
| Affected entity breadth | specific activity, product, or license class | +5 | Narrower targeting. |
| Document type | rulebook, regulation, circular | +10 | Usually stronger authority/impact. |
| Document type | guidance, FAQ, notice | +5 | Still relevant but may require more interpretation caution. |
| Change type | material amendment | +10 | Must be evidenced in diff. |
| Change type | new document | +8 | May require source-level review. |
| Change type | minor wording | +2 | Avoid over-escalation. |
| Change type | layout or navigation only | +0 | Usually no brief; source monitor may record unchanged meaningful content. |
| Ambiguity adjustment | unclear scope or cross-reference missing | +5 | Add points for review need and reduce confidence. |
| Confidence multiplier | 0.95 | n/a | Full evidence, clean diff, clear source, unambiguous text. |
| Confidence multiplier | 0.85 | n/a | Evidence complete but some interpretation or source-context limits. |
| Confidence multiplier | 0.70 | n/a | Partial context, noisy source, or ambiguous affected entities. |
| Confidence multiplier | 0.50 | n/a | Low confidence; human review mandatory and customer brief should usually be blocked. |

## Formula
raw_score = sum of all applicable component points
final_score = min(100, round(raw_score * confidence_multiplier))
risk_level = Low if final_score < 35, Medium if final_score is 35-69, High if final_score >= 70
Use the final score in customer-facing summaries only after evidence, legal language, and QA review.
Use confidence as a separate field, not as a substitute for evidence.

## Human Review Logic
```text
human_review_required = false
if evidence_record_status != "complete": human_review_required = true
if final_score >= 70: human_review_required = true
if confidence < 0.70: human_review_required = true
if source_status in ["FAILED", "QUALITY_DROP", "SOURCE_STRUCTURE_CHANGED"]: human_review_required = true
if deadline_days is not null and deadline_days < 30: human_review_required = true
if enforcement_language_present: human_review_required = true
if affected_entities_unclear: human_review_required = true
if diff_references_missing_document: human_review_required = true
if customer_facing_output: human_review_required = true
```

## Worked SAMPLE / FAKE Example
SAMPLE / FAKE source: VARA monthly reporting guidance hosted at `https://example.invalid/vara-sample-guidance`.
This is not a real regulatory update.
Diff excerpt says: "All licensed VASPs shall submit a monthly transaction activity report to the Authority beginning 21 days from publication. Failure to submit may result in supervisory action."
Component scoring:
- Official regulator publication: +10
- Obligation language, shall submit: +20
- Deadline less than 30 days: +15
- Broad VASP scope: +8
- Enforcement/supervisory action: +7
- New filing/submission: +10
- Document type guidance: +5
Raw score: 75
Confidence multiplier: 0.85 because evidence is complete but this is a SAMPLE / FAKE guidance example and scope would require human review.
Final score: min(100, round(75 * 0.85)) = 64
Risk level: Medium in this scoring example.
Human review: true because customer-facing brief and short deadline.
If the same text appeared in a binding circular with penalty language, the raw score would rise and likely become High.

## Common Mistakes
1. Scoring a brief without a complete evidence record.
2. Treating guidance as regulation without saying why.
3. Treating may/can language as mandatory.
4. Ignoring an effective date.
5. Ignoring a changed reporting cadence.
6. Giving every update High risk to seem cautious.
7. Under-scoring AML/CFT/sanctions/KYC/STR language.
8. Hiding ambiguity instead of flagging human review.
9. Using a risk score as legal advice.
10. Forgetting the confidence multiplier.
11. Failing to cite the diff text that drove the score.
12. Treating SOURCE_STRUCTURE_CHANGED as a regulatory change.

## Output Handoff Format
```markdown
HANDOFF TO RISK + BRIEF PIPELINE / QA
Evidence record: [id]
Run status: [status]
Raw score: [number]
Confidence multiplier: [0.95/0.85/0.70/0.50]
Final score: [number]
Risk level: [Low/Medium/High]
Score factors: [list]
Affected entities: [list]
Ambiguity notes: [list]
Human review required: [true/false]
Human review reason: [reason]
Source evidence: [official_url, diff_path, hashes]
```
