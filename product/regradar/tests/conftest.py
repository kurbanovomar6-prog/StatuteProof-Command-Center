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
