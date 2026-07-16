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
