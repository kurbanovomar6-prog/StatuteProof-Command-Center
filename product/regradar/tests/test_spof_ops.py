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
# STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY=1 is a documented DEV-ONLY override.
if [ -n "${STATUTEPROOF_BACKUP_REMOTE:-}" ]; then
  ok "STATUTEPROOF_BACKUP_REMOTE set — backup archives push off-box"
elif [ "${STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY:-}" = "1" ]; then
  warn "backups are LOCAL-ONLY (STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY=1 dev override — never use on prod)"
else
  bad "STATUTEPROOF_BACKUP_REMOTE is unset — evidence trail does not survive droplet loss; set it in .env (DEPLOY.md § 9) or export STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY=1 (dev only)"
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
    env = {"PATH": "/usr/bin:/bin"}
    env.update(env_extra)
    return subprocess.run(
        [BASH, "-c", _HARNESS_PREFIX + _DEPLOY_CHECK_BACKUP_BLOCK + 'exit "$FAIL"\n'],
        capture_output=True,
        text=True,
        env=env,
    )


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
if [ -n "${STATUTEPROOF_BACKUP_REMOTE:-}" ]; then
  if command -v rclone >/dev/null 2>&1; then
    if rclone copy "$ARCHIVE" "$STATUTEPROOF_BACKUP_REMOTE"; then
      echo "off-box copy (rclone): $ARCHIVE -> $STATUTEPROOF_BACKUP_REMOTE"
    else
      echo "WARNING: off-box copy (rclone) failed; local archive kept, continuing to retention" >&2
      BACKUP_PAGE_MSG="🚨 StatuteProof off-box backup push FAILED (rclone). The archive exists only on the droplet. Check: journalctl -u statuteproof-backup"
    fi
  else
    if scp "$ARCHIVE" "$STATUTEPROOF_BACKUP_REMOTE"; then
      echo "off-box copy (scp): $ARCHIVE -> $STATUTEPROOF_BACKUP_REMOTE"
    else
      echo "WARNING: off-box copy (scp) failed; local archive kept, continuing to retention" >&2
      BACKUP_PAGE_MSG="🚨 StatuteProof off-box backup push FAILED (scp). The archive exists only on the droplet. Check: journalctl -u statuteproof-backup"
    fi
  fi
fi
"""

# Final step: one deferred page per run, only when something went wrong.
_PAGING_BLOCK = """\
# 5) Deferred founder page (single message per run; see page_founder above).
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
[ -r .env ] && { set -a; . ./.env 2>/dev/null || true; set +a; }
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
