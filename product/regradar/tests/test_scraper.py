from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.scraper import fetch_page_with_config


class _FakeElement:
    def inner_html(self) -> str:
        return "<main>" + ("Regulatory circular content. " * 40) + "</main>"


class _FakePage:
    def __init__(self) -> None:
        self.content_calls = 0
        self.wait_calls = 0

    def goto(self, *args, **kwargs) -> None:
        return None

    def wait_for_timeout(self, *_args, **_kwargs) -> None:
        self.wait_calls += 1

    def wait_for_selector(self, *_args, **_kwargs) -> None:
        return None

    def query_selector(self, selector: str):
        return _FakeElement() if selector == "main" else None

    def content(self) -> str:
        self.content_calls += 1
        if self.content_calls == 1:
            raise RuntimeError("Page.content: Unable to retrieve content because the page is navigating and changing the content.")
        return "<html><body><main>" + ("Regulatory circular content. " * 40) + "</main></body></html>"


class _FakeContext:
    def __init__(self, page: _FakePage) -> None:
        self.page = page

    def new_page(self) -> _FakePage:
        return self.page

    def close(self) -> None:
        return None


class _FakeBrowser:
    def __init__(self, page: _FakePage) -> None:
        self.page = page

    def new_context(self, **_kwargs) -> _FakeContext:
        return _FakeContext(self.page)


def test_fetch_page_with_config_retries_page_content_when_dom_is_still_navigating():
    page = _FakePage()

    with patch("app.scraper._get_shared_browser", return_value=_FakeBrowser(page)):
        html = fetch_page_with_config(
            "https://www.sca.gov.ae/en/regulations/regulations-listing",
            force_playwright=True,
        )

    assert "Regulatory circular content" in html
    assert page.content_calls == 2
    assert page.wait_calls >= 1
