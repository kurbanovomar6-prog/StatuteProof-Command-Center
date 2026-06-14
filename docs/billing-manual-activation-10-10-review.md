# Billing and Manual Activation 10/10 Review

## 1. Scope

Reviewed the current billing and pricing posture from the P0 sprint reports and current frontend/backend plan flow:

- public pricing and registration plan intent
- `/api/plan`
- billing/settings app copy
- manual activation wording
- source readiness review dependency

## 2. Current Score

Billing/manual activation score: 7.6/10

The product is honest that paid activation is manual and source-readiness-dependent. The remaining gap is operational: there is no full admin activation console, payment collection flow, invoice workflow, or production Stripe readiness claim.

## 3. What Works

- Public plan choices are treated as plan intent/request, not paid activation.
- Billing copy avoids fake self-serve Stripe checkout.
- Manual activation after source readiness review is the correct current promise.
- Plan gating language is safer after the P0 sprint.

## 4. Remaining Risks

| Risk | Severity | Notes |
|---|---:|---|
| No complete admin activation workflow | P1 | Founder/operator can still manage manually, but it is not a polished paid-plan backend |
| Stripe/live billing readiness not complete | P1 | Do not imply live checkout |
| Plan intent may still be confused with active subscription in future UI changes | P1 | Validators/copy review should guard this |
| No invoice/payment method handling in app | P2 | Acceptable for manual early pilot if stated honestly |

## 5. Allowed Customer-Facing Wording

- “Request Founding Pilot”
- “Manual activation after source readiness review”
- “Plan request received”
- “Active plan changes after operator approval”
- “Billing setup is completed manually for early pilots”

## 6. Forbidden Customer-Facing Wording

- “Payment successful” unless real payment occurred.
- “Subscription active” unless manually or Stripe-activated.
- “Instant activation” for UAE Monitor.
- “Stripe checkout live” unless production Stripe is verified.

## 7. Safe Fixes For This Run

No broad billing code changes are recommended in this continuation pass unless a stale label is found during validation. The safer next product task is an operator-facing activation checklist and admin endpoint review.

## 8. Next Exact Task

Build a manual pilot activation runbook and minimal admin-safe activation path that separates requested plan, approved plan, active subscription, and billing evidence.
