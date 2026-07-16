#!/usr/bin/env bash
# StatuteProof data backup — evidence trail (JSONL + snapshots) and SQLite.
# Usage: bash deploy/backup.sh [output-dir]     (default: ./backups)
# Restore instructions: see DEPLOY.md § Restore.
set -euo pipefail

APP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_ROOT"
OUT_DIR="${1:-$APP_ROOT/backups}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

PY_BIN="${PY_BIN:-$APP_ROOT/.venv/bin/python}"
[ -x "$PY_BIN" ] || PY_BIN="$(command -v python3)"

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

# 3) Off-box copy so the archive survives droplet loss. STRONGLY RECOMMENDED:
# an off-box remote is the only thing that protects the evidence trail if the
# droplet is lost. It stays env-driven (we can't hardcode a remote), so it is a
# no-op unless STATUTEPROOF_BACKUP_REMOTE is set — but local-only mode is never
# silent: when the var is UNSET we warn loudly on stderr every run. The value is
# an rclone remote (e.g. s3:bucket/path) when rclone is installed, otherwise an
# scp target (e.g. user@host:/path). See DEPLOY.md § 9 for setup.
if [ -z "${STATUTEPROOF_BACKUP_REMOTE:-}" ]; then
  echo "WARNING: STATUTEPROOF_BACKUP_REMOTE is unset — backups are LOCAL-ONLY on this droplet;" >&2
  echo "WARNING: the evidence trail is NOT protected against droplet loss. Set STATUTEPROOF_BACKUP_REMOTE in .env (see DEPLOY.md § 9) to push each archive off-box." >&2
fi

# F-MEDIUM: the push is NON-FATAL. Under `set -euo pipefail` a failed rclone/scp
# (network down, bad creds) would otherwise abort the script BEFORE step 4, so
# retention pruning would stop running and old backups would pile up. The whole
# block runs in a guarded `if` (a failing command inside an `if` condition does
# not trip errexit), and any failure logs a warning and continues. The local
# archive is already safely written above (step 2), so a failed off-box copy
# never loses data — it only skips the remote copy for this run.
if [ -n "${STATUTEPROOF_BACKUP_REMOTE:-}" ]; then
  if command -v rclone >/dev/null 2>&1; then
    if rclone copy "$ARCHIVE" "$STATUTEPROOF_BACKUP_REMOTE"; then
      echo "off-box copy (rclone): $ARCHIVE -> $STATUTEPROOF_BACKUP_REMOTE"
    else
      echo "WARNING: off-box copy (rclone) failed; local archive kept, continuing to retention" >&2
    fi
  else
    if scp "$ARCHIVE" "$STATUTEPROOF_BACKUP_REMOTE"; then
      echo "off-box copy (scp): $ARCHIVE -> $STATUTEPROOF_BACKUP_REMOTE"
    else
      echo "WARNING: off-box copy (scp) failed; local archive kept, continuing to retention" >&2
    fi
  fi
fi

# 4) Retention: keep the newest 14 backups.
ls -1t "$OUT_DIR"/statuteproof-backup-*.tar.gz 2>/dev/null | tail -n +15 | while read -r old; do
  rm -f "$old"
  echo "pruned old backup: $old"
done
