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
# It probes the API's own /api/health over loopback and restarts
# statuteproof-api.service + pages the founder ONLY when the API gives NO answer
# (timeout / connection refused = the wedged-or-dead API this exists to recover),
# through the SAME channel the heartbeat/integrity watchdogs use
# (app.ops_alert.notify_founder — admin Telegram bot). A SERVED non-200 (e.g. a
# 503 from /api/health when the monitor/scheduler is stale, or a transient DB
# blip) means the API is ALIVE and answering: restarting it cannot fix a
# dependency, that case is already owned by the heartbeat deadman, so a served
# error is logged and left alone — no restart, no page (avoids a restart storm +
# alarm fatigue on a healthy API).
#
# Exit status (mirrors the heartbeat/verify oneshots):
#   0  API answered — healthy 200, OR a served non-200 that is a dependency
#      signal (alive, not this watchdog's job). Nothing restarted.
#   1  API gave no answer (wedged/dead) — restart + page already issued. This is
#      an EXPECTED signal, not a fault; the .service lists SuccessExitStatus=0 1
#      so the unit does not go into failed state and the timer keeps firing.
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

# A SERVED non-200 (e.g. 503) means the API process is ALIVE and answering — it
# is reporting a degraded DEPENDENCY (a stale monitor/scheduler, or a transient
# DB blip), NOT the wedged-but-unresponsive API this watchdog exists to recover.
# Restarting statuteproof-api.service cannot clear scheduler staleness (a
# separate unit), and that exact case is already owned by the dedicated
# statuteproof-heartbeat deadman — so restarting + paging on a served 503 would
# only drop live requests and false-page the founder on every 2-minute tick for
# the whole outage. The wedged/dead API this watchdog targets gives NO answer at
# all -> curl yields the sentinel http_code 000 (timeout / connection refused).
# So: restart + page ONLY on 000; a served error is logged and left alone.
if [ "${http_code}" != "000" ]; then
    log "degraded but ALIVE: ${HEALTH_URL} answered '${http_code}' (not 200) — the API is serving, so NOT restarting or paging from here. A served error is a dependency signal (e.g. a stale monitor, which the heartbeat deadman covers), not a wedged API."
    exit 0
fi

log "UNHEALTHY: ${HEALTH_URL} gave no answer (timeout/connection refused) — the API is wedged or dead; restarting ${API_UNIT}"

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
export STATUTEPROOF_API_HEALTH_ALERT="StatuteProof API watchdog: /api/health gave NO answer (timeout/connection refused — the API is wedged or dead) on ${host}. ${restart_status} for ${API_UNIT}. Customers may be seeing 502s — verify the API recovered."
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
