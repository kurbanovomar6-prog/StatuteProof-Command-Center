# Source Health Timeline Model Spec

Date: 2026-06-16

## Principle

Timeline events must be derived from recorded StatuteProof artifacts only. The system must never invent monitoring history, review history, proof paths, or customer actions.

## Event Shape

Each event should include:

- `event_id`
- `source_id`
- `source_name`
- `event_type`
- `timestamp`
- `source_url`
- `proof_path`
- `raw_hash`
- `normalized_hash`
- `diff_path`
- `quality_score`
- `extraction_quality`
- `source_health_status`
- `remediation_reason`
- `assessment_id`
- `reviewer`
- `assessment_impact_level`
- `assessment_note_preview`
- `customer_safe_message`
- `internal_debug_message`

## Event Types

Supported event types:

- `MONITOR_RUN`
- `EVIDENCE_SAVED`
- `BASELINE_COMPLETE`
- `HASH_STABLE`
- `HASH_DRIFT`
- `SOURCE_HEALTH_OK`
- `QUALITY_DROP`
- `REMEDIATION_STARTED`
- `REMEDIATION_RESOLVED`
- `ACKNOWLEDGED`
- `ASSESSED`
- `EXPORT_CREATED`

`EXPORT_CREATED` is reserved for future export metadata if export creation records are persisted. The current MVP can show export action availability without fabricating past export events.

## Source Health Status Mapping

- `MONITOR_OK`: latest extraction passed quality checks and is not a source-health warning.
- `QUALITY_DROP`: extraction quality or normalized content length dropped.
- `HASH_DRIFT`: normalized hash changed between recorded runs; review required before customer alert.
- `REMEDIATION_REQUIRED`: source registry says the source is under extraction remediation.
- `FAILED` / `ACCESS_BLOCKED`: recorded run failed or access was restricted.
- `NO_HISTORY`: no recorded run exists.

## Customer-Safe Messages

- `MONITOR_OK`: “Monitoring is active and the latest extraction passed quality checks.”
- `QUALITY_DROP`: “Extraction quality changed. Manual review may be required.”
- `HASH_DRIFT`: “Content fingerprint changed between runs. Review required before customer alert.”
- `REMEDIATION_REQUIRED`: “This source is under extraction remediation and is not currently treated as monitoring-ready.”
- `NO_HISTORY`: “No monitoring history has been recorded yet.”

## Empty State

If no run or assessment data exists, return:

- an empty `events` array;
- `source_health_status = NO_HISTORY`;
- customer-safe message: “No monitoring history has been recorded yet.”

Do not backfill or simulate old events.

## Review History

Evidence review history should include:

- evidence created from the saved source run;
- proof/hash fields;
- source-health status at record time;
- linked Acknowledge & Assess events;
- customer-safe no-assessment message when no assessment exists.

## Legal Boundary

Timeline and review history support internal compliance review. They do not determine legal obligations, certify compliance, or replace qualified legal/compliance advice.
