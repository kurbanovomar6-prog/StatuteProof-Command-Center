# Production Email Readiness Implementation Plan

Date: 2026-06-16

## Current Email State

StatuteProof currently supports email delivery only in safe test-mode. `product/regradar/app/email_delivery.py` renders a reviewed weekly brief email payload into a local outbox and appends a delivery status row. It does not connect to SMTP, Postmark, SendGrid, or any external customer email provider.

## Existing Test-Mode / Local Outbox Flow

- `build_weekly_brief(...)` creates a weekly brief from reviewed source evidence.
- `deliver_weekly_brief_test_mode(...)` renders Markdown and HTML bodies.
- The payload is written to `data/email_outbox/*.json`.
- Delivery status is appended to `data/email_outbox/delivery_status.jsonl`.
- The payload includes the legal boundary disclaimer.
- External sending is always false.

## Target Production-Readiness Behavior

Add a safe provider readiness layer without sending real emails:

- default provider remains `local_outbox`;
- supported provider names: `local_outbox`, `smtp`, `postmark`, `sendgrid`;
- provider config can be validated without printing secrets;
- backend exposes email status and config-check endpoints;
- frontend shows mode, provider, missing config names, last status, and safe disclaimers;
- tests prove no external send happens when send is disabled.

## Files Likely To Change

- `product/regradar/app/email_delivery.py`
- `product/regradar/app/api.py`
- `product/regradar/tests/test_email_delivery_readiness.py`
- `product/regradar/web/src/api.js`
- `product/regradar/web/src/components/app/IntegrationsPage.jsx`
- `tools/validate_email_delivery_readiness.py`
- `tools/validate_mvp_trust_workflow.py` if needed
- `docs/production-email-delivery-next-step.md`
- `docs/ideal-product-execution-final-report.md`

## Provider Strategy

Use environment-variable presence checks only. Do not print or expose secret values.

Allowed provider env names:

- `STATUTEPROOF_EMAIL_PROVIDER`
- `STATUTEPROOF_EMAIL_FROM`
- `STATUTEPROOF_EMAIL_REPLY_TO`
- `STATUTEPROOF_EMAIL_SENDER_NAME`
- `STATUTEPROOF_EMAIL_SEND_ENABLED`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `POSTMARK_SERVER_TOKEN`
- `SENDGRID_API_KEY`

Provider readiness states:

- `test_mode`: local outbox, no external send;
- `configuration_required`: provider selected but required env names are missing;
- `ready_but_disabled`: provider config is present but external sending is disabled;
- `production_enabled`: provider config is present and external sending is explicitly enabled.

This sprint will not exercise real external sends.

## Safety Gates

- No real email is sent.
- No secrets are printed, returned, or committed.
- Default remains local outbox/test-mode.
- `send_enabled` must be explicit.
- Missing config responses show env variable names only.
- Customer-facing copy must not claim production email is active by default.
- Every status response includes: `Monitoring intelligence only. Not legal advice.`

## Tests / Validators

Add tests for:

- default config is local outbox/test-mode;
- SMTP/Postmark/SendGrid missing config returns `configuration_required`;
- configured provider with send disabled returns `ready_but_disabled`;
- safe provider delivery status rows never set `external_send` true when disabled;
- local outbox behavior remains unchanged;
- last delivery status can be read safely;
- no secret values appear in status payloads.

Add `tools/validate_email_delivery_readiness.py`.

## Future Work Not Included

- Actual SMTP/Postmark/SendGrid network sending.
- Bounce handling.
- Unsubscribe/preference center.
- Domain verification checks.
- Production incident alerts for provider outages.

## Validation Plan

Run:

- `python3 -m compileall product/regradar`
- `python3 -m pytest product/regradar/tests -q`
- `python3 tools/validate_email_delivery_readiness.py`
- existing trust/source/PDF validators
- `git diff --check`
- frontend build/lint/routes

## Commit Policy

Stage only files touched by the production-email readiness task. Do not stage runtime outbox payloads, generated artifacts, secrets, `.env`, or unrelated files. Commit with:

`git commit -m "feat: add production email readiness controls"`
