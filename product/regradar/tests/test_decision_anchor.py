"""Stage-3 decision-head external anchoring — ``app.decision_anchor``.

The sweep RFC3161-anchors every org's decision-chain head by reusing the
existing TSA machinery (:func:`app.rfc3161_anchor.maybe_anchor_head`) verbatim.
All tests use a MOCKED TSA (``rfc3161_anchor.request_timestamp`` is
monkeypatched) — NO real network is ever touched. Coverage:

* dormant by default is a COMPLETE no-op: TSA env unset -> skipped_dormant,
  zero network (transport seams monkeypatched to fail loudly), zero threads,
  zero sidecars, not even a directory listing;
* enabled path: sidecar written next to each org's head file; the stored
  ``sha256:`` prefix is stripped to the bare digest the imprint machinery needs;
* multi-org sweep + per-org fail-soft (one corrupt head never stops the sweep);
* org cap honored; non-canonical / non-int / non-dir entries skipped;
* idempotency: a second sweep over unmoved heads makes zero TSA calls;
* never raises (root-is-a-file, machinery raising mid-sweep);
* wiring: the daily ``verify-trail-watch`` maintenance run invokes the sweep
  best-effort and its failure can never change the watchdog's exit code.
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys
import threading
import urllib.request
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.decision_records as decision_records
from app import decision_anchor
from app import rfc3161_anchor as anchor


# ── fixtures & helpers ────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _dormant_by_default(monkeypatch):
    """Guarantee the anchor is dormant unless a test opts in (mirrors the TSA tests)."""
    monkeypatch.delenv(anchor.ENV_TSA_URL, raising=False)
    yield


@pytest.fixture()
def isolated_base(tmp_path, monkeypatch):
    """Point the decision head-file base dir at a temp dir (owning-module knob)."""
    monkeypatch.setattr(decision_records, "_BASE_DIR", tmp_path)
    return tmp_path


@pytest.fixture()
def enabled(monkeypatch):
    """Enable the anchor and mock the TSA at the request seam (no network, ever).

    Returns the list of digests handed to ``request_timestamp`` so tests can
    assert exactly what reached the (mocked) TSA and how many times.
    """
    monkeypatch.setenv(anchor.ENV_TSA_URL, "https://tsa.test.invalid/tsr")
    calls: list[str] = []

    def _fake_request_timestamp(digest_hex: str):
        calls.append(digest_hex)
        return {
            "schema_version": "1.0",
            "token_format": anchor.TOKEN_FORMAT,
            "token_b64": base64.b64encode(b"fake-rfc3161-token-der").decode("ascii"),
            "tsa_url": "https://tsa.test.invalid/tsr",
            "digest_hex": digest_hex,
            "digest_algorithm": "sha256",
            "requested_at": "2026-07-13T00:00:00Z",
            "asserted_time_utc": "2026-07-13T00:00:00Z",
            "nonce": "1",
        }

    monkeypatch.setattr(anchor, "request_timestamp", _fake_request_timestamp)
    return calls


def _digest(seed: bytes) -> str:
    return hashlib.sha256(seed).hexdigest()


def _write_head(base: Path, org_id: int, head_hash: str) -> Path:
    """Write an org head file byte-shape-identical to ``_write_decision_head``."""
    path = base / "data" / "decision_chain" / str(org_id) / "decision_chain_head.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "org_id": org_id,
        "decision_id": f"dec_{org_id}_1_{'0' * 20}",
        "chain_seq": 1,
        "head_decision_hash": head_hash,
        "updated_at": "2026-07-13T00:00:00+00:00",
        "last_update_kind": "append",
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return path


def _sidecars_under(base: Path) -> list[Path]:
    return sorted(base.rglob("*.tsr*"))


# ── 1. dormant by default = complete no-op ──────────────────────────────────────

def test_dormant_default_no_network_no_sidecar_no_thread(isolated_base, monkeypatch):
    _write_head(isolated_base, 1, "sha256:" + _digest(b"org-1"))

    # Every network seam fails LOUDLY if touched: the transport isolation seam,
    # the module's opener, and stdlib urlopen itself.
    monkeypatch.setattr(
        anchor, "_post_timestamp_query",
        lambda *a, **k: pytest.fail("transport must NOT be called when dormant"),
    )
    monkeypatch.setattr(
        anchor._TSA_OPENER, "open",
        lambda *a, **k: pytest.fail("opener must NOT be called when dormant"),
    )
    monkeypatch.setattr(
        urllib.request, "urlopen",
        lambda *a, **k: pytest.fail("urlopen must NOT be called when dormant"),
    )

    threads_before = threading.active_count()
    summary = decision_anchor.anchor_decision_heads_now()

    assert summary == {"orgs_seen": 0, "anchor_attempted": 0, "skipped_dormant": True}
    assert threading.active_count() == threads_before
    assert _sidecars_under(isolated_base) == []


def test_dormant_skips_even_the_directory_listing(monkeypatch):
    """The dormant contract is checked BEFORE any filesystem work."""
    monkeypatch.setattr(
        decision_anchor, "_chain_root",
        lambda: pytest.fail("the chain root must not be resolved when dormant"),
    )
    summary = decision_anchor.anchor_decision_heads_now()
    assert summary["skipped_dormant"] is True


# ── 2. enabled path: sidecar next to the org head, prefix stripped ───────────────

def test_enabled_anchors_org_head_and_writes_sidecar(isolated_base, enabled):
    bare = _digest(b"org-7-head")
    head_path = _write_head(isolated_base, 7, "sha256:" + bare)

    summary = decision_anchor.anchor_decision_heads_now()

    assert summary == {"orgs_seen": 1, "anchor_attempted": 1, "skipped_dormant": False}
    # The ONLY digest that reached the (mocked) TSA is the bare 64-hex head.
    assert enabled == [bare]

    sidecar = anchor.sidecar_path_for(head_path)
    assert sidecar.exists()
    stored = json.loads(sidecar.read_text(encoding="utf-8"))
    assert stored["anchored_head_record_hash"] == bare
    assert stored["token_format"] == anchor.TOKEN_FORMAT
    # The raw DER token sidecar is dropped next to it, by the same machinery.
    tsr = head_path.with_name(anchor.SIDECAR_TSR_NAME)
    assert tsr.exists()
    assert tsr.read_bytes() == b"fake-rfc3161-token-der"
    # ADDITIVE: the head file itself is byte-for-byte untouched.
    assert json.loads(head_path.read_text(encoding="utf-8"))["head_decision_hash"] == (
        "sha256:" + bare
    )


def test_enabled_accepts_bare_hash_heads_too(isolated_base, enabled):
    """A head stored without the ``sha256:`` prefix anchors identically."""
    bare = _digest(b"bare-head")
    _write_head(isolated_base, 3, bare)

    summary = decision_anchor.anchor_decision_heads_now()

    assert summary["anchor_attempted"] == 1
    assert enabled == [bare]


# ── 3. multi-org sweep ───────────────────────────────────────────────────────────

def test_multi_org_sweep_anchors_every_org(isolated_base, enabled):
    heads = {}
    for org_id in (1, 2, 42):
        bare = _digest(f"org-{org_id}".encode())
        heads[org_id] = (bare, _write_head(isolated_base, org_id, "sha256:" + bare))

    summary = decision_anchor.anchor_decision_heads_now()

    assert summary == {"orgs_seen": 3, "anchor_attempted": 3, "skipped_dormant": False}
    assert sorted(enabled) == sorted(bare for bare, _ in heads.values())
    for org_id, (bare, head_path) in heads.items():
        sidecar = anchor.sidecar_path_for(head_path)
        assert sidecar.exists(), f"org {org_id} missing its sidecar"
        assert json.loads(sidecar.read_text())["anchored_head_record_hash"] == bare


def test_idempotent_second_sweep_makes_no_tsa_calls(isolated_base, enabled):
    _write_head(isolated_base, 1, "sha256:" + _digest(b"idem-1"))
    _write_head(isolated_base, 2, "sha256:" + _digest(b"idem-2"))

    first = decision_anchor.anchor_decision_heads_now()
    assert first["anchor_attempted"] == 2
    assert len(enabled) == 2

    second = decision_anchor.anchor_decision_heads_now()
    # Heads unmoved -> the sidecar cache satisfies both orgs: ZERO new TSA calls.
    assert second == {"orgs_seen": 2, "anchor_attempted": 2, "skipped_dormant": False}
    assert len(enabled) == 2

    # A moved head (org 1 sealed again) re-anchors ONLY that org.
    advanced = _digest(b"idem-1-advanced")
    _write_head(isolated_base, 1, "sha256:" + advanced)
    decision_anchor.anchor_decision_heads_now()
    assert len(enabled) == 3
    assert enabled[-1] == advanced


# ── 4. fail-soft: one bad head never stops the sweep ─────────────────────────────

def test_corrupt_head_is_skipped_and_sweep_continues(isolated_base, enabled):
    # org 1: corrupt JSON head file.
    corrupt = isolated_base / "data" / "decision_chain" / "1" / "decision_chain_head.json"
    corrupt.parent.mkdir(parents=True, exist_ok=True)
    corrupt.write_text("{not json", encoding="utf-8")
    # org 2: healthy head.
    bare = _digest(b"healthy-org-2")
    good_path = _write_head(isolated_base, 2, "sha256:" + bare)
    # org 3: directory exists but the head file is missing.
    (isolated_base / "data" / "decision_chain" / "3").mkdir(parents=True, exist_ok=True)

    summary = decision_anchor.anchor_decision_heads_now()

    assert summary == {"orgs_seen": 3, "anchor_attempted": 1, "skipped_dormant": False}
    assert enabled == [bare]
    assert anchor.sidecar_path_for(good_path).exists()
    assert not anchor.sidecar_path_for(corrupt).exists()


def test_machinery_raising_mid_sweep_never_escapes(isolated_base, enabled, monkeypatch):
    _write_head(isolated_base, 1, "sha256:" + _digest(b"boom-1"))
    _write_head(isolated_base, 2, "sha256:" + _digest(b"boom-2"))

    def _boom(*a, **k):
        raise RuntimeError("machinery blew up")

    monkeypatch.setattr(anchor, "maybe_anchor_head", _boom)

    summary = decision_anchor.anchor_decision_heads_now()  # must NOT raise

    assert summary["orgs_seen"] == 2
    assert summary["anchor_attempted"] == 0  # neither org completed an attempt
    assert summary["skipped_dormant"] is False


def test_root_being_a_file_returns_benign_summary(isolated_base, enabled):
    # data/decision_chain exists but is a FILE, not a directory.
    root = isolated_base / "data" / "decision_chain"
    root.parent.mkdir(parents=True, exist_ok=True)
    root.write_text("not a directory", encoding="utf-8")

    summary = decision_anchor.anchor_decision_heads_now()

    assert summary == {"orgs_seen": 0, "anchor_attempted": 0, "skipped_dormant": False}
    assert enabled == []


def test_missing_root_returns_benign_summary(isolated_base, enabled):
    summary = decision_anchor.anchor_decision_heads_now()
    assert summary == {"orgs_seen": 0, "anchor_attempted": 0, "skipped_dormant": False}
    assert enabled == []


# ── 5. bounds: org cap + non-canonical entries ───────────────────────────────────

def test_org_cap_bounds_the_sweep(isolated_base, enabled, monkeypatch):
    for org_id in range(1, 6):  # 5 orgs
        _write_head(isolated_base, org_id, "sha256:" + _digest(f"cap-{org_id}".encode()))
    monkeypatch.setattr(decision_anchor, "MAX_ORGS_PER_SWEEP", 3)

    summary = decision_anchor.anchor_decision_heads_now()

    assert summary["orgs_seen"] == 3
    assert summary["anchor_attempted"] == 3
    assert len(enabled) == 3


def test_non_canonical_and_non_dir_entries_are_skipped(isolated_base, enabled):
    chain = isolated_base / "data" / "decision_chain"
    chain.mkdir(parents=True, exist_ok=True)
    # Junk that must never be treated as an org:
    (chain / "abc").mkdir()          # non-numeric
    (chain / "007").mkdir()          # non-canonical (writer uses str(int(id)))
    (chain / "-1").mkdir()           # negative
    (chain / "1.5").mkdir()          # not an int
    (chain / "9").write_text("a plain file, not an org dir", encoding="utf-8")
    # One real org:
    bare = _digest(b"real-org")
    _write_head(isolated_base, 5, "sha256:" + bare)

    summary = decision_anchor.anchor_decision_heads_now()

    assert summary == {"orgs_seen": 1, "anchor_attempted": 1, "skipped_dormant": False}
    assert enabled == [bare]


def test_org_id_dirname_parser():
    assert decision_anchor._org_id_from_dirname("42") == 42
    assert decision_anchor._org_id_from_dirname("0") == 0
    assert decision_anchor._org_id_from_dirname("007") is None
    assert decision_anchor._org_id_from_dirname("-1") is None
    assert decision_anchor._org_id_from_dirname("1.5") is None
    assert decision_anchor._org_id_from_dirname("abc") is None
    assert decision_anchor._org_id_from_dirname("") is None
    assert decision_anchor._org_id_from_dirname("١٢") is None  # unicode digits
    assert decision_anchor._org_id_from_dirname("9" * 40) is None  # over length bound


# ── 6. wiring: the daily verify-trail-watch run invokes the sweep ────────────────

class _StubReport:
    ok = True

    def as_dict(self):
        return {"ok": True}


def test_daily_verify_watch_runs_the_sweep(monkeypatch, capsys):
    from tools import verify_trail_watch as vtw

    calls: list[int] = []
    monkeypatch.setattr(
        decision_anchor,
        "anchor_decision_heads_now",
        lambda: calls.append(1)
        or {"orgs_seen": 0, "anchor_attempted": 0, "skipped_dormant": True},
    )
    monkeypatch.setattr(vtw.vt, "verify_trail", lambda source_id=None: _StubReport())

    rc = vtw.run_watch([])

    assert rc == 0
    assert calls == [1]  # the sweep ran exactly once on the daily maintenance path


def test_daily_verify_watch_sweep_failure_never_changes_exit_code(monkeypatch, capsys):
    from tools import verify_trail_watch as vtw

    def _boom():
        raise RuntimeError("sweep exploded")

    monkeypatch.setattr(decision_anchor, "anchor_decision_heads_now", _boom)
    monkeypatch.setattr(vtw.vt, "verify_trail", lambda source_id=None: _StubReport())

    rc = vtw.run_watch([])  # must not raise

    assert rc == 0  # the watchdog verdict is untouched by the add-on pass


class _StubChain:
    ok = False
    break_index = 0
    break_source_id = "src"
    break_run_id = "run"
    reason = "stub break"


class _StubDivergentReport:
    ok = False
    divergent: list = []
    chain = _StubChain()

    def as_dict(self):
        return {"ok": False}


def test_divergence_alert_fires_before_the_sweep(monkeypatch, capsys):
    """LOAD-BEARING ORDER: a slow TSA sweep must never delay an integrity page."""
    from tools import verify_trail_watch as vtw

    order: list[str] = []
    monkeypatch.setattr(
        vtw.vt, "verify_trail", lambda source_id=None: _StubDivergentReport()
    )
    monkeypatch.setattr(
        vtw.ops_alert, "notify_founder", lambda msg: order.append("alert") or True
    )
    monkeypatch.setattr(
        decision_anchor,
        "anchor_decision_heads_now",
        lambda: order.append("sweep")
        or {"orgs_seen": 0, "anchor_attempted": 0, "skipped_dormant": True},
    )

    rc = vtw.run_watch([])

    assert rc == 1
    assert order == ["alert", "sweep"]  # founder is paged FIRST, sweep runs after
