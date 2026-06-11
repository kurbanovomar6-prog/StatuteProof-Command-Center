# Workflow 03: Evidence Dry Run

**When:** Before enabling any new source for production monitoring.
**Agent:** Evidence Trail Agent.
**Output:** Evidence record with PASS status and a verified proof.json.

---

## Prerequisites

- [ ] Source spec exists in `sources.json` with `enabled: false`
- [ ] Official URL verified in browser manually
- [ ] regradar pipeline is running (`python3 -m app.pipeline` or scheduler)

---

## Step 1 — Trigger One Run for This Source

From the `regradar/` directory:

```bash
python3 -m app.pipeline --source [SOURCE_ID] --dry-run
```

Or if the pipeline runs on a schedule, temporarily enable the source and wait for the next cycle.

---

## Step 2 — Check Run Status

```bash
grep "[SOURCE_ID]" data/source_runs/source_runs.jsonl | tail -1 | python3 -m json.tool
```

Expected: `change_status` is FIRST_SEEN, UNCHANGED, or CHANGED.
Not expected at this stage: FAILED or QUALITY_DROP (investigate if either appears).

---

## Step 3 — Run Evidence Dry Run Prompt

Use `prompts/evidence-dry-run-prompt.md` with the Evidence Trail Agent.
Provide the run_id and source_id.

---

## Step 4 — Verify proof.json

```bash
cat data/source_snapshots/[date]/AE/[SOURCE_ID]/[RUN_ID]/proof.json | python3 -m json.tool
```

Check:
- [ ] `disclaimer` field present and matches standard StatuteProof disclaimer
- [ ] `proof_quality` is GOOD or LIMITED (INCOMPLETE → investigate)
- [ ] `official_url` matches the source spec
- [ ] `raw_hash` is 64-character hex string
- [ ] `normalized_hash` is 64-character hex string
- [ ] `run_timestamp` is correct

---

## Step 5 — Run Before-Evidence-Brief Checklist

`checklists/before-evidence-brief.md` — verify all fields before marking PASS.

---

## Step 6 — Record PASS or BLOCK

PASS: evidence_record_status is complete, proof_quality is GOOD or LIMITED, all required fields present.
BLOCK: any required field missing, FAILED status, proof_quality INCOMPLETE, or disclaimer missing.

If BLOCK: investigate the cause before enabling the source.

---

## Step 7 — Enable Source (PASS Only)

After PASS:
1. Set `"enabled": true` in `sources.json`
2. The source will now run on the standard monitoring schedule
3. Record the first real run_id in `STATUTEPROOF_CONTEXT.md`

---

## Invariant to Verify

FAILED ≠ UNCHANGED: run a deliberate FAILED test.

```python
# In regradar/ directory
python3 -c "
from app.source_runs import classify_change
failed = {'access_status': 'failed', 'extraction_quality': 'FAILED'}
result = classify_change(failed, None)
assert result == 'FAILED', f'Expected FAILED, got {result}'
print('INVARIANT: FAILED ≠ UNCHANGED — CONFIRMED')
"
```

This must return CONFIRMED before any source is added to production.
