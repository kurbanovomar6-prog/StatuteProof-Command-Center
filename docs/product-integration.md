# Product Integration Guide

## Where the Code Lives

The StatuteProof / Regradar product code is in:

```
product/
```

This is a working copy of the real product codebase. The Command Center root (`/`) is the operating layer — agents, skills, workflows, docs. The `product/` folder is the implementation layer — the code that actually runs.

---

## Two-Layer Structure

```
StatuteProof-Command-Center/
├── product/                     ← Product code (Python, frontend, DB config)
│   ├── regradar/                ← Main source package
│   └── ...deployment files
│
├── .claude/agents/              ← 10 agent subagent definitions
├── skills/                      ← Review skills (#triggers)
├── workflows/                   ← Step-by-step operating procedures
├── docs/                        ← Operating documentation (including this file)
├── prompts/                     ← Prompt templates
├── checklists/                  ← Pre-action checklists
├── CLAUDE.md                    ← Workspace instructions
└── TOOL_ROUTER.md               ← Agent/skill routing guide
```

**Operating layer** (root): Planning, review, agents, skills, briefs, outreach, legal safety.  
**Implementation layer** (`product/`): Fetch, normalize, hash, diff, risk score, brief, dispatch.

---

## Agent → Code Mapping

When an agent works on the product, these are the relevant code locations:

| Agent | Primary code location |
|-------|----------------------|
| Source Monitor | `product/regradar/app/monitor.py`, `scraper.py`, `extractors.py` |
| Evidence Trail | `product/regradar/app/proof.py`, `data/source_runs/`, `data/source_snapshots/` |
| Risk + Brief Pipeline | `product/regradar/app/risk.py`, `pipeline.py`, `ai_brief.py`, `diff.py` |
| Legal Language | `product/regradar/app/alert_review.py`, `report.py`, `weekly_brief.py` |
| QA / Critic | `product/regradar/tests/`, `product/regradar/app/alert_review.py` |
| Code Architect | `product/regradar/app/api.py`, `web/`, `product/Dockerfile`, `product/Makefile` |

---

## Week 1 Path — What to Build First

Complete these five steps in order before doing anything else:

**Step 1 — Verify official source URL**
Open the target UAE regulatory URL in a browser and confirm:
- Page loads without bot block
- Content is regulatory (circulars, regulations, rulebook)
- URL is stable and official

**Step 2 — Create source spec**
Use `prompts/source-spec-prompt.md`. Specify: source_id, official_url, fetch_method, jurisdiction, category, content_type. Check `checklists/before-source-spec.md` before proceeding.

**Step 3 — Run fetch → normalize → hash**
Run `product/regradar/run.py` against the spec. Confirm:
- `access_status: success`
- `extraction_quality: GOOD` (not FAILED or INCOMPLETE)
- `content_hash` is a 64-char SHA-256
- `change_status: FIRST_SEEN`

**Step 4 — Create evidence record**
Verify the evidence record saves to `product/regradar/data/source_runs/source_runs.jsonl` with all required fields. Check `docs/evidence-record-spec.md` for the required schema.

**Step 5 — Produce SAMPLE / FAKE brief**
Use `prompts/sample-brief-prompt.md`. Label it `SAMPLE / FAKE`. Run through `#risk-brief-review` before sharing with anyone.

---

## What Not to Build Yet

| Do not build | Why |
|-------------|-----|
| Dashboard rewrite | No live evidence data yet — wait for evidence dry run |
| All UAE regulators at once | Validate one source end-to-end first |
| Auto-send client briefs | Legal review + QA required; human in loop for first delivery |
| Legal advice engine | Forbidden by legal safety system (see `docs/legal-safety-system.md`) |
| Runtime agent swarm | Command Center uses document workflows, not runtime orchestration |
| Public API | No auth layer has been verified |

---

## Running the Product

```bash
# Install dependencies
cd product
pip install -r requirements.txt
# (or)
pip install -r regradar/requirements.txt

# Set up .env (local only — never commit)
cp regradar/.env.example regradar/.env
# Fill in ANTHROPIC_API_KEY, etc.

# Run a source fetch
cd regradar
python run.py fetch --source-id AE-dubai-financial-services-authority-dfsa

# Run full pipeline
python run.py pipeline --source-id AE-difc-laws-and-regulations
```

See `product/regradar/docs/deployment_architecture.md` for production deployment.

---

## Safety Rules for Product Work

- Never commit `.env` files or credentials.
- Never commit `regrada.db` or any live database.
- Never commit `telegram_clients.json` (real client data).
- Label all example output `SAMPLE / FAKE`.
- Run `#risk-brief-review` before any customer-facing brief.
- Run `#legal-language` review before any customer-facing copy.
- Check `checklists/before-evidence-brief.md` before producing any brief.
