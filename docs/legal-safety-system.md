# Legal Safety System

## Purpose
This system keeps StatuteProof language inside a safe compliance-intelligence boundary.
It helps the founder write clear customer-facing language without making legal advice, guarantee, or regulator-affiliation claims.

## Boundary Definition
StatuteProof can:
1. Monitor selected official public regulatory sources.
2. Detect changes in normalized source text.
3. Store evidence records with URLs, timestamps, hashes, snapshots, and diffs.
4. Draft evidence-backed compliance intelligence briefs.
5. Support human compliance review by surfacing updates faster.

StatuteProof cannot:
1. Provide legal advice.
2. Certify compliance.
3. Guarantee regulatory compliance.
4. Prevent fines or penalties.
5. Replace lawyers, MLROs, compliance officers, or counsel.
6. Claim regulator approval or partnership.
7. Make fully automated legal or compliance decisions.

## Full Standard Disclaimer
1. StatuteProof reports are generated from monitored official-source records and are provided for information and compliance review support only.
2. StatuteProof reports do not constitute legal advice, regulatory advice, compliance certification, or a legal opinion.
3. StatuteProof does not replace qualified legal counsel, compliance professionals, MLROs, or other professional advisers.
4. StatuteProof does not guarantee compliance, prevent fines, or certify that all regulatory updates have been captured.
5. Source monitoring may be affected by publication delays, website changes, PDF formatting, access limits, or source structure changes.
6. Users should verify official source material directly and review evidence records, hashes, timestamps, and diffs before relying on a report.
7. Users should consult qualified legal or compliance professionals before making regulatory, filing, operational, or customer decisions based on a report.

## Short Outreach Disclaimer
For monitoring information only. Not legal advice and not a guarantee of compliance.

## Claim Risk Levels
High risk examples:
- We guarantee compliance.
- Official partner of a regulator.
- Replace your legal team.

Medium risk examples:
- Stay compliant automatically.
- No need to check regulators manually.
- We handle compliance monitoring for you.

Low risk examples:
- Supports compliance review.
- Evidence-backed monitoring brief.
- Shows last checked timestamp.

## Forbidden Phrase Reference
See `docs/forbidden-phrases-reference.md` for the full phrase and implication-risk table.

## Before/After Rewrite Examples
| Before | After |
|---|---|
| We guarantee you will stay compliant. | We support compliance review with official-source monitoring and evidence-backed briefs. |
| Never miss a VARA update again. | Monitor selected VARA source pages on a defined schedule with visible last-checked timestamps. |
| Our AI lawyer reviews regulations. | StatuteProof drafts monitoring briefs for review by qualified legal or compliance professionals. |
| Replace manual legal review. | Reduce manual source-checking work while keeping human legal and compliance review. |
| Officially approved monitoring. | Monitoring public official sources; not affiliated with or endorsed by regulators. |
| Avoid fines with our platform. | Identify relevant official-source updates earlier for internal review. |
| Automated compliance decisions. | Structured monitoring outputs for human compliance decision-making. |
| Sleep easy knowing you are compliant. | Maintain a clearer evidence trail for selected official-source updates. |

## Human Review Required When
1. High-risk update.
2. Confidence below 0.70.
3. Customer-facing brief.
4. Website claim.
5. Important prospect outreach.
6. Legal-sensitive copy.
7. Regulator name appears in a claim.
8. Deadline, penalty, or sanction language appears.
9. Evidence is missing or incomplete.
10. Ambiguous obligation scope.
11. Source status is QUALITY_DROP or SOURCE_STRUCTURE_CHANGED.

## Agent Responsibilities
Legal Language Agent: detects unsafe phrases, implication risk, replacements, disclaimers.
QA / Critic Agent: final ship/no-ship review.
Risk + Brief Pipeline Agent: keeps briefs evidence-backed and not legal advice.
Outreach Writer Agent: writes short, safe messages and routes to review.
Evidence Trail Agent: blocks briefs without evidence.
