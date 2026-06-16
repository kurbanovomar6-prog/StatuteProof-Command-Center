# Production Email Delivery Next Step

Date: 2026-06-16

## Current Status

Email delivery remains safe test-mode/local outbox only. No external customer email is sent by default, and production email delivery is not claimed.

## Why Production Send Was Not Added In This Sprint

The sprint removed prototype trust risks and built the Global Review Queue. Production email requires provider selection, secret handling, bounce/error states, unsubscribe/preferences where relevant, and clear customer opt-in. That should not be rushed into a trust sprint.

## Recommended Implementation Path

1. Add a provider abstraction for SMTP/Postmark/SendGrid.
2. Keep test-mode as the default unless explicit provider config is present.
3. Validate config presence without printing secrets.
4. Add a UI state:
   - "Email delivery: test-mode only"
   - "Production provider configured"
   - "Delivery failed: review provider settings"
5. Add tests that:
   - never perform external sends;
   - verify test-mode payload and status records;
   - verify missing provider config blocks production send;
   - verify disclaimer is included in every payload.

## Customer-Safe Wording Until Implemented

Allowed:

- "Email brief delivery can be tested through local outbox/test-mode."
- "Production email delivery requires provider configuration."

Forbidden:

- "Weekly email delivery is live."
- "Automated customer emails are enabled."
- "Production delivery guaranteed."
