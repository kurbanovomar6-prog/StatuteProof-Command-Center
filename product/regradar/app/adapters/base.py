"""
Source adapter base class — v4.2.

Adapters provide source-specific content extraction for regulator websites
that defeat the generic two-tier scraper (requests → Playwright).

Contract
--------
• fetch_content() returns clean paragraph text, NOT raw HTML.
• Returns None when the adapter cannot extract meaningful content.
• Never raises — all exceptions must be caught internally.
• Logs failures at WARNING level.

Quality gate
------------
is_quality_content() is the shared helper used by the pipeline to decide
whether adapter output is good enough to use.  If the adapter's text does
not pass this check, the pipeline falls back to the generic scraper.
"""

import ipaddress
import logging
import socket
from urllib.parse import urlsplit, urlunsplit

import requests
import urllib3

from app.text_quality import is_mostly_unreadable

logger = logging.getLogger(__name__)

# Content must exceed both thresholds to be accepted
_MIN_CONTENT_CHARS = 500
_MIN_CONTENT_PARAS = 3

# Undecodable-content guard: real page text decoded correctly contains
# essentially zero unreadable characters (see app/text_quality.py for the
# shared definition). A body that failed decoding (e.g. compressed bytes
# read as UTF-8) is saturated with them. Tolerate a small absolute number
# (sloppy server encodings emit a stray one or two) but reject saturation.
_UNREADABLE_CHAR_FLOOR = 8
_UNREADABLE_CHAR_RATIO = 0.02

# Hard ceiling on DECOMPRESSED response size for adapter fetches. With
# brotli installed, urllib3 transparently inflates br bodies whose
# compression ratio an attacker controls — a bounded chunked read is the
# only guard that limits peak memory (Content-Length reflects wire size,
# not decompressed size). Matches scraper.py's _MAX_RESPONSE_BYTES.
MAX_FETCH_BYTES = 10 * 1024 * 1024
_FETCH_CHUNK_BYTES = 64 * 1024

# ── SSRF guard ────────────────────────────────────────────────────────────────
#
# The pipeline fetches ~116 external regulator URLs. A malicious, compromised,
# or MITM'd source can answer with a 30x redirect (or a rebound DNS record)
# pointing at an internal address — cloud metadata (169.254.169.254),
# loopback, RFC1918, link-local, etc. That is a classic SSRF.
#
# Defence: follow redirects MANUALLY (allow_redirects=False in a bounded loop)
# and, BEFORE firing each hop, resolve the target host and reject if ANY
# resolved IP is non-public. Validation must precede the connection — a
# post-hoc check is too late because the request already fired against the
# internal host. requests re-resolves DNS on connect, so a check that merely
# looked at getaddrinfo would still leave a narrow rebind window; we therefore
# pin the vetted IP and connect straight to it while preserving the original
# Host header and TLS SNI (see _resolve_public_addr / _PinnedHTTPAdapter).

# Only http/https are ever fetched. file://, ftp://, gopher:// etc. are SSRF
# primitives in their own right and must never be followed.
_ALLOWED_SCHEMES = frozenset({"http", "https"})

# Cap redirect chain length. requests defaults to 30; a monitored regulator
# page needs at most a couple of hops (http→https, trailing-slash, www).
_MAX_REDIRECTS = 5

_DEFAULT_PORTS = {"http": 80, "https": 443}


def _ip_to_netloc_host(ip: str) -> str:
    """
    Return a URL-authority-safe host token for a literal IP address.

    IPv6 literals MUST be wrapped in ``[...]`` per RFC 3986 authority syntax;
    a bare IPv6 literal produces a malformed URL (``https://2606:...::1/``)
    that requests rejects with InvalidURL. IPv4 literals and already-bracketed
    values pass through unchanged. This function does NOT strip an IPv6 scope
    id (``fe80::1%eth0``); it does not need to, because scoped/link-local
    literals never reach it — ``_ip_is_blocked`` rejects link-local addresses
    upstream (``_resolve_public_addr`` returns None), so only public, unscoped
    literals are pinned and passed here.
    """
    if ":" not in ip:
        return ip  # IPv4 literal — no bracketing needed
    if ip.startswith("["):
        return ip  # already bracketed
    return f"[{ip}]"


def _ip_is_blocked(ip: "ipaddress._BaseAddress") -> bool:
    """
    Return True when an IP must not be connected to from the fetch path.

    Blocks the full non-public space: loopback (127/8, ::1), private
    (10/8, 172.16/12, 192.168/16, fc00::/7 unique-local), link-local
    (169.254/16 incl. cloud metadata, fe80::/10), unspecified (0.0.0.0, ::),
    multicast, and reserved. IPv4-mapped IPv6 is unwrapped first so an
    attacker cannot smuggle a private v4 address inside a v6 literal.

    ``ip.is_multicast`` must be checked explicitly: ``ipaddress`` classifies
    224.0.0.0/4 (e.g. 239.255.255.250 SSDP) and ff00::/8 (e.g. ff02::1) as
    ``is_global=True``, so ``not ip.is_global`` alone would let them through.
    """
    if getattr(ip, "ipv4_mapped", None) is not None:
        ip = ip.ipv4_mapped
    return not ip.is_global or ip.is_loopback or ip.is_link_local or ip.is_multicast


def _resolve_public_addr(host: str, port: int) -> tuple[int, int, str] | None:
    """
    Resolve ``host`` and return one vetted (family, socktype, ip) tuple to
    connect to, or None if the host does not resolve or ANY resolved address
    is non-public.

    Rejecting when *any* address is blocked (rather than picking a public one)
    closes the multi-record trick where a host publishes both a public and an
    internal A record. Returns the first resolved address so the caller can
    pin it and skip re-resolution on connect. Never raises.
    """
    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except (socket.gaierror, UnicodeError, ValueError) as exc:
        logger.warning("ssrf-guard: cannot resolve host %r: %s", host, exc)
        return None
    if not infos:
        logger.warning("ssrf-guard: host %r resolved to no addresses", host)
        return None

    vetted: tuple[int, int, str] | None = None
    for family, socktype, _proto, _canon, sockaddr in infos:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            logger.warning("ssrf-guard: unparseable resolved address %r for %r", ip_str, host)
            return None
        if _ip_is_blocked(ip):
            logger.warning(
                "ssrf-guard: BLOCKED %r → non-public address %s", host, ip_str,
            )
            return None
        if vetted is None:
            vetted = (family, socktype, ip_str)
    return vetted


def _validate_fetch_target(url: str) -> tuple[int, int, str] | None:
    """
    Parse and vet a fetch target URL. Returns the vetted connect address
    (family, socktype, ip) for a public http/https host, or None when the
    URL is malformed, uses a disallowed scheme, or resolves to a non-public
    address. Never raises.
    """
    try:
        parts = urlsplit(url)
    except ValueError as exc:
        logger.warning("ssrf-guard: unparseable URL %r: %s", url, exc)
        return None

    scheme = (parts.scheme or "").lower()
    if scheme not in _ALLOWED_SCHEMES:
        logger.warning("ssrf-guard: disallowed scheme %r in %r", scheme, url)
        return None

    host = parts.hostname
    if not host:
        logger.warning("ssrf-guard: URL has no host: %r", url)
        return None

    try:
        port = parts.port if parts.port is not None else _DEFAULT_PORTS[scheme]
    except ValueError as exc:
        logger.warning("ssrf-guard: bad port in %r: %s", url, exc)
        return None

    return _resolve_public_addr(host, port)


class _SSRFPoolManager(urllib3.PoolManager):
    """
    PoolManager that only applies the TLS-only pinning kwargs
    (server_hostname / assert_hostname) to HTTPS pools.

    urllib3 already strips SSL_KEYWORDS (which includes ``server_hostname``)
    from the connection kwargs for http pools, but ``assert_hostname`` is NOT
    in that set, so it leaks into HTTPConnection.__init__() and raises
    ``TypeError: ... unexpected keyword argument 'assert_hostname'``. We drop
    it here for the http scheme so a plain-HTTP hop (e.g. an https→http
    redirect, or a future http:// source) connects cleanly instead of the
    crash being swallowed by _guarded_get and the source silently dropping
    out of monitoring.
    """

    def _new_pool(self, scheme, host, port, request_context=None):
        if scheme == "http":
            if request_context is None:
                request_context = self.connection_pool_kw.copy()
            request_context.pop("assert_hostname", None)
            request_context.pop("server_hostname", None)
        return super()._new_pool(scheme, host, port, request_context)


class _PinnedHTTPAdapter(requests.adapters.HTTPAdapter):
    """
    Connect to a pre-vetted IP instead of re-resolving the hostname.

    _validate_fetch_target resolves and vets the host, then this adapter
    forces urllib3 to open the socket to that exact IP. Without pinning,
    requests would re-run DNS at connect time and an attacker controlling
    the record could rebind it to an internal address between our check and
    the connection (TOCTOU). The Host header and TLS SNI still carry the
    original hostname so name-based virtual hosting and certificate
    validation keep working.
    """

    def __init__(self, pinned_ip: str, server_hostname: str, **kwargs):
        self._pinned_ip = pinned_ip
        self._server_hostname = server_hostname
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=requests.adapters.DEFAULT_POOLBLOCK, **pool_kwargs):
        # assert_hostname / server_hostname make urllib3 validate the cert
        # against the real hostname even though we dial the pinned IP. These
        # are TLS-only: _SSRFPoolManager drops them for http pools so a
        # plain-HTTP hop does not TypeError on HTTPConnection.__init__().
        pool_kwargs["server_hostname"] = self._server_hostname
        pool_kwargs["assert_hostname"] = self._server_hostname
        # save these values for pickling (mirrors HTTPAdapter.init_poolmanager)
        self._pool_connections = connections
        self._pool_maxsize = maxsize
        self._pool_block = block
        self.poolmanager = _SSRFPoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            **pool_kwargs,
        )

    def send(self, request, **kwargs):
        # Rewrite the URL host to the pinned IP so urllib3 connects to it,
        # but restore the Host header so the server routes correctly.
        parsed = urlsplit(request.url)
        host_header = request.headers.get("Host") or parsed.hostname
        # Bracket IPv6 literals so the rewritten authority is RFC 3986-valid.
        # A bare IPv6 netloc (e.g. https://2606:4700:4700::1111/) makes requests
        # raise InvalidURL, which _guarded_get would swallow — silently breaking
        # every dual-stack / IPv6 regulator host it pins.
        pinned_host = _ip_to_netloc_host(self._pinned_ip)
        netloc = pinned_host
        if parsed.port is not None:
            netloc = f"{pinned_host}:{parsed.port}"
        request.url = urlunsplit(
            (parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment)
        )
        request.headers["Host"] = host_header
        return super().send(request, **kwargs)


def _guarded_get(
    url: str, *, headers: dict, timeout: float, verify: bool, label: str
):
    """
    Perform an SSRF-guarded, redirect-following GET and return the final
    streamed requests.Response (status 200 body not yet read), or None.

    Each hop is validated with _validate_fetch_target BEFORE the request
    fires, and connected via a per-hop pinned adapter so the vetted IP is
    the one actually dialled. Redirects are followed manually up to
    _MAX_REDIRECTS. Never raises.
    """
    session = requests.Session()
    # Do not inherit any environment proxies / trust settings that could
    # route the "public" fetch through an attacker-controlled hop.
    session.trust_env = False
    current_url = url
    seen = 0
    try:
        while True:
            parts = urlsplit(current_url)
            host = parts.hostname
            vetted = _validate_fetch_target(current_url)
            if vetted is None:
                logger.warning("%s: SSRF guard blocked %s", label, current_url)
                session.close()
                return None
            _family, _socktype, pinned_ip = vetted

            # _validate_fetch_target only returns a vetted address for a URL
            # with a non-empty host, so `host` is guaranteed str here. Assert
            # it so the server_hostname=host invariant is enforced structurally
            # rather than relying on that upstream side effect (host is str|None
            # per urlsplit typing).
            assert host, "vetted fetch target must have a host"

            adapter = _PinnedHTTPAdapter(pinned_ip=pinned_ip, server_hostname=host)
            session.mount("https://", adapter)
            session.mount("http://", adapter)

            response = session.get(
                current_url,
                headers=headers,
                timeout=timeout,
                allow_redirects=False,
                stream=True,
                verify=verify,
            )

            if response.is_redirect or response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("Location")
                response.close()
                if not location:
                    logger.warning("%s: redirect with no Location from %s", label, current_url)
                    session.close()
                    return None
                seen += 1
                if seen > _MAX_REDIRECTS:
                    logger.warning(
                        "%s: exceeded %d redirects starting at %s",
                        label, _MAX_REDIRECTS, url,
                    )
                    session.close()
                    return None
                # Resolve the redirect target relative to the current URL,
                # then loop to re-validate the new host before connecting.
                current_url = requests.compat.urljoin(current_url, location)
                continue

            # Live response handed to the caller; the connection pool is
            # released when the caller closes/exhausts the response body.
            return response
    except Exception as exc:
        logger.warning("%s: request failed for %s: %s", label, url, exc)
        session.close()
        return None


def read_bytes_bounded(response, max_bytes: int, label: str = "adapter") -> bytes | None:
    """
    Read a streamed requests response in chunks, aborting once the
    DECOMPRESSED size exceeds max_bytes. Returns None on overflow or
    read failure — never raises.
    """
    chunks: list[bytes] = []
    total = 0
    try:
        for chunk in response.iter_content(chunk_size=_FETCH_CHUNK_BYTES):
            total += len(chunk)
            if total > max_bytes:
                logger.warning(
                    "%s: response exceeded %d MB decompressed for %s — aborting read",
                    label, max_bytes // (1024 * 1024), response.url,
                )
                response.close()
                return None
            chunks.append(chunk)
    except Exception as exc:
        logger.warning("%s: bounded read failed for %s: %s", label, response.url, exc)
        return None
    return b"".join(chunks)


def fetch_bytes_bounded(
    url: str,
    *,
    headers: dict,
    timeout: float,
    max_bytes: int = MAX_FETCH_BYTES,
    label: str = "adapter",
    verify: bool = True,
) -> bytes | None:
    """
    HTTP GET returning raw (decompressed) bytes with a hard size cap.

    For XML/RSS payloads where the parser handles encoding declarations
    itself. Returns None on any failure. Never raises.

    Redirects are followed manually with a per-hop SSRF guard (see
    _guarded_get): every hop's resolved IP is vetted BEFORE connecting and
    a non-public target (loopback / RFC1918 / link-local / cloud metadata)
    is rejected.
    """
    response = _guarded_get(
        url, headers=headers, timeout=timeout, verify=verify, label=label
    )
    if response is None:
        return None

    with response:
        if response.status_code != 200:
            logger.warning("%s: HTTP %d for %s", label, response.status_code, url)
            return None
        declared_len = response.headers.get("Content-Length")
        if declared_len is not None:
            try:
                if int(declared_len) > max_bytes:
                    logger.warning(
                        "%s: Content-Length %s exceeds %d MB limit for %s",
                        label, declared_len, max_bytes // (1024 * 1024), url,
                    )
                    return None
            except ValueError:
                pass  # malformed header; the bounded read below still protects us
        return read_bytes_bounded(response, max_bytes, label=label)


def fetch_text_bounded_status(
    url: str,
    *,
    headers: dict,
    timeout: float,
    max_bytes: int = MAX_FETCH_BYTES,
    label: str = "adapter",
    verify: bool = True,
) -> tuple[int | None, str | None]:
    """
    HTTP GET with a hard cap on decompressed body size, preserving status.

    Returns (status_code, text). status_code is None when the request itself
    failed (including when the SSRF guard blocks a hop); text is None on any
    failure (request error, non-200 status, oversized body). Never raises.

    Redirects are followed manually with a per-hop SSRF guard (see
    _guarded_get): every hop's resolved IP is vetted BEFORE connecting and
    a non-public target (loopback / RFC1918 / link-local / cloud metadata)
    is rejected.
    """
    response = _guarded_get(
        url, headers=headers, timeout=timeout, verify=verify, label=label
    )
    if response is None:
        return None, None

    with response:
        status = response.status_code
        if status != 200:
            logger.warning("%s: HTTP %d for %s", label, status, url)
            return status, None

        declared_len = response.headers.get("Content-Length")
        if declared_len is not None:
            try:
                if int(declared_len) > max_bytes:
                    logger.warning(
                        "%s: Content-Length %s exceeds %d MB limit for %s",
                        label, declared_len, max_bytes // (1024 * 1024), url,
                    )
                    return status, None
            except ValueError:
                pass  # malformed header; the bounded read below still protects us

        data = read_bytes_bounded(response, max_bytes, label=label)
        if data is None:
            return status, None

        encoding = response.encoding or response.apparent_encoding or "utf-8"
        try:
            return status, data.decode(encoding, errors="replace")
        except LookupError:
            return status, data.decode("utf-8", errors="replace")


def fetch_text_bounded(
    url: str,
    *,
    headers: dict,
    timeout: float,
    max_bytes: int = MAX_FETCH_BYTES,
    label: str = "adapter",
    verify: bool = True,
) -> str | None:
    """
    HTTP GET with a hard cap on decompressed body size.

    Returns decoded text on success, None on any failure (request error,
    non-200 status, oversized body). Never raises.
    """
    _, text = fetch_text_bounded_status(
        url, headers=headers, timeout=timeout, max_bytes=max_bytes, label=label, verify=verify
    )
    return text


def is_quality_content(text: str | None) -> bool:
    """
    Return True when adapter text is substantial enough to use.

    Checks:
      - text is not None or empty
      - at least _MIN_CONTENT_CHARS total characters
      - at least _MIN_CONTENT_PARAS non-empty double-newline paragraphs
      - not saturated with undecodable characters (binary or mis-decoded
        body must fall back to the generic scraper, never enter the diff)
    """
    if not text or len(text) < _MIN_CONTENT_CHARS:
        return False
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paras) < _MIN_CONTENT_PARAS:
        return False
    if is_mostly_unreadable(
        text, floor=_UNREADABLE_CHAR_FLOOR, ratio=_UNREADABLE_CHAR_RATIO
    ):
        logger.warning(
            "is_quality_content: rejecting undecodable content (%d chars)", len(text)
        )
        return False
    return True


class SourceAdapter:
    """
    Abstract base for source-specific content adapters.

    Subclasses must set ``name`` and implement ``can_handle`` and
    ``fetch_content``.
    """

    name: str = "base"

    def can_handle(self, url: str, source: dict | None = None) -> bool:
        """Return True when this adapter can service the given URL."""
        return False

    def fetch_content(self, url: str, source: dict | None = None) -> str | None:
        """
        Fetch and return clean paragraph text for the URL.

        Returns None when extraction is not possible or content quality
        is insufficient.  Must never raise.
        """
        return None
