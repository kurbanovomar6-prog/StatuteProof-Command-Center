"""Tests for the negative-assurance coverage certificate.

Covers the legal-safety contract (disclaimer present, forbidden-claims guard,
evidence-grounding) plus the substantive behaviour: changed + unchanged sources
are both listed, monitoring gaps are disclosed and never hidden, and an empty
period still produces a valid, legally-safe certificate.
"""

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.coverage_certificate import (
    _ALL_FORBIDDEN,
    build_coverage_certificate,
    contains_forbidden_claim,
    export_coverage_certificate_html,
    export_coverage_certificate_json,
    generate_coverage_certificate_pdf,
    month_period,
    render_coverage_certificate_html,
    render_coverage_certificate_markdown,
)
from app.monthly_assurance_report import _FORBIDDEN_PHRASES

_NOW = datetime(2026, 6, 16, tzinfo=timezone.utc)
_FULL_DISCLAIMER_MARK = "do not constitute"  # unique fragment of the full disclaimer


def _write_sources(base: Path, sources: list[dict]) -> None:
    (base / "sources.json").write_text(json.dumps(sources, sort_keys=True), encoding="utf-8")


def _run(
    source_id: str,
    day: int,
    *,
    change_status: str = "UNCHANGED",
    normalized_hash: str | None = "a" * 64,
    error: str = "",
    name: str | None = None,
) -> dict:
    rec = {
        "source_id": source_id,
        "source_name": name or source_id,
        "official_url": f"https://official.example/{source_id}",
        "timestamp_utc": f"2026-06-{day:02d}T10:00:00Z",
        "change_status": change_status,
        "extraction_quality": "FAILED" if change_status in ("FAILED", "QUALITY_DROP") else "GOOD",
        "normalized_hash": normalized_hash,
        "record_type": "heartbeat",
    }
    if error:
        rec["error"] = error
        rec["limitations_notes"] = error
    return rec


def _skip_run(source_id: str, day: int, *, name: str | None = None) -> dict:
    """A cycle the circuit breaker SKIPPED: a durable trail record proving the
    source was not fetched — no HTTP request was made at all."""
    rec = _run(
        source_id,
        day,
        change_status="QUALITY_DROP",
        normalized_hash=None,
        error=(
            "Circuit open — source skipped after consecutive unusable runs; "
            "not fetched this cycle"
        ),
        name=name,
    )
    rec["record_type"] = "quality_drop"
    rec["alert_suppressed_reason"] = "circuit_open"
    rec["failure_code"] = "CIRCUIT_OPEN"
    rec["access_status"] = "circuit_open"
    return rec


def _write_runs(base: Path, runs: list[dict]) -> None:
    path = base / "data" / "source_runs" / "source_runs.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in runs:
            fh.write(json.dumps(r, sort_keys=True) + "\n")


def _standard_scenario(base: Path) -> None:
    """VARA (changed), CBUAE (unchanged/continuous), GAP (gap + FAILED)."""
    _write_sources(
        base,
        [
            {"source_id": "AE-vara", "name": "VARA Rulebook", "url": "https://www.vara.ae/"},
            {"source_id": "AE-cbuae", "name": "CBUAE Rulebook", "url": "https://www.cbuae.gov.ae/"},
            {"source_id": "AE-gap", "name": "Gappy Source", "url": "https://gap.example/"},
        ],
    )
    runs: list[dict] = []
    for d in range(1, 16):
        runs.append(_run("AE-vara", d, change_status="CHANGED" if d == 7 else "UNCHANGED",
                         normalized_hash=("c" * 64 if d == 7 else "a" * 64)))
    for d in range(1, 16):
        runs.append(_run("AE-cbuae", d))
    # GAP source: only checked on day 1 and day 10, plus a FAILED run on day 12.
    runs.append(_run("AE-gap", 1))
    runs.append(_run("AE-gap", 10))
    runs.append(_run("AE-gap", 12, change_status="FAILED", normalized_hash=None,
                     error="HTTP 503 from source"))
    _write_runs(base, runs)


class CoverageCertificateTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _cert(self, **kwargs):
        params = dict(
            period_start="2026-06-01",
            period_end="2026-06-15",
            client_name="Acme Compliance",
            base_dir=self.base,
            now=_NOW,
        )
        params.update(kwargs)
        return build_coverage_certificate(**params)

    # ── changed + unchanged listing ─────────────────────────────────────────

    def test_lists_changed_and_unchanged_sources(self):
        _standard_scenario(self.base)
        cert = self._cert()
        by_id = {r["source_id"]: r for r in cert["sources"]}
        self.assertEqual(by_id["AE-vara"]["change_state"], "CHANGED")
        self.assertEqual(by_id["AE-cbuae"]["change_state"], "UNCHANGED")
        self.assertEqual(cert["summary"]["sources_changed"], 1)
        self.assertGreaterEqual(cert["summary"]["sources_unchanged_with_proof"], 1)
        md = render_coverage_certificate_markdown(cert)
        self.assertIn("Change detected", md)
        self.assertIn("No change on days checked", md)

    def test_provably_unchanged_has_proof_hash_and_check_dates(self):
        _standard_scenario(self.base)
        cert = self._cert()
        cbuae = next(r for r in cert["sources"] if r["source_id"] == "AE-cbuae")
        self.assertEqual(cbuae["days_with_proof_hash"], 15)
        self.assertEqual(cbuae["successful_checks"], 15)
        self.assertTrue(cbuae["first_check_utc"].startswith("2026-06-01"))
        self.assertTrue(cbuae["last_check_utc"].startswith("2026-06-15"))
        self.assertEqual(cbuae["last_proof_hash"], "a" * 64)
        self.assertEqual(cbuae["continuity_status"], "CONTINUOUS")

    # ── honest gap disclosure ───────────────────────────────────────────────

    def test_monitoring_gap_is_shown_not_hidden(self):
        _standard_scenario(self.base)
        cert = self._cert()
        gap = next(r for r in cert["sources"] if r["source_id"] == "AE-gap")
        self.assertGreater(gap["gap_days"], 0)
        self.assertGreaterEqual(gap["max_consecutive_gap_days"], 8)
        self.assertEqual(gap["continuity_status"], "PARTIAL")
        self.assertEqual(cert["summary"]["sources_with_gaps"], 1)
        # And it must appear in the rendered disclosure section, not be omitted.
        md = render_coverage_certificate_markdown(cert)
        self.assertIn("Gappy Source", md)
        self.assertIn("no recorded proof-hash check", md)

    def test_failed_check_disclosed_as_degraded_with_reason(self):
        _standard_scenario(self.base)
        cert = self._cert()
        gap = next(r for r in cert["sources"] if r["source_id"] == "AE-gap")
        self.assertTrue(gap["degraded"])
        self.assertEqual(gap["failed_count"], 1)
        self.assertIn("HTTP 503 from source", gap["degraded_reasons"])
        self.assertEqual(cert["summary"]["sources_degraded"], 1)
        md = render_coverage_certificate_markdown(cert)
        self.assertIn("FAILED and produced no usable content", md)

    def test_quality_drop_disclosed(self):
        _write_sources(self.base, [{"source_id": "AE-qd", "name": "QD Source", "url": "https://qd.example/"}])
        runs = [_run("AE-qd", d) for d in range(1, 15)]
        runs.append(_run("AE-qd", 15, change_status="QUALITY_DROP", normalized_hash=None,
                         error="normalized text thin"))
        _write_runs(self.base, runs)
        cert = self._cert(source_ids=["AE-qd"])
        qd = cert["sources"][0]
        self.assertEqual(qd["quality_drop_count"], 1)
        self.assertTrue(qd["degraded"])
        md = render_coverage_certificate_markdown(cert)
        self.assertIn("quality drop", md)

    def test_explicitly_named_source_with_no_runs_shown_as_no_coverage(self):
        _standard_scenario(self.base)
        cert = self._cert(source_ids=["AE-vara", "AE-never-checked"])
        never = next(r for r in cert["sources"] if r["source_id"] == "AE-never-checked")
        self.assertEqual(never["change_state"], "NO_PROOF")
        self.assertEqual(never["continuity_status"], "NO_COVERAGE")
        self.assertEqual(never["successful_checks"], 0)
        self.assertEqual(cert["summary"]["sources_no_coverage"], 1)
        md = render_coverage_certificate_markdown(cert)
        self.assertIn("No coverage", md)
        self.assertIn("UNVERIFIED", md)

    # ── BLOCK-2: default customer path scopes to CONFIGURED (enabled) sources ──

    def _write_enabled_sources(self, rows: list[dict]) -> None:
        # Full, valid enabled source rows (app.sources.validate_source requires
        # name/url/jurisdiction/category/enabled). Explicit source_id so
        # make_source_id returns it verbatim, matching the run keys.
        (self.base / "sources.json").write_text(json.dumps(rows), encoding="utf-8")

    def test_configured_zero_run_source_is_no_coverage_in_default_path(self):
        # A configured (enabled) source that was NEVER checked in the period must
        # surface as NO_COVERAGE on the DEFAULT (source_ids=None) customer path —
        # not be silently omitted, which would defeat negative assurance.
        self._write_enabled_sources([
            {"source_id": "AE-live", "name": "Live Source", "url": "https://live.example/",
             "jurisdiction": "AE", "category": "financial_regulator", "enabled": True},
            {"source_id": "AE-dark", "name": "Dark Source", "url": "https://dark.example/",
             "jurisdiction": "AE", "category": "financial_regulator", "enabled": True},
        ])
        _write_runs(self.base, [_run("AE-live", d) for d in range(1, 16)])

        cert = self._cert()  # source_ids=None → default customer scope
        by_id = {r["source_id"]: r for r in cert["sources"]}
        self.assertIn("AE-dark", by_id, "a fully-dark configured source must not be omitted")
        self.assertEqual(by_id["AE-dark"]["change_state"], "NO_PROOF")
        self.assertEqual(by_id["AE-dark"]["continuity_status"], "NO_COVERAGE")
        self.assertEqual(by_id["AE-dark"]["successful_checks"], 0)
        self.assertGreaterEqual(cert["summary"]["sources_no_coverage"], 1)

    def test_disabled_source_not_forced_into_default_scope(self):
        # An enabled source is in scope; a disabled one with no runs is not.
        self._write_enabled_sources([
            {"source_id": "AE-on", "name": "On", "url": "https://on.example/",
             "jurisdiction": "AE", "category": "financial_regulator", "enabled": True},
            {"source_id": "AE-off", "name": "Off", "url": "https://off.example/",
             "jurisdiction": "AE", "category": "financial_regulator", "enabled": False},
        ])
        _write_runs(self.base, [_run("AE-on", d) for d in range(1, 16)])
        cert = self._cert()
        ids = {r["source_id"] for r in cert["sources"]}
        self.assertIn("AE-on", ids)
        self.assertNotIn("AE-off", ids)

    def test_enabled_source_ids_returns_configured_scope(self):
        # This is exactly what _handle_coverage_certificate passes by default.
        from app.coverage_certificate import enabled_source_ids

        self._write_enabled_sources([
            {"source_id": "AE-a", "name": "A", "url": "https://a.example/",
             "jurisdiction": "AE", "category": "financial_regulator", "enabled": True},
            {"source_id": "AE-b", "name": "B", "url": "https://b.example/",
             "jurisdiction": "AE", "category": "financial_regulator", "enabled": True},
            {"source_id": "AE-c", "name": "C", "url": "https://c.example/",
             "jurisdiction": "AE", "category": "financial_regulator", "enabled": False},
        ])
        ids = enabled_source_ids(base_dir=self.base)
        self.assertEqual(ids, ["AE-a", "AE-b"])

    # ── legal-safety contract ───────────────────────────────────────────────

    def test_carries_full_and_short_disclaimer(self):
        _standard_scenario(self.base)
        cert = self._cert()
        self.assertIn(_FULL_DISCLAIMER_MARK, cert["disclaimer"])
        self.assertEqual(cert["disclaimer_short"], "Monitoring intelligence only. Not legal advice.")
        md = render_coverage_certificate_markdown(cert)
        self.assertIn(_FULL_DISCLAIMER_MARK, md)
        self.assertIn("**Disclaimer:**", md)

    def test_generated_body_passes_forbidden_claims_guard(self):
        _standard_scenario(self.base)
        cert = self._cert()
        md = render_coverage_certificate_markdown(cert)
        # Guard the CONTENT section (everything before the vetted disclaimer),
        # the same content-vs-disclaimer split the monthly assurance test uses.
        body = md.split("**Disclaimer:**")[0]
        self.assertIsNone(contains_forbidden_claim(body))
        # The negative-assurance statement itself must be clean.
        self.assertIsNone(contains_forbidden_claim(cert["negative_assurance_statement"]))
        # HTML body (pre-disclaimer) is clean too.
        html = render_coverage_certificate_html(cert)
        html_body = html.split("Disclaimer:")[0]
        self.assertIsNone(contains_forbidden_claim(html_body))

    def test_negative_assurance_statement_makes_no_completeness_guarantee(self):
        _standard_scenario(self.base)
        cert = self._cert()
        statement = cert["negative_assurance_statement"].lower()
        self.assertIn("does not assert that every regulatory update was captured", statement)
        for banned in ("never miss", "complete coverage", "guarantee compliance"):
            self.assertNotIn(banned, statement)

    def test_reuses_monthly_assurance_forbidden_phrases(self):
        # Genuine reuse: the shared ban list is a subset of the certificate's.
        monthly = {p.lower() for p in _FORBIDDEN_PHRASES}
        self.assertTrue(monthly.issubset(set(_ALL_FORBIDDEN)))

    def test_render_raises_if_forbidden_phrase_planted_in_body(self):
        _standard_scenario(self.base)
        cert = self._cert()
        # Simulate wording drift: inject a banned affirmative claim into a field
        # that is rendered into the body. The guard must refuse to render.
        cert["negative_assurance_statement"] = "This certificate proves complete coverage of all sources."
        with self.assertRaises(ValueError):
            render_coverage_certificate_markdown(cert)

    def test_contains_forbidden_claim_detects_planted_phrase(self):
        self.assertEqual(contains_forbidden_claim("we guarantee compliance"), "guarantee compliance")
        self.assertEqual(contains_forbidden_claim("we never miss an update"), "never miss")
        self.assertIsNone(contains_forbidden_claim("we checked the source and recorded a proof hash"))

    # ── empty period ────────────────────────────────────────────────────────

    def test_empty_period_is_valid_and_legally_safe(self):
        _standard_scenario(self.base)
        # A period with no runs at all.
        cert = self._cert(period_start="2020-01-01", period_end="2020-01-31")
        self.assertEqual(cert["summary"]["sources_total"], 0)
        self.assertEqual(cert["sources"], [])
        md = render_coverage_certificate_markdown(cert)
        self.assertIn(_FULL_DISCLAIMER_MARK, md)
        self.assertIsNone(contains_forbidden_claim(md.split("**Disclaimer:**")[0]))
        self.assertIn("Coverage Statement", md)

    def test_empty_base_dir_no_files(self):
        # No sources.json and no runs file at all — must not raise.
        cert = self._cert(period_start="2026-06-01", period_end="2026-06-30")
        self.assertEqual(cert["summary"]["sources_total"], 0)
        self.assertIn(_FULL_DISCLAIMER_MARK, cert["disclaimer"])

    # ── determinism + evidence grounding ────────────────────────────────────

    def test_certificate_id_deterministic_for_completed_period(self):
        _standard_scenario(self.base)
        a = self._cert(now=datetime(2026, 6, 16, tzinfo=timezone.utc))
        b = self._cert(now=datetime(2026, 8, 1, tzinfo=timezone.utc))
        self.assertEqual(a["certificate_id"], b["certificate_id"])
        self.assertTrue(a["certificate_id"].startswith("cov-"))

    def test_counts_are_grounded_in_recorded_runs(self):
        _standard_scenario(self.base)
        cert = self._cert()
        vara = next(r for r in cert["sources"] if r["source_id"] == "AE-vara")
        # 15 recorded runs, all with a proof hash, one CHANGED.
        self.assertEqual(vara["checks_in_period"], 15)
        self.assertEqual(vara["successful_checks"], 15)
        self.assertEqual(vara["changed_count"], 1)
        self.assertEqual(vara["official_url"], "https://www.vara.ae/")

    def test_period_end_before_start_raises(self):
        _standard_scenario(self.base)
        with self.assertRaises(ValueError):
            self._cert(period_start="2026-06-15", period_end="2026-06-01")

    def test_runs_outside_period_are_excluded(self):
        _write_sources(self.base, [{"source_id": "AE-x", "name": "X", "url": "https://x.example/"}])
        runs = [
            _run("AE-x", 5, normalized_hash="a" * 64),   # in period
            {  # out of period (May) — must not be counted
                "source_id": "AE-x", "source_name": "X", "official_url": "https://x.example/",
                "timestamp_utc": "2026-05-20T10:00:00Z", "change_status": "CHANGED",
                "normalized_hash": "b" * 64, "record_type": "heartbeat",
            },
        ]
        _write_runs(self.base, runs)
        cert = self._cert(source_ids=["AE-x"])
        row = cert["sources"][0]
        self.assertEqual(row["checks_in_period"], 1)
        self.assertEqual(row["changed_count"], 0)  # the May CHANGED is excluded

    # ── skipped (circuit-open) cycles are not checks ────────────────────────

    def test_circuit_open_skips_are_not_counted_as_checks(self):
        """A cycle skipped by the circuit breaker issues no HTTP request at
        all. Counting its trail record as a "recorded check" would make the
        certificate assert monitoring work that never happened, and would reset
        the staleness clock for exactly the sources that went dark."""
        _write_sources(
            self.base,
            [{"source_id": "AE-walled", "name": "Walled Source", "url": "https://walled.example/"}],
        )
        runs = [_run("AE-walled", 1)]
        runs += [_skip_run("AE-walled", day) for day in range(2, 15)]
        _write_runs(self.base, runs)

        cert = self._cert()
        row = next(r for r in cert["sources"] if r["source_id"] == "AE-walled")

        self.assertEqual(row["checks_in_period"], 1)
        self.assertEqual(row["skipped_cycles"], 13)
        self.assertEqual(row["quality_drop_count"], 0)
        self.assertTrue(row["first_check_utc"].startswith("2026-06-01"))
        self.assertTrue(row["last_check_utc"].startswith("2026-06-01"))
        self.assertEqual(row["last_check_gap_days"], 14)
        self.assertEqual(cert["summary"]["total_checks"], 1)
        self.assertEqual(cert["summary"]["total_skipped_cycles"], 13)

        # The disclosure must name the skipped cycles and must NOT describe
        # them as checks that recorded an extraction problem.
        self.assertIn("not fetched", row["gap_disclosure"])
        self.assertNotIn("recorded a quality drop", row["gap_disclosure"])
        self.assertIn("trails the end of the period", row["gap_disclosure"])

        md = render_coverage_certificate_markdown(cert)
        self.assertIn("performed 1 recorded check(s)", md)
        self.assertIn("not fetched", md)

    def test_circuit_open_only_source_reports_no_coverage(self):
        """A source that was skipped every cycle has no coverage at all."""
        _write_sources(
            self.base,
            [{"source_id": "AE-dark", "name": "Dark Source", "url": "https://dark.example/"}],
        )
        _write_runs(self.base, [_skip_run("AE-dark", day) for day in range(1, 15)])

        cert = self._cert()
        row = next(r for r in cert["sources"] if r["source_id"] == "AE-dark")
        self.assertEqual(row["checks_in_period"], 0)
        self.assertEqual(row["skipped_cycles"], 14)
        self.assertEqual(row["last_check_utc"], "")
        self.assertEqual(row["continuity_status"], "NO_COVERAGE")
        self.assertEqual(cert["summary"]["total_checks"], 0)

    # ── rendering + exports ─────────────────────────────────────────────────

    def test_month_period_helper(self):
        self.assertEqual(month_period(2026, 6), ("2026-06-01", "2026-06-30"))
        self.assertEqual(month_period(2026, 2), ("2026-02-01", "2026-02-28"))

    def test_html_render_contains_table_and_is_standalone(self):
        _standard_scenario(self.base)
        cert = self._cert()
        html = render_coverage_certificate_html(cert)
        self.assertIn("<table>", html)
        self.assertIn("Coverage Certificate", html)
        self.assertIn(_FULL_DISCLAIMER_MARK, html)

    def test_export_json_and_html_write_files(self):
        _standard_scenario(self.base)
        cert = self._cert()
        json_path = export_coverage_certificate_json(cert, output_path=self.base / "cert.json")
        html_path = export_coverage_certificate_html(cert, output_path=self.base / "cert.html")
        self.assertTrue(json_path.exists())
        self.assertTrue(html_path.exists())
        loaded = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(loaded["certificate_id"], cert["certificate_id"])
        self.assertEqual(loaded["document_type"], "coverage_certificate")

    def test_pdf_falls_back_to_html_when_playwright_unavailable(self):
        _standard_scenario(self.base)
        cert = self._cert()
        # Force the Playwright import inside the function to fail → HTML fallback.
        import unittest.mock as mock

        with mock.patch.dict(sys.modules, {"playwright": None, "playwright.sync_api": None}):
            out = generate_coverage_certificate_pdf(cert, output_path=self.base / "cert.pdf")
        self.assertTrue(out.exists())
        self.assertEqual(out.suffix, ".html")
        self.assertIn(_FULL_DISCLAIMER_MARK, out.read_text(encoding="utf-8"))


class CoverageCertificateContentHashSealTest(unittest.TestCase):
    """The full-document content_hash seal and its public-verifier round-trip.

    certificate_id covers only a fixed subset, so it CANNOT detect an edit to the
    negative-assurance prose or a row's continuity_status/degraded flag. content_hash
    is the whole-document seal that does, and app.public_verify recomputes it.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        _standard_scenario(self.base)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _cert(self):
        return build_coverage_certificate(
            period_start="2026-06-01",
            period_end="2026-06-15",
            client_name="Acme Compliance",
            base_dir=self.base,
            now=_NOW,
        )

    def test_certificate_carries_a_full_document_content_hash(self):
        cert = self._cert()
        self.assertIn("content_hash", cert)
        self.assertTrue(cert["content_hash"].startswith("sha256:"))
        self.assertEqual(len(cert["content_hash"].removeprefix("sha256:")), 64)

    def test_content_hash_is_deterministic_and_excludes_generated_at(self):
        # Re-issuing for the same evidence with a different generated_at seals identically.
        cert_a = self._cert()
        later = datetime(2026, 6, 17, 9, 30, tzinfo=timezone.utc)
        cert_b = build_coverage_certificate(
            period_start="2026-06-01",
            period_end="2026-06-15",
            client_name="Acme Compliance",
            base_dir=self.base,
            now=later,
        )
        self.assertNotEqual(cert_a["generated_at_utc"], cert_b["generated_at_utc"])
        self.assertEqual(cert_a["content_hash"], cert_b["content_hash"])

    def test_genuine_certificate_verifies_via_public_verify(self):
        from app.public_verify import verify_submission

        cert = self._cert()
        result = verify_submission(cert)
        self.assertTrue(result["verified"], result["checks"])
        check = _find_check(result, "certificate_content_hash_self_consistent")
        self.assertEqual(check["status"], "pass")

    def test_altered_negative_assurance_statement_fails_content_hash(self):
        from app.public_verify import verify_submission

        cert = self._cert()
        cert["negative_assurance_statement"] += " (edited after sealing)"
        # certificate_id is unchanged by this edit — only content_hash catches it.
        result = verify_submission(cert)
        self.assertFalse(result["verified"])
        check = _find_check(result, "certificate_content_hash_self_consistent")
        self.assertEqual(check["status"], "fail")
        self.assertIn("altered", check["detail"])

    def test_altered_row_continuity_status_fails_content_hash(self):
        from app.public_verify import verify_submission

        cert = self._cert()
        row = cert["sources"][0]
        # Launder the status to a different value than it genuinely holds.
        row["continuity_status"] = "NO_COVERAGE" if row["continuity_status"] != "NO_COVERAGE" else "CONTINUOUS"
        result = verify_submission(cert)
        self.assertFalse(result["verified"])
        self.assertEqual(
            _find_check(result, "certificate_content_hash_self_consistent")["status"], "fail"
        )

    def test_altered_row_degraded_flag_fails_content_hash(self):
        from app.public_verify import verify_submission

        cert = self._cert()
        # Flip a degraded row's flag to hide a failed/degraded check.
        for row in cert["sources"]:
            if row["degraded"]:
                row["degraded"] = False
                break
        else:
            self.fail("scenario should include a degraded source")
        result = verify_submission(cert)
        self.assertFalse(result["verified"])
        self.assertEqual(
            _find_check(result, "certificate_content_hash_self_consistent")["status"], "fail"
        )

    def test_float_field_is_rejected_before_sealing(self):
        # The seal guard forbids floats: their repr is not byte-reproducible across
        # languages, so an auditor could not recompute the digest. Fail loudly.
        from app.coverage_certificate import _content_hash

        cert = self._cert()
        cert["summary"]["total_checks"] = 30.0  # an int silently turned float
        with self.assertRaises(TypeError):
            _content_hash(cert)

    def test_trail_record_content_hash_is_not_treated_as_certificate(self):
        # A source-run trail record ALSO carries a top-level content_hash (different
        # semantics). The certificate recompute must SKIP it, not falsely fail it.
        from app.public_verify import verify_submission

        trail = {
            "source_id": "AE-x",
            "timestamp_utc": "2026-06-10T00:00:00Z",
            "change_status": "FIRST_SEEN",
            "content_hash": "a" * 64,
            "normalized_hash": "b" * 64,
        }
        result = verify_submission(trail)
        self.assertEqual(
            _find_check(result, "certificate_content_hash_self_consistent")["status"],
            "skipped",
        )


def _find_check(result: dict, name: str) -> dict:
    for check in result["checks"]:
        if check["name"] == name:
            return check
    raise AssertionError(f"check {name!r} not in {[c['name'] for c in result['checks']]}")


if __name__ == "__main__":
    unittest.main()
