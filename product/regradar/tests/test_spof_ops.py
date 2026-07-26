"""
spof-ops: single-droplet fatality elimination (audit 2026-07-20).

The whole product — API, scheduler, evidence trail, backups AND the watchdog
that pages the founder — lives on one droplet. Three confirmed HIGHs follow:

1. A missing off-box backup remote was only a stderr warning, so a droplet
   loss silently destroys the sealed evidence trail the product sells.
   -> deploy-check now FAILS when STATUTEPROOF_BACKUP_REMOTE is unset
      (STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY=1 is a documented dev-only
      override), and backup.sh pages the founder via app/ops_alert.py when
      the off-box push fails or is skipped.

2. The deadman watchdog (statuteproof-heartbeat.timer) runs ON the droplet it
   watches — a dead droplet can never page. -> after a SUCCESSFUL internal
   heartbeat check, ops_alert pings an owner-created external service
   (STATUTEPROOF_HEARTBEAT_PING_URL, healthchecks.io / UptimeRobot style);
   the external service alerts when pings STOP arriving.

3. The update/rollback runbook referenced by RESET_RUNBOOK.md did not exist
   and the old runbooks describe a retired nginx stack. -> UPDATE.md exists
   and matches the real Caddy + systemd + /srv/regradar architecture; the
   stale runbooks carry a SUPERSEDED banner.

Shell blocks are pinned with the same literal + drift-guard pattern as
tests/test_backup_offbox_and_systemd.py and run in isolated bash with stub
binaries, so no real DB, network, or Telegram traffic is needed.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

REPO_ROOT = Path(__file__).parent.parent
DEPLOY = REPO_ROOT / "deploy"
BACKUP_SH = DEPLOY / "backup.sh"
DEPLOY_CHECK_SH = DEPLOY / "deploy-check.sh"

BASH = shutil.which("bash")
requires_bash = pytest.mark.skipif(BASH is None, reason="bash not available")

# Guarded .env sourcing shared by backup.sh and deploy-check.sh: `+u` around the
# `.` so an unset expansion inside a value cannot kill the sourcing shell, and no
# stderr redirect so a bad .env still reaches the journal/operator.
_ENV_SOURCE_LINE = 'set -a +u; . ./.env || true; set +a -u'


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ══════════════════════════════════════════════════════════════════════════
# Part A — deploy-check.sh: missing off-box backup remote is a FAILURE
# ══════════════════════════════════════════════════════════════════════════

# The exact section as it appears in deploy/deploy-check.sh. Run in isolation
# with stubbed ok/bad/warn helpers so the test needs no venv, .env or DB.
_DEPLOY_CHECK_BACKUP_BLOCK = """\
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
[ -n "${STATUTEPROOF_HEARTBEAT_PING_URL:-}" ] \\
  && ok "STATUTEPROOF_HEARTBEAT_PING_URL set — external uptime probe wired" \\
  || warn "STATUTEPROOF_HEARTBEAT_PING_URL empty — no external uptime probe (see DEPLOY.md § External uptime probe)"
"""

# Same set -uo pipefail regime as deploy-check.sh itself, plus stub helpers
# mirroring its ok()/bad()/warn() (bad sets FAIL=1; exit "$FAIL" at the end
# mirrors the script's final gate).
_HARNESS_PREFIX = 'set -uo pipefail\nFAIL=0\nok(){ echo "OK:$1"; }\nbad(){ echo "BAD:$1"; FAIL=1; }\nwarn(){ echo "WARN:$1"; }\n'


def _run_deploy_check_block(env_extra: dict[str, str]):
    # The gate branches read STATUTEPROOF_IS_PROD, so the detection block runs
    # in front of them exactly as it does in deploy-check.sh (see Part G).
    return _run_gate_block(_DEPLOY_CHECK_BACKUP_BLOCK, env_extra)


@requires_bash
def test_deploy_check_fails_when_backup_remote_unset():
    """No remote, no override -> the gate FAILS (exit 1) and names the var."""
    result = _run_deploy_check_block({})
    assert result.returncode == 1, result.stdout + result.stderr
    bad_lines = [l for l in result.stdout.splitlines() if l.startswith("BAD:")]
    assert len(bad_lines) == 1
    assert "STATUTEPROOF_BACKUP_REMOTE" in bad_lines[0]


@requires_bash
def test_deploy_check_dev_override_downgrades_to_warning():
    """Documented dev override -> warn (not bad), gate passes."""
    result = _run_deploy_check_block({"STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY": "1"})
    assert result.returncode == 0, result.stdout + result.stderr
    assert "BAD:" not in result.stdout
    assert any(
        l.startswith("WARN:") and "LOCAL-ONLY" in l
        for l in result.stdout.splitlines()
    )


@requires_bash
def test_deploy_check_passes_when_remote_set():
    result = _run_deploy_check_block({"STATUTEPROOF_BACKUP_REMOTE": "s3:bucket/path"})
    assert result.returncode == 0, result.stdout + result.stderr
    assert "BAD:" not in result.stdout
    assert any(
        l.startswith("OK:") and "STATUTEPROOF_BACKUP_REMOTE" in l
        for l in result.stdout.splitlines()
    )


@requires_bash
def test_deploy_check_warns_when_ping_url_unset():
    """External probe is optional -> warn only, never a failure."""
    result = _run_deploy_check_block({"STATUTEPROOF_BACKUP_REMOTE": "s3:bucket/path"})
    assert result.returncode == 0
    assert any(
        l.startswith("WARN:") and "STATUTEPROOF_HEARTBEAT_PING_URL" in l
        for l in result.stdout.splitlines()
    )


@requires_bash
def test_deploy_check_oks_when_ping_url_set():
    result = _run_deploy_check_block(
        {
            "STATUTEPROOF_BACKUP_REMOTE": "s3:bucket/path",
            "STATUTEPROOF_HEARTBEAT_PING_URL": "https://hc-ping.example/uuid",
        }
    )
    assert result.returncode == 0
    assert any(
        l.startswith("OK:") and "STATUTEPROOF_HEARTBEAT_PING_URL" in l
        for l in result.stdout.splitlines()
    )
    assert "WARN:STATUTEPROOF_HEARTBEAT_PING_URL" not in result.stdout


def test_deploy_check_backup_block_matches_script():
    """The literal block tested above is present verbatim (drift guard)."""
    assert _DEPLOY_CHECK_BACKUP_BLOCK.strip() in _read(DEPLOY_CHECK_SH)


# ══════════════════════════════════════════════════════════════════════════
# Part B — backup.sh pages the founder on local-only / failed off-box push
# ══════════════════════════════════════════════════════════════════════════

# page_founder() as defined in backup.sh: invokes "$PY_BIN" - "$MSG" with the
# python body on stdin, guarded by || so a broken venv can never abort the
# backup under errexit.
_PAGE_FOUNDER_FN = """\
page_founder() {
  "$PY_BIN" - "$1" <<'PYEOF' || echo "WARNING: founder page failed (non-fatal); message was: $1" >&2
import sys
sys.path.insert(0, ".")
from app.ops_alert import notify_founder
notify_founder(sys.argv[1])
PYEOF
}
"""

# The warn block after spof-ops: unchanged WARNING echoes + a deferred page
# unless the documented dev override acknowledges local-only mode.
_WARN_BLOCK = """\
if [ -z "${STATUTEPROOF_BACKUP_REMOTE:-}" ]; then
  echo "WARNING: STATUTEPROOF_BACKUP_REMOTE is unset — backups are LOCAL-ONLY on this droplet;" >&2
  echo "WARNING: the evidence trail is NOT protected against droplet loss. Set STATUTEPROOF_BACKUP_REMOTE in .env (see DEPLOY.md § 9) to push each archive off-box." >&2
  if [ "${STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY:-}" != "1" ]; then
    BACKUP_PAGE_MSG="⚠️ StatuteProof backup ran LOCAL-ONLY: STATUTEPROOF_BACKUP_REMOTE is unset, so the evidence trail does NOT survive droplet loss. Set it in /srv/regradar/.env (DEPLOY.md § 9)."
  fi
fi
"""

# The push block after spof-ops: each failure branch records a deferred page.
_OFFBOX_BLOCK = """\
if [ -n "${STATUTEPROOF_BACKUP_REMOTE:-}" ] && [ -n "$PUSH_FILE" ]; then
  if command -v rclone >/dev/null 2>&1; then
    if rclone copy "$PUSH_FILE" "$STATUTEPROOF_BACKUP_REMOTE"; then
      echo "off-box copy (rclone): $PUSH_FILE -> $STATUTEPROOF_BACKUP_REMOTE"
    else
      echo "WARNING: off-box copy (rclone) failed; local archive kept, continuing to retention" >&2
      BACKUP_PAGE_MSG="🚨 StatuteProof off-box backup push FAILED (rclone). The archive exists only on the droplet. Check: journalctl -u statuteproof-backup"
    fi
  else
    if scp -o ConnectTimeout=30 -o ServerAliveInterval=15 -o ServerAliveCountMax=4 "$PUSH_FILE" "$STATUTEPROOF_BACKUP_REMOTE"; then
      echo "off-box copy (scp): $PUSH_FILE -> $STATUTEPROOF_BACKUP_REMOTE"
    else
      echo "WARNING: off-box copy (scp) failed; local archive kept, continuing to retention" >&2
      BACKUP_PAGE_MSG="🚨 StatuteProof off-box backup push FAILED (scp). The archive exists only on the droplet. Check: journalctl -u statuteproof-backup"
    fi
  fi
fi
"""

# Final step: one deferred page per run, only when something went wrong.
_PAGING_BLOCK = """\
# 6) Deferred founder page (single message per run; see page_founder above).
if [ -n "$BACKUP_PAGE_MSG" ]; then
  page_founder "$BACKUP_PAGE_MSG"
fi
"""

_ACCUM_INIT = 'BACKUP_PAGE_MSG=""\n'

# .env sourcing, as it appears in backup.sh right after `cd "$APP_ROOT"`.
# Without it a MANUAL run (UPDATE.md step 1, DEPLOY.md "Manual run") sees only
# the process environment, so a correctly configured droplet still takes the
# LOCAL-ONLY branch: false warning, false founder page, and NO off-box push.
# `-r` (not `-f`): bash EXITS when `.` cannot open the file, and neither
# `2>/dev/null` nor `|| true` catches that — an unreadable .env would abort the
# mandatory pre-update archive outright.
_ENV_SOURCE_BLOCK = """\
[ -r .env ] && { set -a +u; . ./.env || true; set +a -u; }
"""


def test_page_founder_fn_matches_script():
    assert _PAGE_FOUNDER_FN.strip() in _read(BACKUP_SH)


def test_paging_block_matches_script():
    assert _PAGING_BLOCK.strip() in _read(BACKUP_SH)


def test_warn_block_with_page_matches_script():
    assert _WARN_BLOCK.strip() in _read(BACKUP_SH)


def test_offbox_block_with_page_matches_script():
    assert _OFFBOX_BLOCK.strip() in _read(BACKUP_SH)


def _stub_py(tmp_path: Path, *, fail: bool = False) -> Path:
    """Stub PY_BIN: drains the heredoc stdin, records the paged message."""
    p = tmp_path / "bin" / "py"
    p.parent.mkdir(exist_ok=True)
    exit_code = 1 if fail else 0
    p.write_text(
        '#!/usr/bin/env bash\ncat > /dev/null\n'
        f'echo "paged:$2" >> "$sentinel"\nexit {exit_code}\n'
    )
    p.chmod(0o755)
    return p


def _paged_lines(tmp_path: Path) -> list[str]:
    sentinel = tmp_path / "called.log"
    if not sentinel.exists():
        return []
    return [l for l in sentinel.read_text().splitlines() if l.startswith("paged:")]


def _run_warn_page(tmp_path: Path, env_extra: dict[str, str], *, py_fails: bool = False):
    """Isolated run: page_founder + accumulator + warn block + final page."""
    stub = _stub_py(tmp_path, fail=py_fails)
    env = {
        "PATH": "/usr/bin:/bin",
        "PY_BIN": str(stub),
        "sentinel": str(tmp_path / "called.log"),
    }
    env.update(env_extra)
    body = _PAGE_FOUNDER_FN + _ACCUM_INIT + _WARN_BLOCK + _PAGING_BLOCK
    return subprocess.run(
        [BASH, "-c", "set -euo pipefail\n" + body],
        capture_output=True,
        text=True,
        env=env,
    )


@requires_bash
def test_backup_pages_founder_when_local_only(tmp_path):
    """Remote unset, no override -> exactly one LOCAL-ONLY page, exit 0."""
    result = _run_warn_page(tmp_path, {})
    assert result.returncode == 0, result.stderr
    pages = _paged_lines(tmp_path)
    assert len(pages) == 1
    assert "LOCAL-ONLY" in pages[0]


@requires_bash
def test_backup_local_only_override_suppresses_page(tmp_path):
    """STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY=1 acknowledges local-only: no page."""
    result = _run_warn_page(tmp_path, {"STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY": "1"})
    assert result.returncode == 0, result.stderr
    assert _paged_lines(tmp_path) == []
    # ...but the stderr warning stays: the override silences the page, not the log.
    assert "LOCAL-ONLY" in result.stderr


@requires_bash
def test_backup_no_page_when_remote_set(tmp_path):
    result = _run_warn_page(tmp_path, {"STATUTEPROOF_BACKUP_REMOTE": "s3:bucket/path"})
    assert result.returncode == 0, result.stderr
    assert _paged_lines(tmp_path) == []
    assert "LOCAL-ONLY" not in result.stderr


@requires_bash
def test_backup_page_failure_is_nonfatal(tmp_path):
    """A broken PY_BIN must not abort the backup: exit 0 + stderr warning."""
    result = _run_warn_page(tmp_path, {}, py_fails=True)
    assert result.returncode == 0, result.stderr
    assert "founder page failed (non-fatal)" in result.stderr


def _run_env_sourced_warn_page(tmp_path: Path, cwd: Path):
    """Manual-run shape: .env sourcing FIRST, then the local-only warn/page.

    The process environment carries no STATUTEPROOF_* values at all — exactly
    what `sudo -u regradar bash /srv/regradar/deploy/backup.sh` gives you.
    """
    stub = _stub_py(tmp_path)
    env = {
        "PATH": "/usr/bin:/bin",
        "PY_BIN": str(stub),
        "sentinel": str(tmp_path / "called.log"),
    }
    body = _ENV_SOURCE_BLOCK + _PAGE_FOUNDER_FN + _ACCUM_INIT + _WARN_BLOCK + _PAGING_BLOCK
    return subprocess.run(
        [BASH, "-c", "set -euo pipefail\n" + body],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(cwd),
    )


@requires_bash
def test_backup_manual_run_reads_remote_from_dotenv(tmp_path):
    """A manual run on a configured droplet must NOT warn and must NOT page.

    backup.sh reads STATUTEPROOF_BACKUP_REMOTE from the environment; systemd
    supplies it via EnvironmentFile, but a manual run has an empty environment,
    so without sourcing .env the script false-pages the founder and skips the
    off-box push of the mandatory pre-update archive.
    """
    work = tmp_path / "app"
    work.mkdir()
    (work / ".env").write_text("STATUTEPROOF_BACKUP_REMOTE=s3:bucket/path\n")

    result = _run_env_sourced_warn_page(tmp_path, work)
    assert result.returncode == 0, result.stderr
    assert _paged_lines(tmp_path) == []
    assert "LOCAL-ONLY" not in result.stderr


@requires_bash
def test_backup_dotenv_sourcing_is_safe_without_dotenv(tmp_path):
    """No .env at all: errexit must not trip, behaviour is the old local-only."""
    work = tmp_path / "app"
    work.mkdir()

    result = _run_env_sourced_warn_page(tmp_path, work)
    assert result.returncode == 0, result.stderr
    pages = _paged_lines(tmp_path)
    assert len(pages) == 1
    assert "LOCAL-ONLY" in pages[0]


@requires_bash
def test_backup_dotenv_sourcing_is_safe_when_dotenv_unreadable(tmp_path):
    """An unreadable .env degrades to local-only, never aborts the backup."""
    work = tmp_path / "app"
    work.mkdir()
    env_file = work / ".env"
    env_file.write_text("STATUTEPROOF_BACKUP_REMOTE=s3:bucket/path\n")
    env_file.chmod(0o000)

    try:
        result = _run_env_sourced_warn_page(tmp_path, work)
    finally:
        env_file.chmod(0o600)
    assert result.returncode == 0, result.stderr


def test_backup_sh_sources_dotenv_before_remote_check():
    """Drift guard: the sourcing runs after the cd and before every consumer."""
    text = _read(BACKUP_SH)
    line = _ENV_SOURCE_BLOCK.strip()
    assert line in text, "backup.sh no longer sources .env for manual runs"
    idx = text.index(line)
    assert idx > text.index('cd "$APP_ROOT"'), "sourcing must follow the cd to APP_ROOT"
    assert idx < text.index("PY_BIN="), "sourcing must precede PY_BIN resolution"
    assert idx < text.index(
        'if [ -z "${STATUTEPROOF_BACKUP_REMOTE:-}" ]; then'
    ), "sourcing must precede the off-box remote check"


def _run_offbox_page(tmp_path: Path, *, push_fails: bool):
    """Isolated run: page_founder + accumulator + push block + final page,
    with a stub rclone on PATH (mirrors _run_offbox in
    tests/test_backup_offbox_and_systemd.py)."""
    binn = tmp_path / "bin"
    binn.mkdir(exist_ok=True)
    stub_py = _stub_py(tmp_path)
    rclone = binn / "rclone"
    rclone.write_text(
        f'#!/usr/bin/env bash\necho rclone >> "$sentinel"\nexit {1 if push_fails else 0}\n'
    )
    rclone.chmod(0o755)

    env = {
        "PATH": f"{binn}:/usr/bin:/bin",
        "PY_BIN": str(stub_py),
        "sentinel": str(tmp_path / "called.log"),
        "ARCHIVE": str(tmp_path / "statuteproof-backup-TEST.tar.gz"),
        "PUSH_FILE": str(tmp_path / "statuteproof-backup-TEST.tar.gz.age"),
        "STATUTEPROOF_BACKUP_REMOTE": "s3:bucket/path",
    }
    body = _PAGE_FOUNDER_FN + _ACCUM_INIT + _OFFBOX_BLOCK + _PAGING_BLOCK
    return subprocess.run(
        [BASH, "-c", "set -euo pipefail\n" + body],
        capture_output=True,
        text=True,
        env=env,
    )


@requires_bash
def test_backup_pages_founder_when_push_fails(tmp_path):
    result = _run_offbox_page(tmp_path, push_fails=True)
    assert result.returncode == 0, result.stderr
    pages = _paged_lines(tmp_path)
    assert len(pages) == 1
    assert "FAILED" in pages[0]


@requires_bash
def test_backup_no_page_when_push_succeeds(tmp_path):
    result = _run_offbox_page(tmp_path, push_fails=False)
    assert result.returncode == 0, result.stderr
    assert _paged_lines(tmp_path) == []


@requires_bash
def test_backup_sh_still_valid_bash():
    result = subprocess.run(
        [BASH, "-n", str(BACKUP_SH)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr


@requires_bash
def test_deploy_check_sh_still_valid_bash():
    result = subprocess.run(
        [BASH, "-n", str(DEPLOY_CHECK_SH)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr


# ══════════════════════════════════════════════════════════════════════════
# Part C — ops_alert.ping_external_heartbeat (mocked HTTP, hermetic)
# ══════════════════════════════════════════════════════════════════════════


def test_ping_noop_when_url_unset(monkeypatch):
    import app.ops_alert as ops_alert

    monkeypatch.delenv("STATUTEPROOF_HEARTBEAT_PING_URL", raising=False)
    with patch.object(ops_alert._req, "get") as mock_get:
        assert ops_alert.ping_external_heartbeat() is False
    mock_get.assert_not_called()


def test_ping_hits_url_with_timeout(monkeypatch):
    import app.ops_alert as ops_alert

    url = "https://hc-ping.example/uuid"
    monkeypatch.setenv("STATUTEPROOF_HEARTBEAT_PING_URL", url)
    with patch.object(ops_alert._req, "get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200)
        assert ops_alert.ping_external_heartbeat() is True
    mock_get.assert_called_once_with(url, timeout=10)


def test_ping_suppressed_by_ops_alerts_kill_switch(monkeypatch):
    """STATUTEPROOF_OPS_ALERTS_DISABLED must suppress the external ping too.

    The module contract is that the kill switch silences ALL outbound ops
    traffic. A staging box or restore drill carrying a production .env would
    otherwise keep the external deadman green through a real prod outage.
    """
    import app.ops_alert as ops_alert

    monkeypatch.setenv("STATUTEPROOF_HEARTBEAT_PING_URL", "https://hc-ping.example/uuid")
    monkeypatch.setenv("STATUTEPROOF_OPS_ALERTS_DISABLED", "1")
    with patch.object(ops_alert._req, "get") as mock_get:
        assert ops_alert.ping_external_heartbeat() is False
    mock_get.assert_not_called()


def test_ping_non_2xx_returns_false(monkeypatch):
    import app.ops_alert as ops_alert

    monkeypatch.setenv("STATUTEPROOF_HEARTBEAT_PING_URL", "https://hc-ping.example/uuid")
    with patch.object(ops_alert._req, "get") as mock_get:
        mock_get.return_value = MagicMock(status_code=500)
        assert ops_alert.ping_external_heartbeat() is False


def test_ping_never_raises(monkeypatch):
    import app.ops_alert as ops_alert

    monkeypatch.setenv("STATUTEPROOF_HEARTBEAT_PING_URL", "https://hc-ping.example/uuid")
    with patch.object(ops_alert._req, "get", side_effect=Exception("net down")):
        assert ops_alert.ping_external_heartbeat() is False  # must not raise


def _spy(calls: list):
    def _record() -> bool:
        calls.append(1)
        return True

    return _record


def test_check_heartbeat_pings_only_when_fresh(tmp_path, monkeypatch):
    """Fresh heartbeat -> exactly one external ping (droplet proves liveness)."""
    import app.ops_alert as ops_alert

    monkeypatch.delenv("STATUTEPROOF_HEARTBEAT_PING_URL", raising=False)
    hb = tmp_path / "data" / "monitor_heartbeat"
    hb.parent.mkdir(parents=True, exist_ok=True)
    hb.write_text("now\n")  # just written → mtime is fresh
    monkeypatch.setattr(ops_alert, "_HEARTBEAT_FILE", hb)
    monkeypatch.setattr(ops_alert, "WATCH_INTERVAL_MINUTES", 60)
    monkeypatch.setattr(ops_alert, "notify_founder", lambda t: True)

    calls: list[int] = []
    monkeypatch.setattr(ops_alert, "ping_external_heartbeat", _spy(calls))

    assert ops_alert.check_heartbeat() is False
    assert len(calls) == 1


def test_check_heartbeat_does_not_ping_when_missing(tmp_path, monkeypatch):
    """Missing heartbeat -> NO ping: silence upstream is the alarm signal."""
    import app.ops_alert as ops_alert

    monkeypatch.delenv("STATUTEPROOF_HEARTBEAT_PING_URL", raising=False)
    hb = tmp_path / "data" / "monitor_heartbeat"  # never created
    monkeypatch.setattr(ops_alert, "_HEARTBEAT_FILE", hb)
    monkeypatch.setattr(ops_alert, "notify_founder", lambda t: True)

    calls: list[int] = []
    monkeypatch.setattr(ops_alert, "ping_external_heartbeat", _spy(calls))

    assert ops_alert.check_heartbeat() is True
    assert calls == []


def test_check_heartbeat_does_not_ping_when_stale(tmp_path, monkeypatch):
    import os as _os
    import time as _time

    import app.ops_alert as ops_alert

    monkeypatch.delenv("STATUTEPROOF_HEARTBEAT_PING_URL", raising=False)
    hb = tmp_path / "data" / "monitor_heartbeat"
    hb.parent.mkdir(parents=True, exist_ok=True)
    hb.write_text("2020-01-01T00:00:00+00:00\n")
    monkeypatch.setattr(ops_alert, "_HEARTBEAT_FILE", hb)
    monkeypatch.setattr(ops_alert, "WATCH_INTERVAL_MINUTES", 60)
    monkeypatch.setattr(ops_alert, "notify_founder", lambda t: True)
    old = _time.time() - (3 * 60 * 60)
    _os.utime(hb, (old, old))

    calls: list[int] = []
    monkeypatch.setattr(ops_alert, "ping_external_heartbeat", _spy(calls))

    assert ops_alert.check_heartbeat() is True
    assert calls == []


# ══════════════════════════════════════════════════════════════════════════
# Part D — docs match the real architecture
# ══════════════════════════════════════════════════════════════════════════


def test_update_md_exists_and_matches_real_stack():
    update_md = REPO_ROOT / "UPDATE.md"
    assert update_md.is_file(), "UPDATE.md missing (referenced by RESET_RUNBOOK.md)"
    text = _read(update_md)
    for token in (
        "deploy-check",
        "systemctl restart",
        "/srv/regradar",
        "/api/health",
        "verify-trail-watch",
        "Rollback",
        "backup.sh",
    ):
        assert token in text, f"UPDATE.md missing {token!r}"
    assert "caddy" in text.lower()


def test_update_md_copy_step_excludes_live_data():
    """The update-copy step must never overwrite the live data/ tree.

    The repo tracks seed files under data/ (alert queue entries served by
    GET /api/briefs, the append-only canonical evidence-review journal), so
    a bare `cp -r` from the source clone onto a LIVE install would silently
    roll runtime data back to stale repo copies. The runbook must use the
    rsync-with-excludes pattern for the update copy, not `cp -r`.

    The excludes must be ANCHORED (`--exclude /data`, transfer-root-relative):
    an unanchored `--exclude data` matches the path component at any depth,
    so it would also silently skip the repo-tracked frontend source
    web/src/data/ (sourceCounts.js, planCapabilities.js, constants.js, ...)
    and every routine update would rebuild the customer-facing frontend from
    stale sources with no error.
    """
    text = _read(REPO_ROOT / "UPDATE.md")
    update_section = text.split("## Rollback procedure")[0]
    assert (
        "cp -r /srv/regradar-src" not in update_section
    ), "UPDATE.md update copy must not use bare cp -r onto the live tree"
    assert (
        "rsync -a --exclude /data --exclude /backups --exclude /.venv --exclude /.env \\\n"
        "       /srv/regradar-src/product/regradar/ /srv/regradar/"
    ) in update_section, (
        "UPDATE.md update-copy step must rsync with anchored "
        "/data /backups /.venv /.env excludes"
    )
    # No rsync COMMAND in the runbook (update copy, rollback snapshot, or
    # rollback restore) may use the unanchored form — it silently skips
    # web/src/data at any depth. Prose may mention the bare pattern when
    # explaining why it is forbidden, so only command lines are checked.
    rsync_lines = [line for line in text.splitlines() if "rsync -a" in line]
    assert rsync_lines, "UPDATE.md lost its rsync commands entirely"
    for line in rsync_lines:
        for bare in (
            "--exclude data",
            "--exclude backups",
            "--exclude .venv",
            "--exclude .env",
        ):
            assert bare not in line, (
                f"UPDATE.md rsync command uses unanchored pattern {bare!r} "
                f"({line.strip()!r}); anchor it with a leading slash "
                "(e.g. --exclude /data) so nested paths like web/src/data "
                "are still copied"
            )


def test_update_md_rollback_restores_systemd_units():
    """Rollback must reinstall the pre-update unit files, not just the code.

    Update step 7 copies new unit files into /etc/systemd/system and reloads.
    A rollback that restores only /srv/regradar leaves the droplet running the
    NEW unit definitions against OLD code — and deploy-check inspects the tree,
    not /etc/systemd/system, so the gate still passes while the scheduler fails
    to start mid-incident.
    """
    rollback = _read(REPO_ROOT / "UPDATE.md").split("## Rollback procedure")[1]
    assert "/etc/systemd/system/" in rollback, (
        "UPDATE.md rollback never reinstalls the pre-update unit files"
    )
    assert "daemon-reload" in rollback, (
        "UPDATE.md rollback never reloads systemd after restoring the units"
    )
    # sh/dash-safe: two explicit globs, never brace expansion (the runbook is
    # copy-pasted under pressure and `{service,timer}` is a bashism).
    unit_lines = [
        line for line in rollback.splitlines() if "/etc/systemd/system/" in line
    ]
    for line in unit_lines:
        assert "{service,timer}" not in line, (
            f"UPDATE.md rollback unit copy uses brace expansion ({line.strip()!r}); "
            "use two explicit globs so the command also works in sh/dash"
        )


@pytest.mark.parametrize(
    "stale_doc",
    [
        "docs/vps_deployment_runbook.md",
        "docs/production_deployment_checklist.md",
    ],
)
def test_stale_nginx_runbooks_carry_superseded_banner(stale_doc):
    head = _read(REPO_ROOT / stale_doc)[:500]
    assert "SUPERSEDED" in head
    assert "DEPLOY.md" in head
    assert "UPDATE.md" in head


def test_env_example_documents_new_vars():
    text = _read(REPO_ROOT / ".env.example")
    assert "STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY" in text
    assert "STATUTEPROOF_HEARTBEAT_PING_URL" in text


# ══════════════════════════════════════════════════════════════════════════
# Part E — off-box archives are ENCRYPTED, and the timers actually run
# ══════════════════════════════════════════════════════════════════════════
#
# Regression for the MEDIUM introduced by the spof-ops cycle above: making
# STATUTEPROOF_BACKUP_REMOTE mandatory turned "we might copy account secrets
# off-box" into a standing obligation to do so. The archive contains
# regradar.db — password hashes, emails, telegram_chat_ids, and the sessions
# table whose ids ARE bearer credentials. One readable archive replays live
# sessions until expiry. So: nothing leaves the droplet unencrypted, and a
# remote without an encryption secret is a deploy FAILURE.
#
# Second half: a control that is documented but never enabled is worse than a
# known gap — deploy-check now asserts each timer unit is enabled AND active.

# 2b) as it appears in backup.sh, between the tar and the off-box push.
_ENCRYPT_BLOCK = """\
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
"""

_TEST_PASSPHRASE = "correct-horse-battery-staple"


def _encrypt_stubs(tmp_path: Path, *, with_age: bool, with_gpg: bool, fail: bool = False):
    """Stub age/gpg that record argv (+ gpg's stdin) and write the output file."""
    binn = tmp_path / "bin"
    binn.mkdir(exist_ok=True)
    rc = 1 if fail else 0
    body = (
        '#!/usr/bin/env bash\n'
        'echo "$0 $*" >> "$argv_log"\n'
        'cat > "$stdin_log"\n'
        'out=""\n'
        'while [ $# -gt 0 ]; do if [ "$1" = "-o" ]; then out="$2"; fi; shift; done\n'
        f'[ -n "$out" ] && printf ENCRYPTED > "$out"\n'
        f'exit {rc}\n'
    )
    for name, wanted in (("age", with_age), ("gpg", with_gpg)):
        if not wanted:
            continue
        p = binn / name
        p.write_text(body)
        p.chmod(0o755)
    return binn


def _run_encrypt_then_push(
    tmp_path: Path, env_extra: dict[str, str], *, prod_guard: bool = False, **stub_kw
):
    """Encrypt block + real push block + deferred page, with stub tooling.

    prod_guard=True prepends backup.sh's environment detection + override
    refusal, i.e. exercises the script the way a droplet runs it.
    """
    binn = _encrypt_stubs(tmp_path, **stub_kw)
    stub_py = _stub_py(tmp_path)
    rclone = binn / "rclone"
    rclone.write_text('#!/usr/bin/env bash\necho "$2" >> "$pushed_log"\nexit 0\n')
    rclone.chmod(0o755)

    archive = tmp_path / "statuteproof-backup-TEST.tar.gz"
    archive.write_text("PLAINTEXT-ARCHIVE")
    work = tmp_path / "work"
    work.mkdir(exist_ok=True)

    env = {
        "PATH": f"{binn}:/usr/bin:/bin",
        "PY_BIN": str(stub_py),
        "sentinel": str(tmp_path / "called.log"),
        "argv_log": str(tmp_path / "argv.log"),
        "stdin_log": str(tmp_path / "stdin.log"),
        "pushed_log": str(tmp_path / "pushed.log"),
        "ARCHIVE": str(archive),
        "WORK": str(work),
    }
    env.update(env_extra)
    guard = (
        _PROD_DETECT_BLOCK + _PROD_OVERRIDE_REFUSAL_BLOCK if prod_guard else ""
    )
    body = (
        _PAGE_FOUNDER_FN
        + _ACCUM_INIT
        + guard
        + _ENCRYPT_BLOCK
        + _OFFBOX_BLOCK
        + _PAGING_BLOCK
    )
    result = subprocess.run(
        [BASH, "-c", "set -euo pipefail\n" + body],
        capture_output=True,
        text=True,
        env=env,
    )
    pushed_file = tmp_path / "pushed.log"
    pushed = pushed_file.read_text().split() if pushed_file.exists() else []
    return result, pushed


@requires_bash
def test_backup_pushes_age_encrypted_archive(tmp_path):
    """age recipient configured -> the .age file is pushed, never the plaintext."""
    result, pushed = _run_encrypt_then_push(
        tmp_path,
        {
            "STATUTEPROOF_BACKUP_REMOTE": "s3:bucket/path",
            "STATUTEPROOF_BACKUP_AGE_RECIPIENT": "age1examplerecipientkey",
        },
        with_age=True,
        with_gpg=True,
    )
    assert result.returncode == 0, result.stderr
    assert len(pushed) == 1, pushed
    assert pushed[0].endswith(".age"), pushed
    assert Path(pushed[0]).read_text() == "ENCRYPTED"
    # The plaintext archive itself must never be handed to the push tool.
    assert not any(p.endswith(".tar.gz") for p in pushed)
    assert _paged_lines(tmp_path) == []


@requires_bash
def test_backup_pushes_gpg_encrypted_archive_without_leaking_passphrase(tmp_path):
    """No age -> gpg --symmetric; the passphrase arrives on fd 0, never argv."""
    result, pushed = _run_encrypt_then_push(
        tmp_path,
        {
            "STATUTEPROOF_BACKUP_REMOTE": "s3:bucket/path",
            "STATUTEPROOF_BACKUP_PASSPHRASE": _TEST_PASSPHRASE,
        },
        with_age=False,
        with_gpg=True,
    )
    assert result.returncode == 0, result.stderr
    assert len(pushed) == 1 and pushed[0].endswith(".gpg"), pushed
    argv = (tmp_path / "argv.log").read_text()
    assert _TEST_PASSPHRASE not in argv, "passphrase leaked into the gpg command line"
    assert "--passphrase-fd 0" in argv
    assert (tmp_path / "stdin.log").read_text() == _TEST_PASSPHRASE
    # ...and it is never written to any file the script leaves behind.
    for leftover in tmp_path.rglob("*"):
        if leftover.is_file() and leftover.name not in {"stdin.log"}:
            assert _TEST_PASSPHRASE not in leftover.read_text(errors="ignore"), leftover


@requires_bash
def test_backup_refuses_push_when_no_encryption_secret(tmp_path):
    """Remote set, no recipient/passphrase -> NOTHING is pushed; founder paged."""
    result, pushed = _run_encrypt_then_push(
        tmp_path,
        {"STATUTEPROOF_BACKUP_REMOTE": "s3:bucket/path"},
        with_age=True,
        with_gpg=True,
    )
    assert result.returncode == 0, result.stderr
    assert pushed == [], "plaintext archive was pushed off-box"
    assert "REFUSED" in result.stderr
    pages = _paged_lines(tmp_path)
    assert len(pages) == 1 and "REFUSED" in pages[0]


@requires_bash
def test_backup_refuses_push_when_encryption_tooling_absent(tmp_path):
    """Passphrase configured but no age/gpg on the droplet -> refuse + page."""
    result, pushed = _run_encrypt_then_push(
        tmp_path,
        {
            "STATUTEPROOF_BACKUP_REMOTE": "s3:bucket/path",
            "STATUTEPROOF_BACKUP_PASSPHRASE": _TEST_PASSPHRASE,
        },
        with_age=False,
        with_gpg=False,
    )
    assert result.returncode == 0, result.stderr
    assert pushed == []
    assert "REFUSED" in result.stderr
    assert len(_paged_lines(tmp_path)) == 1


@requires_bash
def test_backup_refuses_push_when_encryption_command_fails(tmp_path):
    """age present but exits non-zero -> refuse rather than fall back to clear."""
    result, pushed = _run_encrypt_then_push(
        tmp_path,
        {
            "STATUTEPROOF_BACKUP_REMOTE": "s3:bucket/path",
            "STATUTEPROOF_BACKUP_AGE_RECIPIENT": "age1examplerecipientkey",
        },
        with_age=True,
        with_gpg=False,
        fail=True,
    )
    assert result.returncode == 0, result.stderr
    assert pushed == []
    assert "encryption FAILED" in result.stderr
    assert len(_paged_lines(tmp_path)) == 1


@requires_bash
def test_backup_dev_override_pushes_plaintext_loudly(tmp_path):
    """Documented dev override -> plaintext push, but never silently."""
    result, pushed = _run_encrypt_then_push(
        tmp_path,
        {
            "STATUTEPROOF_BACKUP_REMOTE": "s3:bucket/path",
            "STATUTEPROOF_ALLOW_UNENCRYPTED_BACKUP": "1",
        },
        with_age=False,
        with_gpg=False,
    )
    assert result.returncode == 0, result.stderr
    assert len(pushed) == 1 and pushed[0].endswith(".tar.gz")
    assert "UNENCRYPTED" in result.stderr


@requires_bash
def test_backup_encryption_is_skipped_entirely_when_local_only(tmp_path):
    """No remote -> no encryption attempt and no push (local-only mode)."""
    result, pushed = _run_encrypt_then_push(tmp_path, {}, with_age=True, with_gpg=True)
    assert result.returncode == 0, result.stderr
    assert pushed == []
    assert not (tmp_path / "argv.log").exists()


def test_encrypt_block_matches_script():
    """The literal encryption block is present verbatim in backup.sh."""
    assert _ENCRYPT_BLOCK.strip() in _read(BACKUP_SH)


def test_encryption_precedes_offbox_push_in_script():
    """Ordering guard: nothing may be pushed before the encryption decision."""
    text = _read(BACKUP_SH)
    assert text.index(_ENCRYPT_BLOCK.strip()) < text.index("rclone copy")


def test_push_block_never_references_the_plaintext_archive():
    """Every push command sends $PUSH_FILE, never $ARCHIVE."""
    for line in _read(BACKUP_SH).splitlines():
        stripped = line.strip()
        if stripped.startswith("rclone copy") or stripped.startswith("scp "):
            assert '"$PUSH_FILE"' in stripped, stripped
            assert '"$ARCHIVE"' not in stripped, stripped


# --- deploy-check: a remote without an encryption secret is a FAILURE -------

_DEPLOY_CHECK_ENCRYPTION_BLOCK = """\
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
"""


def _run_block(block: str, env_extra: dict[str, str], *, path: str = "/usr/bin:/bin"):
    return _run_gate_block(block, env_extra, path=path)


@requires_bash
def test_deploy_check_fails_on_remote_without_encryption_secret():
    result = _run_block(
        _DEPLOY_CHECK_ENCRYPTION_BLOCK,
        {"STATUTEPROOF_BACKUP_REMOTE": "s3:bucket/path"},
    )
    assert result.returncode == 1, result.stdout + result.stderr
    bad_lines = [l for l in result.stdout.splitlines() if l.startswith("BAD:")]
    assert len(bad_lines) == 1
    assert "encryption" in bad_lines[0]


@requires_bash
def test_deploy_check_encryption_dev_override_warns():
    result = _run_block(
        _DEPLOY_CHECK_ENCRYPTION_BLOCK,
        {
            "STATUTEPROOF_BACKUP_REMOTE": "s3:bucket/path",
            "STATUTEPROOF_ALLOW_UNENCRYPTED_BACKUP": "1",
        },
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert any(
        l.startswith("WARN:") and "UNENCRYPTED" in l for l in result.stdout.splitlines()
    )


@requires_bash
def test_deploy_check_encryption_silent_when_local_only():
    """No remote -> the encryption gate says nothing (the remote gate speaks)."""
    result = _run_block(_DEPLOY_CHECK_ENCRYPTION_BLOCK, {})
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_deploy_check_encryption_block_matches_script():
    assert _DEPLOY_CHECK_ENCRYPTION_BLOCK.strip() in _read(DEPLOY_CHECK_SH)


# --- deploy-check: the scheduled timers are enabled AND active --------------

_DEPLOY_CHECK_TIMER_BLOCK = """\
echo "── scheduled timers ─────────────────────────────────────"
if ! command -v systemctl >/dev/null 2>&1; then
  warn "systemctl unavailable — timer enablement unverified (not a droplet)"
else
  for unit in statuteproof-compaction.timer statuteproof-backup.timer \\
              statuteproof-heartbeat.timer statuteproof-verify.timer \\
              statuteproof-api-health.timer \\
              statuteproof-scheduler-watchdog.timer; do
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
"""

_TIMERS = [
    "statuteproof-compaction.timer",
    "statuteproof-backup.timer",
    "statuteproof-heartbeat.timer",
    "statuteproof-verify.timer",
    "statuteproof-api-health.timer",
    # The one control that RESTARTS rather than only notifying. Monitoring was
    # dead for four days with every other timer green, because none of them act.
    "statuteproof-scheduler-watchdog.timer",
]


def _stub_systemctl(tmp_path: Path, *, installed: bool, enabled: str, active: str) -> str:
    binn = tmp_path / "sbin"
    binn.mkdir(exist_ok=True)
    p = binn / "systemctl"
    listing = (
        'for u in ' + " ".join(_TIMERS) + '; do echo "$u enabled"; done\n'
        if installed
        else 'true\n'
    )
    p.write_text(
        '#!/usr/bin/env bash\n'
        'case "$1" in\n'
        '  list-unit-files) ' + listing + '    ;;\n'
        f'  is-enabled) echo "{enabled}" ;;\n'
        f'  is-active) echo "{active}" ;;\n'
        'esac\n'
        'exit 0\n'
    )
    p.chmod(0o755)
    return f"{binn}:/usr/bin:/bin"


@requires_bash
def test_deploy_check_timers_pass_when_enabled_and_active(tmp_path):
    path = _stub_systemctl(tmp_path, installed=True, enabled="enabled", active="active")
    result = _run_block(_DEPLOY_CHECK_TIMER_BLOCK, {}, path=path)
    assert result.returncode == 0, result.stdout + result.stderr
    ok_lines = [l for l in result.stdout.splitlines() if l.startswith("OK:")]
    assert len(ok_lines) == len(_TIMERS)
    for timer in _TIMERS:
        assert any(timer in l for l in ok_lines), timer


@requires_bash
def test_deploy_check_timers_fail_when_installed_but_not_enabled(tmp_path):
    """The Cycle-1 gap: units shipped and documented, but never enabled."""
    path = _stub_systemctl(tmp_path, installed=True, enabled="disabled", active="active")
    result = _run_block(_DEPLOY_CHECK_TIMER_BLOCK, {}, path=path)
    assert result.returncode == 1, result.stdout + result.stderr
    bad_lines = [l for l in result.stdout.splitlines() if l.startswith("BAD:")]
    assert len(bad_lines) == len(_TIMERS)
    assert all("NOT enabled" in l for l in bad_lines)


@requires_bash
def test_deploy_check_timers_fail_when_enabled_but_inactive(tmp_path):
    path = _stub_systemctl(tmp_path, installed=True, enabled="enabled", active="inactive")
    result = _run_block(_DEPLOY_CHECK_TIMER_BLOCK, {}, path=path)
    assert result.returncode == 1, result.stdout + result.stderr
    bad_lines = [l for l in result.stdout.splitlines() if l.startswith("BAD:")]
    assert len(bad_lines) == len(_TIMERS)
    assert all("NOT active" in l for l in bad_lines)


@requires_bash
def test_deploy_check_timers_warn_before_units_are_installed(tmp_path):
    """deploy-check runs BEFORE § 7 too — not-yet-installed must not hard-fail."""
    path = _stub_systemctl(tmp_path, installed=False, enabled="", active="")
    result = _run_block(_DEPLOY_CHECK_TIMER_BLOCK, {}, path=path)
    assert result.returncode == 0, result.stdout + result.stderr
    warn_lines = [l for l in result.stdout.splitlines() if l.startswith("WARN:")]
    assert len(warn_lines) == len(_TIMERS)
    assert all("not installed yet" in l for l in warn_lines)


@requires_bash
def test_deploy_check_timers_warn_without_systemctl(tmp_path):
    """Dev laptops / containers have no systemd — warn, never fail."""
    empty = tmp_path / "empty"
    empty.mkdir()
    result = _run_block(_DEPLOY_CHECK_TIMER_BLOCK, {}, path=str(empty))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "BAD:" not in result.stdout
    assert "WARN:systemctl unavailable" in result.stdout


def test_deploy_check_timer_block_matches_script():
    assert _DEPLOY_CHECK_TIMER_BLOCK.strip() in _read(DEPLOY_CHECK_SH)


# --- deploy-check: the PERSISTENT daemons are enabled AND active -------------

# There is NO scheduler.timer — the monitoring loop lives inside the long-running
# statuteproof-scheduler.service. File-presence alone lets an operator enable the
# four timers but never the scheduler daemon and still see DEPLOY-CHECK PASSED
# while ZERO monitoring runs and no alert ever fires. deploy-check must therefore
# runtime-verify the three core daemons the same way it verifies the timers.
_DEPLOY_CHECK_DAEMON_BLOCK = """\
echo "── core daemons ─────────────────────────────────────────"
if ! command -v systemctl >/dev/null 2>&1; then
  warn "systemctl unavailable — daemon enablement unverified (not a droplet)"
else
  for unit in statuteproof-api.service statuteproof-scheduler.service \\
              statuteproof-telegram-bot.service; do
    # Pipe-free on purpose (see scheduled-timers block): `... | grep -q` under
    # `set -o pipefail` reports a SIGPIPE failure whenever grep exits on an early
    # match while systemctl is still writing, so installed units intermittently
    # read as "not installed".
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
"""

_DAEMONS = [
    "statuteproof-api.service",
    "statuteproof-scheduler.service",
    "statuteproof-telegram-bot.service",
]


def _stub_systemctl_units(
    tmp_path: Path, units, *, installed: bool, enabled: str, active: str
) -> str:
    binn = tmp_path / "sbin"
    binn.mkdir(exist_ok=True)
    p = binn / "systemctl"
    listing = (
        'for u in ' + " ".join(units) + '; do echo "$u enabled"; done\n'
        if installed
        else 'true\n'
    )
    p.write_text(
        '#!/usr/bin/env bash\n'
        'case "$1" in\n'
        '  list-unit-files) ' + listing + '    ;;\n'
        f'  is-enabled) echo "{enabled}" ;;\n'
        f'  is-active) echo "{active}" ;;\n'
        'esac\n'
        'exit 0\n'
    )
    p.chmod(0o755)
    return f"{binn}:/usr/bin:/bin"


@requires_bash
def test_deploy_check_daemons_pass_when_enabled_and_active(tmp_path):
    path = _stub_systemctl_units(tmp_path, _DAEMONS, installed=True, enabled="enabled", active="active")
    result = _run_block(_DEPLOY_CHECK_DAEMON_BLOCK, {}, path=path)
    assert result.returncode == 0, result.stdout + result.stderr
    ok_lines = [l for l in result.stdout.splitlines() if l.startswith("OK:")]
    assert len(ok_lines) == len(_DAEMONS)
    for daemon in _DAEMONS:
        assert any(daemon in l for l in ok_lines), daemon


@requires_bash
def test_deploy_check_daemons_fail_when_installed_but_not_enabled(tmp_path):
    """The gap this fix closes: scheduler daemon shipped, documented, never enabled."""
    path = _stub_systemctl_units(tmp_path, _DAEMONS, installed=True, enabled="disabled", active="active")
    result = _run_block(_DEPLOY_CHECK_DAEMON_BLOCK, {}, path=path)
    assert result.returncode == 1, result.stdout + result.stderr
    bad_lines = [l for l in result.stdout.splitlines() if l.startswith("BAD:")]
    assert len(bad_lines) == len(_DAEMONS)
    assert all("NOT enabled" in l for l in bad_lines)


@requires_bash
def test_deploy_check_daemons_fail_when_enabled_but_inactive(tmp_path):
    path = _stub_systemctl_units(tmp_path, _DAEMONS, installed=True, enabled="enabled", active="inactive")
    result = _run_block(_DEPLOY_CHECK_DAEMON_BLOCK, {}, path=path)
    assert result.returncode == 1, result.stdout + result.stderr
    bad_lines = [l for l in result.stdout.splitlines() if l.startswith("BAD:")]
    assert len(bad_lines) == len(_DAEMONS)
    assert all("NOT active" in l for l in bad_lines)


@requires_bash
def test_deploy_check_daemons_warn_before_units_are_installed(tmp_path):
    """deploy-check runs BEFORE § 7 too — not-yet-installed must not hard-fail."""
    path = _stub_systemctl_units(tmp_path, _DAEMONS, installed=False, enabled="", active="")
    result = _run_block(_DEPLOY_CHECK_DAEMON_BLOCK, {}, path=path)
    assert result.returncode == 0, result.stdout + result.stderr
    warn_lines = [l for l in result.stdout.splitlines() if l.startswith("WARN:")]
    assert len(warn_lines) == len(_DAEMONS)
    assert all("not installed yet" in l for l in warn_lines)


@requires_bash
def test_deploy_check_daemons_warn_without_systemctl(tmp_path):
    """Dev laptops / containers have no systemd — warn, never fail."""
    empty = tmp_path / "empty"
    empty.mkdir()
    result = _run_block(_DEPLOY_CHECK_DAEMON_BLOCK, {}, path=str(empty))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "BAD:" not in result.stdout
    assert "WARN:systemctl unavailable" in result.stdout


def test_deploy_check_daemon_block_matches_script():
    assert _DEPLOY_CHECK_DAEMON_BLOCK.strip() in _read(DEPLOY_CHECK_SH)


# --- deploy-check: the service-file presence loop covers the CORE units -----

# Every unit DEPLOY.md § 7 ships as CORE must be asserted present by
# deploy-check.sh — otherwise a missing backup/heartbeat/verify unit slips
# through silently (the timer block above checks enablement, not file presence).
_CORE_SERVICE_FILES = [
    "statuteproof-api.service",
    "statuteproof-scheduler.service",
    "statuteproof-telegram-bot.service",
    "statuteproof-compaction.service",
    "statuteproof-compaction.timer",
    "statuteproof-backup.service",
    "statuteproof-backup.timer",
    "statuteproof-heartbeat.service",
    "statuteproof-heartbeat.timer",
    "statuteproof-verify.service",
    "statuteproof-verify.timer",
]


def test_deploy_check_service_presence_loop_covers_core_units():
    script = _read(DEPLOY_CHECK_SH)
    # Isolate the presence loop (between its header and the next section) so a
    # unit named elsewhere in the script cannot mask a gap in the loop itself.
    start = script.index('echo "── service files')
    loop = script[start : script.index("── scheduled timers", start)]
    for unit in _CORE_SERVICE_FILES:
        assert unit in loop, f"{unit} missing from deploy-check service-file loop"
    # The CBUAE rulebook watcher is opt-in/optional — it must NOT be asserted
    # as a required CORE file (a missing optional unit is not a deploy failure).
    assert "statuteproof-cbuae-rulebook-watch" not in loop


# --- documentation: an unrestorable encrypted backup is worse than none ----


def test_deploy_md_documents_encrypted_restore_path():
    text = _read(REPO_ROOT / "DEPLOY.md")
    assert "STATUTEPROOF_BACKUP_AGE_RECIPIENT" in text
    assert "STATUTEPROOF_BACKUP_PASSPHRASE" in text
    # Exact decrypt commands for BOTH paths must be present in the restore doc.
    assert "age --decrypt" in text
    assert "gpg --decrypt" in text
    # ...and an explicit instruction to rehearse a restore.
    assert "test a restore" in text.lower() or "rehearse" in text.lower()


def test_deploy_md_step_7_verifies_timer_enablement():
    text = _read(REPO_ROOT / "DEPLOY.md")
    seven = text[text.index("## 7. Services") : text.index("## 8.")]
    assert "enable --now" in seven
    assert "deploy-check.sh" in seven, "§ 7 must re-run deploy-check to prove timers run"


def test_env_example_documents_backup_encryption_vars():
    text = _read(REPO_ROOT / ".env.example")
    assert "STATUTEPROOF_BACKUP_AGE_RECIPIENT" in text
    assert "STATUTEPROOF_BACKUP_PASSPHRASE" in text
    assert "STATUTEPROOF_ALLOW_UNENCRYPTED_BACKUP" in text
    # Losing the secret means losing every off-box archive — say so.
    lowered = text.lower()
    assert "lose" in lowered or "losing" in lowered


# --- deploy-check must not contradict backup.sh on the dev override ---------
# backup.sh checks STATUTEPROOF_ALLOW_UNENCRYPTED_BACKUP FIRST, so an override
# left set next to a real encryption secret still pushes PLAINTEXT. If
# deploy-check checks the secret first it prints a green "archives are
# encrypted" for exactly that state — asserting the opposite of the truth about
# password hashes and live session ids landing on third-party storage.


@requires_bash
@pytest.mark.parametrize(
    "secret_var", ["STATUTEPROOF_BACKUP_AGE_RECIPIENT", "STATUTEPROOF_BACKUP_PASSPHRASE"]
)
def test_deploy_check_override_wins_over_encryption_secret(secret_var):
    result = _run_block(
        _DEPLOY_CHECK_ENCRYPTION_BLOCK,
        {
            "STATUTEPROOF_BACKUP_REMOTE": "s3:bucket/path",
            secret_var: "x",
            "STATUTEPROOF_ALLOW_UNENCRYPTED_BACKUP": "1",
        },
    )
    assert any(
        l.startswith("WARN:") and "UNENCRYPTED" in l for l in result.stdout.splitlines()
    ), result.stdout
    assert "are encrypted" not in result.stdout, (
        "deploy-check claims encryption while backup.sh would push plaintext"
    )


def test_override_branch_precedes_encryption_secrets_in_both_scripts():
    """Same branch order in both scripts, or the gate lies about the push."""
    for path in (BACKUP_SH, DEPLOY_CHECK_SH):
        text = _read(path)
        override = text.index("STATUTEPROOF_ALLOW_UNENCRYPTED_BACKUP:-")
        for secret in (
            "STATUTEPROOF_BACKUP_AGE_RECIPIENT:-",
            "STATUTEPROOF_BACKUP_PASSPHRASE:-",
        ):
            assert override < text.index(secret), f"{path.name}: {secret} branch precedes the override"


# --- deploy-check: the gpg passphrase must survive .env SOURCING ------------
# backup.sh/deploy-check load config with `set -a; . ./.env`, i.e. bash SOURCES
# the file: every value gets parameter expansion, command substitution and word
# splitting. A password-manager passphrase like `corr3ct$horse-batteryStaple`
# is silently loaded as `corr3ct-batteryStaple`; gpg then encrypts with the
# MANGLED value and every off-box archive is unrecoverable with the passphrase
# the founder actually stored. Non-emptiness is not enough of a check.

_DEPLOY_CHECK_PASSPHRASE_BLOCK = r"""if [ -n "${STATUTEPROOF_BACKUP_PASSPHRASE:-}" ] && [ -f .env ]; then
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
"""


def _run_passphrase_block(tmp_path, env_line: str | None):
    """Run the gate the way the real script does: source .env, then check."""
    if env_line is not None:
        (tmp_path / ".env").write_text(env_line + "\n", encoding="utf-8")
    script = (
        _HARNESS_PREFIX
        + _ENV_SOURCE_LINE + "\n"
        + _DEPLOY_CHECK_PASSPHRASE_BLOCK
        + 'exit "$FAIL"\n'
    )
    return subprocess.run(
        [BASH, "-c", script],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        env={"PATH": "/usr/bin:/bin"},
    )


@requires_bash
@pytest.mark.parametrize(
    "env_line",
    [
        # parameter expansion of a SET variable — silent, still non-empty
        "STATUTEPROOF_BACKUP_PASSPHRASE=corr3ct$PATH-batteryStaple",
        # command substitution — runs a subshell, yields a different secret
        "STATUTEPROOF_BACKUP_PASSPHRASE=pw`id -un`",
    ],
)
def test_deploy_check_fails_when_passphrase_is_mangled_by_env_sourcing(tmp_path, env_line):
    result = _run_passphrase_block(tmp_path, env_line)
    assert result.returncode == 1, result.stdout + result.stderr
    assert any(l.startswith("BAD:") for l in result.stdout.splitlines()), result.stdout


@requires_bash
@pytest.mark.parametrize(
    "env_line",
    [
        "STATUTEPROOF_BACKUP_PASSPHRASE='corr3ct$horse'",
        'STATUTEPROOF_BACKUP_PASSPHRASE="two words"',
    ],
)
def test_deploy_check_rejects_shell_sensitive_passphrase_even_when_quoted(tmp_path, env_line):
    """Quoting survives bash but not systemd EnvironmentFile — refuse it."""
    result = _run_passphrase_block(tmp_path, env_line)
    assert result.returncode == 1, result.stdout + result.stderr
    assert any("backtick" in l or "whitespace" in l for l in result.stdout.splitlines())


@requires_bash
def test_deploy_check_accepts_alphanumeric_passphrase(tmp_path):
    result = _run_passphrase_block(
        tmp_path, "STATUTEPROOF_BACKUP_PASSPHRASE=Xk29fQz7Lm4RtV8bNc3Ps6Wd1Hy5Gj0Ae"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert any(l.startswith("OK:") for l in result.stdout.splitlines()), result.stdout


@requires_bash
def test_deploy_check_passphrase_gate_silent_when_unset(tmp_path):
    result = _run_passphrase_block(tmp_path, "STATUTEPROOF_BACKUP_REMOTE=s3:b/p")
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_deploy_check_passphrase_block_matches_script():
    assert _DEPLOY_CHECK_PASSPHRASE_BLOCK.strip() in _read(DEPLOY_CHECK_SH)


def test_deploy_md_passphrase_setup_is_shell_safe(tmp_path):
    """§ 9 must show a quoted assignment AND an alphanumeric generator."""
    text = _read(REPO_ROOT / "DEPLOY.md")
    section = text[text.index("STATUTEPROOF_BACKUP_PASSPHRASE") - 2000 :]
    assert "tr -dc" in section, "no alphanumeric-only passphrase generator documented"
    lines = [
        l for l in text.splitlines() if "STATUTEPROOF_BACKUP_PASSPHRASE=" in l and l.startswith("echo")
    ]
    assert lines, "no example passphrase assignment in DEPLOY.md"
    for line in lines:
        assert "<long random passphrase>" not in line, (
            "unconstrained passphrase placeholder — a $ or space silently mangles it"
        )


# --- vendor-DD pack must match what the deploy actually does ---------------

VENDOR_DD = REPO_ROOT / "docs" / "vendor-dd"


def test_security_overview_does_not_claim_backups_stay_on_the_droplet():
    text = _read(VENDOR_DD / "SECURITY-OVERVIEW.md")
    assert "not currently configured" not in text, (
        "DD pack tells prospects no backup leaves the droplet, but deploy-check "
        "now FAILS without an off-box remote"
    )
    assert "STATUTEPROOF_BACKUP_AGE_RECIPIENT" in text or "encrypted before it leaves" in text


def test_vendor_dd_faq_does_not_claim_backups_stay_on_the_droplet():
    text = _read(VENDOR_DD / "VENDOR-DD-FAQ.md")
    assert "not currently configured" not in text


def test_data_flow_doc_describes_the_mandatory_encrypted_off_box_copy():
    text = _read(VENDOR_DD / "DATA-FLOW-AND-RESIDENCY.md")
    assert "Only when `STATUTEPROOF_BACKUP_REMOTE` is set" not in text
    assert "encrypted-in-transit backup archive" not in text, (
        "understates the payload: the archive itself is encrypted at rest off-box"
    )
    assert "an optional off-box remote" not in text


def test_privacy_policy_does_not_claim_blanket_encryption_at_rest():
    """The DD pack says there is no application-level encryption at rest."""
    text = _read(REPO_ROOT / "web" / "src" / "components" / "LegalPage.jsx")
    assert "encryption at rest for stored artefacts" not in text
    assert "encrypted off-box backup archives" in text


# ══════════════════════════════════════════════════════════════════════════
# Part F — the green check must assert what backup.sh actually evaluates
# ══════════════════════════════════════════════════════════════════════════
#
# Round-2 HIGH: deploy-check gated the encryption verdict on the SECRET being
# non-empty, while backup.sh requires the secret AND the binary
# (`... && command -v age`). A droplet where the operator set the recipient but
# skipped `apt-get install -y age` got a green "off-box archives are encrypted
# (age)" and DEPLOY-CHECK PASSED, while every nightly run fell through to the
# final else and REFUSED the push — the evidence trail never left the box and
# the deploy gate said it did.


def _empty_bin(tmp_path: Path) -> Path:
    """A PATH with no age/gpg (and nothing else) — deterministic on any host."""
    d = tmp_path / "nobin"
    d.mkdir(exist_ok=True)
    return d


def _tool_stub(tmp_path: Path, name: str) -> Path:
    d = tmp_path / "toolbin"
    d.mkdir(exist_ok=True)
    p = d / name
    p.write_text("#!/usr/bin/env bash\nexit 0\n")
    p.chmod(0o755)
    return d


@requires_bash
@pytest.mark.parametrize(
    "secret_var,tool",
    [
        ("STATUTEPROOF_BACKUP_AGE_RECIPIENT", "age"),
        ("STATUTEPROOF_BACKUP_PASSPHRASE", "gpg"),
    ],
)
def test_deploy_check_fails_when_encryption_tool_is_missing(tmp_path, secret_var, tool):
    """Secret set, binary absent — backup.sh refuses the push, so this must FAIL."""
    result = _run_block(
        _DEPLOY_CHECK_ENCRYPTION_BLOCK,
        {"STATUTEPROOF_BACKUP_REMOTE": "s3:bucket/path", secret_var: "x"},
        path=str(_empty_bin(tmp_path)),
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "are encrypted" not in result.stdout, result.stdout
    bad_lines = [line for line in result.stdout.splitlines() if line.startswith("BAD:")]
    assert bad_lines, result.stdout
    assert tool in bad_lines[0], bad_lines[0]
    assert "install" in bad_lines[0], bad_lines[0]


@requires_bash
@pytest.mark.parametrize(
    "secret_var,tool",
    [
        ("STATUTEPROOF_BACKUP_AGE_RECIPIENT", "age"),
        ("STATUTEPROOF_BACKUP_PASSPHRASE", "gpg"),
    ],
)
def test_deploy_check_passes_with_remote_secret_and_installed_tool(tmp_path, secret_var, tool):
    result = _run_block(
        _DEPLOY_CHECK_ENCRYPTION_BLOCK,
        {"STATUTEPROOF_BACKUP_REMOTE": "s3:bucket/path", secret_var: "x"},
        path=str(_tool_stub(tmp_path, tool)),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "BAD:" not in result.stdout
    assert any(
        line.startswith("OK:") and secret_var in line for line in result.stdout.splitlines()
    )


def test_encryption_gate_requires_the_same_tooling_backup_sh_requires():
    """Structural guard: neither script may verdict on the secret alone again."""
    check = _read(DEPLOY_CHECK_SH)
    backup = _read(BACKUP_SH)
    for text, label in ((check, "deploy-check.sh"), (backup, "backup.sh")):
        assert (
            '[ -n "${STATUTEPROOF_BACKUP_AGE_RECIPIENT:-}" ] && command -v age' in text
        ), f"{label} no longer requires the age binary alongside the recipient"
        assert (
            '[ -n "${STATUTEPROOF_BACKUP_PASSPHRASE:-}" ] && command -v gpg' in text
        ), f"{label} no longer requires the gpg binary alongside the passphrase"


# --- .env sourcing must never be able to kill the script silently ----------
#
# Round-2 HIGH: both scripts loaded config with
#   `[ -r .env ] && { set -a; . ./.env 2>/dev/null || true; set +a; }`
# Under `set -u` an unset expansion inside .env (e.g. a password-manager
# passphrase containing `$NOPE`) is FATAL to the sourcing shell — `|| true`
# never runs — and `2>/dev/null` swallowed the only diagnostic. backup.sh died
# before the sqlite copy (total backup loss, local and off-box, zero output),
# and deploy-check died before the mangling gate that exists to catch exactly
# that input.

_ENV_MANGLING_LINE = "STATUTEPROOF_BACKUP_PASSPHRASE=abc$NOPE-def"


@requires_bash
@pytest.mark.parametrize("prefix", ["set -euo pipefail\n", "set -uo pipefail\n"])
def test_env_sourcing_survives_an_unset_expansion(tmp_path, prefix):
    (tmp_path / ".env").write_text(_ENV_MANGLING_LINE + "\n", encoding="utf-8")
    script = prefix + _ENV_SOURCE_LINE + "\necho SURVIVED\n"
    result = subprocess.run(
        [BASH, "-c", script],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        env={"PATH": "/usr/bin:/bin"},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "SURVIVED" in result.stdout, result.stdout + result.stderr


@requires_bash
def test_passphrase_gate_still_runs_for_a_passphrase_with_an_unset_expansion(tmp_path):
    """The gate must reach its verdict instead of the shell dying first."""
    result = _run_passphrase_block(tmp_path, _ENV_MANGLING_LINE)
    assert result.returncode == 1, result.stdout + result.stderr
    assert any(line.startswith("BAD:") for line in result.stdout.splitlines()), result.stdout


def test_both_scripts_use_the_guarded_env_sourcing_line():
    assert _ENV_SOURCE_LINE in _read(BACKUP_SH)
    assert _ENV_SOURCE_LINE in _read(DEPLOY_CHECK_SH)
    for text in (_read(BACKUP_SH), _read(DEPLOY_CHECK_SH)):
        assert ". ./.env 2>/dev/null" not in text, (
            "stderr from .env sourcing is the only diagnostic when a value is bad"
        )


# --- the DD pack must not contradict itself, nor claim un-deployed controls -

_PENDING_DEPLOY_MARKER = "takes effect on the production host at its next deploy"


def test_data_flow_subprocessor_table_matches_the_mandatory_remote():
    """§7 said no off-box sub-processor while §4/§5 said one receives the DB nightly."""
    text = _read(VENDOR_DD / "DATA-FLOW-AND-RESIDENCY.md")
    assert "not configured" not in text, (
        "the sub-processor table still tells an outsourcing assessment that no "
        "backup sub-processor is engaged"
    )


@pytest.mark.parametrize(
    "doc",
    ["SECURITY-OVERVIEW.md", "DATA-FLOW-AND-RESIDENCY.md", "VENDOR-DD-FAQ.md"],
)
def test_dd_pack_marks_the_off_box_backup_control_as_pending_deploy(doc):
    """Evidence-first: the pack describes the running host, or says plainly it does not."""
    text = " ".join(_read(VENDOR_DD / doc).split())
    assert _PENDING_DEPLOY_MARKER in text, (
        f"{doc} states the encrypted off-box backup as a current production fact, "
        "but the live host has not been redeployed with it"
    )


# ══════════════════════════════════════════════════════════════════════════
# Part G — dev-only fail-open overrides must be REFUSED on a production host
# ══════════════════════════════════════════════════════════════════════════
#
# Cycle-2 escalation (HIGH): STATUTEPROOF_ALLOW_UNENCRYPTED_BACKUP=1 and
# STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY=1 were honoured everywhere and only
# WARNed in deploy-check, so a prod droplet with either set reached
# DEPLOY-CHECK PASSED while backup.sh pushed the plaintext archive — password
# hashes, emails and the sessions table whose ids are bearer credentials — to
# third-party storage nightly. The failure text itself printed the escape
# hatch, which is how an operator under deploy pressure finds it.

# Shared environment detection, present verbatim in BOTH scripts.
_PROD_DETECT_BLOCK = """\
STATUTEPROOF_IS_PROD=0
case "${STATUTEPROOF_ENV:-${ENVIRONMENT:-}}" in
  production|prod) STATUTEPROOF_IS_PROD=1 ;;
esac
if [ "$APP_ROOT" = "/srv/regradar" ]; then STATUTEPROOF_IS_PROD=1; fi
"""

# backup.sh only: the overrides are neutralised before any branch reads them.
_PROD_OVERRIDE_REFUSAL_BLOCK = """\
if [ "$STATUTEPROOF_IS_PROD" = "1" ]; then
  for _ovr in STATUTEPROOF_ALLOW_UNENCRYPTED_BACKUP STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY; do
    if [ "${!_ovr:-}" = "1" ]; then
      echo "WARNING: $_ovr=1 is a DEVELOPMENT override and is REFUSED on a production host — ignoring it (DEPLOY.md § 9)" >&2
      unset "$_ovr"
    fi
  done
fi
"""


def test_prod_detect_block_matches_both_scripts():
    for path in (BACKUP_SH, DEPLOY_CHECK_SH):
        assert _PROD_DETECT_BLOCK.strip() in _read(path), path.name


def test_prod_override_refusal_block_matches_backup_sh():
    assert _PROD_OVERRIDE_REFUSAL_BLOCK.strip() in _read(BACKUP_SH)


def _run_gate_block(block: str, env_extra: dict[str, str], *, path: str = "/usr/bin:/bin"):
    """Run a deploy-check gate with the environment detection in front of it."""
    env = {"PATH": path, "APP_ROOT": "/tmp/not-prod", "ENVIRONMENT": "development"}
    env.update(env_extra)
    return subprocess.run(
        [BASH, "-c", _HARNESS_PREFIX + _PROD_DETECT_BLOCK + block + 'exit "$FAIL"\n'],
        capture_output=True,
        text=True,
        env=env,
    )


@requires_bash
@pytest.mark.parametrize(
    "prod_env",
    [
        {"ENVIRONMENT": "production"},
        {"ENVIRONMENT": "prod"},
        {"ENVIRONMENT": "development", "STATUTEPROOF_ENV": "production"},
        {"ENVIRONMENT": "development", "APP_ROOT": "/srv/regradar"},
    ],
)
def test_deploy_check_local_only_override_fails_on_production(prod_env):
    """The local-only escape hatch cannot buy a PASSED gate on prod."""
    env = {"STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY": "1"}
    env.update(prod_env)
    result = _run_gate_block(_DEPLOY_CHECK_BACKUP_BLOCK, env)
    assert result.returncode == 1, result.stdout + result.stderr
    bad_lines = [l for l in result.stdout.splitlines() if l.startswith("BAD:")]
    assert bad_lines, result.stdout
    assert "REFUSED" in bad_lines[0], bad_lines[0]


@requires_bash
@pytest.mark.parametrize(
    "prod_env",
    [
        {"ENVIRONMENT": "production"},
        {"ENVIRONMENT": "prod"},
        {"ENVIRONMENT": "development", "STATUTEPROOF_ENV": "production"},
        {"ENVIRONMENT": "development", "APP_ROOT": "/srv/regradar"},
    ],
)
def test_deploy_check_unencrypted_override_fails_on_production(prod_env):
    """The plaintext-push escape hatch cannot buy a PASSED gate on prod."""
    env = {
        "STATUTEPROOF_BACKUP_REMOTE": "s3:bucket/path",
        "STATUTEPROOF_ALLOW_UNENCRYPTED_BACKUP": "1",
    }
    env.update(prod_env)
    result = _run_gate_block(_DEPLOY_CHECK_ENCRYPTION_BLOCK, env)
    assert result.returncode == 1, result.stdout + result.stderr
    bad_lines = [l for l in result.stdout.splitlines() if l.startswith("BAD:")]
    assert bad_lines, result.stdout
    assert "REFUSED" in bad_lines[0], bad_lines[0]
    assert "are encrypted" not in result.stdout


@requires_bash
def test_deploy_check_overrides_still_work_off_production():
    """Dev laptops keep the documented escape hatch — warn, never fail."""
    remote = _run_gate_block(
        _DEPLOY_CHECK_BACKUP_BLOCK, {"STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY": "1"}
    )
    assert remote.returncode == 0, remote.stdout
    assert "WARN:" in remote.stdout and "BAD:" not in remote.stdout
    enc = _run_gate_block(
        _DEPLOY_CHECK_ENCRYPTION_BLOCK,
        {
            "STATUTEPROOF_BACKUP_REMOTE": "s3:bucket/path",
            "STATUTEPROOF_ALLOW_UNENCRYPTED_BACKUP": "1",
        },
    )
    assert enc.returncode == 0, enc.stdout
    assert "WARN:" in enc.stdout and "BAD:" not in enc.stdout


def test_deploy_check_failure_text_never_teaches_the_override():
    """A blocking message must not hand the operator its own escape hatch."""
    for line in _read(DEPLOY_CHECK_SH).splitlines():
        if not line.strip().startswith("bad "):
            continue
        assert "export STATUTEPROOF_ALLOW" not in line, line
        if "STATUTEPROOF_BACKUP" in line or "STATUTEPROOF_ALLOW" in line:
            assert "DEPLOY.md" in line, line


@requires_bash
@pytest.mark.parametrize(
    "prod_env",
    [{"ENVIRONMENT": "production"}, {"APP_ROOT": "/srv/regradar"}],
)
def test_backup_sh_refuses_the_plaintext_override_on_production(tmp_path, prod_env):
    """Even with the override set in prod .env, nothing is pushed in clear."""
    env = {
        "STATUTEPROOF_BACKUP_REMOTE": "s3:bucket/path",
        "STATUTEPROOF_ALLOW_UNENCRYPTED_BACKUP": "1",
        "APP_ROOT": "/tmp/not-prod",
        "ENVIRONMENT": "development",
    }
    env.update(prod_env)
    result, pushed = _run_encrypt_then_push(
        tmp_path, env, with_age=False, with_gpg=False, prod_guard=True
    )
    assert result.returncode == 0, result.stderr
    assert pushed == [], "plaintext archive pushed off-box from a production host"
    assert "REFUSED on a production host" in result.stderr


@requires_bash
def test_backup_sh_still_honours_the_plaintext_override_off_production(tmp_path):
    result, pushed = _run_encrypt_then_push(
        tmp_path,
        {
            "STATUTEPROOF_BACKUP_REMOTE": "s3:bucket/path",
            "STATUTEPROOF_ALLOW_UNENCRYPTED_BACKUP": "1",
            "APP_ROOT": "/tmp/not-prod",
            "ENVIRONMENT": "development",
        },
        with_age=False,
        with_gpg=False,
        prod_guard=True,
    )
    assert result.returncode == 0, result.stderr
    assert len(pushed) == 1 and pushed[0].endswith(".tar.gz"), pushed


@requires_bash
def test_backup_sh_pages_founder_for_local_only_despite_override_on_production(tmp_path):
    """The local-only override cannot silence the founder page on prod."""
    stub = _stub_py(tmp_path)
    env = {
        "PATH": "/usr/bin:/bin",
        "PY_BIN": str(stub),
        "sentinel": str(tmp_path / "called.log"),
        "APP_ROOT": "/tmp/not-prod",
        "ENVIRONMENT": "production",
        "STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY": "1",
    }
    body = (
        _PAGE_FOUNDER_FN
        + _ACCUM_INIT
        + _PROD_DETECT_BLOCK
        + _PROD_OVERRIDE_REFUSAL_BLOCK
        + _WARN_BLOCK
        + _PAGING_BLOCK
    )
    result = subprocess.run(
        [BASH, "-c", "set -euo pipefail\n" + body],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    pages = _paged_lines(tmp_path)
    assert len(pages) == 1 and "LOCAL-ONLY" in pages[0], pages


def test_env_example_says_the_overrides_are_refused_on_production():
    text = _read(REPO_ROOT / ".env.example").lower()
    assert text.count("refused on a production host") >= 2, (
        ".env.example still presents the dev overrides as merely discouraged"
    )


# ══════════════════════════════════════════════════════════════════════════
# Part H — the documented restore must reconstruct everything the backup holds
# ══════════════════════════════════════════════════════════════════════════
#
# Cycle-2 escalation (HIGH): backup.sh archives regradar.db, data/,
# sources.json, .env.example AND evidence/, but DEPLOY.md § Restore only put
# back data/ and regradar.db. evidence/ is a SIBLING of data/ at APP_ROOT, so
# the data/ rsync never covers it — following the runbook verbatim after
# droplet loss reconstitutes the app WITHOUT the sealed evidence records the
# product sells as durable proof, from an archive that contained them.

_RESTORE_ARCHIVE_TOKEN = "backups/statuteproof-backup-<STAMP>.tar.gz"


def _restore_block() -> str:
    """The § Restore bash block that puts files back on the host."""
    text = _read(REPO_ROOT / "DEPLOY.md")
    section = text[text.index("## Restore from backup") :]
    for block in re.findall(r"```bash\n(.*?)```", section, re.S):
        if "tar -xzf " + _RESTORE_ARCHIVE_TOKEN in block:
            return block
    raise AssertionError("no documented local-restore block in DEPLOY.md § Restore")


def test_deploy_md_restore_puts_back_every_archived_path():
    """Each path backup.sh tars must have a restore step in the runbook."""
    block = _restore_block()
    assert "rsync -a /tmp/restore/data/ data/" in block
    assert "rsync -a /tmp/restore/evidence/ evidence/" in block, (
        "the sealed evidence trail is archived and then thrown away on restore"
    )
    assert "/tmp/restore/sources.json" in block, "sources.json is archived but never restored"
    assert "regradar.db" in block


def test_deploy_md_restore_states_what_the_archive_does_not_contain():
    text = _read(REPO_ROOT / "DEPLOY.md")
    section = text[text.index("## Restore from backup") :]
    assert ".env" in section and "not in the archive" in section.lower(), (
        "the runbook must say plainly which files the archive does NOT carry"
    )


def test_deploy_md_restore_reverifies_the_trail_before_services_start():
    block = _restore_block()
    assert "verify-trail" in block, (
        "restoring the DB without re-verifying the evidence trail is the exact "
        "BASELINE DIVERGENCE state the runbook warns about"
    )


def _fake_app_root(tmp_path: Path) -> Path:
    """A scratch APP_ROOT with the five paths backup.sh archives."""
    root = tmp_path / "app"
    (root / "data" / "runs").mkdir(parents=True)
    (root / "data" / "runs" / "run-1.json").write_text("RUN", encoding="utf-8")
    (root / "data" / "outbox").mkdir()
    (root / "data" / "outbox" / "queued.json").write_text("Q", encoding="utf-8")
    (root / "evidence" / "records" / "rec-abc").mkdir(parents=True)
    (root / "evidence" / "records" / "rec-abc" / "record.json").write_text(
        '{"sealed": true}', encoding="utf-8"
    )
    (root / "sources.json").write_text('{"sources": []}', encoding="utf-8")
    (root / ".env.example").write_text("EXAMPLE=1\n", encoding="utf-8")
    (root / "deploy").mkdir()
    shutil.copy(BACKUP_SH, root / "deploy" / "backup.sh")
    stub = root / "py"
    stub.write_text(
        '#!/usr/bin/env bash\ncat > /dev/null\n'
        'case "${2:-}" in *regradar.db) printf SQLITEDB > "$2" ;; esac\nexit 0\n'
    )
    stub.chmod(0o755)
    return root


@requires_bash
def test_documented_restore_round_trips_the_evidence_tree(tmp_path):
    """End to end: real backup.sh, then the runbook's own restore commands."""
    root = _fake_app_root(tmp_path)
    made = subprocess.run(
        [BASH, str(root / "deploy" / "backup.sh")],
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin", "PY_BIN": str(root / "py")},
    )
    assert made.returncode == 0, made.stdout + made.stderr
    archives = sorted((root / "backups").glob("statuteproof-backup-*.tar.gz"))
    assert len(archives) == 1, archives
    listing = subprocess.run(
        ["tar", "-tzf", str(archives[0])], capture_output=True, text=True
    ).stdout
    assert "evidence/records/rec-abc/record.json" in listing, listing

    # Wipe the host the way droplet loss does, then follow § Restore verbatim.
    shutil.rmtree(root / "data")
    shutil.rmtree(root / "evidence")
    (root / "sources.json").unlink()
    restore_tmp = tmp_path / "restore"
    db_dest = tmp_path / "restored.db"

    script_lines = []
    for line in _restore_block().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith(("systemctl", "chown")) or "run.py" in stripped:
            continue  # service control / trail re-verify need a real droplet
        stripped = stripped.replace("cd /srv/regradar", f"cd {root}")
        stripped = stripped.replace(_RESTORE_ARCHIVE_TOKEN, str(archives[0]))
        stripped = stripped.replace("/tmp/restore", str(restore_tmp))
        stripped = re.sub(r'"\$\(\.venv/bin/python.*?\)"', str(db_dest), stripped)
        script_lines.append(stripped)
    assert any("evidence" in l for l in script_lines), script_lines

    restored = subprocess.run(
        [BASH, "-c", "set -euo pipefail\n" + "\n".join(script_lines)],
        capture_output=True,
        text=True,
        cwd=str(root),
        env={"PATH": "/usr/bin:/bin"},
    )
    assert restored.returncode == 0, restored.stdout + restored.stderr

    sealed = root / "evidence" / "records" / "rec-abc" / "record.json"
    assert sealed.exists(), "the sealed evidence tree did not come back"
    assert sealed.read_text() == '{"sealed": true}'
    assert (root / "data" / "runs" / "run-1.json").read_text() == "RUN"
    assert (root / "sources.json").read_text() == '{"sources": []}'
    assert db_dest.read_text() == "SQLITEDB"


# ══════════════════════════════════════════════════════════════════════════
# Part I — the documented deploy ORDER must make the gates actually run
# ══════════════════════════════════════════════════════════════════════════
#
# Cycle-2 escalation (HIGH): § 6 runs deploy-check, but the backup/encryption
# vars are only written to .env in § 9 — and § 9 never re-runs the gate. Every
# gate added this cycle was dead in the documented order of operations.


def _deploy_md_section(start: str, end: str) -> str:
    text = _read(REPO_ROOT / "DEPLOY.md")
    return text[text.index(start) : text.index(end)]


def test_deploy_md_step_4_configures_the_backup_secrets():
    """§ 6's gate can only see vars § 4 told the operator to write."""
    four = _deploy_md_section("## 4. Configuration", "## 5.")
    assert "STATUTEPROOF_BACKUP_REMOTE" in four
    assert "STATUTEPROOF_BACKUP_AGE_RECIPIENT" in four or "STATUTEPROOF_BACKUP_PASSPHRASE" in four


def test_deploy_md_step_9_reruns_the_gate_after_writing_the_secrets():
    nine = _deploy_md_section("## 9. Log rotation", "## External uptime probe")
    last_secret = max(
        nine.rindex("STATUTEPROOF_BACKUP_AGE_RECIPIENT="),
        nine.rindex("STATUTEPROOF_BACKUP_PASSPHRASE="),
    )
    tail = [l.strip() for l in nine[last_secret:].splitlines()]
    assert any(l.endswith("deploy/deploy-check.sh") for l in tail), (
        "§ 9 writes the backup secrets and never re-runs the gate written for them"
    )
    assert any(l.endswith("deploy/backup.sh") for l in tail), (
        "§ 9 never proves the encrypt-and-push path once at deploy time"
    )


def test_deploy_md_step_9_installs_the_tooling_before_writing_the_secret():
    """Recipient set + age missing is the exact state backup.sh refuses."""
    nine = _deploy_md_section("## 9. Log rotation", "## External uptime probe")
    assert nine.index("apt-get install -y age") < nine.index(
        "echo 'STATUTEPROOF_BACKUP_AGE_RECIPIENT="
    ), "the runbook writes the recipient before installing age"


# ══════════════════════════════════════════════════════════════════════════
# Part J — the vendor-DD pack must disclose the overrides, not state absolutes
# ══════════════════════════════════════════════════════════════════════════


def test_vendor_dd_faq_discloses_the_backup_overrides():
    text = _read(VENDOR_DD / "VENDOR-DD-FAQ.md")
    assert "STATUTEPROOF_ALLOW_UNENCRYPTED_BACKUP" in text, (
        "the pack states the encryption control as an absolute and never "
        "discloses the override that defeats it"
    )
    assert "STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY" in text
    assert "ENVIRONMENT=production" in text, (
        "disclosure must say what makes the overrides inert on the prod host"
    )
