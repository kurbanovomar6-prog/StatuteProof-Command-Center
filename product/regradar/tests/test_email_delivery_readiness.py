import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.email_delivery import (
    build_email_status_response,
    deliver_weekly_brief_provider_ready,
    deliver_weekly_brief_test_mode,
    validate_email_provider_config,
)
from app.evidence_assessment import LEGAL_DISCLAIMER
from app.weekly_brief import build_weekly_brief


def _brief() -> dict:
    return build_weekly_brief(
        client_profile={"client_id": "pilot", "company_name": "Pilot Client"},
        market="AE",
        start=__import__("datetime").datetime(2026, 6, 9, tzinfo=__import__("datetime").timezone.utc),
        end=__import__("datetime").datetime(2026, 6, 16, tzinfo=__import__("datetime").timezone.utc),
        alerts=[],
    )


class EmailDeliveryReadinessTests(unittest.TestCase):
    def test_default_provider_config_is_local_outbox_test_mode(self):
        config = validate_email_provider_config(env={})

        self.assertEqual(config["provider"], "local_outbox")
        self.assertEqual(config["status"], "test_mode")
        self.assertTrue(config["provider_configured"])
        self.assertFalse(config["send_enabled"])
        self.assertEqual(config["missing_config"], [])
        self.assertIn("local outbox", config["customer_safe_status"].lower())
        self.assertNotIn("password", json.dumps(config).lower())

    def test_smtp_missing_password_returns_configuration_required(self):
        config = validate_email_provider_config(env={
            "STATUTEPROOF_EMAIL_PROVIDER": "smtp",
            "STATUTEPROOF_EMAIL_FROM": "briefs@statuteproof.example",
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "smtp-user",
        })

        self.assertEqual(config["provider"], "smtp")
        self.assertEqual(config["status"], "configuration_required")
        self.assertFalse(config["provider_configured"])
        self.assertIn("SMTP_PASSWORD", config["missing_config"])
        self.assertNotIn("smtp-user", json.dumps(config))

    def test_postmark_missing_token_returns_configuration_required(self):
        config = validate_email_provider_config(env={
            "STATUTEPROOF_EMAIL_PROVIDER": "postmark",
            "STATUTEPROOF_EMAIL_FROM": "briefs@statuteproof.example",
        })

        self.assertEqual(config["status"], "configuration_required")
        self.assertIn("POSTMARK_SERVER_TOKEN", config["missing_config"])

    def test_sendgrid_missing_token_returns_configuration_required(self):
        config = validate_email_provider_config(env={
            "STATUTEPROOF_EMAIL_PROVIDER": "sendgrid",
            "STATUTEPROOF_EMAIL_FROM": "briefs@statuteproof.example",
        })

        self.assertEqual(config["status"], "configuration_required")
        self.assertIn("SENDGRID_API_KEY", config["missing_config"])

    def test_configured_provider_with_send_disabled_is_ready_but_disabled(self):
        config = validate_email_provider_config(env={
            "STATUTEPROOF_EMAIL_PROVIDER": "smtp",
            "STATUTEPROOF_EMAIL_FROM": "briefs@statuteproof.example",
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "smtp-user",
            "SMTP_PASSWORD": "secret-password",
            "STATUTEPROOF_EMAIL_SEND_ENABLED": "false",
        })

        self.assertEqual(config["provider"], "smtp")
        self.assertEqual(config["status"], "ready_but_disabled")
        self.assertTrue(config["provider_configured"])
        self.assertFalse(config["send_enabled"])
        self.assertNotIn("secret-password", json.dumps(config))

    def test_provider_delivery_does_not_send_when_disabled_and_records_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            result = deliver_weekly_brief_provider_ready(
                _brief(),
                recipient_email="mlro@example.com",
                env={
                    "STATUTEPROOF_EMAIL_PROVIDER": "sendgrid",
                    "STATUTEPROOF_EMAIL_FROM": "briefs@statuteproof.example",
                    "SENDGRID_API_KEY": "secret-token",
                    "STATUTEPROOF_EMAIL_SEND_ENABLED": "false",
                },
                base_dir=base,
            )

            self.assertFalse(result["ok"])
            self.assertEqual(result["status"], "ready_but_disabled")
            self.assertFalse(result["external_send"])
            self.assertEqual(result["provider"], "sendgrid")
            self.assertIn(LEGAL_DISCLAIMER, result["body_text"])
            self.assertNotIn("secret-token", json.dumps(result))
            rows = (base / result["status_path"]).read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(rows), 1)
            status_row = json.loads(rows[0])
            self.assertEqual(status_row["status"], "ready_but_disabled")
            self.assertFalse(status_row["external_send"])

    def test_email_status_response_is_safe_and_includes_last_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            deliver_weekly_brief_test_mode(_brief(), recipient_email="mlro@example.com", base_dir=base)

            status = build_email_status_response(base_dir=base, env={
                "STATUTEPROOF_EMAIL_PROVIDER": "smtp",
                "STATUTEPROOF_EMAIL_FROM": "briefs@statuteproof.example",
                "SMTP_HOST": "smtp.example.com",
                "SMTP_PORT": "587",
                "SMTP_USERNAME": "smtp-user",
                "SMTP_PASSWORD": "secret-password",
            })

            self.assertTrue(status["ok"])
            self.assertEqual(status["provider"], "smtp")
            self.assertEqual(status["status"], "ready_but_disabled")
            self.assertEqual(status["last_delivery_status"]["status"], "written")
            self.assertEqual(status["disclaimer"], LEGAL_DISCLAIMER)
            self.assertNotIn("secret-password", json.dumps(status))
            self.assertNotIn("smtp-user", json.dumps(status))


if __name__ == "__main__":
    unittest.main()
