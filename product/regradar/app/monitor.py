"""
Multi-source monitoring orchestrator — v4.

monitor_all_sources() runs the full pipeline over every enabled source
in sources.json.  One failed source never stops the rest.

Return contract
---------------
Each item in the returned list is either:

  success:
    run_pipeline_for_source() result dict with an extra "status" = "ok" key.

  error:
    {
        "source_name":  str,
        "url":          str,
        "jurisdiction": str,
        "category":     str,
        "changed":      False,
        "status":       "error",
        "error":        str,    human-readable error message
    }
"""

import logging

from app.config import AI_MAX_CALLS_PER_RUN
from app.pipeline import reset_ai_call_counter, run_pipeline_for_source
from app.sources import get_enabled_sources

logger = logging.getLogger(__name__)


def monitor_all_sources(
    verbose: bool = False,
) -> list[dict]:
    """
    Run the change-detection pipeline over all enabled sources.

    Parameters
    ----------
    verbose : bool
        When True, print a short progress line to stdout before and after
        each source.  Useful for the CLI ``all`` command.

    Returns
    -------
    list[dict]
        One result dict per source, in the order they appear in sources.json.
    """
    sources = get_enabled_sources()
    total   = len(sources)
    reset_ai_call_counter(AI_MAX_CALLS_PER_RUN)

    if total == 0:
        logger.warning("No enabled sources found in sources.json")
        if verbose:
            print("  No enabled sources found in sources.json")
        return []

    results: list[dict] = []

    for idx, source in enumerate(sources, 1):
        name = source.get("name", source["url"])
        jur  = source.get("jurisdiction", "")

        if verbose:
            label = f"{name}  ({jur})" if jur else name
            print(f"  [{idx}/{total}] {label} ...", flush=True)

        logger.info(
            "Monitoring [%d/%d]: %s — %s", idx, total, name, source["url"]
        )

        try:
            result = run_pipeline_for_source(source)
            results.append(result)

            if verbose:
                changed   = result.get("changed", False)
                is_new    = result.get("is_new",  False)
                risk      = result.get("risk_level", "LOW") if changed else ""
                if not changed:
                    status_str = "✓  unchanged"
                elif is_new:
                    status_str = f"★  baseline stored  [{risk}]"
                else:
                    added = result.get("added_count", 0)
                    rem   = result.get("removed_count", 0)
                    status_str = (
                        f"⚡  changed  [{risk}]  "
                        f"+{added} added  -{rem} removed"
                    )
                print(f"       → {status_str}")

            logger.info(
                "Done [%d/%d]: %s  changed=%s risk=%s",
                idx, total, name,
                result.get("changed"), result.get("risk_level", "—"),
            )

        except KeyboardInterrupt:
            # Let KeyboardInterrupt propagate so the CLI can handle it cleanly
            raise

        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"
            logger.error(
                "Error [%d/%d]: %s — %s", idx, total, name, error_msg
            )
            if verbose:
                print(f"       → ✗  error: {error_msg}")

            results.append({
                "source_name":   name,
                "url":           source.get("url", ""),
                "jurisdiction":  source.get("jurisdiction", ""),
                "category":      source.get("category", ""),
                "source_status": source.get("status", "active"),
                "changed":       False,
                "status":        "error",
                "error":         error_msg,
            })

    return results
