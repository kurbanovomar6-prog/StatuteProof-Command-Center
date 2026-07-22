#!/usr/bin/env bash
# StatuteProof API liveness watchdog.
#
# statuteproof-api.service is Type=simple with Restart=on-failure. That covers a
# CRASH but NOT an alive-but-wedged API: a SQLite writer-lock stall or a
# TasksMax thread-pool exhaustion leaves serve_forever() alive while every
# request blocks. systemd sees the process running and never restarts it, Caddy
# returns 502 to every caller, and the external uptime probe stays GREEN off the
# still-healthy SCHEDULER heartbeat — so paying customers are down with no auto-
# recovery and no founder page. The scheduler has its own deadman
# (statuteproof-heartbeat); the API did not — this oneshot is it.
#
# It probes the API's own /api/health over loopback and, when the API does not
# answer a healthy 200, restarts statuteproof-api.service AND pages the founder
# through the SAME channel the heartbeat/integrity watchdogs use
# (app.ops_alert.notify_founder — admin Telegram bot).
#
# Exit status (mirrors the heartbeat/verify oneshots):
#   0  API answered 200 (healthy) — nothing to do.
#   1  API wedged/unhealthy — restart + page already issued. This is an EXPECTED
#      signal, not a fault; the .service lists SuccessExitStatus=0 1 so the unit
#      does not go into failed state and the timer keeps firing.
set -euo pipefail

APP_DIR="${STATUTEPROOF_APP_DIR:-/srv/regradar}"
# The API binds --port 5001 in statuteproof-api.service; override in lockstep if
# that ever changes. Loopback only — Caddy terminates TLS in front of it.
API_PORT="${STATUTEPROOF_API_PORT:-5001}"
HEALTH_URL="http://127.0.0.1:${API_PORT}/api/health"
# Short, finite probe: a wedged API never answers, so a long timeout only delays
# recovery. Enough to ride out a brief GC pause, no more.
PROBE_TIMEOUT_S="${STATUTEPROOF_API_HEALTH_TIMEOUT_S:-8}"
PYTHON_BIN="${APP_DIR}/.venv/bin/python"
API_UNIT="statuteproof-api.service"

log() { echo "[api-health-check] $*"; }

# Probe /api/health. NO -f: without it curl exits 0 for ANY HTTP response and
# prints the status via -w, and exits non-zero ONLY on the connection failure /
# timeout cases (the wedged/crashed API). So a reachable-but-503 API keeps its
# real code, while a dead one collapses to the sentinel below.
http_code="000"
if http_code="$(curl -sS -o /dev/null -w '%{http_code}' \
        --max-time "${PROBE_TIMEOUT_S}" "${HEALTH_URL}" 2>/dev/null)"; then
    :
else
    http_code="000"   # no HTTP response (timeout / connection refused)
fi

if [ "${http_code}" = "200" ]; then
    log "healthy (HTTP 200) — ${HEALTH_URL}"
    exit 0
fi

log "UNHEALTHY: ${HEALTH_URL} returned '${http_code}' (expected 200) — restarting ${API_UNIT}"

# Best-effort restart. Managing the system unit needs privilege, which is why
# this watchdog runs as root (see the .service). NEVER abort the page on a
# restart error — a failed restart is exactly when the founder must be told.
restart_status="restart issued"
if ! systemctl restart "${API_UNIT}" 2>/dev/null; then
    restart_status="RESTART COMMAND FAILED"
    log "${restart_status} for ${API_UNIT}"
fi

# Page the founder through the already-wired channel, reusing
# app.ops_alert.notify_founder (best-effort; never raises, returns False when
# ops alerts are disabled/unconfigured). The message is passed via env, never
# interpolated into the Python source, so a hostname can't break out of the
# string. CWD is /srv/regradar (WorkingDirectory=), so the import resolves.
host="$(hostname -s 2>/dev/null || echo host)"
export STATUTEPROOF_API_HEALTH_ALERT="StatuteProof API watchdog: /api/health returned '${http_code}' (expected 200) on ${host}. ${restart_status} for ${API_UNIT}. Customers may be seeing 502s — verify the API recovered."
if [ -x "${PYTHON_BIN}" ]; then
    "${PYTHON_BIN}" - <<'PY' || true
import os
from app.ops_alert import notify_founder
notify_founder(
    os.environ.get(
        "STATUTEPROOF_API_HEALTH_ALERT",
        "StatuteProof API watchdog: API unhealthy.",
    )
)
PY
else
    log "python venv missing at ${PYTHON_BIN} — cannot page founder"
fi

# Signal remediation to systemd via exit 1 (expected — SuccessExitStatus=0 1).
exit 1
