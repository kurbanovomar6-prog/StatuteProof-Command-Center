"""Regulator-scope relevance routing gate (buyer #1 DONE-gate).

A customer must be able to scope which regulators they receive. When a
profile declares a non-empty ``regulators`` scope, alerts whose resolved
regulator is not in that scope are excluded outright (authoritative
exclusion, not a score penalty). Empty/absent scope preserves the prior
behavior for backward compatibility.
"""

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.alert_routing import resolve_regulator, score_alert_for_user
from app.profile import (
    ALLOWED_REGULATOR_CODES,
    normalize_regulators,
)


def _routing_profile(regulators=None, markets=None, alert_threshold="MEDIUM"):
    """Minimal routing profile shaped like user_profile_to_routing_profile()."""
    return {
        "client_id": "user_1",
        "user_id": 1,
        "company_name": "Test Co",
        "markets": markets if markets is not None else ["UAE"],
        "industries": [],
        "topics": [],
        "sources": [],
        "custom_sources": [],
        "alert_threshold": alert_threshold,
        "risk_threshold": alert_threshold,
        "regulators": regulators if regulators is not None else [],
    }


def _alert(source_name, source_url, risk_level="HIGH", market="AE", source_id=None):
    return {
        "alert_id": f"draft-{source_name}",
        "source_id": source_id,
        "source_name": source_name,
        "source_url": source_url,
        "url": source_url,
        "risk_level": risk_level,
        "change_type": "REGULATORY_UPDATE",
        "market": market,
        "jurisdiction": market,
        "topics": [],
    }


# Representative real alerts, one per regulator, using production hosts/names.
CBUAE_ALERT = _alert("CBUAE AML/CFT Rulebook", "https://rulebook.centralbank.ae/en/aml")
DFSA_ALERT = _alert("DFSA AML Rulebook Module", "https://dfsaen.thomsonreuters.com/rulebook")
FSRA_ALERT = _alert("ADGM FSRA Rulebook", "https://www.fsra.adgm.com/rulebook")
VARA_ALERT = _alert("VARA Rulebook Revision Updates", "https://rulebooks.vara.ae/rulebook")
SCA_ALERT = _alert("UAE Capital Market Authority (CMA)", "https://www.uaecma.gov.ae/")
FTA_ALERT = _alert("UAE Federal Tax Authority (FTA)", "https://tax.gov.ae/")
DIFC_ALERT = _alert("DIFC Laws and Regulations", "https://www.difc.com/laws")
OTHER_ALERT = _alert("Central Bank of Russia", "https://cbr.ru/press/pr/", market="RU")


class RegulatorResolverTests(unittest.TestCase):
    def test_resolves_cbuae_from_host(self):
        self.assertEqual(resolve_regulator(CBUAE_ALERT), "CBUAE")

    def test_resolves_cbuae_from_rulebook_subdomain(self):
        alert = _alert("Rulebook", "https://rulebook.centralbank.ae/en")
        self.assertEqual(resolve_regulator(alert), "CBUAE")

    def test_resolves_dfsa_from_host(self):
        self.assertEqual(resolve_regulator(DFSA_ALERT), "DFSA")

    def test_resolves_dfsa_from_dfsa_ae(self):
        alert = _alert("DFSA Regulatory Notices", "https://www.dfsa.ae/notices")
        self.assertEqual(resolve_regulator(alert), "DFSA")

    def test_resolves_fsra_from_adgm(self):
        self.assertEqual(resolve_regulator(FSRA_ALERT), "FSRA")

    def test_resolves_fsra_from_adgm_com(self):
        alert = _alert("ADGM FSRA Rules and Regulations", "https://www.adgm.com/rules")
        self.assertEqual(resolve_regulator(alert), "FSRA")

    def test_resolves_vara_from_host(self):
        self.assertEqual(resolve_regulator(VARA_ALERT), "VARA")

    def test_resolves_sca_from_uaecma(self):
        self.assertEqual(resolve_regulator(SCA_ALERT), "SCA")

    def test_resolves_fta_from_tax_gov(self):
        self.assertEqual(resolve_regulator(FTA_ALERT), "FTA")

    def test_resolves_fta_from_mof(self):
        alert = _alert("UAE Ministry of Finance", "https://mof.gov.ae/")
        self.assertEqual(resolve_regulator(alert), "FTA")

    def test_resolves_difc_from_host(self):
        self.assertEqual(resolve_regulator(DIFC_ALERT), "DIFC")

    def test_resolves_other_for_unknown(self):
        self.assertEqual(resolve_regulator(OTHER_ALERT), "OTHER")

    def test_resolves_from_source_id_prefix(self):
        alert = _alert("Some source", "https://example.invalid/", source_id="AE-cbuae-rulebook")
        self.assertEqual(resolve_regulator(alert), "CBUAE")

    def test_resolves_other_when_no_signal(self):
        alert = _alert("Mystery source", "", market="AE")
        self.assertEqual(resolve_regulator(alert), "OTHER")


class RegulatorGateTests(unittest.TestCase):
    def test_vasp_vara_scope_excludes_cbuae_high_alert(self):
        """THE headline gate: VASP scoped to VARA must not receive CBUAE."""
        profile = _routing_profile(regulators=["VARA"])
        result = score_alert_for_user(profile, CBUAE_ALERT)
        self.assertFalse(result["matched"])

    def test_vasp_vara_scope_matches_vara_high_alert(self):
        profile = _routing_profile(regulators=["VARA"])
        result = score_alert_for_user(profile, VARA_ALERT)
        self.assertTrue(result["matched"])

    def test_difc_fintech_scope_receives_dfsa(self):
        profile = _routing_profile(regulators=["DFSA", "DIFC"])
        self.assertTrue(score_alert_for_user(profile, DFSA_ALERT)["matched"])

    def test_difc_fintech_scope_receives_difc(self):
        profile = _routing_profile(regulators=["DFSA", "DIFC"])
        self.assertTrue(score_alert_for_user(profile, DIFC_ALERT)["matched"])

    def test_difc_fintech_scope_excludes_cbuae_and_vara(self):
        profile = _routing_profile(regulators=["DFSA", "DIFC"])
        self.assertFalse(score_alert_for_user(profile, CBUAE_ALERT)["matched"])
        self.assertFalse(score_alert_for_user(profile, VARA_ALERT)["matched"])

    def test_empty_scope_preserves_prior_behavior(self):
        """Empty regulators scope => unchanged (still matches per old logic)."""
        profile = _routing_profile(regulators=[])
        result = score_alert_for_user(profile, CBUAE_ALERT)
        self.assertTrue(result["matched"])

    def test_absent_scope_preserves_prior_behavior(self):
        profile = _routing_profile()
        del profile["regulators"]
        result = score_alert_for_user(profile, CBUAE_ALERT)
        self.assertTrue(result["matched"])

    def test_exclusion_gives_zero_score_and_reason(self):
        profile = _routing_profile(regulators=["VARA"])
        result = score_alert_for_user(profile, CBUAE_ALERT)
        self.assertEqual(result["score"], 0)
        self.assertTrue(any("regulator" in r.lower() for r in result["reasons"]))

    def test_scope_matching_alert_keeps_scoring(self):
        """In-scope alert is not penalized: risk + market still score."""
        profile = _routing_profile(regulators=["VARA"])
        result = score_alert_for_user(profile, VARA_ALERT)
        self.assertGreaterEqual(result["score"], 40)


class EnabledSourceRegulatorCoverageTests(unittest.TestCase):
    """DURABLE FIX regression: every enabled source in the real sources.json
    must resolve to a *real* (non-OTHER) regulator code, and must carry a
    non-blank source_id.

    Why this is the load-bearing test: score_alert_for_user() applies a HARD
    exclusion when a customer scopes to specific regulators and the alert's
    resolved regulator is not in that scope. Any enabled source that resolves
    to OTHER is silently undeliverable to every scoped customer (OTHER is not
    a code a customer can subscribe to). Before this fix, ~23 of 116 enabled
    sources (EOCN sanctions/TFS, Ministry of Economy AML, Dubai Legislation
    Portal, MoJ, DFM, ICP, TDRA, MOCCAE, JAFZA, DMCC, ...) fell into OTHER and
    were dropped. This test fails the moment a new enabled source lacks
    taxonomy coverage, forcing the code/host/name rule to be added.
    """

    @staticmethod
    def _enabled_sources():
        from app.source_intake import load_sources_json

        return [s for s in load_sources_json() if s.get("enabled")]

    @staticmethod
    def _alert_from_source(source):
        """Shape a source row the way the routing pipeline shapes an alert.

        make_source_id mirrors how alert drafts derive their source_id at
        monitor time, so the resolver sees the same signals in production.
        """
        from app.source_runs import make_source_id

        source_id = source.get("source_id") or make_source_id(source)
        url = source.get("url")
        return {
            "source_id": source_id,
            "source_url": url,
            "url": url,
            "source_name": source.get("name"),
        }

    def test_every_enabled_source_resolves_to_non_other(self):
        enabled = self._enabled_sources()
        self.assertGreater(len(enabled), 0, "expected enabled sources in sources.json")
        offenders = []
        for source in enabled:
            code = resolve_regulator(self._alert_from_source(source))
            if code == "OTHER":
                offenders.append((source.get("source_id"), source.get("name"), source.get("url")))
        self.assertEqual(
            offenders,
            [],
            "enabled sources resolving to OTHER are silently undeliverable to "
            f"scoped customers; add taxonomy coverage: {offenders}",
        )

    def test_every_enabled_source_resolved_code_is_scopable(self):
        """A resolved code that is not in ALLOWED_REGULATOR_CODES could never
        match a customer's normalized scope, so it would be as bad as OTHER."""
        for source in self._enabled_sources():
            code = resolve_regulator(self._alert_from_source(source))
            self.assertIn(code, ALLOWED_REGULATOR_CODES, source.get("name"))

    def test_every_enabled_source_has_non_blank_source_id(self):
        blanks = [
            s.get("name")
            for s in self._enabled_sources()
            if not (s.get("source_id") and str(s.get("source_id")).strip())
        ]
        self.assertEqual(blanks, [], f"enabled sources with blank source_id: {blanks}")


class NonPrudentialRegulatorResolverTests(unittest.TestCase):
    """Targeted resolution checks for the newly added non-prudential codes,
    so the taxonomy coverage is pinned regardless of sources.json churn."""

    def test_eocn_from_host(self):
        self.assertEqual(
            resolve_regulator(_alert("EOCN News", "https://www.eocn.gov.ae/en-us/news")),
            "EOCN",
        )

    def test_eocn_uaeiec_mirror_shares_code(self):
        self.assertEqual(
            resolve_regulator(_alert("UAEIEC News", "https://www.uaeiec.gov.ae/en-us/news")),
            "EOCN",
        )

    def test_ministry_of_economy_from_host(self):
        self.assertEqual(
            resolve_regulator(_alert("Ministry of Economy — AML", "https://www.moet.gov.ae/aml")),
            "MOEC",
        )

    def test_dubai_legislation_portal_from_host(self):
        self.assertEqual(
            resolve_regulator(_alert("DLP", "https://dlp.dubai.gov.ae/en/Pages/LegislationSearch.aspx")),
            "DLP",
        )

    def test_ministry_of_justice_from_host(self):
        self.assertEqual(
            resolve_regulator(_alert("MoJ News", "https://www.moj.gov.ae/en/media-center/news.aspx")),
            "MOJ",
        )

    def test_dfm_from_host(self):
        self.assertEqual(
            resolve_regulator(_alert("DFM Circulars", "https://www.dfm.ae/the-exchange/regulation/circulars")),
            "DFM",
        )

    def test_free_zones_and_authorities_from_host(self):
        cases = {
            "https://icp.gov.ae/en/media-center/": "ICP",
            "https://tdra.gov.ae/en/media": "TDRA",
            "https://www.moccae.gov.ae/en/media-center": "MOCCAE",
            "https://www.jafza.ae/resource-centre/media/": "JAFZA",
            "https://dmcc.ae/latest-news": "DMCC",
        }
        for url, expected in cases.items():
            self.assertEqual(resolve_regulator(_alert("X", url)), expected, url)

    def test_dfm_name_token_does_not_false_positive(self):
        """A bare 'dfm' substring (e.g. 'ARDFM Kazakhstan') must NOT resolve to
        DFM; only the dfm.ae host or an ae-dfm- source_id is a DFM signal."""
        self.assertEqual(
            resolve_regulator(
                {"source_id": "KZ-ardfm-financial-market", "source_name": "ARDFM Kazakhstan", "url": "https://ardfm.kz/"}
            ),
            "OTHER",
        )

    def test_new_codes_are_scopable(self):
        for code in ("EOCN", "MOEC", "DLP", "MOJ", "DFM", "ICP", "TDRA", "MOCCAE", "JAFZA", "DMCC"):
            self.assertIn(code, ALLOWED_REGULATOR_CODES, code)

    def test_scoped_customer_receives_eocn_and_excludes_cbuae(self):
        """End-to-end: a sanctions-focused customer scoped to EOCN receives an
        EOCN alert and is not spammed with an out-of-scope CBUAE alert."""
        profile = _routing_profile(regulators=["EOCN"])
        eocn_alert = _alert("EOCN Sanctions Update", "https://www.eocn.gov.ae/en-us/news")
        self.assertTrue(score_alert_for_user(profile, eocn_alert)["matched"])
        self.assertFalse(score_alert_for_user(profile, CBUAE_ALERT)["matched"])


class ProfileRegulatorFieldTests(unittest.TestCase):
    def test_allowed_codes_cover_seven(self):
        for code in ("CBUAE", "DFSA", "FSRA", "VARA", "SCA", "FTA", "OTHER"):
            self.assertIn(code, ALLOWED_REGULATOR_CODES)

    def test_difc_is_allowed(self):
        self.assertIn("DIFC", ALLOWED_REGULATOR_CODES)

    def test_normalize_uppercases_and_filters(self):
        self.assertEqual(normalize_regulators(["vara", "dfsa"]), ["VARA", "DFSA"])

    def test_normalize_drops_unknown_codes(self):
        self.assertEqual(normalize_regulators(["VARA", "NONSENSE"]), ["VARA"])

    def test_normalize_dedupes(self):
        self.assertEqual(normalize_regulators(["VARA", "vara"]), ["VARA"])

    def test_normalize_empty_returns_empty(self):
        self.assertEqual(normalize_regulators([]), [])
        self.assertEqual(normalize_regulators(None), [])


import contextlib


@contextlib.contextmanager
def isolated_profile_module():
    """Reload app.profile against an isolated DB path, then restore.

    Yields the reloaded app.profile module so persistence tests never touch
    the shared DB.
    """
    import importlib
    import os
    import tempfile

    import app.config
    import app.db
    import app.profile

    base = tempfile.mkdtemp()
    os.environ["STATUTEPROOF_BASE_DIR"] = base
    os.environ["REGRADAR_DB_PATH"] = os.path.join(base, "r.db")
    importlib.reload(app.config)
    importlib.reload(app.db)
    importlib.reload(app.profile)
    try:
        yield app.profile
    finally:
        os.environ.pop("STATUTEPROOF_BASE_DIR", None)
        os.environ.pop("REGRADAR_DB_PATH", None)
        importlib.reload(app.config)
        importlib.reload(app.db)
        importlib.reload(app.profile)


class ProfilePersistenceTests(unittest.TestCase):
    def test_profile_persists_and_returns_regulators(self):
        with isolated_profile_module() as profile_mod:
            profile_mod.get_or_create_profile(4242)
            updated = profile_mod.update_profile(4242, {"regulators": ["vara", "dfsa"]})
            self.assertEqual(updated["regulators"], ["VARA", "DFSA"])
            reread = profile_mod.get_or_create_profile(4242)
            self.assertEqual(reread["regulators"], ["VARA", "DFSA"])


class RegulatorsFailClosedTests(unittest.TestCase):
    """Regression: a non-empty-but-all-invalid scope must NOT silently
    un-scope the customer (HIGH fail-open found by verifier)."""

    def test_all_invalid_codes_raise_and_do_not_store(self):
        with isolated_profile_module() as profile_mod:
            profile_mod.get_or_create_profile(5151)
            profile_mod.update_profile(5151, {"regulators": ["VARA"]})
            # ["TYPO"] is non-empty but yields no valid codes -> reject.
            with self.assertRaises(ValueError):
                profile_mod.update_profile(5151, {"regulators": ["TYPO"]})
            # Prior valid scope must be untouched, NOT reset to [] (= all).
            reread = profile_mod.get_or_create_profile(5151)
            self.assertEqual(reread["regulators"], ["VARA"])

    def test_typo_scope_customer_still_excludes_out_of_scope_alert(self):
        """End-to-end: after the rejected ["TYPO"] update, the customer's
        prior VARA scope still excludes a CBUAE alert (no silent un-scoping)."""
        with isolated_profile_module() as profile_mod:
            profile_mod.get_or_create_profile(5252)
            profile_mod.update_profile(5252, {"regulators": ["VARA"]})
            with self.assertRaises(ValueError):
                profile_mod.update_profile(5252, {"regulators": ["TYPO"]})
            routing = profile_mod.get_or_create_profile(5252)
            profile = _routing_profile(regulators=routing["regulators"])
            self.assertEqual(profile["regulators"], ["VARA"])
            self.assertFalse(score_alert_for_user(profile, CBUAE_ALERT)["matched"])

    def test_mixed_valid_and_invalid_keeps_valid(self):
        with isolated_profile_module() as profile_mod:
            profile_mod.get_or_create_profile(5353)
            updated = profile_mod.update_profile(5353, {"regulators": ["VARA", "TYPO"]})
            self.assertEqual(updated["regulators"], ["VARA"])

    def test_explicit_empty_still_means_all(self):
        with isolated_profile_module() as profile_mod:
            profile_mod.get_or_create_profile(5454)
            profile_mod.update_profile(5454, {"regulators": ["VARA"]})
            # Explicit [] clears the scope back to "all" (backward compatible).
            updated = profile_mod.update_profile(5454, {"regulators": []})
            self.assertEqual(updated["regulators"], [])


if __name__ == "__main__":
    unittest.main()
