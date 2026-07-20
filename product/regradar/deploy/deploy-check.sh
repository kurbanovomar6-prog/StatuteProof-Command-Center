#!/usr/bin/env bash
# StatuteProof deploy-check — fails loudly when anything required is missing.
# Run from the app root (/srv/regradar) BEFORE starting services:
#   bash deploy/deploy-check.sh
set -uo pipefail

RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[0;33m'; NC=$'\033[0m'
FAIL=0
APP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_ROOT"

ok()   { echo "${GREEN}  ✓ $1${NC}"; }
bad()  { echo "${RED}  ✗ $1${NC}"; FAIL=1; }
warn() { echo "${YELLOW}  ! $1${NC}"; }

echo "StatuteProof deploy-check — $APP_ROOT"
echo "── runtime ──────────────────────────────────────────────"

PY_BIN="${PY_BIN:-$APP_ROOT/.venv/bin/python}"
[ -x "$PY_BIN" ] || PY_BIN="$(command -v python3 || true)"
if [ -z "$PY_BIN" ]; then
  bad "no python3 found (expected .venv/bin/python or python3 on PATH)"
else
  PY_VER="$("$PY_BIN" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
  "$PY_BIN" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' \
    && ok "python $PY_VER (>= 3.11) at $PY_BIN" \
    || bad "python $PY_VER too old — 3.11+ required"
fi

"$PY_BIN" -c 'import requests, bs4, lxml, dotenv' 2>/dev/null \
  && ok "core python dependencies importable" \
  || bad "core dependencies missing — run: $PY_BIN -m pip install -r requirements.txt"

echo "── configuration (.env) ─────────────────────────────────"
if [ ! -f .env ]; then
  bad ".env missing — copy .env.example and fill values"
else
  ok ".env present"
  # shellcheck disable=SC2046
  set -a; . ./.env 2>/dev/null || true; set +a

  # Required always
  for var in SECRET_KEY ENVIRONMENT; do
    v="${!var:-}"
    if [ -z "$v" ]; then bad "required env var $var is empty"; \
    elif [[ "$v" == *change-me* ]]; then bad "$var still holds the placeholder value"; \
    else ok "$var set"; fi
  done

  # Email provider coherence: selected provider must be fully configured.
  provider="${STATUTEPROOF_EMAIL_PROVIDER:-local_outbox}"
  case "$provider" in
    local_outbox) ok "email provider: local_outbox (no external send)";;
    smtp)
      for var in STATUTEPROOF_EMAIL_FROM SMTP_HOST SMTP_PORT SMTP_USERNAME SMTP_PASSWORD; do
        [ -n "${!var:-}" ] && ok "$var set" || bad "smtp selected but $var is empty"
      done;;
    postmark)
      for var in STATUTEPROOF_EMAIL_FROM POSTMARK_SERVER_TOKEN; do
        [ -n "${!var:-}" ] && ok "$var set" || bad "postmark selected but $var is empty"
      done;;
    sendgrid)
      for var in STATUTEPROOF_EMAIL_FROM SENDGRID_API_KEY; do
        [ -n "${!var:-}" ] && ok "$var set" || bad "sendgrid selected but $var is empty"
      done;;
    *) bad "unknown STATUTEPROOF_EMAIL_PROVIDER: $provider";;
  esac

  [ -n "${TELEGRAM_ALERTS_BOT_TOKEN:-}" ] && ok "TELEGRAM_ALERTS_BOT_TOKEN set" \
    || warn "TELEGRAM_ALERTS_BOT_TOKEN empty — customer Telegram pairing disabled"
  [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && ok "TELEGRAM_BOT_TOKEN set" \
    || warn "TELEGRAM_BOT_TOKEN empty — founder contact notifications disabled"
fi

echo "── backup & uptime protection ───────────────────────────"
# Off-box backup is what lets the sealed evidence trail survive droplet loss —
# a missing remote is a deploy FAILURE, not a warning (audit 2026-07-20).
# STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY=1 is a documented DEV-ONLY override.
if [ -n "${STATUTEPROOF_BACKUP_REMOTE:-}" ]; then
  ok "STATUTEPROOF_BACKUP_REMOTE set — backup archives push off-box"
elif [ "${STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY:-}" = "1" ]; then
  warn "backups are LOCAL-ONLY (STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY=1 dev override — never use on prod)"
else
  bad "STATUTEPROOF_BACKUP_REMOTE is unset — evidence trail does not survive droplet loss; set it in .env (DEPLOY.md § 9) or export STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY=1 (dev only)"
fi
[ -n "${STATUTEPROOF_HEARTBEAT_PING_URL:-}" ] \
  && ok "STATUTEPROOF_HEARTBEAT_PING_URL set — external uptime probe wired" \
  || warn "STATUTEPROOF_HEARTBEAT_PING_URL empty — no external uptime probe (see DEPLOY.md § External uptime probe)"

echo "── app config validation ────────────────────────────────"
if "$PY_BIN" run.py validate-config >/tmp/sp-validate-config.out 2>&1; then
  ok "run.py validate-config passed"
else
  bad "run.py validate-config FAILED — output:"
  sed 's/^/      /' /tmp/sp-validate-config.out | tail -20
fi

echo "── filesystem ───────────────────────────────────────────"
for d in data logs; do
  mkdir -p "$d" 2>/dev/null
  if [ -w "$d" ]; then ok "$d/ writable"; else bad "$d/ not writable by $(whoami)"; fi
done
"$PY_BIN" - <<'EOF' && ok "sqlite database reachable" || bad "sqlite database not reachable"
import sqlite3, sys
sys.path.insert(0, ".")
from app.config import DB_PATH
conn = sqlite3.connect(DB_PATH); conn.execute("SELECT 1"); conn.close()
EOF

echo "── frontend build ───────────────────────────────────────"
if [ ! -f web/dist/index.html ]; then
  bad "web/dist missing — build with: cd web && npm ci && npm run build"
else
  ok "web/dist present"
  if grep -rql "localhost:5001\|127\.0\.0\.1:5001" web/dist/assets/ 2>/dev/null; then
    bad "built frontend references localhost — rebuild without a localhost VITE_API_URL"
  else
    ok "built frontend has no localhost API references"
  fi
fi

echo "── service files ────────────────────────────────────────"
for unit in statuteproof-api.service statuteproof-scheduler.service \
            statuteproof-telegram-bot.service statuteproof-compaction.service \
            statuteproof-compaction.timer; do
  [ -f "deploy/systemd/$unit" ] && ok "deploy/systemd/$unit present" || bad "deploy/systemd/$unit missing"
done
[ -f deploy/Caddyfile ] && ok "deploy/Caddyfile present" || bad "deploy/Caddyfile missing"
[ -f deploy/logrotate.d/statuteproof ] && ok "logrotate config present" || bad "logrotate config missing"

echo "─────────────────────────────────────────────────────────"
if [ "$FAIL" -ne 0 ]; then
  echo "${RED}DEPLOY-CHECK FAILED — fix the ✗ items above before starting services.${NC}"
  exit 1
fi
echo "${GREEN}DEPLOY-CHECK PASSED.${NC}"
