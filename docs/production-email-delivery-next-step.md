# Production Email Delivery Readiness Status

Date: 2026-06-16

## Current Status

Email delivery has safe production-readiness controls. No external customer email is sent by default, and production email delivery is not claimed as live.

Implemented:

- local outbox/test-mode remains default;
- provider config validation for SMTP/Postmark/SendGrid;
- safe email status API;
- safe config-check API;
- Integrations UI showing provider mode, missing config, disabled/enabled state, and last delivery status;
- validator blocking fake production-email claims and secret leakage.

Not implemented:

- real external SMTP/Postmark/SendGrid sending;
- bounce/error webhook handling;
- unsubscribe/preference center.

## Customer-Safe Wording Now

Allowed:

- "Email brief delivery can be tested through local outbox/test-mode."
- "Production email delivery requires provider configuration."
- "Provider readiness and missing configuration are visible in the dashboard."
- "External sending is disabled unless explicitly configured and enabled server-side."

Forbidden:

- "Weekly email delivery is live."
- "Automated customer emails are enabled."
- "Production delivery guaranteed."

## Next Implementation Path

1. Add actual provider send adapters behind an explicit `STATUTEPROOF_EMAIL_SEND_ENABLED=true` gate.
2. Add a one-recipient manual send-test endpoint with explicit confirmation.
3. Add provider failure and retry status.
4. Add unsubscribe/preferences before broad self-serve use.
