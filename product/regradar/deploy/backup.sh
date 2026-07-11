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

# 2) Evidence trail + artifacts. --ignore-failed-read: a file rotated away
# mid-backup must not kill the whole archive.
ARCHIVE="$OUT_DIR/statuteproof-backup-$STAMP.tar.gz"
tar -czf "$ARCHIVE" \
  --exclude='data/outbox' \
  -C "$WORK" regradar.db \
  -C "$APP_ROOT" data sources.json .env.example

echo "backup written: $ARCHIVE ($(du -h "$ARCHIVE" | cut -f1))"

# 3) Optional off-box copy so the archive survives droplet loss. No-op unless
# STATUTEPROOF_BACKUP_REMOTE is set. Value is an rclone remote (e.g. s3:bucket/path)
# when rclone is installed, otherwise an scp target (e.g. user@host:/path).
if [ -n "${STATUTEPROOF_BACKUP_REMOTE:-}" ]; then
  if command -v rclone >/dev/null 2>&1; then
    rclone copy "$ARCHIVE" "$STATUTEPROOF_BACKUP_REMOTE"
    echo "off-box copy (rclone): $ARCHIVE -> $STATUTEPROOF_BACKUP_REMOTE"
  else
    scp "$ARCHIVE" "$STATUTEPROOF_BACKUP_REMOTE"
    echo "off-box copy (scp): $ARCHIVE -> $STATUTEPROOF_BACKUP_REMOTE"
  fi
fi

# 4) Retention: keep the newest 14 backups.
ls -1t "$OUT_DIR"/statuteproof-backup-*.tar.gz 2>/dev/null | tail -n +15 | while read -r old; do
  rm -f "$old"
  echo "pruned old backup: $old"
done
