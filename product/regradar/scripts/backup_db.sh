#!/usr/bin/env bash
# scripts/backup_db.sh — WAL-safe SQLite backup for StatuteProof / RegRadar
#
# Usage:
#   bash scripts/backup_db.sh
#
# Make executable:
#   chmod +x scripts/backup_db.sh
#
# Designed to be called from a crontab entry or manually.
# Keeps the last 7 backups and removes older ones.
# Exits with a non-zero code on any failure.

set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────────
# Resolve paths relative to this script so it works from any working directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

DB_PATH="${PROJECT_DIR}/data/source_runs.db"
BACKUP_DIR="${PROJECT_DIR}/data/backups"
KEEP_LAST=7

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/source_runs_${TIMESTAMP}.db"

# ── Logging helper ─────────────────────────────────────────────────────────────
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

log "=== StatuteProof DB backup starting ==="

# ── Guard: database must exist ────────────────────────────────────────────────
if [[ ! -f "${DB_PATH}" ]]; then
    log "ERROR: Database not found at ${DB_PATH}"
    exit 1
fi

# ── Guard: sqlite3 must be available ─────────────────────────────────────────
if ! command -v sqlite3 &>/dev/null; then
    log "ERROR: sqlite3 is not installed or not on PATH"
    exit 1
fi

# ── Create backup directory if needed ────────────────────────────────────────
if [[ ! -d "${BACKUP_DIR}" ]]; then
    log "Creating backup directory: ${BACKUP_DIR}"
    mkdir -p "${BACKUP_DIR}"
fi

# ── Perform WAL-safe backup via SQLite .backup pragma ─────────────────────────
# The .backup command is the only truly WAL-safe way to copy a live SQLite DB.
# A plain cp can capture a torn write if a WAL checkpoint fires mid-copy.
log "Backing up ${DB_PATH} -> ${BACKUP_FILE}"
sqlite3 "${DB_PATH}" ".backup ${BACKUP_FILE}"

if [[ ! -f "${BACKUP_FILE}" ]]; then
    log "ERROR: Backup file was not created — sqlite3 may have failed silently"
    exit 1
fi

BACKUP_SIZE="$(du -sh "${BACKUP_FILE}" | cut -f1)"
log "Backup complete: ${BACKUP_FILE} (${BACKUP_SIZE})"

# ── Prune: keep only the last KEEP_LAST backups ───────────────────────────────
# List files by modification time (oldest first), then delete all but the
# newest KEEP_LAST files. This is portable across Linux and macOS.
BACKUP_COUNT="$(find "${BACKUP_DIR}" -maxdepth 1 -name 'source_runs_*.db' | wc -l | tr -d ' ')"

if (( BACKUP_COUNT > KEEP_LAST )); then
    DELETE_COUNT=$(( BACKUP_COUNT - KEEP_LAST ))
    log "Pruning ${DELETE_COUNT} old backup(s) (keeping last ${KEEP_LAST})"

    # Sort by name (timestamps in filename make lexicographic == chronological)
    # and remove the oldest ones.
    find "${BACKUP_DIR}" -maxdepth 1 -name 'source_runs_*.db' \
        | sort \
        | head -n "${DELETE_COUNT}" \
        | while IFS= read -r old_file; do
            log "  Deleting: ${old_file}"
            rm -f "${old_file}"
        done
else
    log "No pruning needed (${BACKUP_COUNT} backup(s) stored, limit ${KEEP_LAST})"
fi

log "=== Backup finished successfully ==="
