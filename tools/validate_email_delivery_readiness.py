#!/usr/bin/env python3
"""Validate production-email readiness controls without real external sending."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []

    email_delivery = read("product/regradar/app/email_delivery.py")
    api = read("product/regradar/app/api.py")
    api_js = read("product/regradar/web/src/api.js")
    integrations = read("product/regradar/web/src/components/app/IntegrationsPage.jsx")
    tests = read("product/regradar/tests/test_email_delivery_readiness.py")

    required_email_helpers = [
        "def validate_email_provider_config",
        "def build_email_status_response",
        "def deliver_weekly_brief_provider_ready",
        "def record_email_config_check",
        "def latest_email_delivery_status",
        '"local_outbox"',
        '"smtp"',
        '"postmark"',
        '"sendgrid"',
    ]
    for marker in required_email_helpers:
        if marker not in email_delivery:
            errors.append(f"Missing email readiness helper/marker: {marker}")

    if "external_send" not in email_delivery or "False" not in email_delivery:
        errors.append("Email readiness code must explicitly keep external_send false for safe paths.")
    if "STATUTEPROOF_EMAIL_SEND_ENABLED" not in email_delivery:
        errors.append("Email readiness code must require explicit send-enabled configuration.")
    if "SMTP_PASSWORD" not in email_delivery or "POSTMARK_SERVER_TOKEN" not in email_delivery or "SENDGRID_API_KEY" not in email_delivery:
        errors.append("Email readiness code must validate expected provider config names.")

    required_routes = [
        "/api/delivery/email-status",
        "/api/delivery/email-config-check",
        "/api/delivery/email-test-mode",
    ]
    for route in required_routes:
        if route not in api:
            errors.append(f"Missing email readiness API route: {route}")

    for marker in ("emailStatus()", "emailConfigCheck()", "emailTestMode("):
        if marker not in api_js:
            errors.append(f"Missing frontend API client marker: {marker}")

    required_ui_markers = [
        "Local outbox / test-mode",
        "Provider configured but disabled",
        "Configuration required",
        "Production sending enabled",
        "No provider secrets are shown",
        "Monitoring intelligence only. Not legal advice.",
    ]
    for marker in required_ui_markers:
        if marker not in integrations:
            errors.append(f"Missing email readiness UI marker: {marker}")

    required_tests = [
        "test_default_provider_config_is_local_outbox_test_mode",
        "test_smtp_missing_password_returns_configuration_required",
        "test_postmark_missing_token_returns_configuration_required",
        "test_sendgrid_missing_token_returns_configuration_required",
        "test_configured_provider_with_send_disabled_is_ready_but_disabled",
        "test_provider_delivery_does_not_send_when_disabled_and_records_status",
        "test_email_status_response_is_safe_and_includes_last_status",
    ]
    for marker in required_tests:
        if marker not in tests:
            errors.append(f"Missing email readiness test: {marker}")

    customer_facing = integrations
    forbidden_claims = [
        "weekly email delivery is live",
        "automated customer emails are enabled",
        "production delivery guaranteed",
        "guaranteed compliance",
        "never miss",
        "perfect parsing",
        "production email active by default",
    ]
    for claim in forbidden_claims:
        if claim in customer_facing.lower():
            errors.append(f"Forbidden customer-facing email/compliance claim found: {claim}")

    for secret_literal in ("secret-password", "secret-token", "POSTMARK_SERVER_TOKEN=", "SENDGRID_API_KEY=", "SMTP_PASSWORD="):
        if secret_literal in "\n".join([email_delivery, api, api_js, integrations]):
            errors.append(f"Secret-like literal found in runtime/frontend code: {secret_literal}")

    if errors:
        print("Email delivery readiness validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Email delivery readiness validation PASSED")
    print("- Provider config/status helpers are present")
    print("- Local outbox remains the safe default")
    print("- Email status/config-check API and UI markers are present")
    print("- Forbidden customer-facing claims and secret literals are absent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
