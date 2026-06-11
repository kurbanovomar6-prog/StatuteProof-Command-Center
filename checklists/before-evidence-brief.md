# Checklist: Before Evidence Brief

Complete all items before drafting any brief from an evidence record.

## Evidence Record Completeness

- [ ] evidence_record_id exists and is unique
- [ ] evidence_record_status is complete (not pending, not partial)
- [ ] run_id is present
- [ ] run_timestamp is present (ISO 8601)
- [ ] source_id and source_name are present
- [ ] official_url is present and matches the source spec
- [ ] change_status is CHANGED or QUALITY_DROP (only draft briefs for these statuses)
- [ ] access_status is success (not failed)
- [ ] extraction_quality is GOOD or LIMITED (not INCOMPLETE or FAILED)

## Hash Verification

- [ ] raw_hash is a 64-character SHA-256 hex string
- [ ] normalized_hash is a 64-character SHA-256 hex string
- [ ] previous_hash exists (for CHANGED status)
- [ ] raw_path file exists on disk
- [ ] normalized_path file exists on disk

## Proof File

- [ ] proof.json exists at the snapshot path
- [ ] proof_quality is GOOD or LIMITED
- [ ] disclaimer field is present in proof.json
- [ ] limitations_notes explains any proof_quality: LIMITED issues

## Diff File

- [ ] diff.json exists and is non-empty
- [ ] diff.md exists and shows readable paragraph-level changes
- [ ] diff excerpt has been read and understood before risk scoring

## Brief Safety Gate

- [ ] Risk score is assigned only after reading the diff excerpt
- [ ] confidence value is stated numerically (not as a word)
- [ ] If confidence < 0.70: human review flag is present
- [ ] If risk_score >= 70: human review flag is present
- [ ] If enforcement or penalty language appears in diff: human review flag is present
- [ ] Affected entities are drawn from source text, not inferred from general knowledge
- [ ] Ambiguity notes document any unclear scope, dates, or entities

## Before Delivery

- [ ] Brief reviewed by `#risk-brief-review` skill
- [ ] Legal Language Agent reviewed all customer-facing copy
- [ ] QA / Critic approved
- [ ] Full standard disclaimer is present in the brief
- [ ] SAMPLE / FAKE label if this is an example brief (not real)
