# Source Health Customer Messaging Report

Date: 2026-06-16

## Implemented Customer-Safe Messages

Source-health messages are centralized in `app.source_health_timeline.source_health_customer_message`.

Current wording:

- `MONITOR_OK`: “Monitoring is active and the latest extraction passed quality checks.”
- `QUALITY_DROP`: “Extraction quality changed. Manual review may be required.”
- `HASH_DRIFT`: “Content fingerprint changed between runs. Review required before customer alert.”
- `REMEDIATION_REQUIRED`: “This source is under extraction remediation and is not currently treated as monitoring-ready.”
- `FAILED`: “The latest source check failed. Manual review may be required.”
- `ACCESS_BLOCKED`: “The source could not be accessed publicly during the latest check. Manual review may be required.”
- `NO_HISTORY`: “No monitoring history has been recorded yet.”

## Legal Boundary

The messaging avoids:

- legal advice;
- guaranteed compliance;
- “never miss” claims;
- perfect parsing claims;
- regulator certification implication.

## Product Rationale

Hash drift is framed as source-health/review risk, not as a customer-ready regulatory alert. This reduces false confidence and keeps the MLRO workflow evidence-first.
