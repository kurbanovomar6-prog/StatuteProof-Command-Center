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
