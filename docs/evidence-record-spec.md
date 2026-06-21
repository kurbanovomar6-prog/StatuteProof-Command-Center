# Evidence Record Spec

## Purpose
The evidence record is the trust layer of StatuteProof.
It proves which official source was checked, when it was checked, what content was captured, what changed, and whether the evidence is complete enough for a brief.
The evidence record supports compliance review but does not provide legal advice.
No evidence record means no compliance brief.

## Canonical Storage Path Structure
```text
evidence/
  {regulator_slug}/
    {source_id}/
      {run_id}/
        raw.html                    # required if HTML source
        raw.pdf                     # required if PDF source
        current.normalized.txt       # required
        previous.normalized.txt      # required if not FIRST_SEEN
        diff.txt                    # required if CHANGED
        snapshot.html               # required
        metadata.json               # required
        evidence-record.json        # required
```

## Path Rules
1. `regulator_slug` must be lowercase and stable, for example `vara`, `cbuae`, `dfsa`, `adgm-fsra`.
2. `source_id` must be stable across runs and must not include timestamps.
3. `run_id` must include source_id and UTC timestamp.
4. Store raw content exactly as fetched or captured.
5. Store normalized text after deterministic cleaning.
6. Store previous normalized text for every non-FIRST_SEEN comparison.
7. Store diff only when status is CHANGED.
8. Never overwrite files inside a completed run folder.

## Full Field Reference Table
| Field | Required | Description | Example |
|---|---|---|---|
| schema_version | yes | Schema version for record format | 2.0 |
| record_id | yes | Stable evidence record ID | evr_sample_fake_001 |
| record_status | yes | pending, complete, integrity_error, blocked | complete |
| source.source_id | yes | Source monitor ID | vara-guidance |
| source.regulator | yes | Regulator name | VARA |
| source.official_url | yes | Official source URL | https://example.invalid/vara |
| source.source_name | yes | Human-readable source name | SAMPLE VARA page |
| run.run_id | yes | Monitoring run ID | run_vara_20260611_0001 |
| run.timestamp | yes | UTC timestamp | 2026-06-11T00:00:00Z |
| run.status | yes | One of 6 run statuses | CHANGED |
| content.previous_hash | conditional | Previous normalized SHA-256 | sha256:... |
| content.current_hash | yes | Current normalized SHA-256 | sha256:... |
| content.raw_content_path | yes | Raw file path | evidence/.../raw.html |
| content.normalized_current_path | yes | Current normalized path | evidence/.../current.normalized.txt |
| content.normalized_previous_path | conditional | Previous normalized path | evidence/.../previous.normalized.txt |
| change.diff_path | conditional | Diff path for CHANGED | evidence/.../diff.txt |
| change.summary | yes | Short evidence-only summary | SAMPLE / FAKE summary |
| change.lines_added | yes | Added lines count | 4 |
| change.lines_removed | yes | Removed lines count | 0 |
| files.snapshot_path | yes | Snapshot path | evidence/.../snapshot.html |
| files.raw_path | yes | Raw path | evidence/.../raw.html |
| files.normalized_path | yes | Normalized path | evidence/.../current.normalized.txt |
| files.previous_path | conditional | Previous normalized path | evidence/.../previous.normalized.txt |
| files.diff_path | conditional | Diff path | evidence/.../diff.txt |
| integrity.hash_verified | yes | Recomputed hash matches | true |
| integrity.integrity_status | yes | VERIFIED, FAILED, NOT_APPLICABLE | VERIFIED |
| integrity.verified_at | yes | UTC verification timestamp | 2026-06-11T00:02:00Z |
| review.human_review_required | yes | Review gate flag | true |
| review.review_status | yes | not_required, pending, approved, blocked | pending |
| review.review_reason | yes | Reason for review state | High risk sample |

## Complete Status Criteria
A record may be marked complete only when all conditions are true:
1. Official URL is present.
2. Source ID and regulator are present.
3. Run ID and timestamp are present.
4. Run status is not FAILED or QUALITY_DROP.
5. Raw content path exists.
6. Current normalized text path exists.
7. Current normalized hash is valid `sha256:` plus 64 lowercase hex characters.
8. Hash is recomputed from normalized text and matches record.
9. Snapshot exists.
10. Metadata exists.
11. Previous normalized text exists for non-FIRST_SEEN runs.
12. Diff exists for CHANGED runs.
13. Review fields are populated.
14. SAMPLE / FAKE data is clearly separated from production evidence.

## Immutability Rules
After `record_status: complete`, do not edit the record in place.
Allowed after completion:
- Add a separate review note referencing the record ID.
- Add a separate append-only review decision record referencing the record ID and evidence-record hash.
- Add a separate correction record with a new record ID.
- Add downstream brief ID in a separate linked artifact.
- Mark a later superseding record as authoritative.
Not allowed after completion:
- Changing hashes.
- Replacing raw files.
- Replacing normalized text.
- Rewriting diff.
- Deleting the run folder.
- Mixing sample files with production files.

## Append-Only Review Journal

Canonical evidence records are immutable after completion. Human approval,
rejection, or blocked status must be stored outside `evidence-record.json`.

Default local review store:

```text
data/evidence_reviews/canonical_evidence_reviews.jsonl
```

Each review row must include:

1. review ID.
2. evidence record ID.
3. evidence record path.
4. SHA-256 hash of the reviewed `evidence-record.json`.
5. decision: `approved`, `rejected`, or `blocked`.
6. reviewer.
7. note.
8. reviewed timestamp.
9. `customer_delivery_approved: false`.

An external review decision may make a pending canonical record eligible for
draft brief inputs only when the latest decision is `approved` and the
underlying evidence record still validates. It does not approve customer
delivery.

## SAMPLE vs Production Separation Rule
SAMPLE / FAKE evidence must never live in the same folder tree as production customer evidence.
Sample examples may use `examples/` or `evidence/sample/` only.
Production evidence must use regulator and source IDs based on verified source configuration.
Any file containing fictional data must say SAMPLE / FAKE at the top or in the record field.

## Retention Guidance
- Keep raw snapshots indefinitely during MVP.
- Keep normalized text indefinitely during MVP.
- Keep diffs indefinitely during MVP.
- Do not delete failed run logs; failures are part of source health history.
- Use immutable backup before any migration.
- Define customer-specific retention only after legal/commercial review.

## Client-Facing Proof Format
Use these six fields for a simple customer proof view:
1. Source name.
2. Official URL.
3. Detection timestamp.
4. Evidence record ID.
5. Current normalized hash.
6. Diff path or summary reference.

## Handoff Package To Risk + Brief Pipeline
```markdown
Evidence record ID:
Official URL:
Regulator:
Run status:
Current hash:
Previous hash:
Diff path:
Raw snapshot path:
Normalized current path:
Integrity status:
Human review required:
Ambiguity notes:
```

## Common Failure Modes
1. Missing raw snapshot.
2. Missing previous normalized file for comparison.
3. Hash in JSON does not match file content.
4. Diff path is missing for CHANGED run.
5. FAILED run is promoted to complete.
6. SAMPLE / FAKE data appears in production folder.
7. Complete record is edited after the fact.
8. Source URL is copied from a non-official page.
9. Timestamp lacks timezone.
10. Review fields are empty.
11. Evidence record references files that do not exist.
12. Brief is generated while record is pending.
