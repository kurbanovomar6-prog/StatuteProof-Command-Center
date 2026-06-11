#!/usr/bin/env bash
# =============================================================================
# entrypoint.sh — RegRadar container bootstrap
#
# Dispatches the correct process type and gates schema migrations in front of
# the web process so the database is always ready before NiceGUI accepts traffic.
#
# Usage (called by Procfile / railway.toml):
#   bash entrypoint.sh web     → migrate schema, then start NiceGUI
#   bash entrypoint.sh worker  → start Celery worker  (migrations skipped)
#   bash entrypoint.sh beat    → start Celery beat    (migrations skipped)
#
# PROCESS_TYPE env var is the fallback when no positional argument is given.
# =============================================================================
set -euo pipefail

PROCESS="${1:-${PROCESS_TYPE:-web}}"

_log() { printf '[entrypoint][%s][%s] %s\n' "$(date -u +%T)" "$PROCESS" "$*"; }

# ── Schema migration (web only) ───────────────────────────────────────────────
# Workers deliberately skip migration:
#   • Railway starts services sequentially once the web healthcheck passes,
#     so the schema is guaranteed to exist before any worker boots.
#   • ensure_schema_migrations() uses ALTER TABLE IF NOT EXISTS (idempotent),
#     but running it concurrently from N worker replicas generates log noise
#     and unnecessary DB round-trips.
#   • A failed migration exits non-zero here, which makes Railway abort the
#     deploy before any traffic reaches the new pod — fail-fast, no half-migrated
#     production databases.
if [ "$PROCESS" = "web" ]; then
    _log "running schema migrations..."
    python - <<'PYEOF'
from app.infrastructure.db.session import engine, init_db
from app.infrastructure.db.models import ensure_schema_migrations
init_db()                      # CREATE TABLE IF NOT EXISTS for all ORM models
ensure_schema_migrations(engine)  # ALTER TABLE idempotent column additions
print("[entrypoint] schema OK")
PYEOF
    _log "schema migrations complete"
fi

# ── Process dispatch ──────────────────────────────────────────────────────────
# exec replaces the shell with the child process so SIGTERM/SIGKILL from
# Docker / Railway propagate directly to Python or Celery — no zombie shell.
case "$PROCESS" in

    web)
        _log "starting NiceGUI on ${APP_HOST:-0.0.0.0}:${PORT:-8080}"
        exec python main.py
        ;;

    worker)
        _log "starting Celery worker (queues: scraping,reports,default)"
        exec celery -A celery_app worker \
            --loglevel=INFO \
            --queues=scraping,reports,default \
            --concurrency="${CELERY_CONCURRENCY:-2}" \
            --hostname="worker@%h" \
            --without-gossip \
            --without-mingle \
            --max-tasks-per-child=50
        ;;

    beat)
        _log "starting Celery beat (PersistentScheduler)"
        exec celery -A celery_app beat \
            --loglevel=INFO \
            --scheduler celery.beat:PersistentScheduler \
            --schedule /app/data/celerybeat-schedule
        ;;

    *)
        _log "ERROR: unknown process type '${PROCESS}'"
        echo "Usage: $0 {web|worker|beat}" >&2
        exit 1
        ;;
esac
