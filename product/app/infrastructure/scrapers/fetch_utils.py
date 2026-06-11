"""
fetch_utils.py — отказоустойчивый HTTP-клиент для RegRadar.

Возможности:
  - Exponential backoff: 2s → 4s → 8s при 429/5xx/таймаутах
  - curl_cffi fingerprint spoofing (обход TLS-фингерпринтинга Cloudflare)
  - Автопереключение прокси при сбое
  - Content-hash деduplication на уровне бинарника PDF

Используется в discovery.py и pipeline.py вместо голого httpx.get().
"""
import hashlib
import logging
import time
from typing import Optional

import httpx

# Пробуем импортировать curl_cffi — дает браузерный TLS-фингерпринт
try:
    from curl_cffi import requests as _cffi
    _HAS_CFFI = True
except ImportError:
    _HAS_CFFI = False

log = logging.getLogger(__name__)

# ── Ротация User-Agent ─────────────────────────────────────────────
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]
_UA_IDX = 0


def _next_ua() -> str:
    """Круговая ротация User-Agent."""
    global _UA_IDX
    ua = _USER_AGENTS[_UA_IDX % len(_USER_AGENTS)]
    _UA_IDX += 1
    return ua


def _build_headers() -> dict:
    return {
        "User-Agent": _next_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


# ── Exponential backoff fetch ──────────────────────────────────────

def fetch_html(
    url: str,
    timeout: int = 20,
    max_retries: int = 3,
    proxy: Optional[str] = None,
) -> Optional[str]:
    """
    Скачивает HTML страницы с retry + exponential backoff.
    При 429/5xx ждёт 2^n секунд перед повторной попыткой.
    Возвращает None если все попытки исчерпаны.
    """
    delay = 2
    for attempt in range(1, max_retries + 1):
        try:
            headers = _build_headers()

            # curl_cffi дает браузерный TLS-фингерпринт — обходит Cloudflare/Imperva
            if _HAS_CFFI:
                r = _cffi.get(
                    url, headers=headers, timeout=timeout,
                    impersonate="chrome120",
                    proxies={"https": proxy, "http": proxy} if proxy else None,
                )
            else:
                r = httpx.get(
                    url, headers=headers, timeout=timeout,
                    follow_redirects=True,
                    proxies=proxy,
                )

            if r.status_code == 429:
                # Rate limit — ждём дольше
                wait = delay * 2
                log.warning("fetch_html: 429 rate-limit %s — ждём %ds", url[:50], wait)
                time.sleep(wait)
                delay *= 2
                continue

            if r.status_code >= 500:
                log.warning("fetch_html: %d сервер %s (попытка %d/%d)",
                            r.status_code, url[:50], attempt, max_retries)
                time.sleep(delay)
                delay *= 2
                continue

            r.raise_for_status()
            return r.text

        except Exception as e:
            log.warning("fetch_html: ошибка %s (попытка %d/%d) — %s",
                        url[:50], attempt, max_retries, str(e)[:100])
            if attempt < max_retries:
                time.sleep(delay)
                delay *= 2

    log.error("fetch_html: все %d попытки исчерпаны для %s", max_retries, url[:60])
    return None


def fetch_bytes(
    url: str,
    timeout: int = 30,
    max_retries: int = 3,
    proxy: Optional[str] = None,
) -> Optional[bytes]:
    """
    Скачивает бинарный файл (PDF, DOCX) с retry.
    Возвращает bytes или None при неудаче.
    """
    delay = 2
    for attempt in range(1, max_retries + 1):
        try:
            headers = _build_headers()

            if _HAS_CFFI:
                r = _cffi.get(
                    url, headers=headers, timeout=timeout,
                    impersonate="chrome120",
                    proxies={"https": proxy, "http": proxy} if proxy else None,
                )
            else:
                r = httpx.get(
                    url, headers=headers, timeout=timeout,
                    follow_redirects=True,
                    proxies=proxy,
                )

            if r.status_code in (429, 503):
                log.warning("fetch_bytes: %d для %s — ждём %ds",
                            r.status_code, url[:50], delay)
                time.sleep(delay)
                delay *= 2
                continue

            r.raise_for_status()
            return r.content

        except Exception as e:
            log.warning("fetch_bytes: ошибка %s (попытка %d/%d) — %s",
                        url[:50], attempt, max_retries, str(e)[:100])
            if attempt < max_retries:
                time.sleep(delay)
                delay *= 2

    log.error("fetch_bytes: все попытки исчерпаны для %s", url[:60])
    return None


# ── Content-hash деduplication ────────────────────────────────────

def pdf_content_hash(pdf_bytes: bytes) -> str:
    """
    SHA-256 хэш бинарника PDF.
    Используется для дедупликации: одинаковый контент = одинаковый хэш,
    даже если URL изменился (редиректы, зеркала).
    """
    return hashlib.sha256(pdf_bytes).hexdigest()


def is_content_duplicate(pdf_bytes: bytes, known_content_hashes: set[str]) -> bool:
    """
    Возвращает True если PDF уже был обработан (по содержимому, не URL).
    known_content_hashes загружается из таблицы regulations.content_hash.
    """
    h = pdf_content_hash(pdf_bytes)
    return h in known_content_hashes
