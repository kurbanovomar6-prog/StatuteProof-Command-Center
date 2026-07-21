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
  # `+u` around the `.`: under `set -u` an unset expansion inside a VALUE (a
  # passphrase containing `$NOPE`) kills the sourcing shell outright, so the
  # script exited right here — after "✓ .env present", with no ✗ and no banner
  # — and every gate below, including the passphrase-mangling gate written for
  # exactly that input, never ran. Stderr is deliberately not redirected.
  set -a +u; . ./.env || true; set +a -u

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

# Which host is this? The dev-only fail-open overrides below must not be
# honoured on production: the only thing between a prod droplet and a plaintext
# off-box push of password hashes and live session ids cannot be one env var an
# operator sets under deploy pressure. ENVIRONMENT is the codebase's own
# environment signal (app/config.py, required above); the documented production
# install path is a second, independent signal for a host whose .env failed to
# load; STATUTEPROOF_ENV wins over both for a non-standard install. Kept
# byte-identical in deploy/backup.sh so the gate and the script agree.
STATUTEPROOF_IS_PROD=0
case "${STATUTEPROOF_ENV:-${ENVIRONMENT:-}}" in
  production|prod) STATUTEPROOF_IS_PROD=1 ;;
esac
if [ "$APP_ROOT" = "/srv/regradar" ]; then STATUTEPROOF_IS_PROD=1; fi

echo "── backup & uptime protection ───────────────────────────"
# Off-box backup is what lets the sealed evidence trail survive droplet loss —
# a missing remote is a deploy FAILURE, not a warning (audit 2026-07-20).
# STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY=1 is a DEV-ONLY override and is REFUSED
# on production (both here and in backup.sh). No ✗ message quotes an override:
# a blocking message that prints its own escape hatch is how the escape hatch
# ends up in a prod .env.
if [ -n "${STATUTEPROOF_BACKUP_REMOTE:-}" ]; then
  ok "STATUTEPROOF_BACKUP_REMOTE set — backup archives push off-box"
elif [ "${STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY:-}" = "1" ] && [ "$STATUTEPROOF_IS_PROD" != "1" ]; then
  warn "backups are LOCAL-ONLY (STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY=1 dev override — refused on a production host)"
elif [ "${STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY:-}" = "1" ]; then
  bad "STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY=1 is a development override and is REFUSED on a production host — remove it from .env and set STATUTEPROOF_BACKUP_REMOTE (DEPLOY.md § 9)"
else
  bad "STATUTEPROOF_BACKUP_REMOTE is unset — evidence trail does not survive droplet loss; set it in .env (DEPLOY.md § 9)"
fi
[ -n "${STATUTEPROOF_HEARTBEAT_PING_URL:-}" ] \
  && ok "STATUTEPROOF_HEARTBEAT_PING_URL set — external uptime probe wired" \
  || warn "STATUTEPROOF_HEARTBEAT_PING_URL empty — no external uptime probe (see DEPLOY.md § External uptime probe)"

# Making the remote MANDATORY (above) created a standing obligation to place a
# copy of regradar.db — password hashes, emails, telegram_chat_ids and the
# sessions table whose ids ARE bearer credentials — on storage we do not
# control. So a configured remote WITHOUT an encryption secret is a deploy
# FAILURE too: backup.sh refuses the push in that state, which would silently
# leave the evidence trail unprotected. STATUTEPROOF_ALLOW_UNENCRYPTED_BACKUP=1
# is a documented DEV-ONLY override (it makes backup.sh push in the clear).
# BRANCH ORDER MIRRORS backup.sh ON PURPOSE: backup.sh honours the dev override
# FIRST, so an override left set next to a real encryption secret still pushes
# PLAINTEXT. Checking the secret first here would print a green "archives are
# encrypted" for exactly the misconfiguration this gate exists to catch.
# The TOOL is checked too, for the same reason: backup.sh requires the secret
# AND the binary, so a set recipient without `age` installed makes it refuse
# every push. Asserting the config instead of what backup.sh evaluates is how
# a green deploy-check ends up contradicting a backup that never leaves the box.
if [ -z "${STATUTEPROOF_BACKUP_REMOTE:-}" ]; then
  :
elif [ "${STATUTEPROOF_ALLOW_UNENCRYPTED_BACKUP:-}" = "1" ] && [ "$STATUTEPROOF_IS_PROD" != "1" ]; then
  warn "off-box archives push UNENCRYPTED (STATUTEPROOF_ALLOW_UNENCRYPTED_BACKUP=1 dev override — refused on a production host; backup.sh honours it AHEAD of any encryption secret)"
elif [ "${STATUTEPROOF_ALLOW_UNENCRYPTED_BACKUP:-}" = "1" ]; then
  bad "STATUTEPROOF_ALLOW_UNENCRYPTED_BACKUP=1 is a development override and is REFUSED on a production host — remove it from .env and set STATUTEPROOF_BACKUP_AGE_RECIPIENT or STATUTEPROOF_BACKUP_PASSPHRASE (DEPLOY.md § 9)"
elif [ -n "${STATUTEPROOF_BACKUP_AGE_RECIPIENT:-}" ] && command -v age >/dev/null 2>&1; then
  ok "STATUTEPROOF_BACKUP_AGE_RECIPIENT set + age installed — off-box archives are encrypted (age)"
elif [ -n "${STATUTEPROOF_BACKUP_PASSPHRASE:-}" ] && command -v gpg >/dev/null 2>&1; then
  ok "STATUTEPROOF_BACKUP_PASSPHRASE set + gpg installed — off-box archives are encrypted (gpg)"
elif [ -n "${STATUTEPROOF_BACKUP_AGE_RECIPIENT:-}" ]; then
  bad "STATUTEPROOF_BACKUP_AGE_RECIPIENT is set but the age binary is MISSING — backup.sh refuses every off-box push in this state and the archive never leaves the droplet; install it: apt-get install -y age (DEPLOY.md § 9)"
elif [ -n "${STATUTEPROOF_BACKUP_PASSPHRASE:-}" ]; then
  bad "STATUTEPROOF_BACKUP_PASSPHRASE is set but the gpg binary is MISSING — backup.sh refuses every off-box push in this state and the archive never leaves the droplet; install it: apt-get install -y gnupg (DEPLOY.md § 9)"
else
  bad "STATUTEPROOF_BACKUP_REMOTE is set but no backup encryption secret — archives carry password hashes and live session ids; set STATUTEPROOF_BACKUP_AGE_RECIPIENT or STATUTEPROOF_BACKUP_PASSPHRASE in .env (DEPLOY.md § 9)"
fi

# The gpg passphrase is the one secret whose EXACT BYTES must round-trip: this
# script and backup.sh both load config by SOURCING .env, so bash applies
# parameter expansion, command substitution and word splitting to every value.
# A password-manager passphrase containing `$`, a backtick or a space is loaded
# as something else, gpg encrypts with the MANGLED value, and every off-box
# archive becomes unrecoverable with the passphrase the founder actually stored.
# Non-emptiness (above) cannot see that — compare the RAW .env bytes (grep/cut,
# no shell) against the sourced value instead.
if [ -n "${STATUTEPROOF_BACKUP_PASSPHRASE:-}" ] && [ -f .env ]; then
  raw_pass="$(grep -a -m1 '^STATUTEPROOF_BACKUP_PASSPHRASE=' .env | cut -d= -f2- || true)"
  raw_pass="${raw_pass%\"}"; raw_pass="${raw_pass#\"}"
  raw_pass="${raw_pass%\'}"; raw_pass="${raw_pass#\'}"
  if [ -z "$raw_pass" ]; then
    warn "STATUTEPROOF_BACKUP_PASSPHRASE is not a plain .env line — cannot verify it survives .env sourcing"
  elif [ "$raw_pass" != "$STATUTEPROOF_BACKUP_PASSPHRASE" ]; then
    bad "STATUTEPROOF_BACKUP_PASSPHRASE is MANGLED by .env sourcing — gpg would encrypt with a passphrase nobody stored and every off-box archive would be unrecoverable; regenerate it alphanumeric (DEPLOY.md § 9)"
  elif [[ "$raw_pass" == *'$'* || "$raw_pass" == *'`'* || "$raw_pass" =~ [[:space:]] ]]; then
    bad "STATUTEPROOF_BACKUP_PASSPHRASE contains \$, a backtick or whitespace — bash and systemd EnvironmentFile treat those differently, so the effective passphrase can change silently; regenerate it alphanumeric (DEPLOY.md § 9)"
  else
    ok "STATUTEPROOF_BACKUP_PASSPHRASE survives .env sourcing byte-for-byte"
  fi
fi

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

# A documented control that never executes is worse than a known gap: shipping
# the timer units is not the same as running them. Re-run this check AFTER
# DEPLOY.md § 7 (`systemctl enable --now …`) — before that the units are simply
# not installed yet, which warns rather than fails so the documented order of
# steps still works.
echo "── scheduled timers ─────────────────────────────────────"
if ! command -v systemctl >/dev/null 2>&1; then
  warn "systemctl unavailable — timer enablement unverified (not a droplet)"
else
  for unit in statuteproof-compaction.timer statuteproof-backup.timer \
              statuteproof-heartbeat.timer statuteproof-verify.timer; do
    # Pipe-free on purpose: `... | grep -q` under `set -o pipefail` reports a
    # SIGPIPE failure whenever grep exits on an early match while systemctl is
    # still writing, so installed units intermittently read as "not installed".
    case "$(systemctl list-unit-files "$unit" 2>/dev/null || true)" in
      *"$unit"*) unit_installed=1 ;;
      *) unit_installed=0 ;;
    esac
    if [ "$unit_installed" != 1 ]; then
      warn "$unit not installed yet — install and enable it (DEPLOY.md § 7), then re-run this check"
    elif [ "$(systemctl is-enabled "$unit" 2>/dev/null)" != "enabled" ]; then
      bad "$unit is installed but NOT enabled — it will not survive reboot; run: systemctl enable --now $unit"
    elif [ "$(systemctl is-active "$unit" 2>/dev/null)" != "active" ]; then
      bad "$unit is enabled but NOT active — run: systemctl start $unit"
    else
      ok "$unit enabled and active"
    fi
  done
fi

echo "─────────────────────────────────────────────────────────"
if [ "$FAIL" -ne 0 ]; then
  echo "${RED}DEPLOY-CHECK FAILED — fix the ✗ items above before starting services.${NC}"
  exit 1
fi
echo "${GREEN}DEPLOY-CHECK PASSED.${NC}"
