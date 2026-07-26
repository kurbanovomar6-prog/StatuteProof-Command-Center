#!/usr/bin/env bash
# StatuteProof scheduler liveness watchdog — the one that RESTARTS.
#
# statuteproof-scheduler.service is Type=simple with Restart=on-failure. That
# covers a CRASH but NOT an alive-but-wedged watch loop. On 2026-07-21 the loop
# entered source [75/139] (DIFC; Playwright "Target crashed" + HTTP 429) and
# blocked in futex_wait_queue for 4 days 2 hours. The process stayed ALIVE, so
# systemd never restarted it and `systemctl is-active` reported "active" the
# whole time.
#
# Three controls existed and none of them recovered it:
#   • Restart=on-failure          — nothing failed; the process never exited.
#   • deploy/api-health-check.sh  — watches the API, and correctly refuses to
#                                   restart on a SERVED 503 (a dependency
#                                   signal). Not its job, by design.
#   • statuteproof-heartbeat      — fired ~190 times over those 4 days and
#                                   called notify_founder() every time. It only
#                                   NOTIFIES. Nothing restarted the unit.
#
# This oneshot is the missing action. It reads the same heartbeat the deadman
# reads (app.ops_alert.heartbeat_state — a PURE read, so asking does not emit a
# second founder page), and when the loop has not completed a full cycle within
# 2x the configured interval it RESTARTS statuteproof-scheduler.service and then
# pages the founder saying so. It mirrors deploy/api-health-check.sh: runs as
# root because it manages a system unit, pages through the same
# app.ops_alert.notify_founder channel, and never aborts the page on a failed
# restart — a failed restart is exactly when the founder must be told.
#
# BACKOFF — a crash-looping scheduler must not be restarted forever in silence:
#   • MIN_GAP_S   : never restart twice inside this window. A freshly restarted
#                   loop writes its startup heartbeat immediately, but a loop
#                   that is crash-looping needs room to fail visibly rather than
#                   being kicked on every tick.
#   • MAX_RESTARTS in WINDOW_S : past this budget the watchdog STOPS restarting
#                   and pages once per window saying auto-recovery has given up.
#                   Silent infinite restarts would hide a real, permanent fault.
#
# Exit status (mirrors the heartbeat/verify/api-health oneshots):
#   0  heartbeat fresh, or a deliberate no-action tick (inside MIN_GAP_S).
#   1  the loop is wedged — a restart was issued, or the restart budget is
#      exhausted and the founder was paged. EXPECTED, not a fault: the .service
#      lists SuccessExitStatus=0 1 so the timer keeps firing.
set -uo pipefail

APP_DIR="${STATUTEPROOF_APP_DIR:-/srv/regradar}"
# Overridable so the logic can be exercised with stubs in tests; production
# never sets these.
PYTHON_BIN="${STATUTEPROOF_PYTHON_BIN:-${APP_DIR}/.venv/bin/python}"
SYSTEMCTL_BIN="${STATUTEPROOF_SYSTEMCTL_BIN:-systemctl}"
SCHED_UNIT="statuteproof-scheduler.service"

STATE_DIR="${STATUTEPROOF_WATCHDOG_STATE_DIR:-/var/lib/statuteproof}"
STATE_FILE="${STATE_DIR}/scheduler-watchdog-restarts"
GAVE_UP_FILE="${STATE_DIR}/scheduler-watchdog-gave-up"

MAX_RESTARTS="${STATUTEPROOF_SCHEDULER_WATCHDOG_MAX_RESTARTS:-3}"
WINDOW_S="${STATUTEPROOF_SCHEDULER_WATCHDOG_WINDOW_S:-21600}"     # 6 h
MIN_GAP_S="${STATUTEPROOF_SCHEDULER_WATCHDOG_MIN_GAP_S:-900}"     # 15 min

log() { echo "[scheduler-watchdog] $*"; }

now_epoch() { date +%s; }

page_founder() {
    # Message passed via env, never interpolated into the Python source, so a
    # hostname or source name can't break out of the string. CWD is APP_DIR
    # (WorkingDirectory=), so the import resolves.
    export STATUTEPROOF_SCHEDULER_WATCHDOG_ALERT="$1"
    if [ ! -x "${PYTHON_BIN}" ]; then
        log "python missing at ${PYTHON_BIN} — cannot page founder"
        return 0
    fi
    "${PYTHON_BIN}" - <<'PY' || true
import os
from app.ops_alert import notify_founder
notify_founder(
    os.environ.get(
        "STATUTEPROOF_SCHEDULER_WATCHDOG_ALERT",
        "StatuteProof scheduler watchdog: the monitoring loop is wedged.",
    )
)
PY
}

cd "${APP_DIR}" 2>/dev/null || {
    log "app dir ${APP_DIR} unreachable — cannot check the scheduler"
    exit 0
}

if [ ! -x "${PYTHON_BIN}" ]; then
    log "python venv missing at ${PYTHON_BIN} — cannot read the heartbeat"
    exit 0
fi

# Ask the app itself, so the staleness threshold can never drift from the one
# the deadman uses. heartbeat_state() is a PURE read: no founder page, no
# external uptime ping. One pipe-delimited line: REASON|AGE_SECONDS|PROGRESS.
hb_line="$("${PYTHON_BIN}" - <<'PY' 2>/dev/null
from app.ops_alert import describe_progress, heartbeat_state

state = heartbeat_state()
age = "-1" if state.age_seconds is None else str(int(state.age_seconds))
print("|".join([state.reason, age, describe_progress(state.progress)]))
PY
)"

if [ -z "${hb_line}" ]; then
    log "heartbeat query produced no output — treating as UNKNOWN, taking no action"
    exit 0
fi

IFS='|' read -r hb_reason hb_age hb_progress <<< "${hb_line}"

case "${hb_reason}" in
    fresh)
        log "scheduler healthy — last full cycle ${hb_age}s ago. ${hb_progress}"
        exit 0
        ;;
    stale|missing)
        : # fall through to remediation
        ;;
    *)
        # "error" means our own read failed. That is not evidence of a wedge,
        # and restarting the monitoring engine on our own bug would be worse
        # than the bug.
        log "heartbeat state '${hb_reason}' is not a wedge signal — no action"
        exit 0
        ;;
esac

log "WEDGED: heartbeat ${hb_reason} (age ${hb_age}s). ${hb_progress}"

mkdir -p "${STATE_DIR}" 2>/dev/null || true
NOW="$(now_epoch)"
CUTOFF=$(( NOW - WINDOW_S ))

# Prune the restart log to the rolling window, then count what is left.
recent=""
if [ -f "${STATE_FILE}" ]; then
    while read -r ts; do
        case "${ts}" in ''|*[!0-9]*) continue ;; esac
        [ "${ts}" -ge "${CUTOFF}" ] && recent="${recent}${ts}"$'\n'
    done < "${STATE_FILE}"
fi
printf '%s' "${recent}" > "${STATE_FILE}" 2>/dev/null || true

restart_count=0
last_restart=0
while read -r ts; do
    [ -z "${ts}" ] && continue
    restart_count=$(( restart_count + 1 ))
    [ "${ts}" -gt "${last_restart}" ] && last_restart="${ts}"
done <<< "${recent}"

# Just restarted? Give the loop room to come back before kicking it again. A
# fresh process writes its startup heartbeat before the first sweep, so if it
# is genuinely recovering this branch stops firing within one tick.
if [ "${last_restart}" -gt 0 ] && [ $(( NOW - last_restart )) -lt "${MIN_GAP_S}" ]; then
    log "restarted $(( NOW - last_restart ))s ago (min gap ${MIN_GAP_S}s) — waiting for ${SCHED_UNIT} to come back; no action"
    exit 0
fi

host="$(hostname -s 2>/dev/null || echo host)"

# Budget exhausted: stop restarting. Page ONCE per window — a page every tick
# for a permanently broken scheduler is how real pages get muted.
if [ "${restart_count}" -ge "${MAX_RESTARTS}" ]; then
    gave_up_at=0
    if [ -f "${GAVE_UP_FILE}" ]; then
        read -r gave_up_at < "${GAVE_UP_FILE}" || gave_up_at=0
        case "${gave_up_at}" in ''|*[!0-9]*) gave_up_at=0 ;; esac
    fi
    if [ "${gave_up_at}" -gt "${CUTOFF}" ]; then
        log "restart budget exhausted (${restart_count}/${MAX_RESTARTS} in ${WINDOW_S}s); founder already paged at ${gave_up_at} — staying quiet"
        exit 1
    fi
    printf '%s\n' "${NOW}" > "${GAVE_UP_FILE}" 2>/dev/null || true
    log "restart budget exhausted (${restart_count}/${MAX_RESTARTS} in ${WINDOW_S}s) — NOT restarting; paging founder"
    page_founder "🚨 StatuteProof scheduler watchdog GAVE UP on ${host}. ${SCHED_UNIT} was auto-restarted ${restart_count} time(s) in the last $(( WINDOW_S / 3600 ))h and the monitoring loop is STILL wedged (heartbeat ${hb_reason}, ${hb_age}s old). Auto-restart is now suspended so a crash loop is not hidden. ${hb_progress}. Monitoring is DOWN until someone looks at it: journalctl -u ${SCHED_UNIT} -n 200"
    exit 1
fi

log "restarting ${SCHED_UNIT} (restart $(( restart_count + 1 ))/${MAX_RESTARTS} in this ${WINDOW_S}s window)"
restart_status="restart issued"
if ! "${SYSTEMCTL_BIN}" restart "${SCHED_UNIT}" 2>/dev/null; then
    restart_status="RESTART COMMAND FAILED"
    log "${restart_status} for ${SCHED_UNIT}"
fi
printf '%s\n' "${NOW}" >> "${STATE_FILE}" 2>/dev/null || true
# A successful restart re-opens the budget conversation: clear the give-up
# marker so a LATER exhaustion in a new window pages again instead of being
# suppressed by a stale marker.
rm -f "${GAVE_UP_FILE}" 2>/dev/null || true

page_founder "🚨 StatuteProof monitoring loop was WEDGED on ${host} — heartbeat ${hb_reason} (${hb_age}s old, ${hb_progress}). ${restart_status} for ${SCHED_UNIT} (restart $(( restart_count + 1 ))/${MAX_RESTARTS} in the last $(( WINDOW_S / 3600 ))h). Sources were NOT being checked while it was wedged — verify the next full cycle completes."

exit 1
