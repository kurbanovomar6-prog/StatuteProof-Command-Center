"""Tests for the negative-assurance monitoring digest (SILENCE-WITH-PROOF).

These lock in the legal boundary that IS the whole risk of this feature:

  * counts are grounded in real recorded runs / sealed records (nothing invented);
  * a no-change source is framed as "no change DETECTED", never "compliant" /
    "no action needed" / "all clear";
  * a source that FAILED to check is disclosed as a GAP and is never folded into
    the clean no-change ("all clear") list;
  * every captured change links to its sealed evidence-record hash;
  * every rendered string passes the forbidden-claims guard; and
  * an empty period yields an honest empty digest, not a fabricated one.
"""

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.assurance_digest import (
    _ASSURANCE_FORBIDDEN,
    build_assurance_digest,
    find_forbidden_assurance_claims,
    render_assurance_digest_email_text,
    render_assurance_digest_markdown,
)
from app.legal_safety import FORBIDDEN_PHRASES, find_forbidden_claims

_NOW = datetime(2026, 6, 8, tzinfo=timezone.utc)
_FULL_DISCLAIMER_MARK = "do not constitute"  # unique fragment of the full disclaimer
_SHORT_DISCLAIMER = "For monitoring information only. Not legal advice and not a guarantee of compliance."


def _write_enabled_sources(base: Path, rows: list[dict]) -> None:
    (base / "sources.json").write_text(json.dumps(rows), encoding="utf-8")


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


def _write_sealed_record(
    base: Path,
    *,
    source_id: str,
    run_id: str,
    timestamp: str,
    status: str = "CHANGED",
    record_hash: str | None = "sha256:" + "d" * 64,
    record_status: str = "complete",
    regulator: str = "VARA",
    summary: str = "Saved snapshot changed against the previous normalized content.",
) -> dict:
    """Write a minimal canonical evidence-record.json (as the pipeline would seal)."""
    record: dict = {
        "schema_version": "2.0",
        "record_id": f"evr_{source_id}_{run_id}",
        "record_status": record_status,
        "source": {
            "source_id": source_id,
            "source_name": f"{source_id} name",
            "official_url": f"https://official.example/{source_id}",
            "regulator": regulator,
        },
        "run": {"run_id": run_id, "timestamp": timestamp, "status": status},
        "change": {"summary": summary, "lines_added": 3, "lines_removed": 1},
        "integrity": {"verified_at": timestamp},
    }
    if record_hash is not None:
        record["record_hash"] = record_hash
    path = base / "evidence" / regulator.lower() / source_id / run_id / "evidence-record.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, sort_keys=True), encoding="utf-8")
    return record


class AssuranceDigestTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _standard(self) -> None:
        """VARA (one sealed change), CBUAE (continuous no-change), GAP (checked once + FAILED)."""
        _write_enabled_sources(
            self.base,
            [
                {"source_id": "AE-vara", "name": "VARA Rulebook", "url": "https://www.vara.ae/",
                 "jurisdiction": "AE", "category": "financial_regulator", "enabled": True},
                {"source_id": "AE-cbuae", "name": "CBUAE Rulebook", "url": "https://www.cbuae.gov.ae/",
                 "jurisdiction": "AE", "category": "financial_regulator", "enabled": True},
                {"source_id": "AE-gap", "name": "Gappy Source", "url": "https://gap.example/",
                 "jurisdiction": "AE", "category": "financial_regulator", "enabled": True},
            ],
        )
        runs: list[dict] = []
        for d in range(1, 8):
            runs.append(_run("AE-vara", d, change_status="CHANGED" if d == 3 else "UNCHANGED",
                             normalized_hash=("c" * 64 if d == 3 else "a" * 64)))
        for d in range(1, 8):
            runs.append(_run("AE-cbuae", d))
        runs.append(_run("AE-gap", 1))
        runs.append(_run("AE-gap", 5, change_status="FAILED", normalized_hash=None, error="HTTP 503 from source"))
        _write_runs(self.base, runs)
        _write_sealed_record(self.base, source_id="AE-vara", run_id="run3",
                             timestamp="2026-06-03T10:00:00Z", status="CHANGED", regulator="VARA")

    def _digest(self, **kwargs):
        params = dict(
            period_start="2026-06-01",
            period_end="2026-06-07",
            client_name="Acme Compliance",
            base_dir=self.base,
            now=_NOW,
        )
        params.update(kwargs)
        return build_assurance_digest(**params)

    # ── counts grounded in real recorded runs ───────────────────────────────

    def test_counts_match_recorded_runs(self):
        self._standard()
        d = self._digest()
        s = d["summary"]
        self.assertEqual(s["sources_monitored"], 3)
        self.assertEqual(s["sources_checked"], 3)
        # 7 (vara) + 7 (cbuae) + 2 (gap) recorded checks.
        self.assertEqual(s["total_checks"], 16)
        self.assertEqual(s["sources_with_detected_change"], 1)
        # Only CBUAE is a clean continuous no-change source (VARA changed, GAP is gappy).
        self.assertEqual(s["sources_no_change_detected"], 1)
        self.assertEqual(s["sources_with_gaps"], 1)
        self.assertEqual(s["sources_degraded"], 1)

    # ── no-change is DETECTION, not compliance/no-action ─────────────────────

    def test_no_change_framed_as_detection_not_compliance(self):
        self._standard()
        d = self._digest()
        ids = [r["source_id"] for r in d["sources_no_change_detected"]]
        self.assertIn("AE-cbuae", ids)
        md = render_assurance_digest_markdown(d)
        body = md.split("**Disclaimer:**")[0]
        # It says "no change ... detected", bounded to detection.
        self.assertIn("no change was detected", body.lower())
        # It NEVER says any of these safety/compliance claims.
        for banned in (
            "you are compliant", "no action needed", "all clear",
            "no changes occurred", "nothing to do", "you're covered",
        ):
            self.assertNotIn(banned, body.lower())

    def test_statement_carries_no_change_detection_language(self):
        self._standard()
        d = self._digest()
        statement = d["assurance_statement"].lower()
        self.assertIn("no change was detected", statement)
        self.assertIn("monitoring activity", statement)
        # No truth-claim / safety phrasing.
        self.assertNotIn("no changes occurred", statement)
        self.assertNotIn("you are compliant", statement)

    # ── bounded audit-register negative-assurance form ───────────────────────

    def test_statement_uses_bounded_audit_register_form(self):
        # The coverage sentence must be the bounded auditor's negative-assurance
        # register form: period + N sources + regulators, then the DETECTION-
        # bounded "no change ... other than the items listed below" clause.
        self._standard()
        d = self._digest()
        statement = d["assurance_statement"]
        # Period is bounded explicitly with both dates.
        self.assertIn("Between 2026-06-01 and 2026-06-07", statement)
        # Count of monitored sources is named.
        self.assertIn("monitored 3 source(s)", statement)
        # Regulators the sources fall under are named ("across ...").
        self.assertIn("across ", statement)
        # The negative-assurance clause is bounded to detection and to the items
        # listed below — never "nothing changed" / "you are compliant".
        self.assertIn(
            "no change was detected in the monitored sources other than the items listed below",
            statement,
        )

    def test_statement_names_resolved_regulators_not_raw_other(self):
        self._standard()
        d = self._digest()
        phrase = d["coverage_scope_regulators"]
        # Real regulator codes are named; the unclassifiable "Gappy Source" is
        # summarised, never shown as the literal resolver bucket "OTHER".
        self.assertIn("CBUAE", phrase)
        self.assertIn("VARA", phrase)
        self.assertNotIn("OTHER", phrase)
        self.assertIn("other monitored official sources", phrase)
        self.assertIn(phrase, d["assurance_statement"])

    def test_statement_single_day_period_uses_on_date(self):
        self._standard()
        d = self._digest(period_start="2026-06-03", period_end="2026-06-03")
        statement = d["assurance_statement"]
        self.assertIn("On 2026-06-03", statement)
        self.assertNotIn("Between", statement)

    # ── failed check disclosed as a GAP, never "all clear" ───────────────────

    def test_failed_source_is_gap_never_folded_into_no_change(self):
        self._standard()
        d = self._digest()
        no_change_ids = {r["source_id"] for r in d["sources_no_change_detected"]}
        gap_ids = {r["source_id"] for r in d["gaps_and_degraded"]}
        self.assertNotIn("AE-gap", no_change_ids, "a failed/gappy source must not be 'all clear'")
        self.assertIn("AE-gap", gap_ids)
        gap = next(r for r in d["gaps_and_degraded"] if r["source_id"] == "AE-gap")
        self.assertTrue(gap["degraded"])
        self.assertEqual(gap["failed_count"], 1)
        self.assertGreater(gap["gap_days"], 0)
        # And it is rendered in the disclosed gaps section.
        md = render_assurance_digest_markdown(d)
        self.assertIn("Gappy Source", md)
        self.assertIn("Gaps and degraded checks (disclosed)", md)

    def test_never_checked_source_is_gap_not_no_change(self):
        # A configured (enabled) source that never ran must surface as NO_COVERAGE
        # in the gaps section, never as no-change.
        _write_enabled_sources(
            self.base,
            [
                {"source_id": "AE-live", "name": "Live", "url": "https://live.example/",
                 "jurisdiction": "AE", "category": "financial_regulator", "enabled": True},
                {"source_id": "AE-dark", "name": "Dark", "url": "https://dark.example/",
                 "jurisdiction": "AE", "category": "financial_regulator", "enabled": True},
            ],
        )
        _write_runs(self.base, [_run("AE-live", d) for d in range(1, 8)])
        d = self._digest()
        no_change_ids = {r["source_id"] for r in d["sources_no_change_detected"]}
        gap_ids = {r["source_id"] for r in d["gaps_and_degraded"]}
        self.assertNotIn("AE-dark", no_change_ids)
        self.assertIn("AE-dark", gap_ids)
        self.assertGreaterEqual(d["summary"]["sources_no_coverage"], 1)

    # ── changes link to their sealed record hashes ───────────────────────────

    def test_captured_changes_link_to_sealed_record_hash(self):
        self._standard()
        d = self._digest()
        sealed = d["changes_captured_and_sealed"]
        self.assertEqual(len(sealed), 1)
        change = sealed[0]
        self.assertEqual(change["source_id"], "AE-vara")
        self.assertEqual(change["record_id"], "evr_AE-vara_run3")
        self.assertEqual(change["record_hash"], "sha256:" + "d" * 64)
        self.assertTrue(change["record_hash_prefix"].startswith("sha256:"))
        self.assertTrue(change["record_path"].endswith("evidence-record.json"))
        self.assertEqual(change["verification"]["record_hash"], "sha256:" + "d" * 64)
        # The hash is rendered so a recipient can verify it.
        md = render_assurance_digest_markdown(d)
        self.assertIn("evr_AE-vara_run3", md)
        self.assertIn(change["record_hash_prefix"], md)

    def test_unsealed_record_not_counted_as_captured_change(self):
        # A record with no record_hash (not sealed) or record_status != complete
        # must NOT count as a captured-and-sealed change.
        self._standard()
        _write_sealed_record(self.base, source_id="AE-cbuae", run_id="runX",
                             timestamp="2026-06-04T10:00:00Z", status="CHANGED",
                             record_hash=None, regulator="CBUAE")
        _write_sealed_record(self.base, source_id="AE-cbuae", run_id="runY",
                             timestamp="2026-06-04T11:00:00Z", status="CHANGED",
                             record_status="pending", regulator="CBUAE")
        d = self._digest()
        ids = {c["record_id"] for c in d["changes_captured_and_sealed"]}
        self.assertNotIn("evr_AE-cbuae_runX", ids)
        self.assertNotIn("evr_AE-cbuae_runY", ids)
        self.assertEqual(d["summary"]["changes_captured_and_sealed"], 1)

    def test_first_seen_baseline_not_counted_as_change(self):
        self._standard()
        _write_sealed_record(self.base, source_id="AE-cbuae", run_id="seed",
                             timestamp="2026-06-02T10:00:00Z", status="FIRST_SEEN",
                             regulator="CBUAE")
        d = self._digest()
        ids = {c["record_id"] for c in d["changes_captured_and_sealed"]}
        self.assertNotIn("evr_AE-cbuae_seed", ids)

    def test_sealed_record_outside_period_excluded(self):
        self._standard()
        _write_sealed_record(self.base, source_id="AE-vara", run_id="may",
                             timestamp="2026-05-20T10:00:00Z", status="CHANGED", regulator="VARA")
        d = self._digest()
        ids = {c["record_id"] for c in d["changes_captured_and_sealed"]}
        self.assertNotIn("evr_AE-vara_may", ids)

    def test_sealed_record_out_of_scope_excluded(self):
        # A sealed change for a source NOT in the reported scope must not leak in.
        self._standard()
        _write_sealed_record(self.base, source_id="AE-other-tenant", run_id="r",
                             timestamp="2026-06-03T10:00:00Z", status="CHANGED", regulator="DFSA")
        d = self._digest(source_ids=["AE-vara"])
        ids = {c["record_id"] for c in d["changes_captured_and_sealed"]}
        self.assertNotIn("evr_AE-other-tenant_r", ids)

    # ── every rendered string passes the forbidden-claims guard ──────────────

    def test_rendered_strings_pass_forbidden_guard(self):
        self._standard()
        d = self._digest()
        md = render_assurance_digest_markdown(d)
        email = render_assurance_digest_email_text(d)
        # Product-wide guard (the mandated one), content section before the vetted disclaimer.
        md_body = md.split("**Disclaimer:**")[0]
        email_body = email.split("Disclaimer:")[0]
        self.assertEqual(find_forbidden_claims(md_body), [])
        self.assertEqual(find_forbidden_claims(email_body), [])
        # Digest superset guard over the individual authored strings.
        self.assertEqual(find_forbidden_assurance_claims(d["assurance_statement"]), [])
        self.assertEqual(find_forbidden_assurance_claims(d["verification"]["note"]), [])
        # The guard is a strict superset of the product ban list (reuse, not fork).
        self.assertTrue({p.lower() for p in FORBIDDEN_PHRASES}.issubset(set(_ASSURANCE_FORBIDDEN)))

    def test_render_raises_if_forbidden_phrase_planted(self):
        self._standard()
        d = self._digest()
        d["assurance_statement"] = "This confirms you are compliant and no action needed."
        with self.assertRaises(ValueError):
            render_assurance_digest_markdown(d)

    def test_build_fails_closed_on_forbidden_summary_in_sealed_record(self):
        # A sealed record's change.summary is free text sourced OUTSIDE this module
        # and is not scanned at write time. build_assurance_digest must fail closed
        # on it — the raw dict is always returned, so it must be provably clean.
        self._standard()
        _write_sealed_record(
            self.base, source_id="AE-cbuae", run_id="badsum",
            timestamp="2026-06-04T10:00:00Z", status="CHANGED", regulator="CBUAE",
            summary="This update means you are compliant and no action needed.",
        )
        with self.assertRaises(ValueError):
            self._digest()

    def test_build_fails_closed_on_forbidden_source_name(self):
        # A custom source name is user free text; if a banned phrase reaches a
        # rendered field it must fail closed at build, not leak into the raw dict.
        self._standard()
        _write_sealed_record(
            self.base, source_id="AE-vara", run_id="badname",
            timestamp="2026-06-04T10:00:00Z", status="CHANGED", regulator="VARA",
        )
        # Overwrite the just-written record with a poisoned source_name.
        rec_path = self.base / "evidence" / "vara" / "AE-vara" / "badname" / "evidence-record.json"
        rec = json.loads(rec_path.read_text())
        rec["source"]["source_name"] = "We guarantee compliance Ltd"
        rec_path.write_text(json.dumps(rec))
        with self.assertRaises(ValueError):
            self._digest()

    def test_raw_digest_is_scan_clean_without_rendering(self):
        # The raw dict is returned by the API regardless of format; every authored
        # string in it (not just the two headline strings) must be clean.
        self._standard()
        d = self._digest()

        def _walk(v):
            if isinstance(v, str):
                yield v
            elif isinstance(v, dict):
                for k, val in v.items():
                    if k in ("disclaimer", "disclaimer_short", "disclaimer_short_legacy"):
                        continue
                    yield from _walk(val)
            elif isinstance(v, (list, tuple)):
                for item in v:
                    yield from _walk(item)

        for s in _walk(d):
            self.assertEqual(find_forbidden_assurance_claims(s), [], s)

    # ── explicit-empty scope is honest, never a global fallback (tenancy) ─────

    def test_explicit_empty_scope_is_empty_not_global(self):
        # Passing an explicit empty scope must yield an empty digest even when the
        # period has runs — it must NEVER widen to the global default source set.
        self._standard()
        d = self._digest(source_ids=[])
        self.assertEqual(d["summary"]["sources_monitored"], 0)
        self.assertEqual(d["summary"]["total_checks"], 0)
        self.assertEqual(d["sources_no_change_detected"], [])
        self.assertEqual(d["gaps_and_degraded"], [])
        self.assertEqual(d["changes_captured_and_sealed"], [])
        # Still legally-safe and carries the full + short disclaimer.
        self.assertIn(_FULL_DISCLAIMER_MARK, d["disclaimer"])
        self.assertEqual(d["disclaimer_short"], _SHORT_DISCLAIMER)
        md = render_assurance_digest_markdown(d)
        self.assertEqual(find_forbidden_claims(md.split("**Disclaimer:**")[0]), [])

    def test_carries_full_and_short_disclaimer_verbatim(self):
        self._standard()
        d = self._digest()
        self.assertEqual(d["disclaimer_short"], _SHORT_DISCLAIMER)
        self.assertIn(_FULL_DISCLAIMER_MARK, d["disclaimer"])
        md = render_assurance_digest_markdown(d)
        self.assertIn(_SHORT_DISCLAIMER, md)
        self.assertIn(_FULL_DISCLAIMER_MARK, md)
        email = render_assurance_digest_email_text(d)
        self.assertIn(_SHORT_DISCLAIMER, email)

    # ── empty period → honest empty digest ───────────────────────────────────

    def test_empty_period_is_honest_not_fabricated(self):
        self._standard()
        d = self._digest(period_start="2020-01-01", period_end="2020-01-07")
        s = d["summary"]
        self.assertEqual(s["total_checks"], 0)
        self.assertEqual(s["changes_captured_and_sealed"], 0)
        self.assertEqual(d["changes_captured_and_sealed"], [])
        self.assertEqual(d["sources_no_change_detected"], [])
        # The statement must be honest about the empty period, not "all clear".
        statement = d["assurance_statement"].lower()
        self.assertIn("no recorded monitoring checks", statement)
        for banned in ("all clear", "no action needed", "you are compliant"):
            self.assertNotIn(banned, statement)
        md = render_assurance_digest_markdown(d)
        self.assertIn(_FULL_DISCLAIMER_MARK, md)
        self.assertEqual(find_forbidden_claims(md.split("**Disclaimer:**")[0]), [])

    def test_no_files_at_all_does_not_raise(self):
        d = build_assurance_digest(
            period_start="2026-06-01", period_end="2026-06-07", base_dir=self.base, now=_NOW
        )
        self.assertEqual(d["summary"]["sources_monitored"], 0)
        self.assertEqual(d["changes_captured_and_sealed"], [])
        # Still legally-safe and renderable.
        md = render_assurance_digest_markdown(d)
        self.assertIn(_SHORT_DISCLAIMER, md)

    # ── determinism ──────────────────────────────────────────────────────────

    def test_digest_id_deterministic_for_same_evidence(self):
        self._standard()
        a = self._digest(now=datetime(2026, 6, 8, tzinfo=timezone.utc))
        b = self._digest(now=datetime(2026, 7, 1, tzinfo=timezone.utc))
        self.assertEqual(a["digest_id"], b["digest_id"])
        self.assertTrue(a["digest_id"].startswith("asr-"))

    def test_period_end_before_start_raises(self):
        self._standard()
        with self.assertRaises(ValueError):
            self._digest(period_start="2026-06-07", period_end="2026-06-01")


if __name__ == "__main__":
    unittest.main()
