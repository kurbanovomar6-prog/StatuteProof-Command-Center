from abc import ABC, abstractmethod


class AbstractScraper(ABC):
    @abstractmethod
    def fetch_page(self, url: str) -> str: ...

    @abstractmethod
    def fetch_pdf_bytes(self, url: str) -> bytes: ...

    @abstractmethod
    def extract_pdf_links(self, url: str, link_pattern: str = ".pdf") -> list[str]: ...
