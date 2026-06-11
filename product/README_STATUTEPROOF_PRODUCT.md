# StatuteProof / Regradar — Product Code

This folder contains the actual StatuteProof / Regradar product code, copied from the development workspace at:

```
/Users/kurbnovomar/документы/obsidian/ruflo/regrada/
```

The original source folder is unchanged. This is a working copy for Command Center integration.

---

## Folder Structure

```
product/
├── regradar/          ← Main Python source package (all business logic here)
│   ├── app/           ← Core modules: monitor, pipeline, diff, proof, risk, ai_brief, alert_review...
│   ├── data/          ← Source runs, snapshots, source configs, evidence samples
│   ├── docs/          ← Deployment docs, runbooks, source onboarding rules
│   ├── reports/       ← Coverage and quality reports
│   ├── scripts/       ← Utility scripts (validate_uae_sources, run_cbuae_rulebook_watch...)
│   ├── tests/         ← Test suite
│   ├── tools/         ← Developer tools
│   ├── web/           ← Frontend (React, src/App.jsx)
│   ├── run.py         ← CLI entry point
│   ├── sources.json   ← Source registry
│   └── requirements.txt
├── Dockerfile         ← Production container
├── Makefile           ← Build and run commands
├── railway.toml       ← Railway deployment config
├── requirements.txt   ← Root-level Python dependencies
├── main.py            ← Server entry point
├── app.py             ← Streamlit application entry
└── ...
```

---

## Relationship to Command Center Root

The Command Center root (`../`) is the **operating layer**:
- `../CLAUDE.md` — instructions for this workspace
- `../TOOL_ROUTER.md` — which agent or skill to use for each task
- `../.claude/agents/` — 10 specialized Claude Code subagents
- `../skills/` — review skills invoked by trigger words
- `../workflows/` — step-by-step operating workflows
- `../docs/` — operating documentation

This `product/` folder is the **implementation layer**: the real code that runs, fetches, normalizes, and stores evidence.

---

## How to Work on Implementation Tasks

1. Read `../TOOL_ROUTER.md` first to choose the right agent.
2. Inspect `product/regradar/app/` for the relevant module.
3. Use the Source Monitor Agent for monitoring code changes.
4. Use the Evidence Trail Agent for evidence file structure.
5. Use the Risk + Brief Pipeline Agent for brief generation logic.
6. Use the Legal Language Agent and QA / Critic for any customer-facing text.

---

## First Real Task

Before building anything new, complete the evidence dry run:

1. Verify a real UAE source URL is accessible (VARA, CBUAE, or DFSA).
2. Create a source spec using `../prompts/source-spec-prompt.md`.
3. Run fetch → normalize → hash using `product/regradar/run.py`.
4. Confirm the evidence record saves with all required fields.
5. Produce a SAMPLE / FAKE brief using `../prompts/sample-brief-prompt.md`.

See `../workflows/03-evidence-dry-run.md` for the full procedure.

---

## What Is Not Here (Excluded for Safety)

| Excluded | Reason |
|----------|--------|
| `regradar/.env` | Real API keys (ANTHROPIC_API_KEY, etc.) — never commit |
| `regrada.db` | Production SQLite database with live data |
| `regrada.db-wal`, `regrada.db-shm` | Live WAL files — open during active runs |
| `telegram_clients.json` | Real client data (names, Telegram chat IDs) |
| `keys/` | Credential files |
| `logs/` | Application logs that may contain API responses |
| `ruvector.db`, `agentdb.rvf` | Production vector databases |

**Never commit secrets.** Add a real `.env` file locally if running the product, but keep it in `.gitignore`.

---

## .env Setup (Local Only)

Copy the example and fill in real values locally — never commit:

```bash
cp regradar/.env.example regradar/.env
# Edit regradar/.env with real ANTHROPIC_API_KEY etc.
```
