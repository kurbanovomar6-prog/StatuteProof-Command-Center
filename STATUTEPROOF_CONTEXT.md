# StatuteProof — Product and Pipeline Context

## What StatuteProof Is

StatuteProof is an official-source regulatory monitoring service for UAE financial regulators (VARA, CBUAE, DFSA, ADGM, MoF UAE, UAE FIU, DIFC, Ministry of Economy, UAE Legislation Portal).

It:
- Fetches selected official regulatory source pages on a defined schedule
- Detects text changes using SHA-256 hashes of normalized content
- Stores cryptographic evidence records (raw snapshot, normalized text, hash, diff, timestamp, run ID)
- Drafts evidence-backed compliance intelligence briefs for human review

It does **not**:
- Provide legal advice
- Certify compliance
- Guarantee that all regulatory updates are captured
- Replace legal counsel, MLROs, or compliance officers
- Make automated compliance decisions

## Pipeline Architecture (regradar codebase)

The product pipeline is in this workspace under:

`product/regradar/`

Older external-path references may exist in archived reports, but current parser,
Source Lab, evidence, API, and frontend work should inspect `product/regradar`
first.

### Pipeline Flow

```
fetch → normalize → hash → compare → diff/baseline → rule-based risk → AI analysis (optional) → save → alert
```

Key invariants:
- FAILED ≠ UNCHANGED (programmatically enforced in `classify_change()`)
- LLM is never in the change-detection path (only used for optional brief drafting after classification)
- Evidence record appended atomically to JSONL before any alert is sent
- Confidence set to "low" for HIGH/MEDIUM scores without AI validation

### Run Status Taxonomy

| Status | Meaning |
|--------|---------|
| FIRST_SEEN | Source fetched successfully for the first time |
| UNCHANGED | Hashes match previous run |
| CHANGED | Hashes differ; diff computed |
| FAILED | Fetch or extraction failed |
| QUALITY_DROP | Extraction quality degraded vs previous run |

Note: SOURCE_STRUCTURE_CHANGED is not yet implemented.

### Data Locations (regradar)

- Run records: `data/source_runs/source_runs.jsonl`
- Snapshots: `data/source_snapshots/{date}/{market}/{source_id}/{run_id}/`
  - `raw.txt`, `normalized.txt`, `metadata.json`, `proof.json`, `diff.json`, `diff.md`
- Active source registry: `product/regradar/sources.json`

## UAE Source Readiness

Use `product/regradar/sources.json` and the latest readiness report as the
canonical source of truth before making customer-facing claims.

As of this context refresh, `sources.json` has 13 enabled UAE sources with a
strict readiness split of 9 registry-active sources and 4 remediation sources:

- DFSA Rulebook / rules and standards
- DFSA Regulatory Notices
- UAE FIU Homepage
- DIFC Laws and Regulations

Do not describe DFSA, UAE FIU Homepage, or DIFC Laws as customer-visible ready
until live Source Lab checks, proof artifacts, and QA/legal gates support that
claim.

## Evidence Record (as of 2026-06-11)

- 132 real run records in JSONL
- VARA: 11 runs, consistently GOOD quality, ~36,591 normalized chars
- Last confirmed real data: VARA AML/CFT circular text from vara.ae

## Frontend Status

The React 18 frontend (`product/regradar/web/`) has a real app shell and Source
Lab UI, but some screens still use demo/mock data. Customer-facing source
readiness labels must be checked against API/registry truth before demo use.

## Audit Findings (2026-06-11)

Score: historical 7.5/10. Current parser/source-readiness claims must be
validated against the latest audit reports and source registry before use.

Critical open items:
1. Dashboard/source data (HIGH) — verify `GET /api/sources/health` and app
   source tables do not overclaim readiness before demo
2. `.env` in `regradar/` (HIGH) — verify not committed, verify contents
3. Source readiness count consistency (HIGH) — align public/app copy with
   `sources.json` and latest evidence-readiness report
4. SOURCE_STRUCTURE_CHANGED not implemented (MEDIUM)

Full audit: `/Users/kurbnovomar/AI-Company-Agent-OS/STATUTEPROOF_PROJECT_AUDIT.md`

## ICP (Ideal Customer Profile)

UAE-regulated financial service firm required to monitor VARA/CBUAE/DFSA updates:
- Role: CCO, MLRO, Head of Compliance, in-house Counsel
- Company size: 10-150 people
- Obligation: Must track regulator publications; current process is manual
- Pain: Missing updates, delayed awareness, no audit trail

See `docs/icp-definition.md` in AI-Company-Agent-OS for the full profile.

## Positioning

> "Official-source regulatory monitoring with evidence-backed compliance briefs."

Target: UAE financial compliance professionals who need to monitor VARA, CBUAE, and DFSA publications without missing updates or fabricating audit trails.
