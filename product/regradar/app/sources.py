"""
Source configuration loader — v4.

Loads regulatory monitoring targets from sources.json.
Invalid or malformed entries are skipped with a warning — the rest
of the program continues normally.

Public API
----------
load_sources(path)     → list of all source dicts (valid entries only)
get_enabled_sources()  → filtered to enabled=True
validate_source(src)   → True if the dict has all required keys
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# sources.json lives next to run.py, one level above this file
_DEFAULT_PATH = Path(__file__).parent.parent / "sources.json"

_REQUIRED_KEYS  = {"name", "url", "jurisdiction", "category", "enabled"}
_VALID_STATUSES = {
    "active",
    "limited",
    "disabled",
    "mapped",
    "disabled_external_access",   # geo-block / JS SPA zero-extraction / protocol error
    "disabled_navigation_only",   # SPA returns identical navigation/menu text only
    "adapter_required",           # loads but needs custom adapter for reliable extraction
    # Extended statuses used by source management tooling
    "candidate",                  # under evaluation, not yet activated
    "remediation",                # temporarily disabled pending fix
    "duplicate_url",              # URL is already covered by another active source
    "replaced",                   # superseded by a different source record
}


# ── validation ────────────────────────────────────────────────────────────────

def validate_source(source: dict) -> bool:
    """
    Return True when `source` contains all required keys with non-empty values.

    Logs a warning for each missing or empty field.  Does not raise.
    """
    if not isinstance(source, dict):
        logger.warning("Source entry is not a dict: %r", source)
        return False

    missing = _REQUIRED_KEYS - source.keys()
    if missing:
        logger.warning(
            "Source %r missing required keys: %s",
            source.get("name", "<unnamed>"),
            ", ".join(sorted(missing)),
        )
        return False

    # url and name must be non-empty strings
    for key in ("name", "url"):
        if not isinstance(source[key], str) or not source[key].strip():
            logger.warning(
                "Source %r has blank or non-string '%s'",
                source.get("name", "<unnamed>"), key,
            )
            return False

    # url must look like an HTTP address
    if not source["url"].startswith(("http://", "https://")):
        logger.warning(
            "Source %r has invalid URL (must start with http/https): %s",
            source.get("name"), source["url"],
        )
        return False

    # enabled must be a boolean
    if not isinstance(source["enabled"], bool):
        logger.warning(
            "Source %r: 'enabled' must be true or false, got %r",
            source.get("name"), source["enabled"],
        )
        return False

    # status is optional; if present must be a recognised value
    status = source.get("status")
    if status is not None and status not in _VALID_STATUSES:
        logger.warning(
            "Source %r has invalid 'status' %r (must be one of: %s)",
            source.get("name"), status, ", ".join(sorted(_VALID_STATUSES)),
        )
        return False

    return True


# ── loader ────────────────────────────────────────────────────────────────────

def load_sources(path: str | Path = _DEFAULT_PATH) -> list[dict]:
    """
    Parse sources.json and return a list of validated source dicts.

    Invalid entries are skipped and logged.  Returns an empty list when the
    file is missing or contains malformed JSON — never raises.

    Parameters
    ----------
    path : str | Path
        Path to the JSON file.  Defaults to ``sources.json`` in the project
        root (one level above this module).

    Returns
    -------
    list[dict]
        Valid source entries, in file order.
    """
    fpath = Path(path)

    if not fpath.exists():
        logger.warning("sources.json not found at %s — no sources loaded", fpath)
        return []

    try:
        raw = fpath.read_text(encoding="utf-8")
        entries = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("sources.json is not valid JSON: %s", exc)
        return []
    except OSError as exc:
        logger.error("Cannot read sources.json: %s", exc)
        return []

    if not isinstance(entries, list):
        logger.error("sources.json must be a JSON array at the top level")
        return []

    valid: list[dict] = []
    for i, entry in enumerate(entries):
        if validate_source(entry):
            valid.append(entry)
        else:
            logger.warning("Skipping source at index %d (validation failed)", i)

    logger.info("Loaded %d/%d valid sources from %s", len(valid), len(entries), fpath)
    return valid


def get_enabled_sources(path: str | Path = _DEFAULT_PATH) -> list[dict]:
    """
    Return only the enabled sources from sources.json.

    Parameters
    ----------
    path : str | Path
        Passed through to ``load_sources()``.

    Returns
    -------
    list[dict]
        Validated sources where enabled=True.
    """
    all_sources = load_sources(path)
    enabled     = [s for s in all_sources if s["enabled"]]
    logger.info(
        "%d/%d sources enabled", len(enabled), len(all_sources)
    )
    return enabled
