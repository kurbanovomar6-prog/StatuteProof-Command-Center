"""Path-confinement contract for the shared evidence-file resolver.

`app.evidence_pack._safe_under_root` gates which files may be read into three
surfaces: the PUBLIC unauthenticated Evidence Room share, the Regulator Binder
handed to regulators, and the Evidence Pack export. Its contract — "resolve
`rel` under `root`; return None if empty or escaping the workspace" — had zero
direct test coverage (test-coverage audit 2026-07-13), so a future refactor
(symlink handling, `.resolve()` semantics, a "simplification") could silently
reopen a traversal read on an externally-facing surface. These tests pin it.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.evidence_pack import _safe_under_root


@pytest.mark.parametrize(
    "rel",
    [
        "../../../etc/passwd",
        "/etc/passwd",
        "sub/../../etc/passwd",
        "..",
        "../outside.txt",
        "",
        "   ",
        None,
    ],
)
def test_safe_under_root_rejects_escape_or_empty(tmp_path, rel):
    assert _safe_under_root(rel, tmp_path) is None


def test_safe_under_root_accepts_legit_relative_path(tmp_path):
    (tmp_path / "sub").mkdir()
    got = _safe_under_root("sub/diff.txt", tmp_path)
    assert got == (tmp_path / "sub" / "diff.txt").resolve()


def test_safe_under_root_rejects_absolute_path_inside_root_when_it_escapes(tmp_path):
    # An absolute path is only accepted if it actually resolves under root.
    outside = tmp_path.parent / "sibling_secret.txt"
    outside.write_text("secret", encoding="utf-8")
    assert _safe_under_root(str(outside), tmp_path) is None


def test_safe_under_root_symlink_escaping_root_is_rejected(tmp_path):
    # A symlink planted inside root that points outside must be caught: .resolve()
    # follows the link, and the relative_to(root) check then rejects it — so the
    # externally-facing surfaces never read the link's real (outside) target.
    outside = tmp_path.parent / "outside_target.txt"
    outside.write_text("SECRET", encoding="utf-8")
    link = tmp_path / "inside_link.txt"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable on this platform")
    assert _safe_under_root("inside_link.txt", tmp_path) is None


def test_evidence_room_diff_excerpt_never_reads_a_traversal_diff_path(tmp_path):
    # The public Evidence Room diff excerpt must yield "" for a record whose
    # diff_path escapes root — never the escaped file's bytes.
    from app.evidence_room import _diff_excerpt

    (tmp_path.parent / "secret_outside_root.txt").write_text("SECRET-LEAK", encoding="utf-8")
    record = {"change": {"diff_path": "../secret_outside_root.txt"}, "files": {}}
    excerpt = _diff_excerpt(record, tmp_path)
    assert "SECRET-LEAK" not in str(excerpt)
