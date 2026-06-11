# Workflow 04: Monitoring to Brief

**When:** A CHANGED or QUALITY_DROP event is detected in a production run.
**Agents:** Risk + Brief Pipeline, Legal Language Agent, QA / Critic.
**Skills:** `#risk-brief-review`.
**Output:** A reviewed, labeled brief ready for founder decision on delivery.

---

## Prerequisites

- [ ] Evidence record with `change_status: CHANGED` or `QUALITY_DROP`
- [ ] `evidence_record_status: complete`
- [ ] `proof_quality: GOOD` or `LIMITED` (not INCOMPLETE)

---

## Step 1 — Retrieve the Evidence Record

```bash
grep "[SOURCE_ID]" data/source_runs/source_runs.jsonl | grep '"change_status": "CHANGED"' | tail -1
```

Note: `run_id`, `evidence_record_id`, `diff_path`, `normalized_hash`, `previous_hash`.

---

## Step 2 — Read the Diff

```bash
cat data/source_snapshots/[date]/AE/[SOURCE_ID]/[RUN_ID]/diff.md
```

Understand what changed before asking the Risk + Brief Pipeline to score it.

---

## Step 3 — Run Risk Scoring

Use `docs/risk-scoring-guide.md` and ask the Risk + Brief Pipeline Agent:
- Provide the diff excerpt
- Provide the evidence_record_id and status
- Ask for risk_level, risk_score, score_components, and confidence

Rule: do not assign a score without a diff excerpt. Evidence first.

---

## Step 4 — Draft the Brief

Use `prompts/sample-brief-prompt.md` as the format reference.
If this is a real (not sample) brief:
- Remove SAMPLE / FAKE labels
- Use the real evidence_record_id
- Use the real diff excerpt
- Include the full standard disclaimer

---

## Step 5 — Review with `#risk-brief-review`

```
#risk-brief-review
Brief path: [path to draft brief]
evidence_record_id: [ID]
evidence_record_status: complete
Risk score: [0-100]
Confidence: [0.00-1.00]
Human review required: [yes/no — reason]
```

If the skill returns NO-SHIP: stop. Do not proceed until required fixes are made.

---

## Step 6 — Legal Language Review

Route to Legal Language Agent.
Use `prompts/legal-safe-copy-review-prompt.md`.
Focus on: disclaimer completeness, affected entity language, any guarantee implications.

---

## Step 7 — QA Gate

QA / Critic Agent reviews the final draft.
Confirm: SHIP or NO-SHIP.

---

## Step 8 — Founder Decision

Bring the brief and QA decision to the founder.
The founder decides: deliver / hold / request additional review.

Automatic hold conditions (do not deliver without founder decision):
- risk_score >= 70
- confidence < 0.70
- any enforcement or penalty language in the diff
- affected entities unclear

---

## Step 9 — Delivery

If approved: deliver with the full standard disclaimer.
Log delivery date, recipient, and evidence_record_id.
