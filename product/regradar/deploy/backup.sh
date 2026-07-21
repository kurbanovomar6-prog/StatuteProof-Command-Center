#!/usr/bin/env bash
# StatuteProof data backup — evidence trail (JSONL + snapshots) and SQLite.
# Usage: bash deploy/backup.sh [output-dir]     (default: ./backups)
# Restore instructions: see DEPLOY.md § Restore.
set -euo pipefail

APP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_ROOT"
# Configuration: same guarded .env sourcing deploy-check.sh uses. systemd hands
# the timer these values via EnvironmentFile, but a MANUAL run (UPDATE.md step 1,
# DEPLOY.md "Manual run") has an empty environment — without this the script took
# the LOCAL-ONLY branch on a correctly configured droplet, false-paged the founder
# and genuinely skipped the off-box push of the mandatory pre-update archive.
# Idempotent under systemd (same values re-exported). `-r` not `-f`: bash EXITS
# when `.` cannot open the file — neither `2>/dev/null` nor `|| true` catches
# that — so an unreadable .env would abort the backup under `set -euo pipefail`.
# `+u` around the `.` for the same class of reason: under `set -u` an unset
# expansion INSIDE a value (a password-manager passphrase containing `$NOPE`)
# is fatal to the sourcing shell, `|| true` never runs, and the backup died
# here — before the sqlite copy, so no local archive either — with no output at
# all. No stderr redirect: a bad .env must reach the journal, not vanish.
[ -r .env ] && { set -a +u; . ./.env || true; set +a -u; }

# Which host is this? The dev-only fail-open overrides
# (STATUTEPROOF_ALLOW_UNENCRYPTED_BACKUP / STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY)
# must not be honoured on production: they defeat the encryption and off-box
# gates, and a deploy-check verdict cannot protect a run that reads .env
# directly. ENVIRONMENT is the codebase's own environment signal
# (app/config.py); the documented production install path is a second,
# independent signal for a host whose .env failed to load; STATUTEPROOF_ENV
# wins over both for a non-standard install. Kept byte-identical in
# deploy/deploy-check.sh so the gate and this script agree.
STATUTEPROOF_IS_PROD=0
case "${STATUTEPROOF_ENV:-${ENVIRONMENT:-}}" in
  production|prod) STATUTEPROOF_IS_PROD=1 ;;
esac
if [ "$APP_ROOT" = "/srv/regradar" ]; then STATUTEPROOF_IS_PROD=1; fi
# Neutralise them here, ahead of every branch that reads them, so no later
# condition can be fooled — and say so loudly rather than silently ignoring
# what the operator wrote.
if [ "$STATUTEPROOF_IS_PROD" = "1" ]; then
  for _ovr in STATUTEPROOF_ALLOW_UNENCRYPTED_BACKUP STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY; do
    if [ "${!_ovr:-}" = "1" ]; then
      echo "WARNING: $_ovr=1 is a DEVELOPMENT override and is REFUSED on a production host — ignoring it (DEPLOY.md § 9)" >&2
      unset "$_ovr"
    fi
  done
fi

OUT_DIR="${1:-$APP_ROOT/backups}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

PY_BIN="${PY_BIN:-$APP_ROOT/.venv/bin/python}"
[ -x "$PY_BIN" ] || PY_BIN="$(command -v python3)"

# Founder paging (best-effort, NEVER fatal): local-only mode and failed off-box
# pushes must page the founder via the admin Telegram bot (app/ops_alert.py —
# the same channel the heartbeat/integrity watchdogs use), not just whisper to
# stderr where nobody looks between deploys. Guarded so a broken venv/import
# can never abort the backup itself.
page_founder() {
  "$PY_BIN" - "$1" <<'PYEOF' || echo "WARNING: founder page failed (non-fatal); message was: $1" >&2
import sys
sys.path.insert(0, ".")
from app.ops_alert import notify_founder
notify_founder(sys.argv[1])
PYEOF
}

mkdir -p "$OUT_DIR"

# 1) Consistent SQLite copy via the online-backup API (safe while services run).
"$PY_BIN" - "$WORK/regradar.db" <<'EOF'
import sqlite3, sys
sys.path.insert(0, ".")
from app.config import DB_PATH
src = sqlite3.connect(DB_PATH)
dst = sqlite3.connect(sys.argv[1])
src.backup(dst)
dst.close(); src.close()
print(f"sqlite backup: {DB_PATH} -> {sys.argv[1]}")
EOF

# 2) Evidence trail + artifacts.
ARCHIVE="$OUT_DIR/statuteproof-backup-$STAMP.tar.gz"
# evidence/ holds the SEALED canonical evidence records — the artifacts the
# product sells as durable proof. Omitting it meant droplet loss destroyed the
# very records customers rely on. Conditional: absent until the first seal.
EVIDENCE_DIR=""
[ -d "$APP_ROOT/evidence" ] && EVIDENCE_DIR="evidence"
# --ignore-failed-read (GNU tar only — the droplet): the live auto-seal
# creates and, on failure, rmtree's record dirs concurrently with this walk;
# a file vanishing mid-backup must degrade to a warning, not abort the run
# under `set -e` (which would also skip the off-box push AND retention).
TAR_FLAGS=""
if tar --version 2>/dev/null | grep -q "GNU tar"; then
  TAR_FLAGS="--ignore-failed-read"
fi
tar -czf "$ARCHIVE" $TAR_FLAGS \
  --exclude='data/outbox' \
  -C "$WORK" regradar.db \
  -C "$APP_ROOT" data sources.json .env.example $EVIDENCE_DIR

echo "backup written: $ARCHIVE ($(du -h "$ARCHIVE" | cut -f1))"

# Deferred founder page — set below, sent once after retention.
BACKUP_PAGE_MSG=""

# 3) ENCRYPT before anything leaves the box. The archive contains regradar.db:
# password hashes, emails, telegram_chat_ids AND the sessions table, whose ids
# are bearer credentials — one readable archive replays live sessions until
# they expire. Making the off-box remote mandatory (deploy-check, 2026-07-20)
# turned "might" into a standing obligation, so the push is now encrypted or
# it does not happen. Key material never touches disk on the droplet: age uses
# a PUBLIC recipient key (the private key stays off-box with the owner), gpg
# reads its passphrase on fd 0 — never argv, never a temp file.
# The ciphertext lives only in $WORK and dies with the trap; the LOCAL archive
# in backups/ stays plaintext on purpose — the droplet already holds the live
# database, so it adds no new exposure there, and retention + the restore path
# (DEPLOY.md § Restore) keep working unchanged.
PUSH_FILE=""
if [ -n "${STATUTEPROOF_BACKUP_REMOTE:-}" ]; then
  ENC_OUT="$WORK/$(basename "$ARCHIVE")"
  if [ "${STATUTEPROOF_ALLOW_UNENCRYPTED_BACKUP:-}" = "1" ]; then
    echo "WARNING: STATUTEPROOF_ALLOW_UNENCRYPTED_BACKUP=1 — pushing the archive UNENCRYPTED off-box (dev only; never on prod)" >&2
    PUSH_FILE="$ARCHIVE"
  elif [ -n "${STATUTEPROOF_BACKUP_AGE_RECIPIENT:-}" ] && command -v age >/dev/null 2>&1; then
    if age -r "$STATUTEPROOF_BACKUP_AGE_RECIPIENT" -o "$ENC_OUT.age" "$ARCHIVE"; then
      PUSH_FILE="$ENC_OUT.age"
      echo "encrypted for off-box push (age): $(basename "$PUSH_FILE")"
    else
      echo "WARNING: age encryption FAILED — refusing to push the archive in clear" >&2
      BACKUP_PAGE_MSG="🚨 StatuteProof backup encryption FAILED (age): the off-box push was REFUSED rather than sending password hashes and live session ids in clear. Check STATUTEPROOF_BACKUP_AGE_RECIPIENT (DEPLOY.md § 9)."
    fi
  elif [ -n "${STATUTEPROOF_BACKUP_PASSPHRASE:-}" ] && command -v gpg >/dev/null 2>&1; then
    if printf '%s' "$STATUTEPROOF_BACKUP_PASSPHRASE" | gpg --batch --yes --quiet --pinentry-mode loopback --passphrase-fd 0 --symmetric --cipher-algo AES256 -o "$ENC_OUT.gpg" "$ARCHIVE"; then
      PUSH_FILE="$ENC_OUT.gpg"
      echo "encrypted for off-box push (gpg): $(basename "$PUSH_FILE")"
    else
      echo "WARNING: gpg encryption FAILED — refusing to push the archive in clear" >&2
      BACKUP_PAGE_MSG="🚨 StatuteProof backup encryption FAILED (gpg): the off-box push was REFUSED rather than sending password hashes and live session ids in clear. Check STATUTEPROOF_BACKUP_PASSPHRASE (DEPLOY.md § 9)."
    fi
  else
    echo "WARNING: no usable backup encryption (need STATUTEPROOF_BACKUP_AGE_RECIPIENT + age, or STATUTEPROOF_BACKUP_PASSPHRASE + gpg) — off-box push REFUSED" >&2
    BACKUP_PAGE_MSG="🚨 StatuteProof off-box backup push REFUSED: no usable encryption on the droplet. The archive carries password hashes and live session ids, so it is never pushed in clear. Set STATUTEPROOF_BACKUP_AGE_RECIPIENT (+ install age) or STATUTEPROOF_BACKUP_PASSPHRASE (+ install gnupg) in /srv/regradar/.env (DEPLOY.md § 9)."
  fi
fi

# 4) Off-box copy so the archive survives droplet loss. STRONGLY RECOMMENDED:
# an off-box remote is the only thing that protects the evidence trail if the
# droplet is lost. It stays env-driven (we can't hardcode a remote), so it is a
# no-op unless STATUTEPROOF_BACKUP_REMOTE is set — but local-only mode is never
# silent: when the var is UNSET we warn loudly on stderr every run. The value is
# an rclone remote (e.g. s3:bucket/path) when rclone is installed, otherwise an
# scp target (e.g. user@host:/path). See DEPLOY.md § 9 for setup.
if [ -z "${STATUTEPROOF_BACKUP_REMOTE:-}" ]; then
  echo "WARNING: STATUTEPROOF_BACKUP_REMOTE is unset — backups are LOCAL-ONLY on this droplet;" >&2
  echo "WARNING: the evidence trail is NOT protected against droplet loss. Set STATUTEPROOF_BACKUP_REMOTE in .env (see DEPLOY.md § 9) to push each archive off-box." >&2
  if [ "${STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY:-}" != "1" ]; then
    BACKUP_PAGE_MSG="⚠️ StatuteProof backup ran LOCAL-ONLY: STATUTEPROOF_BACKUP_REMOTE is unset, so the evidence trail does NOT survive droplet loss. Set it in /srv/regradar/.env (DEPLOY.md § 9)."
  fi
fi

# F-MEDIUM: the push is NON-FATAL. Under `set -euo pipefail` a failed rclone/scp
# (network down, bad creds) would otherwise abort the script BEFORE step 4, so
# retention pruning would stop running and old backups would pile up. The whole
# block runs in a guarded `if` (a failing command inside an `if` condition does
# not trip errexit), and any failure logs a warning and continues. The local
# archive is already safely written above (step 2), so a failed off-box copy
# never loses data — it only skips the remote copy for this run.
if [ -n "${STATUTEPROOF_BACKUP_REMOTE:-}" ] && [ -n "$PUSH_FILE" ]; then
  if command -v rclone >/dev/null 2>&1; then
    if rclone copy "$PUSH_FILE" "$STATUTEPROOF_BACKUP_REMOTE"; then
      echo "off-box copy (rclone): $PUSH_FILE -> $STATUTEPROOF_BACKUP_REMOTE"
    else
      echo "WARNING: off-box copy (rclone) failed; local archive kept, continuing to retention" >&2
      BACKUP_PAGE_MSG="🚨 StatuteProof off-box backup push FAILED (rclone). The archive exists only on the droplet. Check: journalctl -u statuteproof-backup"
    fi
  else
    if scp "$PUSH_FILE" "$STATUTEPROOF_BACKUP_REMOTE"; then
      echo "off-box copy (scp): $PUSH_FILE -> $STATUTEPROOF_BACKUP_REMOTE"
    else
      echo "WARNING: off-box copy (scp) failed; local archive kept, continuing to retention" >&2
      BACKUP_PAGE_MSG="🚨 StatuteProof off-box backup push FAILED (scp). The archive exists only on the droplet. Check: journalctl -u statuteproof-backup"
    fi
  fi
fi

# 5) Retention: keep the newest 14 backups.
ls -1t "$OUT_DIR"/statuteproof-backup-*.tar.gz 2>/dev/null | tail -n +15 | while read -r old; do
  rm -f "$old"
  echo "pruned old backup: $old"
done

# 6) Deferred founder page (single message per run; see page_founder above).
if [ -n "$BACKUP_PAGE_MSG" ]; then
  page_founder "$BACKUP_PAGE_MSG"
fi
