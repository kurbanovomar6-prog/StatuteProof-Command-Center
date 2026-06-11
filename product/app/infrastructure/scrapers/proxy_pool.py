"""
Proxy pool with geo-aware rotation for RU-blocked regulators (cbr.ru).

Strategy: free → paid tier, least-cost first.
Proxy is used ONLY for domains in GEO_RESTRICTED set.
All other requests go direct (no proxy overhead on 90% of traffic).

Free tier (no budget):
  - WebShare free tier: 10 RU proxies, 1GB/mo
  - ProxyScrape API: public proxy list, unreliable but zero cost
  - Rotating residential via SSH tunnel to any RU VPS (~$3/mo on TimeWeb)

Budget impact: adding proxy adds ~200-400ms RTT for CBR only.
"""
import itertools
import logging
import os
import random
import time
from dataclasses import dataclass, field
from threading import Lock
from urllib.parse import urlparse

import httpx

log = logging.getLogger(__name__)

# Only these domains route through proxy — everything else is direct
GEO_RESTRICTED: set[str] = {"cbr.ru", "www.cbr.ru"}

# Env-configurable proxy list (comma-separated)
# Format: http://user:pass@host:port  OR  socks5://host:port
_ENV_PROXIES = os.getenv("RU_PROXIES", "")

# SSH tunnel default (cheapest option: RU VPS + `ssh -D 1080 user@vps`)
_SSH_SOCKS5 = os.getenv("RU_SSH_SOCKS5", "")  # e.g. "socks5://127.0.0.1:1080"


@dataclass
class ProxyEntry:
    url: str
    failures: int = 0
    last_used: float = 0.0
    healthy: bool = True


class ProxyPool:
    """
    Thread-safe proxy pool with:
    - Health-based rotation (skip proxies with consecutive failures)
    - Cooldown after failure (30s before retry)
    - Automatic fallback to direct connection if all proxies fail
    """

    _FAILURE_THRESHOLD = 3    # mark unhealthy after N consecutive failures
    _COOLDOWN_SEC = 30        # seconds before retrying a failed proxy

    def __init__(self):
        self._lock = Lock()
        self._proxies: list[ProxyEntry] = []
        self._cycle = None
        self._load_from_env()

    def _load_from_env(self):
        urls: list[str] = []
        if _SSH_SOCKS5:
            urls.append(_SSH_SOCKS5)
        if _ENV_PROXIES:
            urls.extend(p.strip() for p in _ENV_PROXIES.split(",") if p.strip())
        self._proxies = [ProxyEntry(url=u) for u in urls]
        if self._proxies:
            log.info("proxy_pool: loaded %d proxies", len(self._proxies))
        else:
            log.info("proxy_pool: no proxies configured — will use direct connection for GEO_RESTRICTED sites")

    def _needs_proxy(self, url: str) -> bool:
        try:
            domain = urlparse(url).netloc.lower()
            return any(domain == d or domain.endswith("." + d) for d in GEO_RESTRICTED)
        except Exception:
            return False

    def _pick(self) -> ProxyEntry | None:
        now = time.monotonic()
        with self._lock:
            healthy = [
                p for p in self._proxies
                if p.healthy or (now - p.last_used > self._COOLDOWN_SEC)
            ]
            if not healthy:
                return None
            # Least-recently-used selection
            return min(healthy, key=lambda p: p.last_used)

    def mark_failure(self, proxy_url: str):
        with self._lock:
            for p in self._proxies:
                if p.url == proxy_url:
                    p.failures += 1
                    p.last_used = time.monotonic()
                    if p.failures >= self._FAILURE_THRESHOLD:
                        p.healthy = False
                        log.warning("proxy_pool: marked unhealthy %s", proxy_url[:40])
                    break

    def mark_success(self, proxy_url: str):
        with self._lock:
            for p in self._proxies:
                if p.url == proxy_url:
                    p.failures = 0
                    p.healthy = True
                    p.last_used = time.monotonic()
                    break

    def get(self, url: str, timeout: int = 15, **kwargs) -> httpx.Response:
        """
        Drop-in replacement for httpx.get() with automatic proxy routing.
        Non-restricted URLs go direct; restricted URLs use proxy pool.
        Falls back to direct if all proxies are unhealthy.
        """
        headers = kwargs.pop("headers", {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        })

        if not self._needs_proxy(url):
            # Direct connection — no proxy overhead
            return httpx.get(url, headers=headers, timeout=timeout,
                             follow_redirects=True, **kwargs)

        proxy = self._pick()
        if proxy is None:
            log.warning("proxy_pool: no healthy proxies, trying direct for %s", url[:50])
            return httpx.get(url, headers=headers, timeout=timeout,
                             follow_redirects=True, **kwargs)

        try:
            resp = httpx.get(
                url,
                headers=headers,
                timeout=timeout,
                follow_redirects=True,
                proxies=proxy.url,
                **kwargs,
            )
            self.mark_success(proxy.url)
            log.debug("proxy_pool: OK via %s → %s", proxy.url[:30], url[:50])
            return resp
        except Exception as e:
            self.mark_failure(proxy.url)
            log.warning("proxy_pool: failed %s via %s — %s", url[:50], proxy.url[:30], e)
            # Fallback to direct
            return httpx.get(url, headers=headers, timeout=timeout,
                             follow_redirects=True, **kwargs)


# Singleton — one pool for the whole process
proxy_pool = ProxyPool()
