# Production Email Current State

Date: 2026-06-16

## Weekly Brief Rendering

Weekly briefs are built in `product/regradar/app/weekly_brief.py`.

Key functions:

- `build_weekly_brief(...)`
- `render_weekly_brief_markdown(...)`
- `render_weekly_brief_html(...)`

Brief rendering already includes legal-safe language and blocks forbidden compliance/legal claims.

## Local Outbox Delivery

Safe test-mode email output is handled by `product/regradar/app/email_delivery.py`.

Current function:

- `deliver_weekly_brief_test_mode(...)`

It writes:

- local email payload JSON under `data/email_outbox/`;
- delivery status JSONL under `data/email_outbox/delivery_status.jsonl`.

It does not send external email.

## Delivery Status Recording

Delivery status is appended in `email_delivery._append_status(...)`. Current statuses include:

- `written`
- `failed`

The new readiness layer should add config-related statuses without pretending delivery happened:

- `configuration_required`
- `ready_but_disabled`
- `test_mode`

## Frontend Email / Test-Mode State

`product/regradar/web/src/components/app/IntegrationsPage.jsx` currently lets a user:

- send a Telegram sample brief;
- write an email test-mode payload to the local outbox;
- view messaging that no external customer email is sent.

It does not yet show provider readiness, missing config fields, or last email delivery status.

## Missing For Production Provider Readiness

- provider config model;
- safe config validation endpoint;
- email status endpoint;
- frontend provider/mode/status display;
- validator blocking fake production-email claims;
- tests proving external send remains disabled unless explicitly configured.

## Safest Implementation Path

1. Keep `deliver_weekly_brief_test_mode(...)` unchanged for local outbox delivery.
2. Add provider config/status helpers beside it.
3. Add API endpoints for status and config check.
4. Add UI status panel in Integrations.
5. Add validators and tests that prevent fake “sent” claims or secret leakage.
