# Migration Product Folder Audit

**Date:** 2026-06-11
**Purpose:** Locate the real StatuteProof/Regradar product code before any migration.
**Action taken:** Read-only search. No files moved, copied, or edited.

---

## 1. Candidate Folder Paths

| # | Path | Type |
|---|------|------|
| A | `/Users/kurbnovomar/документы/obsidian/ruflo/regrada/` | Project root (deployment config + code) |
| B | `/Users/kurbnovomar/документы/obsidian/ruflo/regrada/regradar/` | Main Python package (the code itself) |
| C | `/Users/kurbnovomar/документы/obsidian/rufло/regrada/regradar/web/` | Frontend only (Cyrillic-folder copy) |
| D | `/Users/kurbnovomar/документы/obsidian/ruflo/deploy_monitor/` | Telegram monitor deployment stub |
| E | `/Users/kurbnovomar/StatuteProof-Command-Center/` | Command center workspace (docs only, no code) |
| F | `/Users/kurbnovomar/AI-Company-Agent-OS/` | Agent OS (no product code) |

---

## 2. Evidence For Each Candidate

### A — `/Users/kurbnovomar/документы/obsidian/ruflo/regrada/`

**Project root.** Contains deployment and infrastructure layer:

| File / Dir | Significance |
|-----------|-------------|
| `Dockerfile` | Production container definition |
| `Makefile` | Build commands |
| `Procfile` | Railway/Heroku process definitions |
| `railway.toml` | Railway deployment config |
| `docker-compose.yml` | Local + production orchestration |
| `requirements.txt` | Python dependencies |
| `main.py` | Entry point (`RegRadar — entry point. Page logic lives in src/pages/`) |
| `app.py`, `mvp_core.py` | Earlier/parallel application entry points |
| `celery_app.py`, `scheduler_workers.py` | Background task workers |
| `database.py` | DB connection layer |
| `regrada.db`, `regrada.db-shm`, `regrada.db-wal` | Live SQLite database with WAL files |
| `regradar/` | The full Python source package (Candidate B) |
| `snapshots/` | Additional snapshot storage |
| `app/` | Streamlit pages (sidebar, styles, pages/) |
| `logs/`, `keys/`, `scripts/`, `services/`, `src/`, `tests/` | Supporting directories |
| `README.md` | "RegRadar Enterprise — Autonomous Regulatory Intelligence Platform" |

**Verdict:** This is the deployable project root. Everything needed to run and deploy the product is here.

---

### B — `/Users/kurbnovomar/документы/obsidian/ruflo/regrada/regradar/`

**Main Python source package.** The actual product logic lives here.

**2601 Python files.** Key app/ modules:

| Module | Purpose |
|--------|---------|
| `monitor.py` | Core source monitoring |
| `pipeline.py` | End-to-end fetch→normalize→hash→compare pipeline |
| `diff.py`, `chunk_diff.py` | Text diff engine |
| `proof.py` | Evidence record generation |
| `risk.py` | Risk scoring |
| `alert_review.py`, `alert_routing.py` | Alert review and routing logic |
| `ai.py`, `ai_brief.py` | AI brief drafting (Anthropic) |
| `scraper.py`, `extractors.py`, `document_extractor.py` | Source fetching |
| `text_normalization.py` | Text normalization |
| `source_runs.py`, `sources.py` | Source lifecycle management |
| `weekly_brief.py` | Weekly brief generation |
| `telegram.py`, `telegram_clients.py` | Telegram delivery |
| `auth.py`, `api.py` | Authentication and API layer |

**UAE-specific adapters** in `app/adapters/`:
- `uae_cbuae_rulebook.py` — CBUAE Rulebook watch
- `uae_fsra_circulars.py` — FSRA Circulars

**Real run records** — `data/source_runs/source_runs.jsonl`:
- 132 run records
- Contains VARA, CBUAE, DFSA, ADGM, UAE Ministry of Finance, UAE Ministry of Economy, FTA, UAEFIU, SCA, UAE Legislation Portal, DIFC Laws, UAE e-Laws Portal
- Records in `{"access_status": ..., "change_status": ..., "content_hash": ..., "run_id": ..., "source_id": ...}` format — matching the evidence record spec

**Real source snapshots** — `data/source_snapshots/2026-05-30/AE/`:
- 12 UAE regulators with dated run folders
- Format: `AE-{source-id}/AE-{timestamp}-{hash}/`

**Alert reviews** — `data/alert_reviews/reviews.jsonl` exists

**Documentation** — `docs/`:
- `deployment_architecture.md`, `vps_deployment_runbook.md`
- `cbuae_rulebook_watch_scheduler.md`
- `first_pilot_readiness_checklist.md`, `production_deployment_checklist.md`
- `sales_readiness.md`

**Coverage reports** — `reports/`:
- `ae_source_pack_2026-05-24.md`, `bh_validated_source_pack_2026-05-27.md`
- Coverage JSON files dated 2026-05-23 through 2026-05-29
- `cbuae_rulebook_proof/` directory

**Frontend** — `web/src/App.jsx` (React)

**Sources config** — `sources.json` (top-level source registry)

**requirements.txt includes:**
```
requests, python-dotenv, beautifulsoup4, lxml, playwright, trafilatura,
readability-lxml, anthropic, pypdf, python-docx, openpyxl
```

**Verdict:** This is the real product code. All 7 product signals present: source monitoring code, evidence records, run history, snapshots, UAE source adapters, alert review, deployment docs.

---

### C — `/Users/kurbnovomar/документы/obsidian/rufло/regrada/regradar/web/`

**Frontend only.** The Cyrillic-named `rufло` (vs Latin `ruflo`) folder contains only `web/` → `src/App.jsx`. No backend, no data, no run records. This is likely a deployment artifact or an older partial copy.

**Verdict:** NOT the product. Frontend fragment only.

---

### D — `/Users/kurbnovomar/документы/obsidian/ruflo/deploy_monitor/`

**Telegram monitoring stub.** Contains:
- `Dockerfile`
- `requirements.txt`
- `tg_monitor.py` — single Telegram monitor script
- `ruvector.db`

No source monitoring pipeline, no evidence records, no UAE sources.

**Verdict:** NOT the product. A standalone Telegram monitor deployment helper.

---

### E — `/Users/kurbnovomar/StatuteProof-Command-Center/`

**This workspace** — documentation, agents, skills, workflows, prompts, checklists. No Python source code, no database, no run records.

**Verdict:** NOT the product. Command center / documentation layer.

---

### F — `/Users/kurbnovomar/AI-Company-Agent-OS/`

**Agent OS** — Claude Code agent definitions and orchestration framework. No product code.

**Verdict:** NOT the product.

---

## 3. Most Likely Real Product

**`/Users/kurbnovomar/документы/obsidian/ruflo/regrada/`** is the product root.

**`/Users/kurbnovomar/документы/obsidian/ruflo/regrada/regradar/`** is the Python source package inside it.

The two are one product. The `regrada/` folder is where you run the product from (Makefile, Dockerfile, requirements.txt, database). The `regradar/` subfolder is the importable Python package with all the business logic.

---

## 4. Folders That Are NOT the Product

| Folder | Why Not |
|--------|---------|
| `/Users/kurbnovomar/документы/obsidian/rufло/regrada/regradar/web/` | Frontend fragment only, no backend |
| `/Users/kurbnovomar/документы/obsidian/ruflo/deploy_monitor/` | Single Telegram script, not the full pipeline |
| `/Users/kurbnovomar/StatuteProof-Command-Center/` | Docs/agents workspace, no code |
| `/Users/kurbnovomar/AI-Company-Agent-OS/` | Agent OS framework, no product code |
| `/Users/kurbnovomar/Desktop/polymarket-weather-monitor/` | Different product (Polymarket) |
| `/Users/kurbnovomar/polymarket-weather-bot/` | Different product (Polymarket) |

---

## 5. Risks

| Risk | Details |
|------|---------|
| **Live database open** | `regrada.db`, `regrada.db-shm`, `regrada.db-wal` exist at the project root. The `.db-wal` file means SQLite WAL mode is active — the database may have uncommitted transactions. Do not copy during an active write. |
| **132 run records in JSONL** | `source_runs.jsonl` is a live append-only file. Do not copy mid-run. |
| **`keys/` directory** | Contains credentials/keys. Must not be committed or copied to a public repo. |
| **`.env` files likely present** | Not verified (user instruction: do not touch git). Verify before any migration that `.env`, `keys/`, and any credential files are excluded from git. |
| **Two entry points exist** | Both `main.py` (newer, clean) and `app.py`/`mvp_core.py` (older) are present at the root. Before migration, confirm which is the active entry point in production. |
| **Cyrillic vs Latin folder names** | Both `ruflo` (Latin) and `rufло` (Cyrillic-letter `о`) exist in the same parent. On case-insensitive filesystems, these could collide. On migration, use only the Latin `ruflo` folder. |
| **regrada.db in the repo** | If this SQLite file is tracked in git, it must be removed from tracking before any migration push. |

---

## 6. Recommended Source Folder

**For migration, use this folder as the source root:**

```
/Users/kurbnovomar/документы/obsidian/ruflo/regrada/
```

This is the deployable project root. It contains the Dockerfile, Makefile, requirements.txt, database, and the `regradar/` Python package. Everything needed to run and deploy StatuteProof/Regradar is inside this single folder.

**The Python source package specifically:**
```
/Users/kurbnovomar/документы/obsidian/ruflo/regrada/regradar/
```

**Do not use:**
- The Cyrillic `rufло` folder
- `deploy_monitor/` (incomplete)
- Any BACKUP folder

**Before any migration run:**
1. Confirm `keys/` is gitignored
2. Confirm `.env` files are gitignored
3. Confirm `regrada.db` is gitignored
4. Confirm no active pipeline run is writing to `source_runs.jsonl`
5. Decide if the older entry points (`app.py`, `mvp_core.py`) are still in use or can be excluded
