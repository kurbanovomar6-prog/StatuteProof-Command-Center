"""Reproducible measurement for the HEALTH-HONESTY axis.

The question this answers: when a surface says a source is healthy, how old is the
check behind that word?

    python3 tools/measure_health_axis.py            # human summary
    python3 tools/measure_health_axis.py --json     # machine-readable

Two things are measured separately on purpose:

  * what the REGISTRY asserts (``last_monitor_status`` / ``last_checked_at`` in
    sources.json) — these are the fields the founder and the API read;
  * what the RUN TRAIL proves (data/source_runs/source_runs.jsonl) — the only
    record of a check that actually happened.

When those disagree, the registry is asserting a health it cannot support, and the
gap between them is the number this axis has to move.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SOURCES = ROOT / "sources.json"
TRAIL = ROOT / "data" / "source_runs" / "source_runs.jsonl"
FRESH_DAYS = 7


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(value) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        try:
            parsed = datetime.fromisoformat(text[:10])
        except ValueError:
            return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _age_days(value, now: datetime) -> float | None:
    parsed = _parse_iso(value)
    return None if parsed is None else (now - parsed).total_seconds() / 86400.0


def _alert_rows(rows: list[dict]) -> list[dict]:
    return [
        r for r in rows
        if r.get("enabled")
        and r.get("monitoring_mode") == "fresh_alert"
        and r.get("alert_eligible") is True
    ]


def _last_run_stamps() -> dict[str, datetime]:
    """Newest observed run TIMESTAMP per source id, straight from the trail.

    Timestamps rather than ages, because the surface check below has to feed the
    real check_freshness() the same kind of value the API feeds it.
    """
    newest: dict[str, datetime] = {}
    if not TRAIL.exists():
        return {}
    with TRAIL.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except (ValueError, TypeError):
                continue
            sid = str(record.get("source_id") or "").strip()
            if not sid:
                continue
            stamp = _parse_iso(record.get("checked_at_utc") or record.get("run_at"))
            if stamp is None:
                continue
            if sid not in newest or stamp > newest[sid]:
                newest[sid] = stamp
    return newest


def _surface_lies_about_staleness() -> int:
    """Rows the /api/sources/status route would present as healthy while its own
    freshness field says otherwise.

    Exercises the handler, not a formula about it. Any row whose presented
    status reads healthy while freshness is STALE / NEVER_RUN / UNKNOWN is a
    row a customer would read as live coverage without a recent check behind it.
    """
    from io import BytesIO
    from unittest.mock import MagicMock

    try:
        import app.api as api
        from app.api import _Handler
    except Exception:  # noqa: BLE001 — probe reports, never raises
        return -1

    handler = _Handler.__new__(_Handler)
    handler.command = "GET"
    handler.path = "/api/sources/status"
    handler.request = MagicMock()
    handler.client_address = ("127.0.0.1", 9999)
    handler.server = MagicMock()
    handler.rfile = BytesIO(b"")
    handler.wfile = BytesIO()
    handler.close_connection = False
    headers = MagicMock()
    headers.get = lambda key, default="": {"Content-Length": "0"}.get(key, default)
    handler.headers = headers
    sent: list = []
    handler._send_json = lambda data, status=200, **kw: sent.append(data)

    # api_sources binds require_auth at import time, so patching app.api alone
    # leaves the handler using the original and the probe silently gets a 401 —
    # zero rows, which then reads as "nothing lies". Patch both names.
    import app.api_sources as api_sources

    originals = (api.require_auth, api_sources.require_auth)
    stub = lambda _h: {"id": 1, "email": "probe@example.com"}  # noqa: E731
    api.require_auth = stub
    api_sources.require_auth = stub
    try:
        handler.do_GET()
    except Exception:  # noqa: BLE001
        return -1
    finally:
        api.require_auth, api_sources.require_auth = originals

    if not sent:
        return -1
    rows = (sent[-1] or {}).get("sources") or []
    # No rows means the probe learned nothing. Returning 0 there would be the
    # same fake green this rewrite exists to remove.
    if not rows:
        return -1
    # Not a vocabulary of "healthy" words — the registry uses its own strings
    # and a new one would slip past a fixed list. The rule is simply that a row
    # whose freshness cannot back it must SAY so in the status a customer reads.
    stale_states = {"STALE", "NEVER_RUN", "UNKNOWN"}
    lying = 0
    for row in rows:
        freshness = str(row.get("freshness") or "").upper()
        presented = str(row.get("status") or "").upper()
        if freshness in stale_states and presented not in stale_states:
            lying += 1
    return lying


def measure() -> dict:
    now = _now()
    payload = json.loads(SOURCES.read_text(encoding="utf-8"))
    rows = payload["sources"] if isinstance(payload, dict) else payload
    alerting = _alert_rows(rows)
    trail_stamps = _last_run_stamps()
    trail_ages = {sid: (now - stamp).total_seconds() / 86400.0 for sid, stamp in trail_stamps.items()}

    claimed_ok = 0
    registry_ages: list[float] = []
    no_registry_date = 0
    proven_fresh = 0
    proven_stale = 0
    never_run = 0
    ok_but_unproven: list[str] = []

    for row in alerting:
        sid = str(row.get("id") or row.get("source_id") or "")
        status = str(row.get("last_monitor_status") or "")
        if status == "MONITOR_OK":
            claimed_ok += 1

        registry_age = _age_days(row.get("last_checked_at"), now)
        if registry_age is None:
            no_registry_date += 1
        else:
            registry_ages.append(registry_age)

        trail_age = trail_ages.get(sid)
        if trail_age is None:
            never_run += 1
        elif trail_age <= FRESH_DAYS:
            proven_fresh += 1
        else:
            proven_stale += 1

        # The finding that matters: asserts health, cannot prove a recent check.
        if status == "MONITOR_OK" and (trail_age is None or trail_age > FRESH_DAYS):
            ok_but_unproven.append(sid)

    registry_ages.sort()
    median = registry_ages[len(registry_ages) // 2] if registry_ages else None

    # What the CUSTOMER-FACING surface would say, which is the number this axis is
    # actually about. The registry stays stale by design — monitoring runs do not
    # write to it — so the fix was to derive freshness from the trail at read time.
    # Measuring the registry alone would therefore show no improvement even after
    # the surface stopped lying, which is exactly the kind of number that flatters
    # or slanders a change without describing it.
    # DRIVE THE REAL ROUTE. The previous version compared check_freshness(stamp)
    # against an age derived from that same stamp with the same parser, so the
    # condition was unsatisfiable by construction and printed 0 no matter what
    # any endpoint did. Reverting the freshness override in app/api_sources.py —
    # the exact regression this axis exists to catch — would not have moved it.
    surface_healthy_without_recent_check = _surface_lies_about_staleness()

    return {
        "measured_at": now.isoformat(),
        "surface_healthy_without_recent_check": surface_healthy_without_recent_check,
        "alert_eligible": len(alerting),
        "registry_claims_monitor_ok": claimed_ok,
        "registry_status_breakdown": dict(
            Counter(str(r.get("last_monitor_status") or "(none)") for r in alerting)
        ),
        "registry_last_checked_missing": no_registry_date,
        "registry_median_age_days": round(median, 1) if median is not None else None,
        "trail_proven_fresh_within_7d": proven_fresh,
        "trail_proven_stale_over_7d": proven_stale,
        "trail_never_run": never_run,
        "claims_ok_but_no_recent_run": len(ok_but_unproven),
        "claims_ok_but_no_recent_run_ids": sorted(ok_but_unproven)[:10],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = measure()

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    print(f"alert-eligible sources: {report['alert_eligible']}")
    print(f"  registry says MONITOR_OK:            {report['registry_claims_monitor_ok']}")
    print(f"  registry last_checked_at missing:    {report['registry_last_checked_missing']}")
    print(f"  registry median check age (days):    {report['registry_median_age_days']}")
    print("proven by the run trail:")
    print(f"  checked within {FRESH_DAYS}d:                   {report['trail_proven_fresh_within_7d']}")
    print(f"  last check older than {FRESH_DAYS}d:            {report['trail_proven_stale_over_7d']}")
    print(f"  no run in the trail at all:          {report['trail_never_run']}")
    print(f"\n>> registry asserts MONITOR_OK with no recent run: {report['claims_ok_but_no_recent_run']}")
    for sid in report["claims_ok_but_no_recent_run_ids"]:
        print(f"      {sid}")
    print(
        "\n>> what the CUSTOMER SURFACE would show as healthy without a recent "
        f"check: {report['surface_healthy_without_recent_check']}"
    )
    print(
        "   (this is the number the axis moves. The registry fields above stay "
        "stale by design — monitoring runs write to the activation queue, not to "
        "sources.json — so freshness is derived from the run trail at read time.)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
