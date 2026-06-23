#!/usr/bin/env bash
# scripts/setup_cron.sh — Print the crontab entry for the daily DB backup
#
# This script does NOT automatically modify your crontab.
# It prints the exact line you need to add, then gives you instructions.
#
# Usage:
#   bash scripts/setup_cron.sh
#
# Make executable:
#   chmod +x scripts/setup_cron.sh

set -euo pipefail

# ── Resolve the absolute path to the project root ────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

CRON_LINE="0 2 * * * cd ${PROJECT_DIR} && bash scripts/backup_db.sh >> logs/backup.log 2>&1"

echo ""
echo "============================================================"
echo "  StatuteProof — Daily DB Backup Cron Setup"
echo "============================================================"
echo ""
echo "  WARNING: Review the path below before adding it."
echo "  The path was auto-detected from the location of this script."
echo "  If you deploy to a different server, update the path manually."
echo ""
echo "  Detected project root:"
echo "    ${PROJECT_DIR}"
echo ""
echo "  Crontab entry to add (runs every day at 02:00 AM):"
echo ""
echo "    ${CRON_LINE}"
echo ""
echo "------------------------------------------------------------"
echo "  How to install:"
echo ""
echo "  Option A — edit crontab interactively:"
echo "    crontab -e"
echo "    (paste the line above, save, and exit)"
echo ""
echo "  Option B — append non-interactively (run as yourself):"
echo "    (crontab -l 2>/dev/null; echo \"${CRON_LINE}\") | crontab -"
echo ""
echo "  Verify the entry was added:"
echo "    crontab -l"
echo ""
echo "  Backup logs will appear in:"
echo "    ${PROJECT_DIR}/logs/backup.log"
echo ""
echo "  Test a manual run now:"
echo "    bash ${PROJECT_DIR}/scripts/backup_db.sh"
echo ""
echo "============================================================"
echo ""
