"""
Federal Register (federalregister.gov) JSON API adapter.

Strategy
--------
The Federal Register exposes a public, unauthenticated JSON API.
The pipeline fetches the configured URL as plain text and passes that
raw JSON string to run().

1. Parse the raw JSON text received as the `html` argument.
2. Extract the `results` array.
3. For each result pull: document_number, title, publication_date,
   document_type, html_url.
4. Filter to documents published within the last 90 days.
5. CRITICAL — sort by document_number (a stable, immutable identifier
   assigned at publication).  Sorting by date or title is unstable
   because results order and title text can change across API calls.
6. Return one line per document:
   "{document_number}: {title} ({document_type})"

The default source URL is:
  https://www.federalregister.gov/api/v1/documents.json
    ?conditions[agencies][]=financial-crimes-enforcement-network
    &conditions[type][]=RULE
    &per_page=20
    &order=newest

Operators may configure any federalregister.gov API URL in sources.json;
can_handle() accepts the full domain.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

import requests

from app.adapters.base import SourceAdapter
from app.config import HTTP_TIMEOUT_S, REQUESTS_UA

logger = logging.getLogger(__name__)

_CUTOFF_DAYS = 90
_MAX_RESULTS = 100   # guard against unexpectedly large payloads


class FederalRegisterAdapter(SourceAdapter):
    """Source adapter for federalregister.gov — JSON API, document_number sorted."""

    name = "federal_register"

    def can_handle(self, url: str, source: dict | None = None) -> bool:
        return "federalregister.gov" in url

    def fetch_content(self, url: str, source: dict | None = None) -> str | None:
        """
        Fetch the Federal Register JSON API and return sorted, stable text.

        The pipeline may call this with the raw JSON string already fetched
        (passed as the `html` positional argument in run()) or it may call
        fetch_content() directly with the source URL.  Both paths are handled:
        this method always re-fetches from the URL to guarantee freshness.

        Returns None when the API cannot be reached or yields no usable results.
        Never raises.
        """
        try:
            resp = requests.get(
                url,
                headers={
                    "User-Agent": REQUESTS_UA,
                    "Accept":     "application/json",
                },
                timeout=HTTP_TIMEOUT_S,
                allow_redirects=True,
            )
        except Exception as exc:
            logger.warning("Federal Register fetch error for %s: %s", url, exc)
            return None

        if resp.status_code != 200:
            logger.warning(
                "Federal Register: HTTP %d for %s", resp.status_code, url
            )
            return None

        return self._parse_json_text(resp.text, url)

    def run(self, html: str, url: str, source: dict | None = None) -> str | None:
        """
        Entry point called by the pipeline with pre-fetched text.

        `html` is the raw API response body (JSON text).  Delegates directly
        to the JSON parser so no redundant network call is made when the
        pipeline has already fetched the content.
        """
        if html and html.strip().startswith("{"):
            return self._parse_json_text(html, url)
        # If the pipeline passed something other than JSON, fetch fresh.
        return self.fetch_content(url, source)

    # ── private helpers ───────────────────────────────────────────────────────

    def _parse_json_text(self, text: str, url: str) -> str | None:
        """Parse the JSON response text and return formatted output or None."""
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.warning(
                "Federal Register JSON parse error for %s: %s", url, exc
            )
            return None

        if not isinstance(data, dict):
            logger.warning("Federal Register: unexpected top-level JSON type for %s", url)
            return None

        results = data.get("results")
        if not isinstance(results, list):
            logger.warning(
                "Federal Register: no 'results' array in response for %s", url
            )
            return None

        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=_CUTOFF_DAYS)

        kept: list[dict] = []
        for doc in results[:_MAX_RESULTS]:
            if not isinstance(doc, dict):
                continue

            pub_date_str = doc.get("publication_date", "")
            if pub_date_str:
                try:
                    # Federal Register dates are "YYYY-MM-DD"
                    pub_dt = datetime.strptime(pub_date_str, "%Y-%m-%d").replace(
                        tzinfo=timezone.utc
                    )
                    if pub_dt < cutoff:
                        continue
                except ValueError:
                    # Unparseable date — include the document to avoid silent drops
                    logger.debug(
                        "Federal Register: cannot parse publication_date %r, including doc",
                        pub_date_str,
                    )

            doc_number = (doc.get("document_number") or "").strip()
            if not doc_number:
                continue

            kept.append(doc)

        if not kept:
            logger.info(
                "Federal Register: no documents within last %d days for %s",
                _CUTOFF_DAYS, url,
            )
            return None

        # Sort by document_number — stable identifier, never changes after publication.
        kept.sort(key=lambda d: d.get("document_number", ""))

        lines: list[str] = []
        for doc in kept:
            doc_number   = (doc.get("document_number")   or "").strip()
            title        = (doc.get("title")              or "").strip()
            doc_type     = (doc.get("document_type")      or "").strip()

            line = doc_number
            if title:
                line += f": {title}"
            if doc_type:
                line += f" ({doc_type})"
            lines.append(line)

        combined = "\n".join(lines)
        logger.info(
            "Federal Register adapter: %d chars from %d documents (out of %d results)",
            len(combined), len(kept), len(results),
        )
        return combined
