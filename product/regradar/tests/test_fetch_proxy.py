"""Egress-proxy support for WAF/geo-blocked regulator hosts.

Several UAE regulator portals (verified live: CBUAE rulebook + main site, DFSA
news, ADGM/FSRA) return HTTP 403 to our datacenter IP while serving 200 to other
IPs. An owner-configured forward proxy (env STATUTEPROOF_FETCH_PROXY) is applied
ONLY to an allowlist of those hosts, so the proxy is never aimed at an
arbitrary/user-supplied URL. These tests pin the security-critical behavior:
allowlist gating + the SSRF guard still refusing internal targets even when a
proxy is configured.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.adapters.base as base  # noqa: E402
from app.adapters.base import proxy_for_url  # noqa: E402


def _recent_ts() -> str:
    """Timestamp of a run recorded in the current cycle — the verified-count
    predicate only accepts records recent enough to evidence the CURRENT
    configuration, so fixtures must not hardcode a fixed date."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def test_proxy_none_when_env_unset(monkeypatch):
    monkeypatch.delenv("STATUTEPROOF_FETCH_PROXY", raising=False)
    assert proxy_for_url("https://rulebook.centralbank.ae/en/rulebook/x") is None


def test_proxy_applies_only_to_allowlisted_hosts(monkeypatch):
    monkeypatch.setenv("STATUTEPROOF_FETCH_PROXY", "http://proxy.example:8080")
    monkeypatch.delenv("STATUTEPROOF_PROXY_HOSTS", raising=False)
    # Allowlisted blocked regulators → proxy.
    assert proxy_for_url("https://rulebook.centralbank.ae/en/rulebook/x") == "http://proxy.example:8080"
    assert proxy_for_url("https://www.centralbank.ae/en/") == "http://proxy.example:8080"
    assert proxy_for_url("https://www.dfsa.ae/news") == "http://proxy.example:8080"
    # NOT allowlisted → no proxy (normal direct, IP-pinned fetch).
    assert proxy_for_url("https://www.vara.ae/en/") is None
    assert proxy_for_url("https://evil.attacker.example/x") is None


def test_proxy_never_applied_to_internal_targets(monkeypatch):
    """SSRF safety: an internal/metadata URL is never on the allowlist, so it
    never receives a proxy (would otherwise be a way to aim the proxy inward)."""
    monkeypatch.setenv("STATUTEPROOF_FETCH_PROXY", "http://proxy.example:8080")
    monkeypatch.delenv("STATUTEPROOF_PROXY_HOSTS", raising=False)
    assert proxy_for_url("http://169.254.169.254/latest/meta-data/") is None
    assert proxy_for_url("http://127.0.0.1/") is None
    assert proxy_for_url("http://10.0.0.5/internal") is None


def test_proxy_custom_allowlist_replaces_default(monkeypatch):
    monkeypatch.setenv("STATUTEPROOF_FETCH_PROXY", "http://p:1")
    monkeypatch.setenv("STATUTEPROOF_PROXY_HOSTS", "example.gov, portal.test")
    assert proxy_for_url("https://data.example.gov/x") == "http://p:1"
    assert proxy_for_url("https://portal.test/y") == "http://p:1"
    # Default hosts no longer apply once an explicit list is set.
    assert proxy_for_url("https://rulebook.centralbank.ae/x") is None


def test_guarded_get_with_proxy_still_blocks_internal_target():
    """The proxy changes TRANSPORT, not the guard: _guarded_get must still refuse
    an internal/metadata target (link-local 169.254.169.254) even when a proxy is
    passed — the per-hop SSRF validation runs before any connection."""
    result = base._guarded_get(
        "http://169.254.169.254/latest/meta-data/",
        headers={}, timeout=5, verify=True, label="test",
        proxy="http://proxy.example:8080",
    )
    assert result is None


def test_guarded_get_proxy_flows_to_session_for_public_host(monkeypatch):
    """When the target passes SSRF validation, the proxy is set on the session so
    the request actually egresses through it (and the pinned adapter is skipped)."""
    captured: dict = {}

    # Pretend the host resolves to a public address so validation passes.
    monkeypatch.setattr(base, "_validate_fetch_target", lambda url: (2, 1, "93.184.216.34"))

    class _FakeResp:
        status_code = 200
        is_redirect = False

    class _FakeSession:
        def __init__(self):
            self.proxies = {}
            self.trust_env = True
            self.mounted: list = []

        def mount(self, prefix, adapter):
            self.mounted.append(type(adapter).__name__)

        def get(self, *a, **k):
            captured["proxies"] = dict(self.proxies)
            captured["mounted"] = list(self.mounted)
            return _FakeResp()

        def close(self):
            pass

    monkeypatch.setattr(base.requests, "Session", _FakeSession)

    resp = base._guarded_get(
        "https://rulebook.centralbank.ae/en/rulebook/x",
        headers={}, timeout=5, verify=True, label="test",
        proxy="http://proxy.example:8080",
    )
    assert resp is not None
    assert captured["proxies"] == {"http": "http://proxy.example:8080", "https": "http://proxy.example:8080"}
    # Proxy path must NOT mount the IP-pinning adapter (incompatible with a proxy);
    # it mounts the plain default adapter instead.
    assert "_PinnedHTTPAdapter" not in captured["mounted"]


def test_redact_creds_scrubs_proxy_password():
    from app.adapters.base import _redact_creds
    assert _redact_creds("ProxyError: http://user:secret@proxy:8080 failed") == \
        "ProxyError: http://***@proxy:8080 failed"
    assert "secret" not in _redact_creds("connect to https://u:p@h/x")
    assert _redact_creds("plain error, no creds") == "plain error, no creds"


def test_guarded_get_drops_proxy_on_off_allowlist_redirect(monkeypatch):
    """Open-relay defence: a redirect that LEAVES the allowlist must be fetched
    DIRECTLY (no proxy). One allowlisted first hop must not authorise the proxy
    for an arbitrary redirect target (e.g. an open redirect off a regulator site)."""
    monkeypatch.setenv("STATUTEPROOF_FETCH_PROXY", "http://proxy.example:8080")
    monkeypatch.delenv("STATUTEPROOF_PROXY_HOSTS", raising=False)
    monkeypatch.setattr(base, "_validate_fetch_target", lambda url: (2, 1, "93.184.216.34"))
    hops: list = []

    class _Resp:
        def __init__(self, status, location=None):
            self.status_code = status
            self.is_redirect = location is not None
            self.headers = {"Location": location} if location else {}

        def close(self):
            pass

    class _Sess:
        def __init__(self):
            self.proxies: dict = {}
            self.trust_env = True
            self._n = 0

        def mount(self, *a):
            pass

        def get(self, current_url, **k):
            hops.append((current_url, dict(self.proxies)))
            self._n += 1
            if self._n == 1:  # redirect CBUAE (allowlisted) -> non-allowlisted host
                return _Resp(302, "https://evil.attacker.example/x")
            return _Resp(200)

        def close(self):
            pass

    monkeypatch.setattr(base.requests, "Session", _Sess)
    base._guarded_get(
        "https://rulebook.centralbank.ae/en/rulebook/x",
        headers={}, timeout=5, verify=True, label="test",
        proxy="http://proxy.example:8080",
    )
    # Hop 1 (CBUAE, allowlisted) → proxied.
    assert hops[0][1].get("https") == "http://proxy.example:8080"
    # Hop 2 (evil.attacker.example, NOT allowlisted) → proxy dropped (direct).
    assert hops[1][1] == {}


def test_proxy_unblocked_remediation_truth_table(monkeypatch):
    """A remediation source re-enters the alert pool ONLY when all four hold:
    monitoring_mode == remediation, explicit proxy_remediation flag, proxy env
    configured, and the host on the fixed allowlist. The explicit flag is what
    keeps the 10 dfsa.ae remediation sources (unverified remediation cause)
    from silently flipping."""
    from app.sources import proxy_unblocked_remediation

    cbuae = {
        "url": "https://rulebook.centralbank.ae/en/rulebook/x",
        "monitoring_mode": "remediation",
        "proxy_remediation": True,
        "alert_eligible": False,
    }
    monkeypatch.delenv("STATUTEPROOF_FETCH_PROXY", raising=False)
    monkeypatch.delenv("STATUTEPROOF_PROXY_HOSTS", raising=False)
    assert proxy_unblocked_remediation(cbuae) is False  # no proxy → stays out

    monkeypatch.setenv("STATUTEPROOF_FETCH_PROXY", "http://proxy.example:8080")
    assert proxy_unblocked_remediation(cbuae) is True   # proxy set → re-enters
    assert proxy_unblocked_remediation({**cbuae, "proxy_remediation": False}) is False
    assert proxy_unblocked_remediation({k: v for k, v in cbuae.items() if k != "proxy_remediation"}) is False
    assert proxy_unblocked_remediation({**cbuae, "monitoring_mode": "candidate"}) is False
    assert proxy_unblocked_remediation({**cbuae, "url": "https://example.gov.ae/x"}) is False  # host not allowlisted
    assert proxy_unblocked_remediation(None) is False


def test_alert_gate_admits_proxy_unblocked_cbuae_remediation(monkeypatch):
    from app.pipeline import _source_may_auto_alert

    cbuae = {
        "name": "CBUAE Rulebook X",
        "url": "https://rulebook.centralbank.ae/en/rulebook/x",
        "monitoring_mode": "remediation",
        "proxy_remediation": True,
        "alert_eligible": False,
    }
    candidate = {"url": "https://example.gov.ae/c", "monitoring_mode": "candidate", "alert_eligible": False}

    monkeypatch.delenv("STATUTEPROOF_FETCH_PROXY", raising=False)
    monkeypatch.delenv("STATUTEPROOF_PROXY_HOSTS", raising=False)
    assert _source_may_auto_alert(cbuae) is False       # today's behavior preserved
    assert _source_may_auto_alert(None) is True         # bare-URL path unchanged
    assert _source_may_auto_alert({"url": "https://x.example"}) is True  # no registry flags → unchanged

    monkeypatch.setenv("STATUTEPROOF_FETCH_PROXY", "http://proxy.example:8080")
    assert _source_may_auto_alert(cbuae) is True        # proxy set → alert pool
    assert _source_may_auto_alert(candidate) is False   # SF-3: candidates NEVER flip


def test_proxy_remediation_verified_requires_recorded_success(monkeypatch, tmp_path):
    """Config alone is NOT evidence: the customer-facing count predicate must
    stay False until a successful production run is recorded for the source,
    and drop back to False when the source goes back to failing (e.g. CBUAE
    also blocks the proxy's egress IP)."""
    import json as _json

    from app.sources import proxy_remediation_verified

    cbuae = {
        "url": "https://rulebook.centralbank.ae/en/rulebook/x",
        "monitoring_mode": "remediation",
        "proxy_remediation": True,
        "alert_eligible": False,
    }
    runs_file = tmp_path / "source_runs.jsonl"
    monkeypatch.setenv("STATUTEPROOF_FETCH_PROXY", "http://proxy.example:8080")
    monkeypatch.delenv("STATUTEPROOF_PROXY_HOSTS", raising=False)

    # Proxy configured but no run trail at all → unverified, never counted.
    assert proxy_remediation_verified(cbuae, runs_file=runs_file) is False

    # Latest recorded run for the URL is FAILED → still unverified.
    runs_file.write_text(
        _json.dumps({"url": cbuae["url"], "official_url": cbuae["url"], "change_status": "FAILED",
                     "timestamp_utc": _recent_ts()}) + "\n",
        encoding="utf-8",
    )
    assert proxy_remediation_verified(cbuae, runs_file=runs_file) is False

    # A successful run through the proxy is recorded → NOW counted. Another
    # source's newer FAILED record must not mask it (per-URL scan).
    with runs_file.open("a", encoding="utf-8") as fh:
        fh.write(_json.dumps({"url": cbuae["url"], "official_url": cbuae["url"], "change_status": "NO_CHANGE",
                              "timestamp_utc": _recent_ts()}) + "\n")
        fh.write(_json.dumps({"url": "https://other.example/y", "change_status": "FAILED",
                              "timestamp_utc": _recent_ts()}) + "\n")
    assert proxy_remediation_verified(cbuae, runs_file=runs_file) is True

    # QUALITY_DROP is not a verified good fetch either.
    with runs_file.open("a", encoding="utf-8") as fh:
        fh.write(_json.dumps({"url": cbuae["url"], "official_url": cbuae["url"], "change_status": "QUALITY_DROP",
                              "timestamp_utc": _recent_ts()}) + "\n")
    assert proxy_remediation_verified(cbuae, runs_file=runs_file) is False

    # Without the proxy env the routing predicate is False → verified is too.
    monkeypatch.delenv("STATUTEPROOF_FETCH_PROXY", raising=False)
    assert proxy_remediation_verified(cbuae, runs_file=runs_file) is False


def test_proxy_remediation_verified_requires_a_RECENT_record(monkeypatch, tmp_path):
    """A stale success is not evidence of the CURRENT configuration: the 25
    CBUAE entries still carry successful records from before the host began
    returning 403, so counting the newest record regardless of age would let
    setting STATUTEPROOF_FETCH_PROXY alone inflate the public fresh-alert count
    with zero successful proxied fetches."""
    import json as _json
    from datetime import datetime, timedelta, timezone

    from app.sources import proxy_remediation_verified

    cbuae = {
        "url": "https://rulebook.centralbank.ae/en/rulebook/x",
        "monitoring_mode": "remediation",
        "proxy_remediation": True,
        "alert_eligible": False,
    }
    runs_file = tmp_path / "source_runs.jsonl"
    monkeypatch.setenv("STATUTEPROOF_FETCH_PROXY", "http://proxy.example:8080")
    monkeypatch.delenv("STATUTEPROOF_PROXY_HOSTS", raising=False)

    def _write(stamp, status="NO_CHANGE"):
        record = {"url": cbuae["url"], "official_url": cbuae["url"], "change_status": status}
        if stamp is not None:
            record["timestamp_utc"] = stamp
        runs_file.write_text(_json.dumps(record) + "\n", encoding="utf-8")

    now = datetime.now(timezone.utc)

    # (a) newest record is a success from weeks ago (pre-403 baseline) → NOT counted.
    _write((now - timedelta(days=17)).isoformat())
    assert proxy_remediation_verified(cbuae, runs_file=runs_file) is False

    # (b) same source, success recorded in the current cycle → counted.
    _write((now - timedelta(minutes=5)).isoformat())
    assert proxy_remediation_verified(cbuae, runs_file=runs_file) is True

    # (c) recent but FAILED / QUALITY_DROP → NOT counted.
    for status in ("FAILED", "QUALITY_DROP"):
        _write((now - timedelta(minutes=5)).isoformat(), status)
        assert proxy_remediation_verified(cbuae, runs_file=runs_file) is False

    # (d) missing or unparseable timestamp → unverified, never counted.
    _write(None)
    assert proxy_remediation_verified(cbuae, runs_file=runs_file) is False
    _write("not-a-timestamp")
    assert proxy_remediation_verified(cbuae, runs_file=runs_file) is False


def test_sources_summary_counts_proxy_remediation_only_after_verified_run(monkeypatch, tmp_path):
    """Customer-facing fresh_alert_count must NOT jump on activation day: with
    the proxy env set but zero successful fetches recorded, a proxy-remediation
    source stays out of the count; it enters only once a successful production
    run for it exists in the trail."""
    import json as _json

    from app.source_summary import build_sources_summary

    cbuae_url = "https://rulebook.centralbank.ae/en/rulebook/x"
    sources = [
        {
            "name": "CBUAE Rulebook X", "url": cbuae_url, "jurisdiction": "AE",
            "category": "banking", "enabled": True,
            "monitoring_mode": "remediation", "proxy_remediation": True,
            "alert_eligible": False,
        },
        {
            "name": "VARA", "url": "https://www.vara.ae/en/", "jurisdiction": "AE",
            "category": "vasp", "enabled": True,
            "monitoring_mode": "fresh_alert", "alert_eligible": True,
        },
    ]
    (tmp_path / "sources.json").write_text(_json.dumps(sources), encoding="utf-8")
    runs_dir = tmp_path / "data" / "source_runs"
    runs_dir.mkdir(parents=True)
    runs_file = runs_dir / "source_runs.jsonl"

    monkeypatch.setenv("STATUTEPROOF_FETCH_PROXY", "http://proxy.example:8080")
    monkeypatch.delenv("STATUTEPROOF_PROXY_HOSTS", raising=False)

    # Env set, no verified run → only the genuine fresh_alert source counts.
    summary = build_sources_summary("AE", base_dir=tmp_path)
    assert summary["fresh_alert_count"] == 1
    assert summary["remediation_count"] == 1

    # First successful proxied run recorded → the source enters the count.
    runs_file.write_text(
        _json.dumps({
            "url": cbuae_url, "official_url": cbuae_url, "market": "AE",
            "change_status": "NO_CHANGE",
            "timestamp_utc": _recent_ts(),
        }) + "\n",
        encoding="utf-8",
    )
    summary = build_sources_summary("AE", base_dir=tmp_path)
    assert summary["fresh_alert_count"] == 2


def _proxy_summary_fixture(tmp_path, *, proxy_source_count: int = 3):
    """sources.json + a verified run trail for ``proxy_source_count`` CBUAE
    remediation sources plus one of every other counted mode."""
    import json as _json

    urls = [f"https://rulebook.centralbank.ae/en/rulebook/{i}" for i in range(proxy_source_count)]
    sources = [
        {
            "name": f"CBUAE Rulebook {i}", "url": url, "jurisdiction": "AE",
            "category": "banking", "enabled": True,
            "monitoring_mode": "remediation", "proxy_remediation": True,
            "alert_eligible": False,
        }
        for i, url in enumerate(urls)
    ] + [
        {
            "name": "VARA", "url": "https://www.vara.ae/en/", "jurisdiction": "AE",
            "category": "vasp", "enabled": True,
            "monitoring_mode": "fresh_alert", "alert_eligible": True,
        },
        {
            "name": "Library", "url": "https://www.difc.ae/lib", "jurisdiction": "AE",
            "category": "legal", "enabled": True,
            "monitoring_mode": "evidence_library", "alert_eligible": False,
        },
        {
            "name": "Candidate", "url": "https://example.gov.ae/c", "jurisdiction": "AE",
            "category": "legal", "enabled": True,
            "monitoring_mode": "candidate", "alert_eligible": False,
        },
    ]
    (tmp_path / "sources.json").write_text(_json.dumps(sources), encoding="utf-8")
    runs_dir = tmp_path / "data" / "source_runs"
    runs_dir.mkdir(parents=True)
    runs_file = runs_dir / "source_runs.jsonl"
    with runs_file.open("w", encoding="utf-8") as fh:
        for url in urls:
            fh.write(_json.dumps({
                "url": url, "official_url": url, "market": "AE",
                "change_status": "NO_CHANGE",
                "timestamp_utc": _recent_ts(),
            }) + "\n")
    return sources


def test_proxy_promoted_sources_are_not_double_counted(monkeypatch, tmp_path):
    """Buckets must stay disjoint: a proxy-remediation source promoted into
    fresh_alert_count must leave remediation_count, so fresh-alert + the four
    mode counts partition enabled_count exactly (no inflated coverage)."""
    from app.source_summary import build_sources_summary

    _proxy_summary_fixture(tmp_path, proxy_source_count=3)
    monkeypatch.setenv("STATUTEPROOF_FETCH_PROXY", "http://proxy.example:8080")
    monkeypatch.delenv("STATUTEPROOF_PROXY_HOSTS", raising=False)

    summary = build_sources_summary("AE", base_dir=tmp_path)
    assert summary["enabled_count"] == 6
    assert summary["fresh_alert_count"] == 4  # 1 genuine + 3 verified proxy
    assert summary["remediation_count"] == 0  # all three promoted out
    counts = summary["monitoring_mode_counts"]
    total = (
        summary["fresh_alert_count"]
        + counts["evidence_library"]
        + counts["candidate"]
        + counts["remediation"]
    )
    assert total == summary["enabled_count"]


def test_summary_reads_run_trail_at_most_once(monkeypatch, tmp_path):
    """GET /api/health is unauthenticated: the fresh-alert count must read and
    parse the run-trail tail ONCE per request, not once per proxy source."""
    from app.source_summary import build_sources_summary

    _proxy_summary_fixture(tmp_path, proxy_source_count=3)
    monkeypatch.setenv("STATUTEPROOF_FETCH_PROXY", "http://proxy.example:8080")
    monkeypatch.delenv("STATUTEPROOF_PROXY_HOSTS", raising=False)

    opens: list[str] = []
    real_open = Path.open

    def counting_open(self, *args, **kwargs):
        mode = kwargs.get("mode", args[0] if args else "r")
        if self.name == "source_runs.jsonl" and "b" in str(mode):
            opens.append(str(self))
        return real_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", counting_open)
    summary = build_sources_summary("AE", base_dir=tmp_path)
    assert summary["fresh_alert_count"] == 4
    assert len(opens) <= 1, f"trail tail read {len(opens)} times for 3 proxy sources"


def test_sources_json_cbuae_rulebook_entries_carry_proxy_remediation_flag():
    import json
    from urllib.parse import urlsplit

    entries = json.loads((Path(__file__).parent.parent / "sources.json").read_text(encoding="utf-8"))
    rulebook = [
        s for s in entries
        if (urlsplit(s.get("url", "")).hostname or "").endswith("rulebook.centralbank.ae")
        and s.get("monitoring_mode") == "remediation"
    ]
    assert len(rulebook) == 25
    assert all(s.get("proxy_remediation") is True for s in rulebook)
    assert all(s.get("enabled") is True for s in rulebook)


def test_proxy_residual_risk_is_documented_and_honest():
    """The proxy path must not overclaim SSRF protection: a residual-risk
    statement must exist and explicitly name that IP-pinning is NOT done and the
    DNS-rebind window is not closed for the allowlisted hosts."""
    from app.adapters.base import PROXY_RESIDUAL_RISK
    assert isinstance(PROXY_RESIDUAL_RISK, str) and len(PROXY_RESIDUAL_RISK) > 100
    low = PROXY_RESIDUAL_RISK.lower()
    assert "pin" in low
    assert "rebind" in low
    assert "allowlist" in low
