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


if __name__ == "__main__":
    unittest.main()
