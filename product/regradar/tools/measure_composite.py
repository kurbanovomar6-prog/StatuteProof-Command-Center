"""The composite score, computed instead of estimated.

    python3 tools/measure_composite.py
    python3 tools/measure_composite.py --json
    python3 tools/measure_composite.py --skip code_tests    # slow axis, see below

WHY THIS EXISTS. The composite went 88, then 50 on inspection, then 66, then 50
again. Every one of those was an average over the axes somebody had bothered to
look at, with the rest filled in by feel — and a felt score always collapses the
first time anyone checks it. So:

**If any axis is unmeasured, this prints NO composite at all.**

Not a partial average, not "6 of 8 axes look fine". Refusing to produce a number
is the whole point: an average that silently omits the two axes nobody wrote a
measurement for is exactly the artefact that produced 88.

Each axis score below is a function of specific fields from that axis's own
committed measurement tool, with the mapping written out here rather than
carried in someone's head. When reality changes, the number changes; when
nothing changes, re-running gives the identical number. That is the property the
old scores never had.

A NOTE ON LOCAL vs PRODUCTION. Some axis data can only be established on the
deployed box (whether the scheduler is actually running, how fresh the real
source checks are). Those parts are scored on CODE BEHAVIOUR that is verifiable
here — does the API refuse to call a stale source healthy — never on this
laptop's run trail, which says nothing about production.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent.parent
sys.path.insert(0, str(ROOT))

TARGET = 85  # every axis must clear this for the goal to be met


def _run_tool(script: str, timeout: int = 900) -> dict | None:
    """Run one axis tool and return its JSON, or None if it could not be run."""
    path = ROOT / "tools" / script
    if not path.exists():
        return None
    try:
        proc = subprocess.run(
            [sys.executable, str(path), "--json"],
            capture_output=True, text=True, timeout=timeout, cwd=str(ROOT),
        )
    except subprocess.TimeoutExpired:
        return None
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def _pct(passed: int, total: int) -> float:
    return round(100.0 * passed / total, 1) if total else 0.0


# ── per-axis scoring ─────────────────────────────────────────────────────────
#
# Each scorer returns (score, [(check_name, bool_or_None, detail)]). A check that
# is None counts as NOT met — an unverifiable check never scores as a pass.


def score_evidence(data: dict) -> tuple[float, list]:
    pv = data.get("public_verify") or {}
    vt = data.get("verify_trail") or {}
    real = int(pv.get("real_evidence_records") or 0)
    pct_real = float(pv.get("verified_pct_of_real") or 0)
    coverage = vt.get("coverage") or {}

    checks = [
        (">=95% verified over real records", pct_real >= 95, f"{pct_real}% of {real}"),
        (">=100 real records sampled", real >= 100, f"{real} real records"),
        # The anchor was previously unscored, and that omission is what let the
        # one attack the in-file chain cannot see pass unnoticed: an actor who
        # deletes records and RELINKS the survivors produces a chain satisfying
        # every internal invariant. Only the head anchor disagrees.
        ("hash chain intact AND the head anchor matches",
         vt.get("chain_status") == "ok" and vt.get("anchor_status") == "match",
         f"chain={vt.get('chain_status')} anchor={vt.get('anchor_status')}"),
        # This replaces "chain covers the WHOLE trail", which asked for
        # chained >= total and was therefore satisfiable by running relink_chain
        # over everything — retro-stamping the very records it claimed to
        # protect. The question that actually matters is whether every record is
        # tamper-evident by SOME route, and the sealed legacy block is the other
        # route. Strictly stronger: it still requires the chain, adds the anchor,
        # and requires the manifest digest to RECOMPUTE over the ordered
        # identities rather than merely exist.
        ("every trail record is tamper-evident",
         coverage.get("fully_covered") is True
         and vt.get("legacy_status") == "intact",
         f"{coverage.get('chained', '?')} chained + {coverage.get('sealed', '?')} "
         f"sealed = {int(coverage.get('chained') or 0) + int(coverage.get('sealed') or 0)}"
         f"/{coverage.get('total', '?')}"
         + (f", {coverage.get('uncovered')} uncovered" if coverage.get("uncovered") else "")),
    ]
    return _pct(sum(1 for _, ok, _ in checks if ok), len(checks)), checks


def score_reliability(data: dict) -> tuple[float, list]:
    units_tracked, units_named = _systemd_units_state()
    checks = [
        ("a hung source does not wedge the sweep", data.get("sweep_wedged") is False,
         f"sweep_wedged={data.get('sweep_wedged')}"),
        ("the abandoned source leaves a durable failure the breaker sees",
         data.get("breaker_sees_the_abandoned_source") is True,
         str(data.get("breaker_sees_the_abandoned_source"))),
        # Existence was the wrong question and it cost this axis a false pass:
        # both functions existed while every field the watchdog read raised
        # AttributeError, the heredoc's stderr was discarded, and the script
        # exited 0 without restarting anything. What is scored is whether the
        # watchdog's OWN query returns a line.
        ("the watchdog can actually read the heartbeat (its own query runs)",
         data.get("watchdog_can_read_the_heartbeat") is True,
         str(data.get("watchdog_query_output"))[:60] or "no output"),
        ("systemd units are tracked in git", units_tracked, f"{units_tracked}"),
        ("units are named in DEPLOY.md", units_named, f"{units_named}"),
    ]
    return _pct(sum(1 for _, ok, _ in checks if ok), len(checks)), checks


def _systemd_units_state() -> tuple[bool, bool]:
    """Are the watchdog units in git, and named in DEPLOY.md?

    Tracked-in-git is checked with git itself: a unit file sitting untracked in
    the working tree is not shipped, and this axis has been wrongly credited for
    exactly that before.
    """
    try:
        listed = subprocess.run(
            ["git", "ls-files", "product/regradar/deploy/"],
            capture_output=True, text=True, cwd=str(REPO), timeout=30,
        ).stdout
    except Exception:  # noqa: BLE001
        return False, False
    units = [ln for ln in listed.splitlines() if ln.endswith((".service", ".timer"))]
    watchdog_units = [u for u in units if "watchdog" in u]
    if not watchdog_units:
        return False, False
    deploy_md = REPO / "product" / "regradar" / "DEPLOY.md"
    if not deploy_md.exists():
        return True, False
    text = deploy_md.read_text(encoding="utf-8", errors="replace")
    named = all(Path(u).name in text for u in watchdog_units)
    return True, named


def score_health(data: dict) -> tuple[float, list]:
    # Scored on what is verifiable HERE. The number of genuinely stale sources is
    # a property of the deployed scheduler, so it is reported but never scored —
    # this laptop's trail says nothing about production.
    surface_bad = data.get("surface_healthy_without_recent_check")
    freshness_in_api, age_in_api, override_in_api = _health_surface_code_state()
    written_by_a_run = _status_written_by_a_real_run()
    checks = [
        # This asked whether a run WRITES last_checked_at back into the
        # registry, and answered it with a token grep whose accepted tokens
        # included the bare word "write" — a comment could turn it green. It
        # also demanded the wrong design: the run trail is append-only and
        # hash-chained, so a registry copy would be an unchained, weaker
        # duplicate, and sources.json is git-tracked config that a scheduler
        # must not rewrite every cycle. What matters is not who writes the
        # field but whether a STALE run can still be presented as live
        # monitoring, so that is what is now exercised, on real objects.
        ("a stale run can never be described as active monitoring",
         _stale_is_never_called_active(),
         "checked behaviourally" if _stale_is_never_called_active()
         else "a stale run still reads as active"),
        ("the customer surface shows nothing healthy without a recent check",
         surface_bad == 0, f"{surface_bad} such rows"),
        ("the status API reports freshness", freshness_in_api,
         "reported" if freshness_in_api else "absent"),
        ("the status API reports check AGE", age_in_api,
         "reported" if age_in_api else "absent"),
        ("a configured status is OVERRIDDEN when freshness cannot back it",
         override_in_api, "overridden" if override_in_api else "not overridden"),
    ]
    return _pct(sum(1 for _, ok, _ in checks if ok), len(checks)), checks


def _stale_is_never_called_active() -> bool:
    """Drive the real customer-facing wording with a stale run and a fresh one.

    Behavioural, because the grep this replaced could be satisfied by a comment.
    A present-tense claim ("monitoring is active", "passed quality checks") is
    allowed only when the run behind it is inside the stale window; past it the
    wording must state the age instead.
    """
    try:
        from app.source_health_timeline import (
            STALE_AFTER_DAYS,
            source_health_customer_message,
        )
    except Exception:  # noqa: BLE001
        return False

    present_tense = ("is active", "passed quality checks")
    fresh = source_health_customer_message("MONITOR_OK", age_days=1)
    stale = source_health_customer_message(
        "MONITOR_OK", age_days=STALE_AFTER_DAYS + 30)
    return (
        any(c in fresh for c in present_tense)
        and not any(c in stale for c in present_tense)
    )


def _status_written_by_a_real_run() -> bool:
    """Does any run path actually write last_checked_at back into the registry?

    The DoD asks for the registry to be a record of what happened, not a
    hand-maintained assertion. Grepping for the field name alone would match the
    readers, so this looks for a WRITE next to it.
    """
    for name in ("source_registry.py", "monitor.py", "source_runs.py"):
        path = ROOT / "app" / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            if "last_checked_at" not in line:
                continue
            if any(tok in line for tok in ("] =", "\"] =", "update(", "set_", "write")):
                return True
    return False


def _health_surface_code_state() -> tuple[bool, bool, bool]:
    src = ROOT / "app" / "api_sources.py"
    if not src.exists():
        return False, False, False
    text = src.read_text(encoding="utf-8", errors="replace")
    return (
        '"freshness"' in text or "'freshness'" in text,
        "last_run_age_days" in text,
        "configured_status" in text,
    )


def score_customer_path(data: dict) -> tuple[float, list]:
    page, send_visible = _customer_path_code_state()
    checks = [
        ("a real email-verification page exists and is routed", page, str(page)),
        ("a failed verification send is visible to the user", send_visible, str(send_visible)),
        ("an approver can release an alert without a shell",
         data.get("an_approver_can_release_without_a_shell") is True,
         str(data.get("an_approver_can_release_without_a_shell"))),
        ("a non-founder cannot release", data.get("a_non_founder_is_blocked") is True,
         str(data.get("a_non_founder_is_blocked"))),
        ("the release trail records the session identity, not a supplied name",
         data.get("trail_records_the_session_identity") is True,
         str(data.get("trail_records_the_session_identity"))),
    ]
    return _pct(sum(1 for _, ok, _ in checks if ok), len(checks)), checks


def _customer_path_code_state() -> tuple[bool, bool]:
    web = ROOT / "web" / "src"
    page = (web / "components" / "auth" / "VerifyEmailPage.jsx").exists()
    routed = False
    route_map = web / "routeMap.js"
    if route_map.exists():
        routed = "verify-email" in route_map.read_text(encoding="utf-8", errors="replace")
    else:
        for candidate in web.rglob("*.jsx"):
            if "verify-email" in candidate.read_text(encoding="utf-8", errors="replace"):
                routed = True
                break
    api_auth = ROOT / "app" / "api_auth.py"
    send_visible = (
        "verification_email_sent" in api_auth.read_text(encoding="utf-8", errors="replace")
        if api_auth.exists() else False
    )
    return (page and routed), send_visible


def score_security(sec: dict, team: dict) -> tuple[float, list]:
    checks = [
        ("repeated failed logins lock the account",
         sec.get("account_locks_after_repeated_failures") is True,
         f"locks={sec.get('account_locks_after_repeated_failures')}"),
        ("a wrong password is never accepted",
         sec.get("wrong_password_ever_accepted") is False,
         f"ever_accepted={sec.get('wrong_password_ever_accepted')}"),
        ("an operator bootstrap exists", sec.get("operator_bootstrap_exists") is True,
         str(sec.get("operator_bootstrap_exists"))),
        ("and it produces a real operator principal",
         sec.get("bootstrap_produces_operator") is True,
         f"org after bootstrap: {sec.get('operator_org_after_bootstrap')}"),
        ("an org owner cannot grant GLOBAL scope",
         sec.get("owner_can_grant_global_scope") is False,
         f"can_grant={sec.get('owner_can_grant_global_scope')}"),
        ("an owner can seat a second user without a shell",
         team.get("owner_can_add_a_colleague_without_a_shell") is True,
         str(team.get("owner_can_add_a_colleague_without_a_shell"))),
        ("a seated teammate actually resolves to that org",
         team.get("seated_mate_resolves_to_owner_org") is True,
         str(team.get("seated_mate_resolves_to_owner_org"))),
        ("a seated auditor cannot seat others",
         team.get("auditor_cannot_seat") is True,
         str(team.get("auditor_cannot_seat"))),
    ]
    return _pct(sum(1 for _, ok, _ in checks if ok), len(checks)), checks


def score_code_tests(data: dict) -> tuple[float, list]:
    # The key name is read from the tool's actual output, not guessed: an
    # earlier version looked for a name that does not exist, got None, and
    # scored a PASSING check as a failure.
    leaked = data.get("modules_mutating_live_artifacts")
    fixture = _autouse_fixture_present()
    tracked_failures = _tracked_test_failures()
    count = len(leaked) if isinstance(leaked, list) else leaked
    checks = [
        ("no test module touches the live working artifacts",
         isinstance(count, int) and count == 0,
         f"{count} of {data.get('modules_checked', '?')} modules mutate them"
         if count is not None else "tool reported nothing"),
        ("an autouse temp-BASE_DIR fixture exists", fixture,
         "present" if fixture else "absent"),
        ("no TRACKED test fails",
         tracked_failures == 0,
         # Named, not counted: a bare number is undiagnosable, and this tree is
         # shared with another session whose untracked tests fail.
         ", ".join(_TRACKED_FAILING) if _TRACKED_FAILING
         else ("none" if tracked_failures == 0 else "not run")),
    ]
    return _pct(sum(1 for _, ok, _ in checks if ok), len(checks)), checks


def _autouse_fixture_present() -> bool:
    conftest = ROOT / "tests" / "conftest.py"
    if not conftest.exists():
        return False
    text = conftest.read_text(encoding="utf-8", errors="replace")
    return "autouse=True" in text and "tmp_path" in text


_TRACKED_FAILING: list[str] = []


def _tracked_test_failures() -> int | None:
    """Failures in TRACKED test files only.

    This working tree is shared with another session whose untracked test files
    fail; counting those as this project's health would be attributing someone
    else's unfinished work to the axis.
    """
    # junit XML rather than scraped stdout. With --continue-on-collection-errors
    # pytest emits no "N failed, M passed" line to either stream, so a guard
    # looking for one rejected every valid run — the mirror of the bug it was
    # added to fix, and just as wrong. The XML always carries the totals.
    import tempfile
    import xml.etree.ElementTree as ET

    with tempfile.TemporaryDirectory() as tmp:
        report = Path(tmp) / "junit.xml"
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no",
                 "-p", "no:cacheprovider", "--continue-on-collection-errors",
                 f"--junitxml={report}"],
                capture_output=True, text=True, timeout=3600, cwd=str(ROOT),
            )
        except Exception:  # noqa: BLE001
            return None

        # 0 = all passed, 1 = tests failed. Anything else (2 interrupted,
        # 3 internal, 4 usage, 5 nothing collected) means the suite did not
        # actually run and must never read as "no failures".
        if proc.returncode not in (0, 1):
            _TRACKED_FAILING.append(f"pytest did not run (exit {proc.returncode})")
            return None
        if not report.exists():
            _TRACKED_FAILING.append("pytest produced no junit report")
            return None
        try:
            root = ET.parse(report).getroot()
        except Exception:  # noqa: BLE001
            _TRACKED_FAILING.append("junit report unreadable")
            return None
        suite = root.find("testsuite") if root.tag == "testsuites" else root
        collected = int((suite.get("tests") if suite is not None else 0) or 0)
        if collected <= 0:
            _TRACKED_FAILING.append("pytest collected no tests")
            return None

    failures = [
        ln.split("::")[0].replace("FAILED ", "").replace("ERROR ", "").strip()
        for ln in proc.stdout.splitlines()
        if ln.startswith(("FAILED ", "ERROR "))
    ]
    tracked = 0
    seen: dict[str, bool] = {}
    for rel in failures:
        if rel not in seen:
            check = subprocess.run(
                ["git", "ls-files", "--error-unmatch", f"product/regradar/{rel}"],
                capture_output=True, text=True, cwd=str(REPO),
            )
            seen[rel] = check.returncode == 0
        if seen[rel]:
            tracked += 1
            if rel not in _TRACKED_FAILING:
                _TRACKED_FAILING.append(rel)
    return tracked


def score_claim_honesty(data: dict) -> tuple[float, list]:
    infra = data.get("infrastructure_claims") or {}
    hits = data.get("forbidden_claim_hits") or []
    checks = [
        ("every published number is recomputed from sources.json and matches",
         data.get("all_numbers_match") is True,
         ", ".join(f"{k} {v['published']}vs{v['recomputed']}"
                   for k, v in (data.get("drift") or {}).items()) or "nothing published"),
        ("no forbidden claim is ASSERTED in shipped copy",
         data.get("forbidden_claims_clean") is True,
         f"{len(hits)} asserted"),
        ("the legal pages name the real host",
         infra.get("names_the_real_host") is True and not infra.get("names_a_stale_host"),
         f"real={infra.get('names_the_real_host')} stale={infra.get('names_a_stale_host')}"),
        # A UAE-market regulatory product whose privacy text knows only GDPR is
        # making an implicit claim about the law it operates under.
        # KNOWN WEAKNESS, stated rather than hidden: this is a substring, so the
        # four letters anywhere — including "PDPL does not apply" — satisfy it.
        # Strengthening it means judging whether a SENTENCE is true, which needs
        # the lawyer who writes that sentence, not a scanner.
        ("UAE PDPL is addressed, not only GDPR",
         infra.get("mentions_pdpl") is True,
         f"pdpl={infra.get('mentions_pdpl')} gdpr={infra.get('mentions_gdpr')}"),
        # A published promise with no implementation behind it is the exact
        # failure this axis names, and nothing looked for it: the legal pages
        # tell customers artefacts are "permanently deleted" once their plan's
        # retention window expires, app/plan.py defines retention_days per plan,
        # and no code reads it.
        ("the published data-retention promise is implemented",
         (data.get("retention") or {}).get("promise_without_implementation") is False,
         "implemented by " + ", ".join((data.get("retention") or {}).get("plan_retention_days_readers") or [])
         if (data.get("retention") or {}).get("plan_retention_days_readers")
         else "promised in the legal pages, implemented nowhere"),
    ]
    return _pct(sum(1 for _, ok, _ in checks if ok), len(checks)), checks


def score_ux(data: dict) -> tuple[float, list]:
    axe = data.get("axe") or {}
    vis = data.get("visual_regression") or {}
    tok = data.get("design_tokens") or {}
    public_all = (
        axe.get("public_screens_covered", 0) >= axe.get("public_screens", 1)
    )
    app_half = (
        axe.get("app_screens", 0) > 0
        and axe.get("app_screens_covered", 0) * 2 >= axe.get("app_screens", 0)
    )
    checks = [
        ("every public screen is under axe",
         public_all,
         f"{axe.get('public_screens_covered')}/{axe.get('public_screens')}"),
        ("at least half the authenticated app screens are under axe",
         app_half,
         f"{axe.get('app_screens_covered')}/{axe.get('app_screens')}"),
        # jsdom cannot compute contrast, so a green axe run is silent about it.
        ("colour contrast is actually checked, not just assumed",
         axe.get("contrast_actually_checked") is True,
         str(axe.get("contrast_actually_checked"))),
        ("visual regression renders at every required width",
         vis.get("takes_screenshots") is True and not vis.get("missing_widths"),
         f"missing {vis.get('missing_widths')}"),
        # The check that makes this axis unable to lie: the suites must PASS,
        # not merely exist. Without it the axis scored on test COUNT while 19
        # contrast nodes failed and the landing page overflowed a phone.
        ("the browser a11y + overflow suites actually pass",
         (data.get("browser_suites") or {}).get("all_green") is True,
         f"{(data.get('browser_suites') or {}).get('failed', '?')} failing"
         + (f" ({', '.join((data.get('browser_suites') or {}).get('failing_screens', [])[:4])})"
            if (data.get("browser_suites") or {}).get("failing_screens") else "")),
        ("no dead design tokens, guard in place",
         not tok.get("defined_never_used") and not tok.get("used_never_defined")
         and tok.get("guard_test_present") is True,
         f"{len(tok.get('defined_never_used') or [])} dead, "
         f"guard={tok.get('guard_test_present')}"),
    ]
    return _pct(sum(1 for _, ok, _ in checks if ok), len(checks)), checks


# ── axis table ───────────────────────────────────────────────────────────────

# Per-axis wall-clock budget. code_tests runs pytest once per module to see which
# ones touch the live artifacts, so it is minutes, not seconds — giving it the
# default budget made it time out and report "tool failed to run", which the
# composite then correctly refused to average over.
TIMEOUTS = {"code_tests": 5400, "ux": 2400}

AXES = [
    ("evidence",      "EVIDENCE",       ["measure_evidence_axis.py"]),
    ("reliability",   "RELIABILITY",    ["measure_reliability_axis.py"]),
    ("health",        "HEALTH HONESTY", ["measure_health_axis.py"]),
    ("customer_path", "CUSTOMER PATH",  ["measure_alert_release_axis.py"]),
    ("security",      "SECURITY",       ["measure_security_axis.py", "measure_team_axis.py"]),
    ("code_tests",    "CODE AND TESTS", ["measure_test_isolation.py"]),
    ("claim_honesty", "CLAIM HONESTY",  ["measure_claim_honesty_axis.py"]),
    ("ux",            "UX",             ["measure_ux_axis.py"]),
]


def measure(skip: set[str]) -> dict:
    results: dict = {}
    for key, title, tools in AXES:
        if key in skip:
            results[key] = {"title": title, "score": None, "reason": "skipped by --skip"}
            continue
        missing = [t for t in tools if not (ROOT / "tools" / t).exists()]
        if missing:
            results[key] = {
                "title": title, "score": None,
                "reason": f"NO MEASUREMENT TOOL: {', '.join(missing)}",
            }
            continue
        budget = TIMEOUTS.get(key, 900)
        data = [_run_tool(t, timeout=budget) for t in tools]
        if any(d is None for d in data):
            results[key] = {"title": title, "score": None, "reason": "tool failed to run"}
            continue
        if key == "security":
            score, checks = score_security(data[0] or {}, data[1] or {})
        else:
            scorer = {
                "evidence": score_evidence,
                "reliability": score_reliability,
                "health": score_health,
                "customer_path": score_customer_path,
                "code_tests": score_code_tests,
                "claim_honesty": globals().get("score_claim_honesty"),
                "ux": globals().get("score_ux"),
            }[key]
            score, checks = scorer(data[0] or {})
        results[key] = {
            "title": title,
            "score": score,
            "checks": [{"check": c, "passed": bool(ok), "detail": d} for c, ok, d in checks],
        }

    measured = [r for r in results.values() if r.get("score") is not None]
    unmeasured = [(k, r) for k, r in results.items() if r.get("score") is None]

    return {
        "axes": results,
        "unmeasured": [k for k, _ in unmeasured],
        # The refusal is the feature. A composite over a subset is how a felt
        # score gets laundered into a real-looking number.
        "composite": (
            round(sum(r["score"] for r in measured) / len(measured))
            if measured and not unmeasured else None
        ),
        "target_per_axis": TARGET,
        "below_target": sorted(
            [(k, r["score"]) for k, r in results.items()
             if r.get("score") is not None and r["score"] < TARGET],
            key=lambda kv: kv[1],
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--skip", action="append", default=[],
                        help="axis key to skip (still blocks the composite)")
    args = parser.parse_args()

    report = measure(set(args.skip))
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    for key, _title, _ in AXES:
        row = report["axes"][key]
        score = row.get("score")
        head = f"{row['title']:16}"
        if score is None:
            print(f"{head} ——   {row.get('reason')}")
            continue
        flag = "ok " if score >= TARGET else "LOW"
        print(f"{head} {score:5.1f}  {flag}")
        for c in row.get("checks", []):
            mark = "+" if c["passed"] else "-"
            print(f"    {mark} {c['check']:62} {c['detail']}")

    print()
    if report["composite"] is None:
        print("COMPOSITE: NOT COMPUTED — unmeasured axes: "
              + ", ".join(report["unmeasured"]))
        print("An average over the axes that happen to have a tool is exactly how")
        print("a score of 88 survives until someone checks the rest.")
        return 1
    print(f"COMPOSITE: {report['composite']}   (every axis must reach {TARGET})")
    if report["below_target"]:
        print("below target: " + ", ".join(
            f"{k} {v:.0f}" for k, v in report["below_target"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
