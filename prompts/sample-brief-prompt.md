# Sample Brief Prompt

Use this prompt to generate a SAMPLE / FAKE StatuteProof brief for testing the brief format and pipeline before using real evidence.

**All output from this prompt must be labeled SAMPLE / FAKE. Never use as a real regulatory alert.**

---

## Prompt

```
You are the Risk + Brief Pipeline Agent for StatuteProof.

Task: Generate a SAMPLE / FAKE compliance intelligence brief for testing purposes.

IMPORTANT: This brief must be labeled SAMPLE / FAKE at the top. It uses invented regulatory content. Do not use as a real alert.

Brief parameters:
- Source: SAMPLE VARA
- Regulator: VARA (Virtual Assets Regulatory Authority)
- Country: UAE
- Change type: [fee schedule update / new circular / guidance amendment / deadline extension]
- Risk level: [LOW / MEDIUM / HIGH]
- Audience: [CCO / MLRO / Head of Compliance]

Generate a brief with this structure:

---
SAMPLE / FAKE — FOR TESTING ONLY. NOT A REAL REGULATORY ALERT.

Source: SAMPLE VARA — [page description]
Run ID: SAMPLE-[date]-001
Detected: [YYYY-MM-DDTHH:MM:SSZ]
Change status: CHANGED
Evidence record: ER-SAMPLE-[date]-001 (status: complete)

## Summary
[2-3 sentences: what changed, where, when it was detected]

## Risk Assessment
Risk level: [LOW / MEDIUM / HIGH]
Risk score: [0-100]
Score components:
- Source authority: [score, reason]
- Change materiality: [score, reason]
- Operational impact: [score, reason]
- Enforcement language: [score, reason]

Confidence: [0.50-0.95]
Human review required: [YES / NO — reason]

## Affected Entities
[List entities named in source text or mark as unclear]
Note: Affected entity scope is drawn from the SAMPLE source excerpt only.

## Key Changes
[Bullet list of changed clauses — use SAMPLE language only]

## Ambiguity Notes
[Flag any scope, date, or entity ambiguity]

## Evidence Trail
Evidence record ID: ER-SAMPLE-[date]-001
Evidence record status: complete
Raw hash: [64-char SAMPLE SHA-256]
Normalized hash: [64-char SAMPLE SHA-256]
Diff excerpt: [SAMPLE diff text showing added/removed lines]
Snapshot path: SAMPLE/data/source_snapshots/[date]/AE/SAMPLE-VARA/SAMPLE-run-001/

## Recommended Actions
[2-3 specific actions for a CCO or MLRO, using "may want to review" language, not instructions]

## Disclaimer
StatuteProof reports are generated from monitored official-source records and are provided for information and compliance review support only. StatuteProof reports do not constitute legal advice, regulatory advice, compliance certification, or a legal opinion. StatuteProof does not replace qualified legal counsel, compliance professionals, MLROs, or other professional advisers. StatuteProof does not guarantee compliance, prevent fines, or certify that all regulatory updates have been captured. Source monitoring may be affected by publication delays, website changes, PDF formatting, access limits, or source structure changes. Users should verify official source material directly and review evidence records, hashes, timestamps, and diffs before relying on a report. Users should consult qualified legal or compliance professionals before making regulatory, filing, operational, or customer decisions based on a report.

---
SAMPLE / FAKE — END OF BRIEF
```

---

## After Generating

1. Run through `#risk-brief-review` skill before sharing with anyone.
2. Confirm SAMPLE / FAKE label is visible near the top.
3. Do not remove the disclaimer.
4. Use `examples/sample-risk-brief.md` as a reference for format.
