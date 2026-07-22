"""
F-backup-timer: the evidence-trail backup is scheduled via systemd and can push
archives off-box so they survive droplet loss.

There is no runtime unit for systemd files, so these tests assert:
  1. deploy/backup.sh is syntactically valid bash.
  2. The env-gated off-box block is a NO-OP when STATUTEPROOF_BACKUP_REMOTE is
     unset, and fires exactly once (via rclone if present, else scp) when set.
  3. The new backup .service/.timer exist and match the proven compaction units
     (same user/paths/hardening style), so they schedule the same backup.sh.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
DEPLOY = REPO_ROOT / "deploy"
SYSTEMD = DEPLOY / "systemd"
BACKUP_SH = DEPLOY / "backup.sh"

BASH = shutil.which("bash")
requires_bash = pytest.mark.skipif(BASH is None, reason="bash not available")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# --- 1. backup.sh syntax ----------------------------------------------------


@requires_bash
def test_backup_sh_is_valid_bash():
    """bash -n parses the whole script without a syntax error."""
    result = subprocess.run(
        [BASH, "-n", str(BACKUP_SH)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


# --- 2. off-box push: env gate ----------------------------------------------

# The exact guard block as it appears in backup.sh. We run it in isolation so
# the test does not need a real SQLite DB. Any drift between this literal and
# the script is caught by test_offbox_block_matches_script below.
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

# The off-box block plus a following "retention" step, so we can prove the
# retention step still runs even when the push command exits non-zero.
_OFFBOX_THEN_RETENTION = _OFFBOX_BLOCK + 'echo retention-ran\n'


def _run_offbox(
    tmp_path: Path,
    remote: str | None,
    *,
    with_rclone: bool,
    fail: bool = False,
    script: str | None = None,
):
    """Run just the off-box block with stub rclone/scp on PATH.

    Each stub appends its name to $sentinel when invoked, so the test can prove
    whether (and via which tool) the push fired. ``fail=True`` makes the push
    tool exit non-zero (simulating a network/creds failure). ``script`` lets a
    caller run a longer snippet (e.g. off-box block + a following step).
    """
    binn = tmp_path / "bin"
    binn.mkdir()
    sentinel = tmp_path / "called.log"
    exit_code = 1 if fail else 0

    def _stub(name: str):
        p = binn / name
        p.write_text(
            f'#!/usr/bin/env bash\necho {name} >> "$sentinel"\nexit {exit_code}\n'
        )
        p.chmod(0o755)

    if with_rclone:
        _stub("rclone")
    _stub("scp")

    env = {
        "PATH": f"{binn}:/usr/bin:/bin",
        "sentinel": str(sentinel),
        "ARCHIVE": str(tmp_path / "statuteproof-backup-TEST.tar.gz"),
        # Set by the encryption step (2b); the push block only ever sends this.
        "PUSH_FILE": str(tmp_path / "statuteproof-backup-TEST.tar.gz.age"),
    }
    if remote is not None:
        env["STATUTEPROOF_BACKUP_REMOTE"] = remote

    body = script if script is not None else _OFFBOX_BLOCK
    result = subprocess.run(
        [BASH, "-c", "set -euo pipefail\n" + body],
        capture_output=True,
        text=True,
        env=env,
    )
    calls = sentinel.read_text().split() if sentinel.exists() else []
    return result, calls


@requires_bash
def test_offbox_push_is_noop_when_unset(tmp_path):
    """Unset env var -> no rclone, no scp, clean exit, no output."""
    result, calls = _run_offbox(tmp_path, remote=None, with_rclone=True)
    assert result.returncode == 0, result.stderr
    assert calls == []
    assert result.stdout.strip() == ""


@requires_bash
def test_offbox_push_is_noop_when_empty(tmp_path):
    """Empty env var is treated the same as unset (guarded by -n)."""
    result, calls = _run_offbox(tmp_path, remote="", with_rclone=True)
    assert result.returncode == 0, result.stderr
    assert calls == []


@requires_bash
def test_offbox_push_uses_rclone_when_available(tmp_path):
    """Set env var + rclone present -> rclone fires exactly once, scp never."""
    result, calls = _run_offbox(
        tmp_path, remote="s3:bucket/path", with_rclone=True
    )
    assert result.returncode == 0, result.stderr
    assert calls == ["rclone"]


@requires_bash
def test_offbox_push_falls_back_to_scp(tmp_path):
    """Set env var + rclone absent -> scp fires exactly once."""
    result, calls = _run_offbox(
        tmp_path, remote="user@host:/path", with_rclone=False
    )
    assert result.returncode == 0, result.stderr
    assert calls == ["scp"]


@requires_bash
def test_offbox_push_failure_is_nonfatal_and_retention_still_runs(tmp_path):
    """F-MEDIUM: an rclone push that fails must NOT abort the script under
    errexit — the following retention step must still run, and the overall
    exit code stays 0 (so the systemd unit does not report a failed backup).
    """
    result, calls = _run_offbox(
        tmp_path,
        remote="s3:bucket/path",
        with_rclone=True,
        fail=True,
        script=_OFFBOX_THEN_RETENTION,
    )
    assert result.returncode == 0, result.stderr
    assert calls == ["rclone"]  # the push was attempted
    assert "retention-ran" in result.stdout  # ...and retention still ran after it
    assert "WARNING" in result.stderr  # failure was logged, not silently dropped


@requires_bash
def test_offbox_scp_failure_is_nonfatal_and_retention_still_runs(tmp_path):
    """Same guarantee on the scp fallback path (rclone absent)."""
    result, calls = _run_offbox(
        tmp_path,
        remote="user@host:/path",
        with_rclone=False,
        fail=True,
        script=_OFFBOX_THEN_RETENTION,
    )
    assert result.returncode == 0, result.stderr
    assert calls == ["scp"]
    assert "retention-ran" in result.stdout
    assert "WARNING" in result.stderr


def test_offbox_block_matches_script():
    """The literal block tested above is present verbatim in backup.sh.

    Guards against the test drifting from the real script.
    """
    assert _OFFBOX_BLOCK.strip() in _read(BACKUP_SH)


def test_offbox_scp_has_connect_and_keepalive_timeouts():
    """The scp push must fail fast on a black-holed remote.

    Without ConnectTimeout a dead host holds the TCP connect for minutes, and
    without ServerAlive* a mid-transfer stall never times out at all — either
    wedges the oneshot backup unit and delays the founder page. The rclone
    branch already caps itself (--contimeout/--timeout); only scp was exposed.
    """
    body = _read(BACKUP_SH)
    scp_lines = [
        line.strip()
        for line in body.splitlines()
        if "scp " in line and "$PUSH_FILE" in line
    ]
    assert scp_lines, "no scp push command found in backup.sh"
    for line in scp_lines:
        assert "-o ConnectTimeout=30" in line, line
        assert "-o ServerAliveInterval=15" in line, line
        assert "-o ServerAliveCountMax=4" in line, line


# --- 2b. local-only warning when the remote is unset ------------------------

# Off-box push is the encouraged default, so an unset remote must not be silent:
# backup.sh warns loudly on stderr each run. This block is separate from the
# push guard (above), stays non-fatal under errexit, and never emits on stdout.
_WARN_BLOCK = """\
if [ -z "${STATUTEPROOF_BACKUP_REMOTE:-}" ]; then
  echo "WARNING: STATUTEPROOF_BACKUP_REMOTE is unset — backups are LOCAL-ONLY on this droplet;" >&2
  echo "WARNING: the evidence trail is NOT protected against droplet loss. Set STATUTEPROOF_BACKUP_REMOTE in .env (see DEPLOY.md § 9) to push each archive off-box." >&2
  if [ "${STATUTEPROOF_ALLOW_LOCAL_BACKUP_ONLY:-}" != "1" ]; then
    BACKUP_PAGE_MSG="⚠️ StatuteProof backup ran LOCAL-ONLY: STATUTEPROOF_BACKUP_REMOTE is unset, so the evidence trail does NOT survive droplet loss. Set it in /srv/regradar/.env (DEPLOY.md § 9)."
  fi
fi
"""

# Warning block followed by a later step, to prove the warning is non-fatal and
# the rest of the backup (retention, etc.) still runs after it.
_WARN_THEN_NEXT = _WARN_BLOCK + 'echo next-step-ran\n'


def _run_warn(remote: str | None, *, script: str | None = None):
    """Run the local-only warning block under errexit; return (result)."""
    env = {"PATH": "/usr/bin:/bin"}
    if remote is not None:
        env["STATUTEPROOF_BACKUP_REMOTE"] = remote
    body = script if script is not None else _WARN_BLOCK
    return subprocess.run(
        [BASH, "-c", "set -euo pipefail\n" + body],
        capture_output=True,
        text=True,
        env=env,
    )


@requires_bash
def test_local_only_warning_fires_when_remote_unset():
    """Unset remote -> loud stderr warning, nothing on stdout, clean exit."""
    result = _run_warn(remote=None, script=_WARN_THEN_NEXT)
    assert result.returncode == 0, result.stderr
    assert "WARNING" in result.stderr
    assert "LOCAL-ONLY" in result.stderr
    assert "droplet loss" in result.stderr
    # The warning must not pollute stdout (that stream carries backup paths).
    assert "WARNING" not in result.stdout
    # Non-fatal: the following backup step still runs after the warning.
    assert "next-step-ran" in result.stdout


@requires_bash
def test_local_only_warning_silent_when_remote_set():
    """Remote set -> no local-only warning (the -z guard is false)."""
    result = _run_warn(remote="s3:bucket/path", script=_WARN_THEN_NEXT)
    assert result.returncode == 0, result.stderr
    assert "LOCAL-ONLY" not in result.stderr
    assert "next-step-ran" in result.stdout


def test_local_only_warning_block_matches_script():
    """The warning block is present verbatim in backup.sh (drift guard)."""
    assert _WARN_BLOCK.strip() in _read(BACKUP_SH)


def test_backup_sh_gates_on_remote_env_var():
    """The push is guarded by the documented env var, not hardcoded."""
    body = _read(BACKUP_SH)
    assert "STATUTEPROOF_BACKUP_REMOTE" in body
    # No unconditional upload: every rclone/scp use sits inside the guard.
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("rclone copy") or stripped.startswith("scp "):
            # These live inside the `if [ -n ... ]` block; ensure the guard
            # opens before they appear.
            idx = body.index(stripped)
            guard = body.index('if [ -n "${STATUTEPROOF_BACKUP_REMOTE:-}" ]')
            assert guard < idx


# --- 3. systemd units -------------------------------------------------------


def test_backup_service_and_timer_exist():
    assert (SYSTEMD / "statuteproof-backup.service").is_file()
    assert (SYSTEMD / "statuteproof-backup.timer").is_file()


def test_backup_service_matches_compaction_style():
    """New service reuses the proven compaction hardening + regradar user."""
    svc = _read(SYSTEMD / "statuteproof-backup.service")
    compaction = _read(SYSTEMD / "statuteproof-compaction.service")

    # oneshot job as the regradar user, same working dir + env file.
    for token in (
        "Type=oneshot",
        "User=regradar",
        "Group=regradar",
        "WorkingDirectory=/srv/regradar",
        "EnvironmentFile=/srv/regradar/.env",
        "NoNewPrivileges=true",
        "PrivateTmp=true",
        "ProtectSystem=full",
        "ReadWritePaths=/srv/regradar",
        "StandardOutput=journal",
        "StandardError=journal",
    ):
        assert token in svc, f"missing {token!r} in backup.service"
        assert token in compaction  # sanity: token really is the shared style

    # It must actually run the backup script (not the compaction command).
    assert "ExecStart=/srv/regradar/deploy/backup.sh" in svc
    assert "compact-heartbeats" not in svc


def test_backup_timer_is_daily_and_persistent():
    timer = _read(SYSTEMD / "statuteproof-backup.timer")
    assert "OnCalendar=" in timer
    assert "Persistent=true" in timer
    assert "Unit=statuteproof-backup.service" in timer
    assert "WantedBy=timers.target" in timer


# Type=oneshot disables the systemd start timeout by default, so a unit that
# performs network I/O (off-box push, Telegram page, external ping, or a remote
# fetch) can wedge indefinitely on a black-holed peer. Each such unit must set a
# TimeoutStartSec so systemd reaps a hung run and the failure surfaces.
_NETWORK_ONESHOT_UNITS = [
    "statuteproof-backup.service",
    "statuteproof-heartbeat.service",
    "statuteproof-verify.service",
    "statuteproof-cbuae-rulebook-watch.service",
    "statuteproof-api-health.service",
]


@pytest.mark.parametrize("unit", _NETWORK_ONESHOT_UNITS)
def test_network_oneshot_units_have_timeout_start_sec(unit):
    """Every network-I/O oneshot unit caps its start time (no default timeout)."""
    svc = _read(SYSTEMD / unit)
    assert "Type=oneshot" in svc, f"{unit} is not oneshot"
    match = re.search(r"^TimeoutStartSec=(\d+)\s*$", svc, re.MULTILINE)
    assert match, f"{unit} missing TimeoutStartSec (oneshot has no default timeout)"
    # A finite, positive cap — never 0/'infinity' which would disable it again.
    assert int(match.group(1)) > 0, f"{unit} TimeoutStartSec must be a positive cap"


# --- 4. API liveness watchdog ----------------------------------------------
# statuteproof-api.service is Type=simple with Restart=on-failure: it recovers a
# CRASH but not an alive-but-wedged API (SQLite writer-lock stall / TasksMax
# thread exhaustion leaves serve_forever() up while every request blocks; Caddy
# returns 502 and the external probe stays green off the scheduler heartbeat).
# The watchdog oneshot + timer is that missing deadman for the API.

API_HEALTH_SH = DEPLOY / "api-health-check.sh"


@requires_bash
def test_api_health_check_sh_is_valid_bash():
    """bash -n parses the watchdog script without a syntax error."""
    result = subprocess.run(
        [BASH, "-n", str(API_HEALTH_SH)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_api_health_check_sh_is_executable():
    assert API_HEALTH_SH.is_file(), "deploy/api-health-check.sh missing"
    assert os.access(API_HEALTH_SH, os.X_OK), "deploy/api-health-check.sh not executable"


def test_api_health_check_probes_and_remediates():
    """Script probes /api/health, restarts the API unit, and pages the founder."""
    sh = _read(API_HEALTH_SH)
    # Probes the API's own health endpoint over loopback.
    assert "/api/health" in sh
    assert "127.0.0.1" in sh
    # Remediation: restart the API unit AND page the founder via the wired channel.
    assert "systemctl restart" in sh
    assert "statuteproof-api.service" in sh
    assert "notify_founder" in sh
    # The 200 path exits clean; the unhealthy path signals remediation via exit 1.
    assert "exit 0" in sh
    assert "exit 1" in sh


def test_api_health_units_exist():
    assert (SYSTEMD / "statuteproof-api-health.service").is_file()
    assert (SYSTEMD / "statuteproof-api-health.timer").is_file()


def test_api_health_service_shape():
    """Oneshot that runs the watchdog script, hardened, with the remediation
    exit code whitelisted (exit 1 = restart+page issued, not a fault)."""
    svc = _read(SYSTEMD / "statuteproof-api-health.service")
    assert "Type=oneshot" in svc
    assert "ExecStart=/srv/regradar/deploy/api-health-check.sh" in svc
    # Must be able to restart a system unit → runs as root (documented deviation
    # from the regradar user the other oneshots use).
    assert "User=root" in svc
    # Shared hardening style.
    for token in (
        "NoNewPrivileges=true",
        "PrivateTmp=true",
        "ProtectSystem=full",
        "ReadWritePaths=/srv/regradar",
        "StandardOutput=journal",
        "StandardError=journal",
        "EnvironmentFile=/srv/regradar/.env",
        "WorkingDirectory=/srv/regradar",
    ):
        assert token in svc, f"missing {token!r} in api-health.service"
    # exit 1 (unhealthy → remediated) must not mark the unit failed.
    assert re.search(r"^SuccessExitStatus=.*\b1\b", svc, re.MULTILINE), (
        "api-health.service must whitelist exit 1 (SuccessExitStatus)"
    )


def test_api_health_timer_is_frequent_and_installed():
    timer = _read(SYSTEMD / "statuteproof-api-health.timer")
    assert "OnUnitActiveSec=" in timer
    assert "Unit=statuteproof-api-health.service" in timer
    assert "WantedBy=timers.target" in timer


def test_deploy_check_registers_api_health_units():
    """The deploy gate must verify the new unit files and timer, else a missing
    watchdog ships green."""
    gate = _read(DEPLOY / "deploy-check.sh")
    assert "statuteproof-api-health.service" in gate
    assert "statuteproof-api-health.timer" in gate
    assert "api-health-check.sh" in gate
