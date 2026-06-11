"""
Adapter registry — v4.2.

get_adapter_for_url() scans the registered adapters in order and returns
the first one whose can_handle() returns True.  Returns None when no
adapter matches — the pipeline then uses the generic scraper.

Adapters are instantiated once at module level (singletons) so they can
cache expensive one-time setup if needed in future.
"""

import logging

from app.adapters.base import SourceAdapter
from app.adapters.cbr import CBRAdapter
from app.adapters.minfin import MinfinAdapter
from app.adapters.rosfinmonitoring import RosfinmonitoringAdapter

logger = logging.getLogger(__name__)

_ADAPTERS: list[SourceAdapter] = [
    CBRAdapter(),
    MinfinAdapter(),
    RosfinmonitoringAdapter(),
]


def get_adapter_for_url(
    url: str,
    source: dict | None = None,
) -> SourceAdapter | None:
    """
    Return the first registered adapter that can handle `url`, or None.

    Parameters
    ----------
    url : str
        The URL being processed by the pipeline.
    source : dict | None
        The full source entry from sources.json (may be None when called
        from run_pipeline without source context).

    Returns
    -------
    SourceAdapter | None
    """
    for adapter in _ADAPTERS:
        try:
            if adapter.can_handle(url, source):
                logger.debug("Adapter %r matched for %s", adapter.name, url)
                return adapter
        except Exception as exc:
            logger.warning(
                "Adapter %r raised in can_handle: %s: %s",
                adapter.name, type(exc).__name__, exc,
            )
    return None
