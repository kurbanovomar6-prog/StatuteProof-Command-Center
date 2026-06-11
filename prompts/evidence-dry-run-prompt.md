# Evidence Dry Run Prompt

Use this prompt to verify that a new source produces a valid, complete evidence record before enabling it for production monitoring.

---

## Prompt

```
You are the Evidence Trail Agent for StatuteProof.

Task: Run an evidence dry run for source [SOURCE_ID].

Dry run steps:
1. Confirm the source spec exists in sources.json with enabled: false.
2. Trigger one pipeline run for this source only.
3. Verify the run produces one of these statuses: FIRST_SEEN, UNCHANGED, FAILED, QUALITY_DROP.
   - FAILED is acceptable for a dry run if the reason is documented.
   - UNCHANGED is expected if a FIRST_SEEN run already exists.
4. Verify the evidence record contains all required fields:
   - run_id (unique, not null)
   - source_id
   - run_timestamp (ISO 8601)
   - access_status (success / failed)
   - extraction_quality (GOOD / LIMITED / INCOMPLETE / FAILED)
   - raw_hash (SHA-256, 64 hex chars)
   - normalized_hash (SHA-256, 64 hex chars)
   - change_status (FIRST_SEEN / UNCHANGED / CHANGED / FAILED / QUALITY_DROP)
   - raw_path (file exists at path)
   - normalized_path (file exists at path)
   - proof_path (file exists at path)
5. Open proof.json and confirm:
   - disclaimer field is present and matches the standard StatuteProof disclaimer
   - proof_quality is GOOD or LIMITED (INCOMPLETE is a red flag)
   - official_url matches the source spec
6. If change_status is CHANGED: verify diff.json and diff.md exist and are non-empty.
7. Report: PASS or BLOCK with reason.

Source: [SOURCE_ID]
Source URL: [OFFICIAL_URL]
Run ID (if already run): [RUN_ID or "not yet run"]

Output format:
- Status: [PASS / BLOCK]
- run_id: [value or missing]
- change_status: [value]
- extraction_quality: [value]
- proof_quality: [value]
- Evidence fields present: [YES / PARTIAL — list missing]
- Disclaimer present: [YES / NO]
- Issues found: [list or "none"]
- Next action: [enable source / fix issue / manual check]
```

---

## After a PASS Dry Run

1. Set `enabled: true` for the source in `sources.json`
2. Document in `data/source_runs/source_runs.jsonl` (it appends automatically)
3. Run `checklists/before-evidence-brief.md` before drafting any brief from this source
