import hashlib
import logging
from pathlib import Path
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.core.ports.scraper import AbstractScraper

log = logging.getLogger(__name__)
_CACHE_DIR = Path(".cache/pdfs")
_CACHE_DIR.mkdir(parents=True, exist_ok=True)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


class StaticScraper(AbstractScraper):
    def __init__(self, timeout: int = 30):
        self._client = httpx.Client(headers=_HEADERS, timeout=timeout, follow_redirects=True)

    def fetch_page(self, url: str) -> str:
        resp = self._client.get(url)
        resp.raise_for_status()
        return resp.text

    def fetch_pdf_bytes(self, url: str) -> bytes:
        digest = hashlib.sha256(url.encode()).hexdigest()[:16]
        cache_path = _CACHE_DIR / f"{digest}.pdf"
        if cache_path.exists():
            log.debug("PDF cache hit: %s", url)
            return cache_path.read_bytes()
        resp = self._client.get(url)
        resp.raise_for_status()
        data = resp.content
        cache_path.write_bytes(data)
        return data

    def extract_pdf_links(self, url: str, link_pattern: str = ".pdf") -> list[str]:
        html = self.fetch_page(url)
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for tag in soup.find_all("a", href=True):
            href = tag["href"]
            if link_pattern.lower() in href.lower():
                links.append(urljoin(url, href))
        return links
