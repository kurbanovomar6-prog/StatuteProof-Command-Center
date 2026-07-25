"""Reproducible measurement for the ALERT RELEASE axis.

The question: **can a customer's approver release a held alert, or does every
release still require someone to SSH into production and run a CLI?**

    python3 tools/measure_alert_release_axis.py
    python3 tools/measure_alert_release_axis.py --json

An alert draft sits unreleased until ``app.alert_review.review_alert`` records an
approve_weekly / approve_urgent decision; only then does
``load_approved_alert_candidates`` include it. ``review_alert`` has other
callers — ``weekly_brief`` uses it to HOLD an alert the QA gate rejected —
so the probe asks specifically who can pass an approve_* action, which is
the only thing that releases anything.

Behavioural: it drives the real ``_Handler`` dispatch, so a handler that exists
but was never wired into ``do_POST`` measures as absent — which is what it is
from the browser's side.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Paths a reasonable frontend would call to release a held alert.
_RELEASE_PATHS = (
    "/api/alerts/review",
    "/api/alerts/approve",
    "/api/alerts/release",
    "/api/reviews/decide",
)
_QUEUE_PATHS = (
    "/api/alerts/review-queue",
    "/api/reviews/queue",
)


def _handler(method: str, path: str, body: dict | None = None):
    from app.api import _Handler

    raw = json.dumps(body or {}).encode("utf-8")
    header_map = {"Content-Length": str(len(raw)), "X-Real-IP": "10.0.0.9"}

    h = _Handler.__new__(_Handler)
    h.command = method
    h.path = path
    h.request = MagicMock()
    h.client_address = ("127.0.0.1", 9999)
    h.server = MagicMock()
    h.rfile = BytesIO(raw)
    h.wfile = BytesIO()
    h.close_connection = False
    hdrs = MagicMock()
    hdrs.get = lambda key, default="": header_map.get(key, default)
    h.headers = hdrs
    sent: list[tuple[dict, int]] = []
    h._send_json = lambda data, status=200, **kw: sent.append((data, status))
    h._send_bytes = lambda b, ct, status=200, extra_headers=None: sent.append(
        ({"bytes": len(b)}, status)
    )
    h._sent = sent
    return h


def _probe(method: str, path: str, body: dict | None = None) -> int | None:
    """404 = no such route. Anything else, including 401/403, means it exists."""
    h = _handler(method, path, body)
    try:
        h.do_POST() if method == "POST" else h.do_GET()
    except Exception:  # noqa: BLE001 — an exploding route still exists
        pass
    return h._sent[-1][1] if h._sent else None


def measure() -> dict:
    report: dict = {}

    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        import app.db as app_db

        app_db.DB_PATH = str(tmp / "release.db")

        release = {
            p: _probe("POST", p, {"alert_id": "draft-x", "action": "approve_weekly"})
            for p in _RELEASE_PATHS
        }
        queue = {p: _probe("GET", p) for p in _QUEUE_PATHS}

        report["release_routes"] = release
        report["queue_routes"] = queue
        report["can_release_over_http"] = any(
            s not in (404, None) for s in release.values()
        )
        report["can_see_the_queue_over_http"] = any(
            s not in (404, None) for s in queue.values()
        )

        # Who can reach review_alert at all? If the only caller is run.py, the
        # release path is SSH-only no matter what the UI shows.
        # Match the CALL, not the substring: a bare "review_alert" also appears
        # inside "alert_review" and inside compiled .pyc bytecode, which made an
        # earlier version of this report list fourteen phantom callers.
        import re

        call = re.compile(r"\breview_alert\s*\(")
        callers = sorted(
            path.name
            for path in [*(ROOT / "app").glob("*.py"), ROOT / "run.py"]
            if call.search(path.read_text(encoding="utf-8", errors="replace"))
        )
        report["modules_calling_review_alert"] = callers

        # Calling review_alert is not releasing: weekly_brief calls it with
        # action="manual_review" to HOLD an alert the QA gate rejected. Only an
        # approve_* action releases, so that is what gets counted.
        approves = sorted(
            path.name
            for path in [*(ROOT / "app").glob("*.py"), ROOT / "run.py"]
            if "approve_weekly" in path.read_text(encoding="utf-8", errors="replace")
            or "approve_urgent" in path.read_text(encoding="utf-8", errors="replace")
        )
        report["modules_naming_an_approve_action"] = approves
        report["approval_is_cli_only"] = "api.py" not in approves and "api_alerts.py" not in approves

    report["an_approver_can_release_without_a_shell"] = bool(
        report["can_release_over_http"]
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = measure()

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    print("HTTP door (404 = no such route; 401/403 = route exists, request refused)")
    for label, key in (("release", "release_routes"), ("queue", "queue_routes")):
        for path, status in report[key].items():
            print(f"  {label:8} {path:26} {status}")
    print()
    print(f"  can release over HTTP              {report['can_release_over_http']}")
    print(f"  can see the queue over HTTP        {report['can_see_the_queue_over_http']}")
    print()
    print(f"  modules calling review_alert       {report['modules_calling_review_alert']}")
    print(f"  modules naming an approve action   {report['modules_naming_an_approve_action']}")
    print(f"  approval is CLI-only               {report['approval_is_cli_only']}")
    print()
    print(
        ">> AN APPROVER CAN RELEASE WITHOUT A SHELL: "
        f"{report['an_approver_can_release_without_a_shell']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
