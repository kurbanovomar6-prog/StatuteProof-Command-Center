# Plan Intent And Manual Activation Report

Date: 2026-06-14

## Executive Result

Plan intent versus paid activation was fixed at the backend contract and billing UI level.

A user can still request Founding Pilot, UAE Monitor, or Consultant scope, but the API now returns `pending_manual_activation` instead of `active`. Active capabilities remain Source Readiness Review capabilities until a future founder/manual activation path exists.

## Current Plan Flow

1. Public pricing and Choose Plan pages let the user select a plan.
2. `/api/plan` records plan intent only.
3. No Stripe checkout is triggered.
4. No payment method is stored.
5. No paid monitoring is activated automatically.
6. Billing shows the active plan as Source Readiness Review and the paid tier as a requested plan pending manual activation.

## Fixes Made

Updated `product/regradar/app/plan.py`:

- Paid plan selections now return `status: pending_manual_activation`.
- Added `active_plan_name` / `active_plan_display`.
- Added `requested_plan` / `requested_plan_display`.
- Added `active_capabilities`.
- Added `requested_capabilities`.
- Paid capabilities now include `manual_activation_required: true`.
- Active capabilities remain Source Readiness Review until manual activation exists.

Updated `product/regradar/web/src/components/app/BillingPage.jsx`:

- Billing no longer labels a requested paid plan as the current active plan.
- Billing shows "Pending manual activation" for paid plan requests.
- Billing shows "Requested plan — pending manual activation" separately.

Updated `product/regradar/web/src/components/app/SourceLabPage.jsx`:

- Custom-source gating uses `active_capabilities` first.
- A paid plan request alone does not unlock custom-source activation.

Added `product/regradar/tests/test_auth_plan_contracts.py`:

- Confirms paid plan requests remain pending manual activation.
- Confirms active capabilities remain Source Readiness Review capabilities.
- Confirms requested plan/capabilities are still visible for UI and ops follow-up.

## Stripe Readiness Status

Stripe self-serve checkout remains not active.

Approved customer-facing wording:

- "Plan request saved."
- "Manual activation after source readiness review."
- "No payment has been processed."
- "No payment method is stored."
- "Live monitoring starts after source readiness confirmation."

Forbidden wording:

- "Payment successful."
- "Subscription active."
- "Monitoring activated."
- "Paid plan enabled" unless founder/manual activation has actually occurred.

## Remaining Billing Gaps

- There is no founder/admin activation workflow yet.
- There is no audit log for manual plan activation.
- There is no Stripe subscription state or webhook handling.
- Retention/source limits are still capability labels, not enforced production billing controls.

## Validation

Command run:

`python3 -m pytest product/regradar/tests/test_auth_plan_contracts.py -q`

Result:

`5 passed`

## Next Billing Task

Create a founder-only manual activation path with an activation timestamp, active plan field, activation reviewer, and audit log before accepting paid pilots.
