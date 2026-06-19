import os
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.api import _session_cookie_secure_for_host
from app.plan import _build_state


class SessionCookieSecurityTests(unittest.TestCase):
    def tearDown(self):
        os.environ.pop("STATUTEPROOF_COOKIE_SECURE", None)

    def test_localhost_cookie_is_not_secure_by_default(self):
        os.environ.pop("STATUTEPROOF_COOKIE_SECURE", None)

        self.assertFalse(_session_cookie_secure_for_host("localhost:5173"))
        self.assertFalse(_session_cookie_secure_for_host("127.0.0.1:5001"))
        self.assertFalse(_session_cookie_secure_for_host("[::1]:5001"))

    def test_non_local_cookie_is_secure_by_default(self):
        os.environ.pop("STATUTEPROOF_COOKIE_SECURE", None)

        self.assertTrue(_session_cookie_secure_for_host("statuteproof.com"))

    def test_cookie_secure_env_override_wins(self):
        os.environ["STATUTEPROOF_COOKIE_SECURE"] = "true"
        self.assertTrue(_session_cookie_secure_for_host("localhost:5173"))

        os.environ["STATUTEPROOF_COOKIE_SECURE"] = "false"
        self.assertFalse(_session_cookie_secure_for_host("statuteproof.com"))


class PlanIntentContractTests(unittest.TestCase):
    def test_paid_plan_request_is_pending_manual_activation(self):
        state = _build_state("professional", None, "2026-06-14T12:00:00+00:00")

        self.assertEqual(state["plan_name"], "professional")
        self.assertEqual(state["requested_plan"], "professional")
        self.assertEqual(state["requested_plan_display"], "UAE Monitor")
        self.assertEqual(state["active_plan_name"], "evidence_preview")
        self.assertEqual(state["active_plan_display"], "Source Readiness Review")
        self.assertEqual(state["status"], "pending_manual_activation")
        self.assertTrue(state["manual_activation_required"])
        self.assertEqual(state["active_capabilities"]["source_limit"], 0)
        self.assertEqual(state["active_capabilities"]["custom_sources"], 0)
        self.assertEqual(state["requested_capabilities"]["source_limit"], 225)
        self.assertEqual(state["requested_capabilities"]["custom_sources"], 2)
        self.assertTrue(state["requested_capabilities"]["audit_export"])
        self.assertTrue(state["requested_capabilities"]["pdf_export"])

    def test_evidence_preview_has_no_requested_plan(self):
        state = _build_state("evidence_preview", None, None)

        self.assertEqual(state["plan_name"], "evidence_preview")
        self.assertIsNone(state["requested_plan"])
        self.assertEqual(state["active_plan_name"], "evidence_preview")
        self.assertEqual(state["status"], "evidence_preview")
        self.assertFalse(state["manual_activation_required"])


if __name__ == "__main__":
    unittest.main()
