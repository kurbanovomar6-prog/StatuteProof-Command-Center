# Chosen Family Upgrade Audit: DFSA

Date: 2026-06-21

This audit records the DFSA proof-backed upgrade pass. It is an operator
artifact, not a customer coverage claim.

## Verdict

- Family: DFSA
- Score before: 6.5/10
- Score after: 6.9/10
- Upgrade type: canonical evidence + exact alert linkage
- Source IDs changed: none
- Source counts changed: no
- New proof-backed canonical evidence: yes
- Customer delivery approved: no

## Current DFSA Source Layer

Scorecard source truth remains:

- Total DFSA rows: 44
- Fresh-alert eligible: 16
- Evidence-library: 28
- Candidate: 0
- Remediation: 0
- Active source-health blockers: 0

High-signal fresh-alert examples:

| Source ID | Mode | Status | Alert eligible | Baseline | Last status |
| --- | --- | --- | --- | --- | --- |
| `AE-dfsa-financial-crime-mlro-letters` | fresh_alert | active | true | 3/2 | MONITOR_OK |
| `AE-dfsa-aml-rulebook-module` | fresh_alert | active | true | 5/2 | MONITOR_OK |
| `AE-dfsa-rulebook-thomsonreuters` | fresh_alert | active | true | 3/2 | MONITOR_OK |
| `AE-dfsa-consultation-current` | fresh_alert | active | true | 3/2 | MONITOR_OK |
| `AE-dfsa-enforcement-decisions-current` | fresh_alert | active | true | 3/2 | MONITOR_OK |
| `AE-dfsa-regulatory-actions-current` | fresh_alert | active | true | 3/2 | MONITOR_OK |
| `AE-dfsa-rulebook-official` | fresh_alert | active | true | 2/2 | MONITOR_OK |
| `AE-dfsa-what-we-do-enforcement-1a837c50` | fresh_alert | active | true | 4/2 | MONITOR_OK |

## Target Source Run

Chosen run:

| Field | Value |
| --- | --- |
| Source ID | `AE-dfsa-financial-crime-mlro-letters` |
| Run ID | `intake-20260619T151120Z` |
| Official URL | `https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/financial-crime-prevention-notices-and-mlro-letters` |
| Adapter | `dfsa_notice_listing` |
| Change status | CHANGED |
| Extraction quality | GOOD |
| Diff quality | GOOD |
| Normalized hash | `56fa887024611a571e07858caa055c3cb35e4735127a890d9b4ecbad951c7107` |
| Proof path | `data/source_snapshots/2026-06-19/AE/AE-dfsa-financial-crime-mlro-letters/intake-20260619T151120Z/proof.json` |
| Diff path | `data/source_snapshots/2026-06-19/AE/AE-dfsa-financial-crime-mlro-letters/intake-20260619T151120Z/diff.md` |

Prior baseline runs:

| Run ID | Timestamp | Status | Quality | Normalized hash prefix |
| --- | --- | --- | --- | --- |
| `intake-20260615T114242Z` | 2026-06-15T11:42:42Z | FIRST_SEEN | GOOD | `7fefb2b0aeb6d6b2` |
| `intake-20260615T114257Z` | 2026-06-15T11:42:57Z | UNCHANGED | GOOD | `7fefb2b0aeb6d6b2` |
| `intake-20260619T151120Z` | 2026-06-19T15:11:20Z | CHANGED | GOOD | `56fa887024611a57` |

## Canonical Evidence Created

Command:

```bash
python3 tools/generate_canonical_evidence.py \
  --source-id AE-dfsa-financial-crime-mlro-letters \
  --run-id intake-20260619T151120Z \
  --status CHANGED \
  --limit 1 \
  --write \
  --report-path /tmp/dfsa_mlro_canonical_write.md
```

Result:

- `created=1`
- Record ID:
  `evr_AE-dfsa-financial-crime-mlro-letters_intake-20260619T151120Z`
- Integrity: `hash_verified=true`, `integrity_status=VERIFIED`
- Review status: pending
- Human review required: true

Validation:

```bash
python3 tools/validate_canonical_evidence_records.py
```

Result:

- `records=13`
- All records complete, hash-verifiable, and stored in the canonical evidence tree.

## Alert Linkage

Linked alert file:

`product/regradar/data/alert_queue/20260619T151120-AE-dfsa-financial-crime-mlro-letters-intake-2-8f0d.json`

Link added:

```json
"evidence_record_id": "evr_AE-dfsa-financial-crime-mlro-letters_intake-20260619T151120Z"
```

Digest validation:

```bash
python3 tools/generate_verified_monitoring_digest.py
python3 tools/validate_verified_monitoring_digest.py
```

Result:

- Alerts total: 39
- Pending review: 39
- Canonical evidence linked: 3
- Source health blocked: 0
- Customer delivery: false

## Brief Gate Status

The new DFSA evidence record is not brief-input eligible.

Verification:

```bash
PYTHONPATH=product/regradar python3 - <<'PY'
from pathlib import Path
from app.evidence_records import build_risk_brief_inputs
root = Path("/Users/kurbnovomar/StatuteProof-Command-Center/product/regradar")
rid = "evr_AE-dfsa-financial-crime-mlro-letters_intake-20260619T151120Z"
print(build_risk_brief_inputs(rid, base_dir=root))
PY
```

Result:

- `eligible=False`
- Blocked reason:
  `Canonical evidence record review_status must be approved or not_required before customer brief use; got 'pending'.`

## Blockers To 7/10

- Founder/operator must review the DFSA MLRO evidence record and approve,
  reject, or block it through the canonical evidence review path.
- Remaining DFSA queued alerts still need canonical evidence or explicit noise
  classification.
- DFSA family wording must remain "selected DFSA monitoring", not complete
  DFSA coverage.

## Blockers To 8/10

- Multiple DFSA high-signal examples need canonical evidence and human review.
- Parser confidence needs a larger reviewed sample across rulebook, MLRO,
  enforcement, and consultation sources.
- A customer/design-partner pilot must review at least one DFSA brief before
  any customer-delivery trust claim.

## Safe Claim

Selected DFSA official-source monitoring includes MLRO/financial-crime,
rulebook, consultation, enforcement, and regulatory-action sources with proof
and baseline controls.

## Forbidden Claim

Do not claim complete DFSA coverage, complete DIFC/DFSA legal coverage,
guaranteed compliance, legal advice, perfect parsing, never-miss updates, or
evidence-backed customer delivery.

