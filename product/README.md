# RegRadar Enterprise
### Autonomous Regulatory Intelligence Platform for CIS Financial Markets

> Real-time detection, versioned delta analysis, and personalised Telegram dispatch
> for regulatory documents across Russia · Kazakhstan · Azerbaijan · Belarus · Uzbekistan.

---

## Table of Contents

1. [System Overview & Architecture](#1--system-overview--architecture)
2. [Database Schema & Data Lifecycle](#2--database-schema--data-lifecycle)
3. [Local Installation & Testing Workspace](#3--local-installation--testing-workspace)
4. [Production Infrastructure & Railway Blueprint](#4--production-infrastructure--railway-blueprint)

---

## 1. 🌐 System Overview & Architecture

RegRadar is a multi-tier autonomous compliance intelligence platform. It continuously monitors regulatory portals across five CIS jurisdictions, detects document changes at the byte level, extracts structured compliance signals using a large language model, and delivers personalised alerts to subscribed compliance teams via Telegram — all without human intervention.

### Tier Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           INGESTION TIER                                    │
│                                                                             │
│   Regulator Portal       Playwright Stealth Scraper     Telegram Monitor   │
│   (CBR, NBK, CBAR…)  ──► (camoufox fingerprint)    +   (channel watcher)  │
│                                │                                            │
│                         PDF / HTML extraction                               │
│                         pytesseract OCR fallback                            │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │  raw { source_url, title, summary, jurisdiction }
                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        VERSIONING TIER                                      │
│                                                                             │
│   RegulationRepository.upsert_raw_versioned()                               │
│                                                                             │
│   SHA-256( summary ) ──► compare with latest RegulationVersion.summary_hash│
│                                                                             │
│   ┌── NEW record ──────────────────────────────────────────────────────┐   │
│   │   INSERT regulations + RegulationVersion(version=1)                │   │
│   │   → VersionedUpsertResult(saved=True, is_update=False)             │   │
│   └────────────────────────────────────────────────────────────────────┘   │
│   ┌── IDENTICAL hash ──────────────────────────────────────────────────┐   │
│   │   No-op. Return saved=False. Zero LLM calls. Zero DB writes.       │   │
│   └────────────────────────────────────────────────────────────────────┘   │
│   ┌── CHANGED hash ────────────────────────────────────────────────────┐   │
│   │   UPDATE regulations.summary                                        │   │
│   │   INSERT RegulationVersion(version=N, delta_json=NULL)             │   │
│   │   → VersionedUpsertResult(saved=True, is_update=True)              │   │
│   │   → dispatch analyze_delta_task.delay(version_id, old_summary)     │   │
│   └────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │  version_id + old_summary (Celery message)
                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ANALYSIS TIER  (Celery "reports" queue)              │
│                                                                             │
│   analyze_delta_task                                                        │
│       │                                                                     │
│       ├─ instructor.from_openai(OpenAI())                                   │
│       │      model: gpt-4o-mini                                             │
│       │      response_model: DeltaAnalysis(BaseModel)                       │
│       │        ├─ critical_changes: list[str]  (≤5, ≤120 chars each)        │
│       │        ├─ impact_level: "HIGH" | "MEDIUM" | "LOW"                   │
│       │        └─ business_action_required: str  (exactly 2 sentences)      │
│       │                                                                     │
│       └─ repo.update_version_delta(version_id, delta)                      │
│              → RegulationVersion.delta_json  = delta.model_dump_json()      │
│              → RegulationVersion.impact_level = "HIGH" | …                 │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │  daily cron (09:00 UTC, Celery beat)
                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DISPATCH TIER  (Celery "reports" queue)               │
│                                                                             │
│   send_scheduled_alerts_task                                                │
│       │                                                                     │
│       ├─ get_recent_with_versions(since=now−25h)  ← JOIN regulations +     │
│       │                                              regulation_versions    │
│       ├─ list_active()  ← alert_subscriptions                              │
│       │                                                                     │
│       │  Per subscriber:                                                    │
│       │    filter by jurisdictions   ("RU,KZ" → jur_filter list)           │
│       │    filter by min_risk_level  (_RISK_ORDER threshold comparison)     │
│       │                                                                     │
│       │    frequency == "instant" → format_delta_alert() per regulation    │
│       │    frequency == "daily"   → format_digest()  (up to 6 items)       │
│       │                                                                     │
│       └─ httpx.post(Telegram Bot API /sendMessage)   [sync, no async]      │
│              parse_mode: HTML  ·  disable_web_page_preview: True           │
└─────────────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION TIER                                   │
│                                                                             │
│   NiceGUI dark-theme SPA  (main.py)                                         │
│     ├─ Regulations feed       AG Grid + rowClicked → Version History dialog │
│     ├─ Analytics dashboard    YTD metrics, jurisdiction breakdown           │
│     ├─ AI Scraper             universal_scrape_url_task.delay()             │
│     ├─ Smart Alerts settings  SubscriptionRepository.subscribe()            │
│     └─ Version History modal  timeline · SHA-256 fingerprint · delta pills  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Rationale |
|---|---|
| SHA-256 of `summary` text, not full document | Detects any material edit in O(1) without re-fetching or re-parsing the PDF |
| `instructor` + Pydantic `BaseModel` for LLM output | Eliminates JSON-parsing glue code; `max_retries=1` prevents runaway API spend on malformed completions |
| Synchronous `httpx.post` for Telegram dispatch | Celery prefork workers are OS processes; async coroutines would require a per-worker event loop bridge with no throughput benefit |
| `exec` in `entrypoint.sh` | Shell is replaced by the child process so Railway's SIGTERM reaches Python/Celery directly, enabling graceful shutdown |
| Migrations run in `web` process only | Prevents concurrent `ALTER TABLE` races; Railway's healthcheck ordering guarantees workers start after the web tier is healthy |

---

## 2. 🗄️ Database Schema & Data Lifecycle

### Core Tables

#### `regulations`

Primary store of every detected regulatory document.

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER PK` | Auto-increment |
| `title` | `TEXT` | Up to 500 chars (truncated on ingest) |
| `jurisdiction` | `VARCHAR(5)` | `RU` · `KZ` · `AZ` · `BY` · `UZ` |
| `publication_date` | `VARCHAR(10)` | ISO-8601 string |
| `effective_date` | `VARCHAR(10)` | ISO-8601 string |
| `summary` | `TEXT` | Current (latest) version of the extracted summary |
| `critical_level` | `VARCHAR(20)` | `LOW` · `MEDIUM` · `HIGH` · `CRITICAL` |
| `source_url` | `TEXT` | Original document URL |
| `url_hash` | `VARCHAR(64) UNIQUE` | SHA-256 of `source_url` — primary deduplication key |
| `confidence` | `FLOAT` | LLM extraction confidence 0.0–1.0 |
| `status` | `VARCHAR(20)` | `ACTIVE` · `HUMAN_REVIEW` · `PROCESSING` |
| `source_type` | `VARCHAR(20)` | `WEB` · `TELEGRAM` · `RSS` |
| `ai_analysis` | `TEXT` | Full Claude/GPT enrichment JSON |
| `urgency_score` | `INTEGER` | 1–100 urgency signal |
| `action_plan` | `TEXT` | AI-generated compliance checklist |
| `fines_usd` | `INTEGER` | Maximum penalty extracted from text (USD equivalent) |
| `time_to_discovery_sec` | `INTEGER` | Seconds from publication to first scrape |
| `compute_cost_usd` | `FLOAT` | Total AI API spend for this document |
| `extracted_at` | `DATETIME` | Timestamp of first ingestion |

**Composite index:** `(extracted_at, jurisdiction, critical_level)` — used by `list_recent()` and all dashboard queries.

---

#### `regulation_versions`

Immutable append-only log of every detected content change.

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER PK` | Auto-increment |
| `regulation_id` | `INTEGER FK` | References `regulations.id` |
| `version_number` | `INTEGER` | Monotonically increasing per `regulation_id`; starts at 1 |
| `summary_hash` | `VARCHAR(64)` | Full SHA-256 of the version's `summary` text |
| `summary` | `TEXT` | Snapshot of the summary at this version |
| `delta_json` | `TEXT` | Serialised `DeltaAnalysis` (populated by `analyze_delta_task`) |
| `impact_level` | `VARCHAR(20)` | Denormalised from `delta_json` for fast filtering without deserialisation |
| `created_at` | `DATETIME` | Timestamp of version creation |

**Index:** `(regulation_id, version_number)` — used by `get_versions()` and the Version History modal.

**The 12-character fingerprint** displayed in the UI is `summary_hash[:12]`. This is sufficient for human identification of a version — collision probability at 12 hex chars is 1 in 2⁴⁸ ≈ 281 trillion — while keeping the Version History modal readable.

---

#### `alert_subscriptions`

Per-subscriber Telegram notification preferences.

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER PK` | Auto-increment |
| `chat_id` | `VARCHAR(50) UNIQUE` | Telegram chat ID (user or group) |
| `jurisdictions` | `TEXT` | Comma-separated filter: `"RU,KZ"`. Empty string = all jurisdictions |
| `frequency` | `VARCHAR(20)` | `instant` · `daily` · `weekly` |
| `min_risk_level` | `VARCHAR(20)` | Minimum impact threshold: `LOW` · `MEDIUM` · `HIGH` · `CRITICAL` |
| `is_active` | `BOOLEAN` | Soft-delete flag |
| `created_at` | `DATETIME` | Subscription creation timestamp |
| `last_notified_at` | `DATETIME` | Last successful dispatch timestamp |

---

### `upsert_raw_versioned()` — Preventing Extraction Bloat

The versioning strategy eliminates two categories of waste that plague naive regulatory scrapers:

**Database write bloat** — Portals routinely re-publish unchanged documents (corrected metadata, re-signed PDFs, CDN cache invalidation). Without content hashing, every re-scrape would insert a duplicate row and trigger an expensive LLM call.

**LLM token bloat** — `analyze_delta_task` sends two full summaries to GPT-4o-mini (up to 5,000 tokens per call). At scale across five jurisdictions and dozens of active regulators, unchecked LLM calls make the platform economically unviable.

The resolution path for every ingested document:

```
upsert_raw_versioned(data)
│
├── url_hash not in DB?
│     → INSERT regulation + RegulationVersion(v=1)
│     → return VersionedUpsertResult(saved=True,  is_update=False)
│        ↳ no LLM call — no "old" version to diff against
│
├── url_hash exists AND SHA-256(summary) == latest version hash?
│     → no writes, no LLM call
│     → return VersionedUpsertResult(saved=False, is_update=False)
│        ↳ zero cost — identical content, skip entirely
│
└── url_hash exists AND SHA-256(summary) ≠ latest version hash?
      → UPDATE regulations.summary
      → INSERT RegulationVersion(v=N, delta_json=NULL)
      → return VersionedUpsertResult(saved=True, is_update=True, version_id=N)
         ↳ caller dispatches analyze_delta_task.delay(version_id, old_summary)
            → exactly one LLM call; result stored in RegulationVersion.delta_json
```

LLM spend is strictly proportional to actual regulatory change, not scraping frequency.

---

## 3. 🛠️ Local Installation & Testing Workspace

### Prerequisites

| Tool | Minimum version | Purpose |
|---|---|---|
| Docker | 24.x | Container runtime |
| Docker Compose | v2 (plugin) | Multi-service orchestration |
| Python | 3.12 | Host-side test runner (`make test-local`) |
| GNU Make | 3.81 | Task runner |

---

### First-Time Setup

**1. Clone and configure environment**

```bash
git clone https://github.com/your-org/regrada.git
cd regrada
cp .env.example .env
# Edit .env — set OPENAI_API_KEY, TELEGRAM_BOT_TOKEN at minimum
```

**2. Build the Docker image**

```bash
make build
```

The build runs in two stages: a `builder` stage compiles all Python C-extensions (psycopg2, lxml, Pillow); the `runtime` stage installs Playwright Chromium with its system dependencies via `playwright install --with-deps chromium`. Total image size is approximately 1.8 GB.

**3. Start the full stack**

```bash
make up
```

This starts five services defined in `docker-compose.yml`:

| Service | Container | Role |
|---|---|---|
| `redis-cache` | `regrada_redis` | Celery broker + rate-limit store |
| `web-api` | `regrada_api` | NiceGUI SPA on port 8080 |
| `celery-worker` | `regrada_worker` | Async task processor (4 concurrent subprocesses) |
| `celery-beat` | `regrada_beat` | Cron scheduler (PersistentScheduler) |
| `flower` | `regrada_flower` | Celery monitoring UI on port 5555 |

The `web-api` container runs `entrypoint.sh web`, which executes `init_db()` + `ensure_schema_migrations()` before starting NiceGUI. Workers only start after the web healthcheck passes (`/api/v1/health` → HTTP 200).

**4. Open the dashboard**

```
http://localhost:8080
```

---

### Running the Test Suite

#### Inside Docker — recommended

Runs inside the production image, exactly matching the Railway environment:

```bash
make test
```

Internally executes:

```bash
docker compose build
docker compose run --rm --no-deps \
    -e DATABASE_URL="sqlite:///:memory:" \
    -e OPENAI_API_KEY="sk-test-placeholder" \
    -e TELEGRAM_BOT_TOKEN="0000000000:test-token" \
    -e SECRET_KEY="ci-test-secret" \
    -e REGRADA_API_KEY="ci-test-api-key" \
    web-api \
    python -m pytest tests/ -v --tb=short
```

`--no-deps` skips Redis and all other services. All 28 tests mock external I/O at the module level — no live infrastructure is required.

#### On the host — faster iteration

```bash
pip install pytest pytest-mock pytest-cov
make test-local
```

#### With coverage report — CI pipelines

```bash
make test-ci
```

Produces a terminal coverage breakdown and a JUnit XML file at `/tmp/junit-regrada.xml` compatible with GitHub Actions, GitLab CI, and Railway's test reporter.

---

### Expected Output

```
========================= test session starts ==========================
collected 28 items

tests/test_compliance_engine.py::TestUpsertRawVersioned::test_new_record_returns_saved_true          PASSED
tests/test_compliance_engine.py::TestUpsertRawVersioned::test_identical_summary_skips_version        PASSED
tests/test_compliance_engine.py::TestUpsertRawVersioned::test_changed_summary_triggers_update        PASSED
tests/test_compliance_engine.py::TestUpsertRawVersioned::test_version_numbers_increment_sequentially PASSED
tests/test_compliance_engine.py::TestUpsertRawVersioned::test_get_versions_returns_12char_fingerprint PASSED
tests/test_compliance_engine.py::TestUpsertRawVersioned::test_update_version_delta_persists_delta_json PASSED
tests/test_compliance_engine.py::TestSubscriptionRepository::test_new_subscription_returns_true      PASSED
tests/test_compliance_engine.py::TestSubscriptionRepository::test_update_existing_returns_false      PASSED
tests/test_compliance_engine.py::TestSubscriptionRepository::test_list_active_excludes_inactive      PASSED
tests/test_compliance_engine.py::TestSubscriptionRepository::test_update_last_notified_sets_timestamp PASSED
tests/test_compliance_engine.py::TestSubscriptionRepository::test_jurisdiction_and_risk_persisted    PASSED
tests/test_compliance_engine.py::TestSubscriptionRepository::test_empty_chat_ids_update_does_not_crash PASSED
tests/test_compliance_engine.py::TestDeltaAnalyzerUnit::test_returns_none_when_old_empty            PASSED
tests/test_compliance_engine.py::TestDeltaAnalyzerUnit::test_returns_none_when_new_empty            PASSED
tests/test_compliance_engine.py::TestDeltaAnalyzerUnit::test_returns_none_on_identical_summaries    PASSED
tests/test_compliance_engine.py::TestDeltaAnalyzerUnit::test_format_delta_alert_contains_impact_level PASSED
tests/test_compliance_engine.py::TestDeltaAnalyzerUnit::test_format_delta_alert_medium_impact       PASSED
tests/test_compliance_engine.py::TestDeltaAnalyzerUnit::test_format_delta_alert_no_url_when_empty   PASSED
tests/test_compliance_engine.py::TestDeltaAnalyzerUnit::test_format_digest_includes_jurisdiction_and_level PASSED
tests/test_compliance_engine.py::TestDeltaAnalyzerUnit::test_format_digest_dashboard_link_absent_when_empty PASSED
tests/test_compliance_engine.py::TestCeleryTaskDispatch::test_analyze_delta_task_ok_path            PASSED
tests/test_compliance_engine.py::TestCeleryTaskDispatch::test_analyze_delta_task_version_not_found  PASSED
tests/test_compliance_engine.py::TestCeleryTaskDispatch::test_analyze_delta_task_no_delta_when_llm_returns_none PASSED
tests/test_compliance_engine.py::TestCeleryTaskDispatch::test_send_scheduled_alerts_task_daily_digest PASSED
tests/test_compliance_engine.py::TestCeleryTaskDispatch::test_send_scheduled_alerts_task_risk_threshold_filters_low PASSED
tests/test_compliance_engine.py::TestCeleryTaskDispatch::test_send_scheduled_alerts_task_instant_sends_delta_alert PASSED
tests/test_compliance_engine.py::TestCeleryTaskDispatch::test_send_scheduled_alerts_task_jurisdiction_filter PASSED
tests/test_compliance_engine.py::TestCeleryTaskDispatch::test_send_scheduled_alerts_task_no_subscribers PASSED

========================== 28 passed in 3.41s ==========================
```

---

### Pre-Push Gate

Run before every `git push` or Railway deploy trigger:

```bash
make pre-push
```

Builds the image from scratch and executes the full test suite. A clean pass prints:

```
✓  Build OK
✓  All tests passed
✓  Safe to git push / trigger Railway deploy
```

A non-zero pytest exit code aborts immediately — no broken images reach Railway.

---

### Development Commands Reference

```bash
make build     # build Docker image
make up        # start full stack (redis + web + worker + beat + flower)
make down      # stop and remove all containers
make restart   # hot-reload web-api container after source changes
make logs      # tail web-api and celery-worker logs
make shell     # open bash inside the running web-api container
make test      # full test suite inside Docker (recommended)
make test-ci   # test + JUnit XML + coverage report
make test-local # test on host, no Docker
make pre-push  # build + test gate
make help      # list all targets
```

---

## 4. 🚀 Production Infrastructure & Railway Blueprint

### Multi-Stage Dockerfile

```
┌─────────────────────────────────────────────────────────┐
│  Stage 1: builder  (python:3.12-slim-bookworm)          │
│                                                         │
│  apt: build-essential gcc g++ libffi-dev libssl-dev     │
│       libpq-dev libpoppler-cpp-dev                      │
│                                                         │
│  pip install --prefix=/install -r requirements.txt      │
│  (compiles psycopg2, lxml, Pillow C-extensions)         │
│                                                         │
│  Discarded entirely from the final image.               │
└────────────────────┬────────────────────────────────────┘
                     │  COPY --from=builder /install /usr/local
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Stage 2: runtime  (python:3.12-slim-bookworm)          │
│                                                         │
│  apt: tesseract-ocr tesseract-ocr-{rus,eng}             │
│       poppler-utils fonts-liberation fonts-noto         │
│       libmagic1 ca-certificates curl                    │
│                                                         │
│  groupadd/useradd regrada  (UID/GID 1001, no-login)     │
│                                                         │
│  COPY --chown=regrada:regrada . /app                    │
│  chmod +x /app/entrypoint.sh                            │
│                                                         │
│  playwright install --with-deps chromium                │
│  chown -R regrada:regrada /app/.playwright-browsers     │
│                                                         │
│  USER regrada      ← never runs as root at runtime      │
│  ENV PLAYWRIGHT_BROWSERS_PATH=/app/.playwright-browsers │
│  EXPOSE 8080                                            │
│  HEALTHCHECK /api/v1/health  (start-period 90s)         │
└─────────────────────────────────────────────────────────┘
```

**Why `playwright install --with-deps` rather than manual `apt-get`?**
Playwright maintains its own manifest of system libraries (`libnss3`, `libatk-bridge`, `libgbm`, etc.) that evolves with each browser revision. Delegating to `--with-deps` means the Dockerfile stays correct across Playwright upgrades without any manual library tracking.

**Why `chown` in the same `RUN` layer as `playwright install`?**
Each `RUN` creates a new image layer. A separate `RUN chown` after install would reference all browser binary files again in the diff, approximately doubling the stored size of those layers. Merging both operations into one layer keeps the image compact.

---

### `entrypoint.sh` Bootstrap Flow

```
Container starts (Railway / docker compose)
      │
      ▼
bash entrypoint.sh  [web | worker | beat]
      │
      ├─ PROCESS = "web"
      │      python: init_db()                   ← CREATE TABLE IF NOT EXISTS
      │               ensure_schema_migrations()  ← ALTER TABLE IF NOT EXISTS
      │      ↳ non-zero exit = deploy aborted before traffic routes
      │
      │      exec python main.py
      │           ↳ shell replaced — SIGTERM hits Python directly
      │
      ├─ PROCESS = "worker"
      │      exec celery -A celery_app worker \
      │           --queues=scraping,reports,default \
      │           --concurrency=${CELERY_CONCURRENCY:-2} \
      │           --max-tasks-per-child=50
      │
      └─ PROCESS = "beat"
             exec celery -A celery_app beat \
                  --scheduler celery.beat:PersistentScheduler \
                  --schedule /app/data/celerybeat-schedule
```

`exec` is mandatory in production containers. Without it the shell sits between Docker/Railway and the child process, absorbs `SIGTERM`, and forces the platform to escalate to `SIGKILL` after its timeout — abandoning in-flight Celery tasks mid-execution.

---

### Celery Queue Architecture

| Queue | Tasks routed | Workload profile |
|---|---|---|
| `scraping` | `scrape_single_regulator_task` · `scrape_all_regulators_task` · `universal_scrape_url_task` | CPU-bound + Playwright; 2 workers on Railway Starter, 4 on $10 plan |
| `reports` | `analyze_delta_task` · `send_scheduled_alerts_task` · `generate_reports_task` · `send_email_digest_task` · `ytd_snapshot_task` | I/O-bound (LLM API, Telegram HTTP); 2–4 workers |
| `default` | `health_watchdog_task` · `dead_link_checker_task` · `debug_ping` | Low volume; 1–2 workers |

**Beat schedule:**

| Job | Cron | Queue |
|---|---|---|
| Full scrape of all active regulators | `0 */6 * * *` | `scraping` |
| Executive report generation | `0 7 * * *` (07:00 UTC) | `reports` |
| Daily Telegram digest | `0 8 * * *` (08:00 UTC) | `reports` |
| Personalised subscription alerts | `0 9 * * *` (09:00 UTC) | `reports` |
| YTD metrics snapshot | `0 1 * * *` (01:00 UTC) | `reports` |
| Health watchdog | `0 * * * *` (hourly) | `default` |
| Dead link checker | `30 */6 * * *` (+30 min offset) | `default` |

---

### Railway Deployment: Step-by-Step

**Step 1 — Create Railway project**

```bash
railway new regrada
```

**Step 2 — Add managed services**

In the Railway dashboard, add:
- **PostgreSQL** plugin → auto-injects `DATABASE_URL`
- **Redis** plugin → auto-injects `REDIS_URL`

`session.py` automatically rewrites Railway's `postgres://` prefix to `postgresql://` for SQLAlchemy 2.x compatibility.

**Step 3 — Create Railway services from the same repository**

| Service | Start command | Notes |
|---|---|---|
| `regrada-web` | `bash entrypoint.sh web` | Primary service; runs schema migration on boot |
| `regrada-worker` | `bash entrypoint.sh worker` | Set `CELERY_CONCURRENCY=2` (Starter) or `4` ($10 plan) |
| `regrada-beat` | `bash entrypoint.sh beat` | Single instance only — do not scale horizontally |

**Step 4 — Set environment variables, then deploy**

```bash
make pre-push     # passes all 28 tests locally
git push origin main
```

Railway detects the push, builds from `Dockerfile`, and routes traffic once `/api/v1/health` returns HTTP 200 (healthcheck timeout: 300 seconds per `railway.toml`).

---

### Production Environment Variables

Variables marked **auto** are injected by Railway plugins and require no manual entry.

| Variable | Source | Required | Description |
|---|---|:---:|---|
| `DATABASE_URL` | **auto** — Railway PostgreSQL plugin | ✅ | SQLAlchemy connection string. `session.py` rewrites `postgres://` → `postgresql://` automatically. |
| `REDIS_URL` | **auto** — Railway Redis plugin | ✅ | Celery broker URL. Also used as `CELERY_RESULT_BACKEND` if that variable is unset. |
| `CELERY_RESULT_BACKEND` | manual — copy value of `$REDIS_URL` | ✅ | Task result storage backend. Same Redis instance is fine; use DB index `/1` to separate from broker traffic. |
| `OPENAI_API_KEY` | manual | ✅ | GPT-4o-mini key for `analyze_delta_task` (delta analysis) and the Universal AI Scraper. |
| `ANTHROPIC_API_KEY` | manual | ✅ | Claude key for AI enrichment pipeline (`ai_analysis`, `action_plan` columns). |
| `TELEGRAM_BOT_TOKEN` | manual | ✅ | Bot token from `@BotFather`. Drives all Telegram dispatch in `send_scheduled_alerts_task`. |
| `REGRADA_DASHBOARD_URL` | manual — set after first deploy | ✅ | Public Railway URL injected into Telegram alert links, e.g. `https://regrada.up.railway.app`. Leave empty until the URL is known. |
| `SECRET_KEY` | manual — generate once | ✅ | NiceGUI `storage_secret` for server-side session signing. Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `REGRADA_API_KEY` | manual — generate once | ✅ | Bearer token protecting all `/api/*` endpoints. Generate with the same `secrets.token_hex(32)` call. |
| `CELERY_CONCURRENCY` | manual | — | Worker subprocess count. Default: `2`. Set to `4` on Railway's $10/mo plan. |
| `SENTRY_DSN` | manual | — | Sentry project DSN. The `task_failure` Celery signal in `celery_app.py` forwards exceptions automatically. Leave empty to disable. |
| `PROXY_LIST` | manual | — | Comma-separated proxy URLs for CIS portals that block direct datacenter IPs: `http://user:pass@host:port,…` |
| `DEBUG` | manual | — | Set `false` in production. Enables NiceGUI hot-reload and verbose SQLAlchemy echo when `true`. |
| `LOG_LEVEL` | manual | — | Loguru log level. `INFO` in production; `DEBUG` for temporary diagnostics only. |

---

### Health & Monitoring

| Endpoint | Auth | Response |
|---|---|---|
| `GET /api/v1/health` | None | `{"status": "ok", "db": "ok"}` |
| `GET /api/v1/regulations` | `REGRADA_API_KEY` header | Paginated regulation list |
| `GET /api/v1/regulations/{id}/versions` | `REGRADA_API_KEY` header | Version history with delta JSON |
| `POST /api/v1/subscriptions` | `REGRADA_API_KEY` header | Create or update Telegram subscription |

**Flower** (local): `http://localhost:5555` — real-time queue depths, worker status, task history, retry controls.

**Railway Metrics**: CPU and memory per service. Watch `regrada-worker` memory — Playwright Chromium peaks at ~400 MB per concurrent browser instance.

**Sentry**: the `@task_failure.connect` signal in `celery_app.py` calls `sentry_sdk.capture_exception()` automatically when `SENTRY_DSN` is set — no additional instrumentation required.

---

## Repository Structure

```
regrada/
├── app/
│   ├── application/
│   │   ├── pipeline.py             # AI scrape → persist orchestrator
│   │   └── watchdog.py             # dead-link checker + health monitor
│   ├── core/domain/
│   │   └── models.py               # Pydantic domain models (RegulationModel)
│   └── infrastructure/
│       ├── db/
│       │   ├── models.py           # SQLAlchemy ORM + ensure_schema_migrations()
│       │   ├── repository.py       # RegulationRepository + SubscriptionRepository
│       │   └── session.py          # Engine factory (SQLite dev / PostgreSQL prod)
│       ├── notifications/
│       │   ├── email_digest.py
│       │   └── telegram_alert.py
│       └── reports/
│           └── executive_report.py
├── services/
│   ├── delta_analyzer.py           # DeltaAnalysis model · analyze_delta() · Telegram HTTP
│   └── universal_scraper.py        # Playwright stealth scraper + upsert_raw_versioned()
├── tests/
│   ├── __init__.py
│   └── test_compliance_engine.py   # 28 pytest tests across 4 classes
├── celery_app.py                   # Celery app · task definitions · beat schedule
├── config.py                       # Pydantic Settings (all env vars, PORT bridging)
├── main.py                         # NiceGUI SPA entry point
├── entrypoint.sh                   # Container bootstrap: migration gate + exec dispatch
├── Dockerfile                      # Two-stage production build (builder + runtime)
├── docker-compose.yml              # Local full stack: 5 services + named volumes
├── Procfile                        # Railway / Heroku process types
├── railway.toml                    # Railway deploy config (healthcheck, restart policy)
├── Makefile                        # Dev workflow: build · up · test · pre-push
└── requirements.txt                # Python deps (includes pytest for Docker test runs)
```

---

*RegRadar Enterprise — built for compliance teams that cannot afford to miss a regulatory update.*
