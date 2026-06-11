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

The live pipeline is at `/Users/kurbnovomar/документы/obsidian/ruflo/regrada/regradar/`.
This StatuteProof-Command-Center folder is an **operating and tooling workspace only** — it does not contain the pipeline code.

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
- Active sources: `sources.json` (9 UAE sources enabled)

## Active UAE Sources

| Source | URL | Status |
|--------|-----|--------|
| VARA | https://www.vara.ae/ | VERIFIED ACTIVE |
| CBUAE | https://www.centralbank.ae/ | VERIFIED ACTIVE |
| DFSA | https://www.dfsa.ae/ | VERIFIED ACTIVE |
| ADGM FSRA | (via adgm.com) | Active |
| MoF UAE | (via mof.gov.ae) | Active |
| UAE FIU | (via amlcft.ae) | Active |
| UAE Legislation Portal | (via uaelegislation.gov.ae) | Active |
| DIFC Laws | (via difclaw.difc.ae) | Active |
| Ministry of Economy | (via moec.gov.ae) | Active |

## Evidence Record (as of 2026-06-11)

- 132 real run records in JSONL
- VARA: 11 runs, consistently GOOD quality, ~36,591 normalized chars
- Last confirmed real data: VARA AML/CFT circular text from vara.ae

## Frontend Status

The React 18 frontend (`regradar/web/`) currently uses 100% mock data.
`sourceHealthRows` in `mockData.js` shows all 9 UAE sources as PASS/active — this is fabricated.
Dashboard must be connected to live data before any customer-facing demo.

## Audit Findings (2026-06-11)

Score: 7.5/10. Status: Ready for manual MVP.

Critical open items:
1. Dashboard mock data (HIGH) — connect `GET /api/sources/health` before demo
2. `.env` in `regradar/` (HIGH) — verify not committed, verify contents
3. No git in `regradar/` (HIGH) — initialize before sharing pipeline
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
