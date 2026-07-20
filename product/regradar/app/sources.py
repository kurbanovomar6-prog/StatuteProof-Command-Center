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
import os
from datetime import datetime, timezone
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
    # Disabled-reason statuses present in sources.json — these remain
    # non-eligible for monitoring but must load (not be dropped) so the
    # catalogue stays complete and the loader does not log-spam.
    "disabled_covered_by_hub",    # coverage provided by an aggregating hub source
    "disabled_duplicate",         # duplicate of another catalogue entry
    "disabled_geo_blocked",       # disabled: source geo-restricts access
    "disabled_needs_playwright",  # disabled: requires headless browser rendering
    "disabled_non_uae",           # disabled: out of UAE monitoring scope
    "disabled_path_moved",        # disabled: source URL/path relocated
    "disabled_static_doc",        # disabled: static document, no change signal
    "disabled_static_pdf",        # disabled: static PDF, no change signal
    "geo_blocked",                # source geo-restricts access
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


def proxy_unblocked_remediation(source: dict | None) -> bool:
    """True iff this source sits in remediation ONLY because of a WAF/geo
    block that the owner-configured egress proxy lifts.

    Requires ALL of: monitoring_mode == "remediation", the explicit per-source
    proxy_remediation flag (set on the 25 rulebook.centralbank.ae entries —
    NEVER inferred from the host alone, so remediation sources with other
    causes, e.g. the dfsa.ae extraction remediations, do not silently flip),
    and proxy_for_url() returning a configured proxy for the source URL (env
    STATUTEPROOF_FETCH_PROXY set + host on the fixed allowlist). With the env
    unset this is always False, so behavior is exactly today's.
    """
    if not isinstance(source, dict):
        return False
    if str(source.get("monitoring_mode") or "") != "remediation":
        return False
    if source.get("proxy_remediation") is not True:
        return False
    from app.adapters.base import proxy_for_url  # lazy: keep the loader import-light

    return proxy_for_url(str(source.get("url") or "")) is not None


# Bounded tail read of source_runs.jsonl for the verified-count check — same
# window the monitor circuit breaker uses (≈ many full cycles at 139 sources).
_PROXY_VERIFY_SCAN_BYTES = 4 * 1024 * 1024

# A recorded run only evidences the CURRENT configuration if it is RECENT.
# Watch mode re-checks every enabled source once per WATCH_INTERVAL_MINUTES
# cycle, so a source that is genuinely reachable produces a fresh record every
# cycle; the 25 CBUAE entries, by contrast, still carry successful records from
# before the host began returning 403. Allow a few cycles of slack (retries,
# scheduler restarts, one missed tick) and then stop treating the record as
# evidence. Older than this = unverified = not counted.
_PROXY_VERIFY_MAX_AGE_CYCLES = 6


def proxy_remediation_verified(
    source: dict | None,
    *,
    runs_file: str | Path | None = None,
    status_map: dict[str, str] | None = None,
) -> bool:
    """Counting variant of proxy_unblocked_remediation() for customer-facing
    fresh-alert-eligible counts (api.py health, source_summary.py).

    Configuration alone (proxy env + allowlist) is NOT evidence. The published
    counting standard (web/src/data/sourceQualityAudit.ts, sourcePacks.js) says
    a blocked-host source is not counted as fresh-alert eligible until access
    is re-verified from production — so on top of the routing predicate, the
    MOST RECENT recorded run for the source URL must be BOTH a non-failure (not
    FAILED / QUALITY_DROP) AND recent enough to reflect the current
    configuration (_PROXY_VERIFY_MAX_AGE_CYCLES cycles; a stale pre-block
    success is not evidence). Until the first successful proxied fetch is
    observed — and again whenever the source goes back to failing — the source
    keeps counting as remediation. Temporary understatement is safe;
    overstatement is not. The pipeline SF-3 gate intentionally does NOT use
    this variant: an alert is self-evidencing — it can only fire on a
    successful, sealed fetch made in the same run.

    Callers that classify MANY sources in one request (api._handle_health,
    source_summary.build_sources_summary) must build the url -> status map ONCE
    with latest_run_status_map() and pass it as ``status_map``; otherwise every
    source re-reads and re-parses the trail tail.
    """
    if not proxy_unblocked_remediation(source):
        return False
    return _latest_recorded_run_ok(
        str((source or {}).get("url") or ""), runs_file, status_map=status_map
    )


def latest_run_status_map(runs_file: str | Path | None = None) -> dict[str, str]:
    """Return url -> NEWEST recorded run status from one byte-bounded tail read
    of the run trail (uppercased; missing status becomes ""). Both ``url`` and
    ``official_url`` of each record are keyed, matching the per-source lookup.
    A missing file or a read error yields an empty map — unverified, never
    counted. A record older than the freshness bound (or with a missing /
    unparseable timestamp) is mapped to "" — present but unverified — so a
    stale pre-block success can never count as evidence. Read the trail once
    per request and reuse this map."""
    statuses: dict[str, str] = {}
    now = datetime.now(timezone.utc)
    max_age = _proxy_verify_max_age_seconds()
    for record in _read_run_trail_tail(runs_file):
        status = str(record.get("change_status") or record.get("status") or "").upper()
        if not _record_is_recent(record, now=now, max_age=max_age):
            status = ""
        for key in ("url", "official_url"):
            value = record.get(key)
            if isinstance(value, str) and value:
                statuses[value] = status
    return statuses


def _proxy_verify_max_age_seconds() -> float:
    """Freshness bound for a run record, derived from the real cycle cadence
    (WATCH_INTERVAL_MINUTES) rather than a magic number."""
    from app.config import WATCH_INTERVAL_MINUTES  # lazy: keep the loader import-light

    interval = WATCH_INTERVAL_MINUTES if WATCH_INTERVAL_MINUTES > 0 else 60
    return _PROXY_VERIFY_MAX_AGE_CYCLES * interval * 60.0


def _record_is_recent(record: dict, *, now: datetime, max_age: float) -> bool:
    """True iff the record's own timestamp is within the freshness bound.
    Missing, non-string or unparseable timestamps count as NOT recent, and so
    do wildly future-dated ones (clock skew / tampering) — understating is
    safe, overstating is not."""
    raw = record.get("timestamp_utc") or record.get("run_at")
    if not isinstance(raw, str) or not raw.strip():
        return False
    try:
        stamp = datetime.fromisoformat(raw.strip().replace("Z", "+00:00"))
    except ValueError:
        return False
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return abs((now - stamp).total_seconds()) <= max_age


def _latest_recorded_run_ok(
    source_url: str,
    runs_file: str | Path | None = None,
    *,
    status_map: dict[str, str] | None = None,
) -> bool:
    """True iff the NEWEST run record for source_url in the trail tail is a
    RECENT non-failure. Missing file, no record for the URL in the window, a
    stale/undated record, or a read error all return False — unverified, never
    counted."""
    if not source_url:
        return False
    statuses = latest_run_status_map(runs_file) if status_map is None else status_map
    status = statuses.get(source_url)
    if status is None:
        return False
    return status not in ("", "FAILED", "QUALITY_DROP")


def _read_run_trail_tail(runs_file: str | Path | None = None) -> list[dict]:
    """Parsed run records from a byte-bounded tail read of the trail, oldest
    first (mirrors monitor._consecutive_failures: seek-tail, drop the partial
    first line). Missing file or read error yields an empty list."""
    try:
        if runs_file is None:
            from app.source_runs import source_run_path  # lazy: keep the loader import-light

            run_path = source_run_path()
        else:
            run_path = Path(runs_file)
        if not run_path.exists():
            return []
        with run_path.open("rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            start = max(0, size - _PROXY_VERIFY_SCAN_BYTES)
            fh.seek(start)
            blob = fh.read()
    except Exception as exc:
        logger.warning("proxy_remediation_verified: cannot read run trail: %s", exc)
        return []

    raw_lines = blob.decode("utf-8", errors="replace").splitlines()
    if start > 0 and raw_lines:
        # Seeked into the middle of a record — drop the partial first line.
        raw_lines = raw_lines[1:]

    records: list[dict] = []
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records
