"""Reproducible measurement for the TEAM / MULTI-USER axis.

The question a customer actually asks: **can the person who paid add a
colleague, and can that colleague sign in and see the same org's data, without
anyone touching a shell?**

    python3 tools/measure_team_axis.py
    python3 tools/measure_team_axis.py --json

Behavioural on purpose. It drives the real ``_Handler.do_POST`` / ``do_GET``
dispatch, so a route that exists as a function but was never wired into the
dispatcher measures as absent — which is what it is, from the browser's side.
Everything runs against a temp SQLite file; no working artifacts are touched.

Note on what "seated" means here: the check is not whether a row landed in a
table, but whether the teammate RESOLVES to the owner's org. A membership row
that resolve_principal does not honour would let the UI show a colleague who
still cannot see anything.
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

# Paths a reasonable frontend would call. If none of them route, there is no
# HTTP door regardless of what the CLI can do.
_SEAT_PATHS = (
    "/api/team/members",
    "/api/org/members",
    "/api/account/team",
)
_REVOKE_PATHS = (
    "/api/team/members/revoke",
    "/api/org/members/revoke",
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
    h._send_bytes = lambda body_, ct, status=200, extra_headers=None: sent.append(
        ({"bytes": len(body_)}, status)
    )
    h._sent = sent
    return h


def _status(h) -> int | None:
    return h._sent[-1][1] if h._sent else None


def _probe_route(method: str, path: str, body: dict | None = None) -> int | None:
    """Return the status the dispatcher produces, or None if it blew up.

    404 means "no such route". Anything else — including 401/403 — means the
    route EXISTS and the request was merely rejected, which is the distinction
    this whole measurement turns on.
    """
    h = _handler(method, path, body)
    try:
        if method == "POST":
            h.do_POST()
        else:
            h.do_GET()
    except Exception:  # noqa: BLE001 — an exploding route still exists
        return _status(h)
    return _status(h)


def measure() -> dict:
    report: dict = {}

    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)

        import app.db as app_db

        app_db.DB_PATH = str(tmp / "team.db")

        # ── is there an HTTP door at all? ────────────────────────────────
        routed_seat = {
            p: _probe_route("POST", p, {"email": "x@example.com", "role": "auditor"})
            for p in _SEAT_PATHS
        }
        routed_list = {p: _probe_route("GET", p) for p in _SEAT_PATHS}
        routed_revoke = {
            p: _probe_route("POST", p, {"email": "x@example.com"}) for p in _REVOKE_PATHS
        }

        report["seat_routes"] = routed_seat
        report["list_routes"] = routed_list
        report["revoke_routes"] = routed_revoke
        report["can_seat_over_http"] = any(s not in (404, None) for s in routed_seat.values())
        report["can_list_over_http"] = any(s not in (404, None) for s in routed_list.values())
        report["can_revoke_over_http"] = any(
            s not in (404, None) for s in routed_revoke.values()
        )

        # ── does the underlying seating actually work? ───────────────────
        # Measured separately: an HTTP door onto a broken mechanism is worse
        # than no door, and a working mechanism with no door is the CLI-only
        # state we are trying to leave.
        try:
            from app.auth import create_user
            from app.rbac_runtime import assign_org_role, resolve_principal

            owner = create_user("owner@example.com", "password-123")
            mate = create_user("mate@example.com", "password-123")
            app_db.backfill_org_memberships()

            principal = resolve_principal(owner)
            owner_org = int(principal.org_id or 0)
            seat = assign_org_role(owner, int(mate["id"]), owner_org, "auditor")
            report["cli_seat_ok"] = bool(seat.get("ok", seat.get("assigned", False)))

            mate_principal = resolve_principal(mate)
            report["seated_mate_resolves_to_owner_org"] = (
                int(mate_principal.org_id or -1) == owner_org
            )
            report["seated_mate_role"] = mate_principal.role
        except Exception as exc:  # noqa: BLE001 — the probe reports, never raises
            report["cli_seat_ok"] = f"error: {type(exc).__name__}: {exc}"
            report["seated_mate_resolves_to_owner_org"] = False
            report["seated_mate_role"] = None

        # ── end to end, authenticated ────────────────────────────────────
        # A route that merely exists proves nothing. This drives the real
        # dispatcher as a logged-in owner and then asks the RBAC layer whether
        # the colleague actually landed somewhere they can see.
        try:
            import app.api as api
            import app.api_team as api_team
            from app.auth import create_user
            from app.rbac_runtime import resolve_principal

            boss = create_user("boss@example.com", "password-123")
            staff = create_user("staff@example.com", "password-123")
            outsider = create_user("outsider@example.com", "password-123")
            app_db.backfill_org_memberships()
            boss_org = int(resolve_principal(boss).org_id or 0)

            def _as(user):
                api.require_auth = lambda handler: dict(user)
                api_team.require_auth = lambda handler: dict(user)

            _as(boss)
            h = _handler("POST", "/api/team/members",
                         {"email": "staff@example.com", "role": "auditor"})
            h.do_POST()
            report["http_seat_status"] = _status(h)
            report["http_seat_lands_in_owner_org"] = (
                int(resolve_principal(staff).org_id or -1) == boss_org
            )

            h = _handler("GET", "/api/team/members")
            h.do_GET()
            body = h._sent[-1][0] if h._sent else {}
            report["http_roster_size"] = len(body.get("members", []))

            # The seated auditor must NOT be able to seat anyone else, or
            # "add one colleague" quietly becomes "add the whole internet".
            _as(staff)
            h = _handler("POST", "/api/team/members",
                         {"email": "outsider@example.com", "role": "auditor"})
            h.do_POST()
            report["auditor_seat_refused_status"] = _status(h)
            report["auditor_cannot_seat"] = _status(h) == 403
            report["outsider_stayed_out"] = (
                int(resolve_principal(outsider).org_id or -1) != boss_org
            )

            _as(boss)
            h = _handler("POST", "/api/team/members/revoke", {"email": "staff@example.com"})
            h.do_POST()
            report["http_revoke_status"] = _status(h)
            report["revoked_mate_left_the_org"] = (
                int(resolve_principal(staff).org_id or -1) != boss_org
            )
        except Exception as exc:  # noqa: BLE001 — the probe reports, never raises
            report["end_to_end_error"] = f"{type(exc).__name__}: {exc}"

    report["owner_can_add_a_colleague_without_a_shell"] = bool(
        report.get("can_seat_over_http")
        and report.get("http_seat_lands_in_owner_org")
        and report.get("auditor_cannot_seat")
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
    for label, key in (("seat", "seat_routes"), ("list", "list_routes"), ("revoke", "revoke_routes")):
        for path, status in report[key].items():
            print(f"  {label:7} {path:26} {status}")
    print()
    print(f"  can seat over HTTP                 {report['can_seat_over_http']}")
    print(f"  can list members over HTTP         {report['can_list_over_http']}")
    print(f"  can revoke over HTTP               {report['can_revoke_over_http']}")
    print()
    print("end to end, as a logged-in owner")
    for key in (
        "http_seat_status", "http_seat_lands_in_owner_org", "http_roster_size",
        "auditor_seat_refused_status", "auditor_cannot_seat", "outsider_stayed_out",
        "http_revoke_status", "revoked_mate_left_the_org",
    ):
        print(f"  {key:34} {report.get(key)}")
    if report.get("end_to_end_error"):
        print(f"  end_to_end_error                   {report['end_to_end_error']}")
    print()
    print("underlying mechanism (CLI path)")
    print(f"  assign_org_role succeeds           {report['cli_seat_ok']}")
    print(f"  seated mate resolves to owner org  {report['seated_mate_resolves_to_owner_org']}")
    print(f"  seated mate role                   {report['seated_mate_role']}")
    print()
    print(
        ">> OWNER CAN ADD A COLLEAGUE WITHOUT A SHELL: "
        f"{report['owner_can_add_a_colleague_without_a_shell']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
