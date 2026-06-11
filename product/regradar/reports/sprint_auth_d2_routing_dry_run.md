# Sprint Auth D2 — Approved Alert Routing Dry-Run

## 1. Verdict

Completed. Authenticated users can now request a dry-run preview of human-approved alert artifacts matched against their saved profile, and can manually send one selected approved-preview alert to their own linked Telegram when all readiness checks pass.

Automatic production alert delivery is not enabled.

## 2. Files changed

- app/alert_routing.py
- app/api.py
- web/src/api.js
- web/src/components/app/AlertsPage.jsx

## 3. Approved alert discovery

`app.alert_routing` reads existing file-based alert artifacts through the current review helpers:

- `app.alert_review.list_alert_drafts()`
- `app.alert_review.latest_review_for(alert_id)`
- `STATUS_APPROVED_WEEKLY`
- `STATUS_APPROVED_URGENT`

Only alerts with the latest approved review status are considered. Malformed or missing artifacts are skipped safely. If no approved alerts exist, the API returns a clean empty state.

## 4. User profile routing bridge

The new routing bridge translates `user_profiles` into a routing profile using the authenticated integer `user_id`. It includes company name, markets, industries, topics, empty `sources`, custom sources, `alert_threshold`, mirrored `risk_threshold`, default delivery thresholds, onboarding status and Telegram alert preference.

No `user_id` or `telegram_chat_id` is accepted from request bodies.

## 5. Matching logic

The dry-run scoring is transparent and intentionally simple:

- Risk threshold match: up to 40 points
- Market/jurisdiction match: up to 25 points
- Industry/topic overlap: up to 20 points
- Custom source domain match: up to 15 points

An alert is marked matched when score is at least 40. The backend still returns approved alerts that do not match, but marks them clearly and does not make them delivery-ready.

## 6. API endpoints added

- `GET /api/delivery/preview?days=14`
- `POST /api/delivery/send-preview-alert`

Both endpoints require the Auth A session cookie. The send endpoint validates `alert_id`, sends only one selected alert, and never accepts `user_id` or `chat_id`.

## 7. Frontend preview changes

`AlertsPage` now shows a reviewed alert routing preview above sample alert cards:

- approved alert count
- source, title, risk and review status
- relevance score
- match reasons
- limitations
- source proof URL
- delivery readiness
- manual "Send preview to Telegram" button

Sample cards remain below and are labeled as format previews, not live approved alerts.

## 8. Delivery/logging/idempotency

Manual preview sends reuse the existing D1 `user_delivery_log` helpers. Each alert uses:

`{user_id}:reviewed_alert_preview:{alert_id}`

as the idempotency key, blocking duplicate sends of the same reviewed alert preview to the same user.

The sent-alert lookup also recognizes the legacy preview key shape:

`{user_id}:reviewed_alert:{alert_id}`

Successful and failed sends update the delivery log. Global admin/contact Telegram remains separate.

## 9. Validation performed

- `python3 -m compileall app run.py -q`: passed
- DB init smoke: passed
- Routing smoke: passed
  - approved alerts considered: 1
  - matches returned: 1
  - routing profile includes `sources`, `risk_threshold`, and `delivery_preferences`
- Manual send guard smoke: passed
  - blocked as `not_ready` when Telegram was not connected
- `cd web && npm run build`: passed
- `git diff --check`: passed
- Safety grep: disclaimer-only "not legal advice" matches plus the explicit dry-run no-production-delivery wording

## 10. What is now real

- Approved reviewed alert artifacts can be discovered.
- Account-owned profiles can be converted into routing profiles.
- Approved alerts can be scored against the current user profile.
- The dashboard can show real approved routing previews.
- A user can manually send one eligible reviewed preview alert to their own paired Telegram.
- Duplicate manual sends are blocked.

## 11. What is still not implemented

- Automatic production alert delivery is not enabled.
- Weekly scheduled delivery is not implemented.
- Bulk sending is not implemented.
- Email delivery is not implemented.
- Team accounts are not implemented.
- No unreviewed alerts are sent.
- Real monitoring pipeline alerts are not automatically routed to users.

## 12. Operational notes

Approved alerts depend on existing review artifacts under `data/source_snapshots` and `data/alert_reviews/reviews.jsonl`.

Manual Telegram delivery requires:

- completed onboarding;
- Telegram alerts enabled in Settings;
- a paired Telegram chat from Auth C;
- a matching approved reviewed alert;
- no prior delivery log with the same idempotency key.

## 13. Next sprint recommendation

Auth D3 should add admin-controlled or scheduled delivery only after dry-run validation, with explicit operator controls, audit logs, and conservative rollout limits.
