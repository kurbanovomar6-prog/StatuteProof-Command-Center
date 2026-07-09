"""Eval finding N2 — every store must honor STATUTEPROOF_BASE_DIR.

source_runs honors it (D8), but config.BASE_DIR and email_delivery's
outbox did not: with the env var set, the 2026-07-06 evaluation saw a
verification email written into the repo tree while the trail went to the
configured base dir — and the API read a different tree than the writers.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def _reload_with_env(monkeypatch, tmp_path):
    monkeypatch.setenv("STATUTEPROOF_BASE_DIR", str(tmp_path))
    import app.config as config
    import app.email_delivery as email_delivery

    importlib.reload(config)
    importlib.reload(email_delivery)
    return config, email_delivery


def _restore(monkeypatch):
    monkeypatch.delenv("STATUTEPROOF_BASE_DIR", raising=False)
    import app.config as config
    import app.email_delivery as email_delivery

    importlib.reload(config)
    importlib.reload(email_delivery)


def test_config_base_dir_honors_env(tmp_path, monkeypatch):
    config, _ = _reload_with_env(monkeypatch, tmp_path)
    try:
        assert Path(config.BASE_DIR) == tmp_path.resolve()
    finally:
        _restore(monkeypatch)


def test_email_outbox_honors_env(tmp_path, monkeypatch):
    _, email_delivery = _reload_with_env(monkeypatch, tmp_path)
    try:
        result = email_delivery.send_verification_email(
            "n2@example.com",
            "https://example.com/verify?token=n2-alignment",
            env={"STATUTEPROOF_EMAIL_PROVIDER": "local_outbox"},
        )
        written = list(tmp_path.rglob("*.json"))
        assert written, f"outbox file must land under the configured base dir, got: {result}"
        repo_data = Path(__file__).parent.parent / "data"
        fresh_repo_files = [
            p for p in repo_data.rglob("*n2-alignment*")
        ]
        assert not fresh_repo_files, "nothing may be written into the repo tree"
    finally:
        _restore(monkeypatch)


def test_default_unchanged_without_env(monkeypatch):
    _restore(monkeypatch)
    import app.config as config

    assert Path(config.BASE_DIR) == Path(config.__file__).parent.parent
