"""
discovery.py — Резилентный стелс-движок обнаружения регуляторных документов.

Архитектура:
  ImpersonationRotator  — ротация TLS/JA3-фингерпринтов через curl_cffi
  CircuitBreaker        — автомат состояний CLOSED/OPEN/HALF_OPEN на каждый домен
  Экспоненциальный backoff с джиттером + автопереключение прокси при 429/5xx
  LAYOUT_DRIFT_DETECTED — обнаружение сдвига вёрстки + regex-fallback по <a href>

Стратегии обнаружения:
  STATIC      — прямой парсинг href на странице листинга
  FOLLOW_HTML — двухэтапный: листинг → страницы статей → PDF-ссылки
  JS_RENDER   — Playwright со стелс-патчами для JavaScript SPA (НБРБ, НБК)
  SITEMAP     — разбор sitemap.xml / sitemap_index.xml
  RSS         — feedparser (с STATIC-fallback при пустой ленте)
  AUTO        — каскадный перебор: STATIC → SITEMAP → JS_RENDER

Возвращает только НОВЫЕ URL (отсутствующие в БД по url_hash).
Все ошибки поглощаются и логируются — конвейер никогда не останавливается.
"""

import hashlib
import logging
import random
import re
import threading
import time
from enum import Enum, auto
from urllib.parse import urljoin, urlparse

from tenacity import (
    RetryError,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from bs4 import BeautifulSoup

# Пробуем curl_cffi — даёт браузерный TLS/JA3-фингерпринт, обходит Cloudflare/Imperva
try:
    from curl_cffi import requests as _cffi_requests
    _HAS_CFFI = True
except ImportError:
    _HAS_CFFI = False

log = logging.getLogger(__name__)

# ── Доверенные регуляторные домены ────────────────────────────────────────────
_TRUSTED_DOMAINS: set[str] = {
    "cbr.ru", "minfin.gov.ru", "minfin.ru",
    "nationalbank.kz", "cbar.az", "nbrb.by",
    "gov.kz", "lex.uz", "minfinuz.uz",
    "egov.kz", "pravo.by", "zakon.kz",
    "consultant.ru", "garant.ru",
    "normativ.uz", "regulation.gov.ru",
    "cbk.gov.kz", "finreg.kz",
    "afsa.gov.kz", "akorda.kz",
    "minbank.uz", "cbu.uz",
}

# ── Профили имперсонации curl_cffi: каждый создаёт уникальный TLS/JA3 отпечаток ─
_CFFI_PROFILES: list[str] = [
    "chrome110",
    "chrome107",
    "chrome104",
    "chrome101",
    "chrome100",
    "chrome99",
    "edge99",
    "edge101",
]

# ── Матрица User-Agent + Sec-Ch-Ua для не-cffi режима ─────────────────────────
_UA_MATRIX: list[dict] = [
    {
        "ua": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "ch_ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "ch_platform": '"Windows"',
    },
    {
        "ua": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        ),
        "ch_ua": '"Chromium";v="120", "Microsoft Edge";v="120", "Not)A;Brand";v="24"',
        "ch_platform": '"Windows"',
    },
    {
        "ua": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        ),
        "ch_ua": '"Chromium";v="123", "Google Chrome";v="123", "Not:A-Brand";v="99"',
        "ch_platform": '"macOS"',
    },
    {
        "ua": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        ),
        "ch_ua": '"Chromium";v="110", "Google Chrome";v="110", "Not=A?Brand";v="8"',
        "ch_platform": '"Windows"',
    },
    {
        "ua": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        ),
        "ch_ua": '"Chromium";v="121", "Google Chrome";v="121", "Not;A=Brand";v="99"',
        "ch_platform": '"Linux"',
    },
]

# ── Regex-фильтр для fallback при дрейфе вёрстки ──────────────────────────────
# Находит все якоря с документными расширениями включая query-параметры
_DOC_EXT_RE = re.compile(
    r"\.(pdf|docx?|xlsx?|rtf|zip|rar|7z|odt|pptx?)(\?[^\"'\s]*)?$",
    re.IGNORECASE,
)

# ── Пороги Circuit Breaker ─────────────────────────────────────────────────────
_CB_FAILURE_THRESHOLD = 4    # сбоев подряд до открытия автомата
_CB_COOLDOWN_SEC      = 120  # секунд cooldown перед переходом в HALF_OPEN


# ── Circuit Breaker: автомат состояний на уровне домена ───────────────────────

class _CBState(Enum):
    CLOSED    = auto()   # нормальная работа — запросы проходят
    OPEN      = auto()   # домен недоступен — все запросы блокируются
    HALF_OPEN = auto()   # cooldown истёк — проверяем одним пробным запросом


class _CircuitBreaker:
    """
    Потокобезопасный Circuit Breaker для одного домена.
    Переходы: CLOSED → OPEN (N сбоев) → HALF_OPEN (cooldown) → CLOSED (успех).
    """

    def __init__(self) -> None:
        self._lock     = threading.Lock()
        self.state     = _CBState.CLOSED
        self.failures  = 0
        self.opened_at = 0.0

    def allow_request(self) -> bool:
        """True — запрос разрешён, False — автомат открыт, запрос блокируется."""
        with self._lock:
            if self.state == _CBState.CLOSED:
                return True
            if self.state == _CBState.OPEN:
                # Проверяем истёк ли cooldown
                if time.monotonic() - self.opened_at >= _CB_COOLDOWN_SEC:
                    self.state = _CBState.HALF_OPEN
                    log.debug("circuit_breaker: → HALF_OPEN (cooldown истёк)")
                    return True
                return False
            # HALF_OPEN — пропускаем единственный пробный запрос
            return True

    def record_success(self) -> None:
        """Успешный ответ: сбрасываем счётчик сбоев, закрываем автомат."""
        with self._lock:
            if self.state != _CBState.CLOSED:
                log.info("circuit_breaker: → CLOSED (соединение восстановлено)")
            self.failures = 0
            self.state    = _CBState.CLOSED

    def record_failure(self, domain: str) -> None:
        """Сбой: инкрементируем счётчик, при превышении порога — открываем автомат."""
        with self._lock:
            self.failures += 1
            if self.state == _CBState.HALF_OPEN or self.failures >= _CB_FAILURE_THRESHOLD:
                self.state     = _CBState.OPEN
                self.opened_at = time.monotonic()
                log.error(
                    "circuit_breaker: → OPEN для '%s' (сбоев подряд: %d). "
                    "Запросы заблокированы на %d сек.",
                    domain, self.failures, _CB_COOLDOWN_SEC,
                )


# Глобальный реестр Circuit Breaker — по одному экземпляру на домен
_breakers:      dict[str, _CircuitBreaker] = {}
_breakers_lock: threading.Lock             = threading.Lock()


def _get_breaker(domain: str) -> _CircuitBreaker:
    """Возвращает (или лениво создаёт) Circuit Breaker для домена."""
    with _breakers_lock:
        if domain not in _breakers:
            _breakers[domain] = _CircuitBreaker()
        return _breakers[domain]


# ── Ротатор профилей имперсонации ─────────────────────────────────────────────

class _ImpersonationRotator:
    """Потокобезопасный круговой ротатор curl_cffi-профилей и UA-заголовков."""

    def __init__(self) -> None:
        self._lock     = threading.Lock()
        self._cffi_idx = 0
        self._ua_idx   = 0

    def next_cffi_profile(self) -> str:
        with self._lock:
            p = _CFFI_PROFILES[self._cffi_idx % len(_CFFI_PROFILES)]
            self._cffi_idx += 1
            return p

    def next_ua_entry(self) -> dict:
        with self._lock:
            e = _UA_MATRIX[self._ua_idx % len(_UA_MATRIX)]
            self._ua_idx += 1
            return e

    def build_stealth_headers(self, for_document: bool = False) -> dict:
        """
        Полный набор браузерных заголовков с ротацией Sec-Ch-Ua.
        for_document=True — добавляет Accept для PDF/бинарных файлов.
        """
        e = self.next_ua_entry()
        accept = (
            "application/pdf,application/octet-stream,*/*;q=0.8"
            if for_document
            else (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
            )
        )
        return {
            "User-Agent":                e["ua"],
            "Accept":                    accept,
            "Accept-Language":           "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding":           "gzip, deflate, br",
            "Cache-Control":             "max-age=0",
            "Sec-Ch-Ua":                 e["ch_ua"],
            "Sec-Ch-Ua-Mobile":          "?0",
            "Sec-Ch-Ua-Platform":        e["ch_platform"],
            "Sec-Fetch-Dest":            "document" if for_document else "document",
            "Sec-Fetch-Mode":            "navigate",
            "Sec-Fetch-Site":            "none",
            "Sec-Fetch-User":            "?1",
            "Upgrade-Insecure-Requests": "1",
            "Connection":                "keep-alive",
        }


# Синглтон ротатора — один объект на весь процесс
_rotator = _ImpersonationRotator()


# ── Вспомогательные функции ────────────────────────────────────────────────────

def _url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def _is_trusted(url: str) -> bool:
    """Проверяет принадлежность URL к списку доверенных регуляторных доменов."""
    try:
        domain = urlparse(url).netloc.lower().lstrip("www.")
        return any(domain == d or domain.endswith("." + d) for d in _TRUSTED_DOMAINS)
    except Exception:
        return False


def _domain_of(url: str) -> str:
    """Возвращает нормализованный netloc URL (без www-префикса)."""
    try:
        return urlparse(url).netloc.lower().lstrip("www.")
    except Exception:
        return ""


def _jitter(base: float) -> float:
    """Случайный джиттер ±25% — избегаем детерминированного паттерна запросов."""
    return base * (0.75 + random.random() * 0.5)


def _proxy_dict(proxy_url: str | None) -> dict | None:
    """Формирует словарь прокси для curl_cffi / httpx."""
    if not proxy_url:
        return None
    return {"https": proxy_url, "http": proxy_url}


# ── Пользовательские исключения для tenacity retry-цепочки ───────────────────

class _RateLimitError(Exception):
    """HTTP 429 / 503 — превышен лимит запросов на домене."""

class _ServerError(Exception):
    """HTTP 5xx — серверная ошибка регулятора."""


# ── Резилентный HTTP-клиент с Circuit Breaker + tenacity ─────────────────────

def _fetch_html(
    url: str,
    timeout: int = 20,
    max_retries: int = 3,
    proxy: str | None = None,
) -> str | None:
    """
    Загружает HTML с экспоненциальным backoff через tenacity, ротацией TLS-фингерпринтов
    и Circuit Breaker-защитой на уровне домена.

    Обработка статусов:
      429 — поднимает _RateLimitError → tenacity ждёт и повторяет
      5xx — поднимает _ServerError → tenacity ждёт и повторяет с backoff
      сеть — любое исключение → tenacity повторяет

    Возвращает None если Circuit Breaker открыт или все retry исчерпаны.
    """
    domain  = _domain_of(url)
    breaker = _get_breaker(domain)

    if not breaker.allow_request():
        log.warning("[CB-OPEN] Запрос заблокирован Circuit Breaker для домена '%s'", domain)
        return None

    @retry(
        stop=stop_after_attempt(max_retries),
        wait=wait_exponential_jitter(initial=2, max=60, jitter=3),
        retry=retry_if_exception_type(Exception),
        before_sleep=before_sleep_log(log, logging.WARNING),
    )
    def _attempt() -> str:
        headers = _rotator.build_stealth_headers(for_document=False)
        if _HAS_CFFI:
            profile = _rotator.next_cffi_profile()
            r = _cffi_requests.get(
                url,
                headers=headers,
                timeout=timeout,
                impersonate=profile,
                proxies=_proxy_dict(proxy),
                allow_redirects=True,
            )
        else:
            import httpx
            r = httpx.get(
                url,
                headers=headers,
                timeout=timeout,
                follow_redirects=True,
                **({"proxy": proxy} if proxy else {}),
            )

        if r.status_code == 429:
            breaker.record_failure(domain)
            raise _RateLimitError(f"429 Rate Limit [{url[:70]}]")

        if r.status_code >= 500:
            breaker.record_failure(domain)
            raise _ServerError(f"HTTP {r.status_code} [{url[:70]}]")

        r.raise_for_status()
        return r.text

    try:
        result = _attempt()
        breaker.record_success()
        return result
    except RetryError as exc:
        log.error(
            "fetch_html: все %d попытки исчерпаны для %s — %s",
            max_retries, url[:70], exc.last_attempt.exception(),
        )
        return None
    except Exception as exc:
        log.error("fetch_html: неперехваченная ошибка %s — %s", url[:70], exc)
        breaker.record_failure(domain)
        return None


def _fetch_bytes_resilient(
    url: str,
    timeout: int = 30,
    max_retries: int = 3,
    proxy: str | None = None,
) -> bytes | None:
    """
    Загружает бинарный файл (PDF, DOCX) с Circuit Breaker + tenacity retry.
    Возвращает bytes или None при неудаче.
    """
    domain  = _domain_of(url)
    breaker = _get_breaker(domain)

    if not breaker.allow_request():
        log.warning("[CB-OPEN] Бинарная загрузка заблокирована для домена '%s'", domain)
        return None

    @retry(
        stop=stop_after_attempt(max_retries),
        wait=wait_exponential_jitter(initial=2, max=60, jitter=3),
        retry=retry_if_exception_type(Exception),
        before_sleep=before_sleep_log(log, logging.WARNING),
    )
    def _attempt() -> bytes:
        headers = _rotator.build_stealth_headers(for_document=True)
        if _HAS_CFFI:
            profile = _rotator.next_cffi_profile()
            r = _cffi_requests.get(
                url,
                headers=headers,
                timeout=timeout,
                impersonate=profile,
                proxies=_proxy_dict(proxy),
                allow_redirects=True,
            )
        else:
            import httpx
            r = httpx.get(
                url,
                headers=headers,
                timeout=timeout,
                follow_redirects=True,
                **({"proxy": proxy} if proxy else {}),
            )

        if r.status_code in (429, 503):
            breaker.record_failure(domain)
            raise _RateLimitError(f"HTTP {r.status_code} binary fetch [{url[:70]}]")

        r.raise_for_status()
        return r.content

    try:
        result = _attempt()
        breaker.record_success()
        return result
    except RetryError as exc:
        log.error(
            "fetch_bytes: все %d попытки исчерпаны для %s — %s",
            max_retries, url[:70], exc.last_attempt.exception(),
        )
        return None
    except Exception as exc:
        log.error("fetch_bytes: неперехваченная ошибка %s — %s", url[:70], exc)
        breaker.record_failure(domain)
        return None


# ── Извлечение ссылок из HTML ──────────────────────────────────────────────────

def _extract_doc_links(html: str, base_url: str, pattern: str = ".pdf") -> list[str]:
    """Извлекает документные ссылки из HTML по строковому паттерну."""
    soup  = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        if pattern.lower() in href.lower():
            full = urljoin(base_url, href)
            if _is_trusted(full):
                links.append(full)
    return links


def _drift_fallback_links(html: str, base_url: str) -> list[str]:
    """
    Резервный алгоритм при обнаружении дрейфа вёрстки.

    Извлекает ВСЕ <a href> без учёта паттерна,
    фильтрует по регулярному выражению _DOC_EXT_RE (pdf/docx/xlsx/...),
    применяет фильтр доверенных доменов.

    Вызывается ТОЛЬКО после логирования LAYOUT_DRIFT_DETECTED.
    Предотвращает потерю данных при изменении CSS-структуры сайта.
    """
    soup  = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        full = urljoin(base_url, href)
        if _DOC_EXT_RE.search(href) and _is_trusted(full):
            links.append(full)
    return links


# ── Реализации стратегий обнаружения ─────────────────────────────────────────

def _strategy_static(
    base_url: str,
    link_pattern: str,
    proxy: str | None = None,
) -> list[str]:
    """
    STATIC — прямой парсинг href на странице листинга.

    При status 200 но 0 совпадений — срабатывает алгоритм обнаружения
    дрейфа вёрстки: логируется LAYOUT_DRIFT_DETECTED и запускается
    regex-fallback по всем якорным тегам страницы.
    """
    html = _fetch_html(base_url, proxy=proxy)
    if not html:
        return []

    links = _extract_doc_links(html, base_url, link_pattern)

    if not links:
        # Страница ответила 200 OK но совпадений по паттерну нет —
        # вёрстка регулятора, вероятно, изменилась
        log.critical(
            "[LAYOUT_DRIFT_DETECTED] %s → HTTP 200 OK, но 0 документных ссылок "
            "по паттерну '%s'. Запускаю regex-fallback по всем <a href>.",
            base_url[:80], link_pattern,
        )
        links = _drift_fallback_links(html, base_url)

        if links:
            log.warning(
                "[LAYOUT_DRIFT_DETECTED] Regex-fallback нашёл %d ссылок. "
                "Проверьте CSS-структуру страницы %s — возможно изменилась вёрстка.",
                len(links), base_url[:60],
            )
        else:
            log.error(
                "[LAYOUT_DRIFT_DETECTED] Regex-fallback также не нашёл документов на %s. "
                "Вероятна полная смена структуры или IP-блокировка.",
                base_url[:60],
            )

    return links


def _strategy_follow_html(
    base_url: str,
    article_pattern: str,
    pdf_pattern: str = ".pdf",
    max_articles: int = 15,
    proxy: str | None = None,
) -> list[str]:
    """
    FOLLOW_HTML — двухэтапный: страница листинга → статьи → PDF-ссылки.
    Используется для ЦБР (press/pr/), где каждый материал — отдельная HTML-страница.
    Между запросами к одному домену добавляется случайная задержка (антибот).
    """
    html = _fetch_html(base_url, proxy=proxy)
    if not html:
        return []

    soup       = BeautifulSoup(html, "html.parser")
    article_re = re.compile(article_pattern, re.IGNORECASE)
    seen_art:    set[str]  = set()
    article_urls: list[str] = []

    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        if article_re.search(href) and href not in seen_art:
            seen_art.add(href)
            article_urls.append(href)

    article_urls = article_urls[:max_articles]

    if not article_urls:
        log.warning(
            "[LAYOUT_DRIFT_DETECTED] follow_html: %s → 0 статей по паттерну '%s'",
            base_url[:70], article_pattern,
        )

    pdf_urls: list[str] = []
    for art_url in article_urls:
        # Случайная задержка между запросами — снижает риск блокировки
        time.sleep(_jitter(0.6))
        art_html = _fetch_html(art_url, proxy=proxy)
        if not art_html:
            continue
        found = _extract_doc_links(art_html, art_url, pdf_pattern)
        pdf_urls.extend(found)
        if found:
            log.debug("follow_html: %s → %d PDF", art_url[-60:], len(found))

    return pdf_urls


def _strategy_sitemap(
    base_url: str,
    pdf_pattern: str = ".pdf",
    proxy: str | None = None,
) -> list[str]:
    """
    SITEMAP — разбор sitemap.xml для получения прямых URL документов.
    Проверяет несколько стандартных путей sitemap.
    """
    parsed    = urlparse(base_url)
    root      = f"{parsed.scheme}://{parsed.netloc}"
    candidates = [
        "/sitemap.xml",
        "/sitemap_index.xml",
        "/sitemap/documents.xml",
        "/ru/sitemap.xml",
        "/en/sitemap.xml",
        "/sitemap-docs.xml",
    ]

    for sm_path in candidates:
        html = _fetch_html(root + sm_path, proxy=proxy)
        if not html:
            continue
        raw_urls = re.findall(r"<loc>(.*?)</loc>", html, re.DOTALL)
        pdfs = [
            u.strip() for u in raw_urls
            if pdf_pattern.lower() in u.lower() and _is_trusted(u.strip())
        ]
        if pdfs:
            log.info("sitemap %s: найдено %d документальных URL", sm_path, len(pdfs))
            return pdfs

    return []


def _strategy_rss(
    base_url: str,
    proxy: str | None = None,
) -> list[str]:
    """RSS — feedparser для сайтов с новостными лентами."""
    try:
        import feedparser
    except ImportError:
        log.warning("feedparser не установлен — RSS-стратегия недоступна")
        return []

    parsed     = urlparse(base_url)
    root       = f"{parsed.scheme}://{parsed.netloc}"
    feed_paths = [
        "/rss/", "/rss.xml", "/feed/", "/news.rss",
        "/press/rss/", "/ru/rss", "/en/rss",
        "/atom.xml", "/feed.xml", "/news/rss.xml",
    ]

    for feed_path in feed_paths:
        try:
            d = feedparser.parse(root + feed_path)
            if d.entries:
                links = [e.link for e in d.entries if e.get("link")]
                log.info("RSS %s%s: %d записей", root, feed_path, len(links))
                return links
        except Exception:
            continue

    return []


def _strategy_js_render(
    base_url: str,
    pdf_pattern: str = ".pdf",
) -> list[str]:
    """
    JS_RENDER — Playwright со стелс-патчами для JavaScript-рендеренных SPA.
    Применяется для НБРБ, НБК и других сайтов с динамической загрузкой контента.

    Стелс-меры:
      • JS-инъекция: скрываем navigator.webdriver, добавляем window.chrome
      • Рандомизированный viewport, локаль, временная зона
      • Ожидание networkidle перед извлечением контента
      • LAYOUT_DRIFT_DETECTED при нулевом результате с regex-fallback
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log.warning("playwright не установлен — JS_RENDER недоступен")
        return []

    # JavaScript-патч для сокрытия признаков автоматизации
    _STEALTH_JS = """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
                {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
                {name: 'Native Client', filename: 'internal-nacl-plugin'},
            ]
        });
        Object.defineProperty(navigator, 'languages', {
            get: () => ['ru-RU', 'ru', 'en-US', 'en']
        });
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {},
        };
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications'
                ? Promise.resolve({state: Notification.permission})
                : originalQuery(parameters)
        );
    """

    ua_entry = _rotator.next_ua_entry()
    links: list[str] = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--window-size=1366,768",
                ],
            )
            ctx = browser.new_context(
                user_agent=ua_entry["ua"],
                viewport={"width": 1366, "height": 768},
                locale="ru-RU",
                timezone_id="Europe/Moscow",
            )
            # Внедряем стелс-патч во все страницы контекста до загрузки
            ctx.add_init_script(_STEALTH_JS)
            page = ctx.new_page()
            page.set_extra_http_headers({
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.5",
                "Sec-Ch-Ua":       ua_entry["ch_ua"],
                "Sec-Ch-Ua-Mobile": "?0",
            })

            try:
                page.goto(base_url, timeout=25_000, wait_until="networkidle")
            except Exception:
                # networkidle не дождались — берём что загрузилось по DOMContentLoaded
                try:
                    page.goto(base_url, timeout=25_000, wait_until="domcontentloaded")
                    time.sleep(2.0)  # дополнительное ожидание динамического контента
                except Exception as goto_err:
                    log.warning("js_render: goto %s — %s", base_url[:60], goto_err)
                    browser.close()
                    return []

            html = page.content()
            browser.close()

        links = _extract_doc_links(html, base_url, pdf_pattern)

        # Дрейф вёрстки при JS-рендере — запускаем regex-fallback
        if not links:
            log.warning(
                "[LAYOUT_DRIFT_DETECTED] js_render %s → 0 документов по паттерну '%s'. "
                "Запускаю regex-fallback по всем <a href>.",
                base_url[:70], pdf_pattern,
            )
            links = _drift_fallback_links(html, base_url)

        log.info("js_render %s: %d документных ссылок", base_url[-60:], len(links))

    except Exception as exc:
        log.warning("js_render: критическая ошибка %s — %s", base_url[:60], exc)

    return links


# ── Публичный API ──────────────────────────────────────────────────────────────

def find_document_urls(
    base_url: str,
    link_pattern: str = ".pdf",
    strategy: str = "STATIC",
    known_hashes: set[str] | None = None,
    article_pattern: str = r"/press/pr/\d{4}-\d{2}-\d{2}",
    proxy: str | None = None,
) -> list[str]:
    """
    Главная точка входа движка обнаружения.
    Возвращает список НОВЫХ URL документов (не входящих в known_hashes).

    Параметры:
      base_url        — базовый URL регулятора
      link_pattern    — фрагмент URL документа ('.pdf', '/npa/', и т.д.)
      strategy        — стратегия: STATIC / FOLLOW_HTML / JS_RENDER / SITEMAP / RSS / AUTO
      known_hashes    — множество уже обработанных url_hash из БД
      article_pattern — regex для FOLLOW_HTML: паттерн ссылок на статьи-переходники
      proxy           — прокси-URL для geo-restricted доменов (например, cbr.ru)
    """
    known_hashes = known_hashes or set()
    raw: list[str] = []
    strategy       = strategy.upper().strip()

    if strategy == "STATIC":
        raw = _strategy_static(base_url, link_pattern, proxy=proxy)

    elif strategy == "FOLLOW_HTML":
        raw = _strategy_follow_html(
            base_url, article_pattern, link_pattern, proxy=proxy
        )

    elif strategy == "JS_RENDER":
        raw = _strategy_js_render(base_url, link_pattern)
        if not raw:
            # JS-рендер не дал результатов — пробуем статику как дополнительный fallback
            log.info("JS_RENDER пустой — статический fallback для %s", base_url[-50:])
            raw = _strategy_static(base_url, link_pattern, proxy=proxy)

    elif strategy == "SITEMAP":
        raw = _strategy_sitemap(base_url, link_pattern, proxy=proxy)
        if not raw:
            log.info("SITEMAP пустой — статический fallback для %s", base_url[-50:])
            raw = _strategy_static(base_url, link_pattern, proxy=proxy)

    elif strategy == "RSS":
        raw = _strategy_rss(base_url, proxy=proxy)
        if not raw:
            log.info("RSS пустой — статический fallback для %s", base_url[-50:])
            raw = _strategy_static(base_url, link_pattern, proxy=proxy)

    elif strategy == "AUTO":
        # Каскадный перебор: STATIC → SITEMAP → JS_RENDER
        raw = _strategy_static(base_url, link_pattern, proxy=proxy)
        if not raw:
            log.info("AUTO: статика пуста, пробуем sitemap для %s", base_url[-50:])
            raw = _strategy_sitemap(base_url, link_pattern, proxy=proxy)
        if not raw:
            log.info("AUTO: sitemap пуст, пробуем JS-рендер для %s", base_url[-50:])
            raw = _strategy_js_render(base_url, link_pattern)

    else:
        log.error(
            "discovery: неизвестная стратегия '%s' для %s — допустимо: "
            "STATIC / FOLLOW_HTML / JS_RENDER / SITEMAP / RSS / AUTO",
            strategy, base_url[:60],
        )
        return []

    # Дедупликация: оставляем только новые URL, отсутствующие в БД
    seen:     set[str]  = set()
    new_urls: list[str] = []
    for url in raw:
        h = _url_hash(url)
        if h in known_hashes or url in seen:
            continue
        seen.add(url)
        new_urls.append(url)

    log.info(
        "discovery[%s] %s: %d всего → %d новых",
        strategy, base_url[-50:], len(raw), len(new_urls),
    )
    return new_urls


def get_known_hashes_from_db() -> set[str]:
    """Загружает все url_hash из БД для исключения уже обработанных URL."""
    try:
        from app.infrastructure.db.session import engine
        from sqlalchemy import text
        with engine.connect() as c:
            rows = c.execute(text("SELECT url_hash FROM regulations")).fetchall()
        return {r[0] for r in rows}
    except Exception as exc:
        log.warning("get_known_hashes_from_db: %s", exc)
        return set()
