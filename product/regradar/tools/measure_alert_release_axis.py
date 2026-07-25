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
    "/api/admin/alert-review",
    "/api/alerts/review",
    "/api/alerts/approve",
    "/api/alerts/release",
    "/api/reviews/decide",
)
_QUEUE_PATHS = (
    "/api/admin/alert-review-queue",
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
        # Any HTTP-layer module counts, not a hardcoded filename list — an
        # earlier version named api.py/api_alerts.py and would have kept
        # reporting "CLI-only" after the endpoint landed in api_alert_review.py.
        report["approval_is_cli_only"] = not any(
            name.startswith("api") for name in approves
        )

        # ── end to end, as a logged-in founder ───────────────────────────
        # Route existence proves nothing. This drives the real dispatcher with a
        # real draft on disk and then reads the trail back.
        try:
            report.update(_end_to_end(tmp))
        except Exception as exc:  # noqa: BLE001 — the probe reports, never raises
            report["end_to_end_error"] = f"{type(exc).__name__}: {exc}"

    report["an_approver_can_release_without_a_shell"] = bool(
        report.get("can_release_over_http")
        and report.get("http_approve_status") == 200
        and report.get("trail_records_the_session_identity")
    )
    return report


def _write_draft(base: Path, alert_id: str, *, risky: bool) -> None:
    """One alert draft on disk. `risky` gives it real safety issues."""
    folder = base / "data" / "source_snapshots" / "2026-07-26" / "AE" / "AE-vara" / alert_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "diff.json").write_text(json.dumps({"diff_quality": "GOOD"}), encoding="utf-8")
    draft = {
        "alert_id": alert_id,
        "review_status": "DRAFT",
        "send_decision": "HOLD_FOR_REVIEW",
        "market": "AE",
        "source_id": "AE-vara",
        "source_name": "VARA",
        "checked_at_utc": "2026-07-26T10:00:00+00:00",
        "change_type": "LICENSING",
        # HIGH risk is what makes an approval dispatch INSTANTLY, and LOW
        # confidence / INCOMPLETE proof are real safety issues.
        "risk_level": "HIGH" if risky else "MEDIUM",
        "confidence": "LOW" if risky else "MEDIUM",
        "limitations": [],
        "proof_block": {
            "proof_quality": "INCOMPLETE" if risky else "GOOD",
            "meaningful_change_detected": True,
            "diff_json_path": f"data/source_snapshots/2026-07-26/AE/AE-vara/{alert_id}/diff.json",
        },
    }
    (folder / "alert_draft.json").write_text(
        json.dumps(draft, indent=2), encoding="utf-8"
    )


def _end_to_end(tmp: Path) -> dict:
    out: dict = {}

    import app.alert_review as alert_review
    import app.api as api
    import app.api_alert_review as api_alert_review

    base = tmp / "work"
    base.mkdir(parents=True, exist_ok=True)
    alert_review._BASE_DIR = base
    alert_review._REVIEW_FILE = base / "data" / "alert_reviews" / "reviews.jsonl"

    _write_draft(base, "draft-clean", risky=False)
    _write_draft(base, "draft-risky", risky=True)

    founder = {"id": 1, "email": "founder@statuteproof.com"}
    api.require_auth = lambda handler: dict(founder)
    api_alert_review.require_auth = lambda handler: dict(founder)

    # A customer must not reach this at all; the founder must.
    api._Handler._admin_guard = lambda self, user, **kw: False
    h = _handler("POST", "/api/admin/alert-review",
                 {"alert_id": "draft-clean", "action": "approve_weekly"})
    h.do_POST()
    out["customer_blocked_status"] = h._sent[-1][1] if h._sent else None
    out["a_non_founder_is_blocked"] = out["customer_blocked_status"] != 200

    api._Handler._admin_guard = lambda self, user, **kw: True

    # THE CRITICAL: a HIGH-risk draft with safety issues, approved "for weekly",
    # used to sail through with no friction and dispatch instantly to everyone.
    h = _handler("POST", "/api/admin/alert-review",
                 {"alert_id": "draft-risky", "action": "approve_weekly"})
    h.do_POST()
    body, status = h._sent[-1] if h._sent else ({}, None)
    out["risky_weekly_status"] = status
    out["weekly_approval_is_safety_gated"] = status == 409
    out["safety_issues_returned"] = body.get("safety_issues") if isinstance(body, dict) else None

    # Forcing without a note must still refuse.
    h = _handler("POST", "/api/admin/alert-review",
                 {"alert_id": "draft-risky", "action": "approve_weekly", "force": True})
    h.do_POST()
    out["force_without_note_status"] = h._sent[-1][1] if h._sent else None

    # A forged reviewer must be refused outright, not silently ignored.
    h = _handler("POST", "/api/admin/alert-review",
                 {"alert_id": "draft-clean", "action": "approve_weekly",
                  "reviewer": "Someone Else"})
    h.do_POST()
    out["forged_reviewer_status"] = h._sent[-1][1] if h._sent else None

    # The clean draft releases.
    h = _handler("POST", "/api/admin/alert-review",
                 {"alert_id": "draft-clean", "action": "approve_weekly",
                  "note": "Reviewed."})
    h.do_POST()
    body, status = h._sent[-1] if h._sent else ({}, None)
    out["http_approve_status"] = status
    out["new_status"] = (body.get("record") or {}).get("new_status") if isinstance(body, dict) else None

    latest = alert_review.latest_review_for("draft-clean") or {}
    out["trail_records_the_session_identity"] = (
        latest.get("reviewer") == founder["email"]
    )
    out["record_hides_server_paths"] = isinstance(body, dict) and not any(
        k.endswith("_path") for k in (body.get("record") or {})
    )

    # One unreadable draft must not blank the queue for every other alert.
    bad = base / "data" / "source_snapshots" / "2026-07-26" / "AE" / "AE-vara" / "broken"
    bad.mkdir(parents=True, exist_ok=True)
    (bad / "alert_draft.json").write_bytes(b'{"alert_id": "x\xff\xfe')
    h = _handler("GET", "/api/admin/alert-review-queue")
    h.do_GET()
    body, status = h._sent[-1] if h._sent else ({}, None)
    out["queue_status_with_a_corrupt_draft"] = status
    out["queue_survives_a_corrupt_draft"] = status == 200
    rows = body.get("alerts", []) if isinstance(body, dict) else []
    out["queue_rows"] = len(rows)
    out["queue_states_the_blast_radius"] = any(
        "instant" in str(r.get("delivery_if_approved", "")).lower() for r in rows
    ) if rows else False
    return out


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
    print("end to end, as a logged-in founder")
    for key in (
        "a_non_founder_is_blocked", "risky_weekly_status",
        "weekly_approval_is_safety_gated", "safety_issues_returned",
        "force_without_note_status", "forged_reviewer_status",
        "http_approve_status", "new_status", "trail_records_the_session_identity",
        "record_hides_server_paths", "queue_status_with_a_corrupt_draft",
        "queue_survives_a_corrupt_draft", "queue_rows",
        "queue_states_the_blast_radius",
    ):
        print(f"  {key:34} {report.get(key)}")
    if report.get("end_to_end_error"):
        print(f"  end_to_end_error                   {report['end_to_end_error']}")
    print()
    print(
        ">> AN APPROVER CAN RELEASE WITHOUT A SHELL: "
        f"{report['an_approver_can_release_without_a_shell']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
