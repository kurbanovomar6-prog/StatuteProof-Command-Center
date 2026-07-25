"""Pytest configuration for the StatuteProof regradar test suite.

Adds the repository root to sys.path so that the top-level ``tools/``
namespace package is discoverable alongside the local
``product/regradar/tools/`` namespace package.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Repository root: product/regradar/tests/ -> product/regradar/ -> product/ -> repo root
REPO_ROOT = Path(__file__).resolve().parents[3]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ── working-artifact isolation ────────────────────────────────────────────────
#
# Measured 2026-07-25 with tools/measure_test_isolation.py: running
# tests/test_export_authz_limits.py alone changes the working regradar.db. An
# evidence-integrity product whose own suite writes into its own store is one
# accidental `pytest` away from a corrupted artifact, and it makes every "the DB
# says X" observation untrustworthy.
#
# app/db._connect() reads app.db.DB_PATH at CALL time (app/db.py:40), so an
# autouse fixture that repoints that module attribute covers every test without
# import-time env juggling. Tests that already redirect the DB themselves still
# win: their function-scoped patch is applied after this one.

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _isolate_working_artifacts(tmp_path, monkeypatch):
    """Point every test's writes at a temp tree, never the working one."""
    import app.db as app_db

    monkeypatch.setattr(app_db, "DB_PATH", str(tmp_path / "test-regradar.db"), raising=False)
    # BASE_DIR is read at import time by several stores, so the env var only helps
    # code that resolves it lazily — set it anyway so anything that does is covered,
    # and so a subprocess spawned by a test inherits the temp root rather than ours.
    monkeypatch.setenv("STATUTEPROOF_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("REGRADAR_DB_PATH", str(tmp_path / "test-regradar.db"))
    # Deliberately NOT creating subdirectories here: tests own their tmp_path
    # layout, and pre-creating data/ broke a test that calls .mkdir() on it
    # without exist_ok. Isolation must not reshape the sandbox it hands over.
    yield
